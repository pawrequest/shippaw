import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass
from core.funcs import logger




date_range = 3
temp_file = 'temp_file.json'

stock_change = {}




def stock_check_script_runner(script_path: str, *params):
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



result = stock_check_script_runner(script_path='C:\paul\AmDesp\scripts\commence_playground.ps1', )



def get_dates(n):
    return [datetime.today() + timedelta(days=i) for i in range(n + 1)]


def get_hires_out(date):
    hires_out = ''
    return hires_out

def radios_out(hire):
    radio_type = 'hytera'
    num_radios = 3
    return radio_type, num_radios


dates = get_dates(date_range)
for date in dates:
    hires_out = get_hires_out(date)
    for hire in hires_out:
        radio_type, radio_num = radios_out(hire)
        stock_change[radio_type] = stock_change.get(radio_type, 0) - radio_num
        ...

...




...

