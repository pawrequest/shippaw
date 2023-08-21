using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher
$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $commence_wrapper

param(
[switch]$functionName,
[string]$tableName,
[string]$recordName,
[string]$updatePackageStr
)



# parse json
$updatePackageMap = @{
    'Name' = $recordName
}
(ConvertFrom-Json $updatePackageJsonStr).psobject.properties | Foreach { $updatePackageMap[$_.Name] = $_.Value }


# initialise commence and get table cursor
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($tableName)

function RecordByName($recordName)
{
    # filter table by record name
    $filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
    $filter.FieldName = "Name"
    $filter.FieldValue = $recordName
    $filter.Qualifier = "EqualTo"
    $result = $cursor.Filters.Apply()

    If ($result -eq 1)
    {
        Write-Host One Record Retrieved
        return $cursor.GetEditRowSet()
    }
    Else
    {
        Write-Host ERROR: Filters.Apply returned $result results
    }
}


function HireRecordsCustomerIncludes($searchterm)
{
    $filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
    $filter.FieldName = "To Customer"
    $filter.FieldValue = $searchterm
    $filter.Qualifier = "Contains"
    $result = $cursor.Filters.Apply()

    Write-Host $result Record/s Retrieved
    return $cursor.GetEditRowSet()
}


function NewRecord($recordName, $update_package)
{
    Write-Host Inserting new record

    $new_record = $cursor.GetAddRowSet(1)
    $new_record.ModifyRow(0, 0, $recordName, 0)

    editRecordOverwrite $new_record $update_package

    return $new_record
}

function EditRecordOverwrite($record, $package)
{
    # apply update_package
    foreach ($key in $package.Keys)
    {
        $input_value = $package[$key]
        $ed_index = $record.GetColumnIndex($key)
        $db_val = $record.GetRowValue(0, $ed_index)

        Write-Host "Replacing `"$db_val`"  with (`"$input_value`") in field `"$key`", column_id = $ed_index. result_code follows(0 = success):"
        $record.ModifyRow(0, $ed_index, $input_value, 0)
    }
}
function EditRecordAppend($record, $package)
{
    # apply update_package
    foreach ($key in $package.Keys)
    {
        $input_value = $package[$key]
        $ed_index = $record.GetColumnIndex($key)
        $db_val = $record.GetRowValue(0, $ed_index)

        # if input type is a string and current value is 1+, append
        If ($input_value -is [string] -and $db_val.Length -ge 1)
        {
            Write-Host " Appending `"$input_value`"  to existing value (`"$db_val`") in field `"$key`", column_id = $ed_index. result_code follows(0 = success):"
            $new_val = $input_value + "`r`n" + $db_val
            write-host "new_val: $new_val"
        }
        Else
        {
            Write-Host "Replacing `"$db_val`"  with (`"$input_value`") in field `"$key`", column_id = $ed_index. result_code follows(0 = success):"
            $new_val = $input_value
        }

        $record.ModifyRow(0, $ed_index, $new_val, 0)
    }
}

function PrintRecord($recordName)
{
    record = RecordByName $recordName
    Write-Host $record
    }

switch ($FunctionToExecute)
{
    "EditOverwrite" {
        $record_to_edit = RecordByName $recordName
        editRecordOverwrite $record_to_edit $updatePackageMap
        $record_to_edit.commit()

    }
    "EditAppend" {
        $record_to_edit = RecordByName $recordName
        editRecordAppend $record_to_edit $updatePackageMap
        $record_to_edit.commit()

    }
    "NewCustomer" {
        $record_to_edit = CreateRecord $recordName $updatePackageMap
        $record_to_edit.commit()

    }
    "HiresByCustomer" {
        hires = HireRecordsByCustomerIncludes $recordName
        Write-Host $hires

    }
    "PrintRecord" {
        PrintRecord $recordName
    }
}



#goodbye
$db.Close()


