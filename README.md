# GTFS-Realtime-Capsule
**gtfs-realtime-capsule** is a command-line tool that scrapes, normalizes, and archives real-time public transit data. Inspired by the [BusObservatory API](https://api.busobservatory.org/) by Prof. Anthony Townsend of [Jacobs Urban Tech Hub at Cornell Tech](https://urban.tech.cornell.edu/), the goal of this project is to make it seamless for anyone to help archive realtime transit data and analytics and make it publicly available though a distributed database. 

## Table of Contents

- [📖 Table of Contents](#table-of-contents)
- [❔ About](#about)
- [🚀 Getting Started](#getting-started)
  - [Requirements](#requirements)
  - [Clone the Project](#clone-the-project)
  - [Config](#config)
  - [Run via Docker Compose](#run-via-docker-compose)
  - [Verify Scraped Data](#verify-scraped-data)
- [🔨 Development](#development)
  - [Tech Stack](#tech-stack)
  - [Local Development Setup](#local-development-setup)
  - [Add a new feed](#how-to-scrape-a-new-feed)
- [Support](#support)
- [✨ Roadmap](#roadmap)
- [Contributing](#contributing)
- [👤 Authors](#authors)
- [🤝 Credits](#credits)
- [💛 Support](#support)
- [⚖️ Disclaimer](#disclaimer)
- [📃 License](#license)


## About

[GTFS Realtime](https://gtfs.org/documentation/realtime/reference/) is an extension of the GTFS format that allows transit agencies to share live updates about their services, including delays, vehicle locations, and service disruptions. It is used by Google Maps for realtime updates on transit schedules, including delays, cancellations, and changes in arrival and departure times. Raw GTFS-realtime data parsed from the New York City's ACE Subway Lines feed is available at [example_mta_ace_subway.txt](data/example_mta_ace_subway.txt).

It is a rich dataset, however the feeds are ephemeral. With each update, the feed is overwritten by current transit data and historical data is not available. **GTFS-Realtime-Capsule** solves this problem by scraping, normalizing and archiving feeds as they update.

- **Scraping**: Collect live transit data from various sources.
- **Normalization**: Standardize data formats for consistency and ease of use.
- **Archiving**: Store historical data for future analysis and reporting.

## Getting Started

### Requirements
- Ensure you have [Git](https://git-scm.com/) installed on your machine.
- Create an [Amazon S3](https://aws.amazon.com/s3/) bucket and save your public and secret key.
- Download and install [Docker](https://docs.docker.com/engine/install/).
- Download and install [Docker Compose](https://docs.docker.com/compose/install/).
- Request an API key from [Mobility Database](https://mobilitydatabase.org/).
- Install `make`.

### Clone the Project
1. Open your command prompt or terminal.
1. Clone the repository:
    ```shell
    git clone https://github.com/tsdataclinic/gtfs-realtime-capsule.git
    ```
1. Navigate to the project directory and ensure you're on the main branch:
    ```shell
    cd gtfs-realtime-capsule
    git branch  # Ensure you're on the main branch
    ```
1. Start the [docker daemon](https://docs.docker.com/engine/daemon/start/).


### Config

Update the global config file.
1. Copy [config/global_config.json.sample](config/global_config.json.sample) to config/global_config.json
1. Open the [config/global_config.json](config/global_config.json) in your file editor.
1. Update the `s3_bucket.uri` field to the uri of your Amazon S3 bucket.
1. Update the `s3_bucket.public_key` field to the public key of your Amazon S3 bucket.
1. Update the `s3_bucket.secret_key` field to the secret key of your Amazon S3 bucket.
1. Update the `endpoint_url` field to the endpoint url of your S3 bucket destination. This field is only necessary if you are not using AWS.
1. Update the `signature_version` field to the signature version of your S3 bucket. This field is only necessary if you are not using AWS.
1. Update the `mobilitydatabase.token` field to the API key you requested from [Mobility Database](https://mobilitydatabase.org/).


### Run via Docker Compose

The recommended way to run the project is with Docker Compose. In this example we will scrape the GTFS-realtime feed for the New York City's Subway ACE lines. The feed id is `mdb-1630`. Feed metadata is provided by [Mobility Database](https://mobilitydatabase.org/feeds/mdb-1630).

1. Open your command prompt or terminal.
1. Ensure you are on the root project directory.
```shell
pwd  # make sure you are at repo root directory 
```
1. Generate the `docker-compose.yml` for the mdb-1630 GTFS-realtime feed.
```
make local-prod-generate-compose FEEDS="mdb-1630"  # space separated list of feed ids
```
1. Start the application.
```
make local-prod-run  # this will start containers defined in docker-compose.yml
```

### Verify Scraped Data

Check that the scraper and normalizer is running correctly. Check the Amazon S3 bucket for new files. TODO: Expand here on how to ensure everything is working as intended.

## Development

### Tech Stack

The GTFS Realtime data exchange format is based on [Protocol Buffers](https://protobuf.dev/).

TODO: Expand on the architecture of the project.
- Two components
  - Scraper
    - Read protobufs from the transit agency API endpoint
    - Save raw protobufs to the S3 bucket
  - Normalizer
    - Parse raw protobufs from the S3 bucket
    - Convert data to parquet format

### Local Development Setup

[How to start local development Docker container](doc/howtos/docker.md)

[How to run scraper and normalizer locally](doc/howtos/run.md)

### How to scrape a new feed

Instructions for implementing your custom feeds. [How to implement your feeds](doc/howtos/develop.md)

## Support

[Common Errors](doc/common_errors.md): Address common queries and troubleshooting tips.

For other questions or support, please create an issue.

## Roadmap

### Improve Documentation

Improve documentation.

## Contributing

We welcome contributions! Please see our [contributing guidelines](link-to-contributing.md) for more information.

## Authors

This project was created by Two Sigma Data Clinic volunteers.

## Credits

TODO: Fill this out with third party software used, and prior work done. Reference TS Data Clinic.

## Disclaimer

TODO: Do we need a legal disclaimer here?

## License

This project is licensed under the Apache License - see the [LICENSE](./LICENSE) file for details.
