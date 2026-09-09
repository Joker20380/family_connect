$ErrorActionPreference = 'Stop'
$exe = Join-Path ([Environment]::GetFolderPath('ProgramFiles')) 'WireGuard\wireguard.exe'
$signature = Get-AuthenticodeSignature -LiteralPath $exe
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'WireGuard') {
    throw 'An officially signed WireGuard installation is required.'
}
Write-Output $exe
