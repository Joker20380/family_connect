using FamilyConnect;
using System.ServiceProcess;
using System.Security.Principal;
if(!WindowsIdentity.GetCurrent().IsSystem&&Environment.GetEnvironmentVariable("GITHUB_ACTIONS")!="true")return 2;
try{
 if(args.SequenceEqual(new[]{"/recover-friends-session"})){await TcpSession.Recover();Console.WriteLine("clean");return 0;}
 if(args.SequenceEqual(new[]{"/friends-awg-session"})){
  using var input=System.Text.Json.JsonDocument.Parse(Console.ReadLine()!);var v=input.RootElement;
  var profile=FriendsCatalog.Verify(v.GetProperty("reply"),Convert.FromBase64String(v.GetProperty("anchor").GetString()!),v.GetProperty("device").GetString()!,"nl",Convert.FromBase64String(v.GetProperty("key").GetString()!));
  Store.SecureRoot();var session=new TcpSession();
  try{
   session.StartFriendsAwg("synthetic-ci-owner",FriendsCatalog.NativeAwg(profile));
   var until=DateTime.UtcNow.AddSeconds(60);
   while(session.Status.State!="on"){
    if(session.Status.Error is not null||DateTime.UtcNow>until)throw new IOException("Friends session start failed");
    await Task.Delay(100);
   }
   Console.WriteLine("ready");await Console.In.ReadLineAsync();
  }finally{await session.Shutdown();}
  Console.WriteLine("clean");return 0;
 }

 if(args.SequenceEqual(new[]{"/broker"})){ServiceBase.Run(new Broker());return 0;}
 if(args.SequenceEqual(new[]{"/install-service"})){Native.Install();return 0;}
 if(args.SequenceEqual(new[]{"/remove-service"})){Native.Remove();return 0;}
 return 2;
}catch(Exception e){File.WriteAllText(Path.Combine(AppContext.BaseDirectory,"session-host-error.txt"),e.ToString());return 1;}
