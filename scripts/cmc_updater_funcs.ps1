using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher
param(
[string]$functionName,
[string]$tableName,
[string]$recordName,
[string]$updatePackageStr
)

$PSBoundParameters.GetEnumerator() | ForEach-Object {
    Write-host "$($_.Key): $($_.Value)"
}

$commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $commence_wrapper

# parse json
$updatePackageMap = @{
#    'Name' = $recordName
}
(ConvertFrom-Json $updatePackageStr).psobject.properties | Foreach { $updatePackageMap[$_.Name] = $_.Value }

$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$cursor = $db.GetCursor($tableName)


function RecordByName($recordName)
{
    Write-Host "Retrieving record by name: $recordName"

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
    write-host "Retrieving records where To Customer includes: $searchterm"
    $filter = $cursor.Filters.Create(1, [Vovin.CmcLibNet.Database.FilterType]::Field)
    $filter.FieldName = "To Customer"
    $filter.FieldValue = $searchterm
    $filter.Qualifier = "Contains"
    $result = $cursor.Filters.Apply()

    Write-Host $result Record/s Retrieved
    return $cursor.GetEditRowSet()
}


function EditRecordOverwrite($record, $package)
{
    write-host "Editing record and overwriting values"
    write-host "type of record in EditRecordOverwrite is :" $record.GetType()
    # apply update_package
    foreach ($key in $package.Keys)
    {
        $input_value = $package[$key]
        write-host "key: $key; value: $input_value"
        $ed_index = $record.GetColumnIndex($key)
        write-host "ed_index: $ed_index"
        $db_val = $record.GetRowValue(0, $ed_index)
        write-host "db_val: $db_val"
        if ($ed_index -gt -1){
        Write-Host "Replacing `"$db_val`"  with (`"$input_value`") in field `"$key`", column_id = $ed_index. result_code follows(0 = success):"
        $null = $record.ModifyRow(0, $ed_index, $input_value, 0)
        }
    }
    $record.commit()
    return $record
}


function NewRecord()
{
    Write-Host Inserting new record

    $new_record = $cursor.GetAddRowSet(1)
#    $null = $new_record.ModifyRow(0, 0, $recordName, 0)
#    $edit_resulult = EditRecordOverwrite($new_record, $package)

#    $returned = $new_record.commit()
    write-host "type of record after commit :" $new_record.GetType()
#    write-host "returned: $returned"

    return $new_record
}


function EditRecordAppend($record, $package)
{
    write-host "Editing record and appending values"
    # apply update_package
    foreach ($key in $package.Keys)
    {
        $input_value = $package[$key]
        write-host "record: $record"
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
    write-host "Printing record: $recordName"
    record = RecordByName $recordName
    Write-Host $record
    }


switch ($functionName)
{
    "EditOverwrite" {
        $to_overwrite = RecordByName $recordName
        editRecordOverwrite $to_overwrite $updatePackageMap
        $to_overwrite.commit()

    }
    "EditAppend" {
        $to_append = RecordByName $recordName
        editRecordAppend $to_append $updatePackageMap
        $to_append.commit()

    }
    "NewRecord" {


        $new_record = NewRecord
        $updatePackageMap["Name"] = $recordName
        $new_record = editRecordOverwrite $new_record $updatePackageMap
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


