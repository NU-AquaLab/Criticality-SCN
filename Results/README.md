# Results

We make the data and analysis results generated from our experiment publicly available for researchers to utilize. In between April 2020 and Sept. 2020, we conducted two runs of experiment and collected two set of data. For our IMC 2020 paper we conducted analysis based on the aggregation of both set of data, with each dataset stored in `APR/` and `SEPT/` respectively. 

- `country_ips.json` - This file contains all IP addresses collected during the crawling for each country/region we selected for our experiment. 
```
country_ips = {
    country_alpha-2-code: {
        [
            IP address, 
        ]
    }
}
```