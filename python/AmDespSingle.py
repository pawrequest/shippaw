import datetime
import inspect
import json
import xml.etree.ElementTree as ET
from pprint import pprint

from config import *


def shipment_from_xml(xml):
    shipment = {}
    tree = ET.parse(xml)
    root = tree.getroot()
    fields = root[0][2]
    customer = root[0][3][1][0][0].text
    cat = root[0][0].text

    for field in fields:
        fieldname = field[0].text
        if fieldname:
            fieldname = unsanitise(fieldname)
        fieldvalue = field[1].text
        if fieldvalue:
            fieldvalue = unsanitise(fieldvalue)
        if fieldvalue == "0":
            fieldvalue = False
        shipment[fieldname] = fieldvalue
        shipment[category] = cat
        shipment['customer'] = customer
    return shipment


def unsanitise(string):
    string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;", chr(60)).replace("&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    return string

# def unsanitise(string):
#     string = string.replace("&amp;", chr(38))
#     string = string.replace("&quot;", chr(34))
#     string = string.replace("&apos;", chr(39))
#     string = string.replace("&lt;", chr(60))
#     string = string.replace("&gt;", chr(62))
#     string = string.replace("&gt;", chr(32))
#     string = string.replace("&#", "")
#     string = string.replace(";", "")
#     return string

def process_shipment(shipment):  # master function, takes list of shipments
    dates = client.get_available_collection_dates(sender, courier_id)  # get dates
    print("\t\t", shipment['customer'], "|", shipment['send_date'])
    print("\n--- Checking Available Collection Dates...")
    print('-' * 90)  # U+2500, Box Drawings Light Horizontal # debug

    if check_send_date(shipment, dates):
        if get_address_object(shipment):
            print("YES FUCKING OBJECT",shipment["address_object"])
            print("Shipment Validated:", shipment['customer'], "|", shipment[boxes],
              "box(es) |", shipment["address_object"].street, " | ", shipment["date_object"].date)

    userinput="m"
    while (userinput not in ["yes","edit","exit"]):
        userinput = str(input('\nCONTINUE?:\nEnter "yes" to proceed, "edit" to change address, or "exit" to exit \n')).lower()
        if input("\nType yes to submit shipment\n")[0].lower() == 'y':
            submit_shipment(shipment)
        elif userinput == "edit":
            shipment = adjust_address(shipment)
            submit_shipment(shipment)
        elif userinput == "exit":
            exit()

