; ########################################################
; # KaBlackSmith Setup Script (v1.0.0)
; ########################################################

[Setup]
AppId={{KaBlackSmith-ldu0009-2026}}
AppName=KaBlackSmith
AppVersion=1.0.0
AppPublisher=ldu0009
AppPublisherURL=https://github.com/ldu0009/kakao-sword-raising
DefaultDirName={localappdata}\KaBlackSmith
DefaultGroupName=KaBlackSmith
AllowNoIcons=yes
SetupIconFile=assets\icons\icon.ico
UninstallDisplayIcon={app}\KaBlackSmith.exe
OutputDir=installer_output
OutputBaseFilename=KaBlackSmith_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\KaBlackSmith\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion uninsneveruninstall

[Icons]
Name: "{group}\KaBlackSmith"; Filename: "{app}\KaBlackSmith.exe"
Name: "{userdesktop}\KaBlackSmith"; Filename: "{app}\KaBlackSmith.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KaBlackSmith.exe"; Description: "{cm:LaunchProgram,KaBlackSmith}"; Flags: nowait postinstall skipifsilent
