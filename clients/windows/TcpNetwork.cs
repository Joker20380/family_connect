using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
namespace FamilyConnect;
internal static class TcpNetwork
{
    public static void ValidateAdapter(string alias){if(!Regex.IsMatch(alias,@"\Afc(?:tcp|awg)[0-9a-f]{8}\z"))throw new FormatException("session adapter");}
    public static async Task<JsonElement> Call(string operation,string adapter,int? awg=null)
    {
        ValidateAdapter(adapter);if(awg is int n&&(n<4||n>254))throw new FormatException("AWG address");
        using var resource=typeof(TcpNetwork).Assembly.GetManifestResourceStream("FamilyConnect.TcpNetwork.ps1")!;
        using var reader=new StreamReader(resource);
        var code=await reader.ReadToEndAsync();
        var info=new ProcessStartInfo(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"WindowsPowerShell","v1.0","powershell.exe")){
            UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardInputEncoding=new UTF8Encoding(false),StandardOutputEncoding=new UTF8Encoding(false)
        };
        foreach(var arg in new[]{"-NoProfile","-NonInteractive","-EncodedCommand",Convert.ToBase64String(Encoding.Unicode.GetBytes(code))})info.ArgumentList.Add(arg);
        using var job=new ProcessJob();
        using var process=Process.Start(info)??throw new IOException("network worker");
        try {
            job.Attach(process); // The fixed script waits for input EOF before any mutation.
            var output=process.StandardOutput.ReadToEndAsync();
            #if TCP_SESSION_TEST
            var error=process.StandardError.ReadToEndAsync();
#else
            var error=process.StandardError.BaseStream.CopyToAsync(Stream.Null);
#endif
#if TCP_SESSION_TEST
            const bool test=true;
#else
            const bool test=false;
#endif
            await process.StandardInput.WriteAsync(JsonSerializer.Serialize(new{operation,adapter,test,awg}));process.StandardInput.Close();
            using var deadline=new CancellationTokenSource(TimeSpan.FromSeconds(55));
            await process.WaitForExitAsync(deadline.Token);await error;
            var text=await output;
            if(process.ExitCode!=0){
#if TCP_SESSION_TEST
                File.WriteAllText(Path.Combine(AppContext.BaseDirectory,"session-network-error.txt"),operation+"\n"+await error);
#endif
                throw new IOException("TCP network "+operation+" failed");
            }
            if(text.Length>8192)throw new IOException("network reply size");
            using var result=JsonDocument.Parse(text);return result.RootElement.Clone();
        }finally{
            job.Dispose();
            if(!process.HasExited){process.Kill();process.WaitForExit(10000);}
        }
    }
}
