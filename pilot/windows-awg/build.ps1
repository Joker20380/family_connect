param([Parameter(Mandatory)][string]$Output)
$ErrorActionPreference='Stop'
if((go version) -ne 'go version go1.26.1 windows/amd64'){throw 'Go 1.26.1 Windows amd64 required'}
$revision='b5928efb6ca19f0153958460c3d141f04abc5c2e'
$source=Join-Path $env:RUNNER_TEMP ('fc-awg-source-'+[guid]::NewGuid().ToString('N'))
if(Test-Path $Output){throw 'Use a fresh output directory'}
New-Item -ItemType Directory $Output | Out-Null
git clone https://github.com/amnezia-vpn/amneziawg-go $source
if($LASTEXITCODE -ne 0){throw 'AWG checkout failed'}
git -C $source checkout --detach $revision
if($LASTEXITCODE -ne 0 -or (git -C $source rev-parse HEAD) -ne $revision){throw 'AWG revision mismatch'}
$patch=Join-Path $PSScriptRoot '../awg31/patches/0001-refresh-s4-after-tun-read.patch'
git -C $source apply --check $patch
if($LASTEXITCODE -ne 0){throw 'AWG startup patch mismatch'}
git -C $source apply $patch
if($LASTEXITCODE -ne 0){throw 'AWG startup patch failed'}
New-Item -ItemType Directory "$source/cmd/fc-worker","$source/cmd/fc-fixture" | Out-Null
Copy-Item "$PSScriptRoot/worker/main.go" "$source/cmd/fc-worker/main_windows.go"
Copy-Item "$PSScriptRoot/fixture/main.go" "$source/cmd/fc-fixture/main_windows.go"
$env:GOTOOLCHAIN='local';$env:CGO_ENABLED='0';$env:GOOS='windows';$env:GOARCH='amd64'
Push-Location $source
try{
 go build -trimpath -buildvcs=false '-ldflags=-s -w -buildid=' -o "$Output/fc-awg.exe" ./cmd/fc-worker
 if($LASTEXITCODE -ne 0){throw 'AWG worker build failed'}
 go build -trimpath -buildvcs=false '-ldflags=-s -w -buildid=' -o "$Output/peer-fixture.exe" ./cmd/fc-fixture
 if($LASTEXITCODE -ne 0){throw 'AWG peer fixture build failed'}
}finally{Pop-Location}
$archive=Join-Path $env:RUNNER_TEMP 'fc-awg-wintun.zip'
Invoke-WebRequest 'https://www.wintun.net/builds/wintun-0.14.1.zip' -OutFile $archive
if((Get-FileHash $archive -Algorithm SHA256).Hash.ToLower() -ne '07c256185d6ee3652e09fa55c0b673e2624b565e02c4b9091c79ca7d2f24ef51'){throw 'Wintun archive mismatch'}
$driver=Join-Path $env:RUNNER_TEMP 'fc-awg-wintun'
Expand-Archive $archive -DestinationPath $driver
$dll=Join-Path $driver 'wintun/bin/amd64/wintun.dll'
$sig=Get-AuthenticodeSignature $dll
if($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'WireGuard'){throw 'Wintun signature invalid'}
if((Get-FileHash $dll -Algorithm SHA256).Hash.ToLower() -ne 'e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce'){throw 'Wintun binary mismatch'}
Copy-Item $dll "$Output/wintun.dll"
New-Item -ItemType Directory "$Output/licenses" | Out-Null
Copy-Item "$driver/wintun/LICENSE.txt" "$Output/licenses/Wintun.txt"
Copy-Item "$source/LICENSE" "$Output/licenses/AmneziaWG.txt"
$record=@{revision=$revision;protocol='3.1';startup_patch_sha256=(Get-FileHash $patch -Algorithm SHA256).Hash.ToLower();go=(go version);worker_source_sha256=(Get-FileHash "$PSScriptRoot/worker/main.go" -Algorithm SHA256).Hash.ToLower();files=@{}}
foreach($name in @('fc-awg.exe','wintun.dll','peer-fixture.exe')){$record.files[$name]=(Get-FileHash "$Output/$name" -Algorithm SHA256).Hash.ToLower()}
$record | ConvertTo-Json -Depth 4 | Set-Content "$Output/build.json"
