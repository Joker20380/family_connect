using System.Text.Json;
using FamilyConnect;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.Security;
if(args.Length==3&&args[0]=="--public-windows-update"){
 var anchor=Convert.FromBase64String(File.ReadAllText(args[1]).Trim());
 var offered=await Updates.Check("0.2.12",anchor,args[2]);
 if(offered?.Version!="0.2.13")throw new Exception("Published Windows update not offered");
 if(await Updates.Check("0.2.13",anchor,args[2]) is not null)throw new Exception("Installed Windows version offered again");
 Console.WriteLine($"Public Windows update accepted: {offered.Version}, sequence {offered.Sequence}; installed version correctly current");return;
}
var key=new Ed25519PrivateKeyParameters(new SecureRandom());
var root=key.GeneratePublicKey().GetEncoded();
var device=Convert.ToBase64String(new X25519PrivateKeyParameters(new SecureRandom()).GeneratePublicKey().GetEncoded());
var gateway=Convert.ToBase64String(new X25519PrivateKeyParameters(new SecureRandom()).GeneratePublicKey().GetEncoded());
var now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
var grant=new Grant(1,device,gateway,"185.251.89.19:51820","10.77.0.4","1.1.1.1",now+3600);
string Sign(Grant value){
 var raw=JsonSerializer.SerializeToUtf8Bytes(value,Activation.Json);var s=new Ed25519Signer();s.Init(true,key);
 s.BlockUpdate(Activation.Domain,0,Activation.Domain.Length);s.BlockUpdate(raw,0,raw.Length);
 return JsonSerializer.Serialize(new Envelope(Convert.ToBase64String(raw),Convert.ToBase64String(s.GenerateSignature())),Activation.Json);
}
void Reject(string value,string who,long clock){try{Activation.Verify(value,root,who,clock);}catch(Exception){return;}throw new Exception("accepted invalid activation");}
var envelope=Sign(grant);
if(Activation.Verify(envelope,root,device,now)!=grant)throw new Exception("round trip");
Reject(envelope,gateway,now);Reject(envelope,device,now+3600);
Reject(Sign(grant with{Endpoint="example.com:443"}),device,now);
Reject(Sign(grant with{Dns="1.1.1.1\nPostUp=evil"}),device,now);
Reject(Sign(grant with{Address="10.77.0.3"}),device,now);
Reject(Sign(grant with{ExpiresAt=now+604801}),device,now);
var parsed=JsonSerializer.Deserialize<Envelope>(envelope,Activation.Json)!;
var bad=Convert.FromBase64String(parsed.Signature);bad[0]^=1;
Reject(JsonSerializer.Serialize(parsed with{Signature=Convert.ToBase64String(bad)},Activation.Json),device,now);
Reject(new string('a',8193),device,now);
Console.WriteLine("9 activation checks passed.");
var updateRoot=Path.Combine(AppContext.BaseDirectory,"fixtures");
var updateRaw=File.ReadAllBytes(Path.Combine(updateRoot,"update-v1.json"));
var updatePublic=Convert.FromBase64String(File.ReadAllText(Path.Combine(updateRoot,"update-v1.pub")).Trim());
if(Updates.Verify(updateRaw,updatePublic,1000).Update.Version!="0.2.2")throw new Exception("update interoperability");
void RejectUpdate(byte[] raw,byte[] anchor,long clock){try{Updates.Verify(raw,anchor,clock);}catch(Exception){return;}throw new Exception("accepted invalid update");}
RejectUpdate(updateRaw,root,1000);RejectUpdate(updateRaw,updatePublic,2000);RejectUpdate(updateRaw,updatePublic,998);
RejectUpdate(new byte[65537],updatePublic,1000);
var changed=updateRaw.ToArray();changed[changed.Length/2]^=1;RejectUpdate(changed,updatePublic,1000);
Console.WriteLine("6 update catalog checks passed, including shared Python fixture.");

