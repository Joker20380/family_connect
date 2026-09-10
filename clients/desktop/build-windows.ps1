$ErrorActionPreference = 'Stop'
# Compatibility entry point: Windows uses the native broker/WinForms client.
& "$PSScriptRoot/../windows/build.ps1" @args
exit $LASTEXITCODE
