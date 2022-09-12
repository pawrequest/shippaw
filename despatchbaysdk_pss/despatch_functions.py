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
# jsonfile = "files/Amship.json" # from args
courier_id = 8

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
delivery_name_field = "Delivery Name"
delivery_contact_field = "Delivery Contact"
desp_shipment_id_field = "Despatch ID"
date_object_field = "Date Object"


## receives and parses jsonfile, adds Shipment_id of incremenetal 01+ and hire reference ##

def book_shipments(jsonfile):  # takes dict_list of shipments
    manifest = manifest_from_json(jsonfile)
    for count, shipment in enumerate(manifest):
        if get_shipment_date_object(shipment) == "NO":
            manifest.remove(shipment)
            continue
        shipment = get_shipment_date_object(shipment)
        shipment = get_shipment_address_object(shipment)
        manifest[count]=shipment
        pprint (shipment)
    # manifest = get_date_objects(manifest)
    #manifest = get_shipment_address_object(manifest)
    # print("MANIFEST:")
    # for shipment in manifest:
    #     print(shipment[customer_field],"|",shipment[boxes_field],"boxes to",shipment[address_object_field].street)
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


def manifest_from_json(jsonfile):  # calls parse-shipment
    with open(jsonfile) as f:
        data = json.load(f)
        # Assign Shipment IDs from count and hire ref and parse address into num or firstline, populate manifest
        manifest = []

        for count, shipment in enumerate(data['Items'], start=1):
            shipment[hire_ref_field] = shipment[hire_ref_field].replace(",", "")  # expunge commas from hire ref
            shipment[shipment_id_field] = str(count).zfill(2) + shipment[
                hire_ref_field]  # make an id from count and hire-ref
            shipment = parse_address(shipment[address_field], shipment)  # gets number / firstline
            shipment[customer_field] = shipment[customer_field][0]  # remove customer field from spurious list

            manifest.append(shipment)
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

def get_shipment_date_object(shipment):
    dates = client.get_available_collection_dates(sender, courier_id)
    print(shipment[customer_field])
    send_date_reversed = shipment[send_date_field].split("/")
    send_date_reversed.reverse()
    shipment[send_date_field] = '-'.join(send_date_reversed)
    for count, date in enumerate(dates):
        if date.date == send_date_reversed:  # if date object matches reversed string
            shipment[date_object_field] = date
            print("DATE MATCH - Shipment for", shipment[customer_field], "can be collected on",
                  shipment[date_object_field].date, "\n")
            continue
        else:  # no date match
            print("\nNO COLLECTION ON SEND OUT DATE FOR", shipment[customer_field], "\n")
            if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
                for count, date in enumerate(dates):
                    print(count + 1, date.date)
                choice = int(input("\nChoose a Date\n")) - 1
                shipment[date_object_field] = dates[choice]
                print("Collection Date Is Now ", shipment[date_object_field].date, "\n")
            print('Shipment Removed "' + shipment[customer_field] + '" .... Moving On\n')
            return "NO"
    return(shipment)



def get_manifest_date_objects(manifest):
    dates = client.get_available_collection_dates(sender, courier_id)
    for count, shipment in enumerate(manifest):
        ship_count=count
        print(len(manifest))
        print ("Shipment",count+1, "-", shipment[customer_field])
        # # reverse send date and get matching collection dates
        send_date_reversed = shipment[send_date_field].split("/")
        send_date_reversed.reverse()
        shipment[send_date_field] = '-'.join(send_date_reversed)
        for count, date in enumerate(dates):
            if date.date == shipment[send_date_field]:  # if date object matches reversed string
                shipment[date_object_field] = date
                print("DATE MATCH - Shipment for", shipment[customer_field], "can be collected on",
                      shipment[date_object_field].date,"\n")
                manifest[ship_count] = shipment
                pprint(manifest[ship_count])
                break # out of the date loop, back to shipment loop

        else: # no date match
            print("\nNO COLLECTION ON SEND OUT DATE FOR", shipment[customer_field],"\n")
            if input("\nChoose New Date? (type yes, other to remove shipment and continue)\n") == "yes":
                for count, date in enumerate(dates):
                        print(count+1, date.date)
                choice = int(input("\nChoose a Date\n"))-1
                shipment[date_object_field] = dates[choice]
                manifest[ship_count]=shipment
                print("shipcouint",ship_count+1)

                print("Collection Date Is Now ", shipment[date_object_field].date,"\n")
                #continue
            manifest.remove(shipment)
            print('Shipment Removed "'+shipment[customer_field]+'" .... Moving On\n')
        print(shipment[customer_field])
            #get_date_objects(manifest)
    return (manifest)


