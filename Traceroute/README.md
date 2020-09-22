# Traceroute

## Set Up
python 3.6 is required to run this code
In the `config.json` file, please specify the MongoDB connection string under `mongo_str` to allow the scripts to connect to the database. 
In the `config.json` file, please specify the RIPE Atlas API under `ripe_api` to allow the scripts to generate traceroute measurements. 

### Python dependencies
```
pymongo
bson
ripe.atlas.cousteau
```

## Usage

### Command
The following command will execute the script and generate RIPE Atlas Traceroute measurements. 
`python3 RIPE_traceroute.py (your DB name)`
This script reads the dataset from MongoDB. For each record, it reads the country of origin for that entry, and launch RIPE traceroute using a probe in that country towards all resource IP addresses. 

After the first script completes, run the following command to fetch the scripts from RIPE and push to MongoDB. 
`python3 save_RIPE_result.py (your DB name)`
