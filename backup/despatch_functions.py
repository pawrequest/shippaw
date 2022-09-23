import datetime
import inspect
import json
from pprint import pprint

from config import *


def process_manifest(manifest):  # takes list of shipments
    print("--- Processing Manifest ---")
    dates = client.get_available_collection_dates(sender, courier_id)  # get dates

    print("\n- Manifest imported", "with", len(manifest), "Shipments:\n")
    for count, (shipment) in enumerate(manifest):
        print("\t\t", count + 1, "|", shipment[hire_customer], "|", shipment[send_date])
    print("\n--- Checking Available Collection Dates...")
    print('-' * 90)  # U+2500, Box Drawings Light Horizontal

    for count, shipment in enumerate(manifest):
        if not check_send_date(shipment, dates):
            shipment[date_check] = False
            print("- Date object failure - SHIPMENT", count + 1, "CANCELLED:", shipment[hire_customer])
            print('─' * 90)  # U+2500, Box Drawings Light Horizontal
            manifest.remove(shipment)
            continue

        myprint("get address")
        if not get_address_object(shipment):
            print("ADDRESS OBJECT FAILURE - Shipment", count + 1, "Cancelled:", shipment[hire_customer])
            manifest.remove(shipment)
            continue
        print("Shipment", count + 1, "Validated:", shipment[hire_customer], "|", shipment[boxes],
              "box(es) |", shipment[address_object].street, " | ", shipment[date_object].date)

    while True:
        print("MANIFEST:\n")
        for count, shipment in enumerate(manifest):
            print(str(count + 1) + shipment[address])
        ui = input(
            '\nCONTINUE?:\nEnter a Shipment Number to change its Address, "yes" to proceed, or "exit" to exit \n')
        if ui.isnumeric() and int(ui) <= len(manifest.items()) + 1:
            shipment = manifest[int(ui)]
            shipment = adjust_address(shipment)
            manifest[int(ui)] = shipment
            if input("\nType yes to deliver manifest\n") == 'yes':
                submit_manifest(manifest)
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



def manifest_list_from_json():
    if os.path.isfile(JSONFILE):
        with open(JSONFILE) as f:
            manifest = []
            manifest_data = json.load(f)
            for count, shipment in enumerate(manifest_data['Items']):
                shipment[hire_ref] = shipment[hire_ref].replace(",", "")  # expunge commas from hire ref
                shipment = parse_shipment_address(shipment)  # gets number / deliveryFirstline
                shipment[hire_customer] = shipment[hire_customer][
                    0]  # remove deliveryCustomer field from spurious list
                manifest.append(shipment)
        return manifest
    else:
        print("NOT A FILE")


def parse_manifest_addresses(manifest):
    myprint("Parsing Manifest")
    for count, shipment in enumerate(manifest):
        print(shipment[hire_customer])
        parse_shipment_address(shipment)
        manifest[count] = shipment
    return manifest


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
            shipment[date_object] = date
            return shipment
    else:  # looped exhausted, no date match
        print("\n\t\t*** ERROR: No collections available on", shipment[send_date], "for",
              shipment[hire_customer], "***")
        if input("\nChoose new Date? (type yes, anything else will remove shipment and continue)\n") == "yes":
            for count, date in enumerate(dates):
                print("\t\t", count + 1, date.date)
            choice = ''
            while not choice.isnumeric():
                choice = input("\nEnter a number to choose a date, 0 to cancel this shipment and move on to another\n")
                if choice.isnumeric():
                    if choice == 0:
                        return None
                    else:
                        shipment[date_object] = dates[int(choice) - 1]
                        print("\t\tCollection date for", shipment[hire_customer], "is now ",
                              shipment[date_object].date,
                              "\n")
                        return shipment
                else:
                    print("\t\t Enter a number")
            else:
                return None


def get_address_object(shipment):
    myprint("shipment in get address")
    pprint(shipment)
    if building_num in shipment:
        if shipment[building_num] == 0: shipment[building_num] = False
        search_string = shipment[building_num]
    else:
        search_string = shipment[address_firstline]
    # get object
    address_object = client.find_address(shipment[postcode], search_string)
    shipment[address_object] = address_object
    return shipment


def adjust_address(shipment):  # takes
    print("ADJUST ADDRESS")  # debug
    print("Adjust Shipping Address for:", shipment[hire_customer] + "'s Shipment on",
          shipment[date_object].date,
          "\n")
    candidates = client.get_address_keys_by_postcode(shipment[postcode])
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
        shipment[address_object] = client.get_address_by_key(selected_key)
        print("New Address:", shipment[address_object].street)
        return shipment


def submit_manifest(manifest):
    for key, shipment in manifest.items():
        customer = shipment[hire_customer]
        phone = shipment[phone]
        email = shipment[email]
        address = shipment[address_object]
        boxes = int(float(shipment[boxes]))
        send_date = shipment[date_object]
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

        print("\n" + shipment[hire_customer] + "'s shipment of", shipment[boxes], "parcels to: ",
              shipment[address_object].street, "|", shipment[date_object].date, "|",
              shipment[shipping_service_name],
              "| Price =",
              shipment[shipping_cost])
        if input('Type "yes" to queue, other to skip shipment\n') == 'yes':
            print("BOOKING SHIPMENT")

            shipment_request.collection_date = shipment[date_object].date
            added_shipment = client.add_shipment(shipment_request)
            shipment[added_shipment] = added_shipment
            print("Added Shipment")

            if input('"yes" to book shipment and get labels') == str("yes"):
                client.book_shipments([added_shipment])
                shipment_return = client.get_shipment(added_shipment)
                pprint(shipment_return)

                label_pdf = client.get_labels(shipment_return.shipment_document_id)
                pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)
                label_string = 'shipment[hire_customer] + "-" + shipment[date_object].date + ".pdf"'
                label_pdf.download(LABEL_DIR / label_string)
                print()
                shipment['label_downloaded'] = True
                shipment['shipment_return'] = shipment_return
                print("Shipment for ", shipment[hire_customer], "has been booked, Label downloaded to", LABEL_DIR,
                      label_string)
            shipment[is_shipped] = "Shipped"

            # records despatch references
            # # format / print label ??



        else:
            print("Shipment", shipment[hire_customer], "Skipped by User")
            shipment[is_shipped] = "Failed"
            continue

    with open(DATA_DIR / 'AmShip.json', 'w') as f:
        print("LOGGING")
        new_out = {}
        exclude_keys = [address_object, date_object, service_object]
        for count, (key, shipment) in enumerate(manifest.items()):
            output = {k: shipment[k] for k in set(list(shipment.keys())) - set(exclude_keys)}
            date_blah = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
            new_out.update(
                {date_blah + " - " + str(shipment[is_shipped]) + " - " + shipment[hire_customer]: output})
            print("dumped")
        json.dump(new_out, f)

    print("FINISHED")
    if input("Restart?") == "yes":
        process_manifest(manifest)
    else:
        exit()


def print_manifest(manifest):
    print("\nMANIFEST:")
    for key, shipment in manifest.items():
        print(key, "|", shipment[hire_customer], "|", shipment[send_date], "|",
              shipment[address_object].street)


def print_shipment(shipment):
    pprint(shipment)
    string = " |", shipment[hire_customer], "|", shipment[send_date], "|", shipment[
        address_object].street
    return string


def myprint(*args):
    print(inspect.currentframe().f_code.co_name.upper(), "Called by",
          inspect.currentframe().f_back.f_code.co_name.upper(), "at line", inspect.currentframe().f_lineno)
    for arg in args:
        print(arg)
