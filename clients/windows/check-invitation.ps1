# Disposable GitHub runner only: exercise the installed URI handler without live claims.
$ErrorActionPreference='Stop'
if($env:GITHUB_ACTIONS -ne 'true'){throw 'Disposable CI runner required'}
$app=Join-Path $env:ProgramFiles 'Family Connect/FamilyConnect.exe'
$rule='FamilyConnect-Invitation-CI-'+[Guid]::NewGuid().ToString('N')
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class InvitationWindow {
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
}
'@
function WindowProcess {
 @(Get-Process FamilyConnect -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 })
}
function Wait-Window {
 $until=[DateTime]::UtcNow.AddSeconds(30)
 do {
  $windows=@(WindowProcess)
  if($windows.Count -eq 1){return $windows[0]}
  Start-Sleep -Milliseconds 200
 } while([DateTime]::UtcNow -lt $until)
 throw 'Invitation window did not open'
}
try {
 # The UI and broker share this executable. Block both before synthetic URI launch.
 New-NetFirewallRule -DisplayName $rule -Direction Outbound -Program $app -Action Block -Profile Any | Out-Null
 if(@(WindowProcess).Count -ne 0){throw 'Unexpected existing client window'}
 Start-Process ('familyconnect://invite/'+('a'*64))
 $first=Wait-Window
 $window=$first.MainWindowHandle
 [InvitationWindow]::ShowWindow($window,6) | Out-Null
 if(-not [InvitationWindow]::IsIconic($window)){throw 'Could not minimize invitation window'}
 Start-Process ('familyconnect://invite/'+('b'*64))
 $until=[DateTime]::UtcNow.AddSeconds(20)
 while([InvitationWindow]::IsIconic($window) -and [DateTime]::UtcNow -lt $until){Start-Sleep -Milliseconds 200}
 $again=Wait-Window
 if($again.Id -ne $first.Id -or $again.MainWindowHandle -ne $window -or [InvitationWindow]::IsIconic($window)){
  throw 'Second invitation did not restore the existing window'
 }
 $invalid=Start-Process $app -ArgumentList 'familyconnect://invite/invalid' -PassThru
 if(-not $invalid.WaitForExit(10000)){$invalid.Kill();throw 'Malformed invitation did not exit'}
 if($invalid.ExitCode -ne 2){throw 'Malformed invitation was not rejected'}
 Write-Host '::notice title=Invitation handler::Installed URI launch and second-link single-window delivery passed; malformed URI rejected; outbound traffic blocked.'
} finally {
 foreach($process in @(WindowProcess)){$process.Kill();$process.WaitForExit(10000) | Out-Null}
 Stop-Service FamilyConnectBroker
 Remove-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue
}
