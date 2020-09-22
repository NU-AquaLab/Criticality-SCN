import json, sys, math, time, os
import googlemaps

def load_json(fn):
    data = None
    with open(fn, 'r') as fp:
        data = json.load(fp)
    return data

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
    try:
        drivable_cache = load_json("data/drivable_cache.json")
        print("Drivable Cache Loaded")
    except:
        print("No Cache provided")

def save_drivable_cache():
    with open("data/new_drivable_cache.json", 'w') as fp:
        json.dump(drivable_cache, fp, indent=4)
    print("Drivable Cache Saved")

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

'''
country_ip_map = {
    country_code: {
        access_ip_info: {
            ip,
            city,
            region,
            country,
            loc,
            org,
            postal,
            timezone
        }
    }, 
    matched_ips: [
        ip
    ]
}
'''
def generate_drivability(API, country_ip_map, ip_geolocation_map):
    
    '''
    {
        country_code: access ip geolocation (class Geolocation)
    }
    '''
    code_access_geo = {}
    for code in country_ip_map.keys():
        lat, lon = country_ip_map[code]["access_ip_info"]["loc"].split(',')
        code_access_geo[code] = Geolocation(lat.strip(), lon.strip())

    '''
    {
        country_code: [destination ips]
    }
    '''
    code_destinations = {}
    for code in country_ip_map.keys():
        code_destinations[code] = country_ip_map[code]["matched_ips"]
    
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
            for method in ip_geolocation_map[ip].keys():
                if len(ip_geolocation_map[ip][method]) == 1:
                    code_destinations_geo[code][ip] = Geolocation(
                        ip_geolocation_map[ip][method][0]["Lat"], 
                        ip_geolocation_map[ip][method][0]["Lon"]
                    )
                    break

    # initialize data
    init_google_client(API)
    load_drivable_cache()

    drivability_results = []
    # Drivability test
    for code, start in code_access_geo.items():
        for ip, end in code_destinations_geo[code].items():
            print(code, ip, start, end)

            drivable = None
            if start and end:
                drivable = check_drivability(start, end)
            else:
                drivable = 0

            record = Match(code, ip, drivable)

            drivability_results.append({
                "dst_ip": record.dst, 
                "code": record.code, 
                "drivable": record.drivable
            })

        save_drivable_cache()
        
    return drivability_results