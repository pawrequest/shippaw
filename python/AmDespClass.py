import inspect
import json
import xml.etree.ElementTree as ET

from config import *
from .class_play import *


def shipment_from_xml(xml):
    shipment = Shipment()
    tree = ET.parse(xml)
    root = tree.getroot()
    fields = root[0][2]
    custom = root[0][3][1][0][0].text
    cat = root[0][0].text.lower()
    for field in fields:
        if field[0].text:
            fieldname = field[0].text.lower()
            fieldname = unsanitise(fieldname)
            if "delivery" in fieldname:
                fieldname = fieldname.replace("delivery ", "")
            if " " in fieldname:
                fieldname = fieldname.replace(" ", "_")
            if fieldname in commence_columns.keys():  # debug
                print("KEY IN COM", fieldname)
                fieldname = commence_columns[fieldname]
                print(fieldname)
            if field[1].text:
                fieldvalue = field[1].text
                fieldvalue = unsanitise(fieldvalue)
                if fieldvalue.isnumeric():
                    fieldvalue = int(fieldvalue)
                    if fieldvalue == 0:
                        fieldvalue = None
                setattr(shipment, fieldname, fieldvalue)
    setattr(shipment, category, cat)
    setattr(shipment, customer, custom)
    return shipment


def unsanitise(string):
    string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
                                                                                                            chr(60)).replace(
        "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    return string


def process_shipment(shipment):  # master function takes shipment dict
    # parse address
    shipment = parse_shipment_address(shipment)
    print("\t\t", shipment.boxes, "box/es |", shipment.customer, "|", shipment.firstline, "|",
          shipment.send_date)
    print("\n--- Checking Available Collection Dates...")
    print('-' * 90)  # U+2500, Box Drawings Light Horizontal # debug
    # validate date and address
    dates = client.get_available_collection_dates(sender, courier_id)  # get dates
    if check_send_date(shipment, dates):
        if get_address_object(shipment):
            print("Shipment Validated:", shipment.customer, "|", shipment.boxes,
                  "box(es) |", shipment.address_object.street, " | ", shipment.date_object.date)
    # shall we continue?
    userinput = "1"
    while (userinput not in ["p", "c", "e"]):
        userinput = str(
            input(
                '\nQueue Shipment?:\nEnter "[p]roceed, [c]hange address, or [e]xit\n'))[0].lower()
        if len(userinput) < 1:
            continue
        if userinput[0] == 'p':
            queue_shipment(shipment)
            break
        elif userinput == "c":
            shipment = change_address(shipment)
            queue_shipment(shipment)
            break
        elif userinput == "e":
            userinput = ""
            while len(userinput) < 1:
                userinput = input("Enter [e]xit, or [c]ontinue booking\n")[0].lower()
                if userinput == "e":
                    log_to_json(shipment)
                    exit()
                elif userinput == "c":
                    continue
    userinput = ""
    while True:
        userinput = str(input('\nBook Shipment?:\nEnter "yes" to proceed anything else to exit \n')).lower()
        if userinput[0].lower() == 'y':
            book_shipment(shipment)
        else:
            if input("type [y]es to confirm exit")[0].lower() == "y":
                log_to_json(shipment)
                exit()
            continue


def parse_shipment_address(shipment):
    print("\n--- Parsing Address...\n")
    crapstring = shipment.address
    first_line = crapstring.split("\n")[0]
    first_block = (crapstring.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    for char in first_line:
        if not char.isalpha():
            if not char.isnumeric():
                if not char == " ":
                    first_line = first_line.replace(char, "")
    if first_char.isnumeric():
        shipment.building_num = first_block
    else:
        print("No building number, using firstline:", shipment.address_firstline)
    shipment.address_firstline = first_line

    return shipment


def check_send_date(shipment, dates):
    # validate_collection_date_object function from sdk
    '''
        Converts a string timestamp to a CollectionDate object.
        if isinstance(collection_date, str):
            return CollectionDate(self.despatchbay_client, date=collection_date)
        return collection_date
    :param shipment:
    :param dates:
    :return:
    '''

    send_date_reversed = shipment.send_date.split("/")
    send_date_reversed.reverse()
    shipment.send_date = '-'.join(send_date_reversed)

    for count, date in enumerate(dates):
        if date.date == shipment.send_date:  # if date object matches reversed string
            shipment.date_object = date
            return shipment
    else:  # looped exhausted, no date match
        print("\n\t\t*** ERROR: No collections available on", shipment.send_date, "for",
              shipment.customer, "***\n\n Collections are available on:\n")
        for count, date in enumerate(dates):
            print("\t\t", count + 1, date.date)

        choice = ""
        while True:
            choice = input('\nEnter a number to choose a date, 0 to exit\n')
            if choice == "":
                continue
            if not choice.isnumeric():
                print("Enter a number")
                continue
            if not -1 <= int(choice) <= len(dates) + 1:
                print('\nWrong Number!\n')
                continue
            if int(choice) == 0:
                if input('Type "[y]es" to confirm exit: ')[0].lower() == "y":
                    log_to_json(shipment)
                    exit()
                continue
            else:
                shipment.date_object = dates[int(choice) - 1]
                print("\t\tCollection date for", shipment.customer, "is now ", shipment.date_object.date, "\n")
                return shipment


def get_address_object(shipment):
    if shipment.building_num:
        if shipment.building_num != 0:
            search_string = shipment.building_num
        else:
            print("No building number, searching firstline")
            shipment.building_num = False
            search_string = shipment.address_firstline
    else:
        print("No building number, searching firstline")
        search_string = shipment.address_firstline
    # get object
    address_object = client.find_address(shipment.postcode, search_string)
    shipment.address_object = address_object
    return shipment


def change_address(shipment):  # takes
    print("Changing shipping address  | ", shipment.customer, " | ",
          str(shipment.date_object.date),
          "\n")
    candidates = client.get_address_keys_by_postcode(shipment.postcode)
    for count, candidate in enumerate(candidates, start=1):
        print("Candidate", count, "|", candidate.address)
    selection = ""
    while True:
        selection = input('\nEnter a candidate number, 0 to exit \n')
        if selection.isnumeric():
            selection=int(selection)
        else:
            continue
        if selection == 0:
            if str(input("[e]xit?"))[0].lower() == "e":
                log_to_json(shipment)
                exit()
            continue
        if not -1 <= selection <= len(candidates) + 1:
            print("Wrong Number")
            continue
        break
    selected_key = candidates[int(selection) - 1].key
    shipment.address_object = client.get_address_by_key(selected_key)
    print("New Address:", shipment.address_object.street)
    return shipment


def make_request(shipment):
    recipient_address = client.address(
        company_name=shipment.customer,
        country_code="GB",
        county=shipment.address_object.county,
        locality=shipment.address_object.locality,
        postal_code=shipment.address_object.postal_code,
        town_city=shipment.address_object.town_city,
        street=shipment.address_object.street
    )

    recipient = client.recipient(
        name=shipment.delivery_contact,
        telephone=shipment.phone,
        email=shipment.email,
        recipient_address=recipient_address

    )
    parcels = []
    for x in range(shipment.boxes):
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
        client_reference=shipment.customer,
        collection_date=shipment.date_object.date,
        sender_address=sender,
        recipient_address=recipient,
        follow_shipment='true'
    )
    shipment_request.collection_date = shipment.date_object.date
    services = client.get_available_services(shipment_request)
    shipment_request.service_id = 101
    shipment.shipping_service_name = services[0].name
    shipment.shipping_cost = services[0].cost
    shipment.services = services
    atest = [a for a in dir(shipment_request) if not a.startswith('__')]
    return shipment_request


def queue_shipment(shipment):
    shipment_request = make_request(shipment)
    added_shipment = client.add_shipment(shipment_request)
    shipment.added_shipment = added_shipment

    print("\n" + shipment.customer + "'s shipment of", shipment.boxes, "parcels to: ",
          shipment.address_object.street, "|", shipment.date_object.date, "|",
          shipment.shipping_service_name,
          "| Price =",
          shipment.shipping_cost)

    choice = ""
    while str(choice) not in ["y", "r"]:
        choice = input('Type "[y]es" to queue, "r" to restart, anything else will cancel\n')
        if len(choice) < 1:
            continue
        if str(choice)[0].lower() != "y":
            if str(choice)[0].lower() == "r":
                print("Restarting")
                process_shipment(shipment)
            if input("Type [y]es to exit")[0].lower() == "y":
                log_to_json(shipment)
                exit()
    print("Adding Shipment to Despatchbay Queue")
    return shipment


# [a for a in dir(obj) if not a.startswith('__')]
# ['bar', 'foo', 'func']

def book_shipment(shipment):
    client.book_shipments(shipment.added_shipment)
    shipment_return = client.get_shipment(shipment.added_shipment)

    label_pdf = client.get_labels(shipment_return.shipment_document_id)
    pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)
    label_string = ""
    label_string = label_string + shipment.customer + "-" + str(shipment.date_object.date) + ".pdf"
    print(label_string)
    print(type(label_string))
    label_pdf.download(LABEL_DIR / label_string)
    tracking_numbers = []
    for parcel in shipment_return.parcels:
        tracking_numbers.append(parcel.tracking_number)

    shipment.shipment_return = shipment_return
    shipment.shipment_doc_id = shipment_return.shipment_document_id
    shipment.label_url = shipment_return.labels_url
    shipment.parcels = shipment_return.parcels
    shipment.tracking = tracking_numbers
    shipment.label_location = str(LABEL_DIR) + label_string

    shipment.collection_booked = True
    shipment.label_downloaded = True
    print("Shipment for ", shipment.customer, "has been booked, Label downloaded to", shipment.label_location)
    log_to_json(shipment)
    exit()


def log_to_json(shipment):
    export_dict = {}
    export_keys = [k for k in dir(shipment) if
                   not k.startswith('__') and k not in export_exclude_keys and getattr(shipment, k)]

    for key in export_keys:
        export_dict.update({key: getattr(shipment, key)})
    with open(DATA_DIR / 'AmShip.json', 'w') as f:
        json.dump(export_dict, f, sort_keys=True)
        print("Data dumped to json:",export_keys)
    return shipment


def myprint(*args):
    print(inspect.currentframe().f_code.co_name.upper(), "Called by",
          inspect.currentframe().f_back.f_code.co_name.upper(), "at line", inspect.currentframe().f_back.f_lineno,
          inspect.currentframe().f_back.f_back.f_code.co_names)
    for arg in args:
        print(arg)
