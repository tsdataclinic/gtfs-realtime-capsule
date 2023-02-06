#TODO: this construct should include the following: lamdba API handler function, gateway, and route53 stuff

from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
)

class BusObservatoryAPI(Construct):
    def __init__(
        self, 
        scope: Construct, 
        id: str,
        bucket: s3.Bucket,
        **kwargs
        ):

        super().__init__(scope, id, **kwargs)
        


       #TODO: pull from current deployed stack? or copy from the rail sign stack
        # Lambda function to run Athena queries
        self.lambda_fn = _lambda.Function(self, "AthenaLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda_API"),
            environment={
                "ATHENA_OUTPUT_BUCKET": self.bucket.bucket_name,
                "ATHENA_DB_NAME": self.lakeformation_db.database_name
            }
        )


        # API Gateway REST API
        self.api = apigw.RestApi(self, "AthenaAPI",
            rest_api_name="Athena Query API",
            description="API to run Athena queries"
        )

        # API Gateway resource and method
        query_resource = self.api.root.add_resource("query")
        query_method = query_resource.add_method("GET", apigw.LambdaIntegration(self.lambda_fn),
            authorization_type=apigw.AuthorizationType.NONE,
            request_parameters={"method.request.querystring.query": True}
        )

        # Create an ACM certificate for the custom domain
        certificate = acm.Certificate(self, "APIDomainCertificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(route53.HostedZone.from_lookup(self, "HostedZone", domain_name=domain_name))
        )

        # Add custom domain to API Gateway
        domain_name = apigw.DomainName(self, "APIDomainName",
            domain_name=domain_name,
            certificate=certificate,
            endpoint_type=apigw.EndpointType.REGIONAL
        )

        # Add the custom domain to the API Gateway
        domain_name.add_base_path_mapping(self.api, {
            "basePath": "/",
            "restApiId": self.api.rest_api_id
        })