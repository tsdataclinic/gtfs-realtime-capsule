# CODE SOURCES
#
# https://catalog.us-east-1.prod.workshops.aws/workshops/697be460-9224-4b82-99e2-5103b900ed4e/en-US/030-build/034-code-walkthrough


from constructs import Construct

from aws_cdk import (
    Duration,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_alpha
)


class BusObservatoryGrabber(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        bucket: s3.Bucket,
        feeds: dict,
        **kwargs
    ):

        super().__init__(scope, id, **kwargs)

        # S3 Bucket is passed as 'bucket'

        # CREATE THE GRABBER LAMBDA
        # this will build and package an env using entry folder requirements.txt without need for layers

        handler = _lambda_alpha.PythonFunction(
            self,
            "TEST_BusObservatoryGrabber_Lambda",
            entry="bus_observatory_stack/my_lambdas/lambda_Grabber",
            runtime=_lambda.Runtime.PYTHON_3_8,
            index="app.py",
            handler="handler",
            timeout=Duration.seconds(60),
            environment=dict(
                DATALAKE_BUCKET=bucket.bucket_name
            ),
        )

        # grant write access to handler on source bucket
        bucket.grant_write(handler)

        # IS THIS NEEDED?
        # # Give the lambda resource based policy
        # # both source_arn and source_account is needed for security reason
        # handler.add_permission('s3-trigger-lambda-s3-invoke-function',
        #                       principal=iam_.ServicePrincipal('s3.amazonaws.com'),
        #                       action='lambda\:InvokeFunction',
        #                       source_arn=source_bucket.bucket_arn,
        #                       source_account=self.account)
        # # grant access to the handler
        # # - this is a lot easier than adding policies, but not all constructs support this
        # target_bucket.grant_read_write(handler)

        # CONFIGURE SCHEDULED EVENTS

        #TEST PARAMS -- Australian GTFS-RT feed

        test_feed = {
            "tfnsw_bus": {
                "publish": "True",
                "system_name": "Transport for New South Wales",
                "city_name": "Sydney, NSW, AU",
                "feed_type": "gtfsrt",
                "url": "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses",
                "api_key": "HTHniGwUwxSJoty8T3kQTtBtd9jxBl8QFyws",
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
            }
        feed = test_feed

        params = {
            "bucket_name" : bucket.bucket_name,
            "system_id" : next(iter(feed.keys())), # get the first (only) key
            "feed_config" : feed
        }

        # create a rule, runs every 1 minute
        rule = events.Rule(
            self, 
            "TEST_single_rule",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            targets = [
                targets.LambdaFunction(
                    handler,
                    event=events.RuleTargetInput.from_object(params)
                    )
                ]
        )


        #FIXME: now iterate over the feeds
        # events = []
        # for feed in feeds:
        #     #TODO: insert working code from above
        #     events.append(rule)
