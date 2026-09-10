param([switch]$SignedRelease, [string]$SigningThumbprint=$env:FC_SIGNING_THUMBPRINT)
$ErrorActionPreference='Stop'
trap {
    $message=($_.Exception.Message+' at '+$_.InvocationInfo.PositionMessage).Replace('%','%25').Replace("`r",'%0D').Replace("`n",'%0A')
    Write-Host "::error::$message"
    exit 1
}
Set-Location $PSScriptRoot
function Check-Exit { if($LASTEXITCODE -ne 0){throw "Build command failed: $LASTEXITCODE"} }
if($SignedRelease -and $SigningThumbprint -notmatch '^[0-9a-fA-F]{40}$') { throw 'A trusted code-signing certificate is required for signed releases.' }
New-Item -ItemType Directory -Force build,dist | Out-Null
$vendor=Join-Path $PSScriptRoot 'build/wireguard-windows'
if(-not(Test-Path $vendor)) {
    git clone https://git.zx2c4.com/wireguard-windows $vendor
    Check-Exit
}
git -C $vendor checkout --force --detach a4b7f47672b393698127ca14a58f5953bc8b5217
Check-Exit
& "$PSScriptRoot/build-tunnel.ps1" -Vendor $vendor
dotnet run --project Tests/Tests.csproj -c Release
Check-Exit
dotnet publish FamilyConnect.csproj -c Release -r win-x64 --self-contained true -o build/publish
Check-Exit
Copy-Item "$vendor/embeddable-dll-service/amd64/tunnel.dll" build/publish/
Invoke-WebRequest 'https://download.wireguard.com/wireguard-nt/wireguard-nt-1.1.zip' -OutFile build/wireguard-nt.zip
if((Get-FileHash build/wireguard-nt.zip -Algorithm SHA256).Hash -ne 'DCEB30A9BC4BE48CCE0F74160FC88A585A2C2627366E8F846FC6658F9038DACE'){throw 'WireGuardNT checksum mismatch'}
Expand-Archive build/wireguard-nt.zip -DestinationPath build/driver -Force
$driver='build/driver/wireguard-nt/bin/amd64/wireguard.dll'
$signature=Get-AuthenticodeSignature $driver
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'WireGuard'){throw 'WireGuardNT signature invalid'}
Copy-Item $driver build/publish/
New-Item -ItemType Directory -Force build/publish/licenses | Out-Null
Copy-Item build/driver/wireguard-nt/LICENSE.txt build/publish/licenses/WireGuardNT.txt
Copy-Item "$vendor/COPYING" build/publish/licenses/WireGuard-Windows.txt
Copy-Item THIRD-PARTY.md build/publish/licenses/
$bcLicense=Get-ChildItem "$env:USERPROFILE/.nuget/packages/bouncycastle.cryptography/2.7.0" -Recurse -File | Where-Object { $_.Name -match '^LICENSE' } | Select-Object -First 1
if(-not $bcLicense){throw 'Bouncy Castle license missing'}
Copy-Item $bcLicense.FullName build/publish/licenses/BouncyCastle.txt
Copy-Item ../../docs/windows-native.ru.md,../../docs/windows-native.en.md build/publish/
$iscc="${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if(-not(Test-Path $iscc)){throw 'Install Inno Setup 6 on the build machine.'}
$argsList=@('setup.iss')
if($SignedRelease){
    $signTool=(Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe"|Sort-Object FullName|Select-Object -Last 1).FullName
    if(-not $signTool){throw 'Windows SDK SignTool required'}
    foreach($file in @('FamilyConnect.exe','FamilyConnect.dll','tunnel.dll')){
        & $signTool sign /sha1 $SigningThumbprint /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 "build/publish/$file"
        Check-Exit
        $sig=Get-AuthenticodeSignature "build/publish/$file"
        if($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Thumbprint -ne $SigningThumbprint){throw 'Signature verification failed'}
    }
    $signCommand='"'+$signTool+'" sign /sha1 '+$SigningThumbprint+' /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $f'
    $argsList+=@('/DSignedRelease','/DBuildLabel=signed',('/Sfamilyconnect='+$signCommand))
}
& $iscc @argsList
Check-Exit
if($SignedRelease){
    $sig=Get-AuthenticodeSignature 'dist/FamilyConnect-Setup-0.2.3-signed.exe'
    if($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Thumbprint -ne $SigningThumbprint){throw 'Installer signature verification failed'}
}
Get-ChildItem dist/*.exe|ForEach-Object { $h=Get-FileHash $_ -Algorithm SHA256; "$($h.Hash.ToLower())  $($_.Name)" }|Set-Content dist/SHA256SUMS
