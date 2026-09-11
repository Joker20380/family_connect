using System.Text.Json;
namespace FamilyConnect;
internal sealed class TcpSession
{
    readonly object gate=new();
    string state="off",transport="tcp";string? owner,error;
    Task? worker;CancellationTokenSource? cancel;
    static string Marker=>Path.Combine(Store.Root,"tcp-session.json");
    sealed record Journal(int Version,string Adapter,int? Awg=null);
    public (string State,string? Owner,string? Error,string Transport) Status {get{lock(gate)return(state,owner,error,transport);}}
    public static async Task Recover()
    {
        if(!File.Exists(Marker))return;
        if(new FileInfo(Marker).Length>4096)throw new IOException("session journal size");
        var record=JsonSerializer.Deserialize<Journal>(File.ReadAllText(Marker),Activation.Json)??throw new FormatException("session journal");
        if(record.Version!=1)throw new FormatException("session journal version");
        TcpNetwork.ValidateAdapter(record.Adapter);
        await TcpNetwork.Call("cleanup",record.Adapter,record.Awg);File.Delete(Marker);
    }
    public void Start(string sid,TcpGrant grant,bool recover=true)=>StartCore(sid,grant,null,null,recover);
    public void StartAwg(string sid,AwgGrant grant,string key,bool recover=true)=>StartCore(sid,null,grant,key,recover);
    void StartCore(string sid,TcpGrant? grant,AwgGrant? awg,string? key,bool recover)
    {
        lock(gate){
            if(state!="off"||File.Exists(Marker))throw new InvalidOperationException("TCP session busy or needs cleanup");
            owner=sid;error=null;transport=awg is null?"tcp":"awg";state="pending";cancel=new CancellationTokenSource();
            worker=Run(grant,awg,key,cancel.Token,recover);
        }
    }
    public void Stop(){lock(gate){if(state is "on" or "pending"){state="pending";cancel?.Cancel();}}}
    public async Task Shutdown(){Stop();Task? task;lock(gate)task=worker;if(task is not null)await task;}
    async Task Run(TcpGrant? grant,AwgGrant? awg,string? key,CancellationToken token,bool recover)
    {
        // Yield before slow operations so the pipe can accept cancellation and status while starting.
        await Task.Yield();
        // One retry budget per explicit Connect; successful restarts do not reset it.
        int retries=0;bool established=false;
        while(true){
            TcpEngine? engine=null;string? failure=null;bool clean=false;
            using var monitoring=CancellationTokenSource.CreateLinkedTokenSource(token);Task? health=null;
            var alias=(awg is null?"fctcp":"fcawg")+Guid.NewGuid().ToString("N")[..8];
            try {
                token.ThrowIfCancellationRequested();
                var route=await TcpNetwork.Call("preflight",alias,awg?.Number);token.ThrowIfCancellationRequested();
                Store.Atomic(Marker,JsonSerializer.SerializeToUtf8Bytes(new Journal(1,alias,awg?.Number),Activation.Json));
                var uplink=route.GetProperty("uplink").GetString()!;
                if(awg is not null){
                    engine=TcpEngine.StartAwg(Path.Combine(AppContext.BaseDirectory,"awg"),AwgProfile.Config(awg,key!,alias,uplink));
                }else {
#if TCP_SESSION_TEST
                var config=JsonSerializer.Serialize(new{log=new{loglevel="none"},inbounds=new[]{new{protocol="tun",settings=new{name=alias,MTU=1280}}},
                    outbounds=new[]{new{protocol="vless",settings=new{vnext=new[]{new{address="127.0.0.1",port=grant!.Port,users=new[]{new{id=grant.Id,encryption="none"}}}}},
                        streamSettings=new{sockopt=new{@interface=uplink}}}}});
#else
                var config=TcpProfile.Config(grant!,alias,uplink);
#endif
                engine=TcpEngine.Start(Path.Combine(AppContext.BaseDirectory,"tcp"),config);
                }
                await TcpNetwork.Call("apply",alias,awg?.Number);token.ThrowIfCancellationRequested();
                if(!engine.Running)throw new IOException("TCP exited during start");
                if(!recover&&!await TcpHealth.Ready(alias,token,awg?.Number))throw new IOException("transport unavailable");
                lock(gate){token.ThrowIfCancellationRequested();established=true;state="on";error=null;}
                health=TcpHealth.Watch(alias,monitoring.Token,awg?.Number);
                var ended=await Task.WhenAny(engine.WaitForExitAsync(),health);
                if(!token.IsCancellationRequested)failure=ended==health?"tcp-health-failed":"tcp-engine-exited";
            }catch(OperationCanceledException) when(token.IsCancellationRequested){}
            catch(Exception){failure="tcp-session-failed";}
            finally {
                lock(gate)state="pending";
                monitoring.Cancel();
                if(health is not null){try{await health;}catch(OperationCanceledException){}}
                try {
                    engine?.Dispose();
                    if(File.Exists(Marker))await Recover();
                    clean=true;
                }catch{failure="tcp-cleanup-required";}
            }
            lock(gate){
                // Never reconnect after user cancellation, failed cleanup, or an initial setup failure.
                if(!clean||token.IsCancellationRequested||!established||!recover||retries==3){
                    state=clean?"off":"pending";
                    error=!clean?failure:token.IsCancellationRequested?null:established&&retries==3?"tcp-recovery-exhausted":failure;
                    cancel?.Dispose();cancel=null;return;
                }
                state="pending";error="tcp-reconnecting";
            }
            var delay=TimeSpan.FromSeconds(15*(1<<retries++));
            try {await Task.Delay(delay,token);}
            catch(OperationCanceledException) when(token.IsCancellationRequested){
                lock(gate){state="off";error=null;cancel?.Dispose();cancel=null;}return;
            }
        }
    }
}