def parse_shipment_address(shipment):
    crapstring = shipment[address]
    first_line = crapstring.split("\r")[0]
    second_line = crapstring.split("\r")[1]
    # rsecond_line = crapstring.split("\r")[2]
    myprint("FIRSTLINE", first_line, "\n", "SECOND", second_line)  # debug
    first_block = (crapstring.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    for char in first_line:
        if not char.isalpha():
            if not char.isnumeric():
                if not char == " ":
                    first_line = first_line.replace(char, "")
    if first_char.isnumeric():
        shipment[building_num] = first_block
    shipment[address_firstline] = first_line
    return shipment


def check_send_date(shipment, dates):
    send_date_reversed = shipment[send_date].split("/")
    send_date_reversed.reverse()
    shipment[send_date] = '-'.join(send_date_reversed)

    for count, date in enumerate(dates):
        if date.date == shipment[send_date]:  # if date object matches reversed string
            shipment["date_object"] = date
            return shipment
    else:  # looped exhausted, no date match
        print("\n\t\t*** ERROR: No collections available on", shipment[send_date], "for",
              shipment['customer'], "***")

        if input("\nChoose new Date? (type yes, anything else will exit)\n")[0].lower() == "y":
            for count, date in enumerate(dates):
                print("\t\t", count + 1, date.date)
            choice = input('\nEnter a number to choose a date, "exit" to exit\n')
            if choice[0].lower() == "e":
                if input('Type "yes" to confirm exit: ')[0].lower() == "y":
                    return None
            else:
                shipment["date_object"] = dates[int(choice) - 1]
                print("\t\tCollection date for", shipment['customer'], "is now ",shipment["date_object"].date, "\n")
                return shipment


def get_address_object(shipment):
    if building_num in shipment:
        if shipment[building_num] != 0:
            print("Got building number to search by")
            search_string = shipment[building_num]
        else:
            print("No building number, searching firstline")
            shipment[building_num] = False
            search_string = shipment[address_firstline]
    else:
        print("No building number, searching firstline")
        search_string = shipment[address_firstline]
    # get object
    address_object = client.find_address(shipment[postcode], search_string)
    shipment["address_object"] = address_object
    return shipment


def adjust_address(shipment):  # takes
    print("Adjust Shipping Address for:", shipment['customer'] + "'s Shipment on",
          shipment["date_object"].date,
          "\n")
    candidates = client.get_address_keys_by_postcode(shipment[postcode])
    for count, candidate in enumerate(candidates, start=1):
        print("Candidate", count, "|", candidate.address)

    selection = input('\nEnter a candidate number "exit" to exit) \n')
    selected_key = candidates[int(selection) - 1].key
    if selection[0].lower() == "e":
        if input("Type yes to confirm exit")[0].lower() == "y":
            exit()
    else:
        shipment["address_object"] = client.get_address_by_key(selected_key)
        print("New Address:", shipment["address_object"].street)
        return shipment


def submit_shipment(shipment):
    customer = shipment['customer']
    phone = shipment['phone']
    email = shipment['email']
    address = shipment["address_object"]
    boxes = int(float(shipment['boxes']))
    send_date = shipment["date_object"]
    recipient_name = shipment[delivery_contact]
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
    shipment[shipping_service_name] = services[0].name
    shipment[shipping_service_id] = shipment_request.service_id
    shipment[shipping_cost] = services[0].cost

    print("\n" + shipment['customer'] + "'s shipment of", shipment[boxes], "parcels to: ",
          shipment["address_object"].street, "|", shipment["date_object"].date, "|",
          shipment[shipping_service_name],
          "| Price =",
          shipment[shipping_cost])
    if input('Type "yes" to queue, other to skip shipment\n') == 'yes':
        print("BOOKING SHIPMENT")

        shipment_request.collection_date = shipment["date_object"].date
        added_shipment = client.add_shipment(shipment_request)
        shipment[added_shipment] = added_shipment
        print("Added Shipment")

        if input('"yes" to book shipment and get labels') == str("yes"):
            client.book_shipments([added_shipment])
            shipment_return = client.get_shipment(added_shipment)
            pprint(shipment_return)

            label_pdf = client.get_labels(shipment_return.shipment_document_id)
            pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)
            label_string = shipment['customer'], "-", shipment["date_object"].date+".pdf"
            # label_string = 'shipment['customer'] + "-" + shipment["date_object"].date + ".pdf"'
            label_pdf.download(LABEL_DIR / label_string)
            print()
            shipment['label_downloaded'] = True
            shipment['shipment_return'] = shipment_return
            print("Shipment for ", shipment['customer'], "has been booked, Label downloaded to", LABEL_DIR,
                  label_string)
            shipment[is_shipped] = "Shipped"

        # records despatch references
        # # format / print label ??

        else:
            print("Shipment", shipment['customer'], "Skipped by User")
            shipment[is_shipped] = "Failed"

    with open(DATA_DIR / 'AmShip.json', 'w') as f:
        print("LOGGING")
        output = {}
        exclude_keys = ["address_object", "date_object", 'service_object', 'despatch_shipped_object']
        for key, value in shipment:
            if "object" not in key:
                output[key] = output[value]
                date_blah = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
                output.update({date_blah + " - " + str(shipment[is_shipped]) + " - " + shipment['customer']: output})
            print("dumped")
        json.dump(output, f)

    print("FINISHED")
    exit()


def print_shipment(shipment):
    pprint(shipment)
    string = " |", shipment['customer'], "|", shipment[send_date], "|", shipment[
        "address_object"].street
    return string


def myprint(*args):
    print(inspect.currentframe().f_code.co_name.upper(), "Called by",
          inspect.currentframe().f_back.f_code.co_name.upper(), "at line", inspect.currentframe().f_back.f_lineno, inspect.currentframe().f_back.f_back.f_code.co_names)
    for arg in args:
        print(arg)
