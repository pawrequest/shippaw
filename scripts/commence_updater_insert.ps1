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
$updatePackageMap = @{'Name' = $recordName }
(ConvertFrom-Json $updatePackageJsonStr).psobject.properties | Foreach { $updatePackageMap[$_.Name] = $_.Value }

# get commence db table
$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($tableName)

# create blank record
$new_record = $cursor.GetAddRowSet(1)

# set record rows from input json (plus name from $recordname)
foreach ($key in $updatePackageMap.Keys) {
    $ed_index = $new_record.GetColumnIndex($key)
    Write-Host "`"$key`" = `"$($updatePackageMap[$key])`" in column_id $ed_index. result_code follows(0 = success):"
    $new_record.ModifyRow(0, $ed_index, $updatePackageMap[$key], 0)
}

$confirmation = Read-Host -Prompt "Do you want to commit the new record? (y)"
if ($confirmation -eq "y")
{
    $new_record.Commit()
}

#goodbye
$db.Close()
