import pathlib
import sys
from python.despatch_functions import *

# ## normal operation ##################
# manifest = manifest_from_json()     ##
# process_manifest(manifest)          ##
# ######################################


## get upcoming collection data ##############
# collections = client.get_collections()    ##
# pprint (collections)                      ##
##############################################

manifest = manifest_from_json()
print (type(manifest))
for key, value in manifest:
    print (key, value)

# def clean_objects(manifest):
#     for key, shipment in manifest:
#         pprint (shipment)
