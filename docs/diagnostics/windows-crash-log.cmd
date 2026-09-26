@echo off
setlocal
set "FC_CRASH_REPORT=%TEMP%\FamilyConnect-crash-%RANDOM%-%RANDOM%.txt"
powershell.exe -NoLogo -NoProfile -Command "& { 'Family Connect crash diagnostics (read-only)'; Get-Date; 'CPU'; Get-CimInstance Win32_Processor | Select-Object Name,Architecture | Format-List; 'Windows'; Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' | Select-Object ProductName,DisplayVersion,CurrentBuildNumber,UBR | Format-List; 'Application errors for FamilyConnect in the last 7 days'; $events = Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001,1026; StartTime=(Get-Date).AddDays(-7)} -ErrorAction Continue; $matching = @($events | Where-Object { $_.ToXml() -match 'FamilyConnect[.]exe|FamilyConnect[.]dll|Family Connect' } | Select-Object -First 30); if ($matching.Count -eq 0) { 'No matching crash records found.' }; foreach ($event in $matching) { $event | Format-List TimeCreated,Id,ProviderName,Message; $event.ToXml() }; 'Configured application mitigations'; if (Get-Command Get-ProcessMitigation -ErrorAction SilentlyContinue) { Get-ProcessMitigation -Name FamilyConnect.exe -ErrorAction Continue | Format-List * } } *>&1 | Out-File -LiteralPath $env:FC_CRASH_REPORT -Encoding utf8 -Width 240"
if errorlevel 1 (
  echo Diagnostic collection failed. Please send the console error.
  pause
  exit /b 1
)
echo Report: %FC_CRASH_REPORT%
start "" notepad.exe "%FC_CRASH_REPORT%"
pause
