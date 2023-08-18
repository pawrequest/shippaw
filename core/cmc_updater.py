import json
import subprocess

from core.config import logger


def update_commence(update_package: dict, table_name: str, record_name: str, script_path: str, append: bool = False,
                    insert=False):
    """ Update commence record via powershell
    :param update_package: dict of vey value pairs to update
    :param table_name: name of commence table
    :param record_name_esc: name of record to update
    :param script_path: path to powershell script
    :param append: append to existing record data or overwrite
    :param with_shell: use shell to confirm update
    :param insert: insert new record (vs edit existing)"""

    POWERSHELL_PATH = "powershell.exe"
    record_name_esc = f'"{record_name}"'
    update_string_esc = json.dumps(update_package).replace('"', '`"')
    update_string_esc = f'"{update_string_esc}"'
    process_command = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', '-Command',
                       script_path, table_name, record_name_esc, update_string_esc]
    if append:
        process_command.append('-append')

    if insert:
        if input(f"Create New Record {record_name} in {table_name}? (y/n)").lower() == 'y':
            process_command.append('-insert')
            process_command = ['cmd.exe', '/c', 'start', '/wait'] + process_command

    logger.info(f'LAUNCH CMD POWERSHELL: {process_command}')

    process_result = subprocess.run(process_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)

    logger.info(f'POWERSHELL RESULT: {process_result.returncode}')

    parse_std_err(process_result) if process_result.stderr \
        else print(process_result.stdout)


def parse_std_err(process_result):
    if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
        logger.warning(f'CmCLibNet is not installed : {process_result.stderr}')
    # todo install cmclibnet and retry
    if "ERROR: Filters.Apply returned " in process_result.stderr:
        if "ERROR: Filters.Apply returned 0 results" in process_result.stderr:
            logger.warning(f'No records found in Commence : {process_result.stderr}')
        else:
            logger.warning(f'Multiple records found, Std Error: {process_result.stderr}')
    else:
        raise RuntimeError(f'Commence Updater failed, Std Error: {process_result.stderr}')
