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




The following VBScript code opens a copy of the currently running script with Notepad.
 	CopyCode imageCopy Code

Set WshShell = WScript.CreateObject("WScript.Shell")
WshShell.Run "%windir%\notepad " & WScript.ScriptFullName

The following VBScript code does the same thing, except it specifies the window type, waits for Notepad to be shut down by the user, and saves the error code returned from Notepad when it is shut down.
 	CopyCode imageCopy Code

Set WshShell = WScript.CreateObject("WScript.Shell")
Return = WshShell.Run("notepad " & WScript.ScriptFullName, 1, true)

Collapse imageExample 2

The following VBScript code opens a command window, changes to the path to C:\ , and executes the DIR command.
 	CopyCode imageCopy Code

Dim oShell
Set oShell = WScript.CreateObject ("WSCript.shell")
oShell.run "cmd /K CD C:\ & Dir"
Set oShell = Nothing