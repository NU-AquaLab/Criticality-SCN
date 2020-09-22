
from pymongo import MongoClient, UpdateOne
from bson.objectid import ObjectId
import googlemaps
import json, sys, math, time, os

mongo_config = None
with open("../config.json", 'r') as fp:
    mongo_config = json.load(fp)["mongo_str"]
mongo_client = MongoClient(mongo_config)

# speed of light in cable (m/s)
C = 299792458 / 1.444
# Earth radius (m)
R = 6372800

class Geolocation:
    def __init__(self, lat, lon, country=""):
        self.latitude = float(lat) # latitude float
        self.longitude = float(lon) # longitude float
        self.country = country
    
    def __str__(self):
        return "%s, %s" % (self.latitude, self.longitude)

    def to_dict(self):
        return {
            "Lat": self.latitude, 
            "Lon": self.longitude, 
            "Code": self.country
        }

'''
Heuristic:
Let the following notations:
    P: probe initialized traceroute, could be the first or second hop router, otherwise use the country location
    S: destination server location
    L1: landing site near probe for the submarine cable
    L2: landing site near destination for the submarine cable
Calculate the full path for P - L1 - L2 - S
Use the min rtt for the last hop of each traceroute measurement
Traverse through each submarine cable, for each landing site of that cable, iterate through them as L1 and L2
Determine whether there it is physically possible for this traceroute to use this submarine cable to complete the path

Result:
This heuristic yields a set of "likely" submarine cable hit

Caveat:
This method neglect router processing delay
    (Potentially this will not affect the result too much because we don't need an accurate cable match, but just a submarine cable hit)
'''

