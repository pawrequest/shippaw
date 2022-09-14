' Sub RunPythonScript()

' 'Declare Variables
' Dim objShell As Object
' Dim PythonExe, PythonScript As String

' 'Create a new Object shell.
' Set objShell = VBA.CreateObject(“Wscript.Shell”)

' PythonExe = 'C:\Users\RYZEN\AppData\Local\Programs\Python\Python310\python.exe'
' ' PythonScript = “commence scripts\python-from-vbs.py”
' PythonScript = 'E:\Dev\Amherst_Despatch\commence scripts\python-from-vbs.py'


' 'Run the Python Script
' objShell.Run PythonExe & PythonScript

' End Sub

RetVal = Shell('C:\Users\giles\AppData\Local\Programs\Python\Python310\python.exe' & 'C:\paul\AmDesp\c++\python-from-vbs.py')