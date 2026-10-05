; Hírlevél követő — Inno Setup telepítő
; Forrás: a BUILD-EXE.cmd által készített program\ mappa

#define MyAppName "Hírlevél követő"
#define MyAppNameAscii "HirlevelKoveto"
#define MyAppVersion "1.0"
#define MyAppPublisher "Hírlevél követő"
#define MyAppExeName "HirlevelKoveto.exe"
#define MyAppUrl ""

[Setup]
AppId={{A7C3E91F-2B4D-4F18-9E6A-8D1C5B0F3A72}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppNameAscii}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.md
InfoBeforeFile=..\OLVASD.md
OutputDir=..\dist_installer
OutputBaseFilename=HirlevelKoveto-Setup
SetupIconFile=..\app\assets\hirlevel.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
AllowNoIcons=yes
; Adatok AppData\Local\HirlevelKoveto-ban maradnak (nem a telepítő mappában)
UsePreviousAppDir=yes

[Languages]
Name: "hungarian"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Windows indításkor a tálcán induljon"; GroupDescription: "Indítás:"; Flags: unchecked

[Files]
; PyInstaller onedir tartalom
Source: "..\program\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Jogi dokumentumok (Markdown)
Source: "..\OLVASD.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\ADATKEZELESI_TAJEKOZTATO.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\FELHASZNALASI_FELTETELEK.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\BIZTONSAG_ES_ADATVEDELEM.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion
; Jogi dokumentumok (HTML - az alkalmazáson belüli megjelenítéshez)
Source: "..\ADATKEZELESI_TAJEKOZTATO.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\FELHASZNALASI_FELTETELEK.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\BIZTONSAG_ES_ADATVEDELEM.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.html"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{#MyAppName} (tálca)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--tray"; WorkingDir: "{app}"
Name: "{group}\OLVASD (útmutató)"; Filename: "{app}\OLVASD.md"; WorkingDir: "{app}"; Flags: createonlyiffileexists
Name: "{group}\Adatkezelési tájékoztató (GDPR)"; Filename: "{app}\ADATKEZELESI_TAJEKOZTATO.md"; WorkingDir: "{app}"; Flags: createonlyiffileexists
Name: "{group}\Biztonság és adatvédelem"; Filename: "{app}\BIZTONSAG_ES_ADATVEDELEM.md"; WorkingDir: "{app}"; Flags: createonlyiffileexists
Name: "{group}\Felhasználási feltételek"; Filename: "{app}\FELHASZNALASI_FELTETELEK.md"; WorkingDir: "{app}"; Flags: createonlyiffileexists
Name: "{group}\MIT-licenc"; Filename: "{app}\LICENSE.md"; WorkingDir: "{app}"; Flags: createonlyiffileexists
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppNameAscii}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--tray"; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Ne töröljük az AppData archívumot / configot — a felhasználó adatai maradjanak
Type: files; Name: "{app}\*.log"
