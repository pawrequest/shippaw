' As a rule of thumb: when you CreateObject("CmcLibNet.[Something]"), you must Close it.
Dim db : Set db = CreateObject("CmcLibNet.Database")
Dim cur : set cur = db.GetCursor("Hire")
Dim filters : Set filters = cur.Filters
Dim f : Set f = filters.Create(1, 1) ' Create(filterClause, filterType); Clause is position for ordering, upto 8; filtertypes: 0:Field, 1:ConnectionToItem
f.Connection = "To" ' connection names are case-sensitive!
f.Category = "Customer"
f.Item = "4CM"
' Msgbox filters.Apply & " items in cursor after applying filters."
cur.SetColumns Array(db.GetNameField("Hire"), "Delivery Email")
cur.SetRelatedColumn 2, "To", "Telephone", "TelephoneKey" 
' MsgBox cur.ColumnCount & " columns were set in cursor"
Dim exportEngine : Set exportEngine = CreateObject("CmcLibNet.Export")
Dim settings : Set settings = exportEngine.Settings ' The Settings thingie is an object, so we have to use 'Set'
settings.ExportFormat = 1 ' JSON has a value of 1
settings.SkipConnectedItems = false
settings.Canonical = true
cur.ExportToFile "C:\test\sampleContactExport.json", settings
' close:
Set settings = Nothing
exportEngine.Close
db.close
Set exportEngine = Nothing
Set db = Nothing