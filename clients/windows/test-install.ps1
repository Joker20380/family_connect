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
        }
        'Broker' {Invoke-Checked $app '/broker-test' 60}
        'UI' {Invoke-Checked $app '/smoke' 30}
        'Uninstall' {
            $uninstaller="$env:ProgramFiles/Family Connect/unins000.exe"
            if(Test-Path $uninstaller){Invoke-Checked $uninstaller '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' 90}
            if(Get-Service FamilyConnectBroker -ErrorAction SilentlyContinue){throw 'Broker left behind'}
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
