
' Sample VBScript illustrating the use of CmcLibNet, a .NET wrapper around the Commence API
' CmcLibNet was developed for use from within .NET applications.
' Because it was also made 'COM-visible', it is possible to use it from any COM capable language
' Therefore, you can use it from Commence Form Scripts as well.
' This example illustrates how to use CmcLibNet from VBScript.
' For this example to work, CmcLibNet has to be registered for ComInterop
' If you did not check that option in the installer,
' you have to register it manually with regasm.exe.

' CmcLibNet contains several 'components': CommenceApp, Database, Export and Services
' * CommenceApp: get info on the Commence.exe application
' * Database: anything that has to do with manipulation the Commence database
' * Export: the export engine contained in CmcLibNet
' * Services: some esoteric features, not shown here.

' Get a reference to the Commence application through CmcLibNet.
Dim app : Set app = CreateObject("CmcLibNet.CommenceApp")
' Display name of currently opened database.
MsgBox "Commence database name: " & app.Name ' this is a silly example of course
' Let's assume we're completely done with our app object.
app.Close
' A note on the Close method:
' Because .NET and COM are very different techniques, you *must* explicitly call the Close method.
' Basically, if you are not using CmcLibNet from a .NET language, make sure you call Close.
' It is *not* sufficient to just set the reference variable to Nothing.
' Failing to call Close() will keep the commence.exe running in the background when the user closes Commence.
' In that case you have to manually end the process in the Windows Task Manager.
' As a rule of thumb: when you CreateObject("CmcLibNet.[Something]"), you must Close it.
' (The story gets weirder though: when used from the Windows Scripting Host,
' which is not .NET, it is not needed. Don't know why.)
'Set app = Nothing ' Optional, but regarded good practice.

' Let's show something more useful.
' Assume we want a list of people connected to account "Concorde Aviation Ltd".
' This means talking to the Commence database.
' Get a reference to the Commence database through CmcLibNet.
Dim db : Set db = CreateObject("CmcLibNet.Database")

' Get a cursor. Note how we do not supply any flags, just the category name.
' This gets a cursor on a category with default flags.
' It is equivalent to [FormOA.CommenceDB.]GetCursor(0, "Contact", 0)
' If you want a cursor on a view, CmcLibNet uses a different parameter order than the Commence API:
' GetCursor("MyView", 1, 0) where 1 indicates you want a view and 0 is the default flag.
' Refer to the documentation for the values of the flags used in CmcLibNet.
' If their meaning is equivalent to their Commence counterpart, they have the same value.
' We will only be dealing with category data, so we don't need any flags here.
' We can just do:
Dim cur : set cur = db.GetCursor("Hire")

' The cursor will contain all items in Contact.
' Let's see how many we have:
MsgBox cur.RowCount & " items in Contact category."

' To take full advantage of the CmcLibNet way of filtering,
' filters (i.e., use SetFilter() and SetLogic()).
' Get a reference to the filters 'factory'. Every cursor in CmcLibNet has one.
Dim filters : Set filters = cur.Filters

' Create a CTI filter (Connection-To-Item)
field_type = 0
cti_type = 1
dim filtertype = field_type

Dim f : Set f = filters.Create(1, filtertype)

'Field Filter'


' CTI Filter (#1):'
f.Connection = "Relates to" ' connection names are case-sensitive!
f.Category = "Account"
f.Item = "Concorde Aviation Ltd"

' Field Filter'
f.FieldName = "ShipMe"
F.FieldValue = "TRUE"
F.Qualifier = "True"
F.Filters.Apply()




' We have defined a filter now. Remember you can create up to 8 filters.
' We now have to apply them. Call the Apply method of the filtering 'engine'.
' Apply will return the number of items in the cursor after applying the filters,
' so we can check how many items we have now.
' Note that does not guarantee your filters all worked as *you* intended,
' it just means Commence accepted them as valid filters.
Msgbox filters.Apply & " items in cursor after applying filters."

' Okay, 1 item left. Let's assume we're interested in the Name of the Contact and the business e-mail.
' Define those columns:
cur.SetColumn 0, db.GetNameField("Contact") ' get whatever the name field in the category is called
cur.SetColumn 1, "emailBusiness"
' There a few things to note here.
' First of all, we didn't specify an option flag SetColumn(index,fieldname,option flag)
' Second, we used a built-in CmcLibNet function te get the name of the Name field

' This 'old-fashioned' way of setting columns works fine
' You can also set them in batch by passing them as an Array.
' Do *not* mix single- and batchmode. That's why the following line is commented out.
'cur.SetColumns Array(db.GetNameField("Contact"), "emailBusiness")

' You can set related columns like you would in the Commence API directly
' Related columns cannot be set in batch mode.
' Assume we want to know the Employee Type of the Contact.
cur.SetRelatedColumn 2, "Relates to", "contactType", "contacttypeKey" ' again, no additional flag required
' Let's see how many columns we have now:
MsgBox cur.ColumnCount & " columns were set in cursor"
'cur.ExportToFile("C:\Temp\MyExportFile.xml")

' Okay, we have 1 item and 3 columns. Let's do something with the data.
' Let's export it to file.
' One of the features unique to CmcLibNet is the ability to directly export cursors
' You could call cur.ExportToFile("MyExportFile.xml")
' This would produce a XML file. Do not be fooled by the .xml extension,
' it has nothing to do with the XML export format, XML is just the default.
' I want to show you something a little more fancy. Let's export to JSON!
' For this, you have to supply an extra parameter, a 'ExportSettings' object.
' This is a feature of the CmcLibNet export engine, so we have to talk to that
Dim exportEngine : Set exportEngine = CreateObject("CmcLibNet.Export")
' The export engine exposes a settings feature unsurprisingly called 'Settings'
Dim settings : Set settings = exportEngine.Settings ' The Settings thingie is an object, so we have to use 'Set'
' Settings has a bunch of properties you can set.
' One of them is the export format. CmcLibNet currently supports Text, HTML, Microsoft Excel, XML and JSON.
' JSON has a value of 1
settings.ExportFormat = 1
cur.ExportToFile "C:\temp\sampleContactExport.json", settings
' Which will produce a file C:\temp\sampleContactExport.json. (change your path accordingly)

' That almost concludes the example. There is a lot more to tell, but this covers the basics.
' Please refer to the documentation on http://cmclibnet.vovin.nl for more.

' Remember, you have to close the references to CmcLibNet.
' If you got a script error at some point (we did not include any error checking!),
' the lines below will not be called and commence.exe will keep running after closing Commence
' This is extremely annoying, and something I hope to fix in the future. But do not keep you hopes up.
' Just be careful to include appropriate error-checking in your production code.
Set settings = Nothing
exportEngine.Close
db.close
Set exportEngine = Nothing
Set db = Nothing
MsgBox "VBScript example of using CmcLibNet finished."