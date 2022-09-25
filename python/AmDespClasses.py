from datetime import datetime

from dateutil.parser import parse

from config import *


class Shipment:
    def __init__(self, shipdict, shipid=None, shipref=None):

        for field in SHIPFIELDS:
            if field in shipdict:
                v = shipdict[field]
                setattr(self, field, v)
            else:
                print(f"*** ERROR - {field} not found in shipdict")
        ## DespatchBay API config
        self.client = CLIENT
        self.courier_id = 8
        self.collectionBooked = False
        self.dbAddressKey = 0
        self.sender = SENDER
        # self.ServiceId = 101 # WRONG CODE?  parcelforce 24... change for others
        self.shipping_service_id = 101  ## parcelforce 24 - maybe make dynamic?
        self.dates = self.client.get_available_collection_dates(SENDER, self.courier_id)  # get dates

        ## provided shipment details
        if shipid:
            self.id = shipid
        else:
            self.id = shipdict['referenceNumber']
        self.customer = shipdict['customer']
        self.deliveryEmail = shipdict['deliveryEmail']
        self.deliveryName = shipdict['deliveryName']
        self.deliveryTel = shipdict['deliveryTel']
        self.deliveryContact = shipdict['deliveryContact']
        self.deliveryAddress = shipdict['deliveryAddress']
        self.deliveryPostcode = shipdict['deliveryPostcode']
        self.sendOutDate = shipdict['sendOutDate']
        self.boxes = shipdict['boxes']
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
            # dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
            for candidate in self.dates:
                if candidate.date == datetime.strftime(self.sendOutDate,
                                                       '%Y-%m-%d'):  # if date object matches send date
                    self.dateObject = candidate
                    print(line, '\n',
                          f"Shipment date for {self.customer} validated - {datetime.strftime(self.sendOutDate, '%A %B %#d')}")

        parse_address()
        val_date_init(self)

    def val_boxes(self):
        while True:
            if self.boxes:
                print(line, "\n",
                      f"Shipment for {self.customer} has {self.boxes} box(es) assigned - is this correct?\n")
                ui = input(f"[C]onfirm or Enter a number of boxes\n")
                if ui.isnumeric():
                    self.boxes = int(ui)
                    print(f"Shipment updated  |  {self.boxes}  boxes\n")
                if ui == 'c':
                    print("Confirmed\n", line)
                    return self
                continue
            else:
                # print("\n\t\t*** ERROR: No boxes added ***\n")
                ui = input("- How many boxes?\n")
                if not ui.isnumeric():
                    print("- Enter a number")
                    continue
                self.boxes = int(ui)
                print("self updated  |  ", self.boxes, "  boxes")
                return self

    def val_dates(self):
        dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
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
            print("\n*** ERROR: No collections available on", self.sendOutDate, "for",
                  self.customer, "***\n\n\n- Collections for", self.customer, "are available on:\n")
            for count, date in enumerate(dates):
                dt = parse(date.date)
                out = datetime.strftime(dt, '%A - %B %#d')
                print("\t\t", count + 1, "|", out)

            while True:
                choice = input('\n- Enter a number to choose a date, [0] to exit\n')
                if choice == "":
                    continue
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
                        self.log_json()
                        exit()
                    continue
                else:
                    self.dateObject = dates[int(choice) - 1]
                    print("\t\tCollection date for", self.customer, "is now ", self.dateObject.date, "\n\n",
                          line)
                    return

    def val_address(self):
        if self.deliveryBuildingNum:
            if self.deliveryBuildingNum != 0:
                search_string = self.deliveryBuildingNum
            else:
                print("No building number, searching deliveryFirstline")
                self.deliveryBuildingNum = False
                search_string = self.deliveryFirstline
        else:
            print("No building number, searching deliveryFirstline")
            search_string = self.deliveryFirstline
        # get object
        address_object = self.client.find_address(self.deliveryPostcode, search_string)
        self.addressObject = address_object
        return self

    def change_add(self):
        ui = input(
            f"- Recipient address is {self.addressObject.street} - is this correct? [C]ontinue, anything else to change address\n\n")
        if ui[0].lower() == "c":
            return
        candidates = self.client.get_address_keys_by_postcode(self.deliveryPostcode)
        for count, candidate in enumerate(candidates, start=1):
            print(" - Candidate", str(count) + ":", candidate.address)
        selection = ""
        while True:
            selection = input('\n- Enter a candidate number, [0] to exit \n')
            if selection.isnumeric():
                selection = int(selection)
            else:
                continue
            if selection == 0:
                if str(input("[e]xit?"))[0].lower() == "e":
                    self.log_json()
                    exit()
                continue
            if not -1 <= selection <= len(candidates) + 1:
                print("Wrong Number")
                continue
            break
        selected_key = candidates[int(selection) - 1].key
        self.addressObject = self.client.get_address_by_key(selected_key)
        print("- New Address:", self.addressObject.street)
        return

    def make_request(self):
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
            sender_address=SENDER,
            recipient_address=self.recipient,
            follow_shipment='true',
            service_id=101  # debug i added this manually?
        )
        self.shipmentRequest.collection_date = self.dateObject.date  #
        self.services = self.client.get_available_services(self.shipmentRequest)
        if self.services[0].service_id != self.shipping_service_id:
            print("Something is wrong with the shipping service name")
        self.shippingServiceName = self.services[0].name
        self.shippingCost = self.services[0].cost
        self.shipping_service_id = self.shipmentRequest.service_id
        self.services = self.services

    def queue(self):
        self.addedShipment = self.client.add_shipment(self.shipmentRequest)

        print("\n", line, '\n-', self.customer, "|", self.boxes, "|",
              self.addressObject.street, "|", self.dateObject.date, "|",
              self.shippingServiceName,
              "| Price =",
              self.shippingCost, '\n', line, '\n')

        choice = "n"
        while choice[0] not in ["q", "r", 'e']:
            choice = input('- [Q]ueue, [R]estart, or [E]xit\n')
            choice = str(choice[0].lower())
            if choice[0] != "q":  # not quote
                if choice != 'r':  # not restart
                    if choice != 'e':  # not exit either
                        continue  # try again
                    else:  # exit
                        if str(input("[E]xit?"))[0].lower() == 'e':  # comfirn exit
                            self.log_json()
                            exit()
                        continue
                else:  # restart
                    if str(input("[R]estart?"))[0].lower() == 'r':  # confirm restart
                        print("Restarting")
                        # self.Process(self)  #debug does it run process? or soemthing else
                    continue  # not restarting
            print("Adding Shipment to Despatchbay Queue")

    def book_collection(self):
        self.client.book_shipments(self.addedShipment)
        shipment_return = self.client.get_shipment(self.addedShipment)

        label_pdf = self.client.get_labels(shipment_return.shipment_document_id)
        pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)
        label_string = ""
        try:
            label_string = label_string + self.customer + "-" + str(self.dateObject.date) + ".pdf"
        except:
            label_string = label_string, self.customer, ".pdf"
        label_pdf.download(LABEL_DIR / label_string)
        self.trackingNumbers = []
        for parcel in shipment_return.parcels:
            self.trackingNumbers.append(parcel.tracking_number)

        self.shipmentReturn = shipment_return
        self.shipmentDocId = shipment_return.shipment_document_id
        self.labelUrl = shipment_return.labels_url
        self.parcels = shipment_return.parcels
        self.labelLocation = str(LABEL_DIR) + label_string

        self.collectionBooked = True
        self.labelDownloaded = True
        print("Shipment for ", self.customer, "has been booked, Label downloaded to", self.labelLocation)
        self.log_json()
        exit()

    def log_json(self):
        pass
        # export from object attrs?

        # export_dict = {}
        # export_keys = [k for k in dir(shipment) if
        #                not k.startswith('__') and k not in EXPORT_EXCLUDE_KEYS and getattr(shipment, k)]
        #
        # self.sendOutDate = self.sendOutDate.strftime('%d/%m/%Y')
        # for key in export_keys:
        #     export_dict.update({key: getattr(shipment, key)})
        # with open(DATA_DIR / 'AmShip.json', 'w') as f:
        #     json.dump(export_dict, f, sort_keys=True)
        #     print("Data dumped to json:", export_keys)
        # return


