using System.Buffers.Binary;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
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
string friendsPath=Path.Combine(store,Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(sid)))+".friends-identity.dpapi");
string friendsMarker=friendsPath+".initialized";
if(File.Exists(friendsPath)||File.Exists(friendsMarker))throw new Exception("Refuse existing friends identity");
int checks=0;
JsonElement Call(string action,string? activation=null){
 using var timeout=new CancellationTokenSource(TimeSpan.FromSeconds(35));
 using var pipe=new NamedPipeClientStream(".","FamilyConnect.Broker.v1",PipeDirection.InOut,PipeOptions.Asynchronous,TokenImpersonationLevel.Impersonation);
 pipe.ConnectAsync(timeout.Token).GetAwaiter().GetResult();
 var raw=JsonSerializer.SerializeToUtf8Bytes(new{action,activation});byte[] header=new byte[4];BinaryPrimitives.WriteInt32LittleEndian(header,raw.Length);
 pipe.WriteAsync(header,timeout.Token).AsTask().GetAwaiter().GetResult();pipe.WriteAsync(raw,timeout.Token).AsTask().GetAwaiter().GetResult();
 pipe.ReadExactlyAsync(header,timeout.Token).AsTask().GetAwaiter().GetResult();int length=BinaryPrimitives.ReadInt32LittleEndian(header);
 if(length<1||length>16384)throw new Exception("reply size");
 byte[] result=new byte[length];pipe.ReadExactlyAsync(result,timeout.Token).AsTask().GetAwaiter().GetResult();
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
 Check(!Call("friends-identity").GetProperty("ok").GetBoolean(),"resume refuses missing friends identity");
 Check(!File.Exists(friendsPath)&&!File.Exists(friendsMarker),"resume does not create friends state");
 var identityReply=Call("friends-create");Check(identityReply.GetProperty("ok").GetBoolean(),"broker identity create");
 var publicIdentity=identityReply.GetProperty("code").GetString()!;
 using(var identity=JsonDocument.Parse(publicIdentity)) {
   Check(identity.RootElement.EnumerateObject().Count()==4,"only public identity fields leave broker");
   Check(identity.RootElement.GetProperty("wireguard_public_key").GetString()==device,"friends migration preserves existing WG key");
 }
 var identityCipher=File.ReadAllBytes(friendsPath);
 bool identityDenied=false;
 try{ProtectedData.Unprotect(identityCipher,SHA256.HashData(Encoding.UTF8.GetBytes("family-connect/friends-identity/v1\0"+sid)),DataProtectionScope.CurrentUser);}
 catch(CryptographicException){identityDenied=true;}
 Check(identityDenied,"friends identity bound to LocalSystem DPAPI, not UI user");
 using(var broker=new ServiceController("FamilyConnectBroker")) {
   broker.Stop();broker.WaitForStatus(ServiceControllerStatus.Stopped,TimeSpan.FromSeconds(130));
   broker.Start();broker.WaitForStatus(ServiceControllerStatus.Running,TimeSpan.FromSeconds(130));
 }
 Check(Call("friends-identity").GetProperty("code").GetString()==publicIdentity,"broker restart preserves friends identity");
 Check(File.ReadAllBytes(friendsPath).SequenceEqual(identityCipher),"restart leaves encrypted identity unchanged");
 File.WriteAllBytes(friendsPath,new byte[]{1,2,3});
 Check(!Call("friends-create").GetProperty("ok").GetBoolean(),"corrupt identity refuses recreate");
 Check(File.ReadAllBytes(friendsPath).SequenceEqual(new byte[]{1,2,3}),"corrupt identity preserved for recovery");
 File.WriteAllBytes(friendsPath,identityCipher);File.Delete(friendsPath);
 Check(!Call("friends-create").GetProperty("ok").GetBoolean(),"missing marked identity refuses recreate");
 Check(!File.Exists(friendsPath),"missing identity not silently regenerated");
 File.WriteAllBytes(friendsPath,identityCipher);
 Check(Call("friends-identity").GetProperty("code").GetString()==publicIdentity,"restored identity resumes");
 string wgPath=Path.Combine(store,Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(sid)))+".key.dpapi");
 var savedWg=File.ReadAllBytes(wgPath);
 try {
   File.Delete(wgPath);
   Check(!Call("request").GetProperty("ok").GetBoolean(),"legacy request cannot regenerate enrolled WG key");
   Check(!Call("friends-create").GetProperty("ok").GetBoolean(),"friends owner refuses missing WG key");
   Check(!File.Exists(wgPath),"missing WG key remains absent for recovery");
 } finally {File.WriteAllBytes(wgPath,savedWg);}

 Check(!Call("friends-referral","unexpected").GetProperty("ok").GetBoolean(),"referral rejects unsupported input without HTTP");
 Check(!Call("friends-connect-tcp-ru","unexpected").GetProperty("ok").GetBoolean(),"Friends connect rejects unsupported input without HTTP");
 Check(!Call("friends-activate","invalid").GetProperty("ok").GetBoolean(),"invalid invitation fails before HTTP");
 File.WriteAllText(output,$"PASS: {checks} broker TCP and Friends identity/DPAPI/restart/recovery checks. No tunnel started.\n");
 Console.WriteLine(File.ReadAllText(output));
}catch(Exception e){File.WriteAllText(output,"FAIL after "+checks+" checks: "+e.GetType().Name+": "+e.Message+"\n"+e.StackTrace+"\n");throw;}
finally{File.WriteAllBytes(anchor,originalAnchor);File.Delete(profile);File.Delete(friendsPath);File.Delete(friendsMarker);}
