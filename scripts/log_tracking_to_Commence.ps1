# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"

$category = $args[0]
$ref_name = $args[1]
$shipment_id = $args[2]
$outbound = $args[3]

Write-Host LOG TO COMMENCE SCRIPT - SHIPMENT TYPE - $ID_direction
Write-Host LOG TO COMMENCE SCRIPT -  REF NAME - $ref_name
Write-Host LOG TO COMMENCE SCRIPT -  SHIP ID - $ref_name
Write-Host LOG TO COMMENCE SCRIPT -  OUTBOUND - $outbound

#cursor properties
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($category)
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)

# filter properties
$filter.FieldName = "Name"
$filter.FieldValue = $ref_name
$filter.Qualifier = "EqualTo"

if ($outbound -eq 'True'){
    Write-Host "SHIPMENT IS OUTBOUND"
    $box_to_tick = "DB label printed"
    $ID_direction = "Outbound ID"
}
Else {
    Write-Host "SHIPMENT IS INBOUND"
    $box_to_tick = "Pickup Arranged"
    $ID_direction = "Inbound ID"
}

If ($cursor.Filters.Apply() = 0){
    # edit and write to db
    $ed = $cursor.GetEditRowSet()

    $ed_index = $ed.GetColumnIndex($box_to_tick)
    $ed.ModifyRow(0, $ed_index, $true, 0)
    $ed.commit

    $ed_index = $ed.GetColumnIndex($ID_direction)
    $ed.ModifyRow(0, $ed_index, $shipment_id, 0)
    $ed.Commit()

}

Else{
    "ERROR IN POWERSHELL SCRIPT"
    "MULTIPLE RECORDS RETURNED?"
    "LOG TO COMMENCE SCRIPT - SHIPMENT TYPE - $ID_direction"
    "LOG TO COMMENCE SCRIPT -  REF NAME - $ref_name"
    "LOG TO COMMENCE SCRIPT -  SHIP ID - $ref_name"
    "LOG TO COMMENCE SCRIPT -  ISARETURN - $outbound"
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