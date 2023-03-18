from dateutil.parser import parse
from datetime import datetime

import PySimpleGUI as sg
from .gui_layouts import GuiLayout
DT_DB = '%Y-%m-%d'


class AmdespGui:
    def __init__(self, shipment):
        self.shipment = shipment
        self.layouts = GuiLayout(self)
        self.dialogues = Dialogues(self)

class Dialogues:
    def __init__(self, parent):
        self.shipment = parent.shipment

    def boxes_dialogue(self):
        shipment = self.shipment
        boxes = shipment.boxes
        client = shipment.CNFG.client
        layout = [
            [sg.Text(f"{boxes} box(es) assigned for {shipment.customer}")],
            [sg.Text("Adjust the number of boxes:")],
            [sg.InputText()],
            [sg.Submit(), sg.Cancel()]
        ]
        window = sg.Window("Boxes Dialogue", layout)

        while True:
            event, values = window.read()

            if event == sg.WINDOW_CLOSED or event == "Cancel":
                window.close()

            user_input = values[0]

            match user_input:
                case "":
                    ...
                case str(number) if number.isnumeric():
                    boxes = int(number)
                    # sg.popup(f"Shipment updated to {updated_boxes} boxes") # something else
                case _:
                    sg.popup("Invalid input, please enter a number or leave blank.")

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
            window.close()
            shipment.parcels = parcels
            return

    def address_dialogue(self):
        shipment = self.shipment
        client = shipment.CNFG.client

        layout = GuiLayout(shipment).shipment_details()
        window = sg.Window("Address Dialogue", layout)
        ...




        # if shipment.address_from_postcode_and_string(shipment.delivery_postcode,shipment.search_term)

    def date_dialogue(self):
        shipment = self.shipment
        client = shipment.CNFG.client
        if shipment.is_return:
            send_date_obj = datetime.today()
            send_date = f"{datetime.today():{DT_DB}}"
        else:
            send_date_obj = parse(shipment.send_out_date)
            send_date = datetime.strftime(send_date_obj, DT_DB)


        available_dates = shipment.available_dates
        default_date = None
        for a in available_dates:
            if a.date == send_date_obj.date():
                default_date = a.date
                break

        if default_date is None:
            default_date = available_dates[0].date


        radio_buttons = [[sg.Radio(str(a.date), group_id="date", default=a.date == default_date)] for a in
                         available_dates
                         ]
        layout = [[sg.Text("Please select a date:")],
                  *radio_buttons,
                  [sg.Submit(), sg.Cancel()]
                  ]
        window = sg.Window("Date Dialogue", layout)

        while True:
            event, values = window.read()
            match event:
                case sg.WINDOW_CLOSED | 'Cancel':
                    window.close()
                    exit()
                case 'Submit':
                    chosen_date = None
                    for i, date_obj in enumerate(available_dates):
                        if i:
                            shipment.date = available_dates[i]
                            window.close()
                            return
                    else:
                        sg.popup('Please select a date')


