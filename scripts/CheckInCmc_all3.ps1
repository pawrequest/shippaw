# only run to update vbs in commence
# initialise cmclib

using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$CommenceWrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $CommenceWrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase

## check in hire-detail-vbs
$HireForm = "hire_pss23"
$HireFormVbs = "C:\AmDesp\vbs\hire_pss.VBS"
$HireChecked = $db.CheckInFormScript("Hire", $HireForm, $HireFormVbs)
Write-Host "Hire Form checked in" is $HireChecked

##check in Customer-detail-vbs
$CustomerForm = "customer_pss23"
$CustomerFormVbs = "C:\AmDesp\vbs\customer_pss.VBS"
$CustomerChecked = $db.CheckInFormScript("Customer", $CustomerForm, $CustomerFormVbs )
Write-Host "Customer Form Form checked in" is $CustomerChecked

##check in sale detail form
$SaleForm = "sale_pss"
$SaleFormVbs = "C:\AmDesp\vbs\sale_pss.VBS"
$SaleChecked = $db.CheckInFormScript("Sale", $SaleForm, $SaleFormVbs )
Write-Host "Sale Form Form checked in" is $SaleChecked

### Goodbye
$db.Close()

# end of vbs
