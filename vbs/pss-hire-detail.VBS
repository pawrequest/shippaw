Sub Form_OnClick(ControlId)
    Select Case ControlId
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


        Case "CommandButton19"
        ' book hire in all ok'
			Form.Field("Unpacked By").Value = "PR"
			Form.Field("Unpacked Date").Value = "today"
			Form.Field("Unpacked Time").Value = "now"
			Form.Field("Status").Value = "Returned all OK"
			Form.Field("Actual Return Date").Value = "today"
			Form.Field("Closed").Value = 1
			Form.Save

        Case "CommandButton20"
		 ' exports the hire to xml and calls python to ship xml via external vbs script and powershell. powershell checks  in detail-form script
        Call ExportItemDetailForm("C:\AmDesp\data\AmShip.xml")
        Dim objShell, myconnection
        Set objShell = CreateObject("WScript.Shell")
        objShell.Run "C:\AmDesp\vbs\button-test.vbs"
        Set objShell = Nothing

        Case "CommandButton21"
            ' packed ok
            Form.Field("Packed By").Value = "PR"
            Form.Field("Packed Date").Value = "today"
            Form.Field("Packed Time").Value = "now"
            Form.Field("Status").Value = "Booked in and packed"
            Form.Save
    End Select
End Sub

'''''''''''''''''''''''''''''''''''''''''''''
''''''''' arno-pss function to export item field
'''''''''''''''''''''''''''''''''''''''''''''''''''
Const CMC_DELIM = "<<%||%>>" 'string to delimit the retrieved data. Use any string you want, but make sure it is unlikely it may represent a name/value of a category or field
Const CMC_DELIM2 = "@#$%%$#@" 'string for secondary delimiter for use in parsing connections

Sub ExportItemDetailForm(ByVal strPath)

    'will export all values showing on the form,
    'including ones that are not visible(!)
    'any user, if permissioned, can always show these anwyay.
    Dim db, conv, f, arrFields, arrCons, strDDE
    Set db = Application.Database
    Set conv = db.GetConversation("Commence", "GetData")
    strDDE = "[GetFieldNames(" & dq(Form.CategoryName) & "," & dq(CMC_DELIM) & ")]"
    arrFields = Split(conv.Request(strDDE), CMC_DELIM)
    Dim xmlDoc : Set xmlDoc = CreateObject("Msxml2.DOMDocument.6.0")
    xmlDoc.async = false
    xmlDoc.loadXML("<root><ItemDetailForm/></root>")

    Dim el
    Dim objRoot : Set objRoot = xmlDoc.DocumentElement
    Set el = xmlDoc.createElement("CategoryName")
    el.text = sanitizeXMLString(Form.CategoryName)
    objRoot.childNodes.item(0).appendChild(el)
    Set el = xmlDoc.createElement("FormName")
    el.text = sanitizeXMLString(Form.Name)
    objRoot.childNodes.item(0).appendChild(el)
    Set el = xmlDoc.createElement("Fields")
    Dim fnode : Set fnode = objRoot.childNodes.item(0).appendChild(el)
    Dim i
    For i = 0 To UBound(arrFields) - 1
        ' the idea is that if we cannot instatiate a field,
        ' it isn't on the form, so we need to catch the errors
        On Error Resume Next
        Set f = Form.Field(arrFields(i))
        On Error Goto 0
        ' add to xml doc
        Set el = xmlDoc.createElement("Field")
        Dim n : Set n = fnode.appendChild(el) 'get reference to node
        Set el = xmlDoc.createElement("FieldName")
        el.text = sanitizeXMLString(f.Name)
        n.appendChild(el)
        Set el = xmlDoc.createElement("FieldValue")
        el.text = sanitizeXMLString(f.Value)
    n.appendChild(el)
    Next
    ' process customer connections
    strDDE = "[GetConnectionNames(" & dq(Form.CategoryName) & "," & dq(CMC_DELIM) & "," & dq(CMC_DELIM2) & ")]"
    arrCons = Split(conv.Request(strDDE), CMC_DELIM)
    Dim connect, CustomerName
    Set connect = Form.Connection("To", "Customer") ' customer connection please'
    Set el = xmlDoc.createElement("Customer")
    Dim nodeCustomer : Set nodeCustomer = objRoot.childNodes.item(0).appendChild(el) ' node parent is root'
    el.text = sanitizeXMLString(connect.ItemName)
    Set el = xmlDoc.createElement("ToCategory")
    xmlDoc.Save strPath
    Set xmlDoc = Nothing
    Set conv= Nothing
    Set db = Nothing
End Sub

public Function sanitizeXMLString(invalidString)
	Dim tmp, i
	tmp = invalidString
	'first replace ampersand
	tmp = Replace(tmp, chr(38), "&amp;")
	'then the other special characters
	For i = 160 to 255
		tmp = Replace(tmp, chr(i), "&#" & i & ";")
	Next
	'and then the special characters
	tmp = Replace(tmp, chr(34), "&quot;")
	tmp = Replace(tmp, chr(39), "&apos;")
	tmp = Replace(tmp, chr(60), "&lt;")
	tmp = Replace(tmp, chr(62), "&gt;")
	'tmp = Replace(tmp, chr(32), "&nbsp;")
	sanitizeXMLString = tmp
end function

Function dq(s)

  dq = Chr(34) & s & Chr(34)

End Function
'*********************************************