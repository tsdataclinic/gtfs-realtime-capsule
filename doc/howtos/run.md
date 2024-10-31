# How to run the scraper and normalizer
## Prerequisite
1. Update [config/global_config.json](../../config/global_config.json) to include related credentials.
   1. Update uri, public_key and secret_key for your own s3 bucket
   2. Add your mobilitydatabase token
2. Make sure the implementation and metadata json of the feed you want to scrape is under [src/scraper/feeds/](../../src/scraper/feeds/)
3. Install [docker compose](https://docs.docker.com/compose/install/) in order to run via docker compose (_[make sure docker daemon is started](https://docs.docker.com/engine/daemon/start/)_)
## Run via docker compose (recommended)
We have created 2 make command to help you run both scraper and normalizer easily against any feed: 
```shell
pwd  # make sure you are at repo root directory 
make local-prod-generate-compose FEEDS="YOUR_FEED_1 YOUR_FEED_2 YOUR_FEED_3"  # this will generate the docker-compose.yml against requested feeds
# To run for all avilable feeds:
# make local-prod-generate-compose FEEDS="*"

make local-prod-run  # this will start containers defined in docker-compose.yml
```

## Run locally (alternative)
### Scraper
```shell
python3 src/scraper/scrape.py --help  # help for optional flags
python3 src/scraper/scrape.py -f YOUR_FEED
```
### Normalizer
```shell
python3 src/normalize/normalize.py --help  # help for optional flags
python3 src/normalize/normalize.py -f YOUR_FEED
```