import json
import os
import pathlib
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pprint import pprint

from dateutil.parser import parse

from python.despatchbay.despatchbay_sdk import DespatchBaySDK
from python.utils_pss.utils_pss import toCamel, get_from_ods

CONFIG_ODS = r"C:\AmDesp\data\AmDespConfig.ods"
FIELD_CONFIG = 'FIELD_CONFIG'
line = '-' * 100
debug = True


class Config:
    def __init__(self, ship_mode):
        self.config_ods = CONFIG_ODS

        class DespatchConfig:
            def __init__(self):
                if ship_mode == "sand":
                    print("\n \n \n *** !!! SANDBOX MODE !!! *** \n \n \n")
                    self.api_user = os.getenv("DESPATCH_API_USER_SANDBOX")
                    self.api_key = os.getenv("DESPATCH_API_KEY_SANDBOX")
                    self.courier_id = 99
                    # self.service_id = 9992
                    self.shipping_service_id = 9992
                elif ship_mode == 'prod':
                    self.api_user = os.getenv("DESPATCH_API_USER")
                    self.api_key = os.getenv("DESPATCH_API_KEY")
                    self.courier_id = 8
                    self.shipping_service_id = 101
                else:
                    print("SHIPMODE FAULT - EXIT")
                    exit()

                self.sender_id = "5536"  # should be env var?
                self.client = DespatchBaySDK(api_user=self.api_user, api_key=self.api_key)
                self.sender = self.client.sender(address_id=self.sender_id)
                # self.courier_id = 8
                # self.shipping_service_id = 101  ## parcelforce 24 - maybe make dynamic?
                self.address_vars = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']

        class FieldsCnfg:
            def __init__(self, ods):
                self.export_fields = None
                field_config_dict = get_from_ods(ods, FIELD_CONFIG, 'list')
                for k, v in field_config_dict.items():
                    setattr(self, k, v)

        class PathsConfig:
            def __init__(self):
                self.root = pathlib.Path("/Amdesp")
                self.data_dir = pathlib.Path("/Amdesp/data/")
                self.label_dir = self.data_dir / "Parcelforce Labels"
                self.Json_File = self.data_dir.joinpath("AmShip.json")
                self.xml_file = self.data_dir.joinpath('AmShip.xml')
                self.log_file = self.data_dir.joinpath("AmLog.json")
                self.config_file = self.data_dir.joinpath("AmDespConfig.Ods")
                self.bin_dir = pathlib.Path("/Amdesp/bin/")
                self.pdf_to_print = self.root.joinpath("PDFtoPrinter.exe")
                pathlib.Path(self.data_dir / "Parcelforce Labels").mkdir(parents=True,
                                                                         exist_ok=True)  # make the labels dirs (and parents)

        self.fields = FieldsCnfg(CONFIG_ODS)
        self.paths = PathsConfig()
        self.dbay_cnfg = DespatchConfig()


# CNFG = Config()


