param([Parameter(Mandatory)][string]$Output)
$ErrorActionPreference='Stop'
if((go version) -ne 'go version go1.26.1 windows/amd64'){throw 'Xray requires the accepted Go 1.26.1 Windows amd64 toolchain'}
$revision='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0'
$source=Join-Path $env:RUNNER_TEMP 'fc-xray-windows-source'
if(Test-Path $Output){throw 'Use a fresh output directory'}
New-Item -ItemType Directory $Output | Out-Null
git clone https://github.com/XTLS/Xray-core $source
if($LASTEXITCODE -ne 0){throw 'Xray checkout failed'}
git -C $source checkout --detach $revision
if($LASTEXITCODE -ne 0 -or (git -C $source rev-parse HEAD) -ne $revision){throw 'Xray revision mismatch'}
$env:GOTOOLCHAIN='local';$env:CGO_ENABLED='0';$env:GOOS='windows';$env:GOARCH='amd64'
Push-Location $source
try {
    go build -trimpath -buildvcs=false '-ldflags=-s -w -buildid=' -o "$Output/xray.exe" ./main
    if($LASTEXITCODE -ne 0){throw 'Xray Windows build failed'}
}finally{Pop-Location}
$archive=Join-Path $env:RUNNER_TEMP 'fc-wintun.zip'
Invoke-WebRequest 'https://www.wintun.net/builds/wintun-0.14.1.zip' -OutFile $archive
if((Get-FileHash $archive -Algorithm SHA256).Hash.ToLower() -ne '07c256185d6ee3652e09fa55c0b673e2624b565e02c4b9091c79ca7d2f24ef51'){throw 'Wintun archive checksum mismatch'}
$driver=Join-Path $env:RUNNER_TEMP 'fc-wintun'
Expand-Archive $archive -DestinationPath $driver
$dll=Join-Path $driver 'wintun/bin/amd64/wintun.dll'
$signature=Get-AuthenticodeSignature $dll
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'WireGuard'){throw 'Wintun publisher signature invalid'}
Copy-Item $dll "$Output/wintun.dll"
New-Item -ItemType Directory "$Output/licenses" | Out-Null
Copy-Item "$driver/wintun/LICENSE.txt" "$Output/licenses/Wintun.txt"
Copy-Item "$source/LICENSE" "$Output/licenses/Xray.txt"
$record=@{xray_revision=$revision;go=(go version);wintun='0.14.1';wintun_signer=$signature.SignerCertificate.Subject;files=@{}}
foreach($name in @('xray.exe','wintun.dll')){$record.files[$name]=(Get-FileHash "$Output/$name" -Algorithm SHA256).Hash.ToLower()}
$record | ConvertTo-Json -Depth 4 | Set-Content "$Output/build.json"
& "$Output/xray.exe" version
if($LASTEXITCODE -ne 0){throw 'Xray cannot execute on Windows'}
