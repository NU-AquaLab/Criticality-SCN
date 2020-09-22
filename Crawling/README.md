# Crawling

## Set Up
python 3.6 is required to run this code

We recommend using database for data storage. 
For our experiment, we use [MongoDB](https://www.mongodb.com/)

In the `config.json` file, please specify the MongoDB connection string under `mongo_str` to allow the scripts to connect to the database. 

### Output Schema
We design our crawler to output two set of data for each run on each country. 

```
run: {
    country_code: Alpha-2 country code for the country crawled, 
    start_time: Timestamp for starting the experiment
    access_ip_info: {
        ip: IP address of the VPN server used, 
        city, region, country, postal, timezone: geolocation details of the VPN server, 
        loc: latitude and longitude of the VPN server (e.g. "41.8500,-87.6500")
    }
}
request: {
    country_code: Alpha-2 country code for the country crawled, 
    requests: [
        {
            "initiator": The url that makes the resource request,
            "ip": IP address of the resource,
            "method": ["GET" / "POST" / etc],
            "statusCode": 200 / etc,
            "tabId": A unique ID for each tab opened by browser (to group resources requested by same website together),
            "timeStamp": ,
            "type": Type of the resource, ["main_frame" / "script" / "css" / etc],
            "url": URL of the resource
        }, 
    ]
}
```

## Data

### VPN Config
We here provide a list of all OpenVPN configuration files in the `ovpn_configs` directory. The exact VPN config used for each countries in our experiment are listed in `vpn_used.json`. 

The VPN services we used includes NordVPN and HMA VPN. In order to use those services, you would need to first obtain subscriptions from those VPN service provider and provide your credentials when connecting the VPN. 

### Websites Crawled
We used Alexa Top 50 Country Sites as our proxy for end users' daily browsing activities. The site data were collected on 2020/02/15 (`alexa_top_50_20200215.json`). 