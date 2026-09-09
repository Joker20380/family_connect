$ErrorActionPreference = 'Stop'
$exe = Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'WireGuard\wireguard.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { exit 20 }
$signature = Get-AuthenticodeSignature -LiteralPath $exe
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'WireGuard') { exit 21 }
Write-Output $exe
