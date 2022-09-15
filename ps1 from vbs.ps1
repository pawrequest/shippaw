# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$LOC_ME = "ryzen"

# system-specific paths
if ($LOC_ME = "ryzen") {
    write "PS LOC = RYZEN"
    $JsonPath = (Resolve-Path ($PSScriptRoot + "\data\AmShip.json"))
    $python_exe = "C:\Users\RYZEN\AppData\Local\Programs\Python\Python310\python.exe"
    $python_script = "E:\Dev\AmDesp\main.py"
    $commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
}

elseif ($LOC_ME = "admin") {
    write "PS LOC = ADMIN"
    $JsonPath = (Resolve-Path ($PSScriptRoot + "\data\AmShip.json"))
    $python_exe = "C:\Users\giles\AppData\Local\Programs\Python\Python310\python.exe"
    $python_script = "C:\Paul\AmDesp\main.py"
    $commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
}

Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$export = New-Object ExportEngine
$cursor = $db.GetCursor("Hire")
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)


# filter properties
$filter.FieldName = "ShipMe"
$filter.FieldValue = "TRUE"
$filter.Qualifier = "True"
$cursor.Filters.Apply()

# Filter Columns
$cursor.Columns.AddDirectColumns("To Customer", "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery Name", "Delivery tel", "Delivery Email", "Boxes", "Reference Number",  "Delivery Contact")
$cursor.Columns.Apply()

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

# call python script supplying json
powershell $python_exe $python_script @JsonPath

"COMPLETE"

# TODO sets ShipMe to False
# TODO wrties despatchbay references to commence

# $powershell -executionpolicy ByPass -File .\Get-Printers.ps1
 #>