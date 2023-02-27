from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct
import json
import boto3

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
            bucket_name: str,
            **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)


        ###########################################################
        # S3 BUCKET
        ###########################################################
        bucket = s3.Bucket(
            self, 
            "BusObservatory_S3_Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name=bucket_name
            )

        ###########################################################
        # LOAD FEED CONFIG FROM DISK
        ###########################################################
        #FIXME: this is causing tests to fail due to different start dir for test execution
        # how to fix https://github.com/omarkohl/pytest-datafiles/issues/6
        feeds = json.load(open("bus_observatory_stack/config/feeds.json"))
        
        ###########################################################
        # PARAMETER STORE
        # load the config from bus_observatory_stack/config/feeds.json and store it in parameter store
        ###########################################################

        paramstore = BusObservatoryParamStore(
            self,
            "BusObservatoryParamStore",
            region=self.region,
            bucket_name=bucket_name,
            feeds=feeds
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
            region=self.region,
            bucket=bucket,
            feeds=feeds
        )
        grabber.node.add_dependency(bucket)

        ##########################################################
        # CRAWLER
        ###########################################################
        crawler = BusObservatoryCrawler(
            self,
            "BusObservatoryCrawler",
             region=self.region,
             bucket_name=bucket.bucket_name,
             feeds=feeds
             )
        crawler.node.add_dependency(bucket)

        ##########################################################
        # COMPACTOR
        ###########################################################
        compactor = BusObservatoryCompactor(
           self,
           "BusObservatoryCompactor",
           region=self.region,
           bucket=bucket,
           feeds=feeds
        )
        compactor.node.add_dependency(crawler)

        #FIXME: uncomment for production and api testing
        # # ##########################################################
        # # API
        # # lambda handler
        # # gateway
        # # custom domain
        # # ##########################################################
        
        # api = BusObservatoryAPI(
        #     self,
        #     "BusObservatoryAPI",
        #     region=self.region,
        #     bucket=bucket,
        #     feeds=feeds
        # )
    