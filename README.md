# Criticality-SCN
<h2><a href="https://aqualab.cs.northwestern.edu/publications/">A User-View on the Criticality of the Submarine Cable Network</a></h2>

<p>This project contains the code and dataset accompanying the paper "Out of Sight, Not Out of Mind - A User-View on the Criticality of the 
Submarine Cable Network" appearing in the <a href="https://conferences.sigcomm.org/imc/2020/">Proceedings of the ACM Internet Measurement 
Conference (IMC) 2020<>/a, October 2020, Pittsburgh, USA.</p> 

<h3>Directory Structure</h3>

- `Crawling/` - Data and designed schema used for collecting web browsing data in clients' perspective. 
    - We currently cannot provide our source code for the crawler due to property right concerns. We encourage to use self-designed crawling scripts and follow the schema we provided. 
- `Geolocation` - Data and source code for geolocating the collected IP addresses from crawling. 
- `Traceroute` - Source code to launch RIPE Atlas traceroute measurement for analysis. 
- `CableMatching` - Data and source code for generating country level hops, identifying routes hitting SCN and mapping traceroutes to bundles of submarine cables. 
- `Results` - Statistics and graphs from our measurement results. 

<h3>Pipeline Overview</h3>

- Crawl websites; 
- Geolocate IP addresses for resources; 
- Generate traceroute dataset using RIPE; 
- Geolocate IP addresses for all routers identified in the traceroute dataset; 
- Generate country level routes; 
- Label resources that hits SCN; 
- Map routes to bundles of submarine cables; 

