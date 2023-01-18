"""
notes
crippled moving
"""

import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pprint import pprint

from dateutil.parser import parse

from python.despatchbay.despatchbay_sdk import DespatchBaySDK
from python.utils_pss.utils_pss import toCamel, get_from_ods, unsanitise

CONFIG_ODS = r"C:\AmDesp\data\AmDespConfig.ods"
FIELD_CONFIG = 'FIELD_CONFIG'
line = '-' * 100
debug = False


class Config:
    def __init__(self, ship_mode, xmlfileloc=None):
        self.config_ods = CONFIG_ODS

        # fieldnames
        # hirename
        self.export_fields = ['customer', 'shipmentName', 'deliveryName', 'deliveryContact', 'deliveryTel', 'deliveryEmail',
                              'deliveryAddress', 'deliveryPostcode', 'sendOutDate', 'referenceNumber',
                              'trackingNumbers', 'desp_shipment_id', 'boxes', 'collectionBooked', 'shipRef',
                              'category']
        self.shipment_fields = ['deliveryName', 'deliveryContact', 'deliveryTel', 'deliveryEmail',
                                'deliveryAddress', 'deliveryPostcode', 'sendOutDate', 'referenceNumber',
                                'category', 'shipmentName']
        self.db_address_fields = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']

        # paths
        self.root = pathlib.Path("/Amdesp")
        self.data_dir = pathlib.Path("/Amdesp/data/")
        self.label_dir = self.data_dir / "Parcelforce Labels"
        self.Json_File = self.data_dir.joinpath("AmShip.json")
        if xmlfileloc:
            self.xml_file = self.data_dir.joinpath(xmlfileloc)
        else:
            self.xml_file = self.data_dir.joinpath('AmShipHire.xml')
        self.log_file = self.data_dir.joinpath("AmLog.json")
        self.config_file = self.data_dir.joinpath("AmDespConfig.Ods")
        self.bin_dir = pathlib.Path("/Amdesp/bin/")
        self.pdf_to_print = self.root.joinpath("PDFtoPrinter.exe")

        # make the labels dirs (and parents)
        pathlib.Path(self.data_dir / "Parcelforce Labels").mkdir(parents=True,
                                                                 exist_ok=True)

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

        self.sender_id = "5536"  # should be env var?
        self.client = DespatchBaySDK(api_user=api_user, api_key=api_key)  # now in shipment
        self.sender = self.client.sender(address_id=self.sender_id)  # in shipment

        # def list_services():
        #     recip_add = self.client.address(
        #         company_name='noname',
        #         country_code="GB",
        #         county="London",
        #         locality='London',
        #         postal_code='nw64te',
        #         town_city="london",
        #         street="72 kingsgate road"
        #     )
        #     recip = self.client.recipient(
        #         name="fakename",
        #         recipient_address=recip_add)
        #
        #     # sandy
        #     shippy = self.client.shipment_request(
        #         parcels=[self.client.parcel(
        #             contents="Radios",
        #             value=500,
        #             weight=6,
        #             length=60,
        #             width=40,
        #             height=40,
        #         )],
        #         collection_date=f"{date.today():%Y-%m-%d}",
        #         sender_address=self.sender,
        #         recipient_address=recip)
        #
        #     services = self.client.get_available_services(shippy)
        #     for service in services:
        #         print (service.name)
        # # list_services()


