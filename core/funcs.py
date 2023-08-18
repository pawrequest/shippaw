import json
import os
import random
import shlex
import subprocess
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from pprint import pprint

import PySimpleGUI as sg
import win32com.client
from despatchbay.despatchbay_entities import Address, CollectionDate

from core.config import logger
from core.enums import FieldsList, DateTimeMasks
from shipper.shipment import Shipment


def print_label(shipment):
    """ prints the labels stored at shipment.label_location """
    try:
        os.startfile(str(shipment.label_location), "print")
    except Exception as e:
        logger.warning(f"Failed to print label: {e}")
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
    pprint(export_dict)

    with open(log_path, 'a') as f:
        # todo better loggging.... sqlite?
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")


def email_label(shipment: Shipment, body: str, collection_date: CollectionDate, collection_address: Address):
    collection_date = collection_date_to_datetime(collection_date)

    try:
        ol = win32com.client.Dispatch('Outlook.Application')
        newmail = ol.CreateItem(0)

        col_address = f'{collection_address.company_name if collection_address.company_name else ""}'
        col_address += f'{collection_address.street}'

        body = body.replace("__--__ADDRESSREPLACE__--__", f'{col_address}')
        body = body.replace("__--__DATEREPLACE__--__", f'{collection_date:{DateTimeMasks.DISPLAY.value}}')

        newmail.To = shipment.email
        newmail.Subject = "Radio Hire Return - Shipping Label Attached"
        newmail.Body = body
        attach = str(shipment.label_location)

        newmail.Attachments.Add(attach)
        newmail.Display()  # preview
    except Exception as e:
        logger.warning(f"Failed to email label: {e}")
        return False
    # newmail.Send()


#
# def update_commence_f(update_package: dict, table_name: str, record_name: str, script_path: str):
#     """silently update commence record via powershell """
#     POWERSHELL_PATH = "powershell.exe"
#     update_string = json.dumps(update_package)
#     powershell_command = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', '-file',
#                          script_path, table_name, record_name, update_string]
#     logger.info(f'UPDATE COMMENCE VIA POWERSHELL - COMMANDS: {powershell_command}')
#
#     process_result = subprocess.run(powershell_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
#                                     universal_newlines=True)
#     if process_result.stderr:
#         if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
#             logger.warning(f'CmCLibNet is not installed : {process_result.stderr}')
#         #todo install cmclibnet and retry
#         else:
#             raise RuntimeError(f'Commence Updater failed, Std Error: {process_result.stderr}')
#     else:
#         print(process_result.stdout)

#
# def update_commence_shell(update_package: dict, table_name: str, record_name: str, script_path: str):
#     POWERSHELL_PATH = "powershell.exe"
#     record_name = f'"{record_name}"'
#     update_string = json.dumps(update_package).replace('"', '`"')
#     update_string = f'"{update_string}"'
#     powershell_command = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', '-Command',
#                          script_path, table_name, record_name, update_string]
#
#     cmd_command = ['cmd.exe', '/c', 'start', '/wait'] + powershell_command
#     logger.info(f'LAUNCH CMD POWERSHELL: {cmd_command}')
#     process_result = subprocess.run(cmd_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#     logger.info(f'POWERSHELL RESULT: {process_result}')
#
#
#     if process_result.stderr:
#         if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
#             logger.warning(f'CmCLibNet is not installed : {process_result.stderr}')
#         #todo install cmclibnet and retry
#         else:
#             raise RuntimeError(f'Commence Updater failed, Std Error: {process_result.stderr}')
#     else:
#         print(process_result.stdout)

def update_commence(update_package: dict, table_name: str, record_name: str, script_path: str, with_shell: bool = False):
    """ Update commence record via powershell, with or without shell for confirmation dialogue
    :param update_package: dict of vey value pairs to update"""
    POWERSHELL_PATH = "powershell.exe"
    record_name = f'"{record_name}"'
    update_string = json.dumps(update_package).replace('"', '`"')
    update_string = f'"{update_string}"'
    process_command = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', '-Command',
                         script_path, table_name, record_name, update_string]
    if with_shell:
        process_command = ['cmd.exe', '/c', 'start', '/wait'] + process_command

    logger.info(f'LAUNCH CMD POWERSHELL {with_shell=}: {process_command}')

    process_result = subprocess.run(process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    logger.info(f'POWERSHELL RESULT: {process_result.returncode}')


    if process_result.stderr:
        if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
            logger.warning(f'CmCLibNet is not installed : {process_result.stderr}')
        #todo install cmclibnet and retry
        else:
            raise RuntimeError(f'Commence Updater failed, Std Error: {process_result.stderr}')
    else:
        print(process_result.stdout)


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
            sleep = (backoff_in_seconds * 2 ** x + random.uniform(0, 1))
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


def collection_date_to_datetime(collection_date: CollectionDate):
    return datetime.strptime(collection_date.date, DateTimeMasks.DB.value).date()
