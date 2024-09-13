from src.scraper.feeds.feed import Feed, generic_no_auth_header_scrape


class MDB_MTA_TRIP(Feed):

    def __init__(self):
        feed_json = self.load_feed_json()
        assert feed_json["source_info"]["api_key"], "API Key must be provided in config json"
        self.api_key = feed_json["source_info"]["api_key"]
        self.api_url = feed_json["source_info"]["producer_url"]

    def scrape(self):
        generic_no_auth_header_scrape(f"{self.api_url}?key={self.api_key}")
