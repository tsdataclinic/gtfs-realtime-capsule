import datetime as dt

import s3fs

from src.normalize.parquet_utils import read_data

begin = dt.datetime(2024, 10, 10)
end = dt.datetime(2024, 10, 17)

uri = "s3://dataclinic-gtfs-rt/norm/mdb-1630/trip-updates"
# uri = "s3://dataclinic-gtfs-rt/gtfs_norm/test/mta-subway-ace/vehicles"
# uri = "s3://dataclinic-gtfs-rt/gtfs_norm/test/mta-subway-alerts/"
s3_fs = s3fs.S3FileSystem()
table = read_data(s3_fs, uri, begin, end)
df = table.to_pandas()
print(df)
print(df.columns)
