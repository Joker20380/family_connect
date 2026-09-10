#ifndef BuildLabel
#define BuildLabel "pilot-unsigned"
#endif
[Setup]
AppId={{68D949A5-515C-4328-901F-C870A270FD01}
AppName=Family Connect
AppVersion=0.2.5
AppPublisher=Family Connect
DefaultDirName={autopf}\Family Connect
DefaultGroupName=Family Connect
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
PrivilegesRequired=admin
OutputDir=dist
OutputBaseFilename=FamilyConnect-Setup-0.2.5-{#BuildLabel}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=app.ico
UninstallDisplayIcon={app}\FamilyConnect.exe
CloseApplications=yes
#ifdef SignedRelease
SignTool=familyconnect
SignedUninstaller=yes
#endif
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
[Files]
Source: "build\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Family Connect"; Filename: "{app}\FamilyConnect.exe"
Name: "{autodesktop}\Family Connect"; Filename: "{app}\FamilyConnect.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked
[UninstallRun]
Filename: "{app}\FamilyConnect.exe"; Parameters: "/remove-service"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveFamilyConnectService"
[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var ExitCode: Integer;
begin
  Result := '';
  if FileExists(ExpandConstant('{app}\FamilyConnect.exe')) then
  begin
    if not Exec(ExpandConstant('{app}\FamilyConnect.exe'), '/remove-service', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      Result := 'Cannot stop Family Connect services. / Не удалось остановить службы Family Connect.';
  end;
end;
procedure CurStepChanged(CurStep: TSetupStep);
var ExitCode: Integer;
begin
  if CurStep = ssPostInstall then
    if not Exec(ExpandConstant('{app}\FamilyConnect.exe'), '/install-service', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
      RaiseException('Cannot install Family Connect service. / Не удалось установить службу Family Connect.');
end;
