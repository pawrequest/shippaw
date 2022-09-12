import sys

from despatchbaysdk_pss.despatch_functions import *

# book_shipments(manifest_csv='Am_ship.csv')
# book_shipments(manifest_from_json())
jsonfile = "files/Amship.json"
#book_shipments(jsonfile=sys.argv[1])
book_shipments(jsonfile)
# collections = client.get_collections() # shows upcoming collections
