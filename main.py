import sys
from despatchbaysdk_pss.despatch_functions import *

user_location = "admin"
#user_location = "ryzen"


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
book_shipments(manifest)
