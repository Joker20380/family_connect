using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32.SafeHandles;
namespace FamilyConnect;

// Internal primitive for the broker's forthcoming network session. No IPC action accepts a path or raw config.
internal sealed class TcpEngine : IDisposable
{
    const string XraySha="74475d8c4f68dd07bef754e56778eb2a9061e4dfcc954fa008b912a989bd848a";
    const string WintunSha="e5da8447dc2c320edc0fc52fa01885c103de8c118481f683643cacc3220dafce";
    readonly Process process;
    readonly ProcessJob job;
    readonly FileStream[] binaries;
    bool disposed;
    TcpEngine(Process process,ProcessJob job,FileStream[] binaries){this.process=process;this.job=job;this.binaries=binaries;}
    public int Id=>process.Id;
    public bool Running=>!disposed&&!process.HasExited;
    public Task WaitForExitAsync()=>process.WaitForExitAsync();
    public int ExitCode=>process.ExitCode;
    static FileStream Verified(string folder,string name,string hash)
    {
        var path=Path.Combine(folder,name);
        if((File.GetAttributes(path)&FileAttributes.ReparsePoint)!=0)throw new IOException("Unsafe engine file");
        // Keep a non-write/delete-shared handle open until the child has exited.
        var stream=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.Read);
        try {
            if(Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant()!=hash)throw new IOException("TCP engine checksum mismatch");
            return stream;
        }catch{stream.Dispose();throw;}
    }
    public static TcpEngine Start(string trustedDirectory,string config)
    {
        if(!OperatingSystem.IsWindows())throw new PlatformNotSupportedException();
        if(Encoding.UTF8.GetByteCount(config)>16384)throw new FormatException("TCP config size");
        string folder=Path.GetFullPath(trustedDirectory);
        if((File.GetAttributes(folder)&FileAttributes.ReparsePoint)!=0)throw new IOException("Unsafe engine directory");
        var files=new List<FileStream>();Process? child=null;ProcessJob? owner=null;
        try {
            files.Add(Verified(folder,"xray.exe",XraySha));files.Add(Verified(folder,"wintun.dll",WintunSha));
            owner=new ProcessJob();
            var start=new ProcessStartInfo(Path.Combine(folder,"xray.exe")){
                WorkingDirectory=folder,UseShellExecute=false,CreateNoWindow=true,
                RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true,
                StandardInputEncoding=new UTF8Encoding(false)
            };
            // Do not inherit user-configurable Xray paths, proxy or DLL search environment.
            var inherited=start.Environment.ToDictionary(x=>x.Key,x=>x.Value,StringComparer.OrdinalIgnoreCase);
            start.Environment.Clear();
            // SetupAPI/Wintun needs the standard Windows environment to install its signed driver.
            // In production this is the LocalSystem service environment, never supplied over IPC.
            foreach(var name in new[]{"SystemDrive","ProgramData","ALLUSERSPROFILE","ProgramFiles","ProgramFiles(x86)",
                "ProgramW6432","CommonProgramFiles","CommonProgramFiles(x86)","CommonProgramW6432",
                "TEMP","TMP","USERPROFILE","LOCALAPPDATA","APPDATA","PUBLIC","COMPUTERNAME",
                "PROCESSOR_ARCHITECTURE","PROCESSOR_IDENTIFIER","PROCESSOR_LEVEL","PROCESSOR_REVISION",
                "NUMBER_OF_PROCESSORS","OS"})
                if(inherited.TryGetValue(name,out var value)&&value is not null)start.Environment[name]=value;
            var windows=Environment.GetFolderPath(Environment.SpecialFolder.Windows);
            start.Environment["SystemRoot"]=windows;start.Environment["WINDIR"]=windows;
            start.Environment["SystemDrive"]=Path.GetPathRoot(windows)!.TrimEnd('\\');
            start.Environment["ComSpec"]=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"cmd.exe");
            start.Environment["PATH"]=Environment.GetFolderPath(Environment.SpecialFolder.System);
            start.Environment["XRAY_LOCATION_ASSET"]=folder;start.Environment["XRAY_LOCATION_CONFIG"]=folder;
            foreach(var arg in new[]{"run","-format","json","-config","stdin:"})start.ArgumentList.Add(arg);
            child=Process.Start(start)??throw new IOException("TCP engine start failed");
            // Xray's pinned loader waits for stdin EOF. Before assignment it cannot parse a config/create TUN.
            owner.Attach(child);
            // Drain without retaining/printing engine diagnostics, which can include a credential on errors.
            _=Drain(child.StandardOutput.BaseStream);_=Drain(child.StandardError.BaseStream);
            child.StandardInput.Write(config);child.StandardInput.Close();
            if(child.WaitForExit(150))throw new IOException("TCP engine rejected configuration");
            return new TcpEngine(child,owner,files.ToArray());
        }catch{
            owner?.Dispose();
            if(child is not null){try{if(!child.HasExited){child.Kill();child.WaitForExit(10000);}}finally{child.Dispose();}}
            foreach(var file in files)file.Dispose();throw;
        }
    }
    static async Task Drain(Stream stream){
        try {
#if TCP_ENGINE_TEST
            // Compiled only into the isolated synthetic CI harness, never the desktop executable.
            await stream.CopyToAsync(Console.OpenStandardError());
#else
            await stream.CopyToAsync(Stream.Null);
#endif
        }catch(IOException){}catch(ObjectDisposedException){}
    }
    public void Dispose()
    {
        if(disposed)return;disposed=true;
        try {
            // Closing the sole non-inheritable handle terminates every process in the job.
            job.Dispose();
            if(!process.WaitForExit(10000))throw new TimeoutException("TCP process did not stop");
        }finally{process.Dispose();foreach(var file in binaries)file.Dispose();}
    }
}