var winFixture=File.ReadAllBytes(Path.Combine(updateRoot,"windows-update-v2.json"));
var winAnchor=Convert.FromBase64String(File.ReadAllText(Path.Combine(updateRoot,"windows-update-v2.pub")).Trim());
if(Updates.VerifyWindows(winFixture,winAnchor,1000).Update.Version!="0.2.13")throw new Exception("Windows Python fixture mismatch");
var winText=System.Text.Encoding.UTF8.GetString(Convert.FromBase64String(JsonDocument.Parse(winFixture).RootElement.GetProperty("payload").GetString()!));
byte[] SignWindowsUpdate(string text,string domain="family-connect/app-update/v2\0"){
 var bytes=System.Text.Encoding.UTF8.GetBytes(text);var prefix=System.Text.Encoding.UTF8.GetBytes(domain);
 var signer=new Ed25519Signer();signer.Init(true,key);signer.BlockUpdate(prefix,0,prefix.Length);signer.BlockUpdate(bytes,0,bytes.Length);
 return JsonSerializer.SerializeToUtf8Bytes(new{payload=Convert.ToBase64String(bytes),signature=Convert.ToBase64String(signer.GenerateSignature())});
}
int winChecks=0;
void RejectWindowsUpdate(Action action){try{action();}catch{winChecks++;return;}throw new Exception("Accepted invalid Windows update");}
foreach(var text in new[]{winText.Replace("\"platform\":\"windows\"","\"platform\":\"linux\""),winText.Replace("\"schema\":2","\"schema\":1"),winText.Replace("\"sequence\":9","\"sequence\":0"),winText.Replace("windows-v0.2.13","v0.2.13"),winText.Replace("https://github.com/","https://example.com/"),winText.Replace("\"size\":123","\"size\":0"),winText.Replace("\"size\":123","\"size\":536870913"),winText.Replace("\"sequence\":9","\"sequence\":9,\"sequence\":9"),winText.Replace("\"schema\":2","\"schema\":2,\"command\":\"bad\""),winText.Replace(new string('a',64),new string('A',64))})
 RejectWindowsUpdate(()=>Updates.VerifyWindows(SignWindowsUpdate(text),root,1000));
