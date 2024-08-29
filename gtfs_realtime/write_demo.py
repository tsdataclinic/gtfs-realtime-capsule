import gtfs_realtime_pb2
import requests
from protobuf_utils import protobuf_objects_to_pyarrow_table
from parquet_utils import write_data, add_time_columns
import datetime as dt

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get('https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace')
feed.ParseFromString(response.content)

trip_updates = []
alerts = []
vehicles = []

S3_BUCKET = "dataclinic-gtfs-rt"

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


trip_updates_pa = protobuf_objects_to_pyarrow_table([x[1] for x in trip_updates]) if trip_updates else None
alerts_pa = protobuf_objects_to_pyarrow_table([x[1] for x in alerts]) if alerts else None
vehicles_pa = protobuf_objects_to_pyarrow_table([x[1] for x in vehicles]) if alerts else None

if trip_updates_pa:
    trip_updates_pa = trip_updates_pa.add_column(0, "id", [[x[0] for x in trip_updates]])
    trip_updates_pa = add_time_columns(trip_updates_pa, cur_time, cur_date)

s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test"
write_data(trip_updates_pa, s3_uri)

# if vehicles_pa:
#     print(vehicles_pa.add_column(0, "id", [[x[0] for x in vehicles]]))
#
# if alerts_pa:
#     print(alerts_pa.add_column(0, "id", [[x[0] for x in alerts]]))
