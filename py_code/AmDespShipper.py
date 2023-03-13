import json
import os
import pathlib
import sys
from sys import exit
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pprint import pprint
from dateutil.parser import parse

from py_code.despatchbay.despatchbay_sdk import DespatchBaySDK
from py_code.utils_pss.utils_pss import toCamel, unsanitise, Utility

import dotenv

dotenv.load_dotenv()

SHIPDIR = os.path.abspath(os.path.dirname(__file__))
mydir = pathlib.Path()

LINE = '-' * 100
TABBER = "\t\t"
DEBUG = False
DT_DISPLAY = '%A - %B %#d'
DT_HIRE = '%d/%m/%Y'
DT_DB = '%Y-%m-%d'
DT_EXPORT = '%d-%m-%Y'


class ShippingApp:
    def __init__(self, ship_mode):  # creat app-obj
        # create config object
        self.CNFG = Config(ship_mode)
        # todo cnlear config refs to xmlfile

    def run(self, xmlfile):
        # debug hacky xml insertion for restart
        if xmlfile is None:
            xmlfile = self.CNFG.data_dir / 'Amship.xml'
        shipment = self.prepare_shipment(xmlfile)
        self.process_shipment(shipment)

    def prepare_shipment(self, xmlfile):
        ship_dict = self.xml_to_ship_dict(xmlfile)  # creates ship_dict from xmlfile, calls clean_dict
        shipment = Shipment(ship_dict,
                            self.CNFG)  # creates shipment-obj from ship_dict, passes config object for dbay client etc
        shipment.boxes = shipment.boxes_script()  # checks if there are boxes on the shipment, prompts input and confirmation
        shipment.date = shipment.date_script()  # checks collection is available on the sending date, prompts confirmation
        shipment.address = shipment.address_script()  # checks provided address against dbay for user confirmation / amendment
        return shipment

    def process_shipment(self, shipment, service=None):
        client = self.CNFG.client
        shipment.make_request(service)  # make a shipment_request to despatchbay
        decision = shipment.queue_or_book()  # display shipment_request details and get user_input:

        if decision == "QUEUE":
            # add shipment to dbay queue but don't book collection. no labels or tracking are available and no charge is made
            client.add_shipment(shipment.shipmentRequest)
            shipment.log_json()  # log to jsonfile

        elif decision == "BOOKANDPRINT":
            # the full works
            shipment.desp_shipment_id = client.add_shipment(shipment.shipmentRequest)  # add to dbay queue
            shipment.book_collection()  # book collection
            shipment.print_label()  # download and print pdf (requires correct windows default pdf handler eg sumatra)
            if shipment.category == 'Customer':
                print("Nowhere to log tracking for customer entries")
            else:
                shipment.log_tracking()  # get tracking data and log it to commence db
            shipment.log_json()  # log shipment and outcome to json
            exit()

        elif decision == "RESTART":
            self.run(xmlfile=None)

        elif decision == "EXIT":
            exit()

        elif decision == "SERVICE_CHANGE":
            # change shipping service eg for Express services
            services = shipment.services  # requires a shipment_request
            print(f"Available services:\n")
            for n, service in enumerate(shipment.services, 1):
                print(f"Service ID {n} : {service.name}")

            while True:
                choice = input("\nEnter a Service ID\n")
                if choice.isnumeric() and 0 < int(choice) <= len(services):
                    new_service = services[int(choice) - 1]
                    print(f"{new_service.service_id=}, {new_service.name=}")
                    # self.shipment.CNFG.service_id = new_service.service_id
                    # self.shipment.shippingServiceName = new_service.name
                    self.process_shipment(shipment, service=new_service)
                else:
                    print("Bad input")
                continue

        else:
            print(f"ERROR: \n {decision=}")

        exit()

    def xml_to_ship_dict(self, xmlfile):
        """
        :param xmlfile
        calls clean_dict
        :return: ship_dict
        """
        # if debug: print("XML IMPORTER ACTIVATED")

        ship_dict = dict()

        # inspect xml
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        fields = root[0][2]
        category = root[0][0].text

        for field in fields:
            k = field[0].text
            v = field[1].text
            if v:
                if "Number" in k:
                    v = v.replace(",", "")
                ship_dict.update({k: v})

        # get customer
        if category == "Hire":
            customer = root[0][3].text  # debug

        elif category == "Customer":
            customer = fields[0][1].text
            ship_dict['send Out Date'] = datetime.today().strftime(
                DT_HIRE)  # sets send_date to a string of today formatted like hire
            ship_dict['delivery tel'] = ship_dict['Deliv Telephone']
            # ship_dict.update({'Name':ship_dict['Name']+f"{datetime.now():{DT_EXPORT}}"})
            ship_dict['Name'] += f" {datetime.now():{DT_EXPORT}}"

        elif category == "Sale":
            customer = root[0][3].text  # debug
            ship_dict['Delivery Tel'] = ship_dict['Delivery Telephone']
            # set send_date to a string of today formatted like hire
            ship_dict['send Out Date'] = datetime.today().strftime(DT_HIRE)


        else:
            print("ERROR NO CATEGORY")
            return "ERROR NO CATEGORY"
        ship_dict.update({'Customer': customer})
        ship_dict.update({'Category': category})
        ship_dict.update({'Shipment Name': ship_dict['Name']})
        ship_dict = self.clean_ship_dict(ship_dict)

        if 'boxes' not in ship_dict.keys():
            ship_dict['boxes'] = 0

        if DEBUG:
            print(f"Making {category} shipment for {customer} with {len(ship_dict)} populated fields")

        for attr_name in self.CNFG.shipment_fields:
            if attr_name not in ship_dict.keys():
                print(f"*** Warning - {attr_name} not found in ship_dict - Warning ***")

        return ship_dict

    def clean_ship_dict(self, dict) -> dict:
        """
        cleans your dict

        :param dict:
        :return:
        """
        if DEBUG: print('Cleaning Xml')
        newdict = {}
        if "Send Out Date" not in dict.keys():
            print("No date - added today")
            dict['Send Out Date'] = datetime.today().strftime(DT_HIRE)
        for k, v in dict.items():
            k = unsanitise(k)
            k = toCamel(k)
            if "deliv" in k:
                if "delivery" not in k:
                    k = k.replace('deliv', 'delivery')

            if v:
                v = unsanitise(v)
                if isinstance(v, list):
                    v = v[0]
                if v.isnumeric():
                    v = int(v)
                    if v == 0:
                        v = None
                elif v.isalnum():
                    v = v.title()
                if 'Price' in k:
                    v = float(v)

            newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        return newdict


