from constructs import Construct

from aws_cdk import (
    CfnOutput,
    Duration,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_lambda_python_alpha as lambda_alpha_,
    aws_lambda as _lambda,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_s3 as s3,
)


class BusObservatoryAPI(Construct):
    def __init__(
            self, 
            scope: Construct, 
            id: str, 
            stack_config: dict,
            region: str, 
            bucket,
            **kwargs):
        super().__init__(scope, id, **kwargs)

        feeds=stack_config['feeds']
        
        # CREATE THE API LAMBDA
        # this will build and package an env using entry folder requirements.txt without need for layers

        my_handler = lambda_alpha_.PythonFunction(
            self, 
            "BusObservatoryStack_API_Lambda",
            entry="bus_observatory_stack/my_lambdas/lambda_API",
            runtime=_lambda.Runtime.PYTHON_3_8,
            index="app.py",
            handler="handler",
            timeout=Duration.seconds(120),
            memory_size=1024,
            environment={
                "region": region,
                "bucket": bucket.bucket_name
                },
            )
        
        # Grant the Lambda function permissions

        ssm_permission=iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ssm:GetParametersByPath"],
            resources=["*"]
        )
        my_handler.add_to_role_policy(ssm_permission)
        bucket.grant_read_write(my_handler)

        #TODO: reduce permissions by specifying only the exact resources that the lambda needs to access
        athena_permission=iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetTableMetadata",
            ],
            resources=["*"]
        )
        my_handler.add_to_role_policy(athena_permission)


        #TODO: reduce permissions by specifying only the exact resources that the lambda needs to access
        glue_permission=iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "glue:GetDatabases",
                "glue:GetTable",
                "glue:GetTables"],
            resources=["*"]
        )
        my_handler.add_to_role_policy(glue_permission)

        #TODO: reduce permissions by specifying only the exact resources that the lambda needs to access
        lf_permission=iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "lakeformation:GetDataAccess"],
            resources=["*"]
        )
        my_handler.add_to_role_policy(lf_permission)


        #BUG: this is hardcoded, ideally this bucket should be separate from the main data lake and only contain the results of the queries, and have a lifecycle rule to delete after 1 day
        s3_permission=iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:*"],
            resources=[
                "arn:aws:s3:::aws-athena-query-results-870747888580-us-east-1", 
                "arn:aws:s3:::aws-athena-query-results-870747888580-us-east-1/*"
            ]
        )

        my_handler.add_to_role_policy(s3_permission)

       
        ################################################################################
        # REST API, Custom Domain
        # following https://cloudbytes.dev/aws-academy/cdk-api-gateway-with-custom-domain
        ################################################################################

        root_domain = stack_config['domain']
        subdomain = stack_config['subdomain']
        fully_qualified_domain_name = subdomain+"."+root_domain

        # get the hosted zone
        my_hosted_zone = route53.HostedZone.from_lookup(
            self,
            "BusObservatoryAPI_HostedZone",
            domain_name=root_domain,
            )

        # CREATE AN ACM CERTIFICATE
        my_certificate = acm.Certificate(
            self,
            "BusObservatoryStack_Certificate",
            domain_name=fully_qualified_domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone=my_hosted_zone)
        )

        # EXPORT THE ARN OF THE CERTIFICATE
        self.certificate_arn = my_certificate.certificate_arn

        # create REST API
        my_api = apigateway.LambdaRestApi(
            self,
            "BusObservatoryAPI_ApiGateway",
            handler=my_handler,
            domain_name=apigateway.DomainNameOptions(
                domain_name=fully_qualified_domain_name,
                certificate=my_certificate,
                security_policy=apigateway.SecurityPolicy.TLS_1_2,
                endpoint_type=apigateway.EndpointType.EDGE,
            )
        )

        # create A record
        route53.ARecord(
            self,
            "BusObservatoryAPI_ApiRecord",
            record_name=subdomain,
            zone=my_hosted_zone,
            target=route53.RecordTarget.from_alias(targets.ApiGateway(my_api)),
        )

        # outputs
        CfnOutput(self, 'Hosted Zone', value=my_hosted_zone.zone_name);
        CfnOutput(self, 'API Url', value=my_api.url);
