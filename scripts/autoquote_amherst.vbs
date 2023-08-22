
		Case "CommandButton5"
        ' process the text copied in from an "AutoQuote" email

         Dim tempweb, length, temp, atpos, m, dumpstring, addstring


      ' only do any of this if the "Dump" field contains text to analyse and split out
      If Form.Field("Dump").Value <> "" Then

        ' copy the "dump" field into a memory variable
        dumpstring = Form.Field("Dump").Value
        'Msgbox(dumpstring)

        ' split the fields found in the AutoQuote text into the appropriate database fields


        Form.Field("AQ Ref Number").Value = FindFieldInString(dumpstring, "Quotation Reference:")
        Form.Field("Contact Name").Value = PCase(FindFieldInString(dumpstring, "Name:"), "")
        Form.Field("Name").Value = PCase(FindFieldInString(dumpstring, "Organisation:"),"A")
        Form.Field("Telephone").Value = FindFieldInString(dumpstring, "Phone:")
        Form.Field("Fax").Value = FindFieldInString(dumpstring, "Fax:")
        Form.Field("Email").Value = FindFieldInString(dumpstring, "Email:")
        Form.Field("Charity Number").Value = FindFieldInString(dumpstring, "Registered Charity:")
		Form.Field("First Hire Date").Value = FindFieldInString(dumpstring, "Start Date:")

		' if a charity number is entered, set the charity flag to True
		If Form.Field("Charity Number").Value <> "" Then
		  Form.Field("Charity?").Value = 1
		End If


        ' if the "Name" (organisation) field is blank, then substitute the "Contact Name" field - this works for
        ' customers who are private individuals and do not specify any "organisation"
        If Form.Field("Name").Value = "" Then
          Form.Field("Name").Value = Form.Field("Contact Name").Value
        End If

		' if we have a value in the "Name" field by this point, then we are dealing with an autoquote, so
		' set the "Hire Prospect" check box field to "True"
		If Form.Field("Name").Value <> "" Then
			Form.Field("Hire Prospect").Value = 1
		End If

        ' read in the address and postcode fields
        Form.Field("Address").Value = Pcase(FindFieldInString(dumpstring, "Address:"),"A")
        Form.Field("Postcode").Value = FindFieldInString(dumpstring, "Postcode:")

		' split the address into lines based on commas at the end of each line - added by Giles April 2016
		Form.Field("Address").Value = Replace(Form.Field("Address").Value, ", ", vbCrLf)

		' read in notes fields
        Form.Field("Notes").Value = FindFieldInString(dumpstring, "Purpose of hire:") + vbLf + FindFieldInString(dumpstring, "Additional notes:")

		' read in and format the delivery name, address, phone number etc
		Form.Field("Deliv Name").Value = PCase(FindFieldInString(dumpstring, "Delivery Organisation:"),"A")
		Form.Field("Deliv Contact").Value = PCase(FindFieldInString(dumpstring, "Delivery Name:"), "")
		Form.Field("Deliv Address").Value = Pcase(FindFieldInString(dumpstring, "Delivery Address:"),"A")

		' split the delivery address into lines based on commas at the end of each line - added by Giles April 2016
		Form.Field("Deliv Address").Value = Replace(Form.Field("Deliv Address").Value, ", ", vbCrLf)

		Form.Field("Deliv Telephone").Value = FindFieldInString(dumpstring, "Delivery Phone")
        Form.Field("Deliv Postcode").Value = FindFieldInString(dumpstring, "Delivery Postcode:")

       	' code to copy quantities of items hired into new fields in customer record
		' added by Giles 19th October 2013

		' first, zero all the fields so we don't have leftover values from previous quotes
		Form.Field("Number UHF").Value = 0
		Form.Field("Number Batteries").Value = 0
		Form.Field("Number Cases").Value = 0
		Form.Field("Number EM").Value = 0
		Form.Field("Number EMC").Value = 0
		Form.Field("Number Headset").Value = 0
		Form.Field("Number Headset Big").Value = 0
		Form.Field("Number Icom").Value = 0
		Form.Field("Number Megaphone").Value = 0
		Form.Field("Number Parrot").Value = 0

		' for each item that can be hired, first locate the line of text containing the quantity and price etc for each item of equipment

		' the quantity is the first "word" in the string, so we use string functions to take it off and insert
		' into the appropriate field

		temp = FindFieldInString(dumpstring, "Standard UHF walkie-talkie")
		Form.Field("Number UHF").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Spare battery")
		Form.Field("Number Batteries").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Leather case with neck strap")
		Form.Field("Number Cases").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Standard D-type earpiece/mic")
		Form.Field("Number EM").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Semi-covert (curly tube) in-ear earpiece/mic")
		Form.Field("Number EMC").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Headset with boom microphone")
		Form.Field("Number Headset").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Big headset (noise cancelling)")
		Form.Field("Number Headset Big").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Vehicle or base station radio")
		Form.Field("Number Icom").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "25 watt megaphone")
		Form.Field("Number Megaphone").Value = Left(temp, Instr(temp, " "))

		temp = FindFieldInString(dumpstring, "Lapel speaker / microphone")
		Form.Field("Number Parrot").Value = Left(temp, Instr(temp, " "))


		' summarise the order - date and basic quantities of kit hired
        Form.Field("First Hire Date").Value = FindFieldInString(dumpstring, "Start Date:")

		temp = Cstr(Form.Field("Number UHF").Value) + " radios "
		Form.Field("First Hire Details").Value = temp + "for " + FindFieldInString(dumpstring, "Hire Length:")

		' this last bit is to deal with the "try before you buy" form emails or Sellerdeck orders
		If Form.Field("Contact Name").Value = "" Then
			Form.Field("Contact Name").Value = PCase(FindFieldInString(dumpstring, "Name"), "")
		End If

		' this is for Try Before You Buy
		If Form.Field("Name").Value = "" Then
			Form.Field("Name").Value = PCase(FindFieldInString(dumpstring, "Company/Organisation"),"A")
		End If

		' this is for Sellerdeck data
		If Form.Field("Name").Value = "" Then
			Form.Field("Name").Value = PCase(FindFieldInString(dumpstring, "Organisation"),"A")
		End If

		' this is for Try Before You Buy
		If Form.Field("Address").Value = "" Then
			Form.Field("Address").Value = Pcase(FindFieldInString(dumpstring, "Address1"),"A")
			Form.Field("Address").Value = Form.Field("Address").Value + vbcrlf + Pcase(FindFieldInString(dumpstring, "Address2"),"A")
			Form.Field("Address").Value = Form.Field("Address").Value + vbcrlf + Pcase(FindFieldInString(dumpstring, "Town/City"),"A")
			' set the "Sales Prospect" check box field to "True"
			Form.Field("Sales Prospect").Value = 1
		End If

		' this for Sellerdeck
		If Form.Field("Address").Value = "" Then
		  Form.Field("Address").Value = Pcase(FindFieldInString(dumpstring, "Address"),"A")
		  ' set the "Sales Customer" check box field to "True"
			Form.Field("Sales Customer").Value = 1
		End If

		' this is for Try Before You Buy
		If Form.Field("Postcode").Value = "" Then
			Form.Field("Postcode").Value = FindFieldInString(dumpstring, "Postcode")
		End If

		' this for Sellerdeck
		If Form.Field("Postcode").Value = "" Then
			Form.Field("Postcode").Value = FindFieldInString(dumpstring, "Post Code")
		End If

		' this is for Try Before You Buy
		If Form.Field("Telephone").Value = "" Then
			Form.Field("Telephone").Value = FindFieldInString(dumpstring, "Telephone")
		End If

		' this for Sellerdeck
		If Form.Field("Telephone").Value = "" Then
			Form.Field("Telephone").Value = FindFieldInString(dumpstring, "Phone")
		End If

		' this is for Try Before You Buy
		If Form.Field("Email").Value = "" Then
			Form.Field("Email").Value = FindFieldInString(dumpstring, "Email")
		End If

		' this for Sellerdeck
		If Form.Field("Email").Value = "" Then
			Form.Field("Email").Value = FindFieldInString(dumpstring, "email")
		End If

		' this for Sellerdeck - delivery contact name
		If Form.Field("Deliv Contact").Value = "" Then
		  Form.Field("Deliv Contact").Value = PCase(FindFieldInString(dumpstring, "Delivery Name"),"A")
		End If

		' this for Sellerdeck - delivery company/organisation
		If Form.Field("Deliv Name").Value = "" Then
		  Form.Field("Deliv Name").Value = PCase(FindFieldInString(dumpstring, "Delivery Organisation"),"A")
		End If

		' this for Sellerdeck - delivery address
		If Form.Field("Deliv Address").Value = "" Then
		  Form.Field("Deliv Address").Value = PCase(FindFieldInString(dumpstring, "Delivery Address"),"A")
		End If

		' this for Sellerdeck - delivery phone number
		If Form.Field("Deliv Telephone").Value = "" Then
		  Form.Field("Deliv Telephone").Value = PCase(FindFieldInString(dumpstring, "Delivery Phone"),"A")
		End If

		' this for Sellerdeck - delivery postcode
		If Form.Field("Deliv Postcode").Value = "" Then
		  Form.Field("Deliv Postcode").Value = PCase(FindFieldInString(dumpstring, "Delivery Post Code"),"A")
		End If


		If Form.Field("Notes").Value = "" Then
			Form.Field("Notes").Value = FindFieldInString(dumpstring, "Radio Type") + vbLf + FindFieldInString(dumpstring, "Comments") + vbLf + FindFieldInString(dumpstring, "Hear About")
			Form.Field("First Hire Details").Value = ""
		End If

        ' finally blank the "dump" field so that user changes don't get overwritten next time the record is saved
        Form.Field("Dump").Value = ""

      End If
    End Select
End Sub

