import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import PySimpleGUI as sg
import win32com.client
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document

from core.config import Config
from core.enums import FieldsList, DateTimeMasks
from shipper.shipment import Shipment, logger


def print_label(shipment):
    """ prints the labels stored at shipment.label_location """
    try:
        os.startfile(str(shipment.label_location), "print")
    except Exception as e:
        return False
    else:
        shipment.printed = True
        return True


def log_shipment(config: Config, shipment: Shipment):
    # export from object attrs
    shipment.boxes = len(shipment.parcels)
    export_dict = {}

    for field in FieldsList.export.value:
        try:
            if field == 'sender':
                val = shipment.sender.__repr__()
            elif field == 'recipient':
                val = shipment.recipient.__repr__()
            else:
                val = getattr(shipment, field)
                if isinstance(val, datetime):
                    val = f"{val.isoformat(sep=' ', timespec='seconds')}"

            export_dict.update({field: val})
        except Exception as e:
            print(f"{field} not found in shipment \n{e}")

    with open(config.paths.log_json, 'a') as f:
        # todo better loggging.... sqlite?
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")


def email_label(recipient: str, body: str, attachment: Path):
    ol = win32com.client.Dispatch('Outlook.Application')
    newmail = ol.CreateItem(0)

    newmail.Subject = 'Radio Return - Shipping Label Attached'
    newmail.To = recipient
    newmail.Body = body
    attach = str(attachment)

    newmail.Attachments.Add(attach)
    newmail.Display()  # preview
    # newmail.Send()


def download_label(client: DespatchBaySDK, config: Config, shipment: Shipment):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in user_config.toml"""
    try:
        label_pdf: Document = client.get_labels(document_ids=shipment.shipment_return.shipment_document_id,
                                                label_layout='2A4')

        label_string: str = shipment.shipment_name_printable + '.pdf'
        shipment.label_location = config.paths.labels / label_string
        label_pdf.download(shipment.label_location)
    except:
        return False
    else:
        return True


def powershell_runner(script_path: str, *params: str):
    POWERSHELL_PATH = "powershell.exe"

    commandline_options = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', script_path]
    for param in params:
        commandline_options.append("'" + param + "'")
    logger.info(f'POWERSHELL RUNNER - COMMANDS: {commandline_options}')
    process_result = subprocess.run(commandline_options, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)
    logger.info(f'POWERSHELL RUNNER - PROCESS RESULT: {process_result}')
    if process_result.stderr:
        if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
            raise RuntimeError('CmCLibNet is not installed')
        else:
            raise RuntimeError(f'Std Error = {process_result.stderr}')
    else:
        return process_result.returncode


def update_commence(config: Config, shipment: Shipment, id_to_pass: str):
    """ runs cmclibnet via powershell script to add shipment_id to commence db """

    ps_script = str(config.paths.cmc_logger)
    try:  # utility class static method runs powershell script bypassing execuction policy
        commence_edit = powershell_runner(ps_script, shipment.category, shipment._shipment_name, id_to_pass,
                                          str(config.outbound))
    except RuntimeError as e:
        logger.exception('Error logging to commence')
        sg.popup_scrolled(f'Error logging to commence - is it running?')
        shipment.logged_to_commence = False
    else:
        if commence_edit == 0:
            shipment.logged_to_commence = True
    return shipment.logged_to_commence


def check_today_ship(shipment):
    keep_shipment = True
    if shipment.send_out_date == datetime.today().date() and datetime.now().hour > 12:
        keep_shipment = True if sg.popup_ok_cancel(
            f"Warning - Shipment Send Out Date is today and it is afternoon\n"
            f"{shipment.shipment_name_printable} would be collected on {datetime.strptime(shipment.collection_date.date, DateTimeMasks.DB.value):{DateTimeMasks.DISPLAY.value}}.\n"
            "'Ok' to continue, 'Cancel' to remove shipment from manifest?") == 'Ok' else False

    logger.info(f'PREP SHIPMENT - CHECK TODAY SHIP {shipment.send_out_date}')
    return shipment if keep_shipment else None
