Dim python_exe, python_script, commence_wrapper, JsonPath
python_exe = "C:\AmDesp\python\bin\python.exe"
python_script = "C:\AmDesp\main.py"
commence_wrapper = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
JsonPath = "C:\AmDesp\data\AmShip.json"

' RetVal = Shell(python_exe & python_script)


Dim oShell, source_code_path, variable1, currentCommand, my_command
SET oShell = WScript.CreateObject("Wscript.Shell")
my_command = python_exe + " " + python_script + " " + JsonPath
currentCommand = "cmd /c " & Chr(34) & python_script & " " & JsonPath & Chr(34)
' WScript.echo currentCommand
oShell.run my_command,1,True
