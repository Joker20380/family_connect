$ErrorActionPreference='Stop'
# CI-only check: create and close an adapter without addresses, routes or traffic.
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class DriverCheck {
    [UnmanagedFunctionPointer(CallingConvention.Winapi, CharSet=CharSet.Unicode, SetLastError=true)]
    public delegate IntPtr Create([MarshalAs(UnmanagedType.LPWStr)]string name,[MarshalAs(UnmanagedType.LPWStr)]string type,IntPtr guid);
    [UnmanagedFunctionPointer(CallingConvention.Winapi)] public delegate void Close(IntPtr adapter);
    public static void Run(string path) {
        var library=NativeLibrary.Load(path);
        try {
            var create=Marshal.GetDelegateForFunctionPointer<Create>(NativeLibrary.GetExport(library,"WireGuardCreateAdapter"));
            var close=Marshal.GetDelegateForFunctionPointer<Close>(NativeLibrary.GetExport(library,"WireGuardCloseAdapter"));
            var adapter=create("FamilyConnect-CI","Family Connect",IntPtr.Zero);
            if(adapter==IntPtr.Zero)throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            close(adapter);
        } finally {NativeLibrary.Free(library);}
    }
}
'@
try {
    [DriverCheck]::Run("$env:ProgramFiles/Family Connect/wireguard.dll")
    Write-Host 'Signed driver loaded; test adapter created and removed without routes.'
} catch {
    Write-Host "::error::Driver adapter check failed: $($_.Exception.Message)"
    throw
}
