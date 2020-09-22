import requests
import json
import time
import socket
import os
import ipaddress

class Geolocation:
    def __init__(self, ip):
        self.ip = ip # ip address string
        self.latitude = "" # latitude string
        self.longitude = "" # longitude string
        self.code = "" # country or region code string
        self.city = "" # city name string
        self.time = time.time() # time stamp of the measurement performed
    
    def to_dict(self):
        return {"Lat": self.latitude,
                "Lon": self.longitude, 
                "Code": self.code, 
                "City": self.city, 
                "Time": self.time
                }

    def __eq__(self, other):
        return self.code == other.code
    
class Geolocator:
    def __init__(self):
        # key: ip; value: dic { key: measurement type; value: list of geolocation results}
        self.results = {}

    # input: ip_list: a list of ip addresses to geolocate
    #        measurements: list of strings specifying types of measurements to performed
    def Geolocate(self, ip_list, measurements):
        failed = ip_list
        for m in measurements:
            if m == "RIPE":
                # RIPE active probing geolocation
                self.geolocate_RIPE(ip_list)
            elif m == "HLOC":
                # Hint based LOCation
                self.geolocate_HLOC(ip_list)
            elif m == "SERV":
                # SERVer infrastructure specific
                self.geolocate_SERV(ip_list)
            elif m == "LAST":
                # LAST hop before destination geolocation
                self.geolocate_LAST(ip_list)
            else:
                print("ERROR Unknown Measurement type")
        return

    # input: ip_list: a list of ip addresses to geolocate
    # Geolocate using RIPE active measurement
    def geolocate_RIPE(self, ip_list):
        failed_list = []
        redo_list = []

        for ip in ip_list:
            if ip not in self.results.keys():
                self.results[ip] = {}
            if "RIPE" not in self.results[ip].keys():
                self.results[ip]["RIPE"] = []
            result = query_RIPE(ip)
            if result is None:
                redo_list.append(ip)
            else:
                self.results[ip]["RIPE"].append(result.to_dict())

        print("STEP 1: RIPE Finished: Failed:", len(redo_list), "All:", len(ip_list))

        # if no need to redo
        if len(redo_list) == 0:
            return

        # wait for 10 mins to redo 
        time.sleep(10*60)
        for ip in redo_list:
            result = query_RIPE(ip)
            if result is None:
                failed_list.append(ip)
            else:
                self.results[ip]["RIPE"].append(result.to_dict())

        print("STEP 2: RIPE redo Finished: Failed:", len(failed_list), "All:", len(ip_list))

    # input: ip_list: a list of ip addresses to geolocate
    # Geolocate using reverse DNS and HLOC
    # NOTE: Done, but very low precision
    def geolocate_HLOC(self, ip_list):
        failed_list = []
        for ip in ip_list:
            if ip not in self.results.keys():
                self.results[ip] = {}
            if "HLOC" not in self.results[ip]:
                self.results[ip]["HLOC"] = [] 
        with open("./hloc_tmp/rdns", 'w') as fp:
            for ip in ip_list:
                print("Reverse DNS of %s" % ip)
                try:
                    reversed_dns = socket.gethostbyaddr(ip)
                    # write to rdns file
                    fp.write(ip)
                    fp.write(',')
                    fp.write(reversed_dns[0])
                    fp.write('\n')
                except socket.herror:
                    print("Unknown")
                    failed_list.append(ip)
        
        print("STEP 1: rDNS Finished: Failed:", len(failed_list), "All:", len(ip_list))

        # remove pre-existing files
        os.system("rm -rf hloc_tmp/preprocessing_output")
        exit_code = os.system("python3 -m hloc-tma17.src.data_processing.preprocessing hloc_tmp/rdns -n 1 -t hloc-tma17/src/data_processing/collectedData/tlds.txt -d hloc_tmp/preprocessing_output -i -v ipv4")
        print("STEP 2: preprocessing Finished: Exit Code:", exit_code)

        exit_code = os.system("python3 -m hloc-tma17.src.find_and_evaluate.create_trie hloc-tma17/locations.json hloc-tma17/blacklists/code.blacklist.txt -f hloc-tma17/blacklists/word.blacklist.txt")
        print("STEP 3: create trie Finished: Exit Code:", exit_code)

        exit_code = os.system("python3 -m hloc-tma17.src.find_and_evaluate.find_locations_with_trie hloc_tmp/preprocessing_output/rdns-0.ipencoded hloc-tma17/locations-trie.pickle -n 1 -e -s hloc-tma17/blacklists/special.blacklist.txt")
        print("STEP 4 PART 1: find locations ipencoded Finished: Exit Code:", exit_code)

        found = []
        not_found = []
        with open("./hloc_tmp/preprocessing_output/rdns-0-found.json", 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                found.extend(json.loads(line))
        with open("./hloc_tmp/preprocessing_output/rdns-0-not-found.json", 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                not_found.extend(json.loads(line))

        print("STEP 4 PART 1: ipencoded Found:", len(found), "Not Found:", len(not_found))

        exit_code = os.system("python3 -m hloc-tma17.src.find_and_evaluate.find_locations_with_trie hloc_tmp/preprocessing_output/rdns-0.cor hloc-tma17/locations-trie.pickle -n 1 -e -s hloc-tma17/blacklists/special.blacklist.txt")
        print("STEP 4 PART 2: find locations cor Finished: Exit Code:", exit_code)

        with open("./hloc_tmp/preprocessing_output/rdns-0-found.json", 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                found.extend(json.loads(line))
        with open("./hloc_tmp/preprocessing_output/rdns-0-not-found.json", 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                not_found.extend(json.loads(line))

        print("STEP 4 PART 2: cor and ipencoded Found:", len(found), "Not Found:", len(not_found))

        locations_map = {}
        with open("hloc-tma17/locations.json", 'r') as fp:
            locations_map = json.load(fp)

        for entry in found:
            countries = set()
            # each entry represents an IP address to be geolocated
            ip = entry["1"]

            print("Geolocating", ip)

            hint_loc = {}

            for hint in entry["3"]:
                # all hints for each entry

                for key in hint["1"]:
                    if len(key["2"]) < 2:
                        # ignore too ambiguous hints
                        # not sure whether this filter is valid
                        continue

                    # each hints may have multiple possible keys
                    geo = locations_map[str(key["0"])]
                    # 1: lat; 2: lon; 3: city; 5: state

                    if geo["3"] not in hint_loc.keys():
                        hint_loc[geo["3"]] = []

                    result = Geolocation(ip)
                    result.latitude = "%.2f" % geo["1"]
                    result.longitude = "%.2f" % geo["2"]
                    if geo["3"]:
                        result.city = geo["3"].title()
                    if geo["5"]:
                        result.code = geo["5"].upper()

                    if result.code in countries:
                        continue
                    else:
                        countries.add(result.code)

                    hint_loc[geo["3"]].append(result)

                    self.results[ip]["HLOC"].append(result.to_dict())

        # for key, value in self.results.items():
        #     print(key)
        #     for geo in value["HLOC"]:
        #         print(geo.to_dict())

    # input: ip_list: a list of ip addresses to geolocate
    # Geolocate using popular server databases or patterns
    def geolocate_SERV(self, ip_list):
        failed_list = []
        for ip in ip_list:
            if ip not in self.results.keys():
                self.results[ip] = {}
            if "SERV" not in self.results[ip].keys():
                self.results[ip]["SERV"] = []

        rdns = {}
        Other = []
        for ip in ip_list:
            print("Reverse DNS of %s: " % ip, end="")
            try:
                reversed_dns = socket.gethostbyaddr(ip)
                rdns[ip] = []
                rdns[ip].append(reversed_dns[0])
                for alias in reversed_dns[1]:
                    rdns[ip].append(alias)
                print(rdns[ip])
            except socket.herror:
                print("Unknown")
                failed_list.append(ip)
                Other.append(ip)
        
        print("STEP 1: rDNS Finished: Success:", len(rdns), "All:", len(ip_list))

        # Google: *.1e100.net; first three char of the first subdomain is airport code
        google = {}
        # Amazon: match IP to aws infrastructure location database
        amazon = {}
        # Cloudfront: *.cloudfront.net; first three char of the second subdomain is airport code
        cloudfront = {}
        # Microsoft Azure: match IP to azure infrastructure location database
        # NOTE: Azure IPs are generally not resolved by reverse DNS
        # Azure = {}

        ### DATABASE NEEDED
        # cdn77.com
        # akamaitechnologies.com
        # facebook.com

        for ip in rdns:
            match = False
            for r in rdns[ip]:
                if "amazon" in r or "aws" in r:
                    amazon[ip] = rdns[ip]
                    match = True
                    break
            for r in rdns[ip]:
                if r.endswith("1e100.net"):
                    google[ip] = rdns[ip]
                    match = True
                    break
            for r in rdns[ip]:
                if r.endswith("cloudfront.net"):
                    cloudfront[ip] = rdns[ip]
                    match = True
                    break
            if not match:
                Other.append(ip)

        print("STEP 2: split Finished: Amazon:", len(amazon), "google", len(google), "cloudfront", len(cloudfront))

        aws_loc = {}
        with open("serv_data/aws_locations.json", 'r') as fp:
            aws_loc = json.load(fp)
        aws_ip = []
        with open("serv_data/aws_ip_ranges.json", 'r') as fp:
            aws_ip = json.load(fp)["prefixes"]

        amazon_result = {}
        for ip in amazon:
            found = False
            try:
                for prefix in aws_ip:
                    net = ipaddress.ip_network(prefix["ip_prefix"])
                    if ipaddress.ip_address(ip) in net:
                        # Matched
                        found = True

                        loc = aws_loc[prefix["region"]]
                        result = Geolocation(ip)
                        result.latitude = loc["latitude"]
                        result.longitude = loc["longitude"]
                        result.code = loc["code"]
                        result.city = loc["city"]

                        amazon_result[ip] = result
                        self.results[ip]["SERV"].append(result.to_dict())
                        break
            except:
                break
            if not found:
                failed_list.append(ip)

        print("STEP 3 PART 1: amazon Finished: Success:", len(amazon_result))

        airport_loc = {}
        with open("serv_data/airport_loc.json", 'r') as fp:
            airport_loc = json.load(fp)

        google_result = {}
        for ip in google:
            failed = False
            geo = []
            for r in google[ip]:
                code = str(r.split('.')[0][:3]).upper()
                if code == "any":
                    continue
                try:
                    loc = airport_loc[code]
                    result = Geolocation(ip)
                    result.latitude = loc["lat"]
                    result.longitude = loc["lon"]
                    result.code = loc["code"]

                    if result not in geo:
                        google_result[ip] = result
                        geo.append(result)
                        self.results[ip]["SERV"].append(result.to_dict())
                except:
                    failed = True
            if failed:
                failed_list.append(ip)

        print("STEP 3 PART 2: google Finished: Success:", len(google_result))

        cloudfront_result = {}
        for ip in cloudfront:
            failed = False
            geo = []
            for r in cloudfront[ip]:
                code = str(r.split('.')[1][:3]).upper()
                try:
                    loc = airport_loc[code]
                    result = Geolocation(ip)
                    result.latitude = loc["lat"]
                    result.longitude = loc["lon"]
                    result.code = loc["code"]
                    cloudfront_result[ip] = result

                    if result not in geo:
                        cloudfront_result[ip] = result
                        geo.append(result)
                        self.results[ip]["SERV"].append(result.to_dict())
                except:
                    failed = True
            if failed:
                failed_list.append(ip)

        print("STEP 3 PART 3: cloudfront Finished: Success:", len(cloudfront_result))

        azure_result = {}
        azure_loc = {}
        with open("erv_data/azure_region_locations.json", 'r') as fp:
            azure_loc = json.load(fp)
        azure_ip = []
        with open("serv_data/azure_ip_ranges.json", 'r') as fp:
            azure_ip = json.load(fp)

        for ip in Other:
            found = False
            try:
                for (prefix, region) in azure_ip.items():
                    net = ipaddress.ip_network(prefix)
                    if ipaddress.ip_address(ip) in net:
                        # Matched
                        found = True

                        loc = azure_loc[region]
                        result = Geolocation(ip)
                        result.latitude = loc["latitude"]
                        result.longitude = loc["longitude"]
                        result.code = loc["code"]
                        result.city = loc["city"]
                        azure_result[ip] = result

                        self.results[ip]["SERV"].append(result.to_dict())
                        break
            except:
                break
            if not found:
                failed_list.append(ip)


        print("STEP 3 PART 4: azure Finished: Success:", len(azure_result))

        return
        
    # input: ip_list: a list of ip addresses to geolocate
    # Geolocate using the location of the hop before destination
    def geolocate_LAST(self, ip_list):
        pass

    # Group geolocations based on results
    # output: ip_groups: dictionary of lists of ips geolocated to same location
    def Group_Geolocations(self):
        ip_groups = {}
        for k in self.results.keys():
            for g in self.results[k]:
                key = "%s,%s" % (g.latitude, g.longitude)
                if key not in ip_groups.keys():
                    ip_groups[key] = []
                ip_groups[key].append(g)

        return ip_groups

# query_RIPE:
# Input: ip: ip address
# Output: geolocation: Geolocation object
# run through RIPE Atlas IPMap geolocation process to find the geolocation of ip
def query_RIPE(ip):
    result = Geolocation(ip)

    resp_json = None

    for _ in range(3):
        # 3 tries for get request
        try:
            ripe_url_prefix = "http://openipmap.ripe.net/api/v1/single-radius/"
            request_url = ripe_url_prefix + ip
            print("Requesting IP: %s" % request_url)
            # request for IP geolocation service
            r = requests.get(request_url, timeout=5)

            resp_json = json.loads(r.text)

            break
        except Exception as e:
            print("ERROR: problem during get request %s" % e)
            time.sleep(1)
            continue
    
    if not resp_json:
        return None
    
    if "locations" in resp_json.keys() and resp_json["locations"]:
        location_json = resp_json["locations"]

        top_location = location_json[0]

        if "countryCodeAlpha2" in top_location.keys():
            result.code = top_location["countryCodeAlpha2"]
        if "cityName" in top_location.keys():
            result.city = top_location["cityName"]
        if "longitude" in top_location.keys():
            result.longitude = "%.2f" % top_location["longitude"]
        if "latitude" in top_location.keys():
            result.latitude = "%.2f" % top_location["latitude"]

        print("Good")
        return result
    else:
        print("Redo")
        return None

    