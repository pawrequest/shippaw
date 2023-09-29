import json
import logging
import subprocess
from enum import Enum

logger = logging.getLogger(__name__)


class PS_FUNCS(Enum):
    OVERWRITE = "EditOverwrite"
    APPEND = "EditAppend"
    NEW = "NewRecord"
    HIRES_CUSTOMER = "HiresByCustomer"
    PRINT = "PrintRecord"


def edit_commence(pscript: str, function: str, table: str, record: str, package: dict):
    record_esc = f'"{record}"'
    package_esc = json.dumps(package)  # .replace('"', '`"')
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
        logger.info(f'COMMENCE UPDATER:\n{process_result.stdout}')
    return process_result



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




#
#
# class Commence():
#     def __init__(self, script):
#         self.cmc_updater_script = script
#         self.powershell_path = "powershell.exe"
#
#     def get_record(self, table_name, record_name):
#         record_name_esc = f'"{record_name}"'
#         process_command = [self.powershell_path, '-ExecutionPolicy', 'Unrestricted', '-Command',
#                            self.cmc_updater_script, table_name, record_name_esc]
#         logger.debug(f'LAUNCH CMD POWERSHELL: {process_command}')
#
#         process_result = subprocess.run(process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
#                                         universal_newlines=True)
#         logger.debug(f'POWERSHELL RESULT: {process_result.returncode}')
#
#     def update_record(self, tablename, recordname, update_package):
#         ...
#
#     class Record:
#         def __init__(self, tablename, recordname):
#             self.tablename = tablename
#             self.recordname = recordname
#             self.update_package = {}
#
#         @property
#         def name_esc(self):
#             return f'"{self.recordname}"'
#
