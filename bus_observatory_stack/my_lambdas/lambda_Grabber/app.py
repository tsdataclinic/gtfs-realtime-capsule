import datetime as dt
import boto3
import os
import json
from .parsers import GTFSRT, CleverDevicesXML, SIRI
from pandas import DataFrame

def lambda_handler(event, context):

    # get config from the passed event
    region = event['REGION']
    bucket_name = event['Parameters']['bucket_name']
    feed_config = event['Parameters']['feed_config']
    system_id = event['Parameters']['system_id']

    # fetch + parse data
    feed = Feed(feed_config, system_id)
    positions_df = feed.scrape_feed()

    # dump to S3 as parquet
    datalake = DataLake(region,bucket_name,system_id)
    datalake.dump_buses(positions_df)

    # report summary
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"{system_id}: wrote {positions_df[feed.route_key].nunique()} routes and {len(positions_df)} buses from {system_id} to s3://{bucket}/{system_id}/",
        }),
    }


class Feed:
    def __init__(self, config, system_id) -> None:
        self.system_id = system_id
        self.config = config
        self.feed_type = config['feed_type']
        self.timestamp_key = config['timestamp_key']
        self.route_key = config['route_key']
        # self.tz = config['tz']

        # fields that may be present
        try:
            self.api_key = config['api_key']
        except:
            pass

        # configure header if relevant
        if config['header'] == 'True':
            self.header_key_name = config['header_format']['key_name']
            self.header_key_value = config['header_format']['template'].format(
                key_value=config['api_key'])
            self.header = {self.header_key_name: self.header_key_value}
            self.url = config['url']
        else:
            self.url = config['url']
            self.header = None

    # dispatch function associated with the feed_type (returns positions_df)

    def fetch_gtfsrt(self):
        return GTFSRT.get_buses(self)

    def fetch_njxml(self):
        return CleverDevicesXML.get_buses(self)

    def fetch_siri(self):
        return SIRI.get_buses(self)

    dispatch = {'gtfsrt': fetch_gtfsrt,
                'njxml': fetch_njxml,
                'siri': fetch_siri
                }

    def scrape_feed(self):
        return self.__class__.dispatch[self.feed_type](self)


class DataLake:
    def __init__(self, bucket_name: str, system_id: str, region: str) -> None:
        self.bucket_name = bucket_name
        self.system_id = system_id
        self.region = region

    def dump_buses(self, positions_df: DataFrame):

        # dump to instance ephemeral storage
        timestamp = dt.datetime.now().replace(microsecond=0)
        filename=f"{self.system_id}_{timestamp}.parquet".replace(" ", "_").replace(":", "_")

        positions_df.to_parquet(f"/tmp/{filename}", times='int96')

        # upload to S3
        source_path=f"/tmp/{filename}"
        remote_path=f"lake/{self.system_id}/incoming/{filename}"
        session = boto3.Session(region_name=self.region)
        s3 = session.resource('s3')
        result = s3.Bucket(self.bucket_name).upload_file(source_path,remote_path)

        # clean up /tmp
        try:
            os.remove(source_path)
        except:
            pass
