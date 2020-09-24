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
```
- `country_data.json` - This file contains the parsed statistics collected from online resources and generated measurement results from our experiment for each country in our dataset (see Section 4 and Section 5). 
```
```