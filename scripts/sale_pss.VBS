Option Explicit

Sub Form_OnSave()

  ' define a variable called "cCust" to hold the connection from sale record to customer
  ' this makes it easier to refer to several times later on
  Dim cCust
  Set cCust = Form.Connection("To","Customer")
  ' nstring is used to store the sale record's "Name" field, made up of the customer name (truncated to 27 chars if needed), the date and the 
  ' modified reference number (see refstring)
  Dim nstring

  ' refstring is used to store the sale reference number field as a string, and then with its commas removed, it is then inserted into the 
  ' name field
  Dim refstring
  
  ' addstring is used to make up the "all delivery address" field displayed on the detail form to make it easier for users to copy the whole address in one go
  Dim addstring
  
  ' tempaddress is used to store the address fields during bvlank line suppression
  Dim temp_address
  
  
  
  nstring = ""
  refstring = ""
  addstring = ""
  temp_address = ""
 
 	' code to make the link to the customer and insert the string into the "name" field. 
	If Form.Field("Name").Value = "newsale" And Form.Connection("To", "Customer").ConnectedItemCount()  = 1   Then
      refstring = CStr(Form.Field("Reference Number").Value)
      refstring = Replace(refstring, ",", "")
      nstring = Left(Form.Connection("To", "Customer").ItemName()  , 27) + " - " + Form.Field("Date Ordered").Value + " ref " + refstring
      Form.Field("Name").Value = nstring
   	End If

	' copy the INVOICE name, address, postcode, phone, email, contact name fields from the connected customer record, unless something else
    ' has been entered there already
    If Form.Field("Invoice Name").Value = "" Then
      Form.Field("Invoice Name").Value = cCust.FieldValue("Name")
    End If

   If Form.Field("Invoice Contact").Value = "" Then
      Form.Field("Invoice Contact").Value = cCust.FieldValue("Contact Name")
    End If

    If Form.Field("Invoice Postcode").Value = "" Then
      Form.Field("Invoice Postcode").Value = cCust.FieldValue("Postcode")
    End If

    If Form.Field("Invoice Address").Value = "" Then
      Form.Field("Invoice Address").Value = cCust.FieldValue("Address")
    End If

    If Form.Field("Invoice Telephone").Value = "" Then
      Form.Field("Invoice Telephone").Value = cCust.FieldValue("Telephone")
    End If

    If Form.Field("Invoice Email").Value = "" Then
      Form.Field("Invoice Email").Value = cCust.FieldValue("Email")
    End If

    ' copy the DELIVERY name, address, postcode, phone, email, contact name fields from the connected customer record, unless something else
    ' has been entered there already
    If Form.Field("Delivery Name").Value = "" Then
      Form.Field("Delivery Name").Value = cCust.FieldValue("Deliv Name")
    End If

   If Form.Field("Delivery Contact").Value = "" Then
      Form.Field("Delivery Contact").Value = cCust.FieldValue("Deliv Contact")
    End If

    If Form.Field("Delivery Postcode").Value = "" Then
      Form.Field("Delivery Postcode").Value = cCust.FieldValue("Deliv Postcode")
    End If

    If Form.Field("Delivery Address").Value = "" Then
      Form.Field("Delivery Address").Value = cCust.FieldValue("Deliv Address")
    End If

    If Form.Field("Delivery Telephone").Value = "" Then
      Form.Field("Delivery Telephone").Value = cCust.FieldValue("Deliv Telephone")
    End If

    If Form.Field("Delivery Email").Value = "" Then
      Form.Field("Delivery Email").Value = cCust.FieldValue("Deliv Email")
    End If

    ' call common functions to "tidy up" various fields
	
	
	' trim any spaces off the company / "name" fields
	Form.Field("Invoice Name").Value = Trim(Form.Field("Invoice Name").Value)
	Form.Field("Delivery Name").Value = Trim(Form.Field("Delivery Name").Value)

	' Convert unusual apostrophes (ASCII codes 96, 145, 146) into the older 7-bit ASCII standard apostrophe (ASCII code 39) to avoid invoices printing funny - Giles 
	' do this for both the customer business name and the delivery address business name
	Form.Field("Invoice Name").Value = Replace(Form.Field("Invoice Name").Value, Chr(96), Chr(39))
	Form.Field("Invoice Name").Value = Replace(Form.Field("Invoice Name").Value, Chr(145), Chr(39))
	Form.Field("Invoice Name").Value = Replace(Form.Field("Invoice Name").Value, Chr(146), Chr(39))

	Form.Field("Delivery Name").Value = Replace(Form.Field("Delivery Name").Value, Chr(96), Chr(39))
	Form.Field("Delivery Name").Value = Replace(Form.Field("Delivery Name").Value, Chr(145), Chr(39))
	Form.Field("Delivery Name").Value = Replace(Form.Field("Delivery Name").Value, Chr(146), Chr(39))

	' call function to format the email addresses correctly, trimming and removing angle brackets left in by cutting and pasting
	Form.Field("Invoice Email").Value = FormatEmail(Form.Field("Invoice Email").Value)
	Form.Field("Delivery Email").Value = FormatEmail(Form.Field("Delivery Email").Value)

	' call function to trim, initial capitalise and remove spurious characters from contact names fields
	Form.Field("Invoice Contact").Value = FormatPersonName(Form.Field("Invoice Contact").Value)
	Form.Field("Delivery Contact").Value = FormatPersonName(Form.Field("Delivery Contact").Value)

	' call function to format the UK postcode fields correctly in terms of the middle space
	Form.Field("Invoice Postcode").Value = FormatPostcode(Form.Field("Invoice Postcode").Value)
	Form.Field("Delivery Postcode").Value = FormatPostcode(Form.Field("Delivery Postcode").Value)
	
	' call function to tidy up telephone number fields
	Form.Field("Invoice Telephone").Value = FormatTelNumber(Form.Field("Invoice Telephone").Value)
	Form.Field("Delivery Telephone").Value = FormatTelNumber(Form.Field("Delivery Telephone").Value)
	
	'this gets rid of blank lines in the address fields: copy the contents of the multi-line address field away to a variable called temp_address and then clear the field
	' and copy the variable back into it - just doing this copy and copy back seems to remove the trailing blank lines
	' then use REPLACE function to get rid of any double-spaced lines (i.e. blanks in between lines of text)
	temp_address = Form.Field("Invoice Address").Value
	temp_address = REPLACE(temp_address, vbCrLf & vbCrLf, vbCrLf)
	temp_address = REPLACE(temp_address, vbCrLf & vbCrLf, vbCrLf)
	Form.Field("Invoice Address").Value = temp_address

	' now do the same for the delivery address
	temp_address = Form.Field("Delivery Address").Value
	temp_address = REPLACE(temp_address, vbCrLf & vbCrLf, vbCrLf)
	temp_address = REPLACE(temp_address, vbCrLf & vbCrLf, vbCrLf)
	Form.Field("Delivery Address").Value = temp_address

	' fill the "Purchase Order Print" field if there is content in the "Purchase Order" field
	Form.Field("Purchase Order Print").Value = ""
	If Form.Field("Purchase Order").Value <> "" Then
      Form.Field("Purchase Order Print").Value = "Purchase Order: " + Form.Field("Purchase Order").Value
    End If
	
	'combine the delivery contact name, company name, address and postcode into the "All Address" field
	addstring = Form.Field("Delivery Contact").Value + vbCrLf + Form.Field("Delivery Name").Value + vbCrLf + Form.Field("Delivery Address").Value + vbCrLf + Form.Field("Delivery Postcode").Value
	Form.Field("All Delivery Address").Value = addstring

