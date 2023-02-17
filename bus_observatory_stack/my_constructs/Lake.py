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
    aws_lakeformation as lakeformation,
)


class BusObservatoryLake(Construct):
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
                                'lakeformation:GetDataAccess'
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

        # When your AWS Lake Formation Data catalog settings is not set to 
        # "Use only IAM access control for new databases" or
        # "Use only IAM access control for new tables in new databse"
        # you need to grant additional permission to the data catalog database. 
        # in order for the crawler to run, we need to add some permissions to lakeformation

        location_resource = lakeformation.CfnResource(
            self, 
            "BusObservatory_DatalakeLocationResource",
            resource_arn= bucket.bucket_arn,
            use_service_linked_role=True
        )

        database_permission = lakeformation.CfnPermissions(
            self, 
            "BusObservatory_DatalakeDatabasePermission",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier=glue_role.role_arn),
            resource=lakeformation.CfnPermissions.ResourceProperty(database_resource=lakeformation.CfnPermissions.DatabaseResourceProperty(name=db.database_name)),
            permissions=["ALTER", "DROP", "CREATE_TABLE"],
        )

        # FIXME: this doesnt deploy
        location_permission = lakeformation.CfnPermissions(
            self, 
            "BusObservatory_DatalakeLocationPermission",
            data_lake_principal=lakeformation.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier=glue_role.role_arn),
            resource=lakeformation.CfnPermissions.ResourceProperty(data_location_resource=lakeformation.CfnPermissions.DataLocationResourceProperty(s3_resource=bucket.bucket_arn)),
            permissions=["DATA_LOCATION_ACCESS"],
            )

        #make sure the location resource is created first
        location_permission.node.add_dependency(location_resource)
        location_permission.node.add_dependency(database_permission)

        # FIXME: verify tables are governed / compaction is active
        # check compaction status
        # aws list-table-storage-optimizers --database-name database-name --table-name table-name
        # need to add to crawler settings? "TableType":"GOVERNED",
        # FIXME: how to set the compaction schedule?
