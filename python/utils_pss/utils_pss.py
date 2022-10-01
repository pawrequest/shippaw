import sys

import psutil
import win32gui
from pyexcel_ods3 import get_data


def printel(*els): # elementtree elements
    print("printel")
    if isinstance(els, str):
        els = [els]
    for el in els:
        print(el)
        for elem in el.iter():
            print(elem.tag, elem.text)


def get_from_ods(wkbook, sheet, headers=True): # takes the name of a sheet in
    headers = headers
    wkbook = get_data(wkbook)
    sheet = sheet
    rows = wkbook[sheet]
    rows = [row for row in rows if len(row)>0]
    if headers:
        headers = rows[0]
        body = rows[1:]
    else:
        body = rows
    row_dict = {}
    for row in body:
        fields = [field for field in row if len(row)>0]
        field_dict = {}
        field_list = []
        for c, field in enumerate(fields):
            if headers:
                # make a dict with headers as keys and fields as values
                header = headers[c]
                field_dict.update({header:field})
            else:
                # make a list
                field_list.append(field)
        row_dict.update({row[0]: field_dict})
        sheets_dict=row_dict
    return sheets_dict #, rows # does it need a list of rows?


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


def withoutKeys(d, keys):
    ...
    return {x: d[x] for x in d if x not in keys}


# clean shipdict
# needs generalising
# def cleanDictShip(shipdict):  # if list takes first item!
#     print("Cleaning your shipdict")
#     newdict={}
#     for k, v in shipdict.items():
#         if k in com_fields: k = com_fields[k]
#         k = toCamel(k)
#         if isinstance(v,list):
#             v = v[0]
#         if v.replace(",","").isnumeric() and int(v.replace(',','')) == 0:
#             v = None
#         elif v.isalnum():
#             v = v.title()
#         newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
#         newdict = withoutKeys(newdict, expungedFields)
#         newdict.update({k:v})
#     return(newdict)


def unsanitise(string):
    string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
                                                                                                            chr(60)).replace(
        "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    return string
    # string = string.replace("&amp;", chr(38))
    # string = string.replace("&quot;", chr(34))
    # string = string.replace("&apos;", chr(39))
    # string = string.replace("&lt;", chr(60))
    # string = string.replace("&gt;", chr(62))
    # string = string.replace("&gt;", chr(32))
    # string = string.replace("&#", "")
    # string = string.replace(";", "")
    # return string

#
# # elephant class has a memory - note the underscores
# class Elephant:
#     def __init__(self, fnc):
#         self._fnc = fnc
#         self._memory = []
#
#     def __call__(self):
#         retval = self._fnc()
#         self._memory.append(retval)
#         return retval
#
#     def memory(self):
#         return self._memory


# @Elephant
# def random_odd():
#     return random.choice([1, 3, 5, 7, 9])
# print(random_odd())
# print(random_odd.memory())
# print(random_odd())
# print(random_odd.memory())