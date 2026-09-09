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
                return status.Ok&&request.Ok&&request.Code?.Length==68&&!invalid.Ok?0:10;
            }
            if(args.Length>0&&args[0]!="/smoke")return 2;
            ApplicationConfiguration.Initialize();
            using var form=new MainForm(args.Contains("/smoke"));Application.Run(form);return 0;
        }catch(Exception e){
            if(args.Contains("/broker-test"))File.WriteAllText(Path.Combine(Path.GetTempPath(),"fc-broker-check.txt"),e.GetType().Name+"; hresult="+e.HResult.ToString("X"));
            if(args.Length==0)MessageBox.Show("Family Connect could not start. / Не удалось запустить Family Connect.");
            return 1;
        }
    }
}
