using System.ServiceProcess;
namespace FamilyConnect;
internal static class Program
{
    [STAThread] static int Main(string[] args)
    {
        try{
            if(args.SequenceEqual(new[]{"/broker"})){ServiceBase.Run(new Broker());return 0;}
            if(args.Length==2&&args[0]=="/tunnel-service")return Native.RunTunnel(args[1]);
            if(args.SequenceEqual(new[]{"/install-service"})){Native.Install();return 0;}
            if(args.SequenceEqual(new[]{"/remove-service"})){Native.Remove();return 0;}
            if(args.SequenceEqual(new[]{"/broker-test"})){
                var status=Wire.Call(new("status")).GetAwaiter().GetResult();
                var request=Wire.Call(new("request")).GetAwaiter().GetResult();
                var invalid=Wire.Call(new("activate","{}")).GetAwaiter().GetResult();
                // A pipe hosted by this same installed EXE is still not the broker.
                // Reject it by service PID even when the executable path matches.
                var name="FamilyConnect.IdentityTest."+Guid.NewGuid().ToString("N");
                using var fakeServer=new System.IO.Pipes.NamedPipeServerStream(name,System.IO.Pipes.PipeDirection.InOut,1,
                    System.IO.Pipes.PipeTransmissionMode.Byte,System.IO.Pipes.PipeOptions.Asynchronous);
                var waiting=fakeServer.WaitForConnectionAsync();
                using var fakeClient=new System.IO.Pipes.NamedPipeClientStream(".",name,System.IO.Pipes.PipeDirection.InOut);
                fakeClient.Connect(5000);waiting.GetAwaiter().GetResult();
                bool rejected=false;
                try{Native.VerifyPipeServer(fakeClient.SafePipeHandle);}catch(IOException){rejected=true;}
                if(!rejected)return 11;
                return status.Ok&&request.Ok&&request.Code?.Length==68&&!invalid.Ok?0:10;
            }
            bool invite=args.Length==1&&System.Text.RegularExpressions.Regex.IsMatch(args[0],@"\Afamilyconnect://invite/[0-9a-f]{64}\z");
            if(args.Length>0&&args[0]!="/smoke"&&args[0]!="/layout-test"&&!invite)return 2;
            ApplicationConfiguration.Initialize();
            if(args.Contains("/layout-test")){MainForm.CheckLayouts();return 0;}
            if(args.Contains("/smoke")){using var form=new MainForm(true);Application.Run(form);}
            else new SingleWindowApplication().Run(args);
            return 0;
        }catch(Exception e){
            if(args.Contains("/layout-test"))File.WriteAllText(Path.Combine(Path.GetTempPath(),"fc-layout-check.txt"),e.ToString());
            if(args.Contains("/broker-test"))File.WriteAllText(Path.Combine(Path.GetTempPath(),"fc-broker-check.txt"),e.GetType().Name+"; hresult="+e.HResult.ToString("X"));
            if(args.Length==0)MessageBox.Show("Family Connect could not start. / Не удалось запустить Family Connect.");
            return 1;
        }
    }
}
