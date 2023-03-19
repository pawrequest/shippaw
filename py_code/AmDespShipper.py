import PySimpleGUI as sg
import inspect
import json
import os
import pathlib
import re
import subprocess
import sys
import tomllib
from sys import exit
from datetime import datetime, date
from pprint import pprint
from dateutil.parser import parse

from py_code.despatchbay.despatchbay_sdk import DespatchBaySDK
from py_code.utils_pss.utils_pss import Utility
from py_code.amherst_importer import AmherstImport

import dotenv
from .gui import AmdespGui

dotenv.load_dotenv()

DEBUG = False

LINE = f"{'-' * 130}"
TABBER = "\t\t"
# DT_DISPLAY = '%A - %B %#d'
# DT_HIRE = '%d/%m/%Y'
# DT_DB = '%Y-%m-%d'

SANDBOX_SHIPMENT_ID = '100786-5633'
SHIPMENT_ID = '100786-20850029'


class ShippingApp:
    """
    controller for prepare_shipment and process_shipment
    """

    def __init__(self, sandbox=False):  # creat app-obj
        # create config object
        self.sandbox = sandbox
        self.CNFG = Config(sandbox=sandbox)

    def run(self, mode, xml_file):
        self.mode = mode
        shipment = Shipment(xml_file, self.CNFG)

        gui = AmdespGui(shipment)
        gui.run()

        #
        #
        # match mode:
        #     case 'ship_out':
        #         """prepare and process a shipment. queue and book collections, download and print labels"""
        #         shipment = self.prepare_shipment(shipment)
        #         self.process_shipment(shipment)
        #
        #     case 'ship_in':
        #         remote_shipment = self.prepare_shipment(shipment, is_return=True)
        #
        #         self.process_shipment(remote_shipment)
        #
        #     case "track_out":
        #         self.get_tracking(shipment.shipment_id_outbound)
        #
        #     case "track_in":
        #         self.get_tracking(shipment.shipment_id_inbound)
        #
        #

    def prepare_shipment(self, shipment, is_return=False):
        client = self.CNFG.client

        if is_return:
            shipment.is_return = True
            try:
                shipment.address = client.get_shipment(
                    shipment.shipment_id_outbound).recipient_address.recipient_address
            except AttributeError as e:
                print(f"{LINE}\n{LINE}\n*** ERROR:Bad Shipment_id can't get remote address exiting")
                # todo get renmote address from xmlfile

        shipment.parcels = shipment.boxes_script()
        shipment.date = shipment.date_script()
        shipment.address = shipment.address_script()  # checks provided address against dbay for user confirmation / amendment
        shipment.sender = shipment.get_sender(shipment.address)
        shipment.recipient = shipment.get_recip()
        return shipment

    def process_shipment(self, shipment):
        client = self.CNFG.client

        if getattr(shipment, 'service_id', None):
            service_id = shipment.service.service_id
        else:
            service_id = self.CNFG.service_id

        shipmentRequest = client.shipment_request(
            parcels=shipment.parcels,
            client_reference=shipment.label_text,
            collection_date=shipment.date.date,
            sender_address=shipment.sender,
            recipient_address=shipment.recipient,
            follow_shipment='true',
            service_id=service_id
        )
        shipment.service = self.get_service(shipmentRequest)
        shipment.print_shipment_to_screen()

        while True:
            choice = input(
                f" - [B]ook + {'email' if shipment.is_return else 'print'},  or just [Q]ueue shipment in DespatchBay"
                f"\n - [S]elect new service, [R]estart, or [E]xit\n")

            match choice:
                case "q" | "Q":
                    # add shipment to dbay queue but don't book collection. no labels or tracking are available and no charge is made
                    client.add_shipment(shipmentRequest)
                    shipment.log_json()  # log to jsonfile
                    return

                case "b" | "B":
                    # book shipment
                    if shipment.is_return:
                        shipment.shipment_id_inbound = client.add_shipment(shipmentRequest)
                        shipment.book_collection(shipment.shipment_id_inbound)  # book collection

                        # todo email label
                    else:
                        shipment.shipment_id_outbound = client.add_shipment(shipmentRequest)  # add to dbay queue
                        shipment.book_collection(shipment.shipment_id_outbound)  # book collection
                        shipment.print_label()  # download and print pdf (requires correct windows default pdf handler eg sumatra)

                    # log shipment or collection ID to commence
                    if shipment.category == 'Customer':
                        print("Nowhere to log tracking for customer entries")
                    else:
                        shipment.log_tracking()  # get tracking data and log it to commence db
                    shipment.log_json()  # log shipment and outcome to json
                    return

                case "s" | "S":
                    # change shipping service eg for Express services (requires shipment.shipment_request)
                    shipment.service = self.get_service(shipmentRequest)
                    continue

                case "r" | "R":
                    # restart
                    self.run(self.mode, self.CNFG.backup_xml)

                case "e" | "E":
                    # exit
                    return

                case _:
                    continue

        exit()

    def get_service(self, shipment_request, default=True):
        client = self.CNFG.client
        services = client.get_available_services(shipment_request)
        if default:
            service = services[0]
            return service

        else:
            print(f"Available services:\n")
            for n, service in enumerate(services, 1):
                print(f"Service # {n} : {service.name} - £{service.cost}")

            while True:
                choice = input("\n - Enter a Service # \n")
                if choice.isnumeric() and 0 < int(choice) <= len(services):
                    new_service = services[int(choice) - 1]
                    print(f"{new_service.service_id=}, {new_service.name=}")
                    return new_service
                else:
                    print("Bad input")
                continue

    def get_tracking(self, shipment_id):
        client = self.CNFG.client
        shipment = client.get_shipment(shipment_id)
        tracking_numbers = [parcel.tracking_number for parcel in shipment.parcels]
        try:
            for parcel in tracking_numbers:
                tracking = client.get_tracking(parcel)
                for tracking_event in tracking.TrackingHistory[::-1]:
                    print(
                        f"{tracking_event.Description} in {tracking_event.Location} at {tracking_event.Time} on {tracking_event.Date}\n")
                    if tracking_event.Description == "Delivered":
                        print(f"\nSigned for by {tracking_event.Signatory}")
        except Exception as e:
            print(f"\n \n ERROR: {e}")


