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

from AmDesp_python.despatchbay.despatchbay_sdk import DespatchBaySDK
from AmDesp_python.utils_pss.utils_pss import toCamel, unsanitise

# FIELD_CONFIG = 'FIELD_CONFIG'
line = '-' * 100
debug = False


class Config:
    def __init__(self, ship_mode, xmlfileloc=None):

        # fieldnames
        # hirename
        self.export_fields = ['customer', 'shipmentName', 'deliveryName', 'deliveryContact', 'deliveryTel',
                              'deliveryEmail',
                              'deliveryAddress', 'deliveryPostcode', 'sendOutDate', 'referenceNumber',
                              'trackingNumbers', 'desp_shipment_id', 'boxes', 'collectionBooked', 'shipRef',
                              'category']
        self.shipment_fields = ['deliveryName', 'deliveryContact', 'deliveryTel', 'deliveryEmail',
                                'deliveryAddress', 'deliveryPostcode', 'sendOutDate', 'referenceNumber',
                                'category', 'shipmentName']
        self.db_address_fields = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']

        # paths
        self.root = pathlib.Path.cwd()
        print (self.root)
        self.data_dir = self.root / "data"
        self.label_dir = self.data_dir / "Parcelforce Labels"
        self.Json_File = self.data_dir / "AmShip.json"
        if xmlfileloc:
            self.xml_file = self.data_dir / xmlfileloc
            print(f"{self.xml_file=}")

        else:
            self.xml_file = self.data_dir / "AmShipSale.xml"
            print(f"{self.xml_file=}")

        self.log_file = self.data_dir / "AmLog.json"

        # make the labels dirs (and parents)
        self.label_dir.mkdir(parents=True, exist_ok=True)
        self.log_to_commence_powershell_script = self.root.joinpath("scripts", "log_tracking_to_Commence.ps1")
        self.cmc_lib_net_dll = pathlib.Path("Program Files/Vovin/Vovin.CmcLibNet/Vovin.CmcLibNet.dll")
        self.cmcLibNet_installer = self.root.joinpath("dist", "CmcLibNet_Setup.exe")
        if not self.cmc_lib_net_dll.exists():
            print(
                "ERROR: Vovin CmCLibNet is not installed in expected location 'Program Files/Vovin/Vovin.CmcLibNet/Vovin.CmcLibNet.dll'")
            if self.cmcLibNet_installer.exists():
                print("Launching CmcLibNet installer")
                if os.startfile(self.cmcLibNet_installer):
                    print("CmcLib Installed")
                else:
                    print("ERROR: CmcLibNet Installer Failed - logging to commence is impossible")
            else:
                print(
                    "\n ERROR: CmcLinNet installer missing from '/dist' \nPlease download Installer from https://github.com/arnovb-github/CmcLibNet/releases and install to default program files location"
                    "\n Logging to Commence is impossible")

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
        self.client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        self.sender = self.client.sender(address_id=self.sender_id)

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


