import ctypes
import json
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Callable

import PySimpleGUI as sg
import requests
import win32com.client
from despatchbay.despatchbay_entities import Address, CollectionDate

from core.entities import ApiScope, FieldsList, DateTimeMasks

logger = logging.getLogger(__name__)
# def print_label(shipment):
#     """ prints the labels stored at shipment.label_location """
#     try:
#         os.startfile(str(shipment.label_location), "print")
#     except Exception as e:
#         shipment.is_printed = False
#         logger.warning(f"Failed to print label: {e}")
#         return False
#     else:
#         shipment.is_printed = True
#         return True
def print_label2(file_path:Path):
    """ prints the labels stored at shipment.label_location """
    try:
        os.startfile(str(file_path), "print")
    except Exception as e:
        logger.warning(f"Failed to print: {e}")
        return False
    else:
        return True



def email_label(shipment: 'ShipmentBooked', body: str, collection_date: CollectionDate, collection_address: Address):
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
    # else:
        # newmail.Send()
    # return True


def retry_with_backoff(fn:Callable, retries=5, backoff_in_seconds=1, *args, **kwargs):
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


def is_connected():
    url = "https://www.google.com"
    timeout = 5
    try:
        request = requests.get(url, timeout=timeout)
        logger.debug("Internet is on")

    except (requests.ConnectionError, requests.Timeout) as exception:
        input_blah = input(f"\n\nCONNECTION ERROR: UNABLE TO CONNECT TO GOOGLE: \n(enter to exit...)")
        logger.error(exception)
        sys.exit(404)

    return True


def run_as_admin(cmd):
    """
    Run the given command as administrator
    """
    if ctypes.windll.shell32.IsUserAnAdmin():
        return subprocess.run(cmd, shell=True)
    else:
        return subprocess.run(
            ["powershell.exe", "-Command", f"Start-Process '{cmd[0]}' -ArgumentList '{' '.join(cmd[1:])}' -Verb RunAs"],
            shell=True)


def set_despatch_env(api_user, api_key, sandbox):
    api_user_str = 'DESPATCH_API_USER'
    if sandbox:
        api_user_str += '_SANDBOX'

    api_key_str = 'DESPATCH_API_KEY'
    if sandbox:
        api_key_str += '_SANDBOX'
    #
    # cmd1 = ["setx", api_user_str, api_user, "/M"]
    # cmd2 = ["setx", api_key_str, api_key, "/M"]

    cmd3 = [["setx", api_user_str, api_user, "/M"], ["setx", api_key_str, api_key, "/M"]]

    # result1 = run_as_admin(cmd1)
    # if result1.returncode != 0:
    #     logger.error("Error:", result1.stderr)
    # else:
    #     logger.info(f"Environment variable set: {api_user_str} : {api_user}")
    #
    # result2 = run_as_admin(cmd2)
    # if result2.returncode != 0:
    #     logger.error("Error:", result2.stderr)
    # else:
    #     logger.info(f"Environment variable set: {api_key_str} : {api_key}")

    result2 = run_as_admin(cmd3)
    if result2.returncode != 0:
        logger.error("Error:", result2.stderr)
    else:
        logger.info(f"Environment variable set: {api_key_str} : {api_key}")


def scope_from_sandbox_func(sandbox):
    return ApiScope.SAND.value if sandbox else ApiScope.PRODUCTION.value
