# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$python_exe = "C:\AmDesp\python\bin\python.exe"
$python_script = "C:\AmDesp\main.py"
$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
$JsonPath = "C:\AmDesp\data\AmShip.json"

#cursor properties
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$export = New-Object ExportEngine
$cursor = $db.GetCursor("Hire")
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)

$checked = $db.CheckInFormScript("Hire", "hire_pss", "C:\AmDesp\vbs\amherst-hire-form-pss.VBS")
Write-Host Form checked is $checked
"Script Checkled In"


# filter properties
$filter.FieldName = "ShipMe"
$filter.FieldValue = "TRUE"
$filter.Qualifier = "True"
$cursor.Filters.Apply()

# Filter Columns
#$cursor.Columns.AddDirectColumns("To Customer", "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery Name", "Delivery tel", "Delivery Email", "Boxes", "Reference Number",  "Delivery Contact")
#$cursor.Columns.AddDirectColumns("To Customer","Reference Number", "Name")
#$cursor.Columns.Apply()

# export settings 
$settings = $export.Settings
$settings.ExportFormat = [ExportFormat]::Json # export to JSON
$settings.SkipConnectedItems = $false
#$settings.Canonical = $true
#$settings.HeaderMode = [HeaderMode]::Columnlabel

# export.ExportView("All Contacts-Report", $exportPath + "Contacts with labels as property names.json", $settings) #
# $export.ExportCategory("Contact", (Join-Path -Path $exportPath -ChildPath "contacts.xml")) # Join-Path is again being pedantic about PS but okay
$cursor.ExportToFile($JsonPath, $settings)


#goodbye
$db.Close()

# call python script supplying jsonpath
powershell $python_exe $python_script @JsonPath

"COMPLETE"

# TODO sets ShipMe to False
# TODO wrties despatchbay references to commence

# $powershell -executionpolicy ByPass -File .\Get-Printers.ps1
 #>