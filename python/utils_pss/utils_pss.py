import sys

import psutil
import win32gui

x="'delivery tel'"

def toPascal(x):
    x=x.title()
    for y in x:
        if not y.isalpha():
            if not y.isnumeric():
                x = x.replace(y,'')
    s = x.split()
    return ''.join(i.capitalize() for i in s[1:])

def toCamel(x):
    for i in str(x):
        if not i.isalpha():
            x = x.replace(x(i,''))
    # s = x.replace("-", " ").replace("_", " ")
    s = x.split()
    return s[0] + ''.join(i.capitalize() for i in s[1:])

def getActiveProcesses():
    return {p.name() for p in psutil.process_iter(["name"])}


def getActiveWindow():
    active_window_name = None
    try:
        window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(window)
    except:
        print("Could not get active window: ", sys.exc_info()[0])
    return active_window_name