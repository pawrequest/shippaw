import json
import subprocess
from enum import Enum

from core.config import logger

class PS_FUNCS(Enum):
    OVERWRITE="EditOverwrite"
    APPEND = "EditAppend"
    NEW = "NewRecord"
    HIRES_CUSTOMER= "HiresByCustomer"
    PRINT = "PrintRecord"

def edit_commence(pscript:str, function:str, table:str, record:str, package:dict):
    logger.info(f'COMMENCE UPDATER -{function=} -{table=} -{record=} -{package=}')
    record_esc = f'"{record}"'
    package_esc = json.dumps(package)#.replace('"', '`"')
    # package_esc = f'"{package_esc}"'
    # process_command = [powershell, '-ExecutionPolicy', 'Unrestricted', '-File',
    #                     pscript, function, table, record_esc, package_esc]

    process_command = ["powershell.exe", '-ExecutionPolicy', 'Unrestricted',
        '-File', pscript,
        '-functionName', function,
        '-tableName', table,
        # '-recordName', record_esc,
        '-recordName', record,
        '-updatePackageStr', package_esc
    ]
    process_result = subprocess.run(process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)
    if process_result.stderr:
        parse_std_err(process_result)
    else:
        stdoutput = process_result.stdout.split('\n')
        [logger.info(f'COMMENCE UPDATER - {i}') for i in stdoutput]

    return process_result




class Commence():
    def __init__(self, script):
        self.cmc_updater_script = script
        self.powershell_path = "powershell.exe"

    def get_record(self, table_name, record_name):
        record_name_esc = f'"{record_name}"'
        process_command = [self.powershell_path, '-ExecutionPolicy', 'Unrestricted', '-Command',
                           self.cmc_updater_script, table_name, record_name_esc]
        logger.info(f'LAUNCH CMD POWERSHELL: {process_command}')

        process_result = subprocess.run(process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        universal_newlines=True)
        logger.info(f'POWERSHELL RESULT: {process_result.returncode}')

    def update_record(self, tablename, recordname, update_package):
        ...

    class Record:
        def __init__(self, tablename, recordname):
            self.tablename = tablename
            self.recordname = recordname
            self.update_package = {}

        @property
        def name_esc(self):
            return f'"{self.recordname}"'

#
#
# def update_commence(table_name: str, record_name: str, update_package: dict, script_path: str,
#                     append: bool = False, insert:bool=False):
#     """ Update commence record via powershell
#     :param table_name: name of commence table
#     :param update_package: dict of vey value pairs to update
#     :param record_name_esc: name of record to update
#     :param script_path: path to powershell script
#     :param append: append to existing record data or overwrite
#     :param insert: insert new record"""
#
#     POWERSHELL_PATH = "powershell.exe"
#     record_name_esc = f'"{record_name}"'
#
#     update_string_esc = json.dumps(update_package).replace('"', '`"')
#     update_string_esc = f'"{update_string_esc}"'
#
#     process_command = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', '-Command',
#                        script_path, table_name, record_name_esc, update_string_esc]
#     if append:
#         process_command.append('-append')
#
#     if insert:
#         if input(f"Create New Record {record_name} in {table_name}? (y/n)").lower() == 'y':
#             process_command.append('-insert')
#             # process_command = ['cmd.exe', '/c', 'start', '/wait'] + process_command
#     logger.info(f'LAUNCH CMD POWERSHELL: {process_command}')
#
#     process_result = subprocess.run(process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
#                                     universal_newlines=True)
#     logger.info(f'POWERSHELL RESULT: {process_result.returncode}')
#
#     if process_result.stderr:
#         parse_std_err(process_result)
#     else:
#         stdoutput = process_result.stdout.split('\n')
#         [logger.info(f'COMMENCE UPDATER - {i}') for i in stdoutput]


def parse_std_err(process_result):
    print(process_result.stderr)
    if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
        logger.warning(f'CmCLibNet is not installed : {process_result.stderr}')
    # todo install cmclibnet and retry
    if "ERROR: Filters.Apply returned" in process_result.stderr:
        if "ERROR: Filters.Apply returned 0 results" in process_result.stderr:
            logger.warning(f'No records found in Commence : {process_result.stderr}')
        else:
            logger.warning(f'Multiple records found, Std Error: {process_result.stderr}')
    else:
        logger.warning(f'Commence Updater failed, Std Error: {process_result.stderr}')
