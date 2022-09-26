
' this makes the various buttons on the form work, including the "charity discount" insertion button work, and the buttons for number of weeks of hire
' Jan 2013: added code for the four buttons that insert the due back dates for 1,2,3 week and month (4 week) hire periods
' Mar 2013: added code for the "Student Discount" button, and amended the charity discount rate from 20% to 25%
' Oct 2013: added code to allow user to "pull in" hire quantities from the linked customer record - from Autoquote

Sub Form_OnClick(ControlId)
    Select Case ControlId
        Case "CommandButton1"
            Form.Field("Discount Description").Value = "Charity Discount"
            Form.Field("Discount Percentage").Value = "25%"
        Case "CommandButton2"
            If Form.Field("Send Out Date").Value <> "" Then
				Form.Field("Due Back Date").Value = DateAdd("d",9,Form.Field("Send Out Date").Value)
				Form.Field("Due Back Date").Value = NotWeekends(Form.Field("Due Back Date").Value)
				Form.Field("Weeks").Value = 1

			End If
        Case "CommandButton3"
            If Form.Field("Send Out Date").Value <> "" Then
				Form.Field("Due Back Date").Value = DateAdd("d",16,Form.Field("Send Out Date").Value)
				Form.Field("Due Back Date").Value = NotWeekends(Form.Field("Due Back Date").Value)
				Form.Field("Weeks").Value = 2
			End If

        Case "CommandButton4"
            If Form.Field("Send Out Date").Value <> "" Then
				Form.Field("Due Back Date").Value = DateAdd("d",23,Form.Field("Send Out Date").Value)
				Form.Field("Due Back Date").Value = NotWeekends(Form.Field("Due Back Date").Value)
				Form.Field("Weeks").Value = 3
			End If

        Case "CommandButton5"
            If Form.Field("Send Out Date").Value <> "" Then
				Form.Field("Due Back Date").Value = DateAdd("d",32,Form.Field("Send Out Date").Value)
				Form.Field("Due Back Date").Value = NotWeekends(Form.Field("Due Back Date").Value)
				Form.Field("Weeks").Value = 4
			End If
        Case "CommandButton6"
            Form.Field("Discount Description").Value = "Student Discount"
            Form.Field("Discount Percentage").Value = "25%"
        Case "CommandButton7"
			' this button "pulls" the equipment quantity fields from the corresponding fields in the
			' customer record, that have been put there by being read in from "AutoQuote"
            Form.Field("Number UHF").Value = cCust.FieldValue("Number UHF")
            Form.Field("Number Batteries").Value = cCust.FieldValue("Number Batteries")
			Form.Field("Number Cases").Value = cCust.FieldValue("Number Cases")
			Form.Field("Number EM").Value = cCust.FieldValue("Number EM")
			Form.Field("Number EMC").Value = cCust.FieldValue("Number EMC")
			Form.Field("Number Headset").Value = cCust.FieldValue("Number Headset")
			Form.Field("Number Headset Big").Value = cCust.FieldValue("Number Headset Big")
			Form.Field("Number Icom").Value = cCust.FieldValue("Number Icom")
			Form.Field("Number Megaphone").Value = cCust.FieldValue("Number Megaphone")
			Form.Field("Number Parrot").Value = cCust.FieldValue("Number Parrot")
		Case "CommandButton8"
		' if there is an email address in the "delivery contact" field enclosed in angle brackets, strip it out and put
		' it into the email field leaving just the actual name in the contact name field
		' only do anything if there is an @ in the string in the first place
		If Instr(Form.Field("Delivery Contact").Value,"<") Then
			length = Len(Form.Field("Delivery Contact").Value)
			atpos = Instr(Form.Field("Delivery Contact").Value,"<")
			Form.Field("Delivery Email").Value = Right(Form.Field("Delivery Contact").Value, (length-atpos))
			Form.Field("Delivery Contact").Value = Left(Form.Field("Delivery Contact").Value, atpos)
		End If
		Case "CommandButton9"
			' this button inserts the current date and time into the Packed Date and Packed Time fields
			Form.Field("Packed Date").Value = "today"
			Form.Field("Packed Time").Value = "now"
		Case "CommandButton10"
			' this button inserts the current date and time into the Unpacked Date and Unpacked Time fields
			Form.Field("Unpacked Date").Value = "today"
			Form.Field("Unpacked Time").Value = "now"

		Case "CommandButton11"
			' All Parcelforce
            MsgBox ("All Parcelforce") ' debug
			Form.Field("Send Method").Value = "Parcelforce"
			Form.Field("Collection Method").Value = "Parcelforce"

		Case "CommandButton12"
			' All Courier
            MsgBox ("All Courier")    ' debug
			Form.Field("Send Method").Value = "Other Courier"
			Form.Field("Collection Method").Value = "Other Courier"

		Case "CommandButton13"
			' All Customer
            MsgBox ("All Customer")    ' debug
			Form.Field("Send Method").Value = "Customer Collects"
			Form.Field("Collection Method").Value = "Customer Returns"




		Case "CommandButton18"
		  ' this button inserts the current date into the "Actual Return Date"
			Form.Field("Actual Return Date").Value = "today"

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''''''''   pss                 '''''''''''''''''''''''''''''''
        Case "CommandButton19"
        ' book in hire, all ok'
            Dim ui
            ui = MsgBox("unpacked by paul, all ok?",3)
            if ui = 6 Then
			Form.Field("Unpacked By").Value = "PR"
			Form.Field("Unpacked Date").Value = "today"
			Form.Field("Unpacked Time").Value = "now"
			Form.Field("Status").Value = "Returned all OK"
			Form.Field("Actual Return Date").Value = "today"
			Form.Field("Closed").Value = 1
			Form.Save
			End if
