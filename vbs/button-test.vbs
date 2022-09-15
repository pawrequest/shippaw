Dim objShell
Set objShell = CreateObject(“Wscript.shell”)
objShell.run(“powershell -noexit -file C:\paul\AmDesp\AmDespPowershellAmherstAdmin.ps1”)

' It is also possible to run a specific Windows PowerShell command or series of commands from the VBScript script. This technique is shown here.
'
' objShell.run(“powershell -noexit -command “”&{0..15 | % {Write-Host -foreground $_ ‘Hello World’ }}”””)
'
' Note   Keep in mind that you are writing in VBScript. Therefore, you need to escape the quotation marks with another pair of quotation marks. Also, remember that you use REM to comment out a line, and not the pound sign character (#) that is used in Windows PowerShell.


' working
' 		Case "CommandButton20"
' 		    Dim objShell
'             Set objShell = CreateObject("Wscript.shell")
'             objShell.run("powershell -executionpolicy bypass -noexit -file c:\fso\helloworld.ps1 C:\paul\AmDesp\test.ps1")

