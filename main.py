import sys

from despatchbaysdk_pss.despatch_functions import *

# book_shipments(manifest_csv='Am_ship.csv')
# book_shipments(manifest_from_json())

manifest = manifest_from_json()
pprint(manifest)
book_shipments(manifest)
