# Data lake constructs
# based on example https://catalog.us-east-1.prod.workshops.aws/workshops/697be460-9224-4b82-99e2-5103b900ed4e/en-US/030-build/034-code-walkthrough
import json
from constructs import Construct
from aws_cdk import (
    Duration,
    aws_s3 as s3,
    aws_glue as glue,
    aws_glue_alpha as glue_alpha_,
    aws_iam as iam_,
)


class BusObservatoryCrawler(Construct):
    def __init__(self, scope: Construct, id: str, region: str, bucket_name, feeds: list, **kwargs):

        super().__init__(scope, id, **kwargs)

        # create a bucket object from existing bucket
        bucket = s3.Bucket.from_bucket_name(self, "BusObservatory_Bucket", bucket_name=bucket_name)

        # create a glue crawler to build the data catalog
        # Step 1 . create a role for AWS Glue
        glue_role = iam_.Role(self, "glue_role", 
            assumed_by=iam_.ServicePrincipal('glue.amazonaws.com'),
            managed_policies= [iam_.ManagedPolicy.from_managed_policy_arn(
                self, 
                "BusObservatory_CrawlerGlueRole", 
                managed_policy_arn='arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole'
                )
            ],
            inline_policies={
                'InlinePolicyS3andLF': iam_.PolicyDocument(
                    statements=[
                        iam_.PolicyStatement(
                            actions=[
                                's3:GetObject', 
                                's3:PutObject',
                                # 'lakeformation:GetDataAccess'
                                ], 
                            effect=iam_.Effect.ALLOW, 
                            resources=['*']
                            )
                    ]
                )
            }
        )
        

        # Step 2. create a database named after the bucket name
        db=glue_alpha_.Database(
            self, 
            "BusObservatory_Database",
            database_name=bucket.bucket_name
        )


        # Step 3. create a crawler and schedule to run every 30 mins
        # only crawling new folders at 3rd level of bucket
        # e.g. s3://bucket_name/feeds/nyct_mta_bus_siri/

        target_s3_path = f"s3://{bucket.bucket_name}/feeds/"

        configuration = {
            "Version": 1.0,
            "Grouping": {
                "TableGroupingPolicy": "CombineCompatibleSchemas",
                "TableLevelConfiguration": 3
            }
        }
        configuration_str = json.dumps(configuration)

        glue.CfnCrawler(
            self, 
            "BusObservatory_Glue_Crawler",
            name="BusObservatory_Glue_Crawler",
            database_name=bucket.bucket_name,
            role=glue_role.role_arn,
            schedule={"scheduleExpression":"cron(0/30 * * * ? *)"},
            targets={"s3Targets": [{"path": target_s3_path}]},
            recrawl_policy={"recrawlBehavior": "CRAWL_NEW_FOLDERS_ONLY"},
            configuration= configuration_str
        )

