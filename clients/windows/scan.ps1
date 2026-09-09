param([string]$PathToScan="$PSScriptRoot/dist")
$ErrorActionPreference='Stop'
$status=Get-MpComputerStatus -ErrorAction SilentlyContinue
if(-not $status -or -not $status.AntivirusEnabled){
    Write-Host 'Defender scan NOT performed: antivirus unavailable on this runner.'
    exit 0
}
$started=Get-Date
Start-MpScan -ScanType CustomScan -ScanPath (Resolve-Path $PathToScan)
$root=(Resolve-Path $PathToScan).Path
$detections=Get-MpThreatDetection | Where-Object {
    $_.InitialDetectionTime -ge $started -and ($_.Resources | Where-Object {$_ -like "*$root*"})
}
if($detections){throw 'Defender detected a threat in this build; distribution blocked.'}
Write-Host "Defender custom scan completed. Signature version: $($status.AntivirusSignatureVersion). This does not guarantee other scanners or future results."
