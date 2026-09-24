#ifndef BuildLabel
#define BuildLabel "pilot-unsigned"
#endif
[Setup]
AppId={{68D949A5-515C-4328-901F-C870A270FD01}
AppName=family_connect
AppVersion=0.2.14
AppPublisher=family_connect
DefaultDirName={autopf}\Family Connect
DefaultGroupName=family_connect
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
PrivilegesRequired=admin
MinVersion=10.0.17763
SetupLogging=yes
OutputDir=dist
OutputBaseFilename=FamilyConnect-Setup-0.2.14-{#BuildLabel}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=app.ico
UninstallDisplayIcon={app}\family-connect-door.ico
CloseApplications=yes
ChangesAssociations=yes
#ifdef SignedRelease
SignTool=familyconnect
SignedUninstaller=yes
#endif
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
[Files]
Source: "prepare-install.ps1"; Flags: dontcopy
Source: "app.ico"; DestDir: "{app}"; DestName: "family-connect-door.ico"; Flags: ignoreversion
Source: "build\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[InstallDelete]
Type: files; Name: "{autoprograms}\Family Connect.lnk"
Type: files; Name: "{autodesktop}\Family Connect.lnk"
[Registry]
Root: HKLM; Subkey: "Software\Classes\familyconnect"; ValueType: string; ValueData: "URL:family_connect invitation"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Classes\familyconnect"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKLM; Subkey: "Software\Classes\familyconnect\shell\open\command"; ValueType: string; ValueData: """{app}\FamilyConnect.exe"" ""%1"""
[Icons]
Name: "{autoprograms}\family_connect"; Filename: "{app}\FamilyConnect.exe"; IconFilename: "{app}\family-connect-door.ico"
Name: "{autodesktop}\family_connect"; Filename: "{app}\FamilyConnect.exe"; IconFilename: "{app}\family-connect-door.ico"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked
[UninstallRun]
Filename: "{app}\FamilyConnect.exe"; Parameters: "/remove-service"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveFamilyConnectService"
[Code]
function FailureDetail(const ReportPath: String; ExitCode: Integer): String;
var Detail: AnsiString;
begin
  Result := ' Code: ' + IntToStr(ExitCode) + '.';
  if LoadStringFromFile(ReportPath, Detail) then
    Result := Result + ' ' + String(Detail);
  Log(Result);
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
var ExitCode: Integer; ReportPath, Params: String;
begin
  Result := '';
  ExtractTemporaryFile('prepare-install.ps1');
  ReportPath := ExpandConstant('{tmp}\prepare-result.txt');
  Params := '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{tmp}\prepare-install.ps1') + '" -ReportPath "' + ReportPath + '"';
  if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      Params, '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
    Result := 'Cannot start service preparation. / Не удалось запустить подготовку служб.' + FailureDetail(ReportPath, ExitCode)
  else if ExitCode <> 0 then
    Result := 'Cannot prepare Family Connect services. / Не удалось подготовить службы Family Connect.' + FailureDetail(ReportPath, ExitCode);
end;
procedure CurStepChanged(CurStep: TSetupStep);
var ExitCode: Integer; ReportPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    ReportPath := ExpandConstant('{tmp}\service-result.txt');
    if not Exec(ExpandConstant('{app}\FamilyConnect.exe'), '/install-service "' + ReportPath + '"',
        '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
      RaiseException('Cannot start Family Connect. / Не удалось запустить Family Connect.' + FailureDetail(ReportPath, ExitCode))
    else if ExitCode <> 0 then
      RaiseException('Cannot install Family Connect service. / Не удалось установить службу Family Connect.' + FailureDetail(ReportPath, ExitCode));
  end;
end;