class ShippingApp:
    def __init__(self, ship_mode):  # make app
        CNFG = Config(ship_mode)
        self.shipment = None
        self.client = CNFG.dbay_cnfg.client
        self.sender = CNFG.dbay_cnfg.sender
        self.CNFG = CNFG

    def xml_to_shipment(self):
        ship_dict = self.xml_to_ship_dict()
        parsed = ShipDictObject(ship_dict)
        self.shipment = Shipment(parsed, self.CNFG, parent=self)

    def queue_shipment(self):
        self.boxes = self.shipment.val_boxes()  # checks if there are boxes on the shipment, prompts input and confirmation
        self.shipment.val_dates()  # checks collection is available on the sending date
        self.shipment.addressObject = self.shipment.val_address()  # queries DB address database
        self.shipment.check_address()  # queries DB address database, prompts user to confirm match or call amend_address()
        self.shipment.make_request()  # make a shipment request
        if self.shipment.queue():
            return True
        else:
            print(f"Shipment aborted")

    def xml_to_ship_dict(self):
        if debug: print("XML IMPORTER ACTIVATED")
        ship_dict = {}
        tree = ET.parse(self.CNFG.paths.xml_file)
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
        if category == "Hire":
            print("Xml is a hire record")
            customer = root[0][3].text  # debug
            ship_dict['id'] = ship_dict['Reference Number']

        elif category == "Customer":
            print("Xml is a customer record")
            customer = fields[0][1].text
            ship_dict['send Out Date'] = datetime.today().strftime(
                '%d/%m/%Y')  # datedebug sets customer shipment send date to a string of today formatted like hire
            ship_dict['delivery tel'] = ship_dict['Deliv Telephone']

        else:
            print("no customer found")
            print("ERROR NO CUSTOMER")
        ship_dict.update({'customer': customer})
        ship_dict = self.clean_xml(ship_dict)
        if 'boxes' not in ship_dict.keys():
            ship_dict['boxes'] = 0
        for k, v in ship_dict.items():
            if k == "sendOutDate":
                v = datetime.strptime(v, '%d/%m/%Y')  # datedebug
        print(f"Making shipment object from xml with {len(ship_dict)} fields")
        return ship_dict

    def clean_xml(self, dict) -> dict:
        if debug: print('\n CLEAN XML\n')
        newdict = {}
        if "Send Out Date" not in dict.keys():
            print("No date - added today")
            dict['Send Out Date'] = datetime.today().strftime('%d/%m/%Y')
        for k, v in dict.items():
            # k = unsanitise(k)
            k = toCamel(k)
            if "deliv" in k:
                if "delivery" not in k:
                    k = k.replace('deliv', 'delivery')

            if v:
                # v = unsanitise(v)
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
                # if "Number" in k: # elsewhere?
                #     v = v.replace(",", "")
                # if k == "sendOutDate":
                # v = datetime.strftime(v, '%Y-%m-%d')   #debug wtf?
                # # v = datetime.strptime(v, '%Y%m-%d').date()
                # v = datetime.strptime(v, '%d/%m/%Y').date()

            newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        return newdict

    def book_collection(self):
        self.shipment.book_collection()

    def log_json(self):
        # export from object attrs?
        if "referenceNumber" not in vars(self.shipment):
            self.shipment.referenceNumber = self.shipment.id

        export_dict = {}
        for field in self.CNFG.fields.export_fields:
            val = getattr(self.shipment, field)
            val = f"{val:%d-%m-%Y}" if isinstance(val, datetime) else val
            export_dict.update({field: val})

        with open(self.CNFG.paths.log_file, 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",")
            pprint(f"\n Json exported to {self.CNFG.paths.log_file} {export_dict =}")

            # val = f"{val:%d-%m-%Y} if isinstance(val, datetime) else val}"
            # if isinstance(val, datetime):
            #     val = f"{val:%d-%m-%Y}"

        # export_dict = {field : f"{val:%d-%m-%Y}" if isinstance(val, datetime) else val for val = getattr(self.shipment, field) for field in self.CNFG.fields.export_fields}

        # if isinstance(export_dict, datetime):
        #     export_dict["sendOutDate"]=export_dict["sendOutDate"].strftime('%d/%m/%Y')
        # self.sendOutDate = self.sendOutDate.strftime('%d/%m/%Y')


