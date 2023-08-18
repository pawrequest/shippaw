using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

param(
[string]$tableName,
[string]$recordName,
[string]$updatePackageJsonStr,
[switch]$append,
[switch]$insert
)

Write-Host Update Commence - Tablename = $tableName
Write-Host Update Commence - Recordname = $recordName
Write-Host Update Commence - UpdatePackageJson = $updatePackageJsonStr

# parse json
$updatePackageMap = @{
    'Name' = $recordName
}
(ConvertFrom-Json $updatePackageJsonStr).psobject.properties | Foreach { $updatePackageMap[$_.Name] = $_.Value }

# initialise commence and get table cursor
$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $commence_wrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($tableName)

function GetRecordToEdit($cursor, $recordName)
{
    # filter table by record name
    $filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
    $filter.FieldName = "Name"
    $filter.FieldValue = $recordName
    $filter.Qualifier = "EqualTo"
    $result = $cursor.Filters.Apply()

    If ($result -eq 1)
    {
        Write-Host One Record Retrieved, proceeding to edit
        return $cursor.GetEditRowSet()
    }
    Else
    {
        throw "ERROR: Filters.Apply returned $result results"
        Write-Host ERROR: Filters.Apply returned $result results
    }
}

# create new record
If ($insert)
{
    Write-Host Inserting new record
    $record_to_edit = $cursor.GetAddRowSet(1)
}
# or edit existing
Else
{
    Write-Host Updating existing record
    $record_to_edit = GetRecordToEdit $cursor $recordName
}

# apply update_package
foreach ($key in $updatePackageMap.Keys)
{
    $input_value = $updatePackageMap[$key]
    $ed_index = $record_to_edit.GetColumnIndex($key)
    Write-Host "`"$key`" = `"$input_value`" in column_id $ed_index. result_code follows(0 = success):"

    # if -append is specified, get append existing value
    If ($append -and $input_value -is [string] -and $db_val.Length -ge 1)
    {
        $db_val = $record_to_edit.GetRowValue(0, $ed_index)
        $new_val = $input_value + "`r`n" + $db_val
        write-host "new_val: $new_val"
    }
    Else
    {
        $new_val = $input_value
    }

    $record_to_edit.ModifyRow(0, $ed_index, $new_val, 0)
}

$record_to_edit.commit()

#goodbye
$db.Close()


