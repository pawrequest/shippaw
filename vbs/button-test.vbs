Dim objShell
Set objShell = CreateObject("Wscript.shell")
objShell.run("powershell -executionpolicy bypass -noexit -file ""C:\AmDesp\AmDesp.ps1"),1,true

'''
' Traceback (most recent call last):
'   File "C:\AmDesp\main.py", line 16, in <module>
'     process_manifest(manifest)
'   File "C:\AmDesp\python\despatch_functions.py", line 33, in process_manifest
'     if not get_address_object(shipment):
'   File "C:\AmDesp\python\despatch_functions.py", line 134, in get_address_object
'     address_object = client.find_address(shipment[postcode_field], search_string)
'   File "C:\AmDesp\python\despatchbay_sdk.py", line 56, in wrapped
'     handle_suds_fault(detail)
'   File "C:\AmDesp\python\despatchbay_sdk.py", line 29, in handle_suds_fault
'     raise exceptions.ApiException(error) from error
' python.exceptions.ApiException: b'Server raised fault: \'No Addresses Found At Postcode. Postcode sent was "NN6 6LX". Property sent was "The Laurels".\''