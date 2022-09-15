import sys
from python.despatch_functions import *

# user_location = "admin"
user_location = "ryzen"


# book_shipments(manifest_csv='Am_ship.csv')
# book_shipments(manifest_from_json())
#jsonfile = "data/AmShip.json"
#book_shipments


# # jsonfile = sys.argv[0] # run from powershell supplying json
# jsonfile = ".data/AmShip.json" # run from project json
#
# collections = client.get_collections() # shows upcoming collections
# pprint (collections)

manifest = manifest_from_json()
process_manifest(manifest)
#
# def clean_objects(manifest):
#     for key, shipment in manifest:
#         pprint (shipment)

# shipper = Shipment(manifest['Items'][0])
# print("SHIPPER",shipper)