# import ctypes
# import subprocess
#
# DESPATCH_API_KEY = '2DE45B0B5EDEB688841F'
# DESPATCH_API_KEY_SANDBOX = 'AAD2F91ED25CAE38B4D1'
# DESPATCH_API_USER = '25RM-EB372013'
# DESPATCH_API_USER_SANDBOX = 'D25RM-E1305A31'
# DESPATCH_SENDER_ID = 5536
#
# # set_despatch_api_env(api_user=DESPATCH_API_USER_SANDBOX, api_key=DESPATCH_API_KEY_SANDBOX, sandbox=True)
#
# # def is_admin():
# #     try:
# #         return ctypes.windll.shell32.IsUserAnAdmin()
# #     except:
# #         return False
# # for i in range(1,3):
# #     if not is_admin():
# #
# #         # Re-run the program with elevated privileges
# #         print("not admin")
# #
# #         # Exit the current process
# #         # sys.exit()
# #
# #     else:
# #         ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
# #
# #         # Set the environment variable permanently
# #         print("IS ADMIN")
# #
# #
# #
# # variable {key_name} set to {key_value}")
# from enum import Enum
#
#
# class ShipMode(Enum):
#     SHIP_OUT = 'ship_out'
#     SHIP_IN = 'ship_in'
#     TRACK_OUT = 'track_out'
#     TRACK_IN = 'track_in'
#
#
# mode = ShipMode('ship_in')
# ...
import logging
import sys

from amdesp.config import get_amdesp_logger

DESPATCH_API_USER = '25RM-EB372013'
DESPATCH_API_KEY = '2DE45B0B5EDEB688841F'
DESPATCH_API_USER_SANDBOX = 'D25RM-E1305A31'
DESPATCH_API_KEY_SANDBOX = 'AAD2F91ED25CAE38B4D1'
DESPATCH_SENDER_ID = 5536

import PySimpleGUI as sg
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK

logger = get_amdesp_logger()

ship_id = '100786-6099'
client = DespatchBaySDK(api_user=DESPATCH_API_USER_SANDBOX, api_key=DESPATCH_API_KEY_SANDBOX)

logger.info(f'TRACKING VIEWER GUI - SHIPMENT ID: {ship_id}')
shipment_return = client.get_shipment(ship_id)
tracking_numbers = [parcel.tracking_number for parcel in shipment_return.parcels]
tracking_d = {}
for tracked_parcel in tracking_numbers:
    params = {}
    signatory = None
    parcel_layout = []
    tracking = client.get_tracking(tracked_parcel)
    # courier = tracking['CourierName'] # debug unused?
    # parcel_title = [f'{tracked_parcel} ({courier}):'] # debug unused?
    history = tracking['TrackingHistory']

    for event in history:
        if 'delivered' in event.Description.lower():
            signatory = f"{chr(10)}Signed for by: {event.Signatory}"
            params.update({'background_color': 'aquamarine', 'text_color': 'red'})

        event_text = sg.T(
            f'{event.Date} - {event.Description} in {event.Location}{signatory if signatory else ""}',
            **params)
        parcel_layout.append([event_text])

    parcel_frame = [sg.Column(parcel_layout)]
    tracking_d.update({tracked_parcel: tracking})

shipment_return.tracking_dict = tracking_d
tracking_window = sg.Window('', [parcel_frame])
tracking_window.read()

#
#
#
# ship_id = '100786-6099'
# client = DespatchBaySDK(api_user=DESPATCH_API_USER_SANDBOX, api_key=DESPATCH_API_KEY_SANDBOX)
# dbay_account = client.get_account()
# shipment_return = client.get_shipment(ship_id)
# tracking_numbers = [parcel.tracking_number for parcel in shipment_return.parcels]
# layout = []
#
# for tracked_parcel in tracking_numbers:
#     parcel_lay = []
#     tracking = client.get_tracking(tracked_parcel)
#     history = tracking['TrackingHistory']
#
#     for event in history:
#         parcel_lay.append(sg.T('hello'))
#         logger.info(f'{layout=}')
#     parcel_frame = [sg.Frame('tracking frame', layout=[parcel_lay])]
#     layout.append(parcel_frame)
#
# tracking_window = sg.Window('', layout=layout)
# tracking_window.read()
