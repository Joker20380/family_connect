using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using Microsoft.Win32.SafeHandles;
namespace FamilyConnect;
internal static class Native
{
    public const string BrokerName="FamilyConnectBroker";
    public const string TunnelName="WireGuardTunnel$fc-native";
    public static string Exe => Path.Combine(AppContext.BaseDirectory,"FamilyConnect.exe");
    public static bool Admin => new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator);
    [DllImport("kernel32.dll",SetLastError=true)]static extern bool GetNamedPipeServerProcessId(SafePipeHandle pipe,out uint pid);
    [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern bool QueryFullProcessImageName(IntPtr process,uint flags,StringBuilder path,ref int size);
    [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr handle);
    public static void VerifyPipeServer(SafePipeHandle pipe)
    {
        if(!GetNamedPipeServerProcessId(pipe,out uint pid))throw new IOException("broker identity");
        var handle=OpenProcess(0x1000,false,pid);if(handle==IntPtr.Zero)throw new IOException("broker process");
        try {
            int size=32768;var path=new StringBuilder(size);
            if(!QueryFullProcessImageName(handle,0,path,ref size) || !string.Equals(path.ToString(),Exe,StringComparison.OrdinalIgnoreCase))
                throw new IOException("untrusted broker");
        }finally{CloseHandle(handle);}
    }
    public static void Sc(params string[] args)
    {
        var info=new ProcessStartInfo(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"sc.exe"))
            {UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        foreach(var arg in args)info.ArgumentList.Add(arg);
        using var proc=Process.Start(info) ?? throw new IOException("SCM");
        var output=proc.StandardOutput.ReadToEndAsync();var error=proc.StandardError.ReadToEndAsync();
        if(!proc.WaitForExit(25000)){proc.Kill();throw new System.TimeoutException("SCM");}
        Task.WaitAll(output,error);
        if(proc.ExitCode!=0)throw new Win32Exception(proc.ExitCode);
    }
    public static string TunnelState()
    {
        try{using var s=new ServiceController(TunnelName);return s.Status switch {
            ServiceControllerStatus.Running=>"on",ServiceControllerStatus.Stopped=>"off",_=>"pending"};}
        catch(InvalidOperationException e) when(e.InnerException is Win32Exception {NativeErrorCode:1060}){return "off";}
    }
    public static void StopTunnel()
    {
        if(TunnelState()=="off")return;
        using var service=new ServiceController(TunnelName);
        service.Stop();service.WaitForStatus(ServiceControllerStatus.Stopped,TimeSpan.FromSeconds(20));
    }
    public static void StartTunnel(string profile)
    {
        using var service=new ServiceController(TunnelName);
        try{_ = service.Status;}
        catch(InvalidOperationException e) when(e.InnerException is Win32Exception {NativeErrorCode:1060}) {
            Sc("create",TunnelName,"binPath=",$"\"{Exe}\" /tunnel-service \"{profile}\"","start=","demand","depend=","Nsi/TcpIp",
                "DisplayName=","Family Connect Tunnel");
        }
        // WireGuard's restricted service token requires an unrestricted service SID.
        Sc("sidtype",TunnelName,"unrestricted");service.Refresh();service.Start();
        service.WaitForStatus(ServiceControllerStatus.Running,TimeSpan.FromSeconds(20));
    }
    public static void Install()
    {
        if(!Admin)throw new UnauthorizedAccessException();
        Store.SecureRoot();
        Sc("create",BrokerName,"binPath=",$"\"{Exe}\" /broker","start=","auto","DisplayName=","Family Connect Connection Service");
        Sc("description",BrokerName,"Manages local Family Connect activation and encrypted VPN sessions.");
        Sc("start",BrokerName);
    }
    public static void Remove()
    {
        if(!Admin)throw new UnauthorizedAccessException();
        using var broker=new ServiceController(BrokerName);
        try{if(broker.Status!=ServiceControllerStatus.Stopped){broker.Stop();broker.WaitForStatus(ServiceControllerStatus.Stopped,TimeSpan.FromSeconds(25));}}
        catch(InvalidOperationException e) when(e.InnerException is Win32Exception {NativeErrorCode:1060}){}
        StopTunnel();
        foreach(var name in new[]{TunnelName,BrokerName}) {
            try{Sc("delete",name);}catch(Win32Exception e) when(e.NativeErrorCode==1060){}
        }
    }
    [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetDefaultDllDirectories(uint flags);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern IntPtr LoadLibraryEx(string path,IntPtr reserved,uint flags);
    [DllImport("kernel32.dll",CharSet=CharSet.Ansi,ExactSpelling=true)]static extern IntPtr GetProcAddress(IntPtr module,string name);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl,CharSet=CharSet.Unicode)]delegate bool TunnelProc([MarshalAs(UnmanagedType.LPWStr)]string path);
    public static int RunTunnel(string profile)
    {
        if(!WindowsIdentity.GetCurrent().IsSystem || profile!=Store.TunnelPath) return 2;
        if(!SetDefaultDllDirectories(0x1000))return 3;
        var library=LoadLibraryEx(Path.Combine(AppContext.BaseDirectory,"tunnel.dll"),IntPtr.Zero,0x100|0x800);
        if(library==IntPtr.Zero)return 4;
        var proc=GetProcAddress(library,"WireGuardTunnelService");if(proc==IntPtr.Zero)return 5;
        return Marshal.GetDelegateForFunctionPointer<TunnelProc>(proc)(profile)?0:6;
    }
    [StructLayout(LayoutKind.Sequential)]struct Blob {public int Size;public IntPtr Data;}
    [DllImport("crypt32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern bool CryptProtectData(ref Blob input,string description,IntPtr entropy,IntPtr reserved,IntPtr prompt,uint flags,out Blob output);
    [DllImport("kernel32.dll")]static extern IntPtr LocalFree(IntPtr memory);
    public static byte[] EncryptTunnel(byte[] data)
    {
        // Official tunnel.dll verifies the DPAPI description against the tunnel filename.
        var input=new Blob{Size=data.Length,Data=Marshal.AllocHGlobal(data.Length)};
        try{
            Marshal.Copy(data,0,input.Data,data.Length);
            if(!CryptProtectData(ref input,"fc-native",IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,1,out var output))throw new Win32Exception();
            try{var encrypted=new byte[output.Size];Marshal.Copy(output.Data,encrypted,0,output.Size);return encrypted;}
            finally{LocalFree(output.Data);}
        }finally{Marshal.Copy(new byte[data.Length],0,input.Data,data.Length);Marshal.FreeHGlobal(input.Data);CryptographicOperations.ZeroMemory(data);}
    }
}