' this is the end of the On Save section above


End Sub



' ***** start of functions etc *****

' New Sep 2013 - general function to remove un-needed characters from telephone number fields and try to format the numbers correctly
' as UK phone numbers
' Jan 2014: added stuff to space an "x" for phone extensions properly

Function FormatTelNumber(Telnum)

  Dim xpos
  
  ' first, remove all dashes, brackets etc from phone number 
  Telnum = Replace(Telnum, "-", "")
  Telnum = Replace(Telnum, "(", "")
  Telnum = Replace(Telnum, ")", "")
  Telnum = Replace(Telnum, ".", "")
  Telnum = Replace(Telnum, "/", "")
  Telnum = Replace(Telnum, ":", "")  
  Telnum = Replace(Telnum, "<", "")
  Telnum = Replace(Telnum, ">", "")
  
  ' remove all spaces from the phone number
  Telnum = Replace(Telnum, " ", "")

  ' now we should have (usually) a string consisting only of numbers, maybe with a "+" at the start
    
  ' if the number starts "+44"  then remove it
  If Left(Telnum,3) = "+44" Then
    Telnum = Mid(Telnum,4)
  End If
  
  ' if the number starts "0044" then remove it
  If Left(Telnum,4) = "0044" Then
    Telnum = Mid(Telnum,5)
  End If

  ' if the number starts "44"  then remove it
  If Left(Telnum,2) = "44" Then
    Telnum = Mid(Telnum,3)
  End If
  
  ' if the number starts "7" add a leading "0"
  If Left(Telnum,1) = "7" Then
    Telnum = "0" + Mid(Telnum,1)
  End If
 
  ' if the number starts "1" add a leading "0"
  If Left(Telnum,1) = "1" Then
    Telnum = "0" + Mid(Telnum,1)
  End If
 
 ' if the number starts "2" add a leading "0"
  If Left(Telnum,1) = "2" Then
    Telnum = "0" + Mid(Telnum,1)
  End If
 
  ' from here on, we have to do a big If ... ElseIf statement to deal with specific types of number
  If Left(Telnum,2) = "07" Then
    ' it is a UK mobile number, so insert a space after the fifth digit
    Telnum = Left(Telnum,5) + " " + Mid(Telnum,6)
    
  Elseif Left(Telnum,2) = "02" Then
    ' format London and other "02" numbers correctly - 02x xxxx xxxx
    Telnum = Left(Telnum,3) + " " + Mid(Telnum,4,4) + " " + Mid(Telnum,8)
	
  Elseif Left(Telnum,3) = "011" Then
    ' deal with the large town numbers like Sheffield 0114 etc - 011x xxx xxxx
    Telnum = Left(Telnum,4) + " " + Mid(Telnum,5,3) + " " + Mid (Telnum,8)
	
  Elseif Left(Telnum,4) = "0845" Then
    ' deal with 0845 numbers
    Telnum = Left(Telnum,4) + " " + Mid(Telnum,5)

  Elseif Left(Telnum,4) = "0844" Then
    ' deal with 0844 numbers
    Telnum = Left(Telnum,4) + " " + Mid(Telnum,5)

  Elseif Left(Telnum,4) = "0800" Then
    ' deal with 0800 numbers
    Telnum = Left(Telnum,4) + " " + Mid(Telnum,5)
	  
  Elseif Left(Telnum,2) = "01" Then
	  
	  ' if the fourth character is a "1" then it must be one if the UK large city numbers, (like Edinburgh 0131 xxx xxxx) so format for this
	  If Mid(Telnum,4,1) = "1" Then
	    Telnum = Left(Telnum,4) + " " + Mid(Telnum,5,3) + " " + Mid (Telnum,8)
	  
	  ' if it looks like a general UK Landline, insert a space after what is usually the area code
      Elseif Len(Telnum) < 12 Then
	    Telnum = Left(Telnum,5) + " " + Mid(Telnum,6)
      End If   
	
  End If
  
  ' finally, if there is an "x" in the number string (to show "extension") then insert a space on either side of it
  xpos = Instr(Telnum,"x")
  If xpos <> 0 Then
    Telnum = Left(Telnum,xpos - 1) + " x " + Mid(Telnum, xpos + 1)
  End If
  
  ' return the formatted number
  FormatTelNumber = Telnum

