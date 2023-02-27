from constructs import Construct

from aws_cdk import (
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_alpha
)


class BusObservatoryCompactor(Construct):
    def __init__(self, scope: Construct, id: str, region: str, bucket, feeds: dict, **kwargs):

        super().__init__(scope, id, **kwargs)


        # CREATE THE COMPACTOR LAMBDA
        # this will build and package an env using entry folder requirements.txt without need for layers

        handler = _lambda_alpha.PythonFunction(
            self,
            "BusObservatoryStack_Compactor_Lambda",
            entry="bus_observatory_stack/my_lambdas/lambda_Compactor",
            runtime=_lambda.Runtime.PYTHON_3_8,
            index="app.py",
            handler="handler",
            timeout=Duration.seconds(300), 
            memory_size=2048
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
                f"BusObservatory_Compactor_Rule_{system_id}",
                schedule=events.Schedule.rate(Duration.hours(1)), #FIXME: change to 24 hours for production
                    targets = [
                        targets.LambdaFunction(
                            handler,
                            event=events.RuleTargetInput.from_object(event_input)
                            )
                        ],
                    description=f"BusObservatoryStack Compactor Rule for {system_id}"
                )
