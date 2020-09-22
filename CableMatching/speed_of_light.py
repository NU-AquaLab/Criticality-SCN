import json, sys, math, time, os

def load_json(fn):
    data = None
    with open(fn, 'r') as fp:
        data = json.load(fp)
    return data

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

# geo_distance:
# Takes two Geolocation objects
# Returns the distance calculated
def geo_distance(geo1, geo2):
    lat1, lon1 = geo1.latitude, geo1.longitude
    lat2, lon2 = geo2.latitude, geo2.longitude
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

'''
country_route: {
    dst_ip, 
    code, (country code alpha-2)
    msm_id, (for RIPE traceroute measurement reference)
    prb_id, (for RIPE measurement probe selected reference)
    route: [
        {
            country, (country code alpha-2, or Unknown if not geolocated)
            count (number of repeating countries aggregated in this hop)
        }
    ]
}

traceroute: RIPE Atlas traceroute measurement result format

ip_geolocation_map: {
    ip: {
        (geolocation method name, in our paper we used RIPE and SERV): [
            {
                Lat, 
                Lon, 
                Code, (country code alpha-2)
                City, 
                Time
            }
        ]
    }
}
'''
def do_speedoflight(country_route, traceroute, country_cable_map, ip_geolocation_map):
    bundles = []

    dst_ip = country_route["dst_ip"]
    code = country_route["country_code"]
    route = country_route["result"]
    msm_id = country_route["msm_id"]
    prb_id = country_route["prb_id"]

    start_hop_index = 0
    for i in range(len(route)):
        cables = []
        start_hop = route[i]
        start_hop_index += start_hop["count"]
        key = ""
        if start_hop["country"] == "Unknown":
            continue
        start_hop_traceroute_index = start_hop_index - 1

        start_ip = ""
        start_geo = None
        start_rtt = 0.0

        ip_count = {}
        good = False
        for trial in traceroute[start_hop_traceroute_index]["result"]:
            # {ip address: (count, avg rtt)}
            if "from" in trial.keys() and "rtt" in trial.keys():
                if trial["from"] in ip_geolocation_map.keys():
                    ip = trial["from"]

                    for method in ip_geolocation_map[ip].keys():
                        if len(ip_geolocation_map[ip][method]) == 1:
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

        for method in ip_geolocation_map[start_ip].keys():
            if len(ip_geolocation_map[start_ip][method]) == 1:
                start_geo = Geolocation(
                    ip_geolocation_map[start_ip][method][0]["Lat"], 
                    ip_geolocation_map[start_ip][method][0]["Lon"], 
                    ip_geolocation_map[start_ip][method][0]["Code"]
                )
                break

        end_ip = ""
        end_geo = None
        end_rtt = 0.0
        end_hop_index = start_hop_index
        for end_hop in route[i+1:]:
            end_hop_traceroute_index = end_hop_index
            end_hop_index += end_hop["count"]

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
                        if trial["from"] in ip_geolocation_map.keys():
                            ip = trial["from"]
                            for method in ip_geolocation_map[ip].keys():
                                if len(ip_geolocation_map[ip][method]) == 1:
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

                for method in ip_geolocation_map[end_ip]:
                    if len(ip_geolocation_map[end_ip][method]) == 1:
                        end_geo = Geolocation(
                            ip_geolocation_map[end_ip][method][0]["Lat"], 
                            ip_geolocation_map[end_ip][method][0]["Lon"], 
                            ip_geolocation_map[end_ip][method][0]["Code"]
                        )
                        break
                break

        if key != "" and key in country_cable_map.keys():
            # print(key)
            # print(start_ip, start_hop_traceroute_index)
            # print(end_ip, end_hop_traceroute_index)

            latency = (end_rtt - start_rtt) / 2000
            for cable in country_cable_map[key]:
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

    return {
        "dst_ip": dst_ip, 
        "code": code, 
        "msm_id": msm_id, 
        "prb_id": prb_id, 
        "bundle": bundles
    }

def generate_bundles(country_route_map, traceroute_map):
    country_hop_map = load_json("data/country_hop_cable.json")
    ip_geolocation_map = load_json("data/ip_geolocation.json")

    bundle_results = []
    for key, country_route in country_route_map.items():
        traceroute = traceroute_map[key]
        bundle_results.append(do_speedoflight(country_route, traceroute, country_hop_map, ip_geolocation_map))