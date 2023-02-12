#!/usr/bin/env python3
import os
import aws_cdk as cdk
from bus_observatory_stack.bus_observatory_stack import BusObservatoryStack

app = cdk.App()

env=cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"])

BusObservatoryStack(
    app, 
    "BusObservatoryStack",
    env=env,
    bucket_name="busobservatory-2"
    )

app.synth()
