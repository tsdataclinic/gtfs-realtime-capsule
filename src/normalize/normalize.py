import datetime
import os.path

import click
import boto3
from dateutil import parser
from gtfs_realtime_pb2 import FeedMessage
from src.normalize.protobuf_utils import protobuf_objects_to_pyarrow_table
from src.normalize.parquet_utils import write_data, add_time_columns
import time
import json


def get_last_processed_timestamp(s3, bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(response['Body'].read())['last_processed']
    except s3.exceptions.NoSuchKey:
        return None


def update_last_processed_timestamp(s3, bucket, key, timestamp):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps({'last_processed': timestamp})
    )


def normalize_raw_feed(raw_input, cur_time, cur_date):
    feed = FeedMessage()
    feed.ParseFromString(raw_input)

    trip_updates = []
    vehicles = []
    alerts = []

    for entity in feed.entity:
        entity_id = entity.id
        if entity.HasField('trip_update'):
            trip_updates.append((entity_id, entity.trip_update))
        if entity.HasField('alert'):
            alerts.append((entity_id, entity.alert))
        if entity.HasField('vehicle'):
            vehicles.append((entity_id, entity.vehicle))

    trip_updates_pa = protobuf_objects_to_pyarrow_table([x[1] for x in trip_updates]) if trip_updates else None
    vehicles_pa = protobuf_objects_to_pyarrow_table([x[1] for x in vehicles]) if vehicles else None
    alerts_pa = protobuf_objects_to_pyarrow_table([x[1] for x in alerts]) if alerts else None

    if trip_updates_pa:
        trip_updates_pa = trip_updates_pa.add_column(0, "id", [[x[0] for x in trip_updates]])
        trip_updates_pa = add_time_columns(trip_updates_pa, cur_time, cur_date)

    if vehicles_pa:
        vehicles_pa = vehicles_pa.add_column(0, "id", [[x[0] for x in vehicles]])
        vehicles_pa = add_time_columns(vehicles_pa, cur_time, cur_date)

    if alerts_pa:
        alerts_pa = alerts_pa.add_column(0, "id", [[x[0] for x in alerts]])
        alerts_pa = add_time_columns(alerts_pa, cur_time, cur_date)

    return trip_updates_pa, vehicles_pa, alerts_pa



def parse_files(source_prefix, destination_prefix, start_date, state_file):
    s3 = boto3.client('s3')

    source_bucket, source_key = source_prefix.replace("s3://", "").split("/", 1)
    state_bucket, state_key = state_file.replace("s3://", "").split("/", 1)

    last_processed = get_last_processed_timestamp(s3, state_bucket, state_key)
    if not last_processed:
        last_processed = parser.parse(start_date)

    # List objects in the source bucket
    paginator = s3.get_paginator('list_objects_v2')

    cur_date = datetime.datetime.now()
    cur_processing = last_processed
    if isinstance(cur_processing, str):
        cur_processing = datetime.fromtimestamp
    while cur_processing < cur_date:
        date_partition = os.path.join(source_key, str(cur_processing.year), str(cur_processing.month), str(cur_processing.day))
        print(date_partition)
        for page in paginator.paginate(Bucket=source_bucket, Prefix=date_partition):
            for obj in page.get('Contents', []):
                key = obj['Key']
                print(key)
                if key.endswith('.binpb'):
                    # Check if this file is newer than the last processed file
                    print(int(key.split('/')[-1].split('.')[0]))
                    print(last_processed.timestamp())
                    if int(key.split('/')[-1].split('.')[0]) > last_processed.timestamp():
                        # Download the file
                        response = s3.get_object(Bucket=source_bucket, Key=key)
                        file_content = response['Body'].read()

                        trip_updates_pa, vehicles_pa, alerts_pa = normalize_raw_feed(
                            file_content,
                            obj['LastModified'],
                            obj['LastModified'].date()
                        )

                        if trip_updates_pa:
                            s3_uri = f"{destination_prefix}/trip-updates"
                            write_data(trip_updates_pa, s3_uri)
                        if vehicles_pa:
                            s3_uri = f"{destination_prefix}/vehicles"
                            write_data(vehicles_pa, s3_uri)
                        if alerts_pa:
                            s3_uri = f"{destination_prefix}/alerts"
                            write_data(alerts_pa, s3_uri)

                        # Update the last processed timestamp
                        update_last_processed_timestamp(s3, state_bucket, state_key, str(obj['LastModified'].timestamp()))
        cur_processing += datetime.timedelta(days=1)


# @click.command()
# @click.option('--source-prefix', required=True, help='Source S3 prefix (e.g., s3://bucket/prefix)')
# @click.option('--destination-prefix', required=True, help='Destination S3 prefix for Parquet files')
# @click.option('--start-date', required=True, help='If no state-file is found, the date to start searching for files.')
# @click.option('--state-file', required=True, help='S3 path to store the state (e.g., s3://bucket/state.json)')
# @click.option('--interval', default=60, help='Run interval in seconds (default: 60)')
def main(source_prefix, destination_prefix, start_date, state_file, interval):
    while True:
        parse_files(source_prefix, destination_prefix, start_date, state_file)
        time.sleep(interval)


if __name__ == "__main__":
    main(
        "s3://dataclinic-gtfs-rt/raw/NYC Subway ACE Lines",
        "s3://dataclinic-gtfs-rt/norm/NYC Subway ACE Lines",
        "20240901",
        "s3://dataclinic-gtfs-rt/state/NYC Subway ACE Lines",
        60
    )