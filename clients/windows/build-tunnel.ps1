param([Parameter(Mandatory)][string]$Vendor)
$ErrorActionPreference='Stop'
# Build only the upstream embedded DLL. The official GUI build also downloads
# unrelated CLI/icon tools, including a dynamically generated archive that is unreliable.
# Compiler versions, hashes and flags match wireguard-windows v1.0.1/build.bat.
$deps=Join-Path $Vendor '.deps'
New-Item -ItemType Directory -Force $deps | Out-Null
$packages=@(
    @('go.zip','https://download.wireguard.com/windows-toolchain/distfiles/go1.26.2-windows_amd64_2026-04-20.zip','79b5d5ff6f2718dfe25e199cda314d174ecf5bb19f0f2d777aec089d09a12620'),
    @('llvm.zip','https://download.wireguard.com/windows-toolchain/distfiles/llvm-mingw-20260311-ucrt-x86_64.zip','dd4c67d98959479c7be2fb6709ba074475991590848cb9d0eb2620be06b182e1')
)
foreach($package in $packages){
    $archive=Join-Path $deps $package[0]
    & "$PSScriptRoot/download-dependency.ps1" -Url $package[1] -Output $archive
    if((Get-FileHash $archive -Algorithm SHA256).Hash -ne $package[2]){throw "Compiler checksum mismatch: $($package[0])"}
    & tar.exe -xf $archive -C $deps --strip-components 1
    if($LASTEXITCODE -ne 0){throw 'Compiler extraction failed'}
    Remove-Item $archive
}
$env:PATH="$deps\bin;$env:PATH"
$env:GOROOT=$deps
$env:GOPATH=Join-Path $deps 'gopath'
$env:GOTOOLCHAIN='local'
$env:GOWORK='off'
$env:GOOS='windows'
$env:GOARCH='amd64'
$env:CGO_ENABLED='1'
$env:CC=Join-Path $deps 'bin/x86_64-w64-mingw32-gcc.exe'
$env:CGO_CFLAGS='-O3 -Wall -Wno-unused-function -Wno-switch -std=gnu11 -DWINVER=0x0A00'
Push-Location "$Vendor/embeddable-dll-service"
try {
    New-Item -ItemType Directory -Force amd64 | Out-Null
    & "$deps/bin/go.exe" build -mod=readonly -buildmode c-shared '-ldflags=-w -s' -trimpath -o amd64/tunnel.dll .
    if($LASTEXITCODE -ne 0){throw 'Embedded WireGuard DLL compilation failed'}
}finally{Pop-Location}
