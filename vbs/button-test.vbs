Set objShell = CreateObject("Wscript.shell")
objShell.run("powershell -executionpolicy bypass -noexit -file ""E:\Dev\AmDesp\ps1 from vbs.ps1"""),1,true
strHomeFolder = objShell.ExpandEnvironmentStrings("%APPDATA%") & "AmDesp"
strDataFolder = strHomeFolder & "data"
Msgbox strDataFolder