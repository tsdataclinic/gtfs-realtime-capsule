# Data lake constructs
# based on example https://catalog.us-east-1.prod.workshops.aws/workshops/697be460-9224-4b82-99e2-5103b900ed4e/en-US/030-build/034-code-walkthrough
import json
from constructs import Construct
from aws_cdk import (
    Duration,
    aws_s3 as s3,
    aws_glue as glue_,
    aws_glue_alpha as glue_alpha_,
    aws_iam as iam_,
    aws_lakeformation as lakeformation_,
)


class BusObservatoryLake(Construct):
    def __init__(self, scope: Construct, id: str, region: str, bucket: s3.Bucket, feeds: list, **kwargs):

        super().__init__(scope, id, **kwargs)

        # S3 bucket construct passed in

        # create a glue crawler to build the data catalog
        # Step 1 . create a role for AWS Glue
        glue_role = iam_.Role(self, "glue_role", 
            assumed_by=iam_.ServicePrincipal('glue.amazonaws.com'),
            managed_policies= [iam_.ManagedPolicy.from_managed_policy_arn(
                self, 
                f"{bucket.bucket_name}_CrawlerGlueRole", 
                managed_policy_arn='arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole'
                )
            ]
        )

        # glue role needs "*" read/write - otherwise crawler will not be able to create tables (and no error messages in crawler logs)
        glue_role.add_to_policy(
            iam_.PolicyStatement(
                actions=[
                    's3:GetObject', 
                    's3:PutObject', 
                    'lakeformation:GetDataAccess',
                    'lakeformation:CreateDatabase',
                    'lakeformation:CreateTable',
                    'lakeformation:CreateTableWithColumns'
                    ], 
                effect=iam_.Effect.ALLOW, 
                resources=['*']
                )
            )
        

        # Step 2. create a database named after the bucket name
        db=glue_alpha_.Database(
            self, 
            f"{bucket.bucket_name}_Database",
            database_name=bucket.bucket_name
        )


        # Step 3. create a crawler named "fitsdatalakecrawler-<hex>", and schedule to run every 15 mins
        # You can change the frequency based on your needs
        # cron schedule format cron(Minutes Hours Day-of-month Month Day-of-week Year) 

        #FIXME: update the scheudle to cron(0 2 * * ? *) after testing is done to run every day at 2am
        target_s3_path = f"s3://{bucket.bucket_name}/feeds/"

        # configure the crawler to create tables based on 2nd level of folder structure 
        # e.g. s3://bucket_name/feeds/nyct_mta_bus_siri/
        configuration = {
            "Version": 1.0,
            "Grouping": {
                "TableGroupingPolicy": "CombineCompatibleSchemas",
                "TableLevelConfiguration": 3
            }
        }
        configuration_str = json.dumps(configuration)

        glue_.CfnCrawler(
            self, 
            f"{bucket.bucket_name}-crawler",
            name=f"BusObservatoryStack_{bucket.bucket_name}_crawler",
            database_name=bucket.bucket_name,
            role=glue_role.role_arn,
            schedule={"scheduleExpression":"cron(0/30 * * * ? *)"},
            targets={"s3Targets": [{"path": target_s3_path}]},
            recrawl_policy={"recrawlBehavior": "CRAWL_NEW_FOLDERS_ONLY"},
            configuration= configuration_str
        )


        # # When your AWS Lake Formation Data catalog settings is not set to 
        # # "Use only IAM access control for new databases" or
        # # "Use only IAM access control for new tables in new databse"
        # # you need to grant additional permission to the data catalog database. 
        # # in order for the crawler to run, we need to add some permissions to lakeformation

        # #FIXME: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lakeformation/CfnResource.html
        # location_resource = lakeformation_.CfnResource(
        #     self, 
        #     f"{bucket.bucket_name}_DatalakeLocationResource",
        #     resource_arn= bucket.bucket_arn,
        #     use_service_linked_role=True
        # )

        # #FIXME: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lakeformation/CfnPermissions.html
        # #FIXME: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lakeformation/CfnPermissions.html#datalakeprincipalproperty
        # #FIXME: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lakeformation/CfnPermissions.html#resourceproperty
        # lakeformation_.CfnPermissions(
        #     self, 
        #     f"{bucket.bucket_name}_DatalakeDatabasePermission",
        #     data_lake_principal=lakeformation_.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier=glue_role.role_arn),
        #     resource=lakeformation_.CfnPermissions.ResourceProperty(database_resource=lakeformation_.CfnPermissions.DatabaseResourceProperty(name=db.database_name)),
        #     permissions=["ALTER", "DROP", "CREATE_TABLE"],
        # )

        # location_permission = lakeformation_.CfnPermissions(
        #     self, 
        #     f"{bucket.bucket_name}_DatalakeLocationPermission",
        #     data_lake_principal=lakeformation_.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier=glue_role.role_arn),
        #     resource=lakeformation_.CfnPermissions.ResourceProperty(data_location_resource=lakeformation_.CfnPermissions.DataLocationResourceProperty(s3_resource=bucket.bucket_arn)),
        #         permissions=["DATA_LOCATION_ACCESS"],
        #     )

        # #make sure the location resource is created first
        # location_permission.node.add_dependency(location_resource)