from enum import Enum
import os
import pythena
from starlette.responses import Response
import typing
import json
import boto3



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

#######################################################################
# method 1 -- load latest parquet
#######################################################################

# https://stackoverflow.com/questions/45375999/how-to-download-the-latest-file-of-an-s3-bucket-using-boto3/62864288#62864288

def load_latest_parquet(
        bucket_name, 
        prefix):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator( "list_objects_v2" )
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    latest = None
    for page in page_iterator:
        if "Contents" in page:
            latest2 = max(page['Contents'], key=lambda x: x['LastModified'])
            if latest is None or latest2['LastModified'] > latest['LastModified']:
                latest = latest2
    
    response = s3.get_object(bucket_name, latest['Key'])
    return response['Body'].read()



#######################################################################
# method 2 -- query Athena
#######################################################################

#TODO combine with query_job
def live_query_job(feeds,dbname, system_id, start, end): 
    athena_client = pythena.Athena(database=dbname)
    # n.b. use single quotes in these queries otherwise Athena chokes
    query_String=   \
        f"""
        SELECT *
        FROM {system_id}
        WHERE
        ("{feeds[system_id]['timestamp_key']}" >= from_iso8601_timestamp('{start}') AND "{feeds[system_id]['timestamp_key']}" < from_iso8601_timestamp('{end}'))
        """
    # TODO: do i need a new workgroup for the stack? hardcoded?
    dataframe, _ = athena_client.execute(query=query_String, workgroup="busobservatory")
    # n.b. JSON serializer doesn't like NaNs
    return dataframe.fillna('').to_dict(orient='records')


def fetch_live_by_system_packager(response, system_id, start, end):

    return response 

    #FIXME needs to be a FeatureCollection for the map apps to consume





