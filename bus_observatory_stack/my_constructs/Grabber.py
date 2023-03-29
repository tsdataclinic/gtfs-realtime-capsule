from constructs import Construct

from aws_cdk import (
    Duration,
    aws_iam as iam,
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
            stack_config: dict,
            region: str, 
            bucket, 
            **kwargs):

        super().__init__(scope, id, **kwargs)

        feeds=stack_config['feeds'] 
        
        # CREATE THE GRABBER LAMBDA
        # this will build and package an env using entry folder requirements.txt without need for layers

        handler = _lambda_alpha.PythonFunction(
            self,
            "BusObservatoryStack_Grabber_Lambda",
            entry="bus_observatory_stack/my_lambdas/lambda_Grabber",
            runtime=_lambda.Runtime.PYTHON_3_8,
            index="app.py",
            handler="handler",
            timeout=Duration.seconds(60),
        )

        #grant write access to handler on source bucket
        bucket.grant_read_write(handler.role)

        # CONFIGURE SCHEDULED EVENTS

        for system_id, feed_config in feeds.items():

            event_input = {
                "region": region,
                "bucket_name" : bucket.bucket_name,
                "system_id" : system_id,
                "feed_config" : feed_config
            }

            # create a named rule for each feed, runs every 1 minute
            events.Rule(
                self, 
                f"BusObservatory_Grabber_Rule_{system_id}",
                schedule=events.Schedule.rate(Duration.minutes(1)),
                targets = [
                    targets.LambdaFunction(
                        handler,
                        event=events.RuleTargetInput.from_object(event_input)
                        )
                    ],
                description=f"BusObservatoryStack Grabber Rule for {system_id}"
            )
