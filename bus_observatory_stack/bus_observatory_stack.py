from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct

from bus_observatory_stack.my_constructs.ParamStore import BusObservatoryParamStore
from bus_observatory_stack.my_constructs.Crawler import BusObservatoryCrawler
from bus_observatory_stack.my_constructs.Grabber import BusObservatoryGrabber
from bus_observatory_stack.my_constructs.Compactor import BusObservatoryCompactor
from bus_observatory_stack.my_constructs.API import BusObservatoryAPI

#FIXME: add termination protection when time to deploy to production
class BusObservatoryStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            stack_config: dict,
            **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)


        ###########################################################
        # S3 BUCKET
        ###########################################################
        bucket_name=stack_config["bucket_name"]
        bucket = s3.Bucket(
            self, 
            "BusObservatory_S3_Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name=bucket_name
            )
        
        ###########################################################
        # PARAMETER STORE
        # load the config from bus_observatory_stack/config/feeds.json and store it in parameter store
        ###########################################################
        paramstore = BusObservatoryParamStore(
            self,
            "BusObservatoryParamStore",
            stack_config=stack_config,
            region=self.region
        )
        paramstore.node.add_dependency(bucket)

        ###########################################################
        # SCHEDULED GRABBERS
        # create the lambda and configure scheduled event
        # for each feed
        ###########################################################
        grabber = BusObservatoryGrabber(
            self,
            "BusObservatoryGrabber",
            stack_config=stack_config,
            region=self.region,
            bucket=bucket
        )
        grabber.node.add_dependency(bucket)

        ##########################################################
        # CRAWLER
        ###########################################################
        crawler = BusObservatoryCrawler(
            self,
            "BusObservatoryCrawler",
            stack_config=stack_config,
            region=self.region
        )
        crawler.node.add_dependency(bucket)

        ##########################################################
        # COMPACTOR
        ###########################################################
        compactor = BusObservatoryCompactor(
            self,
            "BusObservatoryCompactor",
            stack_config=stack_config,
            region=self.region,
            bucket=bucket
        )
        compactor.node.add_dependency(crawler)

        # # ##########################################################
        # # API
        # # lambda handler
        # # gateway
        # # custom domain
        # # ##########################################################
        
        # api = BusObservatoryAPI(
        #     self,
        #     "BusObservatoryAPI",
        #     stack_config=stack_config,
        #     region=self.region,
        #     bucket=bucket
        #     )
    