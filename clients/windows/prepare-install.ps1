param([Parameter(Mandatory=$true)][string]$ReportPath)
$ErrorActionPreference='Stop'
$stage='administrator'
try {
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    $principal=New-Object Security.Principal.WindowsPrincipal($identity)
    if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Administrator required'
    }
    # Do not execute the previous client: it may fail before entering Main.
    # Keep all profiles and encrypted identity data untouched.
    foreach($name in @('FamilyConnectBroker','WireGuardTunnel$fc-native')) {
        $stage='stop-'+$name
        $service=Get-Service -Name $name -ErrorAction SilentlyContinue
        if($null -eq $service){continue}
        try {
            if($service.Status -ne 'Stopped') {
                if($service.Status -ne 'StopPending'){$service.Stop()}
                $service.WaitForStatus([ServiceProcess.ServiceControllerStatus]::Stopped,[TimeSpan]::FromSeconds(130))
            }
        } finally {$service.Dispose()}
        $stage='delete-'+$name
        & "$env:SystemRoot\System32\sc.exe" delete $name | Out-Null
        if($LASTEXITCODE -notin @(0,1060,1072)){throw "Service deletion failed: $LASTEXITCODE"}
        # SCM deletion can remain pending while another program holds a handle.
        $deadline=[DateTime]::UtcNow.AddSeconds(30)
        do {
            $pending=Get-Service -Name $name -ErrorAction SilentlyContinue
            if($null -eq $pending){break}
            $pending.Dispose()
            if([DateTime]::UtcNow -ge $deadline){throw 'Service deletion pending; close Services and retry'}
            Start-Sleep -Milliseconds 250
        } while($true)
    }
    'complete' | Set-Content -LiteralPath $ReportPath -Encoding ASCII
    exit 0
} catch {
    # No profile contents or user identity values in installation diagnostics.
    ('stage='+$stage+'; type='+$_.Exception.GetType().Name+'; hresult=0x'+$_.Exception.HResult.ToString('X8')) |
        Set-Content -LiteralPath $ReportPath -Encoding ASCII
    exit 1
}
