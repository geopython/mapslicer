; -- MapTiler.iss --
;

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{51E692DF-521D-4F83-B021-B0D2C4BFA25C}
AppName=MapTiler
AppVerName=MapTiler version 1.0 alpha3
AppPublisher=Petr Pridal - Klokan
AppPublisherURL=http://www.maptiler.com/
AppSupportURL=http://help.maptiler.org/
AppUpdatesURL=http://www.maptiler.org/
DefaultDirName={pf}\MapTiler
DefaultGroupName=MapTiler
LicenseFile=resources\license\LICENSE.txt
OutputBaseFilename=maptiler-1.0-alpha3-setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\maptiler.exe

[Files]
Source: "dist\*"; DestDir: "{app}"
Source: "dist\proj\*"; DestDir: "{app}\proj\"
Source: "dist\gdal\*"; DestDir: "{app}\gdal\"
Source: "dist\gdalplugins\*"; DestDir: "{app}\gdalplugins\"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\MapTiler 1.0 alpha3"; Filename: "{app}\maptiler.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:ProgramOnTheWeb,MapTiler}"; Filename: "http://www.maptiler.org/"
Name: "{group}\Uninstall MapTiler"; Filename: "{uninstallexe}"
Name: "{commondesktop}\MapTiler"; Filename: "{app}\maptiler.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\maptiler.exe"; Description: "{cm:LaunchProgram,MapTiler}"; Flags: nowait postinstall skipifsilent
