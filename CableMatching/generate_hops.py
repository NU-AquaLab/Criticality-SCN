from pymongo import MongoClient, InsertOne, UpdateOne
import json, sys

mongo_config = None
with open("../config.json", 'r') as fp:
    mongo_config = json.load(fp)["mongo_str"]
mongo_client = MongoClient(mongo_config)

db = sys.argv[1]

geolocation_collection = mongo_client[db]["router_ip_geolocations"]
route_collection = mongo_client[db]["country_routes"]
traceroute_collection = mongo_client[db]["traceroutes"]

geo_data = {}
for data in geolocation_collection.find():
    geo_data[data["ip"]] = data["geolocation"]

operations = []

count = 0

country_ip_traceroutes = {}
for data in traceroute_collection.find():
    code = data["country_code"]
    dst_ip = data["dst_addr"]
    if code not in country_ip_traceroutes.keys():
        country_ip_traceroutes[code] = {}
    if dst_ip not in country_ip_traceroutes[code]:
        country_ip_traceroutes[code][dst_ip] = []
    country_ip_traceroutes[code][dst_ip].append(data)    

results = {}
for code in country_ip_traceroutes:
    ip_traceroutes = country_ip_traceroutes[code]
    for dst_ip in ip_traceroutes:
        traceroutes = ip_traceroutes[dst_ip]
        for data in traceroutes:
            msm_id = data["msm_id"]
            prb_id = data["prb_id"]
            count += 1
            print(count, data["country_code"], data["dst_addr"])
            hops = []

            hop = data["result"][0]
            ip = ""
            for trial in hop["result"]:
                if "from" in trial.keys():
                    if ip in set(geo_data.keys()):
                        ip = trial["from"]
                    break
            
            geo = {
                "Lat": "",
                "Lon": "", 
                "Code": "Unknown",
                "City": "", 
                "Time": ""
            }
            if ip != "":
                # hop with at least one valid response
                geo_info = geo_data[ip]

                for method in ["SERV", "RIPE"]:
                    if method in geo_info.keys() and len(geo_info[method]) == 1:
                        geo = geo_info[method][0]
                        break

            current_hop = {"country": geo["Code"], "count": 1}

            for hop in data["result"][1:]:
                ip = ""
                # ip_count = {}
                # good = False
                # for trial in hop["result"]:
                #     if "from" in trial.keys():
                #         good = True
                #         ip = trial["from"]
                #         if ip not in ip_count.keys():
                #             ip_count[ip] = 0
                #         ip_count[ip] += 1

                # if good:
                #     result = sorted(list(ip_count.items()), key=lambda x:x[1], reverse=True)
                #     ip = result[0][0]

                for trial in hop["result"]:
                    if "from" in trial.keys():
                        if ip in set(geo_data.keys()):
                            ip = trial["from"]
                        break
                
                geo = {
                    "Lat": "",
                    "Lon": "", 
                    "Code": "Unknown",
                    "City": "", 
                    "Time": ""
                }
                if ip != "":
                    # hop with at least one valid response
                    geo_info = geo_data[ip]

                    for method in ["SERV", "RIPE"]:
                        if method in geo_info.keys() and len(geo_info[method]) == 1:
                            geo = geo_info[method][0]
                            break

                if geo["Code"] == current_hop["country"]:
                    current_hop["count"] += 1
                else:
                    hops.append(current_hop)
                    current_hop = {"country": geo["Code"], "count": 1}

            hops.append(current_hop)

            operations.append(UpdateOne(
                {
                    "dst_ip": data["dst_addr"], 
                    "country_code": data["country_code"],
                    "msm_id": msm_id,
                    "prb_id": prb_id}, 
                {
                    "$set":
                        {
                            "result": hops
                        }
                }, upsert=True))

        if count % 100 == 0:
            route_collection.bulk_write(operations)
            operations = []

route_collection.bulk_write(operations)
