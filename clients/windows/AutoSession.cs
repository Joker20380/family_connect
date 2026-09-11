using System.Net.NetworkInformation;
using System.Security.Cryptography;
namespace FamilyConnect;
internal sealed class AutoSession
{
    readonly object gate=new();readonly TcpSession child;
    string state="off",transport="wg";string? owner,error;Task? worker;CancellationTokenSource? cancel;
    static string Marker=>Path.Combine(Store.Root,"auto-session.json");
    public AutoSession(TcpSession child){this.child=child;}
    public (string State,string? Owner,string? Error,string Transport) Status{get{lock(gate)return(state,owner,error,transport);}}
    static async Task CleanWg(){Native.StopTunnel();for(int i=0;i<40;i++){
        if(!NetworkInterface.GetAllNetworkInterfaces().Any(n=>n.Name=="fc-native"))return;
        await Task.Delay(250);
    }throw new IOException("WG adapter remains");}
    public static async Task Recover(){
        if(File.Exists(Marker)){
            if(new FileInfo(Marker).Length!=1||File.ReadAllText(Marker)!="1")throw new IOException("automatic session journal");
            await CleanWg();await TcpSession.Recover();File.Delete(Marker);
        }else await TcpSession.Recover();
    }
    public void Start(string sid,bool wg,AwgGrant? awg,TcpGrant? tcp){
        lock(gate){
            if(state!="off"||File.Exists(Marker))throw new InvalidOperationException("automatic session busy");
            var choices=new List<string>();if(wg)choices.Add("wg");if(awg is not null)choices.Add("awg");if(tcp is not null)choices.Add("tcp");
            if(choices.Count==0)throw new FormatException("no transports");
            owner=sid;transport=choices[0];state="pending";error=null;cancel=new();
            worker=Run(sid,choices,awg,tcp,cancel.Token);
        }
    }
    public void ClearError(){lock(gate){if(state=="off")error=null;}}
    public void Stop(){lock(gate){if(state!="off"){state="pending";cancel?.Cancel();}}}
    public async Task Shutdown(){Stop();Task? current;lock(gate)current=worker;if(current is not null)await current;}
    async Task Run(string sid,List<string> choices,AwgGrant? awg,TcpGrant? tcp,CancellationToken token){
        await Task.Yield();bool clean=false;string? failure=null;
        try{
            Store.Atomic(Marker,new byte[]{(byte)'1'});
            await TransportSequence.Run(choices,async(name,connected,ct)=>{
                ct.ThrowIfCancellationRequested();
                if(name=="wg"){
                    Store.Atomic(Store.TunnelPath,File.ReadAllBytes(Store.UserPath(sid,".conf.dpapi")));
                    Store.Atomic(Store.OwnerPath,System.Text.Encoding.UTF8.GetBytes(sid));
                    Native.StartTunnel(Store.TunnelPath);ct.ThrowIfCancellationRequested();
                    if(!await TcpHealth.Ready("fc-native",ct,wireguard:true))throw new IOException("WG unavailable");
                    connected();await TcpHealth.Watch("fc-native",ct,wireguard:true);
                }else{
                    if(name=="awg"){
                        var key=Store.Key(sid);try{child.StartAwg(sid,awg!,Convert.ToBase64String(key),recover:false);}finally{CryptographicOperations.ZeroMemory(key);}
                    }else child.Start(sid,tcp!,recover:false);
                    bool reported=false;
                    while(true){
                        ct.ThrowIfCancellationRequested();var current=child.Status;
                        if(current.State=="off"||current.Error=="tcp-cleanup-required")return;
                        if(current.State=="on"&&!reported){connected();reported=true;}
                        await Task.Delay(250,ct);
                    }
                }
            },async name=>{
                if(name=="wg")await CleanWg();
                else{await child.Shutdown();if(child.Status.State!="off")throw new IOException("transport cleanup incomplete");}
            },(name,on)=>{lock(gate){transport=name;state=on&&!token.IsCancellationRequested?"on":"pending";error=on?null:"auto-switching";}},token);
            failure="auto-exhausted";clean=true;
        }catch(TransportSequence.CleanupException){failure="auto-cleanup-required";}
        catch(OperationCanceledException) when(token.IsCancellationRequested){clean=true;}
        catch(Exception){failure="auto-session-failed";clean=!File.Exists(Marker);}
        if(clean){try{File.Delete(Marker);}catch{clean=false;failure="auto-cleanup-required";}}
        lock(gate){state=clean?"off":"pending";error=failure;cancel?.Dispose();cancel=null;}
    }
}
