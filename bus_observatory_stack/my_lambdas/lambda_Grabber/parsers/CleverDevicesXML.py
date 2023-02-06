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


# def parse_xml_getRoutePoints(data):
#     coordinates_bundle=dict()
#     routes = list()
#     route = Route()
#     e = xml.etree.ElementTree.fromstring(data)
#     for child in e.getchildren():
#         if len(child.getchildren()) == 0:
#             if child.tag == 'id':
#                 route.identity = child.text
#             # bug we make lat, lon into float as soon as fetched? why are they string in the dict later?
#             else:
#                 route.add_kv(child.tag, child.text)
#         if child.tag == 'pas':
#             n = 0
#             p_prev = None
#             for pa in child.findall('pa'):
#                 path = Route.Path()
#                 for path_child in pa.getchildren():
#                     if len(path_child.getchildren()) == 0:
#                         if path_child.tag == 'id':
#                             path.id = path_child.text
#                         elif path_child.tag == 'd':
#                             path.d = path_child.text
#                         elif path_child.tag == 'dd':
#                             path.dd = path_child.text
#                         else:
#                             path.add_kv(path_child.tag, path_child.text)
#                     elif path_child.tag == 'pt':
#                         pt = path_child
#                         stop = False
#                         for bs in pt.findall('bs'):
#                             stop = True
#                             _stop_id = _cond_get_single(bs, 'id')
#                             _stop_st = _cond_get_single(bs, 'st')
#                             break
#                         p = None
#                         if not stop:
#                             p = Route.Point()
#                         else:
#                             p = Route.Stop()
#                             p.identity = _stop_id
#                             p.st = _stop_st
#                         p.d = path.d
#                         p.lat = float(_cond_get_single(pt, 'lat'))
#                         p.lon = float(_cond_get_single(pt, 'lon'))
#                         p.waypoint_id = n
#                         if n != 0:
#                             p.distance_to_prev_waypoint = distance(p_prev.lat, p_prev.lon, p.lat, p.lon)
#                         p_prev = p
#                         n =+ 1
#                         path.points.append(p)
#                 route.paths.append(path)
#                 routes.append(route)
#             break

#     return routes


# class Route(KeyValueData):
#     class Path(KeyValueData):
#         def __init__(self):
#             KeyValueData.__init__(self)
#             self.name = 'Path'
#             self.points = []
#             self.id = ''
#             self.d = ''
#             self.dd = ''

#     class Point(KeyValueData):
#         def __init__(self):
#             KeyValueData.__init__(self)
#             self.name = 'Point'
#             self.lat = ''
#             self.lon = ''
#             self.d = ''
#             # self.waypoint_id = '' # are we using this?
#             self.distance_to_prev_waypoint = ''

#     class Stop(KeyValueData):
#         def __init__(self):
#             KeyValueData.__init__(self)
#             self.name = 'Stop'
#             self.identity = ''
#             self.st = ''
#             self.lat = ''
#             self.lon = ''
#             self.d = ''

#     def __init__(self):
#         KeyValueData.__init__(self)
#         self.name = 'route'
#         self.identity = ''
#         self.paths = []



# _sources = {'nj': 'http://mybusnow.njtransit.com/bustime/map/'}
# _api = {'all_buses': 'getBusesForRouteAll.jsp'}

# def _gen_command(source, func, **kwargs):
#     result = _sources[source] + _api[func]
#     params = ''
#     for k, v in list(kwargs.items()):
#         params = params + k + '=' + str(v) + '&'
#     if params:
#         result += '?' + params[:-1]
#     return result

# def _cond_get_single(tree, key, default=''):
#     res = tree.find(key)
#     if res is not None:
#         return res.text 
#     return default



# def get_xml_data_save_raw(source, function, raw_dir, **kwargs):
#     data = get_xml_data(source, function, **kwargs)
#     if not os.path.exists(raw_dir):
#         os.makedirs(raw_dir)
#     now = datetime.now()
#     handle = open(raw_dir + '/' + now.strftime('%Y%m%d.%H%M%S') + '.' + source + '.xml', 'w')
#     handle.write(data)
#     handle.close()
#     return data
