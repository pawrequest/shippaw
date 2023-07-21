import json
import os
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path

import PySimpleGUI as sg
import win32com.client
from despatchbay.despatchbay_entities import ShipmentReturn, Address
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document

from core.enums import FieldsList, DateTimeMasks
from shipper.shipment import Shipment


from core.config import logger


def print_label(shipment):
    """ prints the labels stored at shipment.label_location """
    try:
        os.startfile(str(shipment.label_location), "print")
    except Exception as e:
        return False
    else:
        shipment.printed = True
        return True


def log_shipment(log_path, shipment: Shipment):
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

    with open(log_path, 'a') as f:
        # todo better loggging.... sqlite?
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")


def email_label(shipment: Shipment, body: str, collection_date: datetime.date, collection_address: Address):
    collection_date = collection_date
    collection_address = collection_address
    ol = win32com.client.Dispatch('Outlook.Application')
    newmail = ol.CreateItem(0)

    col_address = f'{collection_address.company_name if collection_address.company_name else ""}'
    col_address += f'{collection_address.street}'

    body = body.replace("ADDRESSREPLACE", f'{col_address}')
    body = body.replace("DATEREPLACE", f'{collection_date:{DateTimeMasks.DISPLAY}}')

    newmail.To = shipment.email
    newmail.Subject = "Radio Hire Return - Shipping Label Attached"
    newmail.Body = body
    attach = str(shipment.label_location)

    newmail.Attachments.Add(attach)
    newmail.Display()  # preview
    # newmail.Send()


def download_label_2(client: DespatchBaySDK, label_folder_path: Path, label_text: str, shipment_return: ShipmentReturn):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in user_config.toml"""
    try:
        label_pdf: Document = client.get_labels(document_ids=shipment_return.shipment_document_id,
                                                label_layout='2A4')

        label_string: str = label_text + '.pdf'
        label_location = label_folder_path / label_string
        label_pdf.download(label_location)
    except:
        return False
    else:
        return label_location


def download_label(client: DespatchBaySDK, label_folder_path: Path, shipment: Shipment):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in user_config.toml"""
    try:
        label_pdf: Document = client.get_labels(document_ids=shipment.shipment_return.shipment_document_id,
                                                label_layout='2A4')

        label_string: str = shipment.shipment_name_printable + '.pdf'
        label_location = label_folder_path / label_string
        label_pdf.download(label_location)
    except:
        return False
    else:
        return label_location


def powershell_runner(script_path: str, *params):
    POWERSHELL_PATH = "powershell.exe"

    commandline_options = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', script_path]
    for param in params:
        commandline_options.append("'" + param + "'")
    # commandline_options.extend(params)
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



def update_commence(shipment: Shipment, id_to_pass: str, outbound: bool, ps_script: Path):
    """ runs cmclibnet via powershell script to add shipment_id to commence db """

    try:
        commence_edit = powershell_runner(str(ps_script), shipment.category, shipment._shipment_name, id_to_pass,
                                          str(outbound))
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



def retry_with_backoff(fn, retries=5, backoff_in_seconds=1, *args, **kwargs, ):
    x = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.info(f" {fn.__name__=} failed with {str(e)}")
            if x == retries:
                sg.popup_error(f'Error, probably API rate limit, retries exhausted')
                logger.info("Retries exhausted")
                raise
            sleep = (backoff_in_seconds * 2**x + random.uniform(0, 1))
            sg.popup_quick_message(f'Error, probably API rate limit, retrying in {sleep:.0f} seconds')
            logger.info(f"Retrying {fn.__name__} after {sleep} seconds")
            time.sleep(sleep)
            x += 1


def retry_with_backoff_dec(retries=5, backoff_in_seconds=1):
    def rwb(f):
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return f(*args, **kwargs)
                except:
                    if x == retries:
                        raise

                    sleep = (backoff_in_seconds * 2 ** x +
                             random.uniform(0, 1))
                    time.sleep(sleep)
                    x += 1

        return wrapper

    return rwb

