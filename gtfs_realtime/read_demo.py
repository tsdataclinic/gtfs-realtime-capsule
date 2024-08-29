from parquet_utils import read_data
import datetime as dt
import pandas as pd

begin = dt.datetime(2024, 8, 29)
end = dt.datetime(2024, 8, 30)

uri = "s3://dataclinic-gtfs-rt/gtfs_norm/test/"

table = read_data(uri, begin, end)
df = table.to_pandas()
print(df)
print(df.columns)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(df[[col for col in df if "trip." in col]])
