; Script Inno Setup pour AutoFlow
; Génère un installeur Windows à partir de dist\AutoFlow (sortie de PyInstaller).
; Compilation : ISCC.exe packaging\installer.iss

#define AppName "AutoFlow"
#define AppVersion "0.2.0"
#define AppPublisher "AutoFlow"
#define AppExeName "AutoFlow.exe"

[Setup]
AppId={{B7E5B6A0-4C2E-4E2A-9E2B-AUTOFLOW0002}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=AutoFlow-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"
Name: "startup"; Description: "Lancer AutoFlow au démarrage de Windows"; GroupDescription: "Démarrage :"; Flags: unchecked

[Files]
Source: "..\dist\AutoFlow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Lancer AutoFlow"; Flags: nowait postinstall skipifsilent
