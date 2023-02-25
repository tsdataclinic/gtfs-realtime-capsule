#!/usr/bin/env python3
import os, json
import aws_cdk as cdk
from bus_observatory_stack.bus_observatory_stack import BusObservatoryStack

############### CONFIG
stack_config = json.load(open("bus_observatory_stack/config/stack_config.json"))

app = cdk.App()

env=cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"])

BusObservatoryStack(
    app, 
    f"BusObservatory-{stack_config['bucket_name']}",
    env=env,
    bucket_name=stack_config['bucket_name']
    )

app.synth()
