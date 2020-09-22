import json
import xmltodict

data = None
with open("PublicIPs_MC_20180111.xml", 'r') as fp:
    data = fp.read()

tree = xmltodict.parse(data)

ret = None

with open("azure_region_location.json", 'r') as fp:
    ret = json.load(fp)

for region in tree["AzurePublicIpAddresses"]["Region"]:
    ret[region["@Name"]] = {}

with open("azure_region_location.json", 'w') as fp:
    json.dump(ret, fp, indent=4)