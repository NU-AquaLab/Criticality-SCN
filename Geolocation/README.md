# Geolocation

## Set Up
python 3.6 is required to run this code
In the `config.json` file, please specify the MongoDB connection string under `mongo_str` to allow the scripts to connect to the database. 
In the `config.json` file, please specify the RIPE Atlas API under `ripe_api` to allow the scripts to generate traceroute measurements. 

## Usage

### Command
The following command geolocates all resource IP addresses. 
`python3 IP_processor.py -d (your DB name) -m [RIPE | SERV]`

The following command geolocates all the router IP addresses obtained from RIPE Atlas traceroute measurements. 
This command should only be executed after obtaining RIPE traceroute results. 
`python3 IP_processor.py -d (your DB name) -m [RIPE | SERV]`

## Methodology
We utilize two major IP geolocation method for our experiment. 

### RIPE
RIPE method sends query for IP geolocation to [RIPE Atlas IPMap](https://ipmap.ripe.net/) service to obtain geolocation information of IP address. 

### SERV
SERV method utilizes the full url obtained from reverse DNS of the IP address. We then categorize all rDNS records into Google, Cloudfront, Amazon EC2 and MicroSoft Azure, and pipe these information through a two level analysis. For url identified as Google infrastructure, we obtain the airport code from the url and use airport-to-geolocation map to infer the geolocation. For Cloudfront, Amazon EC2 and MicroSoft Azure, we use the public available dataset that anounced by their websites that maps IP prefixes to regions. 