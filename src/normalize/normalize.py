import datetime as dt
import logging
import os.path
import time

import click
import pyarrow as pa
import pytz
import s3fs
import structlog
from dateutil import parser

from norm_utils import (
    update_last_processed_timestamp,
    validate_date,
    get_last_processed_timestamp,
    load_config,
)
from gtfs_realtime_pb2 import FeedMessage
from src.normalize.parquet_utils import write_data, add_time_columns
from src.normalize.protobuf_utils import protobuf_objects_to_pyarrow_table
from src.util.s3_client import create_s3_client

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", key="ts"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
LOGGER = structlog.get_logger()
SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_DIR = f"{SCRIPT_DIR}/../../config"
DATA_DIR = f"{SCRIPT_DIR}/../../data"


def normalize_raw_feed(raw_input, cur_time, cur_date):
    feed = FeedMessage()
    feed.ParseFromString(raw_input)

    trip_updates = []
    vehicles = []
    alerts = []

    for entity in feed.entity:
        entity_id = entity.id
        if entity.HasField("trip_update"):
            trip_updates.append((entity_id, entity.trip_update))
        if entity.HasField("alert"):
            alerts.append((entity_id, entity.alert))
        if entity.HasField("vehicle"):
            vehicles.append((entity_id, entity.vehicle))

    trip_updates_pa = (
        protobuf_objects_to_pyarrow_table([x[1] for x in trip_updates])
        if trip_updates
        else None
    )
    vehicles_pa = (
        protobuf_objects_to_pyarrow_table([x[1] for x in vehicles])
        if vehicles
        else None
    )
    alerts_pa = (
        protobuf_objects_to_pyarrow_table([x[1] for x in alerts]) if alerts else None
    )

    if trip_updates_pa:
        trip_updates_pa = trip_updates_pa.add_column(
            0, "id", [[x[0] for x in trip_updates]]
        )
        trip_updates_pa = add_time_columns(trip_updates_pa, cur_time, cur_date)

    if vehicles_pa:
        vehicles_pa = vehicles_pa.add_column(0, "id", [[x[0] for x in vehicles]])
        vehicles_pa = add_time_columns(vehicles_pa, cur_time, cur_date)

    if alerts_pa:
        alerts_pa = alerts_pa.add_column(0, "id", [[x[0] for x in alerts]])
        alerts_pa = add_time_columns(alerts_pa, cur_time, cur_date)

    return trip_updates_pa, vehicles_pa, alerts_pa


