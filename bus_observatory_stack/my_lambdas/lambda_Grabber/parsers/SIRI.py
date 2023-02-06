import trio
import datetime as dt
import requests
import pandas as pd
from dateutil import parser

####################################################################################
# new code

def get_buses(feed):
        
    # for NYC SIRI only, iterate async calls for each route
    if feed.system_id in ["nyct_mta_bus_siri","TEST_nyct_mta_bus_siri"]:
        
        async def grabber(s,a_path,route_id):
            try:
                r = await s.get(path=a_path, retries=2, timeout=10)
                fetches.append({route_id:r})
            except Exception as e:
                print (f'\t{dt.datetime.now()}\tTimeout or too many retries for {route_id}.')

        async def main(url_paths):
            url_SIRI_root="http://bustime.mta.info"
            from asks.sessions import Session
            s = Session(url_SIRI_root, connections=25)
            async with trio.open_nursery() as n:
                for (route_id, path) in url_paths:
                    n.start_soon(grabber, s, path, route_id )
        fetches = []
        trio.run(main, get_SIRI_urls(feed))
        positions_df = parse_buses(fetches)
        
    #TODO: write / refactor below for a general/non-NYC SIRI feed parser
    else:

        # these aren't used for NYC but might be for general
        system_id=feed.system_id
        api_url = feed.url
        api_key = feed.key_value
        positions_df=pd.DataFrame()
 
    return positions_df

####################################################################################
# legacy code
# 

def get_OBA_routelist(feed):
    url = "http://bustime.mta.info/api/where/routes-for-agency/MTA%20NYCT.json?key={}".format(feed.api_key)     
    try:
        response = requests.get(url, timeout=5)
    except Exception as e:
        pass
    finally:
        routes = response.json()
    return routes

# generate list of SIRI endpoints to fetch
def get_SIRI_urls(feed):
    url_SIRI_suffix="/api/siri/vehicle-monitoring.json?key={}&VehicleMonitoringDetailLevel=calls&LineRef={}"
    SIRI_urls_list = []
    routes=get_OBA_routelist(feed)   
    for route in routes['data']['list']:
        route_id = route['id']
        SIRI_urls_list.append(
            (
                route_id,
                url_SIRI_suffix.format(feed.api_key,route_id)
            )
        )    
    return SIRI_urls_list

def parse_buses(fetches):
    buses=[]   
    for route_report in fetches:
        for route_id,route_data in route_report.items():
            route = route_id.split('_')[1]
            #FIXME: trap this more elegantly
            try:
                route_data=route_data.json()            
                if 'VehicleActivity' in route_data['Siri']['ServiceDelivery']['VehicleMonitoringDelivery'][0]:
                    for monitored_vehicle_journey in route_data['Siri']['ServiceDelivery']['VehicleMonitoringDelivery'][0]['VehicleActivity']:
                        bus = BusObservation(route, monitored_vehicle_journey)
                        buses.append(bus)
                else:
                    pass
            except:
                pass
    positions_df = pd.DataFrame([vars(x) for x in buses])
    positions_df['timestamp'] = positions_df['timestamp'].dt.tz_localize(None)

    # #FIXME: record as UTC local time
    # # 1 convert POSIX timestamp to datetime
    # positions_df['vehicle.timestamp'] = pd.to_datetime(positions_df['vehicle.timestamp'], unit="s")
    
    # # 2 tell pandas its UTC
    # positions_df['vehicle.timestamp'] = positions_df['vehicle.timestamp'].dt.tz_localize('UTC')

    return positions_df

class BusObservation():

    def __init__(self,route,monitored_vehicle_journey):
        self.route = route
        self.parse_buses(monitored_vehicle_journey)

    def __repr__(self):
        output = ''
        # output = None
        for var, val in vars(self).items():
            if var == '_sa_instance_state':
                continue
            else:
                output = output + ('{} {} '.format(var,val))
        return output

    def parse_buses(self, monitored_vehicle_journey):
        lookup = {'route_long':['LineRef'],
                  'direction':['DirectionRef'],
                  'service_date': ['FramedVehicleJourneyRef', 'DataFrameRef'],
                  'trip_id': ['FramedVehicleJourneyRef', 'DatedVehicleJourneyRef'],
                  'gtfs_shape_id': ['JourneyPatternRef'],
                  'route_short': ['PublishedLineName'],
                  'agency': ['OperatorRef'],
                  'origin_id':['OriginRef'],
                  'destination_id':['DestinationRef'],
                  'destination_name':['DestinationName'],
                  'next_stop_id': ['MonitoredCall','StopPointRef'], #<-- GTFS of next stop
                  'next_stop_eta': ['MonitoredCall','ExpectedArrivalTime'], # <-- eta to next stop
                  'next_stop_d_along_route': ['MonitoredCall','Extensions','Distances','CallDistanceAlongRoute'], # <-- The distance of the stop from the beginning of the trip/route
                  'next_stop_d': ['MonitoredCall','Extensions','Distances','DistanceFromCall'], # <-- The distance of the stop from the beginning of the trip/route
                  'alert': ['SituationRef', 'SituationSimpleRef'],
                  'lat':['VehicleLocation','Latitude'],
                  'lon':['VehicleLocation','Longitude'],
                  'bearing': ['Bearing'],
                  'progress_rate': ['ProgressRate'],
                  'progress_status': ['ProgressStatus'],
                  'occupancy': ['Occupancy'],
                  'vehicle_id':['VehicleRef'], #use this to lookup if articulated or not https://en.wikipedia.org/wiki/MTA_Regional_Bus_Operations_bus_fleet
                  'gtfs_block_id':['BlockRef'],
                  'passenger_count': ['MonitoredCall', 'Extensions','Capacities','EstimatedPassengerCount']
                  }
        buses = []
        try:
            setattr(self,'timestamp',parser.isoparse(monitored_vehicle_journey['RecordedAtTime']))
            for k,v in lookup.items():
                try:
                    if len(v) == 2:
                        val = monitored_vehicle_journey['MonitoredVehicleJourney'][v[0]][v[1]]
                        setattr(self, k, val)
                    elif len(v) == 4:
                        val = monitored_vehicle_journey['MonitoredVehicleJourney'][v[0]][v[1]][v[2]][v[3]]
                        setattr(self, k, val)
                    else:
                        val = monitored_vehicle_journey['MonitoredVehicleJourney'][v[0]]
                        setattr(self, k, val)
                except LookupError:
                    # if there's no passenger count, we will set it to null
                    if k == 'passenger_count':
                        setattr(self, k, None)
                except Exception as e:
                    pass
            buses.append(self)
        except KeyError: #no VehicleActivity?
            pass
        return buses
