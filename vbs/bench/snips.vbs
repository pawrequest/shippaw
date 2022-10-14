'Public Function CheckInFormScript (Hire, hire_pss, "C:\AmDesp\vbs\amherst-hire-form-pss.VBS") As Boolean
Dim categoryName, formName, fileName
categoryName = "Hire"
formName = "hire_pss"
fileName = "C:\AmDesp\vbs\amherst-hire-form-pss.VBS"


' Public Function CheckInFormScript (
' 	categoryName As String,
' 	formName As String,
' 	fileName As String
' ) As Boolean

CheckInFormScript (categoryName,formName,fileName)


' check for and make file'
Dim oTxtFile
With (CreateObject("Scripting.FileSystemObject"))
  If .FileExists(JsonPath) Then
    Msgbox "File Exist"
  Else
    Set oTxtFile = .CreateTextFile(JsonPath)
    Msgbox "File Created"
  End If
End With

            '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''''''''   Runs Amdesp direct with Powershell     ''''''''''
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
		    Dim python_exe, python_script, commence_wrapper, JsonPath
            python_exe = "C:\AmDesp\python\bin\python.exe"
            python_script = "C:\AmDesp\AmDespMain.py"
            XmlPath = "C:\AmDesp\data\AmShip.xml"
            Dim oShell, source_code_path, variable1, currentCommand, my_command
            SET oShell = CreateObject("Wscript.Shell")
            RunCmd = "powershell -executionpolicy bypass -noexit -file" & Chr(34) & python_script & " " & XmlPath & Chr(34)
'             Msgbox "RUN PYTHON"
            oShell.run RunCmd,1,true


'  ' ship hires
' Dim objShell
' Set objShell = CreateObject("Wscript.shell")
' objShell.run("powershell -executionpolicy bypass -noexit -file ""C:\AmDesp\AmDesp.ps1"""),1,true

' 'test'
' Dim val
' For val = 1 to 4
' Msgbox "Hello All. I am Number:" & val
' Next
'
' ' dim fs,fname
' ' set fs=Server.CreateObject("Scripting.FileSystemObject")
' ' set fname=fs.CreateTextFile("c:\test.txt",true)
' ' fname.WriteLine("Hello World!")
' ' fname.Close
' ' set fname=nothing
' ' set fs=nothing


' MyCheck = VarType(IntVar)   ' Returns 2.

' Option Explicit
'
' dim list
' Set list = CreateObject("System.Collections.ArrayList")
' list.Add "Banana"
' list.Add "Apple"
' list.Add "Pear"
'
' list.Sort
' list.Reverse
'
' wscript.echo list.Count                 ' --> 3
' wscript.echo list.Item(0)               ' --> Pear
' wscript.echo list.IndexOf("Apple", 0)   ' --> 2
' wscript.echo join(list.ToArray(), ", ") ' --> Pear, Banana, Apple
'

' Dim oJsonParser, oMySubobject, oMyMainObject, sJsonString
' Set oJsonParser = CreateJsonParser()
' Set oMySubobject = CreateObject("Scripting.Dictionary")
' Set oMyMainObject = CreateObject("Scripting.Dictionary")
'
' Call oMySubobject.Add("intVal", CInt(1))
' Call oMySubobject.Add("doubleVal", CDbl(1.2))
' Call oMySubobject.Add("stringVal", "TextA")
'
' Call oMyMainObject.Add("subobject", oMySubobject)
' Call oMyMainObject.Add("array", Array("TextB", 5678, True))
' Call oMyMainObject.Add("timestamp", oJsonParser.CreateDateTime(Now, True))


' Const ENCODE = FALSE
' Const DECODE = TRUE
'
' val = "asdf\\\\nsedfgs"
' val = JSON(val, DECODE)
' MsgBox val
'
' 'Swap replacement values & dividers + concatenation characters
' val = JSON(val, ENCODE)
' MsgBox val
'
' Function JSON(ByVal str, ByVal mode)
'     Dim key, val
'     Set d = CreateObject("Scripting.Dictionary")
'
'     d.Add "\/", "/"
'     d.Add "\b", Chr(8)
'     d.Add "\f", Chr(12)
'     d.Add "\n", Chr(10)
'     d.Add "\r", Chr(13)
'     d.Add "\t", Chr(9)
'
'     If mode Then
'         d.Add "\""", """"
'         d.Add "\\", "\"
'         div = "\\"
'         cat = "\"
'         key = d.Keys
'         val = d.Items
'     Else
'         d.Add "\\", "\"
'         d.Add "\""", """"
'         div = "\"
'         cat = "\\"
'         key = d.Items
'         val = d.Keys
'     End If
'
'     arr = Split(str, div)
'
'     For i = 0 To UBound(arr)
'         For j = 0 To UBound(key)
'             arr(i) = Replace(arr(i), key(j), val(j))
'         Next
'
'         output = output & arr(i)
'         If i <> UBound(arr) Then output = output & cat
'     Next
'
'     d.RemoveAll
'     JSON = output
' End Function
