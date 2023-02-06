# import os
import json
from .parsers import *
# import parsers.GTFSRT as GTFSRT
# import parsers.CleverDevicesXML as CleverDevicesXML
# import parsers.SIRI as SIRI


def lambda_handler(event, context):

    # FIXME: get config from the event
    # {"Parameters": {"name":"test"}, "ContainerOverrides": { "Command": ["echo","Ref::name"] } }
    region = event['REGION']
    config = event['Parameters']
    bucket = config['S3_BUCKET']
    system_id = config['SYSTEM_ID']

    # fetch + parse data
    feed = Feed(config, system_id)
    positions_df = feed.scrape_feed()

    # FIXME: write a new dumper function that takes a df and writes it to s3
    # dump to S3 as parquet
    dump_buses(region,
               bucket,
               system_id,
               positions_df)

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
        self.tz = config['tz']

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
