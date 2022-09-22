#$file = 'c:\temp\important_file.txt'
#if (-not(Test-Path -Path $file -PathType Leaf)) {try {$null = New-Item -ItemType File -Path $file -Force -ErrorAction Stop
#         Write-Host "[$file]created."}
#     catch {throw $_.Exception.Message}}
# else {Write-Host "[$file] already exists."}


#$categoryName = "Hire"
#$formName = "hire_pss"
#$fileName = "C:\AmDesp\vbs\hire_pss.VBS"
#
#CheckInFormScript ($categoryName,$formName,$fileName)

#
#python C:\AmDesp\main.py # foo bar hello=world


###################################################################
#####     calls vbscript passing args     #########################
###################################################################
#CSCRIPT C:\AmDesp\vbs\buttons.vbs arg ar2 "Arg with spaces" ##
###################################################################