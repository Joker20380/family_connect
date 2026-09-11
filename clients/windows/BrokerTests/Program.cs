using System.Buffers.Binary;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using FamilyConnect;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.Security;
if(Environment.GetEnvironmentVariable("GITHUB_ACTIONS")!="true"||!new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator))
    throw new Exception("Isolated elevated Windows CI runner required");
var install=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"Family Connect");
var anchor=Path.Combine(install,"activation.pub");var originalAnchor=File.ReadAllBytes(anchor);
var sid=WindowsIdentity.GetCurrent().User!.Value;
var store=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),"FamilyConnect");
var profile=Path.Combine(store,Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(sid)))+".tcp.dpapi");
if(File.Exists(profile))throw new Exception("Refuse existing TCP profile");
var output=Path.GetFullPath(args[0]);
int checks=0;
JsonElement Call(string action,string? activation=null){
 using var timeout=new CancellationTokenSource(TimeSpan.FromSeconds(35));
 using var pipe=new NamedPipeClientStream(".","FamilyConnect.Broker.v1",PipeDirection.InOut,PipeOptions.Asynchronous,TokenImpersonationLevel.Impersonation);
 pipe.ConnectAsync(timeout.Token).GetAwaiter().GetResult();
 var raw=JsonSerializer.SerializeToUtf8Bytes(new{action,activation});byte[] header=new byte[4];BinaryPrimitives.WriteInt32LittleEndian(header,raw.Length);
 pipe.WriteAsync(header,timeout.Token).GetAwaiter().GetResult();pipe.WriteAsync(raw,timeout.Token).GetAwaiter().GetResult();
 pipe.ReadExactlyAsync(header,timeout.Token).GetAwaiter().GetResult();int length=BinaryPrimitives.ReadInt32LittleEndian(header);
 if(length<1||length>16384)throw new Exception("reply size");
 byte[] result=new byte[length];pipe.ReadExactlyAsync(result,timeout.Token).GetAwaiter().GetResult();
 using var document=JsonDocument.Parse(result);return document.RootElement.Clone();
}
void Check(bool passed,string label){if(!passed)throw new Exception(label);checks++;}
try {
 var device=Convert.ToBase64String(Convert.FromHexString(Call("request").GetProperty("code").GetString()![4..]));
 var key=new Ed25519PrivateKeyParameters(new SecureRandom());
 File.WriteAllText(anchor,Convert.ToBase64String(key.GeneratePublicKey().GetEncoded()));
 var grant=new TcpGrant(1,device,10,DateTimeOffset.UtcNow.ToUnixTimeSeconds()+3600,"192.0.2.10",443,
     Guid.NewGuid().ToString(),Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)).TrimEnd('=').Replace('+','-').Replace('/','_'),"example.com","0123456789abcdef");
 string Sign(TcpGrant value){
   var raw=JsonSerializer.SerializeToUtf8Bytes(value,Activation.Json);var signer=new Ed25519Signer();signer.Init(true,key);
   signer.BlockUpdate(TcpProfile.Domain,0,TcpProfile.Domain.Length);signer.BlockUpdate(raw,0,raw.Length);
   return JsonSerializer.Serialize(new Envelope(Convert.ToBase64String(raw),Convert.ToBase64String(signer.GenerateSignature())),Activation.Json);
 }
 Check(Call("activate-tcp",Sign(grant)).GetProperty("ok").GetBoolean(),"broker signed import");
 Check(Call("status").GetProperty("tcpReady").GetBoolean(),"broker profile status");
 var encrypted=File.ReadAllBytes(profile);
 Check(!Encoding.UTF8.GetString(encrypted).Contains(grant.Id),"credential encrypted on disk");
 bool denied=false;try{ProtectedData.Unprotect(encrypted,null,DataProtectionScope.CurrentUser);}catch(CryptographicException){denied=true;}
 Check(denied,"profile bound to LocalSystem DPAPI");
 foreach(var invalid in new[]{grant with{Sequence=9},grant with{ServerName="other.example"},grant with{ExpiresAt=1},
   grant with{DevicePublicKey=Convert.ToBase64String(RandomNumberGenerator.GetBytes(32))},grant with{Server="127.0.0.1"}}){
   Check(!Call("activate-tcp",Sign(invalid)).GetProperty("ok").GetBoolean(),"broker rejects invalid replacement");
   Check(File.ReadAllBytes(profile).SequenceEqual(encrypted),"invalid replacement preserves accepted profile");
 }
 Check(Call("activate-tcp",Sign(grant)).GetProperty("ok").GetBoolean(),"idempotent import");
 Check(Call("activate-tcp",Sign(grant with{Sequence=11})).GetProperty("ok").GetBoolean(),"newer revision import");
 Check(!Call("activate-tcp",Sign(grant)).GetProperty("ok").GetBoolean(),"persisted sequence floor");
 Check(!Call("activate-tcp","{}").GetProperty("ok").GetBoolean(),"malformed import");
 File.WriteAllText(output,$"PASS: {checks} broker TCP import, DPAPI and replacement checks. No tunnel started.\n");
 Console.WriteLine(File.ReadAllText(output));
}catch(Exception e){File.WriteAllText(output,"FAIL after "+checks+" checks: "+e.GetType().Name+": "+e.Message+"\n"+e.StackTrace+"\n");throw;}
finally{File.WriteAllBytes(anchor,originalAnchor);File.Delete(profile);}
