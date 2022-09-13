# provide manifest json file at runtime
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
sender = client.sender(address_id=sender_id)

logfile = 'AmLog.json'
# jsonfile = 'data/AmShip.json'
courier_id = 8

# DB Column Names
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
delivery_name_field = "Delivery Name"
delivery_contact_field = "Delivery Contact"
desp_shipment_id_field = "Despatch ID"
date_object_field = "Date Object"
shipnum_field = 'Shipment Number'
shipping_service_id = "Shipment Service ID"
service_object_field = 'Shipping Service Object'


def print_manifest(manifest):
    print("\nMANIFEST:")
    for key, shipment in manifest.items():
        print(key, "|", shipment[customer_field], "|", shipment[send_date_field], "|",
              shipment[address_object_field].street)


def book_shipments(manifest):  # takes dict_list of shipments
    dates = client.get_available_collection_dates(sender, courier_id)

    print("\nJSON imported", "with", len(manifest.keys()), "Shipments:\n")
    for count, (key, shipment) in enumerate(manifest.items()):
        print(count + 1, "|", shipment[customer_field], "|", shipment[send_date_field])
    print("\nChecking Available Collection Dates\n")

    for key, shipment in list(manifest.items()):
        if not get_dates(shipment, dates):
            print("SHIPMENT Cancelled", key, "DATE OBJECT FAILURE\n")
            manifest.pop(key)
            continue
        if not get_address_object(shipment):
            print("SHIPMENT Cancelled", key, "ADDRESS OBJECT FAILURE\n")
            manifest.pop(key)
            continue
        print("Shipment", key, "Validated:", shipment[customer_field], "-", shipment[boxes_field],
              "box(es) to -", shipment[address_object_field].street, " - On -", shipment[date_object_field].date)

    while True:
        ui = input('\nEnter a Shipment Number to change its Address, "yes" to proceed, or "exit" to exit \n')
        if ui.isnumeric() == True and int(ui) <= len(manifest.items())+1:
            shipment = manifest[int(ui)]
            shipment = adjust_address(shipment)
            manifest[int(ui)] = shipment
            print_manifest(manifest)
            if input("\nType yes to deliver manifest\n") == 'yes':
                submit_manifest(manifest)
                # deliver_manifest(manifest)
            else:
                print("USER SAYS NO, RESTARTING")
                continue
        if str(ui) == "yes":
            submit_manifest(manifest)
        if str(ui) == "exit":
            exit()
        else:
            print("BAD INPUT?")
            continue


def manifest_from_json(jsonfile):
    with open(sys.argv[1]) as f:
        manifest = {}
        manifest_data = json.load(f)
        for count, shipment in enumerate(manifest_data['Items'], start=1):
            shipment[hire_ref_field] = shipment[hire_ref_field].replace(",", "")  # expunge commas from hire ref
            shipment[shipment_id_field] = str(count).zfill(2) + shipment[
                hire_ref_field]  # make an id from count and hire-ref
            shipment = parse_address(shipment[address_field], shipment)  # gets number / firstline
            shipment[customer_field] = shipment[customer_field][0]  # remove customer field from spurious list
            manifest[count] = shipment
        return manifest