class Shipment:
    def __init__(self, ship_dict, CNFG, reference=None,
                 label_text=None):
        """
        :param ship_dict: a dictionary of shipment details
        :param CNFG: a config() object
        :param reference:
        :param label_text:
        """

        self.desp_shipment_id = None
        self.CNFG = CNFG
        self.sender = CNFG.client.sender(address_id=CNFG.sender_id)
        self.available_dates = CNFG.client.get_available_collection_dates(self.sender,
                                                                          CNFG.courier_id)  # get dates
        ## mandatory shipment details

        try:

            self.deliveryContact = ship_dict['deliveryContact']
            self.deliveryTel = ship_dict['deliveryTel']
            self.deliveryEmail = ship_dict['deliveryEmail']
            self.deliveryAddressStr = ship_dict['deliveryAddress']
            self.deliveryPostcode = ship_dict['deliveryPostcode']
            self.sendOutDate = ship_dict['sendOutDate']
            self.category = ship_dict['category']
            self.customer = ship_dict['customer']
            self.shipmentName = ship_dict['name']
            self.boxes = ship_dict['boxes']
            if DEBUG:
                print(f"{self.shipmentName=}")

        except KeyError as e:
            print(f"Key error - something missing from shipdict \n{e}")
            if not self.deliveryTel:
                self.deliveryTel = input("Enter Delivery Phone Number")

        if label_text:
            self.label_text = label_text
        else:
            self.label_text = self.customer

        self.parcels = None
        self.collectionBooked = False
        self.labelLocation = None
        self.shippingServiceName = None
        self.shippingCost = None
        self.trackingNumbers = None
        self.date = None

        if DEBUG:
            print(f"Shipment with {self.shipmentName=}")

        def parse_address(str_address):
            if DEBUG:
                print("--- Parsing Address...")
            # crapstring = self.deliveryAddress
            firstline = str_address.strip().split("\n")[0]
            first_block = (str_address.split(" ")[0]).split(",")[0]
            first_char = first_block[0]
            for char in firstline:
                if not char.isalnum() and char != " ":
                    firstline = firstline.replace(char, "")

            if first_char.isnumeric():
                return first_block
            else:
                return firstline

        self.search_term = parse_address(self.deliveryAddressStr)

    def boxes_script(self):
        """:returns a number of boxes to send"""

        if DEBUG: print("func = VAL_BOXES")
        if self.boxes or self.boxes == 0:
            boxes = self.boxes
            if boxes == 0:
                boxes = 1
            ui = input(
                f"{TABBER} {boxes} box(es) assigned for {self.customer}"
                f" \n \nEnter a number to adjust, anything else to continue\n")
            if ui.isnumeric():
                print(f"Shipment updated to {ui} boxes")
                boxes = int(ui)

            # backdoor to checkin vbs scripts to commence via powershell and cmclibnet
            if str(ui) == "check":
                categories = input("Categories?")
                categories = categories.split()
                for category in categories:
                    Utility.powershell_runner(str(self.CNFG.cmc_checkin), category)

            return boxes


        else:
            while True:
                print(f"\n{TABBER}*** ERROR: No boxes added ***\n")
                ui = input(f"- How many boxes for shipment to {self.customer}?\n")
                if not ui.isnumeric():
                    print("- Enter a number")
                    continue
                else:
                    boxes = int(ui)
                    print(f"Shipment updated to {ui} boxes")
            return boxes

    def date_script(self, force=False):
        print(f"--- Checking available collection dates...")
        if DEBUG: print("func = VAL_DATES")

        # compare provided send_out date with actually available collection dates in dbay format
        # if matched get date object formatted to use with dbay api
        send_date_obj = parse(self.sendOutDate)
        send_date = datetime.strftime(send_date_obj, DT_DB)
        available_dates = self.available_dates
        for potential_collection_date in available_dates:

            potential_date_str = str(potential_collection_date.date)
            if potential_date_str == send_date:
                dateObject = potential_collection_date
                day = parse(potential_collection_date.date)
                day = datetime.strftime(day, DT_DISPLAY)
                print(f"Collection date match - shipment for {self.customer} will be collected on {day}\n", LINE)
                if not force:  # else continue to user input loop
                    return dateObject

        while True:
            # display available dates
            print(
                f"\n*** ERROR: No collections available on {send_date_obj:{DT_DISPLAY}} ***\n\n\n- Collections for {self.customer} are available on:\n")
            for count, date in enumerate(available_dates, 1):  # 1 index
                dt = parse(date.date)
                out = datetime.strftime(dt, DT_DISPLAY)
                print(f"{TABBER} {count} | {out}")

            # get input
            choice = input(
                f'\n- [Enter] for asap ({datetime.strftime(parse(available_dates[0].date), DT_DISPLAY)}), [A Number] to choose a date, [0] to exit\n')

            if not choice:  # enter to select first available (still 1 index)
                choice = 1
                break
            if not choice.isnumeric():
                print("- Enter a number")
                continue
            if choice.isnumeric():  # choice is numeric - specify collection date
                choice = int(choice)
                if 0 <= choice <= len(available_dates):  # choice in range
                    break
                else:
                    print("out of range")
                    continue
            if choice == 0:
                if input(str('[E]xit?'))[0].lower() == "e":
                    exit()

        dateObject = available_dates[choice - 1]  # 1 index
        print(f"{TABBER} Collection date for", self.customer, "is now ", dateObject.date, "\n\n",
              LINE)
        return dateObject

    def address_script(self, address=None):
        """a script to confirm a proper address has been selected
        searches dbay using postcode and building number / firstline
        if first result is not suitable lists addresses at given postcode
        if none are suitable takes new postcode as input

        once selected, address is presented to user for amendment and/or confirmation
        and returned to

        :return: address:
        """
        if address is None:
            if address_from_search := self.address_from_postcode_and_string(
                    postcode=self.deliveryPostcode, search_string=self.search_term):  # walrus assigns and checks
                address = address_from_search
            else:
                address = self.address_from_postcode_candidates(postcode=self.deliveryPostcode)

        address = self.check_address(address)  # displays address to user
        address_decision = input(f"\n[G]et new address or [A]mend current address, anything else to continue\n\n")

        if address_decision:
            address_decision = str(address_decision)[0].lower()
            if address_decision == "a":
                address = self.amend_address(address)
            elif address_decision == "g":
                address = self.address_from_postcode_candidates(address.postal_code)
                self.address_script(address)

        return address

    #
    # def address_script(self, address=None):
    #     """a script to confirm a proper address has been selected
    #     searches dbay using postcode and building number / firstline
    #     if first result is not suitable lists addresses at given postcode
    #     if none are suitable takes new postcode as input
    #
    #     once selected, address is presented to user for amendment and/or confirmation
    #
    #     :return: address:
    #     """
    #     if address is None:
    #         if address_from_search := self.address_from_postcode_and_string(
    #                 postcode=self.deliveryPostcode):  # walrus assigns and checks
    #             address = address_from_search
    #         else:
    #             address = self.address_from_postcode_candidates(postcode=self.deliveryPostcode)
    #
    #     address = self.check_address(address)  # displays address to user
    #     address_decision = input(f"\n[G]et new address or [A]mend current address, anything else to continue\n\n")
    #     if address_decision:
    #         address_decision = str(address_decision)[0].lower()
    #         if address_decision == "a":
    #             address = self.amend_address(address)
    #         elif address_decision == "g":
    #             address = self.address_from_postcode_candidates(address.postal_code)
    #             self.address_script(address)
    #
    #     return address

    def address_from_postcode_and_string(self, postcode: str = None, search_string: str = None):
        """
        validates a postcode and search_string against despatchbay address database

        if postcode is none get it from Shipment
        if search_string is none use Shipment.building num or else Shipment.firstline

        :param postcode or None:
        :param search_string or Shipment.building_num or firstline:
        :return: address or None:
        """
        if DEBUG: print("func = val_address\n")

        if postcode is None:
            postcode = input("Enter Postcode")

        if search_string is None:
            search_string = input("Enter Search String")

        try:
            address = self.CNFG.client.find_address(postcode, search_string)
        except:
            print("No address match found - go list from postcode")
            return None
        return address

    def address_from_postcode_candidates(self, postcode=None):
        """
        takes a postcode or gets from user input
        queries despatchbay and lists addresses at postcode
        returns user-selected address

        is called by:
            address script if no address has been provided
            check_address() method if no address provided or user doesn't like the displayed address

        :param postcode:
        :return address:
        """
        if DEBUG:
            print("func = change_address \n")

        got_address = False
        while not got_address:
            if postcode is None:
                postcode = input("Enter Postcode\n")

            try:
                candidates = self.CNFG.client.get_address_keys_by_postcode(postcode)
            except:
                print("bad postcode")
                postcode = None
                continue

            else:
                # list candidates and get choice from user
                while candidates:
                    for count, candidate in enumerate(candidates, start=1):
                        print(" - Candidate", str(count) + ":", candidate.address)

                    chosen_candidate = input(
                        '\n- Enter a candidate number, or a postcode to search\n')

                    if not chosen_candidate:
                        continue

                    if chosen_candidate.isnumeric():
                        chosen_candidate = int(chosen_candidate)
                        if not 0 < chosen_candidate <= len(candidates):
                            print("Wrong Number")
                            continue

                        selected_key = candidates[int(chosen_candidate) - 1].key  # get address from despatchbay key
                        address = self.CNFG.client.get_address_by_key(selected_key)
                        print(f"\n - Company: {address.company_name}, Street address:{address.street}")
                        return address

                    else:  # input not a number = a postcode
                        # reset postcode and restart main loop
                        postcode = chosen_candidate
                        break

    def amend_address(self, address=None):
        """
        takes an address or gets from Shipment
        lists variables in address and edits as per user input
        updates Shipment.address
        :param address:
        :return: address and update Shipment.address
        """
        if DEBUG:
            print("func = amend_address\n")

        if address is None:
            address = self.address

        address_vars = self.CNFG.db_address_fields  # get a list of vars considered 'address' from cnfg

        while True:
            print(f"current address: \n")
            # print each attribute of the address object with a 1-indexed identifier
            for c, var in enumerate(address_vars, start=1):
                print(f"{TABBER} {c} - {var} = {getattr(address, var)}")

            # get user selection
            ui = input("\n [Enter] to continue or a number to edit the field\n")

            if not ui:
                return address

            if not ui.isnumeric():
                continue

            ui = int(ui)
            uii = ui - 1  # zero index

            if not uii <= len(address_vars):
                print("wrong number")
                continue

            var_to_edit = address_vars[uii]
            new_var = input(f"{var_to_edit} is currently {getattr(address, var_to_edit)} - enter new value \n")

            while True:
                cont = input(f"[C]hange {var_to_edit} to {new_var}? (anything else to cancel)")
                if cont and cont.isalpha():
                    cont1 = cont[0].lower()
                    if cont1 == 'c':
                        setattr(address, var_to_edit, new_var)
                        self.address = address
                        break  # and go back to previous loop


                else:
                    break  # back to previous loop

    def check_address(self, address=None):
        """
        displays Shipment.address
        takes user input to confirm, change, or amend
        :return: address and updates Shipment.address
        """
        if DEBUG:
            print("func = check_address \n")
        if address is None:
            address = self.address
        while address:
            postcode = address.postal_code

            # print address fields of shipment-obj to the screen
            filtered_address_fields = {k: v for k, v in vars(address).items() if k in self.CNFG.db_address_fields}
            print("Current address details:\n")

            print(f'{os.linesep.join(f"{TABBER}{k}: {v}" for k, v in filtered_address_fields.items())}')

            # offer to replace None company name with customer name
            if address.company_name is None:
                ui = input(f"\n \nReplace 'None' Company Name with {self.customer}? [Y / N]\n")
                if not ui or str(ui[0]).lower() == 'y':
                    address.company_name = self.customer
                    print(f"{TABBER} Company Name updated")
                else:
                    print("Keep company 'None'")
            self.address = address
            return address

    def queue_or_book(self):
        """
        gets user input and returns a response code to caller

        :return: Response code for process_shipment
        """
        if DEBUG:
            print("func = Queue or book\n")

        while True:
            self.print_shipment_to_screen()
            choice = input(
                '- [Q]ueue shipment in DespatchBay, [B]ook + print [S]elect new service, [R]estart, or [E]xit\n')

            if choice:
                choice1 = str(choice[0].lower())

                if choice1 == "b":
                    print("Booking Collection and printing label")
                    return "BOOKANDPRINT"

                elif choice1 == "q":
                    print("Adding Shipment to Despatchbay Queue")
                    return "QUEUE"

                elif choice1 == 'r':
                    print("Restarting")
                    return "RESTART"

                elif choice1 == "e":
                    print("Exiting")
                    return "EXIT"

                elif choice1 == "s":
                    return "SERVICE_CHANGE"

                else:
                    print(f"{choice} is not a valid input")
            else:
                print("No input")
            continue

    def make_request(self, service=None):
        """ builds a dbay shipment_request
        if no service is provided (eg Express) default (Parcelforce 24) is used"""
        print("MAKING REQUEST")
        client = self.CNFG.client
        recipient_address = client.address(
            company_name=self.customer,
            country_code="GB",
            county=self.address.county,
            locality=self.address.locality,
            postal_code=self.address.postal_code,
            town_city=self.address.town_city,
            street=self.address.street
        )

        recipient = client.recipient(
            name=self.deliveryContact,
            telephone=self.deliveryTel,
            email=self.deliveryEmail,
            recipient_address=recipient_address

        )
        self.parcels = []
        for x in range(self.boxes):
            parcel = client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            self.parcels.append(parcel)

        # self.shipmentRequest = client.shipment_request(
        shipmentRequest = client.shipment_request(
            parcels=self.parcels,
            client_reference=self.label_text,
            collection_date=self.date.date,
            sender_address=self.sender,
            recipient_address=recipient,
            follow_shipment='true',
            service_id=self.CNFG.service_id
        )
        shipmentRequest.collection_date = self.date.date

        services = client.get_available_services(shipmentRequest)
        if services[0].service_id != self.CNFG.service_id:
            print("Shipping service is not default")
        if service:
            self.shippingCost = service.cost
            self.shippingServiceName = service.name
        else:
            self.shippingServiceName = services[0].name
            self.shippingCost = services[0].cost
        self.services = services
        self.shipmentRequest = shipmentRequest

    def book_collection(self):
        if DEBUG: print("func = BOOK_COLLECTION \n")
        client = self.CNFG.client

        # book collection
        shipment_return = client.book_shipments(self.desp_shipment_id)[0]  # debug there could be more than one here??
        self.collectionBooked = True

        # save label
        label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
        try:
            label_string = f"{self.customer} - {str(self.date.date)}.pdf"
        except:
            label_string = f"{self.customer}.pdf"
        label_pdf.download(self.CNFG.label_dir / label_string)
        self.labelLocation = str(self.CNFG.label_dir / label_string)

        # save tracking numbers
        self.trackingNumbers = []
        for parcel in shipment_return.parcels:
            self.trackingNumbers.append(parcel.tracking_number)

        print(
            f"\nCollection has been booked for {self.customer} on {self.date.date} "
            f"\nLabel downloaded to {self.labelLocation}.")
        return True

    def print_label(self):
        try:
            os.startfile(self.labelLocation, "print")
        except OSError:
            print("\nERROR: Unable to print\n  -   is default PDF application selected in Windows?")
        self.printed = True

    def print_shipment_to_screen(self):
        print(
            f"\n {LINE} \n {self.customer} | {self.boxes} | {self.address.street} | {self.date.date} | {self.shippingServiceName} | Price = {self.shippingCost * self.boxes} \n {LINE} \n")

    def log_tracking(self):
        """
        runs cmclibnet via powershell script to add tracking numbes to commence db

        :return:
        """
        cmcLibpath = self.CNFG.cmc_lib_net_dll
        tracking_nums = ', '.join(self.trackingNumbers)
        ps_script = str(self.CNFG.log_to_commence_powershell_script)
        try:  # utility class static method runs powershell script bypassing execuction policy
            commence_edit = Utility.powershell_runner(ps_script, self.shipmentName, tracking_nums,
                                                      self.category)
            if DEBUG:
                print(f"{commence_edit=}")

        except Exception as e:
            print(f"{e=}")
            print("\nERROR: Unable to log tracking to Commence")
            if not os.path.exists(ps_script):
                print("  -   Powershell script missing")
            if not os.path.exists(cmcLibpath):
                print("  -   Vovin CmCLibNet missing")
        else:
            print("\nCommence Tracking updated")

    def log_json(self):
        # export from object attrs

        export_dict = {}
        for field in self.CNFG.export_fields:
            if field in vars(self):
                val = getattr(self, field)
                val = f"{val:{DT_EXPORT}}" if isinstance(val, datetime) else val
                export_dict.update({field: val})
            else:
                print(f"{field} not found in shipment")
        export_dict.update({"timestamp": datetime.now().isoformat(' ', timespec='seconds')})
        export_dict.update({"dispatch_address": f"{self.address.postal_code}-{self.address.street}"})
        with open(self.CNFG.log_file, 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",\n")
        print(f"{os.linesep} Json exported to {self.CNFG.log_file}:")
        pprint(export_dict)


