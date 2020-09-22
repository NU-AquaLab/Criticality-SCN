import json, sys
from ripe.atlas.cousteau import AtlasResultsRequest
from pymongo import MongoClient, InsertOne
from datetime import datetime
from copy import deepcopy

mongo_config = None
ripe_config = None
with open("../config.json", 'r') as fp:
    config = json.load(fp)
    mongo_config = config["mongo_str"]
    ripe_config = config["ripe_api"]
mongo_client = MongoClient(mongo_config)

db = sys.argv[2]

measurement_collection = mongo_client[db]["measurement_ids"]
traceroute_collection = mongo_client[db]["traceroutes"]

err = {}

for record in measurement_collection.find():
    country_code = record["country_code"]
    measurement_ids = record["measurement_id"]

    end_error = True

    print(country_code, len(measurement_ids))
    count = 0

    operations = []
    error = False
    # fetching
    for id in measurement_ids:
        print("Fetching %s" % id)
        kwargs = {
            "msm_id": id
        }
        is_success, results = AtlasResultsRequest(**kwargs).create()

        if is_success:
            if len(results) < 1:
                print("WARNING...", country_code)
                if country_code not in err:
                    err[country_code] = []

                if end_error:
                    err[country_code].append([count, count])
                    end_error = False
                err[country_code][-1][1] += 1

                error = True

                count += 1

                continue

            end_error = True
            for r in results:
                result = deepcopy(r)
                result["country_code"] = country_code
                result["status"] = "new"
                result["run"] = "SEPT"
                # print(result)
                # traceroute_collection.insert_one(result)
                operations.append(InsertOne(result))
        else:
            print("Fetch measurement failed")
        
        count += 1

    if error:
        continue

    traceroute_collection.bulk_write(operations)
    
    print("Finish Pushing to DB", country_code)

print("ERROR:", err)
