# Submarine Cable Matching

## Set Up
python 3.6 is required to run this code
In the `config.json` file, please specify the MongoDB connection string under `mongo_str` to allow the scripts to connect to the database. 
In the `config.json` file, please specify the Google api under `google_api` to for making requests to Google Direction service. 

### Python dependencies
```
googlemaps
pymongo
bson
```

## Usage

### Command
First, use the following command to generate country level route from traceroute data. 
`python3 generate_hops.py (your DB name)`

The following command generates submarine cable bundles using speed of light testing. 
`python3 match_cables.py (your DB name) sol`

The following command performs drivability test to determine whether each requested resource must have taken a submarine cable route. 
`python3 match_cables.py (your DB name) drive`

Lastly, the following script checks whether any traceroute entry have potentially uses a satellite route (with a hop whose RTT is >= 476 ms). 
`python3 check_satellite.py (your DB name)`