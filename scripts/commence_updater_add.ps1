using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

param(
[string]$tableName,
[string]$recordName,
[string]$updatePackageJsonStr
)

Write-Host Update Commence - Tablename = $tableName
Write-Host Update Commence - Recordname = $recordName
Write-Host Update Commence - UpdatePackageJson = $updatePackageJsonStr

# parse json
$updatePackageMap = @{ }
(ConvertFrom-Json $updatePackageJsonStr).psobject.properties | Foreach { $updatePackageMap[$_.Name] = $_.Value }

# initialise commence and get table cursor
$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($tableName)

# filter table by record name
$filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
$filter.FieldName = "Name"
$filter.FieldValue = $recordName
$filter.Qualifier = "EqualTo"
$result = $cursor.Filters.Apply()

If ($result -eq 1) {
    Write-Host Record Retrieved, proceeding to edit

    $ed = $cursor.GetEditRowSet()
    foreach ($key in $updatePackageMap.Keys) {
#        Write-Host Editing field `"$key`" with value `"$updatePackageMap[$key]`"
        Write-Host "Editing field `"$key`" with value `"$($updatePackageMap[$key])`""

        $ed_index = $ed.GetColumnIndex($key)
        $current_val = $ed.GetRowValue(0, $ed_index)
        write-host "current_val: $current_val"

        if ($updatePackageMap[$key] -is [string] -and $current_val.Length -ge 3){
            $new_val = $current_val + "`r`n" + $updatePackageMap[$key] }
        else {
            $new_val = $updatePackageMap[$key] }

        write-host "new_val: $new_val"
        $ed.ModifyRow(0, $ed_index, $new_val, 0)
    }
    $ed.commit()
}

Else
{
    Write-Host "ERROR IN POWERSHELL SCRIPT - Filters.Apply() returned " $result
}

#goodbye
$db.Close()
