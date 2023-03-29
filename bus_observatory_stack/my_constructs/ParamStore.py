# HOWTO manage parameter store settings
# https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html

import json
from constructs import Construct

from aws_cdk import (
    aws_ssm as ssm,

)

class BusObservatoryParamStore(Construct):
    def __init__(
            self, 
            scope: Construct, 
            id: str,
            stack_config: dict,
            region: str, 
            **kwargs):
        super().__init__(scope, id, **kwargs)

        bucket_name = stack_config['bucket_name']
        feeds = stack_config['feeds']
        
        #TODO: make sure this overwrites existing values
        #Create SSM parameter for each feed
        for system_id, feed_config in feeds.items():
            ssm.StringParameter(
                self, f"{bucket_name}-{system_id}",
                parameter_name=f"/{bucket_name}/feeds/{system_id}",
                string_value=json.dumps(feed_config),
                tier=ssm.ParameterTier.STANDARD,
            )
