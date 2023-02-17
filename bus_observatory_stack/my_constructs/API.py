from constructs import Construct

from aws_cdk import (
    Duration,
    aws_apigateway as apigateway,
    CfnOutput,
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

        ################################################################################
        # REST API, Custom Domain
        # following https://cloudbytes.dev/aws-academy/cdk-api-gateway-with-custom-domain
        ################################################################################


        # get the hosted zone
        my_hosted_zone = route53.HostedZone.from_lookup(
            self,
            "BusObservatoryAPI_HostedZone",
            domain_name="busobservatory.org" #FIXME: this should be stored in a parameter store
            )

        # create certificate
        my_certificate = acm.DnsValidatedCertificate(
            self,
            "BusObservatoryAPI_Certificate",
            domain_name="beta.busobservatory.org",
            hosted_zone=my_hosted_zone,
            region="us-east-1"
            )

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
            record_name="beta",
            zone=my_hosted_zone,
            target=route53.RecordTarget.from_alias(targets.ApiGateway(my_api)),
        )

        # outputs
        CfnOutput(self, 'Hosted Zone', value=my_hosted_zone.zone_name);
        CfnOutput(self, 'API Url', value=my_api.url);
