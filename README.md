
###### Febuary 2023
# BusObservatory-Stack 

# TO-DOs

## high priority

1. figure out a compaction solution (see below)
    1. lake formation
    2. prepend and batch process
    3. delta lake
2. remove all secrets so i can publish the code
3. Athena results bucket setup needs fixxing
    - right now the API is using a pre-existing athena bucket to temp hold the results of queries before `pythena` cleans them up (`arn:aws:s3:::aws-athena-query-results-870747888580-us-east-1`)
        - this is hardcoded in `my_lambdas/lambda_API/helpers.py`
    - to fix:
        - create a bucket in `my_constructs/API.py` using a dynamic name like `f"{bucket_name}-results"`
        - create a new Athena workgroup, setting the default query results for that workgroup to the
            - see https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_athena/CfnWorkGroup.html
        - make sure the crawler and lakeformation and the rest use this workgroup
        - grant the `my_handler` lambda `s3:*` on the resource `f"arn:aws:s3:::{bucket_name}-results"` and `f"arn:aws:s3:::{bucket_name}-results/*"`
        - in `my_lambdas/lambda_API/helpers.py` queries will automatically use this

## low priority

3. secure API-- see https://pypi.org/project/aws-cdk-secure-api/#
3. speed up large queries by migrating to boto3 vs pythena (https://medium.com/codex/connecting-to-aws-athena-databases-using-python-4a9194427638)


# COMPACTION SOLUTIONS

1. Lake Formation (`dev/governedtable` branch)
    1. whatever solution the AWS people have
    2. using awswrangler
        - watch  https://www.youtube.com/watch?v=DglRcUrqvNo
        - read https://aws-sdk-pandas.readthedocs.io/en/stable/#
        - potential solution = iterate over the feeds and create the governed tables in Lake.py using awswrangler
2. batch compaction
    1. update `Grabber` to prepend `incoming_` to all parquet files
    2. write a compaction lambda to:
        - glob that list of those
        - concatenate them and write them to a new single parquet
        - delete the globbed file list
3. DeltaLake (`dev/deltalake` branch)
    1. delete Lake Formation construct
    2. update Glue crawlers https://aws.amazon.com/blogs/big-data/introducing-native-delta-lake-table-support-with-aws-glue-crawlers/
    3. rewrite `Datalake` class in `my_lambdas/lambda_API/app.py` especially the `dump_buses` method to write as a DeltaLake insert instead of a raw parquet
        - using duckdb https://stackoverflow.com/questions/69407302/how-to-write-to-delta-table-delta-format-in-python-without-using-pyspark
        - or in Rust with delta-rs https://www.confessionsofadataguy.com/delta-lake-without-spark-delta-rs-innovation-cost-savings-and-other-such-matters/
        - or using pyspark running in a Lambda container
            - https://plainenglish.io/blog/spark-on-aws-lambda-c65877c0ac96
            - https://medium.com/geekculture/running-serverless-spark-applications-with-aws-lambda-d7e25795ec1d
            - https://dev.to/aws-builders/spark-as-function-containerize-pyspark-code-for-aws-lambda-and-amazon-kubernetes-1bka
        - using polars (read-only :( https://github.com/pola-rs/polars/issues/2858) https://delta.io/blog/2022-12-22-reading-delta-lake-tables-polars-dataframe/)
    4. write a new lambda in `my_constructs/Lake.py` to do compaction once a day
        - using delta lake python api (requires pyspark?) https://docs.delta.io/latest/optimizations-oss.html#-delta-optimize&language-python
        - run inside in a spark lambda container? or maybe a bigger EKS container?






## Description
This is a prototype fully-managed stack to replace the existing collection of SAM lambdas and independently managed reosurces (S3, EventBridge rules, Route53 records, Glue crawlers and databases etc.)

There are 3 main design goals:
1. to simplify and unify adminstration of the entire infrastructure
2. to implememt Lake Formation governed tables to automatically compact data lakes
3. to standardize on collection of UTM timestamps, with localization in the API
4. simplify addition of new feeds (ideally, be able to implement a simple web-based editor?)

The goal is to complete in Spring 2023 and migrate the existing data lakes over the summer.

## How to test local lambdas
- more info here https://stackoverflow.com/questions/64689865/debugging-lambda-locally-using-cdk-not-sam
- embed a static test event and just pass it

## how to view logs for lambdas

1. get list of log groups `awslogs groups`
2. find the one that corresponds to the Stack ARN (output of `cdk deploy`)
3. tail and follow the log group `aws logs tail --follow {group}`

## resources

- AWS Solutions Constructs https://docs.aws.amazon.com/solutions/latest/constructs/aws-eventbridge-lambda.html

# How Configuration is handled

## At deployment
- `feeds.json` is loaded from the local disk
- Lambda grabber events are configured using this data
- the same feed config data is stored in an SSM Parameter with the format `/bucket-name/feeds/system-id` e.g. `/busobservatory-2/feeds/nyct_mta_bus_siri`

### For the Grabber
- the config for each feed is hard-coded in its lambda event at deployment

### For the API
- the config is read from the parameter store on each invocation


# Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
* `cdk destroy`      remove the stack and all associated resources (non-empty S3 buckets wont be deleted!)

# Troubleshooting Deploy Errors

Don't forget to add your local cdk role (the one created by cdk bootstrap) to LakeFormation data lake admins.