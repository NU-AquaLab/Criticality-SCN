import json, sys, random, time
import argparse

from IP_geolocator import Geolocator
from pymongo import MongoClient, InsertOne, UpdateOne
from bson.objectid import ObjectId

mongo_config = None
with open("../config.json", 'r') as fp:
    mongo_config = json.load(fp)["mongo_str"]
mongo_client = MongoClient(mongo_config)

def update(co, query, update):
  co.update_one(query, update)

class Processor:
    def __init__(self):
        self.results = {}
        self.geolocator = Geolocator()
        self.current_file = ""
        self.current_ids = []

    def Process_ip(self, measurements):
        if len(self.results) == 0:
            return
        if len(measurements) == 0:
            return
        
        ip_list = list(self.results.keys())
        random.seed(time.time())
        random.shuffle(ip_list)
        self.geolocator.Geolocate(ip_list, measurements)

        # store measurement results
        for (ip, result) in self.geolocator.results.items():
            if ip not in self.results.keys():
                self.results[ip] = {}
            for m in measurements:
                if m not in self.results[ip].keys():
                    self.results[ip][m] = []
                # self.results[ip][m].extend(result[m])
                self.results[ip][m] = result[m]

        total = len(self.results)
        total_failed = 0
        total_succeed = 0
        succeed = {}
        failed = {}
        for m in measurements:
            succeed[m] = 0
            failed[m] = 0
        for r in self.results:
            good = False
            for m in measurements:
                if len(self.results[r][m]) == 0:
                    failed[m] += 1
                else:
                    good = True
                    succeed[m] += 1
            if good:
                total_succeed += 1
            else:
                total_failed += 1

        succ_str = "; ".join(["%s: %d" % (k, v) for (k, v) in succeed.items()])
        fail_str = "; ".join(["%s: %d" % (k, v) for (k, v) in failed.items()])
        print("Success details:", succ_str)
        print("Fail details:", fail_str)
        print("%d / %d geolocated, %d / %d failed" % (total_succeed, total, total_failed, total))

    # Load previously store database json file specified by fn to self.results
    def Load(self, fn):
        self.current_file = fn

        file_data = None
        with open(fn, 'r') as fp:
            file_data = json.load(fp)
        
        self.results = {}

        for code in file_data:
            for dst_ip in file_data[code]:
                for result in file_data[code][dst_ip]:
                    for hop in result["result"]:
                        for trial in hop["result"]:
                            if "from" in trial.keys():
                                ip = trial["from"]
                                self.results[ip] = {}

        print("File Data Loaded: # of unique IPs %d" % (len(self.results)))

    # Load_db ip lists to be geolocated from MongoDB
    def Load_db(self, db):
        # geolocations_collection = Submarine_db[db_prefix+"router_ip_geolocations"]
        # done = []

        # for result in geolocations_collection.find():
        #     done.append(result["ip"])

        traceroute_collection = mongo_client[db]["traceroutes"]
        data = traceroute_collection.find({"status": "new"})
        # data = traceroute_collection.find({"country_code": "CN"})
        self.results = {}

        c = 0
        for result in data:
            # if c >= count:
            #     break
            c += 1

            self.current_ids.append(result["_id"])
            for hop in result["result"]:
                for trial in hop["result"]:
                    if "from" in trial.keys():
                        ip = trial["from"]
                        self.results[ip] = {}

        print("Database Loaded: # of unique IPs %d" % (len(self.results)))

    def Dump_db(self, db):
        if len(self.results) == 0:
            return
        traceroute_collection = mongo_client[db]["traceroutes"]
        geolocations_collection = mongo_client[db]["router_ip_geolocations"]
        records = []
        for record in self.results:
            records.append(UpdateOne(
                {"ip": record}, 
                {"$set": {"geolocation": self.results[record]}}, 
                upsert=True))

        updates = []
        for id in self.current_ids:
            updates.append(UpdateOne(
                {'_id': ObjectId(id)}, 
                {'$set': {'status': 'geolocated'}}))

        geolocations_collection.bulk_write(records)
        traceroute_collection.bulk_write(updates)
        print("Database Stored")

if __name__ == "__main__":
    '''
    Supported measurement methods: 
    RIPE

    Input Json file of IP format
    {
        ip: {}
    }

    Output Json file of geolocated IP format
    {
        ip: {
            measurement method: [
                {
                    "Lat": Latitude,
                    "Lon": Longitude,
                    "Code": Country Code,
                    "City": City Name,
                    "Time": Time Stamp
                }
            ]
        }
    }
    '''
    parser = argparse.ArgumentParser(description='IP Geolocation.')
    parser.add_argument('-d', type=str, required=True, help="Name of the Database")
    parser.add_argument('-m', type=str, required=True, nargs='+', help='A list of measurement methods')

    args = parser.parse_args()
    
    processor = Processor()

    db = args.d

    processor.Load_db(db)
    processor.Process_ip(args.m)
    processor.Dump_db(db)