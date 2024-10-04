import s3fs

from src.normalize.parquet_utils import read_data
import datetime as dt

begin = dt.datetime(2024, 8, 29)
end = dt.datetime(2024, 8, 30)

uri = "s3://dataclinic-gtfs-rt/gtfs_norm/test/mta-subway-ace/trip-updates"
# uri = "s3://dataclinic-gtfs-rt/gtfs_norm/test/mta-subway-ace/vehicles"
# uri = "s3://dataclinic-gtfs-rt/gtfs_norm/test/mta-subway-alerts/"
s3_fs = s3fs.S3FileSystem(key="foo", secret="bar")
table = read_data(s3_fs, uri, begin, end)
df = table.to_pandas()
print(df)
print(df.columns)