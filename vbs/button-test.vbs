'''''''''''''''''''''''''''''''''''''''''''''
''''  run powershell file  ''''''''''''''''''
'''''''''''''''''''''''''''''''''''''''''''''
Dim objShell, args
' runscript = "powershell -executionpolicy bypass -noexit -file"
runscript = "powershell -executionpolicy bypass -file"
file = "C:\AmDesp\AmDesp.ps1"
args = ""
Set objShell = CreateObject("WScript.Shell")
objShell.Run (runscript & " " & file & " " & args)
Set objShell = Nothing
''''''''''''''''''''''''''''''''''''''''''''''''''''

' ''''''''''''''''''''''''''
' get args'''''''''''''''''
' '''''''''''''''''''''''''''
' Set args = Wscript.Arguments
' For Each arg In args
'   Wscript.Echo arg
' Next
' '''''''''''''''''''''''''''''