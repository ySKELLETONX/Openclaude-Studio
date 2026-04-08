#define MyAppName "Openclaude Studio"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Openclaude Studio"
#define MyAppExeName "OpenclaudeStudio.exe"

[Setup]
AppId={{1F2F1EBA-1D9B-4EF9-8B32-5F781EE3A998}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Openclaude Studio
DefaultGroupName=Openclaude Studio
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=OpenclaudeStudio-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\openclaude_studio.ico

[Files]
Source: "..\dist\OpenclaudeStudio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Openclaude Studio"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Openclaude Studio"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Openclaude Studio"; Flags: nowait postinstall skipifsilent
