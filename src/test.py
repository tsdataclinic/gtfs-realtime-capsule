import gtfs_realtime_pb2
import requests

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get('https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace')
feed.ParseFromString(response.content)

for entity in feed.entity:
    if entity.HasField('trip_update'):
        print(entity.trip_update)
