import sys
import time

import psutil
import win32gui


def getActiveProcesses():
    return {p.name() for p in psutil.process_iter(["name"])}

# Adapted from Martin Thoma on stackoverflow
# https://stackoverflow.com/a/36419702/8068814
def getActiveWindow():
    active_window_name = None
    try:
        window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(window)
    except:
        print("Could not get active window: ", sys.exc_info()[0])
    return active_window_name

while True:
    print(getActiveWindow())
    print(getActiveWindow())
    time.sleep(3)
