import datetime as dt
from typing import Optional

import pyarrow as pa
from pyarrow import dataset as ds
from pyarrow import parquet as pq
from s3fs import S3FileSystem


def add_time_columns(
        table: pa.Table, timestamp: dt.datetime, date: dt.date
) -> pa.Table:
    table = table.add_column(
        1, "time", pa.array([timestamp] * len(table), type=pa.timestamp("ms"))
    )
    return table.add_column(1, "date",
                            pa.array([date] * len(table), type=pa.date32()))


def write_data(
        s3: S3FileSystem,
        table: pa.Table,
        uri: str,
        existing_data_behavior: str = "overwrite_or_ignore",
) -> None:
    partition = ds.partitioning(
        schema=pa.schema([("date", pa.date32())]), flavor="hive"
    )
    pq.write_to_dataset(
        table=table,
        root_path=uri,
        partitioning=partition,
        filesystem=s3,
        existing_data_behavior=existing_data_behavior,
    )


def read_data(
    s3: S3FileSystem,
    uri: str,
    begin: dt.datetime,
    end: dt.datetime,
    columns: Optional[str] = None,
) -> pa.Table:
    dataset = ds.dataset(
        source=uri.lstrip("s3://"),
        filesystem=s3,
        format="parquet",
        partitioning="hive",
    )

    table = dataset.to_table(
        columns=columns,
        filter=(
                (ds.field("date") >= begin.strftime("%Y-%m-%d"))
                & (ds.field("date") < end.strftime("%Y-%m-%d"))
        ),
    )
    return table


def _read_data_single_date(
        s3: S3FileSystem,
        uri: str,
        date: dt.datetime,
        columns: Optional[str] = None,
) -> pa.Table:
    dataset = ds.dataset(
        source=uri.lstrip("s3://"),
        filesystem=s3,
        format="parquet",
        partitioning="hive",
    )

    table = dataset.to_table(
        columns=columns,
        filter=(
                (ds.field("date") == date.strftime("%Y-%m-%d"))
        ),
    )
    return table


def compact(s3: S3FileSystem, uri, date: dt.date) -> None:
    date = dt.datetime.combine(date, dt.time.min)
    table = _read_data_single_date(s3, uri, date)
    write_data(s3, table, uri, existing_data_behavior="delete_matching")
