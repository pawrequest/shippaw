# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"

#cursor
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor('HIRE')

# filter
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
$today = Get-Date -format "dd/MM/yyyy"
$filter.FieldName = "Send Out Date"
$filter.Qualifier = "On"
$filter.FieldValue = $today


$num_records = $cursor.Filters.Apply()

$cursor.Columns.AddDirectColumns("Radio Type", "Number UHF")
$cursor.Columns.Apply()

$export = New-Object ExportEngine
$exportPath = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop) + "\today_hires.json"



#write $cursor.ColumnCount

Read-Host


write $num_records

$db.Close()

