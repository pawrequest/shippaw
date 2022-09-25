## script:


from datetime import datetime

from dateutil.parser import parse

from config import *

line = '-' * 100


# class Amherst:
#     def __int__(self):
#         pass


class Shipment:
    def __init__(self, shipdict, shipid=None):
        for field in SHIPFIELDS:
            v = shipdict[field]
            setattr(self, field,v)
        self.client = CLIENT
        self.courier_id = 8
        self.category = None
        self.collectionBooked = False
        self.dbAddressKey = 0
        if shipid: self.id = shipid
        self.sender = SENDER
        self.shippingServiceId = 101 # parcelforce 24... change for others
        self.trackingNumbers = None


        self.boxes = shipdict['boxes'] #shipdict['boxes']
        self.dates = self.client.get_available_collection_dates(SENDER, self.courier_id)  # get dates
        self.Customer = shipdict['customer']
        self.deliveryEmail = shipdict['deliveryEmail']
        self.deliveryName = shipdict['deliveryName']
        self.deliveryTel = shipdict['deliveryTel']
        self.deliveryBuildingNum = None
        # self.deliveryContact = shipdict['deliveryContact']
        # self.deliveryAddress = shipdict['deliveryAddress']
        self.deliveryPostcode = shipdict['deliveryPostcode']
        # self.deliveryFirstline = None
        # self.SendOutDate = shipdict['sendOutDate']
        # self.shippingCost = None

        # self.addedShipment = None
        # self.addressObject = None
        # self.dateObject = None
        # self.shipmentRequest = None
        # self.shipmentReturn = None

        # self.labeLocation = None
        # self.labelDownloaded = False
        # self.labelLocation = None
        # self.labelUrl = None
        # self.parcels = None
        # self.recipient = None
        # self.services = None
        # self.shipmentDocId = None
        # self.shippingServiceName = None

        if shipdict:
            if isinstance(shipdict, dict):
                # print("- Dictionary passed in - Getting Attrs from shipdict:")
                for k, v in shipdict.items():
                    if not shipid:
                        if k == 'hireRef':
                            setattr(self, 'id', v)
                    setattr(self, k, v)
        # print("Shipment with id=", self.id, "created")

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
            dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
            for date in dates:
                if date.date == self.sendOutDate:  # if date object matches send date
                    self.dateObject = date
                    print("Shipment date for", self.customer, "validated - ", self.dateObject.date)
                    return

        parse_address()
        val_date_init(self)

    def val_boxes(self):
        while True:
            if self.boxes:
                print(line, "\n\t\t", self.Customer, "|", self.deliveryFirstline, "|", self.deliverySendOutDate, "|", self.boxes,
                      "box/es\n")
                ui = input("[C]onfirm or Enter a number of boxes\n")
                if ui.isnumeric():
                    self.boxes = int(ui)
                    print("Shipment updated  |  ", self.boxes, "  boxes\n")
                if ui == 'c':
                    print("Confirmed")
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

    # need CLIENT
    def val_dates(self):
        dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
        print("--- Checking available collection dates...")
        print(line)  # U+2500, Box Drawings Light Horizontal #
        # self.SendOutDate=datetime.strptime(self.SendOutDate, '%d/%m/%Y').date()
        send_date = datetime.strftime(self.deliverySendOutDate, '%Y-%m-%d')
        # item['send_out_date'] = datetime.strptime(item['send_out_date'], '%d/%m/%Y').date()

        for despdate in dates:
            compdate = str(despdate.date)
            if compdate == send_date:  # if date object matches send date
                self.dateObject = despdate
                return
        else:  # loop exhausted, no date match
            print("\n*** ERROR: No collections available on", self.deliverySendOutDate, "for",
                  self.Customer, "***\n\n\n- Collections for", self.Customer, "are available on:\n")
            for count, date in enumerate(dates):
                dt = parse(date.date)
                out = datetime.strftime(dt, '%A %d %B')
                print("\t\t", count + 1, "|", out)

            while True:
                choice = input('\n- Enter a number to choose a date, [0] to exit\n')
                if choice == "":
                    continue
                if not choice.isnumeric():
                    print("- Enter a number")
                    continue
                if not -1 <= int(choice) <= len(dates) + 1:
                    print('\nWrong Number!\n-Choose new date for', self.Customer, '\n')
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
                    print("\t\tCollection date for", self.Customer, "is now ", self.dateObject.date, "\n\n",
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
        ui = input(f"- Recipient address is {self.addressObject.street} - is this correct? [C]ontinue, anything else to change address")
        if ui[0].lower()=="c":
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
        self.DespAddress = self.client.address(
            company_name=self.Customer,
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
            recipient_address=self.DespAddress

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
            client_reference=self.Customer,
            collection_date=self.dateObject.date,
            sender_address=SENDER,
            recipient_address=self.recipient,
            follow_shipment='true'
        )
        self.shipmentRequest.collection_date = self.dateObject.date  # careful of case! despatchj stuff is _s
        services = self.client.get_available_services(self.shipmentRequest)
        if services[0].id != self.shippingServiceId:
            print("Something is wrong with the shipping service name")
        self.shippingServiceName = services[0].name
        self.shippingCost = services[0].cost
        self.services = services

    def queue(self):
        addedShipment = self.client.add_shipment(self.shipmentRequest)
        self.addedShipment = addedShipment

        print("\n", line, '\n-', self.Customer, "|", self.boxes, "|",
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
        pathlib.Path(DIR_LABEL).mkdir(parents=True, exist_ok=True)
        label_string = ""
        try:
            label_string = label_string + self.Customer + "-" + str(self.dateObject.date) + ".pdf"
        except:
            label_string = label_string, self.Customer, ".pdf"
        label_pdf.download(DIR_LABEL / label_string)
        self.trackingNumbers = []
        for parcel in shipment_return.parcels:
            self.trackingNumbers.append(parcel.tracking_number)

        self.shipmentReturn = shipment_return
        self.shipmentDocId = shipment_return.shipment_document_id
        self.labelUrl = shipment_return.labels_url
        self.parcels = shipment_return.parcels
        self.labelLocation = str(DIR_LABEL) + label_string

        self.collectionBooked = True
        self.labelDownloaded = True
        print("Shipment for ", self.Customer, "has been booked, Label downloaded to", self.labelLocation)
        self.log_json()
        exit()

    def process_shipment(self):
        if self.deliveryBuildingNum:
            print("Building No. Found, address search using no.", self.deliveryBuildingNum)
        else: print("- No building number, address search using deliveryFirstline:", self.deliveryFirstline)
        if self.dateObject:
            print("Send-Out date validated - collection on:", self.dateObject.date)
        else:
            self.val_dates()
        self.val_boxes()
        self.val_address()
        self.change_add()
        self.make_request()


        # if self.boxes == 0:
        #     print("\n\t\t*** ERROR: No boxes added ***\n")
        #     if input("add boxes (y/n)?")[0].lower() == "y":
        #         self.ValBoxes()
        # if self.boxes > 0:
        #     ui = input(
        #         f"{self.boxes} boxes in shipment for {self.Customer} - is this correct? [Y] to confirm or a number of boxers to send")
        #     if ui.isnumeric():
        #         self.boxes = int(ui)
        #     elif [0].lower() == "y":
        #         print("SOME BOLOX")

    def log_json(self):
        pass
        # export from object attrs?

        # export_dict = {}
        # export_keys = [k for k in dir(shipment) if
        #                not k.startswith('__') and k not in EXPORT_EXCLUDE_KEYS and getattr(shipment, k)]
        #
        # self.SendOutDate = self.SendOutDate.strftime('%d/%m/%Y')
        # for key in export_keys:
        #     export_dict.update({key: getattr(shipment, key)})
        # with open(DIR_DATA / 'AmShip.json', 'w') as f:
        #     json.dump(export_dict, f, sort_keys=True)
        #     print("Data dumped to json:", export_keys)
        # return
#
#
#         if d is not None:
#             for k,v in d.items():
#                 setattr(self,k,v)
#
# class MyClass(object):
#     def __init__(self, number):
#         self.number = number
#
# my_objects = []
#
# for i in range(len()):
#     my_objects.append(MyClass(i))
# for obj in my_objects:
#     print (obj.number)
#
# class MyClass(object): pass
# objs = [MyClass() for i in range(10)]
# print(objs)
#


################### end init  ######################################################################################


# def EstablishShipment(self):
#     if self.deliveryBuildingNum: print("Building No. Found, address search using no.", self.deliveryBuildingNum)
#     elif not self.deliveryBuildingNum: print("- No building number, address search using deliveryFirstline:", self.deliveryFirstline)
#     if self.dateObject: print("Send-Out date validated - collection on:", self.dateObject.date)
#     elif not self.dateObject: print("\n*** ERROR: No collections available on", self.SendOutDate, "for", self.Customer, " ***")
#     if input(f"Choose a new collection date for {self.Customer} (y/n)?")[0].lower() == "y":
#         self.ValDates()
#     if self.boxes == 0:
#         print("\n\t\t*** ERROR: No boxes added ***\n")
#         if input("add boxes (y/n)?")[0].lower() == "y":
#             self.ValBoxes()
#     if self.boxes > 0:
#         ui = input(f"{self.boxes} boxes in shipment for {self.Customer} - is this correct? [Y] to confirm or a number of boxers to send")
#         if ui.isnumeric():
#             self.boxes=int(ui)
#         elif [0].lower() =="y":
#             print("SOME BOLOX")


# def ValBoxes(self):
#     if self.boxes == 0:
#         print("\n\t\t*** ERROR: No boxes added ***\n")
#
#
#
#
#     if self.boxes > 0:
#         ui = input(
#             f"{self.boxes} boxes in shipment for {self.Customer} - [C]onfirm or Enter a number of boxes\n")
#         if ui.isnumeric():
#             self.boxes = int(ui)
#             print("self updated  |  ", self.boxes, "  boxes\n")
#         if ui == 'c':
#             return self
#         else:
#             # print("\n\t\t*** ERROR: No boxes added ***\n")
#             ui = input("- How many boxes?\n")
#             if not ui.isnumeric():
#                 print("- Enter a number")
#                 continue
#             self.boxes = int(ui)
#             print("self updated  |  ", self.boxes, "  boxes")
#             return self
#




class Hire():
    def __init__(self, hiredict:dict, hireid=None):
        for k, v in hiredict.items():
            if k == 'hireRef':
                k=k.replace(",","")
            setattr(self, k, v)
            setattr(self, 'id', hireid)

    def make_shipment(self):
        for field in SHIPFIELDS:
            if field in vars(self):
                print(field)





# class HireShipment(Hire):
#     def __init__(self, hire_dict=None, hire_id=None):
#         super().__init__(hire_dict)
#         for k, v in hire_dict.items():
#             if not k in SHIPFIELDS:
#                     (self, k, v)
#
#     def ship(self):
#         shipment = Shipment(self,33)
#         shipment.process_shipment()
