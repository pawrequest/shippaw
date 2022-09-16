$file = 'c:\temp\important_file.txt'
if (-not(Test-Path -Path $file -PathType Leaf)) {try {$null = New-Item -ItemType File -Path $file -Force -ErrorAction Stop
         Write-Host "[$file]created."}
     catch {throw $_.Exception.Message}}
 else {Write-Host "[$file] already exists."}