class ShippingApp:
    def __init__(self, ship_mode, xmlfileloc=None):  # creat app-obj
        self.CNFG = Config(ship_mode, xmlfileloc=xmlfileloc)  # creat app.config-obj
        self.shipment = None

    def run(self):
        self.prepare_shipment()
        self.process_shipment()

    def prepare_shipment(self):
        ship_dict = self.xml_to_ship_dict()  # creates ship_dict from xmlfile
        self.shipment = Shipment(ship_dict, self.CNFG)  # creates shipment-obj from ship_dict, passes config object
        self.shipment.boxes = self.shipment.val_boxes()  # checks if there are boxes on the shipment, prompts input and confirmation
        self.shipment.val_dates()  # checks collection is available on the sending date, prompts confirmation
        self.shipment.address = self.shipment.address_script()

    def process_shipment(self, service=None):
        self.shipment.make_request(service)  # make a shipment request
        decision = self.shipment.queue_or_book()

        if decision == "QUEUE":
            self.shipment.desp_shipment_id = self.CNFG.client.add_shipment(self.shipment.shipmentRequest)
            self.log_json()

        elif decision == "BOOKANDPRINT":
            self.shipment.desp_shipment_id = self.CNFG.client.add_shipment(self.shipment.shipmentRequest)
            # self.CNFG.client.add_shipment(self.shipment.shipmentRequest)
            # debug issues here
            self.shipment.book_collection()
            self.shipment.print_label()
            self.log_json()
            self.log_tracking()
            exit()

        elif decision == "RESTART":
            self.run()

        elif decision == "EXIT":
            exit()

        elif decision == "SERVICE_CHANGE":
            services = self.shipment.services
            print(f"Available services:\n")
            for n, service in enumerate(self.shipment.services, 1):
                print(f"Service ID {n} : {service.name}")

            while True:
                choice = input("\nEnter a Service ID\n")
                if choice.isnumeric() and 0 < int(choice) <= len(services):
                    new_service = services[int(choice) - 1]
                    print(f"{new_service.service_id=}, {new_service.name=}")
                    # self.shipment.CNFG.service_id = new_service.service_id
                    # self.shipment.shippingServiceName = new_service.name
                    self.process_shipment(new_service)
                else:
                    print("Bad input")
                continue

        else:
            print(f"ERROR: \n {decision=}")

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
        # export from object attrs

        export_dict = {}
        for field in self.CNFG.export_fields:
            if field in vars(self.shipment):
                val = getattr(self.shipment, field)
                val = f"{val:%d-%m-%Y}" if isinstance(val, datetime) else val
                export_dict.update({field: val})
            else:
                print(f"{field} not found in shipment")
        export_dict.update({"timestamp": datetime.now().isoformat(' ', timespec='seconds')})
        with open(self.CNFG.log_file, 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",\n")
            pprint(f"\n Json exported to {self.CNFG.log_file} {export_dict =}")

        # if self.shipment.trackingNumbers:
        # # if self.shipment.category in ['Hire', 'Sale']:
        #     self.log_tracking()  # writes to commence db

    def log_tracking(self):
        """
        runs cmclibnet via powershell script to add tracking numbes to commence db

        :return:
        """
        log_tracking_powershell_script = self.CNFG.log_to_commence_powershell_script
        cmcLibpath = self.CNFG.cmc_lib_net_dll
        tracking_nums = ', '.join(self.shipment.trackingNumbers)

        try:
            subprocess.run([
                "powershell.exe",
                # "-executionpolicy bypass",
                "-File",
                log_tracking_powershell_script,
                self.shipment.shipmentName,
                tracking_nums,
                self.shipment.category
            ],
                stdout=sys.stdout)
        except:
            print("\nERROR: Unable to log tracking to Commence")
            if not os.path.exists(log_tracking_powershell_script):
                print("  -   Powershell script missing")
            if not os.path.exists(cmcLibpath):
                print("  -   Vovin CmCLibNet missing")


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
            if debug:
                print(f"{self.shipmentName=}")
            # hirename

        except KeyError:
            print("Key error - something missing from shipdict")

        ## optional shipment details
        try:
            self.referenceNumber = self.shipmentName
        except:
            self.referenceNumber = "NOREF"
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
            if self.boxes == 0:
                self.boxes = 1
            ui = input(
                f"\n {self.boxes}  box(es) assigned for {self.customer} \n \n Enter a number to adjust, anything else to continue\n")
            if ui.isnumeric():
                print(f"Shipment updated to {ui} boxes")
                self.boxes = int(ui)
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
        available_dates = self.CNFG.client.get_available_collection_dates(self.sender,
                                                                          self.CNFG.courier_id)  # get dates
        print(f"--- Checking available collection dates...")
        send_date = datetime.strftime(self.sendOutDate, '%Y-%m-%d')

        for despdate in available_dates:
            compdate = str(despdate.date)
            if compdate == send_date:  # if date object matches send date
                self.dateObject = despdate
                da = datetime.strftime(self.sendOutDate, '%A %B %#d')
                print(f"Collection date match - shipment for {self.customer} will be collected on {da}\n", line)
                return
        else:  # loop exhausted, no date match
            print(
                f"\n*** ERROR: No collections available on {self.sendOutDate:%A - %B %#d} ***\n\n\n- Collections for {self.customer} are available on:\n")
            for count, date in enumerate(available_dates):
                dt = parse(date.date)
                out = datetime.strftime(dt, '%A - %B %#d')
                print("\t\t", count + 1, "|", out)

            while True:
                choice = input(
                    f'\n- [Enter] to select {datetime.strftime(parse(available_dates[0].date), "%A - %B %#d")}, [A Number] to choose a date, [0] to exit\n')
                if not choice:
                    choice = str(1)
                if not choice.isnumeric():
                    print("- Enter a number")
                    continue
                if not -1 <= int(choice) <= len(available_dates) + 1:
                    print('\nWrong Number!\n-Choose new date for', self.customer, '\n')
                    for count, date in enumerate(available_dates):
                        print("\t\t", count + 1, "|", date.date, )
                    continue
                if int(choice) == 0:
                    if input('[E]xit?')[0].lower() == "e":
                        exit()
                    continue
                else:
                    self.dateObject = available_dates[int(choice) - 1]
                    print("\t\tCollection date for", self.customer, "is now ", self.dateObject.date, "\n\n",
                          line)
                    return

    def address_script(self, address=None):
        """

        :return: address:
        """
        if address is None:
            if address_from_search := self.address_from_postcode_and_string(
                    postcode=self.deliveryPostcode):  # walrus assigns and checks
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

    def address_from_postcode_and_string(self, postcode: str = None, prompt_search: bool = False):
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
            postcode = input("Enter Postcode")

        if prompt_search:
            search_string = input("Enter Search String")
        else:
            if self.deliveryBuildingNum:
                search_string = self.deliveryBuildingNum
            else:
                search_string = self.deliveryFirstline
                print(f"No building number, searching by first line of address: {self.deliveryFirstline} \n")
                if search_string is None:
                    search_string = input("Enter Search String")

        try:
            print(f"Searching: {postcode=}, {search_string=}")
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
                cont = input(f"[C]hange {var_to_edit} to {new_var}? (anything else to go back)")
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
        if debug:
            print("func = check_address \n")
        if address is None:
            address = self.address
        while address:
            postcode = address.postal_code

            # print address fields of shipment-obj to the screen
            filtered_address_fields = {k: v for k, v in vars(address).items() if k in self.CNFG.db_address_fields}
            print("Current address details:\n")
            print(
                f'{chr(10).join(f"{k}: {v}" for k, v in filtered_address_fields.items())}')  # chr(10) is newline (no \ allowed in fstrings)

            # offer to replace None company name with customer name
            if address.company_name is None:
                ui = input(f"\n \n Replace 'None' Company Name with {self.customer}? [Y / N]\n")
                if not ui or str(ui[0]).lower() == 'y':
                    address.company_name = self.customer
                    print("Company Name updated")
                else:
                    print("Keep company 'None'")
            self.address = address
            return address

    def make_request(self, service=None):
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

        # self.shipmentRequest = client.shipment_request(
        self.shipmentRequest = client.shipment_request(
            parcels=self.parcels,
            client_reference=self.reference_on_label,
            collection_date=self.dateObject.date,
            sender_address=self.sender,
            recipient_address=self.recipient,
            follow_shipment='true',
            service_id=self.CNFG.service_id
        )
        self.shipmentRequest.collection_date = self.dateObject.date  #
        self.services = client.get_available_services(self.shipmentRequest)
        if self.services[0].service_id != self.CNFG.service_id:
            print("Shipping service is not default")
        if service:
            self.shippingCost = service.cost
            self.shippingServiceName = service.name
        else:
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
        nl = "\n"  # AmDesp_python voodoo to newline in fstring
        print(
            f"\n Collection has been booked for {self.customer} on {self.dateObject.date} \n Label downloaded to {self.labelLocation}. {f'{nl}label printed' if self.printed else None}\n")
        return True

    def print_label(self):
        try:
            os.startfile(self.labelLocation, "print")
        except OSError:
            print("\nERROR: Unable to print\n  -   no default PDF application selected in Windows")
        self.printed = True

    def print_shipment_to_screen(self):
        print(
            f"\n {line} \n {self.customer} | {self.boxes} | {self.address.street} | {self.dateObject.date} | {self.shippingServiceName} | Price = {self.shippingCost * self.boxes} \n {line} \n")


#
# class ShipDictObject:
#     def __init__(self, ship_dict):
#         for k, v in ship_dict.items():
#             setattr(self, k, v)
#

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
