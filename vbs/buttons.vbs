Sub Form_OnClick(ControlId)
    Select Case ControlId
        Case ""
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
''EXPORTS FORM TO XML AND CALLS POWERSHELL   '''''''''''''''''''''''''''''''''''''''''
            Dim objShell, args, runscript, powershell                               ''
            ' runscript = "powershell -executionpolicy bypass -noexit -file"        ''
            runscript = "powershell -executionpolicy bypass -noexit -file"          ''
            powershell = "C:\AmDesp\script\AmDespSingle.ps1"                        ''
            args = ""                                                               ''
            Set objShell = CreateObject("WScript.Shell")                            ''
            objShell.Run (runscript & " " & powershell & " " & args)                ''
            Set objShell = Nothing'                                                 ''
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

        Case ""
            ' All Parcelforce
            MsgBox ("All Parcelforce") ' debug
            Form.Field("Send Method").Value = "Parcelforce"
            Form.Field("Collection Method").Value = "Parcelforce"

		Case ""
			' All Courier
            MsgBox ("All Courier")    ' debug
			Form.Field("Send Method").Value = "Other Courier"
			Form.Field("Collection Method").Value = "Other Courier"

		Case ""
			' All Customer
            MsgBox ("All Customer")    ' debug
			Form.Field("Send Method").Value = "Customer Collects"
			Form.Field("Collection Method").Value = "Customer Returns"


        Case ""
        ' book hire in all ok'
			Form.Field("Unpacked By").Value = "PR"
			Form.Field("Unpacked Date").Value = "today"
			Form.Field("Unpacked Time").Value = "now"
			Form.Field("Status").Value = "Returned all OK"
			Form.Field("Actual Return Date").Value = "today"
			Form.Field("Closed").Value = 1
			Form.Save

        Case ""
		 ' exports the hire to xml and calls python to ship xml via external vbs script and powershell. powershell checks  in detail-form script
        Call ExportItemDetailForm("C:\AmDesp\data\AmShip.xml")
        Dim objShell, myconnection
        Set objShell = CreateObject("WScript.Shell")
        objShell.Run "C:\AmDesp\vbs\button-test.vbs"
        Set objShell = Nothing

        Case ""
            ' packed ok
            Form.Field("Packed By").Value = "PR"
            Form.Field("Packed Date").Value = "today"
            Form.Field("Packed Time").Value = "now"
            Form.Field("Status").Value = "Booked in and packed"
            Form.Save
    End Select
End Sub