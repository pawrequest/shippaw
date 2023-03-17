import PySimpleGUI as sg
from .gui_layouts import GuiLayout


class AmdespGui:
    def __init__(self, shipment):
        import PySimpleGUI as sg
        shipment_details_layout = GuiLayout(shipment)
        shipment_details_layout.from_shipment()
        details_layout = shipment_details_layout.layout

        # define layout for shipment dialogue window
        shipment_dialogue_layout = GuiLayout(shipment)
        shipment_dialogue_layout.boxes()
        dialogue_layout = shipment_dialogue_layout.layout

        # create shipment details and dialogue windows
        shipment_details_window = sg.Window("Shipment Details", details_layout, finalize=True)
        shipment_dialogue_window = sg.Window("Shipment Dialogue", dialogue_layout, finalize=True)


        while True:
            event, values = shipment_dialogue_window.read()
            if event == sg.WINDOW_CLOSED or event == "Cancel":
                break
            elif event == "Submit":
                choice = values["choice"]
                break

        shipment_details_window.close()
        shipment_dialogue_window.close()
