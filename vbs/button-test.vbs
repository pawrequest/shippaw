Dim objShell
Set objShell = CreateObject("Wscript.shell")
objShell.run("powershell -executionpolicy bypass -file ""C:\AmDesp\AmDesp.ps1"),1,true