using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.ServiceProcess;
namespace FamilyConnect;
internal sealed class Broker:ServiceBase
{
    readonly CancellationTokenSource stop=new();Task? loop;readonly TcpSession tcp=new();
    public Broker(){ServiceName=Native.BrokerName;CanStop=true;CanShutdown=true;AutoLog=false;}
    protected override void OnStart(string[] args)
    {
        Store.SecureRoot();RequestAdditionalTime(60000);TcpSession.Recover().GetAwaiter().GetResult();loop=Task.Run(Listen);
    }
    protected override void OnStop()
    {
        RequestAdditionalTime(120000);ShutdownCore();
    }
    void ShutdownCore(){stop.Cancel();loop?.GetAwaiter().GetResult();tcp.Shutdown().GetAwaiter().GetResult();Native.StopTunnel();}
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
        var session=tcp.Status;
        var state=session.State!="off"?session.State:Native.TunnelState();
        var owner=session.State!="off"?session.Owner:File.Exists(Store.OwnerPath)?File.ReadAllText(Store.OwnerPath):null;
        var ready=File.Exists(Store.UserPath(sid,".conf.dpapi"));
        if(request.Action=="status")return new(true,state!="off"&&owner!=sid?"other-user":state!="off"?state:ready?"off":"inactive",Error:session.Owner==sid?session.Error:null,TcpReady:File.Exists(Store.UserPath(sid,".tcp.dpapi")),Transport:session.State!="off"?"tcp":"wg");
        if(request.Action=="request")return new(true,"inactive",Code:"FC1-"+Convert.ToHexString(Convert.FromBase64String(Store.Public(sid))));
        if(state!="off"&&owner!=sid)return new(false,"other-user",Error:"other-user");
        switch(request.Action){
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
                if(session.State!="off"){tcp.Stop();return new(true,tcp.Status.State,Transport:"tcp");}
                Native.StopTunnel();return new(true,"off");
            default:return new(false,"unknown",Error:"unsupported-action");
        }
    }
}
