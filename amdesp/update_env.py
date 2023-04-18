import enum
import os
import subprocess
import sys
import ctypes

class SW(enum.IntEnum):
    HIDE = 0
    MAXIMIZE = 3
    MINIMIZE = 6
    RESTORE = 9
    SHOW = 5
    SHOWDEFAULT = 10
    SHOWMAXIMIZED = 3
    SHOWMINIMIZED = 2
    SHOWMINNOACTIVE = 7
    SHOWNA = 8
    SHOWNOACTIVATE = 4
    SHOWNORMAL = 1


class ERROR(enum.IntEnum):
    ZERO = 0
    FILE_NOT_FOUND = 2
    PATH_NOT_FOUND = 3
    BAD_FORMAT = 11
    ACCESS_DENIED = 5
    ASSOC_INCOMPLETE = 27
    DDE_BUSY = 30
    DDE_FAIL = 29
    DDE_TIMEOUT = 28
    DLL_NOT_FOUND = 32
    NO_ASSOC = 31
    OOM = 8
    SHARE = 26


def set_despatch_api_env(api_user, api_key, sandbox=False):
    if ctypes.windll.shell32.IsUserAnAdmin():
        main(api_user=api_user, api_key=api_key, sandbox=sandbox)
    else:
        hinstance = ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, sys.argv[0], None, SW.SHOWNORMAL
        )
        if hinstance <= 32:
            raise RuntimeError(ERROR(hinstance))


def main(api_user, api_key, sandbox):
    for api_details in zip(('user', 'key'), (api_user, api_key)):
        key_name = f'DESPATCH_API_{api_details[0]}'.upper()
        key_value = api_details[1]
        if sandbox:
            key_name += '_SANDBOX'
        subprocess.call(f'SETX {key_name} {key_value} /M')

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

