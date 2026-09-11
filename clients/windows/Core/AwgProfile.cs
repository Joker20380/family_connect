using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
namespace FamilyConnect;
public sealed record AwgGrant(int Version,string DevicePublicKey,long Sequence,long ExpiresAt,string GatewayPublicKey,string Server,int Port,int Number,Dictionary<string,string> Parameters);
public static class AwgProfile
{
    public static readonly byte[] Domain=Encoding.UTF8.GetBytes("family-connect/windows-awg-activation/v1\0");
    static readonly string[] Required="Jc Jmin Jmax S1 S2 S3 S4 H1 H2 H3 H4".Split(' ');
    public static AwgGrant Verify(string text,byte[] root,string device,long? now)
    {
        if(Encoding.UTF8.GetByteCount(text)>8192||root.Length!=32)throw new FormatException("size");
        var e=TcpProfile.Parse<Envelope>(text);var raw=Convert.FromBase64String(e.Payload);var sig=Convert.FromBase64String(e.Signature);
        if(sig.Length!=64)throw new FormatException("signature");
        var signer=new Ed25519Signer();signer.Init(false,new Ed25519PublicKeyParameters(root,0));
        signer.BlockUpdate(Domain,0,Domain.Length);signer.BlockUpdate(raw,0,raw.Length);
        if(!signer.VerifySignature(sig))throw new FormatException("signature");
        var p=TcpProfile.Parse<AwgGrant>(new UTF8Encoding(false,true).GetString(raw));Validate(p);
        if(p.DevicePublicKey!=device||(now is long n&&(p.ExpiresAt<=n||p.ExpiresAt-n>604800)))throw new FormatException("device or expiry");
        return p;
    }
    public static void Validate(AwgGrant p)
    {
        if(p.Version!=1||p.Sequence<1||p.Sequence>9007199254740991||p.ExpiresAt<1||p.ExpiresAt>253402300799||p.Number<4||p.Number>254||p.Port<1||p.Port>65535)throw new FormatException("profile");
        if(p.DevicePublicKey is null||p.GatewayPublicKey is null||p.Server is null)throw new FormatException("missing field");
        Activation.Key(p.DevicePublicKey);Activation.Key(p.GatewayPublicKey);
        if(!IPAddress.TryParse(p.Server,out var ip)||ip.AddressFamily!=AddressFamily.InterNetwork||ip.ToString()!=p.Server||IPAddress.IsLoopback(ip)||ip.GetAddressBytes()[0] is 0 or >=224)throw new FormatException("endpoint");
        var v=p.Parameters;if(v is null||Required.Any(k=>!v.ContainsKey(k))||v.Any(k=>!Required.Contains(k.Key)&&!Regex.IsMatch(k.Key,@"\AI[1-5]\z")))throw new FormatException("parameters");
        foreach(var name in Required.Take(7)){
            int min=name is "Jc" or "Jmin" or "Jmax"?1:0,max=name=="Jc"?12:name.StartsWith('J')?1280:256;
            if(!Regex.IsMatch(v[name]??"",@"\A[0-9]{1,5}\z")||!int.TryParse(v[name],out var value)||value<min||value>max)throw new FormatException("padding");
        }
        if(int.Parse(v["Jmin"])>int.Parse(v["Jmax"]))throw new FormatException("junk range");
        var ranges=new List<(uint Low,uint High)>();
        foreach(var name in Required.Skip(7)){
            if(!Regex.IsMatch(v[name]??"",@"\A[0-9]{1,10}(?:-[0-9]{1,10})?\z"))throw new FormatException("header");
            var bits=v[name].Split('-');if(!uint.TryParse(bits[0],out var low)||!uint.TryParse(bits[^1],out var high)||low<5||low>high||ranges.Any(r=>low<=r.High&&r.Low<=high))throw new FormatException("header range");
            ranges.Add((low,high));
        }
        foreach(var (name,value) in v.Where(x=>x.Key.StartsWith('I'))){
            if(value is null||value.Length>4096)throw new FormatException("signature packet");
            int pos=0,size=0;
            foreach(Match match in Regex.Matches(value,@"<(?:b 0x([0-9a-fA-F]+)|(r|rd|rc) ([0-9]{1,4})|(t))>")){
                if(match.Index!=pos)throw new FormatException("packet grammar");
                if(match.Groups[1].Success){if(match.Groups[1].Length%2!=0)throw new FormatException("hex");size+=match.Groups[1].Length/2;}
                else size+=match.Groups[2].Success?int.Parse(match.Groups[3].Value):4;
                pos+=match.Length;
            }
            if(pos!=value.Length||size<1||size>1280)throw new FormatException("packet size");
        }
    }
    static string Canonical(AwgGrant p)=>JsonSerializer.Serialize(p with{Parameters=p.Parameters.OrderBy(x=>x.Key,StringComparer.Ordinal).ToDictionary(x=>x.Key,x=>x.Value)},Activation.Json);
    public static void CheckReplacement(AwgGrant next,AwgGrant? previous)
    {
        if(previous is not null&&(next.Sequence<previous.Sequence||(next.Sequence==previous.Sequence&&Canonical(next)!=Canonical(previous))))throw new FormatException("rollback");
    }
    public static string Config(AwgGrant p,string key,string adapter,string uplink)
    {
        Validate(p);Activation.Key(key);
        if(!Regex.IsMatch(adapter,@"\Afcawg[0-9a-f]{8}\z"))throw new FormatException("adapter");
        var config=new StringBuilder("private_key="+Convert.ToHexString(Convert.FromBase64String(key)).ToLowerInvariant()+"\n");
        foreach(var item in p.Parameters.OrderBy(x=>x.Key,StringComparer.Ordinal))config.Append(item.Key.ToLowerInvariant()).Append('=').Append(item.Value).Append('\n');
#if TCP_SESSION_TEST
        const string server="127.0.0.1";
#else
        string server=p.Server;
#endif
        config.Append("public_key=").Append(Convert.ToHexString(Convert.FromBase64String(p.GatewayPublicKey)).ToLowerInvariant()).Append("\nendpoint=").Append(server).Append(':').Append(p.Port).Append("\nallowed_ip=0.0.0.0/0\nallowed_ip=::/0\npersistent_keepalive_interval=25\n\n");
        return JsonSerializer.Serialize(new{adapter,uplink,config=config.ToString()});
    }
}
