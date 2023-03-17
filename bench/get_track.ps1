# # initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
$ref_num = $args[0]
#$ref_num = "29,372"

#cursor properties
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor("Hire")
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)

# filter properties
$filter.FieldName = "Reference Number"
$filter.FieldValue = $ref_num
$filter.Qualifier = "EqualTo"
$cursor.Filters.Apply()

# columns
$cursor.Columns.AddDirectColumns("Tracking Numbers")
$cursor.Columns.Apply()

$outy = $cursor.ReadRow(0)
return $outy

#return $cursor

#goodbye
$db.Close()

# add set db printed = true
