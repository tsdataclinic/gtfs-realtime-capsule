# How to implement your feeds
## Choose your feed ID
Within the project scope, feed ID is used to locate the implementation python file under [src/scraper/feeds](../../src/scraper/feeds) and metadata json file in [config/feeds](../../config/feeds).
### ID specification
* Every ID should be unique.
* It must not contain underscore `_`. Use `-` instead
* Suggested to match the ID in [mobilitydatabase](https://mobilitydatabase.org/feeds?gtfs_rt=true) if your feed is defined in their database already.

## Setup metadata file
Metadata file must be named as `{FEED-ID}.json` and placed under [config/feeds](../../config/feeds).

While there is no constraints to fields in the json file, it is suggested to follow [mobilitydatabase](https://mobilitydatabase.org/)'s schema.
If your feed exists in their database, their [api](https://mobilitydata.github.io/mobility-feed-api/SwaggerUI/index.html#/feeds/getFeed) endpoint will return the json file which you can just copy and paste.

## Implement the logic
Implementation python file must be named as `{FEED-ID}.py` and placed under [src/scraper/feeds](../../src/scraper/feeds).

You must define a class with following specification
* inherit [src/scraper/feeds](../../src/scraper/feeds/feed.py)
* class name must be same as the feed ID, in capitalized letter and underscore `_` instead of `-`. 
* implement `def __init__(self):`
* implement `def scrape(self):` which return the scraped binary result