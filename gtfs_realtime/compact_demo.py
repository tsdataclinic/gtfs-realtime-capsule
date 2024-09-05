
from parquet_utils import compact
import datetime as dt
from time import sleep


S3_BUCKET = "dataclinic-gtfs-rt"

s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test/mta-subway-alerts"
dest_s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test-compact/mta-subway-alerts"
compact(s3_uri, dest_s3_uri, dt.date(2024, 8, 30))
