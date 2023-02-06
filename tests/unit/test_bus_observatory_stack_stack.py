import aws_cdk as core
import aws_cdk.assertions as assertions

from bus_observatory_stack.bus_observatory_stack import BusObservatoryStackStack

# example tests. To run these tests, uncomment this file along with the example
# resource in bus_observatory_stack/bus_observatory_stack_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BusObservatoryStackStack(app, "bus-observatory-stack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
