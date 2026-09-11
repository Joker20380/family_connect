using System.Text.Json;
namespace FamilyConnect;
internal sealed class TcpSession
{
    readonly object gate=new();
    string state="off";string? owner,error;
    Task? worker;CancellationTokenSource? cancel;
    static string Marker=>Path.Combine(Store.Root,"tcp-session.json");
    sealed record Journal(int Version,string Adapter);
    public (string State,string? Owner,string? Error) Status {get{lock(gate)return(state,owner,error);}}
    public static async Task Recover()
    {
        if(!File.Exists(Marker))return;
        if(new FileInfo(Marker).Length>4096)throw new IOException("session journal size");
        var record=JsonSerializer.Deserialize<Journal>(File.ReadAllText(Marker),Activation.Json)??throw new FormatException("session journal");
        if(record.Version!=1)throw new FormatException("session journal version");
        TcpNetwork.ValidateAdapter(record.Adapter);
        await TcpNetwork.Call("cleanup",record.Adapter);File.Delete(Marker);
    }
    public void Start(string sid,TcpGrant grant)
    {
        lock(gate){
            if(state!="off"||File.Exists(Marker))throw new InvalidOperationException("TCP session busy or needs cleanup");
            owner=sid;error=null;state="pending";cancel=new CancellationTokenSource();
            worker=Run(grant,cancel.Token);
        }
    }
    public void Stop(){lock(gate){if(state is "on" or "pending"){state="pending";cancel?.Cancel();}}}
    public async Task Shutdown(){Stop();Task? task;lock(gate)task=worker;if(task is not null)await task;}
    async Task Run(TcpGrant grant,CancellationToken token)
    {
        // Yield before slow operations so the pipe can accept cancellation and status while starting.
        await Task.Yield();
        // One retry budget per explicit Connect; successful restarts do not reset it.
        int retries=0;bool established=false;
        while(true){
            TcpEngine? engine=null;string? failure=null;bool clean=false;
            using var monitoring=CancellationTokenSource.CreateLinkedTokenSource(token);Task? health=null;
            var alias="fctcp"+Guid.NewGuid().ToString("N")[..8];
            try {
                token.ThrowIfCancellationRequested();
                var route=await TcpNetwork.Call("preflight",alias);token.ThrowIfCancellationRequested();
                Store.Atomic(Marker,JsonSerializer.SerializeToUtf8Bytes(new Journal(1,alias),Activation.Json));
                var uplink=route.GetProperty("uplink").GetString()!;
#if TCP_SESSION_TEST
                var config=JsonSerializer.Serialize(new{log=new{loglevel="none"},inbounds=new[]{new{protocol="tun",settings=new{name=alias,MTU=1280}}},
                    outbounds=new[]{new{protocol="vless",settings=new{vnext=new[]{new{address="127.0.0.1",port=grant.Port,users=new[]{new{id=grant.Id,encryption="none"}}}}},
                        streamSettings=new{sockopt=new{@interface=uplink}}}}});
#else
                var config=TcpProfile.Config(grant,alias,uplink);
#endif
                engine=TcpEngine.Start(Path.Combine(AppContext.BaseDirectory,"tcp"),config);
                await TcpNetwork.Call("apply",alias);token.ThrowIfCancellationRequested();
                if(!engine.Running)throw new IOException("TCP exited during start");
                lock(gate){token.ThrowIfCancellationRequested();established=true;state="on";error=null;}
                health=TcpHealth.Watch(alias,monitoring.Token);
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
                if(!clean||token.IsCancellationRequested||!established||retries==3){
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
