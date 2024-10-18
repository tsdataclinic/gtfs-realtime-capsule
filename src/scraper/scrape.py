import importlib
import json
import logging
import os
import time
from datetime import datetime

import click
import structlog

from src.scraper.mobilitydatabase import get_access_token, get_feed_json
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


def check_config(config: dict):
    assert config["s3_bucket"]["uri"]
    assert config["s3_bucket"]["public_key"]
    assert config["s3_bucket"]["secret_key"]
    retries_config = config["s3_bucket"].get("retries")
    if retries_config:
        assert retries_config["mode"], "mode must be specified for enabling " "retry"

    assert config["mobilitydatabase"]["url"]
    assert config["mobilitydatabase"]["token"]


def load_config(path: str):
    with open(path, "r") as f:
        config = json.load(f)
        check_config(config)
        return config


def scrape_loop(s3_client, feed_id: str, s3_bucket: str):
    module = importlib.import_module(f"src.scraper.feeds.{feed_id}")
    feed_class = getattr(module, feed_id.upper().replace("-", "_"))
    feed = feed_class()
    LOGGER.info("Start scraping", s3_bucket=s3_bucket)
    while True:
        content = feed.scrape()
        if not content:
            LOGGER.warn("Got no content from scraping. Skipping this round.")
            time.sleep(60)
            continue
        now = datetime.now()
        s3_file_path = (
            f"raw/{feed_id}/{now.year}/{now.month}/{now.day}/"
            f"{now.timestamp()}.binpb"
        )
        s3_client.put_object(Body=content, Key=s3_file_path, Bucket=s3_bucket)
        LOGGER.info(f"Scraped at {now}")
        time.sleep(60)


def check_feed(feed_json_path: str, feed_id: str, mdb_url: str, mdb_token: str):
    assert os.path.exists(
        f"{SCRIPT_DIR}/feeds/{feed_id}.py"
    ), f"Implementation of {feed_id}.py is not found."
    if not os.path.exists(feed_json_path):
        LOGGER.warn(
            f"{feed_json_path} not found. " f"Will fall back to query mobilitydatabase."
        )
        access_token = get_access_token(mdb_url, mdb_token)
        feed_json = get_feed_json(mdb_url, feed_id, access_token)
        f = open(feed_json_path, "wb")
        f.write(feed_json)
        LOGGER.info(f"Crawled feed json to {feed_json_path}")


@click.command()
@click.option("-f", "--feed_id", required=True, type=str, help="feed ID to be scraped")
@click.option(
    "-c",
    "--config_path",
    type=str,
    default=f"{CONFIG_DIR}/global_config.json",
    help="json path to the global config",
)
def main(feed_id, config_path):
    config = load_config(config_path)
    feed_json_path = f"{CONFIG_DIR}/feeds/{feed_id}.json"
    check_feed(
        feed_json_path,
        feed_id,
        config["mobilitydatabase"]["url"],
        config["mobilitydatabase"]["token"],
    )
    s3 = create_s3_client(config["s3_bucket"])
    scrape_loop(s3, feed_id, config["s3_bucket"]["uri"])


if __name__ == "__main__":
    main()
