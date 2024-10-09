import s3fs

from src.normalize.parquet_utils import compact
import datetime as dt

S3_BUCKET = "dataclinic-gtfs-rt"

s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test/mta-subway-alerts"
dest_s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test-compact/mta-subway-alerts"
s3_fs = s3fs.S3FileSystem(key="foo", secret="bar")
compact(s3_uri, dest_s3_uri, dt.date(2024, 8, 30))