class Shipment(AmherstImport):
    def __init__(self, xml_file, CNFG, reference=None,
                 label_text=None, is_return=False):
        """
        :param ship_dict: a dictionary of shipment details
        :param CNFG: a config() object
        :param reference:
        :param label_text:
        """
        # attrs from importer class
        super().__init__(xml_file, CNFG)

        ## Config object from toml
        self.CNFG = CNFG

        self.service = None
        self.amherst_sender = CNFG.client.sender(
            address_id=CNFG.sender_id,
            name = CNFG.amherst_address['contact'],
            email = CNFG.amherst_address['email'],
            telephone = CNFG.amherst_address['phone'],
            sender_address = CNFG.client.get_sender_addresses()[0]
        )
        self.amherst_recipient = CNFG.client.recipient(
            name=CNFG.amherst_address['contact'],
            email=CNFG.amherst_address['email'],
            telephone = CNFG.amherst_address['phone'],
            recipient_address = CNFG.client.find_address(CNFG.amherst_address['postal_code'], CNFG.amherst_address['street'])



        )
        self.available_dates = CNFG.client.get_available_collection_dates(self.amherst_sender,
                                                                          CNFG.courier_id)  # get dates
        self.label_text = self.shipment_name
        self.is_return = is_return
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = False
        self.label_location = None
        self.shipping_cost = None
        self.trackingNumbers = None
        self.date = None

        if DEBUG: pprint(f"\n{self=}\n")

    def boxes_script(self):
        """:returns a number of boxes to send"""
        client = self.CNFG.client
        if DEBUG: print(debug_msg())
        boxes = self.boxes
        if boxes is None or boxes == 0:
            boxes = 1
        ui = input(f"{boxes} box(es) assigned for {self.customer}\n"
                   f"\n - [Enter] to continue\n"
                   f" - [a number] to adjust\n")

        if ui.isnumeric():
            print(f"Shipment updated to {ui} boxes")
            boxes = int(ui)

        parcels = []
        for x in range(int(boxes)):
            parcel = client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            parcels.append(parcel)
        return parcels

    def date_script(self, sender=None):
        """
        takes date from shipment or today
        :return:
        """
        if DEBUG: print(debug_msg())
        # get send out date from shipment, or use today if is_return
        if self.is_return:
            send_date_obj = datetime.today()
            send_date = f"{datetime.today():{self.CNFG.datetime_masks['DT_DB']}}"
        else:
            send_date_obj = parse(self.send_out_date)
            send_date = datetime.strftime(send_date_obj, self.CNFG.datetime_masks['DT_DB'])

        # dbay client call for available dates
        print(f"--- Checking available collection dates...")
        # client = self.CNFG.client

        available_dates = self.available_dates
        # compare provided send_out date with actually available collection dates in dbay format
        # if matched get date object formatted to use with dbay api
        # compare each available date to the desired one
        for potential_collection_date in available_dates:
            potential_date_str = str(potential_collection_date.date)
            if potential_date_str == send_date:
                dbay_date_obj = potential_collection_date
                day = f"{parse(potential_collection_date.date):{self.CNFG.datetime_masks['DT_DISPLAY']}}"
                ui = input(
                    f"Shipment {'from' if self.is_return else 'for'} "
                    f"{self.customer} can be collected on {day}\n"
                    f"[Y] to confirm ")
                match ui:
                    case "y" | "Y" | "":
                        return dbay_date_obj
                    case _:
                        continue
        else:
            print(
                f"\n*** ERROR: No collections available on {send_date_obj:{self.CNFG.datetime_masks['DT_DISPLAY']}} ***\n")

        new_date = self.get_date()
        return new_date

    def get_date(self):
        available_dates = self.available_dates
        while True:
            print(f"Available Collection Dates:")
            # display available dates
            for count, date in enumerate(available_dates, 1):  # 1 index
                dt = parse(date.date)
                out = datetime.strftime(dt, self.CNFG.datetime_masks['DT_DISPLAY'])
                print(f"{TABBER} {count} | {out}")
            # get input
            choice = input(
                f'\n - [Enter] for ASAP ({datetime.strftime(parse(available_dates[0].date), self.CNFG.datetime_masks["DT_DISPLAY"])})\n'
                f' - [1 - {len(available_dates)}] to choose a date \n'
                f' - [0] to exit\n')
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
                sys.exit()

        dbay_date_obj = available_dates[choice - 1]  # 1 index
        print(f"\nCollection date for {self.customer} is now {dbay_date_obj.date}"
              f"\n{LINE}")

        return dbay_date_obj

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
                    postcode=self.delivery_postcode, search_string=self.search_term):  # walrus assigns and checks
                address = address_from_search
            else:
                address = self.address_from_postcode_candidates(postcode=self.delivery_postcode)

        address = self.check_address(address)  # displays address to user
        address_decision = input(f"\n- [G]et new address or [A]mend current address, anything else to continue\n")

        match address_decision:
            case "a" | "A":
                address = self.amend_address(address)
            case "g" | "G":
                address = self.address_from_postcode_candidates(address.postal_code)
                self.address_script(address)
            case _:
                pass

        return address

    def address_from_postcode_and_string(self, postcode: str = None, search_string: str = None):
        """
        validates a postcode and search_string against despatchbay address database

        if postcode is none get it from Shipment
        if search_string is none use Shipment.building num or else Shipment.firstline

        :param postcode or None:
        :param search_string or Shipment.building_num or firstline:
        :return: address or None:
        """
        if DEBUG: print(debug_msg())

        if postcode is None:
            postcode = input("Enter Postcode")

        if search_string is None:
            search_string = input("Enter Search String")

        try:
            address = self.CNFG.client.find_address(postcode, search_string)
        except:
            print("No address match found - go list from postcode")
            return None
        else:

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
        if DEBUG: print(debug_msg())

        while True:
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

    def amend_address(self, address):
        """
        takes an address or gets from Shipment
        lists variables in address and edits as per user input
        updates Shipment.address
        :param address:
        :return: address and update Shipment.address
        """
        if DEBUG: print(debug_msg())

        # get a list of vars considered 'address' from cnfg
        address_vars = self.CNFG.db_address_fields

        # main loop - display numbered address details and offer to edit
        while True:
            print(f"Current address: \n")
            # print each attribute of the address object with a 1-indexed identifier
            for c, var in enumerate(address_vars, start=1):
                print(f"{TABBER} {c} - {var} = {getattr(address, var)}")

            # get user selection
            ui = input(f"\n - [Enter] to continue or [a number] to edit a field\n")
            if not ui:
                return address
            if not ui.isnumeric():
                continue

            ui = int(ui) - 1  # zero index
            if not 0 <= ui < len(address_vars):
                print("wrong number")
                continue
            else:
                var_to_edit = address_vars[ui]
                new_var = input(f"\n{var_to_edit} is currently {getattr(address, var_to_edit)} \n - Enter new value \n")

            while True:
                ui = input(f"\nChange {var_to_edit} to {new_var}?\n"
                           f" - [Y] or [Enter], anything else to cancel")
                match ui:
                    case 'y' | 'Y' | '':
                        setattr(address, var_to_edit, new_var)
                        print(f"{var_to_edit} changed to {new_var}")
                        return address
                    case _:
                        break

    def check_address(self, address=None):
        """
        displays Shipment.address
        takes user input to confirm, change, or amend
        :return: address and updates Shipment.address
        """
        if DEBUG: print(debug_msg())

        if address is None:
            address = self.address
        while address:
            postcode = address.postal_code

            # print address fields of shipment-obj to the screen
            filtered_address_fields = {k: v for k, v in vars(address).items() if k in self.CNFG.db_address_fields}
            print("Current address details:")

            print(f'\n{os.linesep.join(f"{TABBER}{k}: {v}" for k, v in filtered_address_fields.items())}')

            # offer to replace None company name with customer name
            if address.company_name is None:
                ui = input(f"\n - Replace 'None' Company Name with {self.customer}? [Y / N]\n")
                if not ui or str(ui[0]).lower() == 'y':
                    address.company_name = self.customer
                    print(f"Company Name updated")
                else:
                    print("Keep company 'None'")
            self.address = address
            return address

    def get_remote_address(self, shipment_id):
        client = self.CNFG.client
        remote_address = client.get_shipment(shipment_id).recipient_address.recipient_address
        return remote_address

    def get_recip(self, address=None):
        client = self.CNFG.client
        # shipment is a return - set recipient to home base
        if self.is_return:
            home_address = client.get_sender_addresses()[0]
            recipient = client.recipient(
                name=home_address.name,
                telephone=home_address.telephone,
                email=home_address.email,
                recipient_address=home_address.sender_address,
            )
        else:
            # shipment is not a return - set recipient to customer
            recipient = client.recipient(
                name=self.delivery_contact,
                telephone=self.delivery_tel,
                email=self.delivery_email,
                recipient_address=self.address
            )
        recipient.country_code = "GB"
        return recipient

    def get_sender(self, address):
        """if is_return ios True then address is required
        """
        client = self.CNFG.client
        if self.is_return:
            sender = client.sender(
                name=self.delivery_contact,
                telephone=self.delivery_tel,
                email=self.delivery_email,
                sender_address=address
            )

        else:
            sender = client.sender(
                address_id=self.CNFG.sender_id
            )

        sender.country_code = "GB"
        return sender

    def book_collection(self, shipment_id):
        if DEBUG: print(debug_msg())
        client = self.CNFG.client

        # book collection
        shipment_return = client.book_shipments(shipment_id)[0]  # debug there could be more than one here??
        self.collection_booked = True

        # save label
        label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
        try:
            label_string = f"{self.customer} - {str(self.date.date)}.pdf"
        except:
            label_string = f"{self.customer}.pdf"
        label_pdf.download(self.CNFG.label_dir / label_string)
        self.label_location = str(self.CNFG.label_dir / label_string)

        self.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        print(
            f"\nCollection has been booked for {self.customer} on {self.date.date} "
            f"\nLabel downloaded to {self.label_location}.")
        return True

    def print_label(self):
        try:
            os.startfile(self.label_location, "print")
        except OSError as e:
            print(f"\n ERROR: Unable to print \n {e.strerror}")
        else:
            print("Parcelforce Label printed")
            self.printed = True

    def print_shipment_to_screen(self):
        print(
            f"\n"
            f"{'Collection' if self.is_return else 'Shipment'} of {len(self.parcels)} box(es) {'from' if self.is_return else 'for'} {self.customer} | "
            f"{'Collection' if self.is_return else 'Delivery'} Address : {self.address.street}\n"
            f"Collection Date: {self.date.date} | Service: {self.service.name} | Price: {self.service.cost * len(self.parcels):.2f} \n  \n")

    def log_tracking(self):
        """
        runs cmclibnet via powershell script to add tracking numbes to commence db

        :return:
        """

        class CommenceEditError(Exception):
            pass

        ps_script = str(self.CNFG.log_to_commence_powershell_script)
        try:  # utility class static method runs powershell script bypassing execuction policy
            ship_id_to_pass = str(self.shipment_id_inbound if self.is_return else self.shipment_id_outbound)
            commence_edit = Utility.powershell_runner(ps_script, self.category, self.shipment_name, ship_id_to_pass,
                                                      str(self.is_return), f"{'debug' if DEBUG else None}")

            if commence_edit == 1:
                raise CommenceEditError("\nERROR: Commence Tracking not updated - is Commence running?")

        except CommenceEditError as e:
            print(f"{e}")

        except FileNotFoundError as e:
            print("\nERROR: Unable to log tracking to Commence")
            print(f"  - FileNotFoundError : {e.filename}")

        except Exception as e:
            print(f"{e=}")
            print("\nERROR: Unable to log tracking to Commence")

        else:
            print("\nCommence Tracking updated")

    #
    # def log_collection(self):
    #     """
    #     runs cmclibnet via powershell script to add tracking numbes to commence db
    #
    #     :return:
    #     """
    #
    #     class CommenceEditError(Exception):
    #         pass
    #
    #     # tracking_nums = ', '.join(self.shipmentRequest.parcels trackingNumbers)
    #     tracking_nums = ', '.join(self.trackingNumbers)
    #     ps_script = str(self.CNFG.log_to_commence_powershell_script)
    #     try:  # utility class static method runs powershell script bypassing execuction policy
    #         commence_edit = Utility.powershell_runner(ps_script, self.shipment_name, tracking_nums,
    #                                                   self.category, self.shipment_id_inbound)
    #         if commence_edit == 1:
    #             raise CommenceEditError("\nERROR: Commence Tracking not updated - is Commence running?")
    #
    #     except CommenceEditError as e:
    #         print(f"{e}")
    #
    #     except FileNotFoundError as e:
    #         print("\nERROR: Unable to log tracking to Commence")
    #         print(f"  - FileNotFoundError : {e.filename}")
    #
    #     except Exception as e:
    #         print(f"{e=}")
    #         print("\nERROR: Unable to log tracking to Commence")
    #
    #     else:
    #         print("\nCommence Tracking updated")

    def log_json(self):
        # export from object attrs
        self.parcels = len(self.parcels)
        self.recipient_address = f"{self.recipient.recipient_address.postal_code} - {self.recipient.recipient_address.street}"
        export_dict = {}
        if self.is_return:
            self.sender_address = f"{self.sender.sender_address.street} - {self.sender.sender_address.postal_code}"

        for field in self.CNFG.export_fields:
            try:
                val = getattr(self, field)
                if isinstance(val, datetime):
                    val = f"{val.isoformat(sep=' ', timespec='seconds')}"

                export_dict.update({field: val})
            except Exception as e:
                print(f"{field} not found in shipment")
                print(e)

        with open(self.CNFG.log_file, 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",\n")
        print(f"{os.linesep} Json exported to {self.CNFG.log_file}:")
        pprint(export_dict)


