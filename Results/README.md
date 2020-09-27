# Results

We make the data and analysis results generated from our experiment publicly available for researchers to utilize. In between April 2020 and Sept. 2020, we conducted two runs of experiment and collected two set of data. For our IMC 2020 paper we conducted analysis based on the aggregation of both set of data, with each dataset stored in `APR/` and `SEPT/` respectively. 

- `country_ips.json` - This file contains all IP addresses collected during the crawling for each country/region we selected for our experiment. 
```
country_ips = {
    country_alpha-2_code: [
        IP address, 
    ]
}
```
- `country_ip_route.json` - This file contains all country level routes generated from the RIPE Atlas traceroute measurement results. 
```
country_ip_route = {
    country_alpha-2_code: {
        destination_IP_address: {
            "country_code": country alpha-2 code,
            "dst_ip": destination IP address,
            "result": [
                _(list of country level route)_
                {
                    "country": country alpha-2 code for this hop ("Unknown" if not geolocated),
                    "count": number of traceroute hops geolocated to this country
                }
            ],
            "msm_id": RIPE Atlas Measurement ID,
            "prb_id": RIPE Atlas Probe ID
        }
    }
}
```
- `country_ip_drivability.json` - This file contains the result from drivability test (see Section 3.3). (Notice that the drivability results treat routes which require ferries as not drivable)
```
country_ip_drivability = {
    country_alpha-2_code: {
        destination_IP_address: {
            "country_code": country alpha-2 code,
            "dst_ip": destination IP address,
            "drivable": drivablity test result (-1 for not drivable; 0 for dst_ip not geolocated; all the drivable routes are stored with positive number where the number is the distance in meters)
        }
    }
}
```
- `country_ip_sol_bundles.json` - This file contains the result from speed of light test (see Section 3.3)
```
country_ip_sol_bundles = {
    country_alpha-2_code: {
        destination_IP_address: {
            "code": country alpha-2 code,
            "dst_ip": destination IP address,
            "bundle": [
                {
                    "start": (information about the last geolocated router before hitting SCN)
                    {
                        "ip": IP address of the starting router,
                        "geolocation": {
                            "Lat": latitude, 
                            "Lon": longitude, 
                            "Code": country alpha-2 code,
                        }
                    },
                    "end": (information about the first geolocated router after hitting SCN)
                    {
                        "ip": IP address of the starting router,
                        "geolocation": {
                            "Lat": latitude, 
                            "Lon": longitude, 
                            "Code": country alpha-2 code,
                        }
                    },
                    "latency": latency differentce between the start and end router in traceroute,
                    "code": country that the traceroute was launched,
                    "dst_ip": destination IP address,
                    "cables": [
                        list of cable names, 
                    ]
                }, 
            ]
        }
    }
}
```
- `country_data.json` - This file contains the parsed statistics collected from online resources and generated measurement results from our experiment for each country in our dataset (see Section 4 and Section 5). 
```
country_data = {
    country_alpha-2_code: {
        "name": country alpha-2 code,
        "n_ip": number of unique IP addresses observed,
        "n_geolocated": number of unique IP addresses geolocated,
        "p_geolocated": percentage of unique IP addresses geolocated,
        "n_unknown": number of unique IP addresses not geolocated,
        "n_foreign": number of unique IP addresses that are geolocated to a foreign country,
        "p_foreign": percentage of unique IP addresses that are geolocated to a foreign country,
        "n_population": population of this country,
        "n_gdp": gdp,
        "n_gdppc": gdp per capita,
        "n_user": number of internet users,
        "p_penetration": percentage of internet penetration,
        "n_cable": number of cables connected to this country,
        "n_resource": number of total resource loaded during crawling,
        "n_geolocatedresource": number of resources geolocated,
        "p_geolocatedresource": percentage of resources geolocated,
        "n_tabcount": number of tabs identified by Chrome during crawling,
        "n_match": number of resources that are identified as hitting SCN,
        "p_match": percentage of resources that are identified as hitting SCN,
        "n_cdnresource": number of resources that are identified as CDN hosted (CDNized),
        "p_cdnresource": percentage of resources that are identified as CDN hosted (CDNized),
        "n_cdnmatch": number of CDN hosted resource hitting SCN,
        "p_cdnhit": percentage of CDN hosted resource hitting SCN,
        "n_noncdnresource": number of resources that are identified as non-CDN hosted,
        "p_noncdnresource": percentage of resources that are identified as non-CDN hosted,
        "n_noncdnmatch": number of non-CDN hosted resource hitting SCN,
        "p_noncdnhit": percentage of non-CDN hosted resource hitting SCN,
        "n_nonindexmatch": number of tabs (sites) that have at least one non-index-page resource hitting SCN,
        "p_nonindexmatch": percentage of tabs (sites) that have at least one non-index-page resource hitting SCN,
        "n_indexmatch": number of tabs (sites) with index-page resource hitting SCN,
        "p_indexmatch": percentage of tabs (sites) with index-page resource hitting SCN,
        "n_cdnhost": number of tabs (sites) that have at least one CDN hosted resource,
        "p_cdnhost": percentage of tabs (sites) that have at least one CDN hosted resource,
        "n_cablehit": number of unique cables potentially hit by some traceroutes launched from this country,
        "n_bundle": number of unique SCN bundles hit by some traceroutes launched from this country
    },
}
```