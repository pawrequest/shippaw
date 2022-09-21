# from python.despatch_functions import *
# from python.AmDespSingle import *

## normal operation ##################
manifest = manifest_list_from_json()     ##
process_shipment(manifest)          ##
######################################

# shipment = shipmentFromXml(XMLFILE)
# process_shipment(shipment)


# manifest = manifest_list_from_json()
# for ship in manifest:
#     print(ship)


## get upcoming collection data ##############
# collections = client.get_collections()    ##
# pprint (collections)                      ##
##############################################

# manifest = manifest_from_json()
# def clean_objects(manifest):
#     for shipment in manifest:
#         print (shipment)
# # print(clean_objects(manifest[1]))
# print (manifest)

# if os.path.isfile(JSONFILE):
#     with open(JSONFILE) as f:
#         manifest = []
#         manifest_data = json.load(f)
#         pprint(manifest_data)
# else: print ("NOT A FILE")

# def main(foo, bar, **kwargs):
#     print('Called myscript with:')
#     print('foo = {}'.format(foo))
#     print('bar = {}'.format(bar))
#     for k, v in kwargs.items():
#         print('keyword argument: {} = {}'.format(k, v))
#
# if __name__=='__main__':
#     main(sys.argv[1], # foo
#          sys.argv[2], # bar
#          **dict(arg.split('=') for arg in sys.argv[3:])) # kwargs