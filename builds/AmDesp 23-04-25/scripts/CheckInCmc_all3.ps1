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

#    $vbsfile = 'E:\Dev\AmDesp\scripts\' + $formname + '.vbs' #switch for unbuilt changes
    $vbsfile = 'C:\paul\AmDesp\scripts\' + $formname + '.vbs'
#    $vbsfile = $env:LOCALAPPDATA + '\pss\AmDesp\scripts\' + $formname + '.vbs'
#    $vbsfile = 'r:\paul_notes\pss\AmDesp\scripts\' + $formname + '.vbs'
#    $vbsfile = 'r:\paul_notes\pss\AmDesp\scripts\' + $formname + '.vbs'
#    write-Host $vbsfile
    $formchecked = $db.CheckInFormScript($category, $formname, $vbsfile)
    Write-Host $category " form checked in" is $formchecked
}
### Goodbye
$db.Close()
Read-Host -Prompt "Press Enter to exit"
exit

