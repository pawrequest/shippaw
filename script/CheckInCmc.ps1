# only run to update vbs in commence
# initialise cmclib

using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$CommenceWrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
Add-Type -Path $CommenceWrapper
$db = New-Object -TypeName Vovin.CmcLibNet.Database.CommenceDatabase

## check in hire-detail-script
$HireForm = "hire_pss"
$HireFormVbs = "C:\AmDesp\script\hire_pss.VBS"
$HireChecked = $db.CheckInFormScript("HireShipment", $HireForm, $HireFormVbs)
Write-Host "HireShipment Form checked in" is $HireChecked

##check in deliveryCustomer-detail-script
$CustomerForm = "customer_pss"
$CustomerFormVbs = "C:\AmDesp\script\customer_pss.VBS"
$CustomerChecked = $db.CheckInFormScript("Customer", $CustomerForm, $CustomerFormVbs )
Write-Host "Customer Form Form checked in" is $CustomerChecked

### Goodbye
$db.Close()

# end of script