End Function


' this function cleans up the formatting of any "persons name" field passed to it by removing spaces, wrong characters
' and then making each part of the person's name have a capital letter (added 9th April 2016)
Function FormatPersonName(Pname)

  ' first, trim the field to get rid of leading and trailing spaces
  Pname = Trim(Pname)

  ' remove all silly characters etc from the name
  Pname = Replace(Pname, "(", "")
  Pname = Replace(Pname, ")", "")
  Pname = Replace(Pname, ".", "")
  Pname = Replace(Pname, ",", "")
  Pname = Replace(Pname, "/", "")
  Pname = Replace(Pname, ":", "")  
  Pname = Replace(Pname, "<", "")
  Pname = Replace(Pname, ">", "")
  ' remove speech marks
  Pname = Replace(Pname, Chr(34), "")
  
  ' added May 2022 replace any unusual apostrophes (ASCII code 95, 145, 146) with the standard 7 bit ASCII apostrophe (ASCII code 39) to avoid printing problems
  Pname = Replace(Pname, Chr(96), Chr(39))
  Pname = Replace(Pname, Chr(145), Chr(39))
  Pname = Replace(Pname, Chr(146), Chr(39))
  
  ' now use "Pcase" to make it initial capitals
  Pname = PCase(Pname, "")
  
  ' return the formatted person's name
  FormatPersonName = Pname
  
