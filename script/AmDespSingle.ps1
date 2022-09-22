# initialise
using namespace Vovin.CmcLibNet.Database # requires PS 5 or higher
using namespace Vovin.CmcLibNet.Export # requires PS 5 or higher

$python_exe = "C:\AmDesp\python\bin\python.exe"
$python_script = "C:\AmDesp\AmDespMain.py"
$XmlPath = "C:\AmDesp\data\AmShip.xml"

# call python script supplying jsonpath
powershell $python_exe $python_script @XmlPath

"COMPLETE"
$exit = Read-Host -Prompt '[E]xit?'
if ( $exit = "e" )
{
    Exit
}

write-host -nonewline "[e]xit?] "
$response = read-host
if ( $response -eq "n" ) { exit }

# TODO sets ShipMe to False
# TODO wrties despatchbay references to commence

# $powershell -executionpolicy ByPass -File .\Get-Printers.ps1
 #>