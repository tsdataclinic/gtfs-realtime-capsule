import boto3
from botocore.config import Config


def create_s3_client(s3_config: dict):
    retries_config = s3_config.get("retries")
    if retries_config:
        config = Config(
            retries=retries_config
        )
        s3 = boto3.client(
            "s3",
            aws_access_key_id=s3_config["public_key"],
            aws_secret_access_key=s3_config["secret_key"],
            config=config
        )
    else:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=s3_config["public_key"],
            aws_secret_access_key=s3_config["secret_key"],
        )
    return s3
