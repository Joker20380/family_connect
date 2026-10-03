param([ValidateSet('Install','Broker','UI','Upgrade','Uninstall')][string]$Stage)
$ErrorActionPreference='Stop'
function Invoke-Checked([string]$Exe,[string]$Arguments,[int]$Seconds=90){
    # Wait for the requested process, not an unbounded descendant process tree.
    $p=Start-Process $Exe -ArgumentList $Arguments -PassThru
    if(-not $p.WaitForExit($Seconds*1000)){
        $p.Kill()
        throw "$Stage timed out after $Seconds seconds"
    }
    if($p.ExitCode -ne 0){throw "$Stage exit code: $($p.ExitCode)"}
}
function Get-BrokerSnapshot {
    $service=Get-CimInstance Win32_Service -Filter "Name='FamilyConnectBroker'"
    if($null -eq $service){return [ordered]@{utc=[DateTime]::UtcNow.ToString('o');state='Absent';pid=0}}
    return [ordered]@{utc=[DateTime]::UtcNow.ToString('o');state=$service.State;pid=$service.ProcessId;
        exit_code=$service.ExitCode;service_exit_code=$service.ServiceSpecificExitCode;
        start_mode=$service.StartMode;path=$service.PathName;account=$service.StartName}
}
function Wait-UpgradedBroker([int]$PreviousPid,[DateTime]$Started,[string]$App){
    $timer=[Diagnostics.Stopwatch]::StartNew()
    $previous=''
    while($timer.Elapsed.TotalSeconds -lt 60){
        $snapshot=Get-BrokerSnapshot
        $state="$($snapshot.state)/$($snapshot.pid)"
        if($state -ne $previous){
            $snapshot.elapsed_ms=$timer.ElapsedMilliseconds
            $snapshot | ConvertTo-Json -Compress | Add-Content upgrade-service.jsonl
            Write-Host "::notice::Upgrade readiness: $state elapsed_ms=$($timer.ElapsedMilliseconds)"
            $previous=$state
        }
        if($snapshot.state -eq 'Running' -and $snapshot.pid -ne 0 -and $snapshot.pid -ne $PreviousPid){
            $process=Get-Process -Id $snapshot.pid -ErrorAction SilentlyContinue
            if($null -ne $process -and $process.StartTime.ToUniversalTime() -ge $Started){
                $remaining=[Math]::Min(10000,[int](60000-$timer.ElapsedMilliseconds))
                if($remaining -le 0){break}
                $probe=Start-Process $App -ArgumentList '/broker-test' -PassThru
                try {
                    $finished=$probe.WaitForExit($remaining)
                    $code=if($finished){$probe.ExitCode}else{$probe.Kill();-1}
                    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');probe='broker-status-request-activation';exit_code=$code;
                        elapsed_ms=$timer.ElapsedMilliseconds} | ConvertTo-Json -Compress | Add-Content upgrade-service.jsonl
                    $after=Get-BrokerSnapshot
                    if($code -eq 0 -and $after.state -eq 'Running' -and $after.pid -eq $snapshot.pid){
                        Write-Host "::notice::New broker PID $($after.pid) authenticated status/request/activation PASS after $($timer.ElapsedMilliseconds)ms"
                        return
                    }
                } finally {$probe.Dispose();$process.Dispose()}
            }
        }
        Start-Sleep -Milliseconds 200
    }
    throw 'Broker did not restart with a new ready process within 60 seconds'
}
try {
    Write-Host "::notice::Windows integration stage: $Stage"
    $app="$env:ProgramFiles/Family Connect/FamilyConnect.exe"
    switch($Stage){
        'Install' {
            # Reproduce a first attempt that left an unusable client executable.
            if(Test-Path $app){throw 'Install test requires a clean application directory'}
            New-Item -ItemType Directory -Force (Split-Path $app) | Out-Null
            [IO.File]::WriteAllText($app,'Broken previous apphost; must never be executed')
            $installer=(Resolve-Path "$PSScriptRoot/dist/*pilot-unsigned.exe").Path
            Invoke-Checked $installer '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /LOG=install.log' 180
            if((Get-Service FamilyConnectBroker).Status -ne 'Running'){throw 'Broker service did not start'}
            $icon=Join-Path (Split-Path $app) 'family-connect-door.ico'
            if((Get-FileHash $icon -Algorithm SHA256).Hash -ne (Get-FileHash "$PSScriptRoot/app.ico" -Algorithm SHA256).Hash){throw 'Installed launcher icon differs from accepted artwork'}
            $handler=Get-Item 'Registry::HKEY_LOCAL_MACHINE\Software\Classes\familyconnect\shell\open\command'
            if($handler.GetValue('') -ne ('"'+$app.Replace('/','\')+'" "%1"')){throw 'Invitation handler command mismatch'}
            $tcp="$env:ProgramFiles/Family Connect/tcp"
            $expected=@{'xray.exe'='74475d8c4f68dd07bef754e56778eb2a9061e4dfcc954fa008b912a989bd848a';'wintun.dll'='e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce'}
            foreach($name in $expected.Keys){if((Get-FileHash "$tcp/$name" -Algorithm SHA256).Hash.ToLower() -ne $expected[$name]){throw "Installed TCP hash mismatch: $name"}}
            foreach($name in @('licenses/Xray.txt','licenses/Wintun.txt','build.json')){if(-not(Test-Path "$tcp/$name")){throw "TCP notice missing: $name"}}
            $awg="$env:ProgramFiles/Family Connect/awg"
            if((Get-FileHash "$awg/fc-awg.exe" -Algorithm SHA256).Hash.ToLower() -ne 'e3d11b9552eb8ed84776cf16a8c240e90b4b9ff0d361519c840909ca5f97fdb6'){throw 'Installed AWG worker mismatch'}
            if((Get-FileHash "$awg/wintun.dll" -Algorithm SHA256).Hash.ToLower() -ne 'e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce'){throw 'Installed AWG driver mismatch'}
            if(Test-Path "$awg/peer-fixture.exe"){throw 'CI peer included in installer'}
            foreach($name in @('licenses/AmneziaWG.txt','licenses/Wintun.txt','build.json')){if(-not(Test-Path "$awg/$name")){throw 'AWG notice missing'}}
            $acl=Get-Acl "$env:ProgramData/FamilyConnect"
            if(-not $acl.AreAccessRulesProtected -or $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne 'S-1-5-32-544') {throw 'Key store owner or inheritance is unsafe'}
            foreach($rule in $acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier])) {
                if($rule.AccessControlType -eq 'Allow' -and $rule.IdentityReference.Value -notin @('S-1-5-18','S-1-5-32-544')) {throw 'Unexpected key store access'}
            }
        }
        'Upgrade' {
            $before=Get-BrokerSnapshot
            $before | ConvertTo-Json -Compress | Set-Content upgrade-service.jsonl
            if($before.state -ne 'Running' -or $before.pid -eq 0){throw 'Upgrade requires a running broker'}
            $started=[DateTime]::UtcNow
            $watch=Start-Job -ScriptBlock {
                $ErrorActionPreference='Stop'
                $until=[DateTime]::UtcNow.AddMinutes(5)
                $previous=''
                while([DateTime]::UtcNow -lt $until){
                    $service=Get-CimInstance Win32_Service -Filter "Name='FamilyConnectBroker'"
                    $state=if($null -eq $service){'Absent'}else{"$($service.State)/$($service.ProcessId)"}
                    if($state -ne $previous){
                        [ordered]@{utc=[DateTime]::UtcNow.ToString('o');transition=$state} | ConvertTo-Json -Compress
                        $previous=$state
                    }
                    Start-Sleep -Milliseconds 200
                }
            }
            $sentinel=Join-Path $env:ProgramData 'FamilyConnect/installer-upgrade-sentinel.txt'
            [IO.File]::WriteAllText($sentinel,'preserve-existing-data')
            try {
                $installer=(Resolve-Path "$PSScriptRoot/dist/*pilot-unsigned.exe").Path
                Invoke-Checked $installer '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /LOG=upgrade.log' 240
                $returned=Get-BrokerSnapshot
                $returned.installer_exit_code=0
                $returned | ConvertTo-Json -Compress | Add-Content upgrade-service.jsonl
                Wait-UpgradedBroker -PreviousPid $before.pid -Started $started -App $app
                if([IO.File]::ReadAllText($sentinel) -ne 'preserve-existing-data'){throw 'Upgrade changed stored data'}
                Invoke-Checked $app '/runtime-check' 30
                Invoke-Checked $app '/broker-test' 60
            } finally {
                Stop-Job $watch
                Receive-Job $watch | Add-Content upgrade-service.jsonl
                Remove-Job $watch
                Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Service Control Manager';StartTime=$started} -ErrorAction SilentlyContinue |
                    Where-Object {$_.Message -match 'Family Connect|FamilyConnectBroker'} |
                    ForEach-Object {[ordered]@{utc=$_.TimeCreated.ToUniversalTime().ToString('o');event_id=$_.Id;message=$_.Message} | ConvertTo-Json -Compress} |
                    Add-Content upgrade-service.jsonl
                Get-Content upgrade-service.jsonl | ForEach-Object {Write-Host "::notice::Broker lifecycle $_"}
                Remove-Item -LiteralPath $sentinel -ErrorAction SilentlyContinue
            }
        }
        'Broker' {Invoke-Checked $app '/broker-test' 60}
        'UI' {Invoke-Checked $app '/smoke' 30}
        'Uninstall' {
            $uninstaller="$env:ProgramFiles/Family Connect/unins000.exe"
            if(Test-Path $uninstaller){Invoke-Checked $uninstaller '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' 180}
            if(Get-Service FamilyConnectBroker -ErrorAction SilentlyContinue){throw 'Broker left behind'}
            if(Test-Path "$env:ProgramFiles/Family Connect/tcp/xray.exe"){throw 'TCP payload left behind'}
            if(Test-Path "$env:ProgramFiles/Family Connect/awg/fc-awg.exe"){throw 'AWG payload left behind'}
        }
    }
    Write-Host "::notice::Windows integration passed: $Stage"
} catch {
    $detail=''
    if($Stage -eq 'Install'){$detail=(Get-Content install.log -Tail 12 -ErrorAction SilentlyContinue) -join '%0A'}
    if($Stage -eq 'Broker'){$detail=Get-Content "$env:TEMP/fc-broker-check.txt" -ErrorAction SilentlyContinue}
    Write-Host "::error::$Stage failed: $($_.Exception.Message) $detail"
    throw
}