End Function

Function FormatEmail(Emailstring)

 ' first, trim the field to get rid of leading and trailing spaces
  Emailstring = Trim(Emailstring)
  
  ' get rid of any spaces
  Emailstring = Replace(Emailstring, " ", "")

 ' remove angle brackets
  Emailstring = Replace(Emailstring, "<", "")
  Emailstring = Replace(Emailstring, ">", "")
  
 ' remove speech marks
  Emailstring = Replace(Emailstring, Chr(34), "")
  
  ' remove spaces
  Emailstring = Replace(Emailstring, " ", "")
  
  ' remove double @ 
  Emailstring = Replace(Emailstring, "@@", "@")
  
' return the formatted email address
  FormatEmail = Emailstring
  
End Function


Function FormatPostcode(pcode)

' remove all silly characters etc from the postcode
  Pcode = Replace(Pcode, "(", "")
  Pcode = Replace(Pcode, ")", "")
  Pcode = Replace(Pcode, ".", "")
  Pcode = Replace(Pcode, "/", "")
  Pcode = Replace(Pcode, ":", "")  
  Pcode = Replace(Pcode, "<", "")
  Pcode = Replace(Pcode, ">", "")

'always capitalise postcode field
FormatPostcode = Ucase(pcode)

'FormatPostcode = Trim(FormatPostcode)
FormatPostcode = Replace(FormatPostcode, " ", "")

If Len(FormatPostcode) = 7 Then
  FormatPostcode = Left(FormatPostcode,4) + " " + Mid(FormatPostcode,5)
End If

If Len(FormatPostcode) = 6 Then
  FormatPostcode = Left(FormatPostcode,3) + " " + Mid(FormatPostcode,4)
End If

If Len(FormatPostcode) = 5 Then
  FormatPostcode = Left(FormatPostcode,2) + " " + Mid(FormatPostcode,3)
End If

End Function


'Function to return string in proper case. The "Smode" parameter decides if ALL UPPER WORDS are allowed (mode "A" or Not (Mode Anything Else)
Function PCase(Str, Smode)
  Const Delimiters = " -,."
  Dim PStr, I, Char
  Str = Trim(Str)
  PStr = UCase(Left(Str, 1))
  For I = 2 To Len(Str)
    Char = Mid(Str, i-1, 1)
    If InStr(Delimiters, Char) > 0 Then
      PStr = PStr & UCase(Mid(Str, i, 1))
    Else
      'If the function is in "A" (all upper) mode it allows words all upper case to stay that way, otherwise it makes Each Word Into Title Case
      If Smode = "A" Then
        PStr = PStr & Mid(Str, i, 1)
      Else
        PStr = PStr & LCase(Mid(Str, i, 1))
      End If
    End If
  Next
  PCase = PStr
End Function


' Rob's function to split a string containing several lines of text into an array (v) then search each array element 
' for a given string (the field name) and return the rightmost part of that line (the field contents)
Function FindFieldInString(dumpstring, field)
Dim v 
Dim f
  v = Split(dumpstring, vbLf)
For f = 0 To UBound(v)
    If Left(v(f), Len(field)) = field Then
      FindFieldInString = Trim(Right(v(f), Len(v(f)) - Len(field)))
      Exit Function
    End If
  Next
