import subprocess

script = "Public Function CheckInFormScript (categoryName As String,
	formName As String,
	fileName As String
) As Boolean"

subprocess.call("cscript 19112944.vbs") # works

subprocess.call("cmd /c 19112944.vbs") #
