# gtfs-realtime-capsule
Tool to archive GTFS-rt data

# HOW-TOs
## How to start local development docker
See the [docker doc](docker/README.md)

## How to run the scraper and normalizer
### Prerequisite
1. Update `config/config.json` to include related credentials
2. Make sure the implementation and metadata json of the feed you want to scrape is in `src/scraper/feeds/` 
### Via docker compose
```shell
pwd
# need to run at repo root directory 
make local-prod-generate-compose FEEDS="YOUR_FEED_1 YOUR_FEED_2 YOUR_FEED_3"
# To run for all avilable feeds:
# make local-prod-generate-compose FEEDS="*"

# a dynamic docker-compose.yaml will be generated
make local-prod-run
```
