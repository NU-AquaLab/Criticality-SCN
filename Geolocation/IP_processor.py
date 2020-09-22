import json, sys, random, time
import argparse

from IP_geolocator import Geolocator
from pymongo import MongoClient, InsertOne, UpdateOne
from bson.objectid import Objectid

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
        with open(fn, 'r') as fp:
            self.results = json.load(fp)
        
        print("File Loaded")

    # Load_db ip lists to be geolocated from MongoDB
    def Load_db(self, db):
        results = {}
        total = 0

        ips_collection = mongo_client[db]["ips"]
        data = ips_collection.find({"status": "new"})

        for result in data:
            print(result["country_code"])

            self.current_ids.append(result["_id"])
            results.update(result["match_ips"])
            total += len(result["match_ips"])

            results.update(result["access_ip"])
            total += len(result["access_ip"])

        for result in results:
            ip = result.replace('_', '.')
            self.results[ip] = results[result]

        print("Database Loaded: # of unique IPs %d; # of all IPs: %s" % (len(self.results), total))

    def Load_access(self):
        ips_collection = mongo_client[db]["ips"]
        data = ips_collection.find()
        results = {}
        total = 0

        for result in data:

            results.update(result["access_ip"])
            total += len(result["access_ip"])

        for result in results:
            self.results[result.replace('_', '.')] = results[result]

        print("Database Loaded: # of unique IPs %d; # of all IPs: %s" % (len(self.results), total))

    # Dump self.results into a json file specified by fn
    def Dump(self):
        if self.current_file == "":
            print("Error: No file loaded")
            sys.exit(1)

        fn = self.current_file
        if not self.current_file.endswith(".geolocate.json"):
            fn = self.current_file + ".geolocate.json"

        with open(fn, 'w') as fp:
            json.dump(self.results, fp, indent=2)
        print("File Stored")

    def Dump_db(self, db):
        if len(self.results) == 0:
            return
        ips_collection = mongo_client[db]["ips"]
        geolocations_collection = mongo_client[db]["geolocations"]
        records = []
        for record in self.results:
            records.append(UpdateOne(
                {"ip": record}, 
                {"$set": {"geolocation": self.results[record]}}, 
                upsert=True))

        for id in self.current_ids:
            update(ips_collection, {'_id': ObjectId(id)}, {'$set': {'status': 'geolocated'}})

        geolocations_collection.bulk_write(records)
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