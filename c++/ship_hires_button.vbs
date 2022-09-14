Dim JsonPath; JsonPath = C:\paul\AmDesp\data\AmShip.json

'create app, db, cur'
Dim app : Set app = CreateObject("CmcLibNet.CommenceApp")
Dim db : Set db = CreateObject("CmcLibNet.Database")
Dim cur : set cur = db.GetCursor("Hire")
MsgBox cur.RowCount & " items in Hire category."
' create filter
Dim filters : Set filters = cur.Filters
' Create a CTI filter (Connection-To-Item)
Dim f : Set f = filters.Create(1, 0)
f.FieldName = "ShipMe"
f.FieldValue = "TRUE"
f.Qualifier = "True"
f.Filters.Apply()
Msgbox filters.Apply & " items in cursor after applying filters."
cur.SetColumns Array(db.GetNameField("To Customer", "Send Out Date")

' set related columns
' Related columns cannot be set in batch mode.
' Do *not* mix single- and batchmode. That's why the following line is commented out.
' Assume we want to know the Employee Type of the Contact.
' cur.SetRelatedColumn 2, "Relates to", "contactType", "contacttypeKey" ' again, no additional flag required

MsgBox cur.ColumnCount & " columns were set in cursor"

Dim exportEngine : Set exportEngine = CreateObject("CmcLibNet.Export")
Dim settings : Set settings = exportEngine.Settings ' The Settings thingie is an object, so we have to use 'Set'
settings.ExportFormat = 1 ' json format'
cur.ExportToFile "C:\temp\sampleContactExport.json", settings



Dim settings = export.Settings
settings.ExportFormat = [ExportFormat]::Json # export to JSON
settings.SkipConnectedItems = false
' settings.Canonical = $true
' settings.HeaderMode = [HeaderMode]::Columnlabel
cursor.ExportToFile(JsonPath, settings)