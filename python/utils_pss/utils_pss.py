# import sys
import subprocess


# import win32gui
# from pyexcel_ods3 import get_data

class DictObj:
    def __init__(self, in_dict:dict):
        assert isinstance(in_dict, dict)
        for key, val in in_dict.items():
            if isinstance(val, (list, tuple)):
               setattr(self, key, [DictObj(x) if isinstance(x, dict) else x for x in val])
            else:
               setattr(self, key, DictObj(val) if isinstance(val, dict) else val)




class Utility:
    @staticmethod
    def powershell_runner(script_path,
                          *params):  # SCRIPT PATH = POWERSHELL SCRIPT PATH,  PARAM = POWERSHELL SCRIPT PARAMETERS ( IF ANY )
        POWERSHELL_PATH = "powershell.exe"  # POWERSHELL EXE PATH

        commandline_options = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted',
                               script_path]  # ADD POWERSHELL EXE AND EXECUTION POLICY TO COMMAND VARIABLE
        for param in params:  # LOOP FOR EACH PARAMETER FROM ARRAY
            commandline_options.append("'" + param + "'")  # APPEND YOUR FOR POWERSHELL SCRIPT
        process_result = subprocess.run(commandline_options, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        universal_newlines=True)  # CALL PROCESS
        if 'debug' in params:
            print(f"{commandline_options=}")
        print(f"{process_result.stdout=}")  # PRINT STANDARD OUTPUT FROM POWERSHELL
        print(f"{process_result.stderr=}")  # PRINT STANDARD ERROR FROM POWERSHELL ( IF ANY OTHERWISE ITS NULL|NONE )
        return process_result.returncode



def printel(*els): # elementtree elements
    print("printel")
    if isinstance(els, str):
        els = [els]
    for el in els:
        print(el)
        for elem in el.iter():
            print(elem.tag, elem.text)


# def get_from_ods(ods_file, sheet): # takes the name of a sheet, headers(bool) and output(list of lists or dict)
#     wkbook = get_data(ods_file)
#     sheet = sheet
#     rows = wkbook[sheet]
#     rows = [row for row in rows if len(row)>0]
#     headers = rows[0]
#     headers_stripped = [head.strip() for head in headers]
#     # body = [row for row in rows[1:]]
#     body = rows[1:]
#     out_dict = {}
#     if headers_stripped[0] == 'col': # top left cell of sheet = 'col, so use first column as headers
#         for row in body:
#             k = row[0].strip()  # first iem in row list is header / key... remove whitespace
#             v = row[1:]         # the rest of the list is the content / value
#             v_stripped = [field.strip() for field in v] # strip whitespace from each item in content / value list
#             out_dict.update({k: v_stripped}) # ouptut dict has first cell as keys and rest of row as values
#     else:   # first cell is not 'col' so we assume first row is headers
#         for row in body:
#             row_dict = {}
#             fields = [field for field in row if len(row)>0] # if row has items put them in a list called fields
#             for c, field in enumerate(fields):
#                 k = headers_stripped[c] # for each field in list get output_dict key key from headers at same index
#                 if isinstance(field,str):   # if the field content is a string strip whitespace
#                     field = field.strip()
#                 row_dict.update({k:field})
#             out_dict.update({row[0]:row_dict})
#     return out_dict  # #, rows # does it need a list of rows?


def toPascal(x): #LikeThis
    x = x.title()
    for y in x:
        if not y.isalpha():
            if not y.isnumeric():
                x = x.replace(y, '')
    s = x.split()
    print("JOIN", ''.join(i.capitalize() for i in s[1:]))
    return ''.join(i.capitalize() for i in s[1:])


def toCamel(x): #likeThis
    for i in str(x):
        if not i.isalnum():
            x = x.replace(i, ' ')
    s = x.lower().split()
    return s[0] + ''.join(i.capitalize() for i in s[1:])


# def getActiveProcesses():
#     return {p.name() for p in psutil.process_iter(["name"])}


# def getActiveWindow():
#     active_window_name = None
#     try:
#         window = win32gui.GetForegroundWindow()
#         active_window_name = win32gui.GetWindowText(window)
#     except:
#         print("Could not get active window: ", sys.exc_info()[0])
#     return active_window_name


def withoutKeys(d, keys):
    ...
    return {x: d[x] for x in d if x not in keys}



def unsanitise(string):
    string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
                                                                                                            chr(60)).replace(
        "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    return string