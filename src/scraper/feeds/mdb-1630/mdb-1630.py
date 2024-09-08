from src.scraper.feeds.feed import Feed, generic_no_auth_scrape


class MDB_1630(Feed):

    def __init__(self):
        feed_json = self.load_feed_json()
        self.api_url = feed_json["source_info"]["producer_url"]

    def scrape(self):
        generic_no_auth_scrape(self.api_url)
