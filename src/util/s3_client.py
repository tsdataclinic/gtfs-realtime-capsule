import boto3
from botocore.config import Config

def create_s3_client(s3_config: dict):
    # Create a base configuration with retries if present
    config_parameters = {}
    retries_config = s3_config.get("retries")
    if retries_config:
        config_parameters['retries'] = retries_config

    # Add custom signature version if provided
    if "signature_version" in s3_config:
        config_parameters['signature_version'] = s3_config.get("signature_version")

    # Create the boto Config object
    config = Config(**config_parameters)

    # Use custom endpoint URL if provided, otherwise default to None
    endpoint_url = s3_config.get("endpoint_url", None)

    # Create the S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=s3_config["public_key"],
        aws_secret_access_key=s3_config["secret_key"],
        endpoint_url=endpoint_url,  # Set custom endpoint URL
        config=config,
    )

    return s3
