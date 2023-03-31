from enum import Enum
import os
import pythena
from starlette.responses import Response
import typing
import json
import boto3
# import pytz
from shapely.geometry import Point
from geojson import Feature, FeatureCollection
from geojson import dumps as gjdumps
import pandas as pd
import io
import numpy as np


#######################################################################
# helpers
#######################################################################

# load feed from S3
def get_feeds():
    
    # grab parameter data from parameter store matching "/{bucket-name}/feeds/*"
    param_name_prefix = f"/{os.environ['bucket']}/feeds/"
    ssm = boto3.client('ssm')
    response = ssm.get_parameters_by_path(Path=param_name_prefix)

    #reconstruct a feeds dict from the parameter store data
    feeds = {}
    for f in response['Parameters']:
        system_id=f['Name'].split("/")[-1]
        feeds[system_id] = json.loads(f['Value'])

    return feeds

def filter_feeds(feeds):
    filtered_feeds = {system_id: system_data for system_id, system_data in feeds.items() if system_data['publish'] == 'True'}
    return filtered_feeds

def get_system_id_enum(feeds):
    return Enum('SystemIDs', {k:k for (k,v) in feeds.items()} )

def get_schema(system_id):
    client = boto3.client('athena')
    response = client.get_table_metadata(
        CatalogName='awsdatacatalog', #FIXME: ok to hardcode?
        DatabaseName=os.environ['bucket'],
        TableName=system_id
        )
    print(response)
    return response['TableMetadata']['Columns']
    
def get_system_history(dbname, feed, system_id):
    athena_client = pythena.Athena(database=dbname)
    query_String=   \
        f"""            
        SELECT year ("{feed['timestamp_key']}") as y, month ("{feed['timestamp_key']}") as m, day ("{feed['timestamp_key']}") as d, count(*) as ct
        FROM {system_id}      
        GROUP BY year ("{feed['timestamp_key']}"), month ("{feed['timestamp_key']}"), day ("{feed['timestamp_key']}")
        ORDER BY year ("{feed['timestamp_key']}") ASC, month ("{feed['timestamp_key']}") ASC, day ("{feed['timestamp_key']}") ASC
        """
    dataframe, _ = athena_client.execute(
        query=query_String, 
        workgroup="busobservatory") # FIXME: do i need a new workgroup for the stack? hardcoded?
    # n.b. JSON serializer doesn't like NaNs
    history = dataframe.fillna('').to_dict(orient='records')
    return history

class PrettyJSONResponse(Response):
    media_type = "application/json"
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")

class PrettyGeoJSONResponse(Response):
    media_type = "application/json"
    def render(self, content: typing.Any) -> bytes:
        return gjdumps(
            content,
            ensure_ascii=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")

#######################################################################
# HELPERS FOR /buses/bulk
# TODO change this to daily entire systems, and it returns a redirect to an S3 link, and starts the download?
#######################################################################

def query_job(feeds,dbname, system_id, route, start, end): 
    athena_client = pythena.Athena(database=dbname)
    # n.b. use single quotes in these queries otherwise Athena chokes
    query_String=   \
        f"""
        SELECT *
        FROM {system_id}
        WHERE
        "{feeds[system_id]['route_key']}" = '{route}'
        AND
        ("{feeds[system_id]['timestamp_key']}" >= from_iso8601_timestamp('{start}') AND "{feeds[system_id]['timestamp_key']}" < from_iso8601_timestamp('{end}'))
        """

    # TODO: do i need a new workgroup for the stack? hardcoded?
    dataframe, _ = athena_client.execute(query=query_String, workgroup="busobservatory")
    # n.b. JSON serializer doesn't like NaNs
    return dataframe.fillna('').to_dict(orient='records')

def response_packager(response, system_id, route, start, end):
    return {
        "query": 
                {
                    "system_id": system_id,
                    "route": route,
                    "start (gte)":start,
                    "end (lt)":end
                }, 
        "result":response
        }

#######################################################################
# HELPERS FOR /buses/live
#######################################################################

def get_live_geojson(bucket_name, system_id):

    prefix = f"feeds/{system_id}"

    # after https://stackoverflow.com/questions/45375999/how-to-download-the-latest-file-of-an-s3-bucket-using-boto3
    def get_most_recent_s3_object(bucket_name, prefix):
        s3 = boto3.client('s3')
        paginator = s3.get_paginator( "list_objects_v2" )
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        latest = None
        for page in page_iterator:
            if "Contents" in page:
                latest2 = max(page['Contents'], key=lambda x: x['LastModified'])
                if latest is None or latest2['LastModified'] > latest['LastModified']:
                    latest = latest2
        return latest

    # Retrieve the latest Parquet file from S3
    s3 = boto3.client('s3')
    latest = get_most_recent_s3_object(bucket_name, prefix)
    response = s3.get_object(Bucket=bucket_name, Key=latest['Key'])
    parquet_object = response['Body'].read()

    # Create an in-memory buffer from the Parquet file
    buffer = io.BytesIO(parquet_object)

    # Read the data from the in-memory buffer and create a GeoDataFrame
    df = pd.read_parquet(buffer)

    # cleanup df
    df = df.dropna(subset=['vehicle.position.latitude', 'vehicle.position.longitude'])
    df = df.replace(np.nan, None)

    # # compute age of latest data
    # # after https://stackoverflow.com/questions/8906926/formatting-timedelta-objects
    # def strfdelta(tdelta, fmt):
    #     d = {"days": tdelta.days}
    #     d["hours"], rem = divmod(tdelta.seconds, 3600)
    #     d["minutes"], d["seconds"] = divmod(rem, 60)
    #     return fmt.format(**d)

    # now = pd.Timestamp.now(tz=pytz.UTC)
    # latest_time = pd.Timestamp(df.head(1)['vehicle.timestamp'].values[0]).tz_localize('UTC')
    # age = now - latest_time
    # age_formatted = strfdelta(age, "{days} days, {hours} hours, {minutes} minutes, {seconds} seconds")
    # print (f"The latest parquet is {age_formatted} old")

    # Create a geometry column from the longitude and latitude columns
    df['geometry'] = df.apply(lambda row: Point(row['vehicle.position.longitude'], row['vehicle.position.latitude']), axis=1)

    # Convert the geometry column to a list of GeoJSON points
    geometry_list = []
    for geom in df['geometry']:
        geometry_list.append(geom)

    # Remove the latitude and longitude columns from the DataFrame
    df = df.drop(columns=['vehicle.position.longitude', 'vehicle.position.latitude'])

    # FIXME this is a hack to get the timestamp to serialize, but it's not the right way to do it
    # FIXME also will need to configure the timestamp field name from the config file
    # serialize timestamp (convert to string)
    df['vehicle.timestamp'] = df['vehicle.timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

    # Create a list of GeoJSON features
    features_list = []
    for i in range(len(df)):
        feature = Feature(geometry=geometry_list[i], properties=df.iloc[i].to_dict())
        features_list.append(feature)

    # Create a GeoJSON feature collection from the list of features
    feature_collection = FeatureCollection(features_list)

    return feature_collection