# Takes two geolocation objects
# Returns the distance calculated
def geo_distance(geo1, geo2):
    lat1, lon1 = geo1.latitude, geo1.longitude
    lat2, lon2 = geo2.latitude, geo2.longitude
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def do_speedoflight(db):
    country_cable_data = None
    traceroute_data = {}
    country_route_data = {}
    ip_geolocation_data = {}
    with open("data/country_hop_cable.json", 'r') as fp:
        country_cable_data = json.load(fp)
    print("Submarine Cable per Country Data Loaded")
    
    for data in mongo_client[db]["traceroutes"].find():
        key = "%d - %d" % (data["msm_id"], data["prb_id"])
        traceroute_data[key] = data
    print("Traceroute Data Loaded")

    for data in mongo_client[db]["router_ip_geolocations"].find():
        ip_geolocation_data[data["ip"]] = data["geolocation"]
    print("Router IP Geolocation Data Loaded")

    for data in mongo_client[db]["country_routes"].find():
        key = data["country_code"] + data["dst_ip"]
        country_route_data[key] = data
    print("Country Route Data Loaded")

    records = []
    for _, route in country_route_data.items():
        dst_ip = route["dst_ip"]
        code = route["country_code"]
        country_route = route["result"]
        msm_id = route["msm_id"]
        prb_id = route["prb_id"]

        print(code, dst_ip)

        key = "%d - %d" % (msm_id, prb_id)
        traceroute = traceroute_data[key]["result"]

        bundles = []

        cum_start_hop_index = 0
        for i in range(len(country_route)):
            cables = []
            start_hop = country_route[i]
            cum_start_hop_index += start_hop["count"]
            key = ""
            if start_hop["country"] == "Unknown":
                continue
            start_hop_traceroute_index = cum_start_hop_index - 1

            start_ip = ""
            start_geo = None
            start_rtt = 0.0

            ip_count = {}
            good = False
            for trial in traceroute[start_hop_traceroute_index]["result"]:
                # {ip address: (count, avg rtt)}
                if "from" in trial.keys() and "rtt" in trial.keys():
                    if trial["from"] in ip_geolocation_data.keys():
                        ip = trial["from"]

                        for method in ip_geolocation_data[ip].keys():
                            if len(ip_geolocation_data[ip][method]) == 1:
                                # if ip not in ip_count.keys():
                                #     ip_count[ip] = [0, 0.0]

                                # cur_count = ip_count[ip][0]
                                # cur_rtt = ip_count[ip][1]

                                # ip_count[ip][0] += 1 # number of appearance
                                # ip_count[ip][1] = (cur_rtt * cur_count + trial["rtt"]) / (cur_count + 1) # average rtt

                                if ip not in ip_count.keys():
                                    ip_count[ip] = [1, trial["rtt"]]
                                else:
                                    cur_rtt = ip_count[ip][1]
                                    
                                    ip_count[ip][0] += 1 # number of appearance
                                    if trial["rtt"] > cur_rtt:
                                        ip_count[ip][1] = trial["rtt"] # max rtt

                                good = True
                                break
                        
            if good:
                # result = sorted(list(ip_count.items()), key=lambda x:x[1][0], reverse=True) # sort based on frequency
                result = sorted(list(ip_count.items()), key=lambda x:x[1][1], reverse=True) # sort based on min rtt
                
                start_ip = result[0][0]
                start_rtt = result[0][1][1]

            if start_ip == "":
                # for the inproperly received RIPE measurement traceroute hop result
                continue

            for method in ip_geolocation_data[ip].keys():
                if len(ip_geolocation_data[start_ip][method]) == 1:
                    start_geo = Geolocation(
                        ip_geolocation_data[start_ip][method][0]["Lat"], 
                        ip_geolocation_data[start_ip][method][0]["Lon"], 
                        ip_geolocation_data[start_ip][method][0]["Code"]
                    )
                    break

            end_ip = ""
            end_geo = None
            end_rtt = 0.0
            cum_end_hop_index = cum_start_hop_index
            for end_hop in country_route[i+1:]:
                end_hop_traceroute_index = cum_end_hop_index
                cum_end_hop_index += end_hop["count"]

                if end_hop["country"] == "Unknown":
                    continue
                elif start_hop["country"] == end_hop["country"]:
                    break
                else:
                    ip_count = {}
                    good = False
                    # print(end_hop_traceroute_index)
                    # print(traceroute)
                    for trial in traceroute[end_hop_traceroute_index]["result"]:
                        if "from" in trial.keys() and "rtt" in trial.keys():
                            if trial["from"] in ip_geolocation_data.keys():
                                ip = trial["from"]
                                for method in ip_geolocation_data[ip].keys():
                                    if len(ip_geolocation_data[ip][method]) == 1:
                                        # if ip not in ip_count.keys():
                                        #     ip_count[ip] = [0, 0.0]

                                        # cur_count = ip_count[ip][0]
                                        # cur_rtt = ip_count[ip][1]
                                        
                                        # ip_count[ip][0] += 1 # number of appearance
                                        # ip_count[ip][1] = (cur_rtt * cur_count + trial["rtt"]) / (cur_count + 1) # average rtt

                                        if ip not in ip_count.keys():
                                            ip_count[ip] = [1, trial["rtt"]]
                                        else:
                                            cur_rtt = ip_count[ip][1]
                                            
                                            ip_count[ip][0] += 1 # number of appearance
                                            if trial["rtt"] < cur_rtt:
                                                ip_count[ip][1] = trial["rtt"] # min rtt

                                        good = True
                                        break
                                
                    if good:
                        # result = sorted(list(ip_count.items()), key=lambda x:x[1][0], reverse=True) # sort based on frequency
                        result = sorted(list(ip_count.items()), key=lambda x:x[1][1]) # sort based on min rtt
                        
                        end_ip = result[0][0]
                        end_rtt = result[0][1][1]
                    
                    if end_ip == "":
                        # for the inproperly received RIPE measurement traceroute hop result
                        continue

                    key = start_hop["country"]+'-'+end_hop["country"]

                    for method in ip_geolocation_data[ip].keys():
                        if len(ip_geolocation_data[end_ip][method]) == 1:
                            end_geo = Geolocation(
                                ip_geolocation_data[end_ip][method][0]["Lat"], 
                                ip_geolocation_data[end_ip][method][0]["Lon"], 
                                ip_geolocation_data[end_ip][method][0]["Code"]
                            )
                            break
                    break

            if key != "" and key in country_cable_data.keys():
                # print(key)
                # print(start_ip, start_hop_traceroute_index)
                # print(end_ip, end_hop_traceroute_index)

                latency = (end_rtt - start_rtt) / 2000
                for cable in country_cable_data[key]:
                    # Speed of light test
                    for landing_s in cable["landings_latlng"]:
                        matched = False
                        landing_s_geoloc = Geolocation(landing_s[0], landing_s[1])
                        for landing_d in cable["landings_latlng"]:
                            if landing_d == landing_s:
                                continue
                            landing_d_geoloc = Geolocation(landing_d[0], landing_d[1])
                            path_len = geo_distance(start_geo, landing_s_geoloc) + \
                                        geo_distance(landing_s_geoloc, landing_d_geoloc) + \
                                        geo_distance(landing_d_geoloc, end_geo)

                            min_latency = path_len / C # (seconds)

                            if latency >= min_latency:
                                cables.append(cable["name"])
                                matched = True
                                break
                        if matched:
                            break

                if len(cables) == 0:
                    continue

                bundle = {
                    "start": {
                        "ip": start_ip, 
                        "geolocation": start_geo.to_dict()
                    }, 
                    "end": {
                        "ip": end_ip, 
                        "geolocation": end_geo.to_dict()
                    }, 
                    "latency": latency,
                    "code": code, 
                    "dst_ip": dst_ip, 
                    "cables": cables
                }

                bundles.append(bundle)

        if len(bundles) > 0:
            records.append(UpdateOne(
                {"dst_ip": dst_ip, "code": code}, 
                {"$set": {"bundle": bundles}}, 
                upsert=True))

    print(len(records))

    # submarine_submarine_db[mongo_prefix+"speed_of_lights"].bulk_write(records)

    mongo_client[db]["speed_of_lights"].bulk_write(records)