class ShippingApp:
    def __init__(self, ship_mode, xmlfileloc=None):  # make app
        self.CNFG = Config(ship_mode, xmlfileloc=xmlfileloc)
        self.shipment = None

    def prepare_shipment(self):
        ship_dict = self.xml_to_ship_dict()
        self.shipment = Shipment(ship_dict, self.CNFG)
        # self.shipment = Shipment(parsed, self.CNFG, parent=self)
        self.shipment.boxes = self.shipment.val_boxes()  # checks if there are boxes on the shipment, prompts input and confirmation #debug
        self.shipment.val_dates()  # checks collection is available on the sending date
        self.shipment.address = self.shipment.address_script()  #
        self.shipment.check_address()  # queries DB address database, prompts user to confirm match or call amend_address()

    def process_shipment(self):
        # no self.address here?
        self.shipment.make_request()  # make a shipment request
        decision = self.shipment.queue_or_book()

        if decision == "QUEUE":
            self.desp_shipment_id = self.CNFG.client.add_shipment(self.shipment.shipmentRequest)

        if decision == "BOOKANDPRINT":
            self.shipment.desp_shipment_id = self.CNFG.client.add_shipment(self.shipment.shipmentRequest)
            # self.CNFG.client.add_shipment(self.shipment.shipmentRequest)
            # debug issues here
            self.shipment.book_collection()
            self.shipment.print_label()

        if decision == "RESTART":
            self.process_shipment()

        if decision != "EXIT":
            print(f"ERROR: \n {decision=}")

        self.log_json()
        exit()

    def xml_to_ship_dict(self):
        """
        gets xml from CNFG and makes a dictionary of it's contents

        :return: ship_dict
        """
        # if debug: print("XML IMPORTER ACTIVATED")

        ship_dict = dict()

        # inspect xml
        tree = ET.parse(self.CNFG.xml_file)
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
                '%d/%m/%Y')  # datedebug sets customer shipment send date to a string of today formatted like hire
            ship_dict['delivery tel'] = ship_dict['Deliv Telephone']

        elif category == "Sale":
            customer = root[0][3].text  # debug
            ship_dict['Delivery Tel'] = ship_dict['Delivery Telephone']
            # ship_dict['delivery tel'] = ship_dict['Delivery Postcode']


        else:
            print("ERROR NO CATEGORY")
            return "ERROR NO CATEGORY"
        ship_dict.update({'Customer': customer})
        ship_dict.update({'Category': category})
        ship_dict.update({'Shipment Name': ship_dict['Name']})
        ship_dict = self.clean_ship_dict(ship_dict)

        if 'boxes' not in ship_dict.keys():
            ship_dict['boxes'] = 0

        # am i doing this elsewhere?
        # for k, v in ship_dict.items():
        #     if type(k) == datetime:
        #         v = datetime.strptime(v, '%d/%m/%Y')  # datedebug

        if debug:
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
        if debug: print('Cleaning Xml')
        newdict = {}
        if "Send Out Date" not in dict.keys():
            print("No date - added today")
            dict['Send Out Date'] = datetime.today().strftime('%d/%m/%Y')
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

    def log_json(self):
        # export from object attrs?
        # if "referenceNumber" not in vars(self.shipment):
        #     self.shipment.referenceNumber = self.shipment.id

        export_dict = {}
        for field in self.CNFG.export_fields:
            if field in vars(self.shipment):
                val = getattr(self.shipment, field)
                val = f"{val:%d-%m-%Y}" if isinstance(val, datetime) else val
                export_dict.update({field: val})
            else:
                print(f"{field} not found in shipment")

        with open(self.CNFG.log_file, 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",\n")
            pprint(f"\n Json exported to {self.CNFG.log_file} {export_dict =}")

        if self.shipment.category in ['Hire', 'Sale']:
                self.log_tracking()  # writes to commence db

    def log_tracking(self):
        """
        runs cmclibnet via powershell script to add tracking numbes to commence db

        :return:
        """

        """
        notes:
        
        """
        powershell_script = r"C:\AmDesp\vbs\Edit_Commence.ps1"
        # debug is shipment.name here?
        tracking_nums = ', '.join(self.shipment.trackingNumbers)

        subprocess.run([
            "powershell.exe",
            "-File",
            powershell_script,
            self.shipment.shipmentName,
            tracking_nums,
            self.shipment.category
        ],
            stdout=sys.stdout)


