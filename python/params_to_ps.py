import pathlib
import subprocess, sys
from pprint import pprint
from config import *
import subprocess









ps = pathlib.Path(ROOT_DIR / 'python' / 'ps_test.ps1')

def runtingz(script_path, *args, **kwargs):
    commandline_options = ['powershell.exe', '-ExecutionPolicy', 'Unrestricted',
                           script_path]  # ADD POWERSHELL EXE AND EXECUTION POLICY TO COMMAND VARIABLE
    for param in args:
        #commandline_options.append(param)
        #commandline_options.append("'" + param + "'")
        for thing in param:
            new_param = "'"+thing+"'"
            commandline_options.append(new_param)
    process_result = subprocess.run(commandline_options, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)  # CALL PROCESS
    print(process_result.returncode)
    print(process_result.stdout)
    print(process_result.stderr)

    if process_result.returncode == 0:  # COMPARING RESULT
        Message = "Success !"
    else:
        Message = "Error Occurred !"
    print(Message)

power = runtingz(ps, parameters)