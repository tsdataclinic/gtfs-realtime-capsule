import logging
import os
import time
from typing import Dict

import boto3
import click
import requests

import json
import structlog

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


def load_config(path: str):
    with open(path, 'r') as f:
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


def scrape(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as err:
        LOG.error(f"Failed to get response: {err}", url=url)


@click.command()
@click.option("-f", "--feed_id", required=True, type=str, help="feed ID to be scraped")
@click.option("-c", "--config_path", type=str, default=f"{CONFIG_DIR}/config.json", help="config.json path")
def main(feed_id, config_path):
    config = load_config(config_path)
    s3 = create_s3_client(config["s3_bucket"])
    url = ""
    for feed in config["feeds"]:
        if feed["id"] == feed_id:
            url = feed["source_info"]["producer_url"]
    if not url:
        raise ValueError(f"{feed_id} not found in {config_path}")
    LOG.info("Start scraping", s3_bucket=s3, url=url)

    while True:
        content = scrape(url)
        now = time.time()
        file_path = f'{config["feeds"][0]["feed_name"]}/{now}.bin'
        s3_file_path = f"raw/{file_path}"
        f = open(f"{DATA_DIR}/{file_path}", 'wb')
        f.write(content)
        s3.upload_file(f"{DATA_DIR}/{file_path}", s3_file_path)
        LOG.info(f"Scraped at {now}")
        time.sleep(60)


if __name__ == "__main__":
    main()
