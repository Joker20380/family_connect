using FamilyConnect;
using System.ServiceProcess;
using System.Security.Principal;
if(!WindowsIdentity.GetCurrent().IsSystem&&Environment.GetEnvironmentVariable("GITHUB_ACTIONS")!="true")return 2;
try{
 if(args.SequenceEqual(new[]{"/broker"})){ServiceBase.Run(new Broker());return 0;}
 if(args.SequenceEqual(new[]{"/install-service"})){Native.Install();return 0;}
 if(args.SequenceEqual(new[]{"/remove-service"})){Native.Remove();return 0;}
 return 2;
}catch(Exception e){File.WriteAllText(Path.Combine(AppContext.BaseDirectory,"session-host-error.txt"),e.ToString());return 1;}
