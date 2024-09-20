from src.scraper.feeds.feed import Feed, generic_no_auth_header_scrape


class MDB_1630(Feed):

    def __init__(self):
        feed_json = self.load_feed_json()
        self.api_url = feed_json["source_info"]["producer_url"]

    def scrape(self):
        return generic_no_auth_header_scrape(self.api_url)
