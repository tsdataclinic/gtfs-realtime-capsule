import datetime as dt
import logging
import os.path
import time

import click
import s3fs
import structlog
from dateutil import parser

from parquet_utils import compact
from norm_utils import (
    update_last_processed_timestamp,
    validate_date,
    get_last_processed_timestamp,
    load_config,
)
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


def _s3_prefix_exists(bucket, key, s3) -> bool:
    return "CommonPrefixes" in s3.list_objects(
        Bucket=bucket, Prefix=key, Delimiter="/", MaxKeys=1
    )


def compact_files(
    s3,
    s3_fs,
    normalized_prefix,
    compacted_prefix,
    start_date,
    normalized_state_file,
    compacted_state_file,
):
    dataset_bucket, dataset_key = normalized_prefix.replace("s3://", "").split("/", 1)
    normalized_state_bucket, normalized_state_key = normalized_state_file.replace(
        "s3://", ""
    ).split("/", 1)
    compact_state_bucket, compact_state_key = compacted_state_file.replace(
        "s3://", ""
    ).split("/", 1)

    last_normalized_time = get_last_processed_timestamp(
        s3, normalized_state_bucket, normalized_state_key
    )
    if not last_normalized_time:
        LOGGER.info(
            f"No last normalized time for {normalized_prefix} at {normalized_state_file}. Sleeping"
        )
        return
    last_compact_time = get_last_processed_timestamp(
        s3,
        compact_state_bucket,
        compact_state_key,
    )
    if last_compact_time:
        LOGGER.info(f"Loaded last_processed timestamp of {last_compact_time}")
    else:
        LOGGER.info(
            f"No compact state information found at {compacted_state_file},"
            f" defaulting `last_processed={start_date}"
        )
        last_compact_time = parser.parse(start_date)

    cur_processing = last_compact_time
    while cur_processing < last_normalized_time.date():
        for message_type in ["trip-updates", "vehicles", "alert"]:
            message_type_prefix = os.path.join(normalized_prefix, message_type)
            if _s3_prefix_exists(
                dataset_bucket, os.path.join(dataset_key, message_type), s3
            ):
                LOGGER.info(
                    f"Compacting partition {cur_processing.date()} for {message_type} in {message_type_prefix}"
                )
                compact(s3_fs, message_type_prefix, compacted_prefix, cur_processing)
        cur_processing = (cur_processing + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        LOGGER.info(
            f"Updating last compacted timestamp to "
            f"last date processed: {cur_processing.timestamp()}"
        )
        update_last_processed_timestamp(
            s3, compact_state_bucket, compacted_state_file, cur_processing.timestamp()
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
    "--normalized-prefix",
    type=str,
    default="norm",
    help="S3 prefix with normalized data (e.g., s3://bucket/prefix)",
)
@click.option(
    "--compacted-prefix",
    type=str,
    default="norm",
    help="S3 prefix for compacted data (e.g., s3://bucket/prefix)",
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
    "--normalized-state-file",
    type=str,
    help="S3 path of normalizer state file (e.g., s3://bucket/state.json)",
)
@click.option(
    "--compacted-state-file",
    type=str,
    help="S3 path of compacter state file (e.g., s3://bucket/state.json)",
)
@click.option(
    "--interval", type=int, default=3600, help="Run interval in seconds (default: 3600)"
)
def main(
    feed_id,
    config_path,
    normalized_prefix,
    compacted_prefix,
    start_date,
    normalized_state_file,
    compacted_state_file,
    interval,
):
    config = load_config(config_path)
    s3_bucket_path = f"s3://{config['s3_bucket']['uri']}"
    if not normalized_state_file:  # set default
        normalized_state_file = f"{s3_bucket_path}/state/normalize/{feed_id}"
    if not compacted_state_file:  # set default
        compacted_state_file = f"{s3_bucket_path}/state/compact/{feed_id}"

    s3 = create_s3_client(config["s3_bucket"])
    s3_fs = s3fs.S3FileSystem(
        key=config["s3_bucket"]["public_key"], secret=config["s3_bucket"]["secret_key"]
    )
    while True:
        compact_files(
            s3=s3,
            s3_fs=s3_fs,
            normalized_prefix=os.path.join(normalized_prefix, feed_id),
            compacted_prefix=os.path.join(compacted_prefix, feed_id),
            start_date=start_date,
            normalized_state_file=normalized_state_file,
            compacted_state_file=compacted_state_file,
        )
        time.sleep(interval)


if __name__ == "__main__":
    main()
