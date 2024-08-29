from parquet_utils import write_data, read_data
import pandas as pd
import datetime as dt
import os

data = {
    'id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, 30, 35, 40, 22],
    'salary': [50000.0, 60000.0, 70000.0, 80000.0, 45000.0],
    'timestamp': pd.to_datetime([
        '2023-08-01 12:00:00',
        '2023-08-01 13:00:00',
        '2023-08-02 14:00:00',
        '2023-08-02 15:00:00',
        '2023-08-03 16:00:00'
    ])
}
df = pd.DataFrame(data)
df['date'] = df['timestamp'].dt.date
table = pa.Table.from_pandas(df)

s3_path = os.path.join(S3_BUCKET, "testing", "parquet_test")

write_data(table, s3_path)

table = read_data(s3_path, dt.datetime(2023, 8, 1), dt.datetime(2023, 8, 2, 15))
print(table.to_pandas())

compact_path = os.path.join(S3_BUCKET, "testing", "parquet_compact")
compact(s3_path, compact_path, dt.date(2023, 8, 1))

print(read_data(compact_path, dt.datetime(2023, 8, 1), dt.datetime(2023, 8, 2, 15)).to_pandas())
