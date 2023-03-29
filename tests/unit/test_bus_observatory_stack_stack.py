import json, os
import aws_cdk as core
import aws_cdk.assertions as assertions

from bus_observatory_stack.bus_observatory_stack import BusObservatoryStack

#FIXME: this works here, but then fails in the test when invoking a module that this relative path doesnt work for
stack_config = json.load(open("../bus_observatory_stack/config/stack_config.json"))

#TODO: figure out how to set env vars in pytest
# env=core.Environment(
#     account=os.environ["CDK_DEFAULT_ACCOUNT"],
#     region=os.environ["CDK_DEFAULT_REGION"])
env = core.Environment(
    account="870747888580",
    region="us-east-1"
    )

# fine-grained tests
def test_s3_bucket_created():
    app = core.App()
    stack = BusObservatoryStack(
        app, 
        f"BusObservatory-{stack_config['bucket_name']}",
        env=env,
        bucket_name=stack_config['bucket_name']
        )
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketName": stack_config['bucket_name']
    })


'''
BusObservatoryStack(
    app, 
    f"BusObservatory_{stack_config['bucket_name']}",
    env=env,
    bucket_name=stack_config['bucket_name']
    )
'''