def adjust_address(manifest):
    # list shipments, prompt and confirm selection
    for count, shipment in enumerate(manifest, start=1):
        print(count, "|", shipment[customer_field], "|", shipment[address_firstline_field])
    adjust = int(input('Which Shipment to Adjust? \n'))
    print("Adjusting Shipment", adjust, "|", manifest[adjust - 1][customer_field], "|",
          manifest[adjust - 1][address_object_field].street, "\n")

    # get shipment and candidates for address replacement
    shipment = manifest[adjust - 1]
    candidates = client.get_address_keys_by_postcode(shipment[postcode_field])
    shipment[candidates_field] = candidates

    # display candidates and prompt selection
    for count, candidate in enumerate(candidates, start=1):
        print("Candidate ", count, "|", candidate.address)
    selection = int(input('Which candidate? ("0" to remove shipment from manifest, "exit" to exit) \n'))
    selected_key = candidates[selection - 1].key
    if selection == 0:
        if input('Remove Shipment From manifest? "yes" to continue\n') == "yes":
            manifest.remove(shipment)
    elif selection == "exit":
        exit()
    # apply cahnges
    else:
        shipment[address_field] = client.get_address_by_key(selected_key)
        manifest[adjust - 1] = shipment
    print("MANIFEST ADJUSTED:\n")
    for count, shipment in enumerate(manifest, start=1):
        print(count, "|", shipment[customer_field], "|", shipment[address_firstline_field])
    if input('Type "yes" to Adjust Another') == 'yes':
        adjust_address(manifest)


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

def get_shipment_address_object(shipment):
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

def deliver_manifest(manifest):
    for shipment in manifest:
        customer = shipment[customer_field]
        phone = shipment[phone_field]
        email = shipment[email_field]
        address = shipment[address_object_field]
        boxes = int(float(shipment[boxes_field]))
        send_date = shipment[send_date_field]
        recipient_name = shipment[delivery_contact_field]
        ###
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
        for service in services:
            print(service.name, service.service_id, service.courier)
        dates = client.get_available_collection_dates(sender, services[0].courier.courier_id)
        print("\n" + customer + "'s shipment of", boxes, "parcels to: ",
              recipient.recipient_address.street, "on", shipment[date_object_field].date, "BY", services[0].name, "COSTING:",
              services[0].cost)
        if input('Type "yes" to book and download pdf \n') != 'yes':
            print("exiting")
            pass
        print("Checking Available Dates")
        shipment_request.service_id = services[0].service_id
        for count, date in enumerate(dates):
            print(date.date)
            if date.date == shipment[send_date_field]:
                print("DATE MATCH, Booking service")
                # shipment_request.collection_date = dates[count]
                # added_shipment = client.add_shipment(shipment_request)
                # pprint(added_shipment)
                # shipment_return = client.get_shipment(added_shipment)

                # uncomment to book and get labels / tracking
                # client.book_shipments([added_shipment])
                # label_pdf = client.get_labels(shipment_return.shipment_document_id)
                # label_string = 'files/parcelforce_labels/' + shipment['customer'] + "-" + shipment['collection_date'] + '.pdf'
                # label_pdf.download(label_string)

                shipment['shipped'] = True
                # records despatch references
                # # format / print label ??
                pprint(shipment)
                shipment
                continue

        else:
            print("NO DATES MATCH, passing to next shipment")
            pprint(shipment)
            manifest[shipment] = shipment
            continue

    with open(logfile, 'w') as f:
        json.dump(manifest, f)
