import json
import logging
import os
from abc import ABC, abstractmethod

import requests
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


def generic_no_auth_header_scrape(url: str):
    # Generic scraping implementation for feed that
    # does not need auth in the request header
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as err:
        LOG.error(f"Failed to get response: {err}", url=url)
        return ""


class Feed(ABC):
    @abstractmethod
    def scrape(self):
        pass

    def load_feed_json(self):
        feed_id = self.__class__.__name__.lower().replace("_", "-")
        with open(
                f"{os.path.dirname(__file__)}/../../../"
                f"config/feeds/{feed_id}.json"
        ) as f:
            data = json.load(f)
        return data