def parse_address(crapstring, shipment):
    # get num / firstline
    first_line = crapstring.split("\r")[0]
    first_block = (crapstring.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    for char in first_line:
        if not char.isalpha():
            if not char.isnumeric():
                if not char == " ":
                    first_line = first_line.replace(char, "")
    if first_char.isnumeric():
        shipment[building_num_field] = first_block
    shipment[address_firstline_field] = first_line
    return shipment


def get_dates(shipment, dates):
    send_date_reversed = shipment[send_date_field].split("/")
    send_date_reversed.reverse()
    shipment[send_date_field] = '-'.join(send_date_reversed)

    for count, date in enumerate(dates):
        if date.date == shipment[send_date_field]:  # if date object matches reversed string
            shipment[date_object_field] = date
            return shipment
    else:  # looped exhausted, no date match
        print("\nNO COLLECTION AVAILABLE FOR", shipment[customer_field])
        if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
            for count, date in enumerate(dates):
                print(count + 1, date.date)
            choice = int(input("\nChoose a Date, 0 to cancel this shipment and move on to another\n"))
            if choice == 0:
                return None
            else:
                shipment[date_object_field] = dates[choice - 1]
                print("Collection Date Is Now ", shipment[date_object_field].date, "\n")
                return shipment
        else:
            return None


def get_address_object(shipment):
    # set search string - number or firstline
    if shipment[building_num_field] == 0: shipment[building_num_field] = False
    if not shipment[building_num_field]:
        search_string = shipment[address_firstline_field]
    else:
        search_string = shipment[building_num_field]
    # get object
    address_object = client.find_address(shipment[postcode_field], search_string)
    shipment[address_object_field] = address_object
    return shipment


def adjust_address(shipment):  # takes
    print("Adjust Shipping Address for:", shipment[customer_field] + "'s Shipment on", shipment[date_object_field].date,
          "\n")
    candidates = client.get_address_keys_by_postcode(shipment[postcode_field])
    for count, candidate in enumerate(candidates, start=1):
        print("Candidate", count, "|", candidate.address)

    selection = int(input('\nWhich candidate? ("0" to remove shipment from manifest, "exit" to exit) \n'))
    selected_key = candidates[selection - 1].key
    if selection == 0:
        if input('Remove Shipment From manifest? "yes" to continue\n') == "yes":
            return None
    elif selection == "exit":
        exit()
    else:
        shipment[address_object_field] = client.get_address_by_key(selected_key)
        print("New Address:", shipment[address_object_field].street)
        return shipment



def submit_manifest(manifest):
    for key, shipment in manifest.items():
        create_shipment(shipment)
        print("\n" + shipment[customer_field] + "'s shipment of", shipment[boxes_field], "parcels to: ",
              shipment[address_object_field].street, "on", shipment[date_object_field].date, "BY",
              shipment[service_object_field].name,
              "COSTING:",
              shipment[service_object_field].cost)
        if input('Type "yes" to book, other to skip shipment\n') == 'yes':
            print("BOOKING SHIPMENT")

            # shipment_request.collection_date = shipment[date_object_field].date
            # added_shipment = client.add_shipment(shipment_request)
            # pprint(added_shipment)
            # shipment_return = client.get_shipment(added_shipment)

            # uncomment to book and get labels / tracking
            # client.book_shipments([added_shipment])
            # label_pdf = client.get_labels(shipment_return.shipment_document_id)
            # label_string = 'data/parcelforce_labels/' + shipment['customer'] + "-" + shipment['collection_date'] + '.pdf'
            # label_pdf.download(label_string)

            shipment['shipped'] = True
            # records despatch references
            # # format / print label ??
            continue
        else:
            print("Shipment",shipment[customer_field],"Skipped by User")
            continue
    else:
        print("no shipments confirmed, restarting")
        book_shipments(manifest)
    with open(logfile, 'w') as f:
        # json.dump(manifest, f)
        json.dumps(manifest, indent=4, sort_keys=True, default=str)


def create_shipment(shipment):
    customer = shipment[customer_field]
    phone = shipment[phone_field]
    email = shipment[email_field]
    address = shipment[address_object_field]
    boxes = int(float(shipment[boxes_field]))
    send_date = shipment[date_object_field]
    recipient_name = shipment[delivery_contact_field]
    recipient_address = client.address(
        company_name=customer,
        country_code="GB",
        county=address.county,
        locality=address.locality,
        postal_code=address.postal_code,
        town_city=address.town_city,
        street=address.street
    )

    recipient = client.recipient(
        name=recipient_name,
        telephone=phone,
        email=email,
        recipient_address=recipient_address

    )
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

    shipment_request = client.shipment_request(
        parcels=parcels,
        client_reference=customer,
        collection_date=send_date,
        sender_address=sender,
        recipient_address=recipient,
        follow_shipment='true'
    )
    services = client.get_available_services(shipment_request)
    shipment_request.service_id = services[0].service_id
    shipment[shipping_service_id] = shipment_request.service_id
    shipment[service_object_field] = services[0]

