import PySimpleGUI as sg


# boxes
# dates
# address
class GuiLayout:
    def __init__(self, parent):
        self.shipment = parent.shipment
        self.layout = None

    def address_frame(self):
        layout = [[sg.Text('Company Name:'), sg.InputText(key='company_name')],
                  [sg.Text('Street:'), sg.InputText(key='street')],
                  [sg.Text('Town/City:'), sg.InputText(key='town_city')],
                  [sg.Text('Locality:'), sg.InputText(key='locality')],
                  [sg.Text('Postcode:'), sg.InputText(key='postcode')],
                  [sg.Text('Country:'), sg.InputText(key='country')]]

        return layout

    def sender_recipient_frame(self, title):
        address_layout = self.address_frame()

        layout = [[sg.Text(f'{title} Name:'), sg.InputText(key=f'{title.lower()}_name')],
                  [sg.Text(f'{title} Email:'), sg.InputText(key=f'{title.lower()}_email')],
                  [sg.Text(f'{title} Phone:'), sg.InputText(key=f'{title.lower()}_phone')],
                  address_layout]

        return layout

    def shipment_details_frame(self):
        layout = [[sg.Text('Shipment Name:'), sg.InputText(key='shipment_name')],
                  [sg.Text('Customer:'), sg.InputText(key='customer')],
                  [sg.Text('Category:'), sg.InputText(key='category')],
                  [sg.Text('Boxes:'), sg.InputText(key='boxes')]]

        return layout

    def service_frame(self):
        layout = [[sg.Text('Service Name:'), sg.InputText(key='service_name')],
                  [sg.Text('Service ID:'), sg.InputText(key='service_id')],
                  [sg.Text('Service Cost:'), sg.InputText(key='service_cost')]]

        return layout

    def blank_frame(self):
        return sg.Frame("", [[]], pad=(5, 3), expand_x=True, expand_y=True, background_color='#404040', border_width=0)

    def main_frame(self):
        # sender_frame = sg.Frame('Sender', self.sender_recipient_frame('Sender'))
        # recipient_frame = sg.Frame('Recipient', self.sender_recipient_frame('Recipient'))
        # shipment_details_frame = sg.Frame('Shipment Details', self.shipment_details_frame())
        # service_frame = sg.Frame('Service', self.service_frame())

        layout_addresses = [
            [sg.Frame("Sender", self.sender_recipient_frame("Sender")),
            sg.Frame("Recipient", self.sender_recipient_frame("Recipient"))]
        ]

        layout_frame1 = [
            [self.blank_frame(), self.blank_frame()],
            [sg.Frame("Frame 3", [[self.blank_frame()]], pad=(5, 3), expand_x=True, expand_y=True)],
        ]

        layout=[]
        return layout

    def shipment_formatter(self, name):
        standard_width = 23
        dots = standard_width - len(name) - 2
        return sg.Text(name + ' ' + ' ' * dots, size=(standard_width, 1), justification='r', pad=(0, 0),
                       font='Courier 10')

    def shipment_details(self):
        shipment = self.shipment
        layout = []
        for attr in shipment.CNFG.gui_fields:
            if attr in vars(shipment):
                val = getattr(shipment, attr, None)
                human_readable_attr = shipment.CNFG.gui_map.get(attr, attr.title())
                layout.append([sg.Text({human_readable_attr}),sg.InputText(default_text=getattr(shipment, attr))])
                # [sg.Text('Company Name'),
                #  sg.InputText(default_text=default_values['company_name'], key='company_name')],
        return layout

    def boxes(self):
        boxes = self.shipment.boxes
        self.layout = [
            [sg.Text(f"{boxes} box(es) assigned for shipment")],
            [sg.Text("Adjust the number of boxes:")],
            [sg.InputText(str(boxes), key="boxes")],
            [sg.Button("Confirm"), sg.Button("Cancel")]
        ]

    def dialogue_window(self):
        shipment=self.shipment
        # Shipment Dialogue Window
        shipment_dialogue_layout = GuiLayout(shipment)
        shipment_dialogue_layout.boxes()
        dialogue_layout = shipment_dialogue_layout.layout

        shipment_dialogue_window = sg.Window("Shipment Dialogue", dialogue_layout, finalize=True)
        return shipment_dialogue_window








