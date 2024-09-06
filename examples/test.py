from src.normalize import gtfs_realtime_pb2
import requests
from src.normalize.protobuf_utils import protobuf_objects_to_pyarrow_table
from src.normalize.parquet_utils import add_time_columns
import datetime as dt


S3_BUCKET = "dataclinic-gtfs-rt"

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get('https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace')
feed.ParseFromString(response.content)

trip_updates = []
vehicles = []

cur_time = dt.datetime.now()
cur_date = cur_time.date()
for entity in feed.entity:
    entity_id = entity.id
    if entity.HasField('trip_update'):
        trip_updates.append((entity_id, entity.trip_update))
    # if entity.HasField('alert'):
    #     alerts.append((entity_id, entity.alert))
    if entity.HasField('vehicle'):
        vehicles.append((entity_id, entity.vehicle))
        print(entity.vehicle)

trip_updates_pa = protobuf_objects_to_pyarrow_table([x[1] for x in trip_updates]) if trip_updates else None
vehicles_pa = protobuf_objects_to_pyarrow_table([x[1] for x in vehicles]) if vehicles else None

if trip_updates_pa:
    trip_updates_pa = trip_updates_pa.add_column(0, "id", [[x[0] for x in trip_updates]])
    trip_updates_pa = add_time_columns(trip_updates_pa, cur_time, cur_date)
    print(f"trip-updates count: {len(trip_updates_pa)}")
    s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test/mta-subway-ace/trip-updates"

if vehicles_pa:
    vehicles_pa = vehicles_pa.add_column(0, "id", [[x[0] for x in vehicles]])
    vehicles_pa = add_time_columns(vehicles_pa, cur_time, cur_date)
    print(f"vehicles count: {len(vehicles_pa)}")

    s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test/mta-subway-ace/vehicles"

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get('https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts')
feed.ParseFromString(response.content)

alerts = []

cur_time = dt.datetime.now()
cur_date = cur_time.date()
for entity in feed.entity:
    entity_id = entity.id
    if entity.HasField('alert'):
        print(entity.alert)
        alerts.append((entity_id, entity.alert))

alerts_pa = protobuf_objects_to_pyarrow_table([x[1] for x in alerts]) if alerts else None

if alerts_pa:
    alerts_pa = alerts_pa.add_column(0, "id", [[x[0] for x in alerts]])
    alerts_pa = add_time_columns(alerts_pa, cur_time, cur_date)
    print(f"alerts count: {len(alerts_pa)}")

    s3_uri = f"s3://{S3_BUCKET}/gtfs_norm/test/mta-subway-alerts"

print(cur_time)
