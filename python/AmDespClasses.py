from datetime import datetime

from dateutil.parser import parse

from config import *

line = '-' * 100


# class Amherst:
#     def __int__(self):
#         pass


class Shipment:
    def __init__(self, shipdict=None, shipid=None):
        self.recipient = None
        self.shipmentRequest = None
        self.labelLocation = None
        self.trackingNumbers = None
        self.addedShipment = None
        self.addedShipment = None
        self.addressObject = None
        self.boxes = None
        self.buildingNum = None
        self.building_num = None
        self.category = None
        self.client = client
        self.collectionBooked = False
        self.contact = None
        self.courier_id = 8
        self.customer = None
        self.dAddress = None
        self.dEmail = None
        self.dKey = 0
        self.dName = None
        self.dPhone = None
        self.dPostcode = None
        self.dates = None
        self.firstline = None
        self.hireRef = None
        self.id = None
        self.labeLocation = None
        self.labelDownloaded = False
        self.labelUrl = None
        self.parcels = None
        self.sendDate = None
        self.sender = sender
        self.services = None
        self.shipmentDocId = None
        self.shipmentReturn = None
        self.shippingServiceId = 101
        self.shippingServiceName = None
        self.shippingCost = None
        self.shippingServiceName = None

        if shipdict:
            if isinstance(shipdict, dict):
                print("- Dictionary passed in - Getting Attrs from shipdict:")
                for k, v in shipdict.items():
                    if k == 'hireRef':
                        setattr(self, 'id', v)
                    setattr(self, k, v)
        print("Shipment", shipid, "created")

        def parseAddress():
            print("\n--- Parsing Address...\n")
            crapstring = self.dAddress
            firstline = crapstring.split("\n")[0]
            first_block = (crapstring.split(" ")[0]).split(",")[0]
            first_char = first_block[0]
            self.firstline = firstline
            for char in firstline:
                if not char.isalpha():
                    if not char.isnumeric():
                        if not char == " ":
                            firstline = firstline.replace(char, "")
            if first_char.isnumeric():
                self.building_num = first_block
                print("Building No. Found, using no.", self.building_num, "\n")
            else:
                print("- No building number, using firstline:", self.firstline, '\n')

        parseAddress()

        self.dates = self.client.get_available_collection_dates(sender, self.courier_id)  # get dates

    # end init
    def CheckBoxes(self):
        while True:
            if self.boxes:
                print(line, "\n\t\t", self.customer, "|", self.firstline, "|", self.sendDate, "|", self.boxes,
                      "box/es\n")
                ui = input("[C]onfirm or Enter a number of boxes\n")
                if ui.isnumeric():
                    self.boxes = int(ui)
                    print("self updated  |  ", self.boxes, "  boxes\n")
                if ui == 'c':
                    return self
                continue
            else:
                print("\n\t\t*** ERROR: No boxes added ***\n")
                ui = input("- How many boxes?\n")
                if not ui.isnumeric():
                    print("- Enter a number")
                    continue
                self.boxes = int(ui)
                print("self updated  |  ", self.boxes, "  boxes")
                return self

    #

    # need client
    def ValDates(self):
        dates = self.client.get_available_collection_dates(self.sender, self.courier_id)  # get dates
        print("--- Checking available collection dates...")
        print(line)  # U+2500, Box Drawings Light Horizontal #
        for count, date in enumerate(dates):
            if date.date == self.sendDate:  # if date object matches send date
                self.dateObject = date
                return
        else:  # looped exhausted, no date match
            print("\n*** ERROR: No collections available on", self.sendDate, "for",
                  self.customer, "***\n\n\n- Collections for", self.customer, "are available on:\n")
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
                    print('\nWrong Number!\n-Choose new date for', self.customer, '\n')
                    for count, date in enumerate(dates):
                        print("\t\t", count + 1, "|", date.date, )
                    continue
                if int(choice) == 0:
                    if input('[E]xit?')[0].lower() == "e":
                        self.LogJson()
                        exit()
                    continue
                else:
                    self.dateObject = dates[int(choice) - 1]
                    print("\t\tCollection date for", self.customer, "is now ", self.dateObject.date, "\n\n",
                          line)
                    return

    def ValAddress(self):
        if self.building_num:
            if self.building_num != 0:
                search_string = self.building_num
            else:
                print("No building number, searching firstline")
                self.building_num = False
                search_string = self.firstline
        else:
            print("No building number, searching firstline")
            search_string = self.firstline
        # get object
        address_object = self.client.find_address(self.dPostcode, search_string)
        self.addressObject = address_object
        return

    def ChangeAdd(self):
        print("Changing shipping address  | ", self.customer, " | ",
              str(self.dateObject.date),
              "\n")
        candidates = self.client.get_address_keys_by_postcode(self.dPostcode)
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
                    self.LogJson()
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

    def MakeRequest(self):
        self.DespAddress = self.client.address(
            company_name=self.customer,
            country_code="GB",
            county=self.addressObject.county,
            locality=self.addressObject.locality,
            postal_code=self.addressObject.postal_code,
            town_city=self.addressObject.town_city,
            street=self.addressObject.street
        )

        self.recipient = self.client.recipient(
            name=self.contact,
            telephone=self.dPhone,
            email=self.dEmail,
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
            client_reference=self.customer,
            collection_date=self.dateObject.date,
            sender_address=sender,
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

    def Queue(self):
        addedShipment = self.client.add_shipment(self.shipmentRequest)
        self.addedShipment = addedShipment

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
                            self.LogJson()
                            exit()
                        continue
                else:  # restart
                    if str(input("[R]estart?"))[0].lower() == 'r':  # confirm restart
                        print("Restarting")
                        # self.Process(self)  #debug does it run process? or soemthing else
                    continue  # not restarting
            print("Adding Shipment to Despatchbay Queue")

    def BookCollection(self):
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
        self.LogJson()
        exit()

    def LogJson(self):
        pass
        # export from object attrs?

        # export_dict = {}
        # export_keys = [k for k in dir(shipment) if
        #                not k.startswith('__') and k not in export_exclude_keys and getattr(shipment, k)]
        #
        # self.sendDate = self.sendDate.strftime('%d/%m/%Y')
        # for key in export_keys:
        #     export_dict.update({key: getattr(shipment, key)})
        # with open(DATA_DIR / 'AmShip.json', 'w') as f:
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
