import PySimpleGUI as sg


# boxes
# dates
# address
class GuiLayout:
    def __init__(self, shipment, rows=None):
        self.shipment = shipment
        self.title_font, self.field_font = "Rockwell 24", "Rockwell 16"
        self.title_bar = [sg.T('AmDesp Shipper', font=self.title_font, justification='c', expand_x=True)]
        self.layout = self.title_bar
        if rows:
            self.rows = rows
            self.layout.append(rows)

    def shipment_format(self, name):
        standard_width = 23
        dots = standard_width - len(name) - 2
        return sg.Text(name + ' ' + ' ' * dots, size=(standard_width, 1), justification='r', pad=(0, 0),
                       font='Courier 10')

    def from_shipment(self):
        shipment = self.shipment
        layout = [self.title_bar]
        for attr in shipment.CNFG.gui_fields:
            if attr in vars(shipment):
                val = getattr(shipment, attr, None)
                human_readable_attr = shipment.CNFG.gui_map.get(attr, attr.title())
                layout.append([self.shipment_format(human_readable_attr), sg.Text(val, key=attr)])
            elif attr in ['delivery_telephone']:
                print(f'{attr}')
        self.layout = layout
        return self.layout

    # def afun(self):
    #     shipment_details_layout = [
    #         [sg.Text("Service: "), sg.Text(key="service")],
    #         [sg.Text("Sender: "), sg.Text(key="sender")],
    #         [sg.Text("Recipient: "), sg.Text(key="recipient")],
    #         [sg.Text("Parcels: "), sg.Text(key="parcels")],
    #         [sg.Text("Collection booked: "), sg.Text(key="collection_booked")],
    #         [sg.Text("Label location: "), sg.Text(key="label_location")],
    #         [sg.Text("Shipping cost: "), sg.Text(key="shipping_cost")],
    #         [sg.Text("Tracking numbers: "), sg.Text(key="tracking_numbers")],
    #         [sg.Text("Date: "), sg.Text(key="date")],
    #     ]


    def boxes(self):
        boxes = self.shipment.boxes
        self.layout = [
            [sg.Text(f"{boxes} box(es) assigned for shipment")],
            [sg.Text("Adjust the number of boxes:")],
            [sg.InputText(str(boxes), key="boxes")],
            [sg.Button("Confirm"), sg.Button("Cancel")]
        ]


