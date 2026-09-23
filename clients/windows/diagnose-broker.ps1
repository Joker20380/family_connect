# Read-only diagnostic for the installed client; run as the affected Windows user.
# No activation, key/profile reads, service restart, or VPN connection.
$ErrorActionPreference = 'Stop'
$result = [ordered]@{schema=1; service='unknown'; startType='unknown'; elevated=$false; stage='service'; ok=$false}
$pipe = $null
$deadline = $null
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    $result.elevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $service = Get-Service FamilyConnectBroker
    $result.service = [string]$service.Status
    $result.startType = [string]$service.StartType
    $result.stage = 'pipe-connect'
    $pipe = [IO.Pipes.NamedPipeClientStream]::new('.', 'FamilyConnect.Broker.v1',
        [IO.Pipes.PipeAccessRights]::ReadWrite, [IO.Pipes.PipeOptions]::Asynchronous,
        [Security.Principal.TokenImpersonationLevel]::Impersonation, [IO.HandleInheritability]::None)
    $pipe.Connect(5000)
    $result.stage = 'load-diagnostic-helper'
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class FcBrokerDiagnostic {
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetNamedPipeServerProcessId(SafePipeHandle pipe,out uint pid);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool QueryFullProcessImageName(IntPtr process,uint flags,StringBuilder path,ref int size);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
 public static string ServerPath(SafePipeHandle pipe) {
  uint pid;
  if(!GetNamedPipeServerProcessId(pipe,out pid))throw new System.ComponentModel.Win32Exception();
  var handle=OpenProcess(0x1000,false,pid);
  if(handle==IntPtr.Zero)throw new System.ComponentModel.Win32Exception();
  try { int size=32768;var path=new StringBuilder(size);
   if(!QueryFullProcessImageName(handle,0,path,ref size))throw new System.ComponentModel.Win32Exception();
   return path.ToString();
  } finally {CloseHandle(handle);}
 }
}
'@
    $result.stage = 'server-identity'
    $serverPath = [FcBrokerDiagnostic]::ServerPath($pipe.SafePipeHandle)
    $installed = Join-Path $env:ProgramFiles 'Family Connect\FamilyConnect.exe'
    $result.serverMatchesDefaultInstall = [string]::Equals($serverPath,$installed,[StringComparison]::OrdinalIgnoreCase)
    # The broker path is discovered from the pipe, not supplied over it.
    $result.serverFileVersion = [Diagnostics.FileVersionInfo]::GetVersionInfo($serverPath).FileVersion
    $result.stage = 'status-reply'
    $deadline = [Threading.CancellationTokenSource]::new(8000)
    $body = [Text.Encoding]::UTF8.GetBytes('{"action":"status"}')
    $header = [BitConverter]::GetBytes([int]$body.Length)
    $pipe.WriteAsync($header,0,4,$deadline.Token).GetAwaiter().GetResult()
    $pipe.WriteAsync($body,0,$body.Length,$deadline.Token).GetAwaiter().GetResult()
    function Read-Exact([byte[]]$Buffer) {
        $offset = 0
        while($offset -lt $Buffer.Length) {
            $count = $pipe.ReadAsync($Buffer,$offset,$Buffer.Length-$offset,$deadline.Token).GetAwaiter().GetResult()
            if($count -eq 0){throw [IO.EndOfStreamException]::new()}
            $offset += $count
        }
    }
    $header = [byte[]]::new(4)
    Read-Exact $header
    $size = [BitConverter]::ToInt32($header,0)
    if($size -lt 1 -or $size -gt 16384){throw [IO.InvalidDataException]::new()}
    $body = [byte[]]::new($size)
    Read-Exact $body
    $reply = [Text.Encoding]::UTF8.GetString($body) | ConvertFrom-Json
    $result.replyOk = $reply.ok -eq $true
    # Do not print arbitrary server strings, identity fields, or the full reply.
    if($reply.state -in @('on','off','inactive','pending','unknown','other-user')){$result.state=$reply.state}
    $result.ok = $result.replyOk
    $result.stage = 'complete'
} catch {
    $failure = $_.Exception
    while($null -ne $failure.InnerException){$failure=$failure.InnerException}
    $result.errorType = $failure.GetType().Name
    $result.hresult = $failure.HResult.ToString('X8')
    if($failure -is [ComponentModel.Win32Exception]){$result.win32Error=$failure.NativeErrorCode}
} finally {
    if($null -ne $pipe){$pipe.Dispose()}
    if($null -ne $deadline){$deadline.Dispose()}
}
$result | ConvertTo-Json
