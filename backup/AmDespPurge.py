#########################################################
# #########   CLASSES PURGE#
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
#     elif not self.dateObject: print("\n*** ERROR: No collections available on", self.sendOutDate, "for", self.Customer, " ***")
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

# def process_shipment(self):
    #     if self.deliveryBuildingNum:
    #         print("Building No. Found, address search using no.", self.deliveryBuildingNum)
    #     else: print("- No building number, address search using deliveryFirstline:", self.deliveryFirstline)
    #     if self.dateObject:
    #         print("Send-Out date validated - collection on:", self.dateObject.date)
    #     else:
    #         self.val_dates()
    #     self.val_boxes()
    #     self.val_address()
    #     self.change_add()
    #     self.make_request()

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

######### END PURGE #####################
#######################################

#####################################
######### FUNCS PURGE ###############
# def JsonToShippies(jsondata):
#     shippies = []
#     manifest = manifestFromJson(jsondata)
#     for shipment in manifest:
#         shippies.append(Shipment(shipment, shipment['id']))
#     print("SHIPPIES:", shippies)
#     return shippies

#
# def XmlToShippy(xmlda):  # xmldata name being used?
#     shipment = shipmentFromXml(xmlda)
#     shippy = Shipment(shipment, shipment['Customer'])
#     print("Shippy:", shippy)
#     return shippy


# def shipmentFromXml(xml):  # currently hardcoded xml link.... breaks otherwise... how to passfile refs/paths?
#     # TODO handle xmls with multiple shipments
#     shipment = {}
#     newxml = "C:\AmDesp\sheets\AmShip.xml"
#     tree = ET.parse(CONFIG_PATH['XMLCUSTOMERSTRMERSTR0'])
#     root = tree.getroot()
#     fields = root[0][2]
#     # add shipment-wide
#
#     customer = root[0][3].text  # debug
#
#     cat = root[0][0].text
#     shipment['category'] = cat
#     shipment['Customer'] = customer
#     for field in fields:
#         k = field[0].text
#         v = field[1].text
#         if v:
#             shipment.update({k: v})
#     shipment = cleanDictShip(shipment)
#     print("Xml shipment with", len(shipment), "fields imported")
#     return shipment