class Config:
    def __init__(self, ship_mode):

        # fields
        self.export_fields = ['customer', 'shipmentName', 'deliveryContact', 'deliveryTel',
                              'deliveryEmail', 'trackingNumbers', 'desp_shipment_id', 'boxes', 'collectionBooked',
                              'category']  # debug 'deliveryName',
        self.shipment_fields = ['deliveryContact', 'deliveryTel', 'deliveryEmail',
                                'deliveryAddress', 'deliveryPostcode', 'sendOutDate',
                                'category', 'shipmentName']  # debug 'deliveryName',
        self.db_address_fields = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']

        # paths

        # get root dir
        # PyInstaller sets sys._MEIPASS to the path of the executable
        if getattr(sys, 'frozen', False):
            self.root = pathlib.Path(sys._MEIPASS) # pyinstaller voodoo -  ignore intellisense
        else:
            self.root = pathlib.Path.cwd()


        self.data_dir = self.root / 'data'
        self.scripts_dir = self.root / 'scripts'
        self.label_dir = self.data_dir / 'Parcelforce Labels'
        self.log_file = self.data_dir / 'AmLog.json'
        self.label_dir.mkdir(parents=True, exist_ok=True)

        # Vovin CmcLibNet files for interacting with Commence DB:
        # powershell to check scripts into commence (backdoor = 'check' at first prompt, then category names)
        self.cmc_checkin = self.scripts_dir / 'cmc_checkin.ps1'
        # powershell to log tracking details
        self.log_to_commence_powershell_script = self.scripts_dir / 'log_tracking_to_Commence.ps1'
        self.cmc_lib_net_dll = pathlib.Path('c:/Program Files/Vovin/Vovin.CmcLibNet/Vovin.CmcLibNet.dll')
        self.cmcLibNet_installer = self.root / 'CmcLibNet_Setup.exe'
        if not self.cmc_lib_net_dll.exists():
            print(
                "ERROR: Vovin CmCLibNet is not installed in expected location 'Program Files/Vovin/Vovin.CmcLibNet/Vovin.CmcLibNet.dll'")
            if self.cmcLibNet_installer.exists():
                print("Launching CmcLibNet installer")
                if os.startfile(self.cmcLibNet_installer):
                    print("CmcLib Installed")
                else:
                    print("ERROR: CmcLibNet Installer Failed - logging to commence is impossible")
            else:  # no installer
                print(
                    "\n ERROR: CmcLinNet installer missing from '/dist' \nPlease download Installer from https://github.com/arnovb-github/CmcLibNet/releases and install to default program files location"
                    "\n Logging to Commence is impossible")

        if DEBUG:
            print(f"{self.root=}")
            print(f"{self.cmcLibNet_installer=}")


        # parse shipmode argument and setup despatchbay API keys from .env
        if ship_mode == "sand":
            print("\n \n \n *** !!! SANDBOX MODE !!! *** \n \n \n")
            api_user = os.getenv("DESPATCH_API_USER_SANDBOX")
            api_key = os.getenv("DESPATCH_API_KEY_SANDBOX")
            self.courier_id = 99
            self.service_id = 9992
        elif ship_mode == 'prod':
            api_user = os.getenv("DESPATCH_API_USER")
            api_key = os.getenv("DESPATCH_API_KEY")
            self.courier_id = 8  # parcelforce
            self.service_id = 101  # parcelforce 24

        else:
            print("SHIPMODE FAULT - EXIT")
            exit()

        self.sender_id = os.getenv("DESPATCH_SENDER_ID")
        self.client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        self.sender = self.client.sender(address_id=self.sender_id)

    def check_in_vbs(self, category):
        ...

    def fake_ship_request(self):
        """ for getting available serivces etc"""

        recip_add = self.client.address(
            company_name='noname',
            country_code="GB",
            county="London",
            locality='London',
            postal_code='nw64te',
            town_city="london",
            street="72 kingsgate road"
        )
        recip = self.client.recipient(
            name="fakename",
            recipient_address=recip_add)

        # sandy
        shippy = self.client.shipment_request(
            parcels=[self.client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )],
            collection_date=f"{date.today():%Y-%m-%d}",
            sender_address=self.sender,
            recipient_address=recip)
        return shippy

    def list_services(self, shipment_request):
        services = self.client.get_available_services(shipment_request)
        for service in services:
            print(f"{service.service_id} - {service.name}")
