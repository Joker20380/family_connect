using System.Text.Json;
using FamilyConnect;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.Security;
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