End Function

Sub Form_OnClick(ControlId)
    Select Case ControlId

        Case "CommandButton3"
            if MsgBox("Launch AmDesp to ship sale?",4) =6 Then
                AmDesp("prod")
            End if
        Case "CommandButton4"
            if MsgBox("Launch Amdesp to track shipment?",4) = 6 Then
                AmDesp("track")
            end if
        Case "CommandButton5"
            if MsgBox("Launch Amdesp to create a return from the delivery address??",4) = 6 Then
                AmDesp("create_return")
            end if
    End Select

End Sub

'****************  pss-sub ***********************'



Sub AmDesp(mode)
        ' AmDesp'

        Dim locAmDesp, exeAmDesp, objShell, strCommand, objFSO, locXml
        Set objFSO = CreateObject("Scripting.FileSystemObject")

        locAmDesp = "C:\AmDesp\"
        exeAmDesp = objFSO.BuildPath(locAmDesp, "AmDesp.exe")
        locXml = "C:\AmDesp\data\AmShip.xml"
        ExportItemDetailForm(locXml)

        strCommand = exeAmDesp & " " & mode & " " & locXml
        Set objShell = CreateObject("Wscript.Shell")
        objShell.CurrentDirectory = locAmDesp

        objShell.run "%comspec% /c " & strCommand,1,false ' 1= activate window false = don't wait
        set objShell = nothing
End Sub

'**************** arno+ pss function to export item fields to xml  ***********'

Sub ExportItemDetailForm(ByVal strPath)

    Const CMC_DELIM = "<<%||%>>" 'string to delimit the retrieved data. Use any string you want, but make sure it is unlikely it may represent a name/value of a category or field
    Const CMC_DELIM2 = "@#$%%$#@" 'string for secondary delimiter for use in parsing connections

    Dim db, conv, f, arrFields, arrCons, strDDE
    Set db = Application.Database
    Set conv = db.GetConversation("Commence", "GetData")
    strDDE = "[GetFieldNames(" & dq(Form.CategoryName) & "," & dq(CMC_DELIM) & ")]"
    arrFields = Split(conv.Request(strDDE), CMC_DELIM)
    Dim xmlDoc : Set xmlDoc = CreateObject("Msxml2.DOMDocument.6.0")
    xmlDoc.async = false
    xmlDoc.loadXML("<root><ItemDetailForm/></root>") ' make root/itemdetailform'

    Dim el
    Dim objRoot : Set objRoot = xmlDoc.DocumentElement

    Set el = xmlDoc.createElement("CategoryName")   ' create Root/itemdetailform/CategoryName'
    el.text = sanitizeXMLString(Form.CategoryName)
    objRoot.childNodes.item(0).appendChild(el)
    Set el = xmlDoc.createElement("FormName")       ' create Root/itemdetailform/FormName'
    el.text = sanitizeXMLString(Form.Name)
    objRoot.childNodes.item(0).appendChild(el)
    Set el = xmlDoc.createElement("Fields")         ' create Root/itemdetailform/Fields'
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


    Set el = xmlDoc.createElement("Customer")       ' create Root/itemdetailform/Customer' ' DOES NOT WORK' #debug
    Dim nodeCustomer : Set nodeCustomer = objRoot.childNodes.item(0).appendChild(el) ' node parent is root'
    el.text = sanitizeXMLString(connect.ItemName)
    Set el = xmlDoc.createElement("ToCategory")
    xmlDoc.Save strPath


    Set xmlDoc = Nothing
    Set conv= Nothing
    Set db = Nothing
    Set el = Nothing
    Set connect = Nothing
    Set nodeCustomer = Nothing
    Set objRoot = Nothing
    Set fnode = Nothing
    Set f = Nothing
    Set n = Nothing
    Set connect = Nothing


End Sub


public Function sanitizeXMLString(invalidString)
' used to cleanup strings which interfere with xml format - AmDesp python reverses this'
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
	'tmp = Replace(tmp, chr(32), "&nbsp;") ' (space)'
	sanitizeXMLString = tmp
end function

Function dq(s)

  dq = Chr(34) & s & Chr(34)

End Function