'''
Heuristic:
Let the following notations:
    P: probe initialized traceroute, could be the first or second hop router, otherwise use the country location
    S: destination server location
If there is a land route between P and S, then for a traffic to be routed to the destination, submarine cable must be involved

Result:
This heuristic yields a set of "must" submarine cable hit

Caveat:
Drivability test is not totally reliable
It is only a proximation to land routes
'''
API = os.getenv("API")
gmap_client = None
def init_google_client(key):
    global gmap_client
    if not key:
        print("No API key provided, aborting")
        exit()
    gmap_client = googlemaps.Client(key=key)
    print("Google client initialized")

drivable_cache = {}
def load_drivable_cache():
    global drivable_cache
    with open("data/new_drivable_cache.json", 'r') as fp:
        drivable_cache = json.load(fp)
    print("Drivable Cache Loaded")

def get_key(geo1, geo2):
	k1 = "%.0f,%.0f - %.0f,%.0f" % (geo1.latitude, geo1.longitude, geo2.latitude, geo2.longitude)
	k2 = "%.0f,%.0f - %.0f,%.0f" % (geo2.latitude, geo2.longitude, geo1.latitude, geo1.longitude)
	return k1, k2

# Returns whether two location is drivable
def check_drivability(geo1, geo2):
    key1, key2 = get_key(geo1, geo2)

    if key1 == key2:
        return 1

    cache_hit = False
    key = None

    if key1 in drivable_cache.keys():
        key = key1 
        cache_hit = True
    elif key2 in drivable_cache.keys():
        key = key2
        cache_hit = True
    
    drivable = None
    text = None
    if cache_hit:
        drivable = drivable_cache[key]["drivable"]
        text = drivable_cache[key]["text"]
    else:
        geo_str1 = str(geo1)
        geo_str2 = str(geo2)

        print("Search")

        directions_result = gmap_client.directions(geo_str1, geo_str2, mode="driving", avoid=["ferries"])

        if len(directions_result) > 0:
            route = directions_result[0]["legs"][0]
            for step in route["steps"]:
                key_list = list(step.keys())[:]
                for k in key_list:
                    if k != "html_instructions":
                        del step[k]

            text = json.dumps(route)
            
            if "ferry" in text or "ferries" in text:
                text = "ferry"
                drivable = -1
            else:
                text = "drivable"
                drivable = route["distance"]["value"]
        else:
            text = ""
            drivable = -1
        
        drivable_cache[key1] = {
            "drivable": drivable, 
            "text": text
        }
        
        with open("data/temp_drivable_cache.json", 'w') as fp:
            json.dump(drivable_cache, fp, indent=4)

        time.sleep(0.25)

    return drivable

