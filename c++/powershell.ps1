# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher
Add-Type -Path "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll" # the default path of the assembly when you used the installer
# $cmc = New-Object -TypeName Vovin.CmcLibNet.CommenceApp
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$export = New-Object ExportEngine 
$exportPath = "export\" 

# create objects
$cursor = $db.GetCursor("Hire")
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)


# filter properties
$filter.FieldName = "ShipMe"
$filter.FieldValue = "TRUE" 
$filter.Qualifier = "True"
$cursor.Filters.Apply()

# Filter Columns
$cursor.Columns.AddDirectColumns("To Customer",  "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery tel", "Delivery Email", "Boxes", "Reference Number")
$cursor.Columns.Apply()

# export settings 
$settings = $export.Settings
$settings.ExportFormat = [ExportFormat]::Json # export to JSON
$settings.SkipConnectedItems = $false
# $settings.Canonical = $true
#$settings.HeaderMode = [HeaderMode]::Columnlabel

# export.ExportView("All Contacts-Report", $exportPath + "Contacts with labels as property names.json", $settings) #
# $export.ExportCategory("Contact", (Join-Path -Path $exportPath -ChildPath "contacts.xml")) # Join-Path is again being pedantic about PS but okay
$cursor.ExportToFile($exportPath + "Commence export.json", $settings) # create json file with custom property names 'First_Name' and 'Last_Name'.

#goodbye
$db.Close()