class Shipment:  # taking an xmlimporter object
    def __init__(self, parsed_xml_object, CNFG, shipid=None,
                 shipref=None,
                 parent=None):  # shipdict is a hire object, could be a customer object, or repair i guess...

        if parent:
            self.parent = parent
        self.printed = False
        self.CNFG = CNFG
        self.sender = CNFG.dbay_cnfg.sender
        self.client = CNFG.dbay_cnfg.client
        self.collectionBooked = False
        self.dbAddressKey = 0

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
            sender_address=CNFG.dbay_cnfg.sender,
            recipient_address=recip)

        services = self.client.get_available_services(shippy)

        self.dates = self.client.get_available_collection_dates(CNFG.dbay_cnfg.sender,
                                                                CNFG.dbay_cnfg.courier_id)  # get dates

        for field in CNFG.fields.shipment_fields:

            if field in vars(parsed_xml_object):
                v = getattr(parsed_xml_object, field)
                setattr(self, field, v)
            else:
                print(f"*** ERROR - {field} not found in ship_dict - ERROR ***")

        ## provided shipment details
        if shipid:
            self.id = shipid
        elif 'referenceNumber' in vars(parsed_xml_object):
            self.id = parsed_xml_object.referenceNumber
        else:
            self.id = "101"
        self.customer = parsed_xml_object.customer
        self.deliveryEmail = parsed_xml_object.deliveryEmail
        self.deliveryName = parsed_xml_object.deliveryName
        self.deliveryTel = parsed_xml_object.deliveryTel
        self.deliveryContact = parsed_xml_object.deliveryContact
        self.deliveryAddress = parsed_xml_object.deliveryAddress
        self.deliveryPostcode = parsed_xml_object.deliveryPostcode
        self.sendOutDate = parsed_xml_object.sendOutDate
        self.boxes = parsed_xml_object.boxes
        if shipref:
            self.shipRef = shipref  ## if there is a shipref passed use it as despatchbay reference on label etc
        else:
            self.shipRef = self.customer

        ## obtained shipment details
        self.deliveryBuildingNum = None
        self.deliveryFirstline = None
        self.shippingCost = None
        self.trackingNumbers = None
        self.labeLocation = None
        self.labelDownloaded = False
        self.labelLocation = None
        self.labelUrl = None
        self.parcels = None
        self.shipmentDocId = None
        self.shippingServiceName = None

        # DespatchBay Objects

        self.addedShipment = None
        self.addressObject = None
        self.dateObject = None
        self.shipmentRequest = None
        self.shipmentReturn = None
        self.recipient = None

        print("Shipment with id=", self.id, "created")

        def parse_address():
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
            if debug: print("func = VAL DATES")
            # dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
            if isinstance(self.sendOutDate, str):
                setattr(self, "sendOutDate", datetime.strptime(self.sendOutDate, '%d/%m/%Y'))
            for candidate in self.dates:
                if candidate.date == datetime.strftime(self.sendOutDate,
                                                       '%Y-%m-%d'):  # if date object matches send date
                    self.dateObject = candidate
                    print(line, '\n',
                          f"Shipment date for {self.customer} validated - {datetime.strftime(self.sendOutDate, '%A %B %#d')}")

        parse_address()
        val_date_init(self)

    def val_boxes(self):
        if debug: print("func = VAL_BOXES")
        if self.boxes:
            while True:
                print(line, "\n",
                      f"\nShipment for {self.customer} has {self.boxes} box(es) assigned - is this correct?\n")
                ui = input(f"[C]onfirm {self.boxes} boxes in shipment or Enter a number of boxes\n")
                if ui.isnumeric():
                    print(f"Shipment updated  |  {self.boxes}  boxes\n")
                    return int(ui)
                    # return self
                if ui.lower == 'c':
                    print("Confirmed\n", line)
                    return self.boxes
                continue
        else:
            while True:
                print("\n\t\t*** ERROR: No boxes added ***\n")
                ui = input(f"- How many boxes for shipment to {self.customer}?\n")
                if not ui.isnumeric():
                    print("- Enter a number")
                    continue
                print(f"{self.customer} updated  |  ", self.boxes, "  boxes")
                return int(ui)
                # return self

    def val_dates(self):
        if debug: print("func = VAL_DATES")
        dates = self.client.get_available_collection_dates(self.CNFG.dbay_cnfg.sender,
                                                           self.CNFG.dbay_cnfg.courier_id)  # get dates
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

    def val_address(self):
        if debug: print("func = val_address\n")
        if self.deliveryBuildingNum:
            if self.deliveryBuildingNum != 0:
                search_string = self.deliveryBuildingNum
            else:
                print("No building number, searching by first line of address \n")
                self.deliveryBuildingNum = False
                search_string = self.deliveryFirstline
        else:
            print("No building number - searching by first line of address \n")
            search_string = self.deliveryFirstline
        # get object
        try:
            address_object = self.client.find_address(self.deliveryPostcode, search_string)
        except:
            print("No address match found")
            address_object = self.change_address()
            return address_object
        else:
            return address_object

    def check_address(self):
        if debug: print("func = check_address \n")
        while True:
            if self.addressObject:
                postcode = self.addressObject.postal_code
                addy2 = {k: v for k, v in vars(self.addressObject).items() if k in self.CNFG.dbay_cnfg.address_vars}
                print("Current address details:\n")
                print(
                    f'{chr(10).join(f"{k}: {v}" for k, v in addy2.items())}')  # chr(10) is newline (no \ allowed in fstrings)

                ui = input(
                    f"\n[C]ontinue, [G]et new address or [A]mmend address \n\n")
                if not ui:
                    continue
                uii = ui[0].lower()
                if uii == "c":
                    return
                elif uii == 'g':
                    self.addressObject = self.change_address(postcode)
                elif uii == 'a':
                    self.addressObject = self.amend_address()
            else:
                print("NO ADDRESS OBJECT")
                self.change_address()

    def change_address(self, postcode=None):
        if debug: print("func = change_address \n")
        if postcode == None:
            postcode = self.deliveryPostcode
        candidates = self.client.get_address_keys_by_postcode(postcode)

        for count, candidate in enumerate(candidates, start=1):
            print(" - Candidate", str(count) + ":", candidate.address)
        while True:
            selection = input('\n- Enter a candidate number, [0] to exit, [N] to search a new postcode \n')
            if not selection: continue
            if selection.isnumeric():
                selection = int(selection)
            else:
                if selection[0].lower() == "n":
                    address = self.search_address()
                    return address
                continue
            if selection == 0:
                ui = input("[e]xit?")
                if not ui: continue
                if input("[e]xit?")[0].lower() == "e":
                    return False
                    # exit()
                continue
            if not 0 <= selection <= len(candidates):
                print("Wrong Number")
                continue
            break
        selected_key = candidates[int(selection) - 1].key
        addressObject = self.client.get_address_by_key(selected_key)
        print(f"- New Address: Company:{addressObject.company_name}, Street address:{addressObject.street}")
        while True:
            ui = input("[A]mmend address, or [C]ontinue?\n")
            if not ui: continue
            uii = ui[0].lower()
            if uii == "a":
                addressObject = self.amend_address(addressObject)
                return addressObject
            if uii == 'c':
                return addressObject
            else:
                continue

    def search_address(self):
        if debug: print("func = search_address \n")
        while True:
            pc = input("Enter postcode or go [B]ack\n")
            if pc.isalpha() and len(pc) == 1 and pc[0].lower() == 'b':  # go back
                return None
            try:
                address = self.change_address(pc)
            except:
                print("Bad Postcode")
                continue
            if address:
                return address
            else:
                print("bad postcode 2")
                continue

        # try:
        #     address = self.client.find_address(pc, s_string)
        # except:
        #     print("No results - try again\n")
        #     self.search_address()
        # else:
        #     ui = ""
        #     while ui not in ['y', 'n']:
        #         ui = input(f"Is {address} correct? [Y]es or [N]o, or [E]xit\n")
        #         if ui[0].lower() == 'y':
        #             self.addressObject = address
        #             return
        #         elif ui[0].lower() == 'n':
        #             self.search_address()
        #         elif ui[0].lower() == "e":
        #             if input("really [E]xit?") == 'e':
        #                 exit()
        #             self.search_address()

    def amend_address(self, address=None):
        if debug: print("func = amend_address\n")
        if address == None:
            address = self.addressObject
        print(f"current address = {address.street} \n")
        address_vars = self.CNFG.dbay_cnfg.address_vars
        while True:
            # print("\n")
            for c, var in enumerate(address_vars, start=1):
                print(f"{c} - {var} = {getattr(address, var)}")
            ui = input("\n Enter a number to edit the field, [0] to go back\n")
            if not ui.isnumeric():
                print("That isn't a number")
                continue
            uii = int(ui) - 1
            if int(ui) == 0:
                return address

            if not uii <= len(address_vars):
                print("wrong number")
                continue
            var_to_edit = address_vars[uii]
            new_var = input(f"{var_to_edit} is currently {getattr(address, var_to_edit)} - enter new value \n")
            while True:
                cont = input(f"[C]hange {var_to_edit} to {new_var} or [G]o back?")
                if not cont.isalpha():
                    print("That's not a letter")
                    continue
                conti = cont[0].lower()
                if conti == 'g':
                    break
                if conti == 'c':
                    setattr(address, var_to_edit, new_var)
                    while True:
                        ui = input("[C]hange another, anything else to move on?")
                        uii = ui[0].lower()
                        if uii == 'c':
                            self.amend_address(address)
                        else:
                            return address
            ...
        # for var in vars(address):
        #     print (var)
        ...

    def make_request(self):
        print("MAKING REQUEST")
        self.recipient_address = self.client.address(
            company_name=self.customer,
            country_code="GB",
            county=self.addressObject.county,
            locality=self.addressObject.locality,
            postal_code=self.addressObject.postal_code,
            town_city=self.addressObject.town_city,
            street=self.addressObject.street
        )

        self.recipient = self.client.recipient(
            name=self.deliveryContact,
            telephone=self.deliveryTel,
            email=self.deliveryEmail,
            recipient_address=self.recipient_address

        )
        self.parcels = []
        for x in range(self.boxes):
            parcel = self.client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            self.parcels.append(parcel)

        self.shipmentRequest = self.client.shipment_request(
            parcels=self.parcels,
            client_reference=self.shipRef,
            collection_date=self.dateObject.date,
            sender_address=self.sender,
            recipient_address=self.recipient,
            follow_shipment='true',
            service_id=self.CNFG.dbay_cnfg.shipping_service_id  # debug i added this manually?
        )
        self.shipmentRequest.collection_date = self.dateObject.date  #
        self.services = self.client.get_available_services(self.shipmentRequest)
        if self.services[0].service_id != self.CNFG.dbay_cnfg.shipping_service_id:
            print("Something is wrong with the shipping service name")
        self.shippingServiceName = self.services[0].name
        self.shippingCost = self.services[0].cost
        self.shipping_service_id = self.shipmentRequest.service_id
        self.services = self.services

    def queue(self):
        if debug: print("func = Queue\n")
        print("\n", line, '\n-', self.customer, "|", self.boxes, "|",
              self.addressObject.street, "|", self.dateObject.date, "|",
              self.shippingServiceName,
              "| Price =",
              self.shippingCost * self.boxes, '\n', line, '\n')
        choice = " "
        while True:
            choice = input('- [Q]ueue shipment in DespatchBay, [R]estart, or [E]xit\n')
            if choice:
                choice = str(choice[0].lower())
                if choice[0] != "q":  # not quote
                    if choice != 'r':  # not restart
                        if choice != 'e':  # not exit either
                            continue  # try again
                        else:  # exit
                            if str(input("[E]xit?"))[0].lower() == 'e':  # comfirn exit
                                break
                                # exit()
                            continue
                    else:  # restart
                        ui = input("[R]estart?")
                        if not ui: continue
                        if ui[0].lower() == 'r':  # confirm restart
                            print("Restarting")
                            self.parent.queue_shipment()

                        continue  # not restarting
                elif choice == 'q':
                    self.addedShipment = self.client.add_shipment(self.shipmentRequest)
                    print("Adding Shipment to Despatchbay Queue")
                    return True
            else:
                continue

    def print_label(self):
        if debug: print("func = PRINT_LABEL\n")
        while True:
            ui = input("[P]rint label or [E]xit?\n")
            if not ui:
                continue
            uii = ui[0].lower()
            if uii == 'p':
                command = (self.CNFG.paths.pdf_to_print, self.labelLocation)
                subprocess.call(command, shell=True)
                self.printed = True
                while True:
                    ui = input("[P]rint again, or [E]xit")
                    uii = ui[0].lower()
                    if uii == 'p':
                        self.print_label()
                    elif uii == 'e':
                        return self.printed
            elif uii == 'e':
                return self.printed

    def book_collection(self):
        if debug: print("func = BOOK_COLLECTION \n")
        # CNFG = config
        print("[B]ook collection for", self.customer + "'s shipment?")
        while True:
            choice = input('- [B]ook, [R]estart, or [E]xit\n')
            if not choice:
                continue
            choice = str(choice[0].lower())
            if choice[0] != "b":  # not book
                if choice != 'r':  # not restart
                    if choice != 'e':  # not exit either
                        continue  # try again
                    else:  # exit
                        if str(input("[E]xit?"))[0].lower() == 'e':  # comfirn exit
                            exit()
                        continue
                else:  # restart
                    if str(input("[R]estart?"))[0].lower() == 'r':  # confirm restart
                        print("Restarting")
                        ShippingApp.queue_shipment()  # debug does it run process? or soemthing else
                    continue  # not restarting
            elif choice == 'b':
                self.client.book_shipments(self.addedShipment)
                shipment_return = self.client.get_shipment(self.addedShipment)
                label_pdf = self.client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
                label_string = ""
                try:
                    label_string = label_string + self.customer + "-" + str(self.dateObject.date) + ".pdf"
                except:
                    label_string = label_string, self.customer, ".pdf"
                # label_pdf.download(CONFIG_PATH['DIR_LABEL'] / label_string)
                label_pdf.download(self.CNFG.paths.label_dir / label_string)
                self.trackingNumbers = []
                for parcel in shipment_return.parcels:
                    self.trackingNumbers.append(parcel.tracking_number)

                self.shipmentReturn = shipment_return
                self.shipmentDocId = shipment_return.shipment_document_id
                self.labelUrl = shipment_return.labels_url
                self.parcels = shipment_return.parcels
                self.labelLocation = str(self.CNFG.paths.label_dir / label_string)
                self.print_label()
                self.collectionBooked = True
                self.labelDownloaded = True
                nl = "\n"
                print(
                    f"\n Collection has been booked for {self.customer} on {self.dateObject.date} \n Label downloaded to {self.labelLocation}. {f'{nl}label printed' if self.printed else None}\n")
                return True


class ShipDictObject:
    def __init__(self, ship_dict):
        for k, v in ship_dict.items():
            setattr(self, k, v)
