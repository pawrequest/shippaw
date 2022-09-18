Const CMC_DELIM = "<<%||%>>" 'string to delimit the retrieved data. Use any string you want, but make sure it is unlikely it may represent a name/value of a category or field
Const CMC_DELIM2 = "@#$%%$#@" 'string for secondary delimiter for use in parsing connections


Sub Form_OnClick(ByVal ControlName)
    Select Case ControlName
        Case "CommandButton"
            Call ExportItemDetailForm(exportfile) 'change this
        Exit Sub
    End Select
End Sub

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

    ' set root'
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

    ' process connections
	strDDE = "[GetConnectionNames(" & dq(Form.CategoryName) & "," & dq(CMC_DELIM) & "," & dq(CMC_DELIM2) & ")]"
	arrCons = Split(conv.Request(strDDE), CMC_DELIM)

    Dim c, j, tmp
    Set el = xmlDoc.createElement("Connections")
    Dim cnode : Set cnode = objRoot.childNodes.item(0).appendChild(el)

    For i = 0 To UBound(arrCons) - 1
        tmp = Split(arrCons(i), CMC_DELIM2) 'split Connection name and ToCategory
        On Error Resume Next
        Set c = Form.Connection(tmp(0), tmp(1)) 'is there such a Connection?
        On Error GoTo 0
        If c.ConnectedItemCount > 0 Then 'only export if there are values. Do we want this?
            Set el = xmlDoc.createElement("Connection")
            el.text = sanitizeXMLString(c.Name)
            Dim elConName : Set elConName = cnode.appendChild(el) 'get reference to node
            Set el = xmlDoc.createElement("ToCategory")
            el.text = sanitizeXMLString(c.ToCategory)
            Dim elCatName : Set elCatName = elConName.appendChild(el) 'get reference to node
            For j = 1 To c.ConnectedItemCount 'a populated connection is initialized to 1
                c.CurrentSelection(j)
                Set el = xmlDoc.createElement("ItemName")
                el.text = sanitizeXMLString(c.ItemName)
                elCatName.appendChild(el)
            Next 'j
        End If
    Next 'i

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