RejectWindowsUpdate(()=>Updates.VerifyWindows(SignWindowsUpdate(winText,"family-connect/app-update/v1\0"),root,1000));
RejectWindowsUpdate(()=>Updates.VerifyWindows(winFixture,winAnchor,2000));
RejectWindowsUpdate(()=>Updates.VerifyWindows(winFixture,winAnchor,998));
RejectWindowsUpdate(()=>Updates.VerifyWindows(winFixture,root,1000));
RejectWindowsUpdate(()=>Updates.VerifyWindows(updateRaw,updatePublic,1000));
var winAltered=winFixture.ToArray();winAltered[winAltered.Length/2]^=1;RejectWindowsUpdate(()=>Updates.VerifyWindows(winAltered,winAnchor,1000));
string updateStore=Path.Combine(Path.GetTempPath(),"fc-windows-update-test-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(updateStore);
try{
 File.WriteAllText(Path.Combine(updateStore,"state.json"),JsonSerializer.Serialize(new{sequence=8,digest="legacy",last_now=999}));
 var signedWin=SignWindowsUpdate(winText);
 if(Updates.Accept(signedWin,root,"0.2.12",1000,updateStore)?.Version!="0.2.13")throw new Exception("Windows update not offered");
 if(Updates.Accept(signedWin,root,"0.2.13",1000,updateStore)!=null||Updates.Accept(signedWin,root,"0.2.14",1000,updateStore)!=null)throw new Exception("Equal or older Windows version offered");
 var before=File.ReadAllBytes(Path.Combine(updateStore,"state.json"));
 RejectWindowsUpdate(()=>Updates.Accept(SignWindowsUpdate(winText.Replace("\"sequence\":9","\"sequence\":8")),root,"0.2.12",1000,updateStore));
 RejectWindowsUpdate(()=>Updates.Accept(SignWindowsUpdate(winText.Replace("\"size\":123","\"size\":124")),root,"0.2.12",1000,updateStore));
 RejectWindowsUpdate(()=>Updates.Accept(signedWin,root,"0.2.12",999,updateStore));
 if(!before.SequenceEqual(File.ReadAllBytes(Path.Combine(updateStore,"state.json"))))throw new Exception("Refused catalog changed floor");
}finally{Directory.Delete(updateStore,true);}
Console.WriteLine($"Windows independent update channel: Python fixture, legacy floor migration, version offers and {winChecks} rejection checks passed.");


var tcp=new TcpGrant(1,device,1,now+3600,"192.0.2.10",443,"11111111-2222-4333-8444-555555555555",
    Convert.ToBase64String(Enumerable.Range(1,32).Select(x=>(byte)x).ToArray()).TrimEnd('=').Replace('+','-').Replace('/','_'),"example.com","0123456789abcdef");
string SignTcpRaw(string text,byte[]? domain=null){
 var raw=System.Text.Encoding.UTF8.GetBytes(text);var signer=new Ed25519Signer();signer.Init(true,key);
 var prefix=domain??TcpProfile.Domain;signer.BlockUpdate(prefix,0,prefix.Length);signer.BlockUpdate(raw,0,raw.Length);
 return JsonSerializer.Serialize(new Envelope(Convert.ToBase64String(raw),Convert.ToBase64String(signer.GenerateSignature())),Activation.Json);
}
string SignTcp(TcpGrant value)=>SignTcpRaw(JsonSerializer.Serialize(value,Activation.Json));
int tcpChecks=0;
void RejectTcp(Action action){try{action();}catch(Exception){tcpChecks++;return;}throw new Exception("accepted invalid TCP profile");}
var tcpEnvelope=SignTcp(tcp);
if(TcpProfile.Verify(tcpEnvelope,root,device,now)!=tcp)throw new Exception("TCP round trip");
RejectTcp(()=>TcpProfile.Verify(tcpEnvelope,root,gateway,now));
RejectTcp(()=>TcpProfile.Verify(tcpEnvelope,root,device,now+3600));
RejectTcp(()=>TcpProfile.Verify(SignTcp(tcp with{ExpiresAt=now+604801}),root,device,now));
if(TcpProfile.Verify(tcpEnvelope,root,device,null)!=tcp)throw new Exception("Stored offline profile");
foreach(var invalid in new[]{tcp with{Version=2},tcp with{Sequence=0},tcp with{Sequence=9007199254740992},
 tcp with{Server="127.0.0.1"},tcp with{Server="224.0.0.1"},tcp with{Server="192.0.2.10; bad"},tcp with{Server="example.com"},
 tcp with{Port=0},tcp with{Port=65536},tcp with{Id=Guid.Empty.ToString()},tcp with{PublicKey=new string('A',43)},
 tcp with{PublicKey=tcp.PublicKey+"="},tcp with{ServerName="example.com\nInjected=1"},tcp with{ShortId="0"},
 tcp with{DevicePublicKey=null!},tcp with{PublicKey=null!},tcp with{ShortId=null!}})
 RejectTcp(()=>TcpProfile.Verify(SignTcp(invalid),root,device,now));
RejectTcp(()=>TcpProfile.Verify(SignTcpRaw(JsonSerializer.Serialize(tcp,Activation.Json),Activation.Domain),root,device,now));
var tcpRaw=JsonSerializer.Serialize(tcp,Activation.Json);
RejectTcp(()=>TcpProfile.Verify(SignTcpRaw(tcpRaw.Replace("\"version\":1","\"version\":1,\"version\":1")),root,device,now));
RejectTcp(()=>TcpProfile.Verify(SignTcpRaw(tcpRaw.TrimEnd('}')+",\"command\":\"bad\"}"),root,device,now));
RejectTcp(()=>TcpProfile.Verify(tcpEnvelope.Replace("\"payload\":","\"payload\":\"\",\"payload\":"),root,device,now));
RejectTcp(()=>TcpProfile.Verify(new string('a',8193),root,device,now));
var altered=JsonSerializer.Deserialize<Envelope>(tcpEnvelope,Activation.Json)!;
var signature=Convert.FromBase64String(altered.Signature);signature[0]^=1;
RejectTcp(()=>TcpProfile.Verify(JsonSerializer.Serialize(altered with{Signature=Convert.ToBase64String(signature)},Activation.Json),root,device,now));
TcpProfile.CheckReplacement(tcp,tcp);TcpProfile.CheckReplacement(tcp with{Sequence=2},tcp);
RejectTcp(()=>TcpProfile.CheckReplacement(tcp,tcp with{Sequence=2}));
RejectTcp(()=>TcpProfile.CheckReplacement(tcp with{ServerName="other.example"},tcp));
RejectTcp(()=>TcpProfile.Config(tcp,"Ethernet"));
using(var config=JsonDocument.Parse(TcpProfile.Config(tcp,"fctcp1234abcd"))){
 var outbound=config.RootElement.GetProperty("outbounds")[0];
 if(outbound.GetProperty("streamSettings").GetProperty("security").GetString()!="reality"||
    config.RootElement.GetProperty("inbounds")[0].GetProperty("protocol").GetString()!="tun")throw new Exception("TCP config");
}
var fixtureEnvelope=File.ReadAllText(Path.Combine(updateRoot,"windows-tcp-v1.json"));
var fixtureRoot=Convert.FromBase64String(File.ReadAllText(Path.Combine(updateRoot,"windows-tcp-v1.pub")).Trim());
var fixtureDevice=Convert.ToBase64String(Enumerable.Range(1,32).Select(x=>(byte)x).ToArray());
if(TcpProfile.Verify(fixtureEnvelope,fixtureRoot,fixtureDevice,1000).Sequence!=7)throw new Exception("Python TCP interoperability");
Console.WriteLine($"TCP profile interoperability, config, replacement and {tcpChecks} rejection checks passed.");

using(var config=JsonDocument.Parse(TcpProfile.Config(tcp,"fctcp1234abcd","Ethernet \"uplink\""))){
 if(config.RootElement.GetProperty("outbounds")[0].GetProperty("streamSettings").GetProperty("sockopt").GetProperty("interface").GetString()!="Ethernet \"uplink\"")throw new Exception("uplink serialization");
}
Console.WriteLine("TCP uplink binding serialization passed.");

var awgRoot=Convert.FromBase64String(File.ReadAllText(Path.Combine(updateRoot,"windows-awg-v1.pub")).Trim());
var awgDevice=Convert.ToBase64String(Enumerable.Range(1,32).Select(x=>(byte)x).ToArray());
var awgText=File.ReadAllText(Path.Combine(updateRoot,"windows-awg-v1.json"));
var awg=AwgProfile.Verify(awgText,awgRoot,awgDevice,1000);
if(awg.Number!=4||awg.Sequence!=7)throw new Exception("AWG Python fixture mismatch");
var testAwgKey=new Ed25519PrivateKeyParameters(Enumerable.Range(0,32).Select(x=>(byte)x).ToArray(),0);
string SignAwg(AwgGrant value){
 var raw=JsonSerializer.SerializeToUtf8Bytes(value,Activation.Json);var signer=new Ed25519Signer();signer.Init(true,testAwgKey);signer.BlockUpdate(AwgProfile.Domain,0,AwgProfile.Domain.Length);signer.BlockUpdate(raw,0,raw.Length);
 return JsonSerializer.Serialize(new Envelope(Convert.ToBase64String(raw),Convert.ToBase64String(signer.GenerateSignature())),Activation.Json);
}
void AwgReject(Action action){try{action();}catch(Exception){return;}throw new Exception("Invalid AWG profile accepted");}
AwgReject(()=>AwgProfile.Verify(awgText,awgRoot,gateway,1000));AwgReject(()=>AwgProfile.Verify(awgText,awgRoot,awgDevice,90000));
AwgReject(()=>AwgProfile.Verify(awgText,root,awgDevice,1000));
foreach(var invalid in new[]{awg with{Number=3},awg with{Port=0},awg with{Server="127.0.0.1"},awg with{Sequence=0}})AwgReject(()=>AwgProfile.Verify(SignAwg(invalid),awgRoot,awgDevice,1000));
foreach(var (name,value) in new[]{("Jc","0"),("Jmax","10"),("H1","2005"),("H1","4294967296"),("I1","<r 1281>"),("I1","<b 0x1>"),("I1","bad\nprivate_key=evil")}){
 var parameters=new Dictionary<string,string>(awg.Parameters){[name]=value};AwgReject(()=>AwgProfile.Verify(SignAwg(awg with{Parameters=parameters}),awgRoot,awgDevice,1000));
}
AwgProfile.CheckReplacement(awg with{Parameters=awg.Parameters.Reverse().ToDictionary(x=>x.Key,x=>x.Value)},awg);
AwgReject(()=>AwgProfile.CheckReplacement(awg with{Sequence=6},awg));AwgReject(()=>AwgProfile.CheckReplacement(awg with{Number=5},awg));
AwgProfile.Verify(awgText,awgRoot,awgDevice,null);
var awgConfig=AwgProfile.Config(awg,Convert.ToBase64String(Enumerable.Range(1,32).Select(x=>(byte)x).ToArray()),"fcawg12345678","Wi-Fi");
using(var doc=JsonDocument.Parse(awgConfig)){if(!doc.RootElement.GetProperty("config").GetString()!.Contains("h1=1001-1010\n"))throw new Exception("AWG UAPI config mismatch");}
Console.WriteLine("AWG shared fixture, 16 rejection cases, replacement ordering and UAPI config passed.");

// Policy tests execute the real async sequencing with controlled transport lifetimes.
async Task SequenceCase(string mode){
 var log=new List<string>();using var stop=new CancellationTokenSource();
 var choices=mode=="skip"?new[]{"tcp"}:new[]{"wg","awg","tcp"};
 if(mode=="cancel-before")stop.Cancel();
 try{
  await TransportSequence.Run(choices,(name,connected,ct)=>{
   log.Add("start:"+name);
   if(mode=="cancel-start"){stop.Cancel();ct.ThrowIfCancellationRequested();}
   if(mode=="established"||mode=="cancel-established"){connected();log.Add("on:"+name);}
   if(mode=="cancel-established"){stop.Cancel();ct.ThrowIfCancellationRequested();}
   throw new IOException("synthetic transport unavailable");
  },name=>{log.Add("clean:"+name);if(mode=="cleanup-failure")throw new IOException("synthetic cleanup failure");return Task.CompletedTask;},(_,_)=>{},stop.Token);
  if(mode.StartsWith("cancel")||mode=="cleanup-failure")throw new Exception("Expected terminal policy outcome missing");
 }catch(OperationCanceledException) when(stop.IsCancellationRequested){}
 catch(TransportSequence.CleanupException) when(mode=="cleanup-failure"){}
 var expected=mode=="cancel-before"?Array.Empty<string>():mode=="cleanup-failure"||mode=="cancel-start"?new[]{"start:wg","clean:wg"}:mode=="cancel-established"?new[]{"start:wg","on:wg","clean:wg"}:choices.SelectMany(n=>mode=="established"?new[]{"start:"+n,"on:"+n,"clean:"+n}:new[]{"start:"+n,"clean:"+n}).ToArray();
 if(!log.SequenceEqual(expected))throw new Exception("Transport policy order/cancellation/cleanup: "+mode);
}
foreach(var mode in new[]{"failure","skip","established","cancel-before","cancel-start","cancel-established","cleanup-failure"})await SequenceCase(mode);
Console.WriteLine("7 automatic transport policy order, cancellation, cleanup and exhaustion scenarios passed.");

ControlVectors.Run();

FriendsIdentityChecks.Run();

await FriendsAccessChecks.Run();

FriendsVaultChecks.Run();
FriendsCatalogChecks.Run();
FriendsConfigurationVaultChecks.Run();