class Hire:
    def __init__(self, hiredict: dict, hireid=None):
        self.hiredict = hiredict
        for k, v in hiredict.items():
            if k == 'hireRef':
                k = k.replace(",", "")
            setattr(self, k, v)
            setattr(self, 'id', hireid)

    def make_shipment(self):
        oShip = Shipment(self.hiredict, self.referenceNumber)
        self.oShip = oShip
        return oShip

    def ship_hire(self):  # Runs class methods to ship a hire object
        oShip = self.make_shipment()
        oShip.val_boxes()
        oShip.val_dates()
        oShip.val_address()
        oShip.change_add()
        oShip.make_request()
        oShip.queue()





class Product:
    def __init__(self, dict):
        for field in CLASS_CONFIG['PRODUCT']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Radio(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CLASS_CONFIG['RADIO']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Battery(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CLASS_CONFIG['BATTERY']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Charger(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CLASS_DICT['CHARGER']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class AUDIO_ACC(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CLASS_DICT['AUDIO_ACC']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Price_List(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CLASS_DICT['PRICE_LIST']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")

# class Product:
#     def __init__(self, dict):
#         for field in product_fields:
#             if field in dict.keys():
#                 setattr(self, field, dict[field])
#             else:print(f"ERROR - input missing {field}")
#
# class Radio(Product):
#     def __init__(self,dict):
#         Product.__init__(self,dict)
#         for field in radio_fields:
#             if field in dict.keys():
#                 setattr(self, field, dict[field])
#             else:
#                 print(f"ERROR - input missing {field}")
