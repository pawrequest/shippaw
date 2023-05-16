# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$CommenceWrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $CommenceWrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase
$categories = "hire", "sale", "customer"
foreach ($category in $categories)
{
    $formname = $category + '_pss'
    $vbsfile = 'C:\paul\AmDesp\scripts\' + $formname + '.vbs'
    $formchecked = $db.CheckInFormScript($category, $formname, $vbsfile)

    Write-Host $category "form checked in" is $formchecked
    write-Host Form Name = $formname
    write-Host VBS = $vbsfile
    Write-Host

}
### Goodbye
$db.Close()
exit

