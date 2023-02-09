import app

testdata = {
    "gtfsrt": {
        "tfnsw_bus": {
            "publish": "True",
            "system_name": "Transport for New South Wales",
            "city_name": "Sydney, NSW, AU",
            "feed_type": "gtfsrt",
            "url": "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses",
            "api_key": "HTHniGwUwxSJoty8T3kQTtBtd9jxBl8QFyws",
            "header": "True",
            "header_format": {
                "key_name": "Authorization",
                "template": "apikey {key_value}"
            },
            "route_key": "vehicle.trip.route_id",
            "timestamp_key": "vehicle.timestamp",
            "tz": "Australia/Sydney",
            "notes": "Sampled once per minute. We parse all fields in this feed."
        }
    },
    "siri": {
        "nyct_mta_bus_siri": {
            "publish": "True",
            "system_name": "New York City Transit (SIRI)",
            "city_name": "New York City, NY, US",
            "feed_type": "siri",
            "url": "http://gtfsrt.prod.obanyc.com/vehiclePositions?key={}",
            "api_key": "088886bd-cc48-4d7c-bd8a-498d353d7d13",
            "header": "False",
            "route_key": "route",
            "timestamp_key": "timestamp",
            "tz": "America/New_York",
            "notes": "Sampled once per minute. We parse all fields in this feed."
        }
    },
    "xml": {
        "njtransit_bus": {
            "publish": "True",
            "system_name": "NJTransit",
            "city_name": "NJ, US",
            "feed_type": "njxml",
            "url": "http://mybusnow.njtransit.com/bustime/map/getBusesForRouteAll.jsp",
            "header": "False",
            "route_key": "rt",
            "timestamp_key": "timestamp",
            "tz": "America/New_York",
            "notes": "Sampled once per minute. This feed is based on an old technology and returns an XML response. We parse most of the fields in this feed, but most of them are undocumented."
        }
    }
}


def create_event(testdata: dict, test_type: str) -> dict:

    test_feed_config= testdata[test_type]

    for system_id, feed_config in test_feed_config.items():
        event = {
            "region": "us-east-1",
            "bucket_name": "busobservatory-2",
            "system_id": system_id,
            "feed_config": feed_config
        }
        
    return event

# event = create_event(testdata, "gtfsrt")
# event = create_event(testdata, "siri")
event = create_event(testdata, "xml")

app.handler(event, None)
