; -- MapSlicer.iss --
;

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{51E692DF-521D-4F83-B021-B0D2C4BFA25C}
AppName=MapSlicer
AppVerName=MapSlicer version 1.0 alpha3
AppPublisher=Petr Pridal - Klokan
AppPublisherURL=http://www.mapslicer.com/
AppSupportURL=http://help.mapslicer.org/
AppUpdatesURL=http://www.mapslicer.org/
DefaultDirName={pf}\MapSlicer
DefaultGroupName=MapSlicer
LicenseFile=resources\license\LICENSE.txt
OutputBaseFilename=mapslicer-1.0-alpha3-setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\mapslicer.exe

[Files]
Source: "dist\*"; DestDir: "{app}"
Source: "dist\proj\*"; DestDir: "{app}\proj\"
Source: "dist\gdal\*"; DestDir: "{app}\gdal\"
Source: "dist\gdalplugins\*"; DestDir: "{app}\gdalplugins\"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\MapSlicer 1.0 alpha3"; Filename: "{app}\mapslicer.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:ProgramOnTheWeb,MapSlicer}"; Filename: "http://www.mapslicer.org/"
Name: "{group}\Uninstall MapSlicer"; Filename: "{uninstallexe}"
Name: "{commondesktop}\MapSlicer"; Filename: "{app}\mapslicer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\mapslicer.exe"; Description: "{cm:LaunchProgram,MapSlicer}"; Flags: nowait postinstall skipifsilent
