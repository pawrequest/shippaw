from config import *
import json
import pathlib
from pprint import pprint
import datetime

# from main import user_location
RYZEN = False




def print_manifest(manifest):
    print("\nMANIFEST:")
    for key, shipment in manifest.items():
        print(key, "|", shipment[customer_field], "|", shipment[send_date_field], "|",
              shipment[address_object_field].street)


def process_manifest(manifest):  # takes dict_list of shipments
    dates = client.get_available_collection_dates(sender, courier_id) # get dates

    print("\nJSON imported", "with", len(manifest.keys()), "Shipments:\n")
    for count, (key, shipment) in enumerate(manifest.items()):
        print(key, "|", shipment[customer_field], "|", shipment[send_date_field])
    print("\nChecking Available Collection Dates...")

    for key, shipment in list(manifest.items()):
        if not get_dates(shipment, dates):
            print("DATE OBJECT FAILURE - Shipment", key, "Cancelled:", shipment[customer_field])
            manifest.pop(key)
            continue
        if not get_address_object(shipment):
            print("ADDRESS OBJECT FAILURE - Shipment", key, "Cancelled:", shipment[customer_field])
            manifest.pop(key)
            continue
        print("Shipment", key, "Validated:", shipment[customer_field], "|", shipment[boxes_field],
              "box(es) |", shipment[address_object_field].street, " | ", shipment[date_object_field].date)

    while True:
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


def manifest_from_json():
    with open(JSONFILE) as f:
        manifest = {}
        manifest_data = json.load(f)
        print("MANDATA",manifest_data)
        for count, shipment in enumerate(manifest_data['Items'], start=1):
            shipment[hire_ref_field] = shipment[hire_ref_field].replace(",", "")  # expunge commas from hire ref
            shipment[shipment_id_field] = str(count).zfill(2) + shipment[
                hire_ref_field]  # make an id from count and hire-ref
            shipment = parse_address(shipment[address_field], shipment)  # gets number / firstline
            shipment[customer_field] = shipment[customer_field][0]  # remove customer field from spurious list
            manifest[count] = shipment
    print("MANI",manifest)
    return manifest_data



def get_commence(type="Hire"):
    if type == "Hire":
        # params =
        pass
    elif type =="Sale":
        pass




def parse_address(crapstring, shipment):
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
        print("\n*** ERROR ***\n\t\t--- No Collections Available on", shipment[send_date_field], "for",
              shipment[customer_field], "---")
        if input("\nChoose New Date? (type yes, anything else will remove shipment and continue)\n") == "yes":
            for count, date in enumerate(dates):
                print(count + 1, date.date)
            choice = int(input("\nChoose a Date, 0 to cancel this shipment and move on to another\n"))
            if choice == 0:
                return None
            else:
                shipment[date_object_field] = dates[choice - 1]
                print("Collection Date For", shipment[customer_field], "Is Now ", shipment[date_object_field].date,
                      "\n")
                return shipment
        else:
            return None


def get_address_object(shipment):
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
        shipment[shipping_service_name_field] = services[0].name
        shipment[shipping_service_id_field] = shipment_request.service_id
        shipment[shipping_cost_field] = services[0].cost

        print("\n" + shipment[customer_field] + "'s shipment of", shipment[boxes_field], "parcels to: ",
              shipment[address_object_field].street, "|", shipment[date_object_field].date, "|",
              shipment[shipping_service_name_field],
              "| Price =",
              shipment[shipping_cost_field])
        if input('Type "yes" to queue, other to skip shipment\n') == 'yes':
            print("BOOKING SHIPMENT")

            shipment_request.collection_date = shipment[date_object_field].date
            added_shipment = client.add_shipment(shipment_request)
            shipment[added_shipment_field] = added_shipment
            print("Added Shipment")


            if input('"yes" to book shipment and get labels')==str("yes"):
                client.book_shipments([added_shipment])
                shipment_return = client.get_shipment(added_shipment)
                pprint (shipment_return)

                label_pdf = client.get_labels(shipment_return.shipment_document_id)
                pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)
                label_string = 'shipment[customer_field] + "-" + shipment[date_object_field].date + ".pdf"'
                label_pdf.download(LABEL_DIR + label_string)
                print("Lablel downloaded to",LABEL_DIR, label_string)
                shipment['label_downloaded'] = True
                shipment['shipment_return'] = shipment_return
            shipment[is_shipped_field] = "Shipped"


            # records despatch references
            # # format / print label ??



        else:
            print("Shipment", shipment[customer_field], "Skipped by User")
            shipment[is_shipped_field] = "Failed"
            continue

    with open(DATA_DIR / 'AmShip.json', 'w') as f:
        print("LOGGING")
        new_out = {}
        exclude_keys = [address_object_field, date_object_field, service_object_field]
        for count, (key, shipment) in enumerate(manifest.items()):
            output = {k: shipment[k] for k in set(list(shipment.keys())) - set(exclude_keys)}
            date_blah = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
            new_out.update({date_blah+" - "+str(shipment[is_shipped_field])+" - "+shipment[customer_field]: output})
            print("dumped")
        json.dump(new_out, f)

    print("FINISHED")
    if input("Restart?") == "yes":
        process_manifest(manifest)
    else:
        exit()


class Shipment:
    def __init__(self, shipment_dict):
        print("SHIPMENT DICT")
        pprint(shipment_dict)
        for key in shipment_dict:
            self.key = key