def save_drivable_cache():
    with open("data/new_drivable_cache.json", 'w') as fp:
        json.dump(drivable_cache, fp, indent=4)
    print("Drivable Cache Saved")

class Match:
    def __init__(self, code, dst_ip, drivable):
        self.code = code
        self.dst = dst_ip
        self.drivable = drivable
    
    def to_dict(self):
        return {
            "country_code": self.code, 
            "dst_ip": self.dst, 
            "drivable": self.drivable
        }

def do_drivability(db):
    country_ip_data = {}
    ip_geolocation_data = {}
    country_run_data = {}
    for data in mongo_client[db]["ips"].find():
        country_ip_data[data["country_code"]] = data
    print("IP Data Loaded")

    for data in mongo_client[db]["geolocations"].find():
        ip_geolocation_data[data["ip"]] = data["geolocation"]
    print("Geolocation Data Loaded")

    for data in mongo_client[db]["runs"].find():
        country_run_data[data["country_code2"]] = data
    print("Run Data Loaded")

    '''
    {
        country_code: access ip
    }
    '''
    code_access_ip = {}
    for code, ips in country_ip_data.items():
        for access_ip in ips["access_ip"]:
            code_access_ip[code] = access_ip.replace('_', '.')
    
    '''
    {
        country_code: access ip geolocation (class Geolocation)
    }
    '''
    code_access_geo = {}
    for code in code_access_ip.keys():
        lat, lon = country_run_data[code]["access_ip_info"]["loc"].split(',')
        code_access_geo[code] = Geolocation(lat.strip(), lon.strip())

    '''
    {
        country_code: [destination ips]
    }
    '''
    code_destinations = {}
    for code in code_access_ip.keys():
        code_destinations[code] = [ip.replace('_', '.') for ip in country_ip_data[code]["match_ips"].keys()]
    
    '''
    {
        country_code: {
            ip: destination ip geolocation (class Geolocation)
        }
    }
    '''
    code_destinations_geo = {}
    for code, ips in code_destinations.items():
        code_destinations_geo[code] = {}
        for ip in ips:
            code_destinations_geo[code][ip] = None
            for method in ip_geolocation_data[ip]:
                if len(ip_geolocation_data[ip][method]) == 1:
                    code_destinations_geo[code][ip] = Geolocation(ip_geolocation_data[ip][method][0]["Lat"], ip_geolocation_data[ip][method][0]["Lon"])
                    break

    # print(code_access_geo)
    # print(code_destinations_geo["CN"])
    # exit()

    # initialize data
    init_google_client(API)
    load_drivable_cache()

    # Drivability test
    for code, start in code_access_geo.items():
        records = []
        for ip, end in code_destinations_geo[code].items():
            print(code, ip, start, end)

            drivable = None
            if start and end:
                drivable = check_drivability(start, end)
            else:
                drivable = 0

            record = Match(code, ip, drivable)

            records.append(UpdateOne(
                        {"dst_ip": record.dst, "code": record.code}, 
                        {"$set": {"drivable": record.drivable}}, 
                        upsert=True))

        mongo_client[db]["drivabilities"].bulk_write(records)

        save_drivable_cache()

if __name__ == "__main__":
    db = sys.argv[1]

    if sys.argv[2] == "sol":
        do_speedoflight(db)
    elif sys.argv[2] == "drive":
        do_drivability(db)