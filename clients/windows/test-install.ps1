param([ValidateSet('Install','Broker','UI','Uninstall')][string]$Stage)
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
try {
    Write-Host "::notice::Windows integration stage: $Stage"
    $app="$env:ProgramFiles/Family Connect/FamilyConnect.exe"
    switch($Stage){
        'Install' {
            $installer=(Resolve-Path "$PSScriptRoot/dist/*pilot-unsigned.exe").Path
            Invoke-Checked $installer '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /LOG=install.log' 180
            if((Get-Service FamilyConnectBroker).Status -ne 'Running'){throw 'Broker service did not start'}
            $tcp="$env:ProgramFiles/Family Connect/tcp"
            $expected=@{'xray.exe'='74475d8c4f68dd07bef754e56778eb2a9061e4dfcc954fa008b912a989bd848a';'wintun.dll'='e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce'}
            foreach($name in $expected.Keys){if((Get-FileHash "$tcp/$name" -Algorithm SHA256).Hash.ToLower() -ne $expected[$name]){throw "Installed TCP hash mismatch: $name"}}
            foreach($name in @('licenses/Xray.txt','licenses/Wintun.txt','build.json')){if(-not(Test-Path "$tcp/$name")){throw "TCP notice missing: $name"}}
            $awg="$env:ProgramFiles/Family Connect/awg"
            if((Get-FileHash "$awg/fc-awg.exe" -Algorithm SHA256).Hash.ToLower() -ne '0ff643eee68ce94183b6f5dde75fc9c03eeff96d6731349c9431fc2771be1a70'){throw 'Installed AWG worker mismatch'}
            if((Get-FileHash "$awg/wintun.dll" -Algorithm SHA256).Hash.ToLower() -ne 'e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce'){throw 'Installed AWG driver mismatch'}
            if(Test-Path "$awg/peer-fixture.exe"){throw 'CI peer included in installer'}
            foreach($name in @('licenses/AmneziaWG.txt','licenses/Wintun.txt','build.json')){if(-not(Test-Path "$awg/$name")){throw 'AWG notice missing'}}
            $acl=Get-Acl "$env:ProgramData/FamilyConnect"
            if(-not $acl.AreAccessRulesProtected -or $acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne 'S-1-5-32-544') {throw 'Key store owner or inheritance is unsafe'}
            foreach($rule in $acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier])) {
                if($rule.AccessControlType -eq 'Allow' -and $rule.IdentityReference.Value -notin @('S-1-5-18','S-1-5-32-544')) {throw 'Unexpected key store access'}
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
