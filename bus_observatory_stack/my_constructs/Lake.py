from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    aws_glue_alpha as glue,
)


class BusObservatoryLake(Construct):
    def __init__(
        self, 
        scope: Construct, 
        id: str,
        bucket: s3.Bucket,
        **kwargs
        ):

        super().__init__(scope, id, **kwargs)

        # S3 DATA LAKE
        # bucket construct passed in

        # Create a Glue Catalog
        catalog = glue.CfnCatalog(self, f"{bucket.bucket_name}_Catalog")

        # ##FIXME: review from here

        # # Create a Glue Crawler
        # crawler = glue.CfnCrawler(
        #     self, "GlueCrawler", ##FIXME:
        #     database_name=catalog.database_name,
        #     table_prefix="my_table_",##FIXME:
        #     targets={
        #         "s3Targets": [
        #             {
        #                 "path": bucket.bucket_name
        #             }
        #         ]
        #     }
        # )

        # # Create a Glue Table
        # glue_table = glue.CfnTable(
        #     self, "GlueTable",##FIXME:
        #     database_name=catalog.database_name,
        #     table_input={
        #         "name": "my_table",
        #         "columns": [
        #             {
        #                 "name": "column1",
        #                 "type": "string"
        #             },
        #             {
        #                 "name": "column2",
        #                 "type": "int"
        #             }
        #         ],
        #         "partitionKeys":
