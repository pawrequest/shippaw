def adjust_address(manifest): # takes dict oif dicts with customer name as keys
#     print("Which Shipment To Adjust?\n")
#     for count, (key, shipment) in enumerate(list(manifest.items())):
#         print(count + 1, shipment[customer_field], shipment[date_object_field].date, "To:", shipment[address_object_field].street)
#     # adjust_input = input('\nSelect Shipment 1 - ' + str(len(manifest.items())) + '. Enter 0 to cancel shipment and move on, "exit" to exit \n')
#
#     while True:
#         try:
#             adjust = input('\nSelect Shipment 1 - ' + str(len(manifest.items())) + '. Enter 0 to cancel shipment and move on, "exit" to exit \n')
#         except ValueError:
#             print("Try A number")
#             continue
#         except adjust > len(manifest.items()):
#             print("Too High")
#             continue
#         else:
#             print("selectyed")
#             break
#     if adjust == 0:
#         print("SHIPMENT Cancelled - ", manifest[adjust], "User Cancelled\n")
#         return None
#     if adjust == "exit":
#         print("USER EXIT")
#         exit()
#     else:
#         print("ADJUSTING")
#         shipment = manifest[adjust]
#         shipment = adjust_shipment_address(shipment)
#         manifest[adjust] = shipment
#
#         print("NEW MANIFEST")
#         for count, (key, shipment) in enumerate(list(manifest.items())):
#             print(count + 1, shipment[customer_field], shipment[date_object_field].date, "To:", shipment[address_object_field].street)
#         again_input = input("Adjust Another? yes to again")
#         if again_input == "yes":
#             adjust_address(manifest)
#         return manifest

#

    # # display candidates and prompt selection
    # for count, candidate in enumerate(candidates, start=1):
    #     print("Candidate ", count, "|", candidate.address)
    # selection = int(input('Which candidate? ("0" to remove shipment from manifest, "exit" to exit) \n'))
    # selected_key = candidates[selection - 1].key
    # if selection == 0:
    #     if input('Remove Shipment From manifest? "yes" to continue\n') == "yes":
    #         manifest.remove(shipment)
    # elif selection == "exit":
    #     exit()
    # # apply cahnges
    # else:
    #     shipment[address_field] = client.get_address_by_key(selected_key)
    #     manifest[adjust_input - 1] = shipment
    # print("MANIFEST ADJUSTED:\n")
    # for count, shipment in enumerate(manifest, start=1):
    #     print(count, "|", shipment[customer_field], "|", shipment[address_firstline_field])
    # if input('Type "yes" to Adjust Another') == 'yes':
    #     adjust_address(manifest)

# def deliver_manifest(manifest):
#     for key, shipment in manifest.items():
#         customer = shipment[customer_field]
#         phone = shipment[phone_field]
#         email = shipment[email_field]
#         address = shipment[address_object_field]
#         boxes = int(float(shipment[boxes_field]))
#         send_date = shipment[date_object_field]
#         recipient_name = shipment[delivery_contact_field]
#         recipient_address = client.address(
#             company_name=customer,
#             country_code="GB",
#             county=address.county,
#             locality=address.locality,
#             postal_code=address.postal_code,
#             town_city=address.town_city,
#             street=address.street
#         )
#
#         recipient = client.recipient(
#             name=recipient_name,
#             telephone=phone,
#             email=email,
#             recipient_address=recipient_address
#
#         )
#         parcels = []
#         for x in range(boxes):
#             parcel = client.parcel(
#                 contents="Radios",
#                 value=500,
#                 weight=6,
#                 length=60,
#                 width=40,
#                 height=40,
#             )
#             parcels.append(parcel)
#
#         shipment_request = client.shipment_request(
#             parcels=parcels,
#             client_reference=customer,
#             collection_date=send_date,
#             sender_address=sender,
#             recipient_address=recipient,
#             follow_shipment='true'
#         )
#
#
#         services = client.get_available_services(shipment_request)
#         shipment_request.service_id = services[0].service_id
#
#         print("\n" + customer + "'s shipment of", boxes, "parcels to: ",
#               recipient.recipient_address.street, "on", shipment[date_object_field].date, "BY", services[0].name,
#               "COSTING:",
#               services[0].cost)
#         if input('Type "yes" to book, other to skip shipment\n') == 'yes':
#             print("BOOKING SHIPMENT")
#
#             # shipment_request.collection_date = shipment[date_object_field].date
#             # added_shipment = client.add_shipment(shipment_request)
#             # pprint(added_shipment)
#             # shipment_return = client.get_shipment(added_shipment)
#
#             # uncomment to book and get labels / tracking
#             # client.book_shipments([added_shipment])
#             # label_pdf = client.get_labels(shipment_return.shipment_document_id)
#             # label_string = 'data/parcelforce_labels/' + shipment['customer'] + "-" + shipment['collection_date'] + '.pdf'
#             # label_pdf.download(label_string)
#
#             shipment['shipped'] = True
#             # records despatch references
#             # # format / print label ??
#             continue
#         else:
#             continue
#     else:
#         print("no shipments confirmed, restarting")
#         book_shipments(manifest)
#     with open(logfile, 'w') as f:
#         #json.dump(manifest, f)
#         json.dumps(manifest, indent=4, sort_keys=True, default=str)