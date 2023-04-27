
Updated April 2023

# BusObservatory-Stack 

## Overview 

Open transit data has been around for a decade. But most of this information is not publicly archived, preventing transit researchers and advocates from conducting long-term studies of transit performance and other related issues.

To fill this gap, this repo describes a single, easily-deployed AWS CDK stack that can scape any numnber of transit data feeds, efficiently store them in a data lake, and provide an API for programmatic retrieval of the archived data.

## Stack

The Bus Observatory stack is split into several parts (each is defined in a separate module in `./busobservatory_stack/my_constructs/`):

- **ParamStore** (`ParamStore.py`) — On deployment and any subsequent updates, stack configuration is read and stored from a local file and saved in an AWS Parameter Store for all other components to access. This can be used to securely store API keys and other sensitive information. However, the config file should NOT be committed into the repo. (More info below)
- **Grabber** (`Grabber.py`) — This set of constructs deploy a single, configurable Lambda and define a scheduled event for each feed to fetch, parse, and save real-time transit feeds into an S3 data lake.
- **Compactor** (`Grabber.py`) - Deploys a Lambda function and a scheduled event for each feed to concatenate and save, and remove the consumed files, to compact each day's data into a single larger file.
- **Crawler** (`Grabber.py`) - Deploys a single crawler for the data lake to create an AWS Glue and one table per feed, which runs every 30 minutes.
- **API** (`Grabber.py`) - Deploys a REST API using a custom domain, with requests handled by a Lambda function running FastAPI. This Lambda also serves a small web site to provide basic information.

## Configuration

Configuration works in the following way:
- `bus_observatory_stack/config/feeds.json` is loaded from the local disk
- the same feed config data is stored in an SSM Parameter with the format `/bucket-name/feeds/system-id` e.g. `/busobservatory-2/feeds/nyct_mta_bus_siri`
- each grabber Lambda event is configured with its config hard-coded on deployment
- the API lambda reads the parameter store on each invocation

### Stack Config
The basic format of the config file (`./config/stack_config.json`) is:

```
{
	"bucket_name": "busobservatory-lake",
	"subdomain": "api",
	"domain": "busobservatory.org",
	"feeds": {
        ...
        }
```

