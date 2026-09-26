@echo off
setlocal
set "FC_SETUP=%~dp0FamilyConnect-Setup-0.2.13-pilot-unsigned.exe"
if not exist "%FC_SETUP%" (
  echo Put this file next to FamilyConnect-Setup-0.2.13-pilot-unsigned.exe
  pause
  exit /b 2
)
set "FC_LOGDIR=%TEMP%\FamilyConnect-install-%RANDOM%-%RANDOM%"
mkdir "%FC_LOGDIR%"
if errorlevel 1 exit /b 3
set "DOTNET_HOST_TRACE=1"
set "DOTNET_HOST_TRACE_VERBOSITY=4"
set "DOTNET_HOST_TRACEFILE=%FC_LOGDIR%\dotnet-host.txt"
set "COREHOST_TRACE=1"
set "COREHOST_TRACE_VERBOSITY=4"
set "COREHOST_TRACEFILE=%FC_LOGDIR%\dotnet-host.txt"
ver > "%FC_LOGDIR%\windows.txt"
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v DisplayVersion >> "%FC_LOGDIR%\windows.txt" 2>&1
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuildNumber >> "%FC_LOGDIR%\windows.txt" 2>&1
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v UBR >> "%FC_LOGDIR%\windows.txt" 2>&1
echo Complete the installation attempt, then close the installer.
start "" /wait "%FC_SETUP%" /NORESTART /LOG="%FC_LOGDIR%\setup.log"
echo InstallerExitCode=%ERRORLEVEL% > "%FC_LOGDIR%\result.txt"
sc.exe query FamilyConnectBroker >> "%FC_LOGDIR%\result.txt" 2>&1
sc.exe qc FamilyConnectBroker >> "%FC_LOGDIR%\result.txt" 2>&1
echo Logs: %FC_LOGDIR%
start "" explorer.exe "%FC_LOGDIR%"
pause