class Config:
    """
    sets up the environment
    creates a dbay client
    """

    def __init__(self, sandbox=False):
        self.export_fields = None
        self.shipment_fields = None
        self.db_address_fields = None

        self.datetime_masks = None
        DATA_DIR = None
        SCRIPTS_DIR = None
        self.label_dir = None
        self.log_file = None
        self.backup_xml = None
        self.cmc_checkin = None
        self.log_to_commence_powershell_script = None
        self.cmc_dll = None
        self.cmc_inst = None


        ROOT_DIR = pathlib.Path(pathlib.Path(__file__)).parent.parent
        config_path = ROOT_DIR / 'config.toml'
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        # fields
        self.export_fields = config['fields']['export']
        self.shipment_fields = config['fields']['shipment']
        self.db_address_fields = config['fields']['address']
        self.gui_fields = config['gui']['fields']
        self.gui_map = config['gui']['map']
        self.amherst_address = config['amherst_address']

        self.datetime_masks = config['datetime_masks']

        # paths~
        DATA_DIR = ROOT_DIR / config['paths']['data']
        SCRIPTS_DIR = ROOT_DIR / config['paths']['scripts']
        self.label_dir = DATA_DIR / config['paths']['labels']
        self.log_file = DATA_DIR / config['paths']['log']
        self.backup_xml = DATA_DIR / 'AmShip.xml'
        self.label_dir.mkdir(parents=True, exist_ok=True)

        # CmcLibNet files for interacting with Commence DB:
        self.cmc_checkin = SCRIPTS_DIR / config['paths']['cmc_checkin']
        self.log_to_commence_powershell_script = SCRIPTS_DIR / config['paths']['cmc_log']
        self.cmc_dll = pathlib.Path(config['paths']['cmc_dll'])
        self.cmc_inst = pathlib.Path(ROOT_DIR / config['paths']['cmc_inst'])
        if not self.cmc_dll.exists():
            print(f"Vovin CmCLibNet is not installed in expected location {self.cmc_dll}")
            self.install_cmc()

        # parse shipmode argument and setup API keys from .env
        if sandbox:
            print(f"\n {TABBER * 2}*** !!! SANDBOX MODE !!! *** \n")
            api_user = os.getenv(config['dbay']['sand']['api_user_keyname'])
            api_key = os.getenv(config['dbay']['sand']['api_key_keyname'])
            self.courier_id = config['dbay']['sand']['courier']
            self.service_id = config['dbay']['sand']['service']
        else:
            api_user = os.getenv(config['dbay']['prod']['api_user_keyname'])
            api_key = os.getenv(config['dbay']['prod']['api_key_keyname'])
            self.courier_id = config['dbay']['prod']['courier']  # parcelforce
            self.service_id = config['dbay']['prod']['service']  # parcelforce 24

        # dbay client setup
        self.sender_id = os.getenv("DESPATCH_SENDER_ID")
        # noinspection PyUnboundLocalVariable
        self.client = DespatchBaySDK(api_user=api_user, api_key=api_key)

        if DEBUG:
            print(f"{ROOT_DIR=} \n)")
            pprint(f" {config} \n \n {self}")

    def install_cmc(self):
        try:
            subprocess.run([str(self.cmc_inst), '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           check=True)
        except subprocess.CalledProcessError as e:
            print(f"\n\nERROR: CmcLibNet Installer Failed - logging to commence is impossible \n {e}")

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


def debug_msg(e=None):
    debug_msg = "\n\n"
    debug_msg += f"\nCurrent method = {inspect.currentframe().f_back.f_code.co_name}\n"
    if e:
        debug_msg += f"ERROR: {e}" if {e} else None
