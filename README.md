# BusObservatory-Stack

## February 2023

This is a prototype fully-managed stack to replace the existing collection of SAM lambdas and independently managed reosurces (S3, EventBridge rules, Route53 records, Glue crawlers and databases etc.)

There are 3 main design goals:
1. to simplify and unify adminstration of the entire infrastructure
2. to implememt Lake Formation governed tables to automatically compact data lakes
3. to standardize on collection of UTM timestamps, with localization in the API
4. simplify addition of new feeds (ideally, be able to implement a simple web-based editor?)

The goal is to complete in Spring 2023 and migrate the existing data lakes over the summer.

### How to test local lambdas
- more info here https://stackoverflow.com/questions/64689865/debugging-lambda-locally-using-cdk-not-sam
- embed a static test event and just pass it

### how to view logs for lambdas

1. get list of log groups `awslogs groups`
2. find the one that corresponds to the Stack ARN (output of `cdk deploy`)
3. tail and follow the log group `aws logs tail --follow {group}`

### resources

AWS Solutions Constructs https://docs.aws.amazon.com/solutions/latest/constructs/aws-eventbridge-lambda.html



## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
* `cdk destroy`      remove the stack and all associated resources (non-empty S3 buckets wont be deleted!)

