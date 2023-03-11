; -- Example1.iss --
; Demonstrates copying 3 files and creating an icon.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppName=AmDesp
AppVersion=0.1
WizardStyle=modern
DefaultDirName={autopf}\AmDesp
DefaultGroupName=AmDesp


[Files]
Source: "main.py"; DestDir: "{app}"
Source: "setup.py"; DestDir: "{app}"
Source: "/vbs/*"; DestDir: "{app}/vbs"
Source: "/python/*"; DestDir: "{app}/python"
Source: "/powershell/*"; DestDir: "{app}/powershell"
Source: "/dist/CmcLibNet_Setup.exe"; DestDir: "{app}/dist"


[Run]

