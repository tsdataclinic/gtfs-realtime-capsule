#!/usr/bin/env python3
import os
import aws_cdk as cdk
from bus_observatory_stack.bus_observatory_stack import BusObservatoryStack

############### CONFIG
bucket_name = "busobservatory-datalake-test"


app = cdk.App()

env=cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"])

BusObservatoryStack(
    app, 
    "BusObservatoryStack-Anthony-Test",
    env=env,
    bucket_name=bucket_name
    )

app.synth()
