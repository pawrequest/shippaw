# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
$JsonPath = "C:\AmDesp\data\AmShip.json"

#cursor properties
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

## filter properties
#$filter.FieldName = "Delivery Name"
#$filter.FieldValue = "Test Customer"
#$filter.Qualifier = "Contains"
#$cursor.Filters.Apply()


# edit and write to db
$ed = $cursor.GetEditRowSet()
#echo $row

$ed_index = $ed.GetColumnIndex("Tracking Numbers")
$ed.ModifyRow(0, $ed_index, "SOME TRACKING",0)
$row = $ed.GetRow(0)
echo $row
$ed.Commit()



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

