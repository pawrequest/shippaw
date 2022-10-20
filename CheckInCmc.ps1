# only run to update vbs in commence
# initialise cmclib

using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$CommenceWrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $CommenceWrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase

## check in hire-detail-vbs
$HireForm = "hire_pss"
$HireFormVbs = "C:\AmDesp\vbs\hire_pss.VBS"
$HireChecked = $db.CheckInFormScript("Hire", $HireForm, $HireFormVbs)
Write-Host "Hire Form checked in" is $HireChecked

##check in Customer-detail-vbs
$CustomerForm = "customer_pss"
$CustomerFormVbs = "C:\AmDesp\vbs\customer_pss.VBS"
$CustomerChecked = $db.CheckInFormScript("Customer", $CustomerForm, $CustomerFormVbs )
Write-Host "Customer Form Form checked in" is $CustomerChecked

### Goodbye
$db.Close()

# end of vbs
