; Inno Setup script — يبني ملف تثبيت AswaqBadrHR-Setup.exe
[Setup]
AppName=Aswaq Badr HR
AppVersion=1.0.0
AppPublisher=Mahmoud Thabet
DefaultDirName={autopf}\AswaqBadrHR
DefaultGroupName=Aswaq Badr HR
OutputDir=..\dist_installer
OutputBaseFilename=AswaqBadrHR-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\AswaqBadrHR.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات:"

[Files]
Source: "..\dist\AswaqBadrHR.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\أسواق بدر HR"; Filename: "{app}\AswaqBadrHR.exe"
Name: "{autodesktop}\أسواق بدر HR"; Filename: "{app}\AswaqBadrHR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AswaqBadrHR.exe"; Description: "تشغيل البرنامج"; Flags: nowait postinstall skipifsilent
