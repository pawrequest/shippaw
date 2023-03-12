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
Source: "/vbs/*"; DestDir: "{app}/vbs"
Source: "/powershell/*"; DestDir: "{app}/powershell"
Source: "/dist/; DestDir: "{app}/dist"


[Run]

