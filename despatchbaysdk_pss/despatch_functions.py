import json
import os
import sys

from .despatchbay_sdk import DespatchBaySDK
from pprint import pprint
import datetime

api_user = os.getenv('DESPATCH_API_USER')
api_key = os.getenv('DESPATCH_API_KEY')
client = DespatchBaySDK(api_user=api_user, api_key=api_key)
sender_id = '5536'
logfile = 'AmDespOutputLog.csv'
# jsonfile = PROVIDED AT CLI

# Commence Column Names
customer_field = 'To Customer'
phone_field = 'Delivery Tel'
email_field = 'Delivery Email'
address_field = 'Delivery Address'
boxes_field = 'Boxes'
send_date_field = 'Send Out Date'
postcode_field = 'Delivery Postcode'
hire_ref_field = 'Reference Number'
shipment_id_field = 'Shipment_id'
candidates_field = 'Candidates'
building_num_field = 'Building Num'
address_firstline_field = 'Address First Line'
searchterm_field = 'Search Term'
address_object_field = 'Address Object'


## imports json manifest file, adds Shipment_id of incremenetal 01+ and hire reference, returns dict ##
def manifest_from_json(jsonfile=sys.argv[1]):  # calls parse-shipment
    with open(jsonfile) as f:
        data = json.load(f)
        # Assign Shipment IDs from count and hire ref and parse address into num or firstline, populate manifest
        manifest = []
        for count, shipment in enumerate(data['Items'], start=1):
            shipment[shipment_id_field] = str(count).zfill(2) + shipment[hire_ref_field]
            shipment = parse_shipment_address(shipment[address_field], shipment)
            manifest.append(shipment)
        return manifest


def parse_shipment_address(crapstring, shipment):
    first_line = crapstring.split("\r")[0]
    first_block = (crapstring.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    for char in first_line:
        pass
    if first_char.isnumeric():
        shipment[building_num_field] = first_block
    shipment[address_firstline_field] = first_line
    return shipment


def adjust_address(manifest):
    # list shipments, prompt and confirm selection
    for count, shipment in enumerate(manifest, start=1):
        print(count, "-", shipment[address_object_field].street)
    adjust = int(input('Which Shipment to Adjust? \n'))
    print("Adjusting Shipment", adjust, ":", manifest[adjust - 1][customer_field[0]], "-",
          manifest[adjust - 1][address_object_field].street, "\n")

    # get shipment and candidates for address replacement
    shipment = manifest[adjust - 1]
    candidates = client.get_address_keys_by_postcode(shipment[postcode_field])
    shipment[candidates_field] = candidates

    # display candidates and prompt selection
    for count, candidate in enumerate(candidates, start=1):
        print("Candidate Address", count, ":", candidate.address)
    selection = int(input('Which candidate? ("0" to quit) \n'))
    selection_key = candidates[selection - 1].key
    if selection == 0:
        exit()

    # apply cahnges
    shipment[address_field] = client.get_address_by_key(selection_key)
    manifest[adjust - 1] = shipment
    print("MANIFEST ADJUSTED:\n")
    pprint(manifest[adjust - 1][address_field].street)
    if input('Type "yes" to Adjust Another') == 'yes':
        adjust_address(manifest)


def get_address_objects(manifest):
    for count, shipment in enumerate(manifest, start=1):
        # set search string - number or firstline
        if not shipment[building_num_field]:
            search_string = shipment[address_firstline_field]
        else:
            search_string = shipment[building_num_field]
        # get object
        address = client.find_address(shipment[postcode_field], search_string)
        print("\nShipment", count, "of", shipment['Boxes'], "Boxes To", address.street, "On",
              shipment['Send Out Date'], "(Date tbc)")
        manifest[count - 1][address_object_field] = address
        return manifest


def book_shipments(manifest):  # takes dict_list of shipments
    manifest = get_address_objects(manifest)
    print("MANIFEST ", manifest)
    proceed = input('\nEnter "yes" to proceed, "exit" to exit, other to adjust an address \n')
    if str(proceed) == "yes":
        deliver_manifest(manifest)
    elif str(proceed) == "exit":
        print("EXITING")
        exit()
    else:
        adjust_address(manifest)
        if input("\nType yes to deliver manifest \n") == 'yes':
            deliver_manifest(manifest)
        print("EXITING")


def deliver_manifest(manifest):
    for shipment in manifest:
        customer = shipment[customer_field][0]
        phone = shipment[phone_field]
        email = shipment[email_field]
        address = shipment[address_object_field].street
        print(address)
        boxes = int(float(shipment[boxes_field]))
        send_date = shipment[send_date_field]

        recipient = client.recipient(
            name=customer,
            telephone=phone,
            email=email,
            recipient_address=address)
        parcels = []
        for x in range(boxes):
            parcel = client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            parcels.append(parcel)
        sender = client.sender(
            address_id=sender_id
        )

        shipment_request = client.shipment_request(
            parcels=parcels,
            client_reference=customer,
            collection_date=send_date,
            sender_address=sender,
            recipient_address=recipient,
            follow_shipment='true'
        )

        services = client.get_available_services(shipment_request)
        dates = client.get_available_collection_dates(sender, services[0].courier.courier_id)
        print("\n" + customer + "'s shipment of", boxes, "parcels to: ",
              recipient.recipient_address.street, "on", dates[0].date, "BY", services[0].name, "COSTING:",
              services[0].cost)
        if input('Type "yes" to book and download pdf \n') != 'yes':
            print("exiting")
            exit()
        print("rolling on")
        exit()
        # shipment_request.service_id = services[0].service_id
        # shipment_request.collection_date = dates[0]
        # added_shipment = client.add_shipment(shipment_request)
        # client.book_shipments([added_shipment])
        # shipment_return = client.get_shipment(added_shipment)
        # label_pdf = client.get_labels(shipment_return.shipment_document_id)
        # label_string = './' + shipment['customer'] + "-" + shipment['collection_date'] + '.pdf'
        # label_pdf.download(label_string)
        # format / print label ??
        # with open('AmDespOutputLog.csv', 'a', newline='') as csvfile:
        #     writer = csv.writer(csvfile, delimiter=',')
        #     # header = ['booked_date', 'send_date', 'customer', 'num_boxes', 'service', 'cost', 'label_file']
        #     # writer.writerow(i for i in header)
        #     data = [datetime.datetime.now(), shipment_request.collection_date.date, shipment_request.client_reference,
        #             len(shipment_request.parcels), services[0].name, services[0].cost, label_string]
        #     writer.writerow(data)
