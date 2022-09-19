# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$PythonExe = "C:\AmDesp\python\bin\python.exe"
$PythonScript = "C:\AmDesp\main.py"
$CommenceWrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
$JsonPath = "C:\AmDesp\data\AmShip.json"
$HireForm = "hire_pss"
$CustomerForm = "customer_pss"
$HireFormVbs = "C:\AmDesp\vbs\hire_pss.VBS"
$CustomerFormVbs = "C:\AmDesp\vbs\customer_pss.VBS"

##cursor properties
Add-Type -Path $CommenceWrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
#$export = New-Object ExportEngine
#$cursor = $db.GetCursor("Hire")
#$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)

# check in hire-detail-script
$HireChecked = $db.CheckInFormScript("Hire", $HireForm, $HireFormVbs)
Write-Host "Hire Form checked in" is $HireChecked


# check in customer-detail-script
$SaleChecked = $db.CheckInFormScript("Customer", $CustomerForm, $CustomerFormVbs )
Write-Host "Sale Form checked in" is $SaleChecked


## filter properties
#$filter.FieldName = "ShipMe"
#$filter.FieldValue = "TRUE"
#$filter.Qualifier = "True"
#$cursor.Filters.Apply()

# Filter Columns
#$cursor.Columns.AddDirectColumns("To Customer", "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery Name", "Delivery tel", "Delivery Email", "Boxes", "Reference Number",  "Delivery Contact")
#$cursor.Columns.AddDirectColumns("To Customer","Reference Number", "Name")
#$cursor.Columns.Apply()

## export settings
#$settings = $export.Settings
#$settings.ExportFormat = [ExportFormat]::Json # export to JSON
#$settings.SkipConnectedItems = $false
#$settings.Canonical = $true
#$settings.HeaderMode = [HeaderMode]::Columnlabel

# export.ExportView("All Contacts-Report", $exportPath + "Contacts with labels as property names.json", $settings) #
# $export.ExportCategory("Contact", (Join-Path -Path $exportPath -ChildPath "contacts.xml")) # Join-Path is again being pedantic about PS but okay
#$cursor.ExportToFile($JsonPath, $settings)


#goodbye
$db.Close()
# call python script supplying jsonpath
powershell $PythonExe $PythonScript @JsonPath

"COMPLETE"

# TODO sets ShipMe to False
# TODO wrties despatchbay references to commence

# $powershell -executionpolicy ByPass -File .\Get-Printers.ps1
 #>