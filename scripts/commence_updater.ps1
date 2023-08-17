using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

param(
    [string]$tableName,
    [string]$recordName,
    [string]$updatePackageJsonStr
)

Write-Host Update Commence - Tablename = $tableName
Write-Host Update Commence - Recordname = $recordName
Write-Host Update Commence - UpdatePackage = $updatePackageJsonStr

# parse json
$processStatus | ConvertTo-Json > $jsonOutput
$updatePackageMap = @{}
(ConvertFrom-Json $updatePackageJsonStr).psobject.properties | Foreach { $updatePackageMap[$_.Name] = $_.Value }



# db / cursor properties
$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($tableName)

# filter properties
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
$filter.FieldName = "Name"
$filter.FieldValue = $recordName
$filter.Qualifier = "EqualTo"

If ($cursor.Filters.Apply() = 0){
    Write-Host Record Retrieved, proceeding to edit

    $ed = $cursor.GetEditRowSet()
    foreach ($key in $updatePackageMap.Keys) {
        Write-Host Editing field $key with value $updatePackageMap[$key]
        $ed_index = $ed.GetColumnIndex($key)
        write-host "ed_index: $ed_index"
        $ed.ModifyRow(0, $ed_index, $updatePackageMap[$key], 0)
}
    $ed.commit()
}
Else{
    Write-Host ERROR IN POWERSHELL SCRIPT MULTIPLE RECORDS RETURNED?
}

#goodbye
$db.Close()
