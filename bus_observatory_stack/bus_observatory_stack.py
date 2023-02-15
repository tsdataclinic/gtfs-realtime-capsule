from aws_cdk import (
    Stack,
    aws_s3 as s3,
)
from constructs import Construct
import json
import boto3

from bus_observatory_stack.my_constructs.ParamStore import BusObservatoryParamStore
from bus_observatory_stack.my_constructs.Lake import BusObservatoryLake
from bus_observatory_stack.my_constructs.Grabber import BusObservatoryGrabber
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

        #FIXME: hardcoded region
        aws_region = "us-east-1"

        ###########################################################
        # S3 BUCKET
        ###########################################################
        bucket = s3.Bucket.from_bucket_name(self, bucket_name, bucket_name)

        ###########################################################
        # LOAD FEED CONFIG FROM DISK
        ###########################################################
        feeds = json.load(open("feeds.json"))
        
        ###########################################################
        # PARAMETER STORE
        # load the config from feeds.json and store it in parameter store
        ###########################################################

        paramstore = BusObservatoryParamStore(
            self,
            "BusObservatoryParamStore",
            region=aws_region,
            bucket=bucket,
            feeds=feeds
        )

        ###########################################################
        # SCHEDULED GRABBERS
        # create the lambda and configure scheduled event
        # for each feed
        ###########################################################
        grabber = BusObservatoryGrabber(
            self,
            "BusObservatoryGrabber",
            region=aws_region,
            bucket=bucket,
            feeds=feeds
        )

        ##########################################################
        # DATA LAKE
        # crawlers
        # crawl schedule
        # governed tables for each folder/feed

        lake = BusObservatoryLake(
            self,
            "BusObservatoryLake",
             region=aws_region,
             bucket_name=bucket.bucket_name,
             feeds=feeds
             )

        # ##########################################################
        # API
        # lambda handler
        # gateway
        # custom domain
        # ##########################################################
        
        api = BusObservatoryAPI(
            self,
            "BusObservatoryAPI",
            region=aws_region,
            bucket=bucket,
            feeds=feeds
        )
    