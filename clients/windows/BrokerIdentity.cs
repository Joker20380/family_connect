using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
namespace FamilyConnect;

// SCM permits authenticated local users to query status/configuration. Opening a
// LocalSystem process does not: that rejected ordinary users before any IPC request.
// Bind the pipe PID to the running, separately hosted LocalSystem service and its
// administrator-controlled executable configuration before sending any credentials.
internal static class BrokerIdentity
{
    [StructLayout(LayoutKind.Sequential)]
    struct Status
    {
        internal uint Type, State, Controls, Win32Exit, ServiceExit, Checkpoint, WaitHint, Pid, Flags;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct Config
    {
        internal uint Type, StartType, ErrorControl;
        internal IntPtr BinaryPath, LoadOrderGroup;
        internal uint Tag;
        internal IntPtr Dependencies, Account, DisplayName;
    }
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool GetNamedPipeServerProcessId(SafePipeHandle pipe, out uint pid);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr OpenSCManager(string? machine, string? database, uint access);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr OpenService(IntPtr manager, string name, uint access);
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern bool QueryServiceStatusEx(IntPtr service, int level, out Status status, int size, out int needed);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool QueryServiceConfig(IntPtr service, IntPtr config, int size, out int needed);
    [DllImport("advapi32.dll")]
    static extern bool CloseServiceHandle(IntPtr handle);

    internal static void Verify(SafePipeHandle pipe, string serviceName, string executable)
    {
        if(!GetNamedPipeServerProcessId(pipe,out uint pid))throw new Win32Exception();
        var manager=OpenSCManager(null,null,0x0001); // SC_MANAGER_CONNECT only.
        if(manager==IntPtr.Zero)throw new Win32Exception();
        try
        {
            var service=OpenService(manager,serviceName,0x0001|0x0004); // QUERY_CONFIG | QUERY_STATUS.
            if(service==IntPtr.Zero)throw new Win32Exception();
            try
            {
                if(!QueryServiceStatusEx(service,0,out var status,Marshal.SizeOf<Status>(),out _))throw new Win32Exception();
                if(pid==0 || status.Pid!=pid || status.State!=4 || status.Type!=0x10)
                    throw new IOException("Untrusted broker service process");
                // The documented maximum service configuration buffer is 8 KiB.
                const int size=8192;
                var buffer=Marshal.AllocHGlobal(size);
                try
                {
                    if(!QueryServiceConfig(service,buffer,size,out _))throw new Win32Exception();
                    var config=Marshal.PtrToStructure<Config>(buffer);
                    if(config.Type!=0x10 || !string.Equals(Marshal.PtrToStringUni(config.Account),"LocalSystem",StringComparison.OrdinalIgnoreCase)
                        || !string.Equals(Marshal.PtrToStringUni(config.BinaryPath),$"\"{executable}\" /broker",StringComparison.OrdinalIgnoreCase))
                        throw new IOException("Untrusted broker service configuration");
                }
                finally{Marshal.FreeHGlobal(buffer);}
            }
            finally{CloseServiceHandle(service);}
        }
        finally{CloseServiceHandle(manager);}
    }
}
