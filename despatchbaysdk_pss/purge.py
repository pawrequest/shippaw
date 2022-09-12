# def get_manifest_date_objects(manifest):
#     dates = client.get_available_collection_dates(sender, courier_id)
#     for count, shipment in enumerate(manifest):
#         ship_count = count
#         print(len(manifest))
#         print("Shipment", count + 1, "-", shipment[customer_field])
#         # # reverse send date and get matching collection dates
#         send_date_reversed = shipment[send_date_field].split("/")
#         send_date_reversed.reverse()
#         shipment[send_date_field] = '-'.join(send_date_reversed)
#         for count, date in enumerate(dates):
#             if date.date == shipment[send_date_field]:  # if date object matches reversed string
#                 shipment[date_object_field] = date
#                 print("DATE MATCH - Shipment for", shipment[customer_field], "can be collected on",
#                       shipment[date_object_field].date, "\n")
#                 manifest[ship_count] = shipment
#                 pprint(manifest[ship_count])
#                 break  # out of the date loop, back to shipment loop
#
#         else:  # no date match
#             print("\nNO COLLECTION ON SEND OUT DATE FOR", shipment[customer_field], "\n")
#             if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
#                 for count, date in enumerate(dates):
#                     print(count + 1, date.date)
#                 choice = int(input("\nChoose a Date\n")) - 1
#                 shipment[date_object_field] = dates[choice]
#                 manifest[ship_count] = shipment
#                 print("shipcouint", ship_count + 1)
#
#                 print("Collection Date Is Now ", shipment[date_object_field].date, "\n")
#                 # continue
#             manifest.remove(shipment)
#             print('Shipment Removed "' + shipment[customer_field] + '" .... Moving On\n')
#         print(shipment[customer_field])
#         # get_date_objects(manifest)
#     return (manifest)
def get_manifest_address_objects(manifest):
    for count, shipment in enumerate(manifest, start=1):
        # set search string - number or firstline
        if shipment[building_num_field] == 0: shipment[building_num_field] = False
        if not shipment[building_num_field]:
            search_string = shipment[address_firstline_field]
        else:
            search_string = shipment[building_num_field]
        # get object
        address_object = client.find_address(shipment[postcode_field], search_string)
        manifest[count - 1][address_object_field] = address_object
    return manifest

#
# def get_shipment_date_object(shipment):
#     print(shipment[customer_field], "Getting Dates")
#
#     dates = client.get_available_collection_dates(sender, courier_id)
#
#     send_date_reversed = shipment[send_date_field].split("/")
#     send_date_reversed.reverse()
#     shipment[send_date_field] = '-'.join(send_date_reversed)
#
#     for count, date in enumerate(dates):
#         if date.date == shipment[send_date_field]:  # if date object matches reversed string
#             shipment[date_object_field] = date
#             print("DATE MATCH - Shipment for", shipment[customer_field], "can be collected on",
#                   shipment[date_object_field].date, "\n")
#             return shipment
#     else:  # no date match
#         print("\nNO COLLECTION AVAILABLE FOR", shipment[customer_field], "\n")
#         if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
#             for count, date in enumerate(dates):
#                 print(count + 1, date.date)
#             choice = int(input("\nChoose a Date, 0 to cancel and move on\n") + 1)
#             if choice == 0:
#                 return 1
#             else:
#                 shipment[date_object_field] = dates[choice]
#                 print("Collection Date Is Now ", shipment[date_object_field].date, "\n")
#                 return shipment
#         else:
#             print("No alternative selected")
#             return 1
