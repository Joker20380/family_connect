using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.ServiceProcess;
namespace FamilyConnect;
internal sealed class Broker:ServiceBase
{
    readonly CancellationTokenSource stop=new();Task? loop;readonly TcpSession tcp=new();readonly AutoSession automatic;
    public Broker(){automatic=new(tcp);ServiceName=Native.BrokerName;CanStop=true;CanShutdown=true;AutoLog=false;}
    protected override void OnStart(string[] args)
    {
        Store.SecureRoot();RequestAdditionalTime(120000);AutoSession.Recover().GetAwaiter().GetResult();loop=Task.Run(Listen);
    }
    protected override void OnStop()
    {
        RequestAdditionalTime(120000);ShutdownCore();
    }
    void ShutdownCore(){stop.Cancel();loop?.GetAwaiter().GetResult();automatic.Shutdown().GetAwaiter().GetResult();tcp.Shutdown().GetAwaiter().GetResult();Native.StopTunnel();}
    protected override void OnShutdown()=>ShutdownCore();
    async Task Listen()
    {
        var acl=new PipeSecurity();
        acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.NetworkSid,null),PipeAccessRights.FullControl,AccessControlType.Deny));
        acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.LocalSystemSid,null),PipeAccessRights.FullControl,AccessControlType.Allow));
        acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.AuthenticatedUserSid,null),
            PipeAccessRights.ReadWrite|PipeAccessRights.Synchronize,AccessControlType.Allow));
        while(!stop.IsCancellationRequested){
            try{
                using var pipe=NamedPipeServerStreamAcl.Create(Wire.Pipe,PipeDirection.InOut,1,PipeTransmissionMode.Byte,
                    PipeOptions.Asynchronous|PipeOptions.FirstPipeInstance,16384,16384,acl);
                await pipe.WaitForConnectionAsync(stop.Token);
                using var deadline=CancellationTokenSource.CreateLinkedTokenSource(stop.Token);deadline.CancelAfter(TimeSpan.FromSeconds(35));
                var request=await Wire.Read<Request>(pipe,deadline.Token);
                string? sid=null;pipe.RunAsClient(()=>sid=WindowsIdentity.GetCurrent().User?.Value);
                if(sid is null)throw new UnauthorizedAccessException();
                Reply answer;
                try{answer=Handle(sid,request);}
                catch(FormatException){answer=new(false,"unknown",Error:"activation-invalid");}
                catch(System.Text.Json.JsonException){answer=new(false,"unknown",Error:"activation-invalid");}
                catch(Exception){answer=new(false,"unknown",Error:"system-failed");}
                await Wire.Write(pipe,answer,deadline.Token);
            }
            catch(OperationCanceledException) when(stop.IsCancellationRequested){break;}
            catch(Exception){try{await Task.Delay(200,stop.Token);}catch(OperationCanceledException){break;}}
        }
    }
    Reply Handle(string sid,Request request)
    {
        var auto=automatic.Status;bool autoActive=auto.State!="off";
        var session=autoActive?auto:tcp.Status;
        var state=session.State!="off"?session.State:Native.TunnelState();
        var owner=session.State!="off"?session.Owner:File.Exists(Store.OwnerPath)?File.ReadAllText(Store.OwnerPath):null;
        var ready=File.Exists(Store.UserPath(sid,".conf.dpapi"));
        if(request.Action=="status")return new(true,state!="off"&&owner!=sid?"other-user":state!="off"?state:ready?"off":"inactive",Error:auto.Owner==sid&&auto.Error is not null?auto.Error:session.Owner==sid?session.Error:null,TcpReady:File.Exists(Store.UserPath(sid,".tcp.dpapi")),Transport:session.State!="off"?session.Transport:"wg",AwgReady:File.Exists(Store.UserPath(sid,".awg.dpapi")),Automatic:autoActive);
        if(request.Action=="request")return new(true,"inactive",Code:"FC1-"+Convert.ToHexString(Convert.FromBase64String(Store.Public(sid))));
        if(state!="off"&&owner!=sid)return new(false,"other-user",Error:"other-user");
        if(request.Action.StartsWith("connect",StringComparison.Ordinal)&&state=="off")automatic.ClearError();
        switch(request.Action){
            case "connect-auto":
                if(state!="off")return new(false,state,Error:"busy");
                var autoAwg=Store.Awg(sid);var autoTcp=Store.Tcp(sid);
                if(!ready&&autoAwg is null&&autoTcp is null)return new(false,"inactive",Error:"activation-required");
                automatic.Start(sid,ready,autoAwg,autoTcp);
                return new(true,"pending",Transport:automatic.Status.Transport,Automatic:true);
            case "connect-awg":
                if(state!="off")return new(false,state,Error:"busy");
                var awg=Store.Awg(sid);if(awg is null)return new(false,"inactive",Error:"activation-required");
                if(!Directory.Exists(Path.Combine(AppContext.BaseDirectory,"awg")))return new(false,"off",Error:"awg-engine-missing");
                var key=Store.Key(sid);
                try{tcp.StartAwg(sid,awg,Convert.ToBase64String(key));}finally{System.Security.Cryptography.CryptographicOperations.ZeroMemory(key);}
                return new(true,"pending",Transport:"awg",AwgReady:true);
            case "activate-awg":
                if(state!="off")return new(false,state,Error:"disconnect-first");
                Store.ActivateAwg(sid,request.Activation??"");return new(true,ready?"off":"inactive",AwgReady:true);
            case "connect-tcp":
                if(state!="off")return new(false,state,Error:"busy");
                var profile=Store.Tcp(sid);
                if(profile is null)return new(false,"inactive",Error:"activation-required");
                if(!Directory.Exists(Path.Combine(AppContext.BaseDirectory,"tcp")))return new(false,"off",Error:"tcp-engine-missing");
                tcp.Start(sid,profile);return new(true,"pending",TcpReady:true,Transport:"tcp");
            case "activate-tcp":
                if(state!="off")return new(false,state,Error:"disconnect-first");
                Store.ActivateTcp(sid,request.Activation??"");return new(true,ready?"off":"inactive",TcpReady:true);
            case "activate":
                if(state!="off")return new(false,state,Error:"disconnect-first");
                Store.Activate(sid,request.Activation??"");return new(true,"off");
            case "connect":
                if(session.State!="off")return new(false,state,Error:"busy");
                if(!ready)return new(false,"inactive",Error:"activation-required");
                if(state=="on")return new(true,"on");
                if(state!="off")return new(false,state,Error:"busy");
                Store.Atomic(Store.TunnelPath,File.ReadAllBytes(Store.UserPath(sid,".conf.dpapi")));
                Store.Atomic(Store.OwnerPath,System.Text.Encoding.UTF8.GetBytes(sid));
                try{Native.StartTunnel(Store.TunnelPath);}catch{Native.StopTunnel();throw;}
                return new(true,Native.TunnelState());
            case "disconnect":
                if(autoActive){automatic.Stop();return new(true,"pending",Transport:auto.Transport,Automatic:true);}
                if(session.State!="off"){tcp.Stop();return new(true,tcp.Status.State,Transport:tcp.Status.Transport);}
                Native.StopTunnel();return new(true,"off");
            default:return new(false,"unknown",Error:"unsupported-action");
        }
    }
}