- *bucket_name* - a valid, unique S3 bucket name. This bucket will be created.
- *subdomain* - the hostname for the API site
- *domain* - the domain for the API site (web address will be https://subdomain.domain). The domain must exist as a hosted zone in AWS Route53 prior to deployment.

### Feed Config

Each feed to be archived should have a unique key:value pair within the "feeds" dict. Feed configuration is complex, given the different types of feeds and individual requirements of each feed API in terms of expected headers. API keys may need to be obtained from transit agency feed providers. These will be stored securely in an AWS Parameter Store. This file should NOT be committed to a public copy of this repository.

Key settings to review:
- `"feed_type"` selects the parsed used. Valid values are `gtfsrt, siri, njxml`
- Feeds tagged `"publish":"False"` will not be available in the API.
- `"notes"` is displayed in the API website's feed listing.


```
# A GTFS-RT feed with an API key

"tfnsw_bus": {
    "publish": "True",
    "system_name": "Transport for New South Wales",
    "city_name": "Sydney, NSW, AU",
    "feed_type": "gtfsrt",
    "url": "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses",
    "api_key": "abcd1234",
    "header": "True",
    "header_format": {
        "key_name": "Authorization",
        "template": "apikey {key_value}"
    },
    "route_key": "vehicle.trip.route_id",
    "timestamp_key": "vehicle.timestamp",
    "tz": "Australia/Sydney",
    "notes": "Sampled once per minute. We parse all fields in this feed."
}

# A GTFS-RT feed with an API key but a different header format

"wmata_bus": {
    "publish": "True",
    "system_name": "Washington Metropolitan Area Transit Authority",
    "city_name": "Washington, DC, US",
    "feed_type": "gtfsrt",
    "url": "https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb",
    "api_key": "abcd1234",
    "header": "True",
    "header_format": {
        "key_name": "api_key",
        "template": "abcd1234"
    },
    "route_key": "vehicle.trip.route_id",
    "timestamp_key": "vehicle.timestamp",
    "tz": "America/New_York",
    "notes": "Sampled once per minute. We parse all fields in this feed."
}


# A GTFS-RT field WITHOUT an API key

"mbta_all": {
    "publish": "True",
    "system_name": "Massachusetts Bay Transit Authority",
    "city_name": "Boston, MA, US",
    "feed_type": "gtfsrt",
    "url": "https://cdn.mbta.com/realtime/VehiclePositions.pb",
    "header": "False",
    "route_key": "vehicle.trip.route_id",
    "timestamp_key": "vehicle.timestamp",
    "tz": "America/New_York",
    "notes": "Sampled once per minute, inlcudes buses and trolleys. We parse all fields in this feed."
}


# A SIRI feed with an API key

"nyct_mta_bus_siri": {
    "publish": "True",
    "system_name": "New York City Transit (SIRI)",
    "city_name": "New York City, NY, US",
    "feed_type": "siri",
    "url": "http://gtfsrt.prod.obanyc.com/vehiclePositions?key={}",
    "api_key": "abcd1234",
    "header": "False",
    "route_key": "route",
    "timestamp_key": "timestamp",
    "tz": "America/New_York",
    "notes": "Sampled once per minute. We parse all fields in this feed."
}


# A Clever Devices XML feed

"njtransit_bus": {
    "publish": "True",
    "system_name": "NJTransit",
    "city_name": "NJ, US",
    "feed_type": "njxml",
    "url": "http://mybusnow.njtransit.com/bustime/map/getBusesForRouteAll.jsp",
    "header": "False",
    "route_key": "rt",
    "timestamp_key": "timestamp",
    "tz": "America/New_York",
    "notes": "Sampled once per minute. This feed is based on an old technology and returns an XML response. We parse most of the fields in this feed, but most of them are undocumented."
}
```

# Data

## timestamps
- GTFS-RT feeds are stored in UTC time.
- NY and NJ seem to be local


# Deployment

## Synth

Run `cdk synth` to generate all of the assets locally. Docker must be running.

## Deploy

Run `cdk deploy` to upload all the assets and create the stack in the AWS cloud. When its done, wait a minute for the first grab to run, and then try to access the API at `https://subdomain.domain`

## Update

Run `cdk diff` to list changes and then `cdk deploy` to update the stack. This should rebuild any Lambdas and if you added feeds to the config, it will generate new services and assets for all the new feeds.

## Debugging

Most errors are caused by either the Grabber or API Lambda functions. To access error logs, find the log group id by clicking through `CloudFormation / the stack / Resources / Grabber / the Lambda / the lambda function / Montior / CloudWatch logs` and tail it, e.g.:
- `aws logs tail --follow /aws/lambda/BusObservatory-busobserva-BusObservatoryGrabberBus-4yDcnrtj3nf`

Alternately:
- get list of log groups `awslogs groups` (requires installation of `awslogs`)
- find the one that corresponds to the Stack ARN (output of `cdk deploy`)
- tail and follow the log group `aws logs tail --follow {group}`



# Known Issues

## major
- the GTFS-RT grabber is lazy and often writes parquet files with numeric fields encoded as `int` rather than `double`. This causes problems for AWS Glue. Any query that tries to fetch results contained in one of these files will cause an error.

## minor
- the API can't serve images. This is related to the wrapper (`mangum`) used to handle the FastApi script.
- the Athena results bucket setup needs fixxing
    - right now the API is using a pre-existing athena bucket to temp hold the results of queries before `pythena` cleans them up (`arn:aws:s3:::aws-athena-query-results-870747888580-us-east-1`)
        - this is hardcoded in `my_lambdas/lambda_API/helpers.py`
    - to fix:
        - create a bucket in `my_constructs/API.py` using a dynamic name like `f"{bucket_name}-results"`
        - create a new Athena workgroup, setting the default query results for that workgroup to the
            - see https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_athena/CfnWorkGroup.html
        - make sure the crawler and lakeformation and the rest use this workgroup
        - grant the `my_handler` lambda `s3:*` on the resource `f"arn:aws:s3:::{bucket_name}-results"` and `f"arn:aws:s3:::{bucket_name}-results/*"`
        - in `my_lambdas/lambda_API/helpers.py` queries will automatically use this

# Development

Testing the lambdas locally is a big PITA
    
- more info here https://stackoverflow.com/questions/64689865/debugging-lambda-locally-using-cdk-not-sam


## replace pythena query execution with boto3
- speed up large queries by migrating to boto3 vs pythena (https://medium.com/codex/connecting-to-aws-athena-databases-using-python-4a9194427638)

## secure the API
- see https://pypi.org/project/aws-cdk-secure-api/#
- see https://www.freecodecamp.org/news/how-to-add-jwt-authentication-in-fastapi/
- or webauthn?

## implement tests
-  https://docs.aws.amazon.com/cdk/v2/guide/testing.html
