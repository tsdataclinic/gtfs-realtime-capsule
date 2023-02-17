
###### Febuary 2023
# BusObservatory-Stack 

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