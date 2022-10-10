# import win32gui
# import re
#
#
# class WindowMgr:
#     """Encapsulates some calls to the winapi for window management"""
#
#     def __init__ (self):
#         """Constructor"""
#         self._handle = None
#
#     def find_window(self, class_name, window_name=None):
#         """find a window by its class_name"""
#         self._handle = win32gui.FindWindow(class_name, window_name)
#
#     def _window_enum_callback(self, handle, wildcard):
#         """Pass to win32gui.EnumWindows() to check all the opened windows"""
#         if re.match(wildcard, str(win32gui.GetWindowText(handle))) is not None:
#             self._handle = handle
#
#     def find_window_wildcard(self, wildcard):
#         """find a window whose title matches the wildcard regex"""
#         self._handle = None
#         win32gui.EnumWindows(self._window_enum_callback, wildcard)
#
#     def set_foreground(self):
#         """put the window in the foreground"""
#         win32gui.SetForegroundWindow(self._handle)
#
#
# w = WindowMgr()
# w.find_window_wildcard(".*notepad.*")
# w.set_foreground()
#

from pywinauto import application

# https://pywinauto.readthedocs.io/en/latest/getting_started.html
# from pywinauto.application import Application
# app = Application(backend="uia").start('notepad.exe')
#
# # describe the window inside Notepad.exe process
# dlg_spec = app.UntitledNotepad
# # wait till the window is really open
# actionable_dlg = dlg_spec.wait('visible')
# app = application.Application(backend='uia')
# dlg = app.top_window()
# sleep(2)
# dialogs = app.windows()
# pprint(f"{dialogs=}")

# for dialog in dialogs:
#     print(f"{dialog}")
#
#     ...

app = application.Application(backend='uia')
app.start(r"C:\Program Files\LibreOffice\program\scalc.exe")
app.connect(title='Untitled 1 - LibreOffice Calc', timeout=120)
app.Untitled1LibreOfficeCalc.print_control_identifiers()


# app = application.Application(backend='uia')
# app.start(r"C:\Program Files\LibreOffice\program\scalc.exe")
# app.connect(title='Untitled1LibreOfficeCalc', timeout=10)
# app.Untitled1LibreOfficeCalc.print_control_identifiers()


# app.UntitledNotepad.draw_outline()
# app.UntitledNotepad.menu_select("Edit -> Replace")
# sleep(2)
# app.Replace.print_control_identifiers()
# sleep(2)
# app.Replace.Cancel.click()
# sleep(2)
# app.UntitledNotepad.Edit.type_keys("Hi from Python interactive prompt %s" % str(dir()), with_spaces = True)
# sleep(2)
# app.UntitledNotepad.menu_select("File -> Exit")
# sleep(2)
# app.Notepad.DontSave.click()
# sleep(2)
