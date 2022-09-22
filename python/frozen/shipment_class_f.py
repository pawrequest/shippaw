class Shipment(id=1):
    def __init__(self, id, d=None):
        self.label_downloaded = None
        self.collection_booked = None
        self.label_location = None
        self.parcels = None
        self.label_url = None
        self.shipment_doc_id = None
        self.added_shipment = None
        self.shipping_service_name = None
        self.address_object = None
        self.building_num = None
        self.shipment_return = None
        self.id = id
        self.customer = None
        self.category = None
        self.send_date = None
        self.d_address = None
        self.d_email = None
        self.d_phone = None
        self.d_postcode = None
        self.hire_ref = None
        self.d_name = None
        self.contact = None
        self.boxes = 0
        self.shipping_service_id = 101
        self.d_key = 0

#     def GetJson(self, json):
#         pass
#
#     def Unsanitise(self, string):
#         string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
#                                                                                                                 chr(60)).replace(
#             "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
#         return string
#
#     def GetXml(self, xml):
#         tree = ET.parse(xml)
#         root = tree.getroot()
#         fields = root[0][2]
#         connected_customer = root[0][3][1][0][0].text
#         cat = root[0][0].text.lower()
#         for field in fields:
#             if field[0].text:
#                 fieldname = field[0].text.lower()
#                 fieldname = self.Unsanitise(fieldname)
#                 if " " in fieldname:
#                     fieldname = fieldname.replace(" ", "_")
#                 if fieldname in commence_columns.keys():  # debug
#                     fieldname = commence_columns[fieldname]
#                 if field[1].text:
#                     fieldvalue = field[1].text
#                     fieldvalue = self.Unsanitise(fieldvalue)
#                     if fieldvalue.isnumeric():
#                         fieldvalue = int(fieldvalue)
#                         if fieldvalue == 0:
#                             fieldvalue = None
#                     setattr(self, fieldname, fieldvalue)
#         setattr(self, self.category, cat)
#         print(self.send_date)
#         if cat.lower() == "customer":
#             print("IS A CUSTOMER")
#             self.send_date = datetime.today().date()
#         elif cat.lower() == "hire":
#             print("IS A HIRE")
#             setattr(self, self.customer, connected_customer)
#             self.send_date = datetime.strftime(self.send_date, '%d/%m/%Y')
#
#     def CheckBoxes(self, shipment):
#         ui = ""
#         while True:
#             if self.boxes:
#                 print(line, "\n\t\t", self.customer, "|", self.firstline, "|", self.send_date)
#                 ui = input("[C]onfirm or Enter a number of boxes\n")
#                 if ui.isnumeric():
#                     self.boxes = int(ui)
#                     print("self updated  |  ", self.boxes, "  boxes\n")
#                 if ui == 'c':
#                     return self
#                 continue
#             else:
#                 print("\n\t\t*** ERROR: No boxes added ***\n")
#                 ui = input("- How many boxes?\n")
#                 if not ui.isnumeric():
#                     print("- Enter a number")
#                     continue
#                 self.boxes = int(ui)
#                 print("self updated  |  ", self.boxes, "  boxes")
#                 return self
#
#     def ParseAddress(self):
#         print("\n--- Parsing Address...\n")
#         crapstring = self.d_address
#         firstline = crapstring.split("\n")[0]
#         first_block = (crapstring.split(" ")[0]).split(",")[0]
#         first_char = first_block[0]
#         self.firstline = firstline
#         for char in firstline:
#             if not char.isalpha():
#                 if not char.isnumeric():
#                     if not char == " ":
#                         firstline = firstline.replace(char, "")
#         if first_char.isnumeric():
#             self.building_num = first_block
#         else:
#             print("- No building number, using firstline:", self.firstline, '\n')
#
#     def ValDates(self):
#         dates = client.get_available_collection_dates(sender, courier_id)  # get dates
#         print("--- Checking available collection dates...")
#         print(line)  # U+2500, Box Drawings Light Horizontal #
#         for count, date in enumerate(dates):
#             if date.date == self.send_date:  # if date object matches send date
#                 self.date_object = date
#                 return
#         else:  # looped exhausted, no date match
#             print("\n*** ERROR: No collections available on", self.send_date, "for",
#                   self.customer, "***\n\n\n- Collections for", self.customer, "are available on:\n")
#             for count, date in enumerate(dates):
#                 dt = parse(date.date)
#                 out = datetime.strftime(dt, '%A %d %B')
#                 print("\t\t", count + 1, "|", out)
#
#             choice = ""
#             while True:
#                 choice = input('\n- Enter a number to choose a date, [0] to exit\n')
#                 if choice == "":
#                     continue
#                 if not choice.isnumeric():
#                     print("- Enter a number")
#                     continue
#                 if not -1 <= int(choice) <= len(dates) + 1:
#                     print('\nWrong Number!\n-Choose new date for', self.customer, '\n')
#                     for count, date in enumerate(dates):
#                         print("\t\t", count + 1, "|", date.date, )
#                     continue
#                 if int(choice) == 0:
#                     if input('[E]xit?')[0].lower() == "e":
#                         self.LogJson(self)
#                         exit()
#                     continue
#                 else:
#                     self.date_object = dates[int(choice) - 1]
#                     print("\t\tCollection date for", self.customer, "is now ", self.date_object.date, "\n\n",
#                           line)
#                     return
#
#     def ValAddress(self):
#         if self.building_num:
#             if self.building_num != 0:
#                 search_string = self.building_num
#             else:
#                 print("No building number, searching firstline")
#                 self.building_num = False
#                 search_string = self.firstline
#         else:
#             print("No building number, searching firstline")
#             search_string = self.firstline
#         # get object
#         addressObject = client.find_address(self.d_postcode, search_string)
#         self.addressObject = addressObject
#         return
#
#     def ChangeAdd(self):
#         print("Changing shipping address  | ", self.customer, " | ",
#               str(self.date_object.date),
#               "\n")
#         candidates = client.get_address_keys_by_postcode(self.d_postcode)
#         for count, candidate in enumerate(candidates, start=1):
#             print(" - Candidate", str(count) + ":", candidate.address)
#         selection = ""
#         while True:
#             selection = input('\n- Enter a candidate number, [0] to exit \n')
#             if selection.isnumeric():
#                 selection = int(selection)
#             else:
#                 continue
#             if selection == 0:
#                 if str(input("[e]xit?"))[0].lower() == "e":
#                     self.LogJson(self)
#                     exit()
#                 continue
#             if not -1 <= selection <= len(candidates) + 1:
#                 print("Wrong Number")
#                 continue
#             break
#         selected_key = candidates[int(selection) - 1].key
#         self.addressObject = client.get_address_by_key(selected_key)
#         print("- New Address:", self.addressObject.street)
#         return
#
#     def MakeRequest(self):
#         recipient_address = client.address(
#             company_name=self.customer,
#             country_code="GB",
#             county=self.addressObject.county,
#             locality=self.addressObject.locality,
#             postal_code=self.addressObject.postal_code,
#             town_city=self.addressObject.town_city,
#             street=self.addressObject.street
#         )
#
#         recipient = client.recipient(
#             name=self.contact,
#             telephone=self.d_phone,
#             email=self.d_email,
#             recipient_address=recipient_address
#
#         )
#         parcels = []
#         for x in range(self.boxes):
#             parcel = client.parcel(
#                 contents="Radios",
#                 value=500,
#                 weight=6,
#                 length=60,
#                 width=40,
#                 height=40,
#             )
#             parcels.append(parcel)
#
#         shipment_request = client.shipment_request(
#             parcels=parcels,
#             client_reference=self.customer,
#             collection_date=self.date_object.date,
#             sender_address=sender,
#             recipient_address=recipient,
#             follow_shipment='true'
#         )
#         shipment_request.collection_date = self.date_object.date
#         services = client.get_available_services(shipment_request)
#         shipment_request.service_id = 101
#         self.shippingServiceName = services[0].name
#         self.shippingCost = services[0].cost
#         self.services = services
#         atest = [a for a in dir(shipment_request) if not a.startswith('__')]
#         return shipment_request
#
#     def Queue(self, shipment):
#         shipment_request = self.MakeRequest(self)
#         added_shipment = client.add_shipment(shipment_request)
#         self.added_shipment = added_shipment
#
#         print("\n", line, '\n-', self.customer, "|", self.boxes, "|",
#               self.addressObject.street, "|", self.date_object.date, "|",
#               self.shippingServiceName,
#               "| Price =",
#               self.shippingCost, '\n', line, '\n')
#
#         choice = "n"
#         while choice[0] not in ["q", "r", 'e']:
#             choice = input('- [Q]ueue, [R]estart, or [E]xit\n')
#             choice = str(choice[0].lower())
#             if choice[0] != "q":  # not quote
#                 if choice != 'r':  # not restart
#                     if choice != 'e':  # not exit either
#                         continue  # try again
#                     else:  # exit
#                         if str(input("[E]xit?"))[0].lower() == 'e':  # comfirn exit
#                             self.LogJson(shipment)
#                             exit()
#                         continue
#                 else:  # restart
#                     if str(input("[R]estart?"))[0].lower() == 'r':  # confirm restart
#                         print("Restarting")
#                         self.Process(self)
#                     continue  # not restarting
#             print("Adding Shipment to Despatchbay Queue")
#             return shipment
#
#     def BookCollection(self, shipment):
#         client.book_shipments(self.added_shipment)
#         shipment_return = client.get_shipment(self.added_shipment)
#
#         label_pdf = client.get_labels(shipment_return.shipment_document_id)
#         pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)
#         label_string = ""
#         label_string = label_string + self.customer + "-" + str(self.date_object.date) + ".pdf"
#         print(label_string)
#         print(type(label_string))
#         label_pdf.download(LABEL_DIR / label_string)
#         trackingNumbers = []
#         for parcel in shipment_return.parcels:
#             trackingNumbers.append(parcel.tracking_number)
#
#         self.shipment_return = shipment_return
#         self.shipment_doc_id = shipment_return.shipment_document_id
#         self.label_url = shipment_return.labels_url
#         self.parcels = shipment_return.parcels
#         self.tracking = trackingNumbers
#         self.label_location = str(LABEL_DIR) + label_string
#
#         self.collection_booked = True
#         self.label_downloaded = True
#         print("Shipment for ", self.customer, "has been booked, Label downloaded to", self.label_location)
#         self.LogJson(self)
#         exit()
#
#     def LogJson(self, shipment):
#         export_dict = {}
#         export_keys = [k for k in dir(shipment) if
#                        not k.startswith('__') and k not in export_exclude_keys and getattr(shipment, k)]
#
#         self.send_date = self.send_date.strftime('%d/%m/%Y')
#         for key in export_keys:
#             export_dict.update({key: getattr(shipment, key)})
#         with open(DATA_DIR / 'AmShip.json', 'w') as f:
#             json.dump(export_dict, f, sort_keys=True)
#             print("Data dumped to json:", export_keys)
#         return
#
# #
# #         if d is not None:
# #             for k,v in d.items():
# #                 setattr(self,k,v)
# #
# # class MyClass(object):
# #     def __init__(self, number):
# #         self.number = number
# #
# # my_objects = []
# #
# # for i in range(len()):
# #     my_objects.append(MyClass(i))
# # for obj in my_objects:
# #     print (obj.number)
# #
# # class MyClass(object): pass
# # objs = [MyClass() for i in range(10)]
# # print(objs)