def parse_files(s3, s3_fs, source_prefix, destination_prefix, start_date, state_file):
    source_bucket, source_key = source_prefix.replace("s3://", "").split("/", 1)
    state_bucket, state_key = state_file.replace("s3://", "").split("/", 1)

    last_processed = get_last_processed_timestamp(s3, state_bucket, state_key)
    if last_processed:
        LOGGER.info(f"Loaded last_processed timestamp of {last_processed}")
    else:
        last_processed = pytz.UTC.localize(parser.parse(start_date))
        LOGGER.info(
            f"No state information found at {state_file},"
            f" defaulting `last_processed={last_processed}"
        )

    # List objects in the source bucket
    paginator = s3.get_paginator("list_objects_v2")

    cur_time = pytz.UTC.localize(dt.datetime.utcnow())
    cur_processing = last_processed

    global_data_written = False
    while cur_processing <= cur_time:
        date_partition = os.path.join(
            source_key,
            str(cur_processing.year),
            str(cur_processing.month),
            str(cur_processing.day),
        )
        LOGGER.info(f"Processing date: {date_partition}")
        max_epoch_timestamp = cur_processing.timestamp()

        for page in paginator.paginate(Bucket=source_bucket, Prefix=date_partition, PaginationConfig={'PageSize': 30}):
            trip_updates_pa = None
            vehicles_pa = None
            alerts_pa = None

            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".binpb"):
                    # Check if this file is newer than the last processed file
                    file_write_epoch_time = float(key.split("/")[-1].removesuffix(".binpb"))
                    if file_write_epoch_time > cur_processing.timestamp():
                        LOGGER.info(f"Processing file: {key}")
                        # Download the file
                        response = s3.get_object(Bucket=source_bucket, Key=key)
                        file_content = response["Body"].read()

                        cur_trip_updates_pa, cur_vehicles_pa, cur_alerts_pa = (
                            normalize_raw_feed(
                                file_content,
                                obj["LastModified"],
                                obj["LastModified"].date(),
                            )
                        )

                        trip_updates_pa = (
                            pa.concat_tables([trip_updates_pa, cur_trip_updates_pa])
                            if trip_updates_pa
                            else cur_trip_updates_pa
                        )
                        vehicles_pa = (
                            pa.concat_tables([vehicles_pa, cur_vehicles_pa])
                            if vehicles_pa
                            else cur_vehicles_pa
                        )
                        alerts_pa = (
                            pa.concat_tables([alerts_pa, cur_alerts_pa])
                            if alerts_pa
                            else cur_alerts_pa
                        )

                    max_epoch_timestamp = max(max_epoch_timestamp, file_write_epoch_time)

            new_data_written = False
            if trip_updates_pa:
                s3_uri = f"{destination_prefix}/trip-updates"
                time_range = pa.compute.min_max(trip_updates_pa['time'])
                LOGGER.info(
                    f"Writing {trip_updates_pa.num_rows} entries to {s3_uri}. "
                    f"Min timestamp {time_range['min']}, max timestamp {time_range['max']}"
                )
                write_data(s3_fs, trip_updates_pa, s3_uri)
                new_data_written = True
            if vehicles_pa:
                s3_uri = f"{destination_prefix}/vehicles"
                time_range = pa.compute.min_max(vehicles_pa['time'])
                LOGGER.info(
                    f"Writing {vehicles_pa.num_rows} entries to {s3_uri}. "
                    f"Min timestamp {time_range['min']}, max timestamp {time_range['max']}"
                )
                write_data(s3_fs, vehicles_pa, s3_uri)
                new_data_written = True
            if alerts_pa:
                s3_uri = f"{destination_prefix}/alerts"
                time_range = pa.compute.min_max(alerts_pa['time'])
                LOGGER.info(
                    f"Writing {alerts_pa.num_rows} entries to {s3_uri}. "
                    f"Min timestamp {time_range['min']}, max timestamp {time_range['max']}"
                )
                write_data(s3_fs, alerts_pa, s3_uri)
                new_data_written = True
            if new_data_written:
                global_data_written = True
                LOGGER.info(
                    f"Updating last processed timestamp to "
                    f"maximum file timestamp: {dt.datetime.utcfromtimestamp(max_epoch_timestamp).isoformat()}"
                )
            update_last_processed_timestamp(s3, state_bucket, state_key, max_epoch_timestamp)
        cur_processing = (cur_processing + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    if not global_data_written:
        LOGGER.warning(
            "No new data written - is this expected?"
        )


@click.command()
@click.option("-f", "--feed_id", required=True, type=str, help="feed ID to be scraped")
@click.option(
    "-c",
    "--config_path",
    type=str,
    default=f"{CONFIG_DIR}/global_config.json",
    help="json path to the global config",
)
@click.option(
    "--source-prefix",
    type=str,
    default="raw",
    help="Source S3 prefix (e.g., s3://bucket/prefix)",
)
@click.option(
    "--destination-prefix",
    type=str,
    default="norm",
    help="Destination S3 prefix for Parquet files",
)
@click.option(
    "--start-date",
    callback=validate_date,
    default=None,
    help="If no state-file is found, the date to "
    "start searching for files. Defaults to "
    "today's date if not provided.",
)
@click.option(
    "--state-file",
    type=str,
    help="S3 path to store the state (e.g., s3://bucket/state.json)",
)
@click.option(
    "--interval", type=int, default=60, help="Run interval in seconds (default: 60)"
)
def main(
    feed_id,
    config_path,
    source_prefix,
    destination_prefix,
    start_date,
    state_file,
    interval,
):
    config = load_config(config_path)
    s3_bucket_path = f"s3://{config['s3_bucket']['uri']}"
    if not state_file:  # set default
        state_file = f"{s3_bucket_path}/state/{feed_id}"

    for key, val in config.get("normalize_argv_override", {}).items():
        LOGGER.info(f"Overriding argv {key}={val}")
        exec(key + f"={val}")

    s3 = create_s3_client(config["s3_bucket"])
    s3_fs = s3fs.S3FileSystem(
        key=config["s3_bucket"]["public_key"], secret=config["s3_bucket"]["secret_key"]
    )
    while True:
        parse_files(
            s3=s3,
            s3_fs=s3_fs,
            source_prefix=os.path.join(f"{s3_bucket_path}/{source_prefix}", feed_id),
            destination_prefix=os.path.join(
                f"{s3_bucket_path}/{destination_prefix}", feed_id
            ),
            start_date=start_date,
            state_file=state_file,
        )
        time.sleep(interval)


if __name__ == "__main__":
    main()