class Shipment:
    def __init__(self, ship_dict, CNFG, reference=None,
                 label_text=None):
        """
        :param ship_dict: a dictionary of shipment details
        :param CNFG: a config() object
        :param reference:
        :param label_text:
        """

        self.CNFG = CNFG
        self.sender = CNFG.client.sender(address_id=CNFG.sender_id)
        self.dates = CNFG.client.get_available_collection_dates(self.sender,
                                                                CNFG.courier_id)  # get dates
        ## mandatory shipment details
        try:

            self.deliveryName = ship_dict['deliveryName']
            self.deliveryContact = ship_dict['deliveryContact']
            self.deliveryTel = ship_dict['deliveryTel']
            self.deliveryEmail = ship_dict['deliveryEmail']
            self.deliveryAddress = ship_dict['deliveryAddress']
            self.deliveryPostcode = ship_dict['deliveryPostcode']
            self.sendOutDate = ship_dict['sendOutDate']
            self.category = ship_dict['category']
            self.customer = ship_dict['customer']
            self.shipmentName = ship_dict['name']
            self.boxes = ship_dict['boxes']
            print(f"{self.shipmentName=}")
            # hirename

        except KeyError:
            print("Key error - something missing from shipdict")

        ## optional shipment details
        self.referenceNumber = self.shipmentName
        # print(f"{self.referenceNumber=}")
        #
        # if reference_number:
        #     self.referenceNumber = reference_number
        # elif 'referenceNumber' in ship_dict.keys():
        #     self.referenceNumber = ship_dict['referenceNumber']
        # else:
        #     self.referenceNumber = "101"

        if label_text:
            self.reference_on_label = label_text  ## if there is a shipref passed use it as despatchbay reference on label etc
        else:
            self.reference_on_label = self.customer

        ## obtained shipment details
        self.deliveryBuildingNum = None
        self.deliveryFirstline = None
        self.parcels = None

        self.collectionBooked = False
        self.shipmentDocId = None
        self.labelUrl = None
        self.labelDownloaded = False
        self.labelLocation = None
        self.printed = False
        self.shippingServiceName = None

        self.shippingCost = None
        self.trackingNumbers = None

        # DespatchBay Objects

        self.desp_shipment_id = None
        self.address = ship_dict['deliveryAddress']
        self.dateObject = None
        self.shipmentRequest = None
        self.shipmentReturn = None
        self.recipient = None

        if debug:
            print(f"Shipment with {self.shipmentName=}")

        def parse_address():
            if debug:
                print("--- Parsing Address...")
            crapstring = self.deliveryAddress
            firstline = crapstring.split("\n")[0]
            first_block = (crapstring.split(" ")[0]).split(",")[0]
            first_char = first_block[0]
            self.deliveryFirstline = firstline
            for char in firstline:
                if not char.isalnum() and char != " ":
                    firstline = firstline.replace(char, "")
            if first_char.isnumeric():
                self.deliveryBuildingNum = first_block

        def val_date_init(self):
            if debug: print("func = VAL DATES INIT")
            if isinstance(self.sendOutDate, str):
                setattr(self, "sendOutDate", datetime.strptime(self.sendOutDate, '%d/%m/%Y'))
            for candidate in self.dates:
                if candidate.date == datetime.strftime(self.sendOutDate,
                                                       '%Y-%m-%d'):  # if date object matches send date
                    self.dateObject = candidate
                    print(line, '\n',
                          f"Shipment date = {datetime.strftime(self.sendOutDate, '%A %B %#d')}")
            # if debug:
            #     print("")

        parse_address()
        val_date_init(self)

    def val_boxes(self):
        if debug: print("func = VAL_BOXES")
        if 'boxes' in vars(self):
            ui = input(f"{self.boxes}  box(es) assigned for {self.customer} \n Enter a number to adjust, anything else to continue\n")
            if ui.isnumeric():
                print (f"Shipment updated to {ui} boxes")
                self.boxes=int(ui)
            return self.boxes

        else:
            while True:
                print("\n\t\t*** ERROR: No boxes added ***\n")
                ui = input(f"- How many boxes for shipment to {self.customer}?\n")
                if not ui.isnumeric():
                    print("- Enter a number")
                    continue
                else:
                    self.boxes = int(ui)
                    print(f"Shipment updated to {ui} boxes")
            return self.boxes

    def val_dates(self):
        if debug: print("func = VAL_DATES")
        dates = self.CNFG.client.get_available_collection_dates(self.sender,
                                                                self.CNFG.courier_id)  # get dates
        print("--- Checking available collection dates...")
        send_date = datetime.strftime(self.sendOutDate, '%Y-%m-%d')

        for despdate in dates:
            compdate = str(despdate.date)
            if compdate == send_date:  # if date object matches send date
                self.dateObject = despdate
                da = datetime.strftime(self.sendOutDate, '%A %B %#d')
                print(f"Collection date match - shipment for {self.customer} will be collected on {da}\n", line)
                return
        else:  # loop exhausted, no date match
            print(
                f"\n*** ERROR: No collections available on {self.sendOutDate:%A - %B %#d} ***\n\n\n- Collections for {self.customer} are available on:\n")
            for count, date in enumerate(dates):
                dt = parse(date.date)
                out = datetime.strftime(dt, '%A - %B %#d')
                print("\t\t", count + 1, "|", out)

            while True:
                choice = input('\n- Enter a number to choose a date, [0] to exit\n')
                if not choice: continue
                if not choice.isnumeric():
                    print("- Enter a number")
                    continue
                if not -1 <= int(choice) <= len(dates) + 1:
                    print('\nWrong Number!\n-Choose new date for', self.customer, '\n')
                    for count, date in enumerate(dates):
                        print("\t\t", count + 1, "|", date.date, )
                    continue
                if int(choice) == 0:
                    if input('[E]xit?')[0].lower() == "e":
                        exit()
                    continue
                else:
                    self.dateObject = dates[int(choice) - 1]
                    print("\t\tCollection date for", self.customer, "is now ", self.dateObject.date, "\n\n",
                          line)
                    return

    def address_script(self):
        """

        :return: address:
        """
        if debug: print("func = address script\n")

        address = self.val_address()

        if address is None:
            # list by postcode
            address = self.address_from_postcode(postcode=self.deliveryPostcode)
            # address = self.ammend_or_cont(address)
        return address

    def val_address(self, postcode: str = None, search_string: str = None):
        """
        validates a postcode and search_string against despatchbay address database

        if postcode is none get it from Shipment
        if search_string is none use Shipment.building num or else Shipment.firstline

        :param postcode or None:
        :param search_string or Shipment.building_num or firstline:
        :return: address or None:
        """
        if debug: print("func = val_address\n")

        if postcode is None:
            postcode = self.deliveryPostcode

        if search_string is None:
            if self.deliveryBuildingNum:
                # if self.deliveryBuildingNum != 0:
                search_string = self.deliveryBuildingNum
            else:
                search_string = self.deliveryFirstline
                print(f"No building number, searching by first line of address: {self.deliveryFirstline} \n")

        try:
            address = self.CNFG.find_address(postcode, search_string)
            # address = DespatchBaySDK.find_address(postcode, search_string)
            print(f"{postcode=}, {search_string=}")
        except:
            print("No address match found")
            return None
        else:
            return address

    def address_from_postcode(self, postcode=None):
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
        if debug:
            print("func = change_address \n")

        got_address = False
        while not got_address:
            if postcode is None:
                postcode = input("Enter Postcode\n")

            try:
                candidates = self.CNFG.client.get_address_keys_by_postcode(postcode)
            except:
                print("bad postcode")
                continue
                # self.address_from_postcode()

            else:
                while candidates:
                    for count, candidate in enumerate(candidates, start=1):
                        print(" - Candidate", str(count) + ":", candidate.address)

                    chosen_candidate = input(
                        '\n- Enter a candidate number, or a letter to cancel and search a new postcode \n')

                    if not chosen_candidate:
                        continue

                    if chosen_candidate.isalpha():
                        postcode = None
                        break

                    elif chosen_candidate.isnumeric():
                        chosen_candidate = int(chosen_candidate)

                        if not 0 <= chosen_candidate <= len(candidates):  # include 0 as exit
                            print("Wrong Number")
                            continue

                        selected_key = candidates[int(chosen_candidate) - 1].key
                        address = self.CNFG.client.get_address_by_key(selected_key)
                        print(f"\n - Company: {address.company_name}, Street address:{address.street}")
                        return address

    def ammend_or_cont(self, address):
        """
        takes address and user input

        :param address:
        :return amended address:
        """
        while True:
            ui = input(f"\n [A]mend address? or [A]ny other key to continue\n")

            if ui.isalpha():
                if ui[0].lower() == "a":
                    self.amend_address(address=address)

            else:
                return address

    def amend_address(self, address=None):
        """
        takes an address or gets from Shipment
        lists variables in address and edits as per user input
        updates Shipment.address
        :param address:
        :return: address and update Shipment.address
        """
        if debug:
            print("func = amend_address\n")

        if address is None:
            address = self.address

        address_vars = self.CNFG.db_address_fields  # get a list of vars considered 'address' from cnfg

        print(f"current address: \n")
        while True:
            # print each attribute of the address object with a 1-indexed identifier
            for c, var in enumerate(address_vars, start=1):
                print(f"{c} - {var} = {getattr(address, var)}")

            # get user selection
            ui = input("\n Enter a number to edit the field, a letter to go back\n")

            if ui.isalpha():
                return address

            if not ui.isnumeric():
                continue

            ui = int(ui)
            uii = ui - 1

            if not uii <= len(address_vars):
                print("wrong number")
                continue

            var_to_edit = address_vars[uii]
            new_var = input(f"{var_to_edit} is currently {getattr(address, var_to_edit)} - enter new value \n")

            while True:
                cont = input(f"[C]hange {var_to_edit} to {new_var}? (anything else to go back)")
                if cont and cont.isalpha():
                    cont1 = cont[0].lower()
                    if cont1 == 'c':
                        setattr(address, var_to_edit, new_var)
                        self.address = address
                        break


                else:
                    break

    def check_address(self):
        """
        displays Shipment.address
        takes user input to confirm, change, or amend
        :return: True and updates Shipment.address
        """
        if debug:
            print("func = check_address \n")

        while self.address:
            postcode = self.address.postal_code
            addy2 = {k: v for k, v in vars(self.address).items() if k in self.CNFG.db_address_fields}
            print("Current address details:\n")
            print(
                f'{chr(10).join(f"{k}: {v}" for k, v in addy2.items())}')  # chr(10) is newline (no \ allowed in fstrings)

            ui = input(
                f"\n[G]et new address or [A]mend current address, anything else to continue\n\n")

            if ui.isalpha():
                uii = ui[0].lower()
                if uii == 'g':
                    self.address = self.address_from_postcode(postcode)
                    return True

                elif uii == 'a':
                    self.address = self.amend_address()
                    return True

            else:
                return True

        print("NO ADDRESS OBJECT - go get one")
        self.address_from_postcode()

    def make_request(self):
        print("MAKING REQUEST")
        client = self.CNFG.client
        self.recipient_address = client.address(
            company_name=self.customer,
            country_code="GB",
            county=self.address.county,
            locality=self.address.locality,
            postal_code=self.address.postal_code,
            town_city=self.address.town_city,
            street=self.address.street
        )

        self.recipient = client.recipient(
            name=self.deliveryContact,
            telephone=self.deliveryTel,
            email=self.deliveryEmail,
            recipient_address=self.recipient_address

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

        self.shipmentRequest = client.shipment_request(
            parcels=self.parcels,
            client_reference=self.reference_on_label,
            collection_date=self.dateObject.date,
            sender_address=self.sender,
            recipient_address=self.recipient,
            follow_shipment='true',
            service_id=self.CNFG.service_id  # debug i added this manually?
        )
        self.shipmentRequest.collection_date = self.dateObject.date  #
        self.services = client.get_available_services(self.shipmentRequest)
        if self.services[0].service_id != self.CNFG.service_id:
            print("Something is wrong with the shipping service name")
        self.shippingServiceName = self.services[0].name
        self.shippingCost = self.services[0].cost

    def queue_or_book(self):
        """
        gets user input and returns a response code to caller

        :return: Response code for process_shipment
        """
        if debug:
            print("func = Queue or book\n")

        while True:
            self.print_shipment_to_screen()
            choice = input('- [Q]ueue shipment in DespatchBay, [B]ook + print [R]estart, or [E]xit\n')

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

                else:
                    print(f"{choice} is not a valid input")
            else:
                print("No input")
            continue

    def book_collection(self):
        if debug: print("func = BOOK_COLLECTION \n")
        client = self.CNFG.client

        shipment_return = client.book_shipments(self.desp_shipment_id)[0]  # debug there could be more than one here!

        label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
        try:
            label_string = f"{self.customer} - {str(self.dateObject.date)}.pdf"
        except:
            label_string = f"{self.customer}.pdf"
        label_pdf.download(self.CNFG.label_dir / label_string)
        self.trackingNumbers = []
        for parcel in shipment_return.parcels:
            self.trackingNumbers.append(parcel.tracking_number)

        # self.shipmentReturn = shipment_return #debug why save this?
        self.shipmentDocId = shipment_return.shipment_document_id
        self.labelUrl = shipment_return.labels_url
        # self.parcels = shipment_return.parcels #debug why save?
        self.labelLocation = str(self.CNFG.label_dir / label_string)
        # self.print_label() #debug printing as a seperate method call in process shipment script
        self.collectionBooked = True
        self.labelDownloaded = True
        nl = "\n"  # python voodoo to newline in fstring
        print(
            f"\n Collection has been booked for {self.customer} on {self.dateObject.date} \n Label downloaded to {self.labelLocation}. {f'{nl}label printed' if self.printed else None}\n")
        return True

    def print_label(self):
        os.startfile(self.labelLocation, "print")
        self.printed = True

    def print_shipment_to_screen(self):
        print(
            f"\n {line} \n {self.customer} | {self.boxes} | {self.address.street} | {self.dateObject.date} | {self.shippingServiceName} | Price = {self.shippingCost * self.boxes} \n {line} \n")


class ShipDictObject:
    def __init__(self, ship_dict):
        for k, v in ship_dict.items():
            setattr(self, k, v)


""" 
fake shipment to get service codes
        # fake_ship = [
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
            sender_address=CNFG.sender,
            recipient_address=recip)"""
