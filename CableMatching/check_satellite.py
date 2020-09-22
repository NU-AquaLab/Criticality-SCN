
from pymongo import MongoClient, UpdateOne
from bson.objectid import ObjectId
import googlemaps
import json, sys, math, time, os

mongo_config = None
with open("../config.json", 'r') as fp:
    mongo_config = json.load(fp)["mongo_str"]
mongo_client = MongoClient(mongo_config)

db = sys.argv[1]

traceroute_collection = mongo_client[db]["traceroutes"]
sol_collection = mongo_client[db]["sol_bundles"]
dri_collection = mongo_client[db]["drivabilities"]

traceroutes = []
for data in traceroute_collection.find():
    traceroutes.append(data)

operations = []
for traceroute in traceroutes:
    satellite = False
    for hop_index in range(len(traceroute["result"])):
        max_rtt = -99999
        found = False
        for trial in traceroute["result"][hop_index]["result"]:
            if 'rtt' in trial.keys() and float(trial["rtt"]) > max_rtt:
                max_rtt = float(trial["rtt"])
                found = True
        
        if not found:
            continue
        
        found = False
        min_rtt = 99999
        if hop_index == len(traceroute["result"]) - 1:
            # reaches to the last hop, no need to check
            break

        end_hop = traceroute["result"][hop_index+1]
        for trial in end_hop["result"]:
            if 'rtt' in trial.keys() and float(trial["rtt"]) < min_rtt:
                min_rtt = float(trial["rtt"])
                found = True
        
        if not found:
            continue

        if min_rtt - max_rtt > 476:
            print(min_rtt - max_rtt, traceroute["country_code"], traceroute["msm_id"], traceroute["dst_addr"], traceroute["run"])
            satellite = True
            break

    operations.append(UpdateOne(
        {
            "code": traceroute["country_code"], 
            "dst_ip": traceroute["dst_addr"], 
            "run": traceroute["run"]
        }, 
        {"$set": {"satellite": satellite}}
    ))

sol_collection.bulk_write(operations)
dri_collection.bulk_write(operations)