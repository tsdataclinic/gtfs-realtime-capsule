import datetime as dt
from time import sleep

import requests
import s3fs

from src.normalize import gtfs_realtime_pb2
from src.normalize.parquet_utils import write_data, add_time_columns
from src.normalize.protobuf_utils import protobuf_objects_to_pyarrow_table

S3_BUCKET = "dataclinic-gtfs-rt"

API_KEY = "010c4409-73cf-477a-913c-3f95e9300d5a"

PATH = f"{S3_BUCKET}/gtfs_norm/test/mta-bus"
s3_fs = s3fs.S3FileSystem(key="foo", secret="bar")

while True:
    for endpoint in [
        "https://gtfsrt.prod.obanyc.com/tripUpdates?key=",
        "https://gtfsrt.prod.obanyc.com/vehiclePositions?key=",
        "https://gtfsrt.prod.obanyc.com/alerts?key="
    ]:
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(endpoint + API_KEY)
        feed.ParseFromString(response.content)

        trip_updates = []
        vehicles = []
        alerts = []

        cur_time = dt.datetime.now()
        cur_date = cur_time.date()
        for entity in feed.entity:
            entity_id = entity.id
            if entity.HasField('trip_update'):
                trip_updates.append((entity_id, entity.trip_update))
            if entity.HasField('alert'):
                alerts.append((entity_id, entity.alert))
            if entity.HasField('vehicle'):
                vehicles.append((entity_id, entity.vehicle))

        trip_updates_pa = protobuf_objects_to_pyarrow_table(
            [x[1] for x in trip_updates]) if trip_updates else None
        vehicles_pa = protobuf_objects_to_pyarrow_table(
            [x[1] for x in vehicles]) if vehicles else None
        alerts_pa = protobuf_objects_to_pyarrow_table(
            [x[1] for x in alerts]) if alerts else None

        if trip_updates_pa:
            trip_updates_pa = trip_updates_pa.add_column(0, "id", [
                [x[0] for x in trip_updates]])
            trip_updates_pa = add_time_columns(trip_updates_pa, cur_time,
                                               cur_date)
            print(f"trip-updates count: {len(trip_updates_pa)}")
            s3_uri = f"{PATH}/trip-updates"
            write_data(s3_fs, trip_updates_pa, s3_uri)

        if vehicles_pa:
            vehicles_pa = vehicles_pa.add_column(0, "id",
                                                 [[x[0] for x in vehicles]])
            vehicles_pa = add_time_columns(vehicles_pa, cur_time, cur_date)
            print(f"vehicles count: {len(vehicles_pa)}")

            s3_uri = f"{PATH}/vehicles"
            write_data(s3_fs, vehicles_pa, s3_uri)

        if alerts_pa:
            alerts_pa = alerts_pa.add_column(0, "id", [[x[0] for x in alerts]])
            alerts_pa = add_time_columns(alerts_pa, cur_time, cur_date)
            print(f"alerts count: {len(alerts_pa)}")

            s3_uri = f"{PATH}/alerts"
            write_data(s3_fs, alerts_pa, s3_uri)

    print(cur_time)
    sleep(60)
