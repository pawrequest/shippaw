# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
$ref_name = $args[0]
$tracking_nums = $args[1]
$category = $args[2]

#cursor properties
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($category)
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)

# filter properties
$filter.FieldName = "Name"
$filter.FieldValue = $ref_name
$filter.Qualifier = "EqualTo"

If ($cursor.Filters.Apply() = 0){
    # edit and write to db
    $ed = $cursor.GetEditRowSet()
    $ed_index = $ed.GetColumnIndex("Tracking Numbers")
    $ed.ModifyRow(0, $ed_index, $tracking_nums, 0)
    $ed.Commit()
    "I just edited commence tracking numbers for $ref_name"

    $ed_index = $ed.GetColumnIndex("DB label printed")
    $ed.ModifyRow(0, $ed_index, $true, 0)

    $ed.Commit()

}
Else{
    "MULTIPLE RECORDS RETURNED"
}
#goodbye
$db.Close()

# add set db printed = true
#
#  $ed2 = $cursor.GetEditRowSet()
#    $ed2_index = $ed2.GetColumnIndex("DB label printed")
#    $ed2.ModifyRow(0, $ed2_index, 1, 0)
#    $ed2.Commit()
#    "Set DB Printed = True"
 #>