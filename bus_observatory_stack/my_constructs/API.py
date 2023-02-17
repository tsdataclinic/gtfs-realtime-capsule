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
    def __init__(self, scope: Construct, id: str, region: str, bucket, feeds: dict, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # CREATE THE API LAMBDA
        # this will build and package an env using entry folder requirements.txt without need for layers

        my_handler = lambda_alpha_.PythonFunction(
            self, 
            "BusObservatoryStack_API_Lambda",
            entry="bus_observatory_stack/my_lambdas/lambda_API",
            runtime=_lambda.Runtime.PYTHON_3_8,
            index="app.py",
            handler="handler",
            timeout=Duration.seconds(60),
            environment={
                "region": region,
                "bucket": bucket.bucket_name
                },
            )
        
        # Grant the Lambda function permission to read SSM parameters
        my_handler.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ssm:DescribeParameters"],
            resources=["*"]
        ))

        # Grant the Lambda function permission to run an Athena query
        my_handler.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ssm:DescribeParameters"],
            resources=["*"]
        ))

        # GRANT THE LAMBDA FUNCTION PERMISSION TO RUN ATHENA QUERIES

        my_handler.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["athena:StartQueryExecution"],
            resources=["*"]
        ))

        ################################################################################
        # REST API, Custom Domain
        # following https://cloudbytes.dev/aws-academy/cdk-api-gateway-with-custom-domain
        ################################################################################

        #FIXME: this should be stored in a parameter store or passed down from the parent stack
        root_domain = "busobservatory.org"
        subdomain = "beta"
        fully_qualified_domain_name = subdomain+"."+root_domain

        # get the hosted zone
        my_hosted_zone = route53.HostedZone.from_lookup(
            self,
            "BusObservatoryAPI_HostedZone",
            domain_name=root_domain 
            )

        #FIXME: dnsvaidatedcertificate is deprecated
        # [WARNING] aws-cdk-lib.aws_certificatemanager.DnsValidatedCertificate is deprecated.
        #   use {@link Certificate} instead
        # # create certificate
        # my_certificate = acm.DnsValidatedCertificate(
        #     self,
        #     "BusObservatoryAPI_Certificate",
        #     domain_name="beta.busobservatory.org",
        #     hosted_zone=my_hosted_zone,
        #     region="us-east-1"
        #     )

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
                domain_name="beta.busobservatory.org",
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
