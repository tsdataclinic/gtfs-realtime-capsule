import importlib
import logging
import os
import time
from datetime import datetime
from typing import Dict

import boto3
import click

import json
import structlog

from src.scraper.mobilitydatabase import get_access_token, get_feed_json

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", key="ts"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
LOG = structlog.get_logger()
SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_DIR = f"{SCRIPT_DIR}/../../config"
DATA_DIR = f"{SCRIPT_DIR}/../../data"


def check_config(config: Dict):
    assert config["s3_bucket"]["uri"]
    assert config["s3_bucket"]["public_key"]
    assert config["s3_bucket"]["secret_key"]

    assert config["mobilitydatabase"]["url"]
    assert config["mobilitydatabase"]["token"]


def load_config(path: str):
    with open(path, "r") as f:
        config = json.load(f)
        check_config(config)
        return config


def create_s3_client(s3_config: Dict):
    session = boto3.Session(
        aws_access_key_id=s3_config["public_key"],
        aws_secret_access_key=s3_config["secret_key"],
    )
    s3 = session.resource("s3").Bucket(s3_config["uri"])
    return s3


def scrape_loop(s3_client, feed_id: str):
    module = importlib.import_module(f"src.scraper.feeds.{feed_id}.{feed_id}")
    feed_class = getattr(module, feed_id.upper().replace("-", "_"))
    feed = feed_class()
    LOG.info("Start scraping", s3_bucket=s3_client)
    while True:
        content = feed.scrape()
        now = datetime.now()
        s3_file_path = f'raw/{feed_id}/{now.year}/{now.month}/{now.day}/{now.timestamp()}.binpb'
        s3_client.put_object(Body=content, Key=s3_file_path)
        LOG.info(f"Scraped at {now}")
        time.sleep(60)


def check_feed(feed_json_path: str, feed_id: str, mdb_url: str, mdb_token: str):
    assert os.path.exists(f"{SCRIPT_DIR}/feeds/{feed_id}/{feed_id}.py"), f"Implementation of {feed_id}.py is not found."
    if not os.path.exists(feed_json_path):
        LOG.warn(f"{feed_json_path} not found. Will fall back to query mobilitydatabase.")
        access_token = get_access_token(mdb_url, mdb_token)
        feed_json = get_feed_json(mdb_url, feed_id, access_token)
        f = open(feed_json_path, "wb")
        f.write(feed_json)
        LOG.info(f"Crawled feed json to {feed_json_path}")


@click.command()
@click.option("-f", "--feed_id", required=True, type=str, help="feed ID to be scraped")
@click.option(
    "-c",
    "--config_path",
    type=str,
    default=f"{CONFIG_DIR}/config.json",
    help="config.json path",
)
def main(feed_id, config_path):
    config = load_config(config_path)
    feed_json_path = f"{SCRIPT_DIR}/feeds/{feed_id}/{feed_id}.json"
    check_feed(feed_json_path, feed_id, config["mobilitydatabase"]["url"], config["mobilitydatabase"]["token"])
    s3 = create_s3_client(config["s3_bucket"])
    scrape_loop(s3, feed_id)


if __name__ == "__main__":
    main()
