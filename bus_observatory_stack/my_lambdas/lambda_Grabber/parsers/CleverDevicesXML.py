import pandas as pd
import xml.etree.ElementTree
import time
from datetime import datetime

####################################################################################
# new code

def get_buses(feed):
    
    # argument is a Feed object
    #todo: something with feed
    
    data, fetch_timestamp = get_xml_data(feed)
    positions_df = pd.DataFrame([vars(bus) for bus in parse_xml_getBusesForRouteAll(data)])
    positions_df['timestamp'] = fetch_timestamp
    positions_df = positions_df.drop(['name','bus'], axis=1) 
    positions_df[["lat", "lon"]] = positions_df[["lat", "lon"]].apply(pd.to_numeric)
    
    # return fix_timestamp(feed.timestamp_key, positions_df)
    return positions_df

####################################################################################
# legacy code
# API like: https://github.com/harperreed/transitapi/wiki/Unofficial-Bustracker-API

class KeyValueData:
    def __init__(self, **kwargs):
        self.name = 'KeyValueData'
        for k, v in list(kwargs.items()):
            setattr(self, k, v)

    def add_kv(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return self.name + '[%s]' % out_string

    def to_dict(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value)) # list of tuples
        line.sort(key=lambda x: x[0])
        out_dict = dict()
        for l in line:
            out_dict[l[0]]=l[1]
        return out_dict

class Bus(KeyValueData):
    def __init__(self, **kwargs):
        KeyValueData.__init__(self, **kwargs)
        self.name = 'Bus'


# #FIXME: record in UTC time
# not sure where this code should go below, and it needs to be modifed (this was copied from NYC SIRI)
# # 1 convert POSIX timestamp to datetime
# positions_df['vehicle.timestamp'] = pd.to_datetime(positions_df['vehicle.timestamp'], unit="s")
# # 2 tell pandas its UTC
# positions_df['vehicle.timestamp'] = positions_df['vehicle.timestamp'].dt.tz_localize('UTC')

def get_timestamp(tz):

    # https://gist.github.com/ffturan/234730392091c66134aff662c87c152e    
    import os
    os.environ['TZ'] = tz
    time.tzset()
    return datetime.now()

def get_xml_data(feed):
    import urllib.request
    tries = 1
    while True:
        try:
            data = urllib.request.urlopen(feed.url).read()
            if data:
                timestamp=get_timestamp(feed.tz)
                #TODO: maybe convert timestamp to UTC here?
                break
        except Exception as e:
            print (e)
            print (str(tries) + '/12 cant connect to NJT API... waiting 5s and retry')
            if tries < 12:
                tries = tries + 1
                time.sleep(5)
            else:
                print('failed trying to connect to NJT API for 1 minute, giving up')
                # bug handle this better than TypeError: cannot unpack non-iterable NoneType object
                return
    return data, timestamp

def validate_xmldata(xmldata):
    e = xml.etree.ElementTree.fromstring(xmldata)
    for child in e.getchildren():
        if child.tag == 'pas':
            if len(child.findall('pa')) == 0:
                print('Route not valid')
                return False
            elif len(child.findall('pa')) > 0:
                return True

def parse_xml_getBusesForRouteAll(data):
    results = []
    e = xml.etree.ElementTree.fromstring(data)
    for atype in e.findall('bus'):
        fields = {}
        for field in list(atype.iter()):
            if field.tag not in fields and hasattr(field, 'text'):
                if field.text is None:
                    fields[field.tag] = ''
                    continue
                fields[field.tag] = field.text

        results.append(Bus(**fields))

    return clean_buses(results)

def clean_buses(buses):
    buses_clean = []
    for bus in buses:
        if bus.run.isdigit() is True:  # removes any buses with non-number run id, and this should populate throughout the whole project
            if bus.rt.isdigit() is True:  # removes any buses with non-number route id, and this should populate throughout the whole project
                buses_clean.append(bus)
    return buses_clean
