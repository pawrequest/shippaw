import sys

from despatchbaysdk_pss.despatch_functions import *

# book_shipments(manifest_csv='Am_ship.csv')
# book_shipments(manifest_from_json())
#jsonfile = "data/AmShip.json"
#book_shipments


# # jsonfile = sys.argv[0] # run from powershell supplying json
# jsonfile = ".data/AmShip.json" # run from project json
#
# # collections = client.get_collections() # shows upcoming collections

manifest = manifest_from_json(sys.argv[0])
book_shipments(manifest)
# print("gsdgsd", os.path.realpath(__file__))