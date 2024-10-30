import datetime as dt
import json
import click


def check_config(config: dict):
    print(config)
    assert config["s3_bucket"]["uri"]
    assert config["s3_bucket"]["public_key"]
    assert config["s3_bucket"]["secret_key"]
    retries_config = config["s3_bucket"].get("retries")
    if retries_config:
        assert retries_config["mode"], "mode must be specified for enabling " "retry"


def load_config(path: str):
    with open(path, "r") as f:
        config = json.load(f)
        check_config(config)
        return config


def get_last_processed_timestamp(s3, bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return dt.datetime.fromtimestamp(
            float(json.loads(response["Body"].read())["last_processed"])
        )
    except s3.exceptions.NoSuchKey:
        return None


def update_last_processed_timestamp(s3, bucket, key, timestamp):
    s3.put_object(
        Bucket=bucket, Key=key, Body=json.dumps({"last_processed": timestamp})
    )


def validate_date(ctx, param, value):
    if value is None:  # If no input is provided, use today's date
        return str(dt.date.today())
    try:
        # Attempt to parse the date with the expected format
        return str(dt.datetime.strptime(value, "%Y%m%d").date())
    except ValueError:
        # Raise a BadParameter error if the format is incorrect
        raise click.BadParameter("Date must be in YYYYMMDD format.")
