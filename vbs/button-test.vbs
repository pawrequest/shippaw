' things that don't work in commence:
' 'WScript, Echo,

' Set objShell = CreateObject("Wscript.shell")
' objShell.run("powershell -executionpolicy bypass -file ""E:\Dev\AmDesp\ps1 from vbs.ps1"""),1,true
' strHomeFolder = objShell.ExpandEnvironmentStrings("%APPDATA%") & "AmDesp"
' strDataFolder = strHomeFolder & "data"
' Msgbox strDataFolder
'
' Dim fso, d, f, s
' Set fso = CreateObject("Scripting.FileSystemObject")
' Set f = fso.GetFile(filespec)
' s = UCase(f.Path) & "<BR>"
' s = s & "Created: " & f.DateCreated & "<BR>"
' s = s & "Last Accessed: " & f.DateLastAccessed & "<BR>"
' s = s & "Last Modified: " & f.DateLastModified
' ShowFileAccessInfo = s
'



Dim objFSO
Set objFSO = CreateObject("Scripting.FileSystemObject")
Dim CurrentDirectory
CurrentDirectory = objFSO.GetAbsolutePathName(".")
strFileName = CurrentDirectory & "\test.xlsx"
Wscript.Echo strFileName

