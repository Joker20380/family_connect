$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m pip install pyinstaller==6.22.2
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m PyInstaller --noconfirm --clean --windowed --onedir --uac-admin --name FamilyConnect --add-data 'verify-wireguard.ps1;.' app.py
exit $LASTEXITCODE
