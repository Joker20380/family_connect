using System.Net;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;

namespace FamilyConnect;

public sealed record Grant(int Version, string DevicePublicKey, string GatewayPublicKey,
    string Endpoint, string Address, string Dns, long ExpiresAt);
public sealed record Envelope(string Payload, string Signature);
public static class Activation
{
    public static readonly byte[] Domain = Encoding.UTF8.GetBytes("family-connect/device-activation/v1\0");
    public static readonly JsonSerializerOptions Json = new() { PropertyNamingPolicy=JsonNamingPolicy.CamelCase,
        UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow };
    public static void Key(string value)
    {
        var bytes=Convert.FromBase64String(value);
        if(bytes.Length!=32 || bytes.All(x=>x==0) || Convert.ToBase64String(bytes)!=value) throw new FormatException("key");
    }
    public static Grant Verify(string envelope, byte[] root, string device, long now)
    {
        if(Encoding.UTF8.GetByteCount(envelope)>8192) throw new FormatException("size");
        var e=JsonSerializer.Deserialize<Envelope>(envelope,Json) ?? throw new FormatException("envelope");
        var raw=Convert.FromBase64String(e.Payload); var sig=Convert.FromBase64String(e.Signature);
        var signer=new Ed25519Signer();signer.Init(false,new Ed25519PublicKeyParameters(root,0));
        signer.BlockUpdate(Domain,0,Domain.Length);signer.BlockUpdate(raw,0,raw.Length);
        if(!signer.VerifySignature(sig))throw new FormatException("signature");
        var grant=JsonSerializer.Deserialize<Grant>(raw,Json) ?? throw new FormatException("grant");
        if(grant.Version!=1 || grant.DevicePublicKey!=device || grant.ExpiresAt<=now || grant.ExpiresAt>now+604800)
            throw new FormatException("device or validity");
        Key(device);Key(grant.GatewayPublicKey);
        // Pilot uses a controlled IPv4 gateway and an allocated address in its VPN subnet.
        var ep=grant.Endpoint.Split(':');
        if(ep.Length!=2 || !IPAddress.TryParse(ep[0],out var ip) || ip.AddressFamily!=System.Net.Sockets.AddressFamily.InterNetwork
            || ep[0]!=ip.ToString() || !ushort.TryParse(ep[1],out var port) || port==0)throw new FormatException("endpoint");
        var octets=grant.Address.Split('.');
        if(octets.Length!=4 || string.Join('.',octets.Take(3))!="10.77.0" || !int.TryParse(octets[3],out var n)
            || n<4 || n>254 || grant.Address!=$"10.77.0.{n}")throw new FormatException("address");
        if(!IPAddress.TryParse(grant.Dns,out var dns) || grant.Dns!=dns.ToString())throw new FormatException("dns");
        return grant;
    }
    public static string Config(Grant grant, string privateKey)
    {
        Key(privateKey);
        var number=int.Parse(grant.Address.Split('.')[3]);
        return $"[Interface]\nPrivateKey = {privateKey}\nAddress = {grant.Address}/32, fd77:92::{number:x}/128\nDNS = {grant.Dns}\nMTU = 1380\n\n[Peer]\nPublicKey = {grant.GatewayPublicKey}\nEndpoint = {grant.Endpoint}\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n";
    }
}
