param([Parameter(Mandatory)][string]$Url,[Parameter(Mandatory)][string]$Output)
$ErrorActionPreference='Stop'
# Called only by the pinned upstream build script. The caller checks the pinned SHA256 next.
for($attempt=1;$attempt -le 3;$attempt++){
    try {Invoke-WebRequest -Uri $Url -OutFile $Output -TimeoutSec 180;return}
    catch {if($attempt -eq 3){throw};Start-Sleep -Seconds 2}
}
