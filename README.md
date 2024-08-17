# gtfs-realtime-capsule
Tool to archive GTFS-rt data

# Local development environment setup via docker
After installing docker on your system:
```shell
make local-dev-build
make local-dev-run
# you are now in shell in the docker container
# if you want to shell back in after exiting:
make local-dev-shell
# if you want to tear down local dev env:
make local-dev-down
```

# Run the scraper
Run the scrape.py script.

```bash
python scrape.py
```

An example is included in `example_mta_subway.txt`.