'
'         Case "CommandButton20"
'         ' book in hire, problems'
' 			Form.Field("Unpacked By").Value = "PR"
' 			Form.Field("Unpacked Date").Value = "today"
' 			Form.Field("Unpacked Time").Value = "now"
' 			Form.Field("Status").Value = "Returned with problems"
' 			Form.Field("Actual Return Date").Value = "today"

        Case "CommandButton21"
        ' packed
            Dim uii
            ui = MsgBox("unpacked by paul, all ok?",3)
            if uii = 6 Then
            Form.Field("Packed By").Value = "PR"
            Form.Field("Packed Date").Value = "today"
            Form.Field("Packed Time").Value = "now"
            Form.Field("Status").Value = "Booked in and packed"
            Form.Save
            End if

        Case "CommandButton22"


        Case "CommandButton20"
            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''''''''   Runs Amdesp direct with cmd     ''''''''''
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
		    Dim python_exe, python_script, commence_wrapper, xmlfile
            python_exe = "C:\AmDesp\python\bin\python.exe"
            python_script = "C:\AmDesp\AmDespMain.py"
            commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
            xmlfile = "C:\AmDesp\data\AmShip.xml"
		    ExportItemDetailForm(xmlfile)
            Dim oShell, currentCommand, my_command
            SET oShell = CreateObject("Wscript.Shell")
'             my_command = python_exe & " -noexit " & python_script & " " & JsonPath
            currentCommand = "cmd /c " & python_exe & " " & python_script & Chr(34) '  & " " & xmlfile'
            Msgbox "RUN PYTHON"
            oShell.run currentCommand,1,true


'             Dim objShell, args, runscript, powershell, XmlPath, RunCmd, python_script
'             XmlPath = "C:\AmDesp\data\AmShip.xml"
'             python_script = "C:\AmDesp\AmDespMain.py"
'             RunCmd = "powershell -executionpolicy bypass -noexit -file"
' '             RunCmd = "powershell -executionpolicy bypass -noexit -file" & Chr(34) & python_script & " " & XmlPath & Chr(34)
'             powershell = "C:\AmDesp\script\AmDespSingle.ps1"
' 		    ExportItemDetailForm(XmlPath)
'             args = "XmlPath"
'             Set objShell = CreateObject("WScript.Shell")
'             objShell.Run (RunCmd & " " & powershell & " ") ' & " " & args
' '             objShell.Run (RunCmd & " " & python_script),1,true
'             Set objShell = Nothing
            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''''''''   Runs Amdesp direct with Powershell     ''''''''''
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
' 		    Dim python_exe, python_script, XmlPath
' '             ' '  runs AmDesp direct with CMD
'             python_exe = "C:\AmDesp\python\bin\python.exe"
'             python_script = "C:\AmDesp\AmDespMain.py"
'             XmlPath = "C:\AmDesp\data\AmShip.xml"
' 		    ExportItemDetailForm(XmlPath)
'             Dim oShell, currentCommand, my_command
'             SET oShell = CreateObject("Wscript.Shell")
'             RunCmd = "powershell -executionpolicy bypass -noexit -file" & Chr(34) & python_script & " " & XmlPath & Chr(34)
'             oShell.run RunCmd,1,true


'             currentCommand = "cmd /c " & Chr(34) & python_script & " " & JsonPath & Chr(34)
'             Msgbox "RUN PYTHON"

' C:\AmDesp\script\AmDespSingle.ps1

'''''''''''''''''''''''''''''''''''''''''


' 		    Dim python_exe, python_script, commence_wrapper, JsonPath
'             python_exe = "C:\AmDesp\python\bin\python.exe"
'             python_script = "C:\AmDesp\AmDespMain.py"
'             XmlPath = "C:\AmDesp\data\AmShip.xml"
'             Dim oShell, source_code_path, variable1, currentCommand, my_command
'             SET oShell = CreateObject("Wscript.Shell")
'             pyPs = "powershell -executionpolicy bypass -noexit -file" & python_exe & python_script & XmlPath
'             RunCmd = "powershell -executionpolicy bypass -noexit -file" & Chr(34) & python_script & " " & XmlPath & Chr(34)
'             my_command = python_exe &  python_script & " " & JsonPath
' '             Msgbox "RUN PYTHON"
'             oShell.run pyPs,1,true
' objShell.run("powershell -executionpolicy bypass -noexit -file ""C:\AmDesp\AmDesp.ps1"""),1,true
' objShell.run("powershell -executionpolicy bypass -noexit -file ""C:\AmDesp\AmDesp.ps1"""),1,true

'
' 		 ' exports the hire to xml and calls python to ship xml
'         Call ExportItemDetailForm("C:\AmDesp\data\AmShip.xml")
'         Dim objShell, myconnection
'         Set objShell = CreateObject("WScript.Shell")
'         objShell.Run "C:\AmDesp\vbs\button.vbs"
'         Set objShell = Nothing


' 		 ' exports the hire to xml and calls python to ship xml
'         Call ExportItemDetailForm("C:\AmDesp\data\AmShip.xml")
'         Dim objShell, myconnection
'         Set objShell = CreateObject("WScript.Shell")
'         objShell.Run "C:\AmDesp\vbs\button.vbs"
'         Set objShell = Nothing

''''''''''''''''''    pss             ''''''''''''''''''''''''''''''
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''