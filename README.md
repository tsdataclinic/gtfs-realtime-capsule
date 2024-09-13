# gtfs-realtime-capsule
Tool to archive GTFS-rt data

# HOW-TOs
## How to start local development docker
See the [docker doc](docker/README.md)

## How to run the scraper
### Prerequisite
1. Update `config/config.json` to include related credentials
2. Make sure the implementation and metadata json of the feed you want to scrape is in `src/scraper/feeds/` 
### Via docker
In `docker/prod/Dockerfile`, update the last `CMD` step with correct feed you want to scrape 

```shell
make local-prod-build
make local-prod-run
# you are now in shell in the docker container
# you can check the scraped files in 
ls /src/data/
```

To inspect scraper log on the computer running docker
```shell
docker logs -f local-prod
```
To store them locally:
```shell
docker logs -f local-prod &> prod_run.log &
```

### Locally on your computer
```shell
python3 /local/src/scraper/scrape.py -f YOUR_FEED
```

An example is included in `example_mta_subway.txt`.
