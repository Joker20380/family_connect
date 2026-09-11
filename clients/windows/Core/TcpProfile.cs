using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
namespace FamilyConnect;

public sealed record TcpGrant(int Version, string DevicePublicKey, long Sequence, long ExpiresAt,
    string Server, int Port, string Id, string PublicKey, string ServerName, string ShortId);

public static class TcpProfile
{
    public static readonly byte[] Domain=Encoding.UTF8.GetBytes("family-connect/windows-tcp-activation/v1\0");
    static readonly Regex Host=new(@"\A(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\z",RegexOptions.CultureInvariant);
    static void Unique(JsonElement element)
    {
        if(element.ValueKind==JsonValueKind.Object){
            var seen=new HashSet<string>(StringComparer.Ordinal);
            foreach(var item in element.EnumerateObject()){
                if(!seen.Add(item.Name))throw new FormatException("duplicate field");
                Unique(item.Value);
            }
        }else if(element.ValueKind==JsonValueKind.Array)foreach(var item in element.EnumerateArray())Unique(item);
    }
    internal static T Parse<T>(string text)
    {
        using var document=JsonDocument.Parse(text,new JsonDocumentOptions{MaxDepth=8});
        Unique(document.RootElement);
        return JsonSerializer.Deserialize<T>(text,Activation.Json)??throw new FormatException("missing profile");
    }
    public static TcpGrant Verify(string text,byte[] root,string device,long? importTime)
    {
        if(text.Length>8192||Encoding.UTF8.GetByteCount(text)>8192)throw new FormatException("size");
        var envelope=Parse<Envelope>(text);
        if(envelope.Payload is null||envelope.Signature is null)throw new FormatException("envelope");
        var raw=Convert.FromBase64String(envelope.Payload);var signature=Convert.FromBase64String(envelope.Signature);
        if(root.Length!=32||signature.Length!=64)throw new FormatException("signature");
        var signer=new Ed25519Signer();signer.Init(false,new Ed25519PublicKeyParameters(root,0));
        signer.BlockUpdate(Domain,0,Domain.Length);signer.BlockUpdate(raw,0,raw.Length);
        if(!signer.VerifySignature(signature))throw new FormatException("signature");
        var grant=Parse<TcpGrant>(new UTF8Encoding(false,true).GetString(raw));
        Validate(grant);
        Activation.Key(device);
        if(grant.DevicePublicKey!=device)throw new FormatException("device");
        // Expiry is an import deadline. An accepted stored profile remains usable offline.
        if(importTime is long now&&(grant.ExpiresAt<=now||grant.ExpiresAt-now>604800))throw new FormatException("expiry");
        return grant;
    }
    public static void Validate(TcpGrant p)
    {
        if(p.Version!=1||p.Sequence<1||p.Sequence>9007199254740991||p.ExpiresAt<1||p.ExpiresAt>253402300799)
            throw new FormatException("version or sequence");
        if(p.DevicePublicKey is null||p.Server is null||p.Id is null||p.PublicKey is null||p.ServerName is null||p.ShortId is null)
            throw new FormatException("missing field");
        Activation.Key(p.DevicePublicKey);
        if(!IPAddress.TryParse(p.Server,out var ip)||ip.AddressFamily!=AddressFamily.InterNetwork||ip.ToString()!=p.Server
            ||IPAddress.IsLoopback(ip)||ip.GetAddressBytes()[0] is 0 or >=224||p.Port<1||p.Port>65535)
            throw new FormatException("endpoint");
        if(!Guid.TryParseExact(p.Id,"D",out var id)||id==Guid.Empty||id.ToString("D")!=p.Id)throw new FormatException("identity");
        if(!Regex.IsMatch(p.PublicKey,@"\A[A-Za-z0-9_-]{43}\z"))throw new FormatException("key");
        var key=Convert.FromBase64String(p.PublicKey.Replace('-','+').Replace('_','/')+"=");
        if(key.All(b=>b==0)||Convert.ToBase64String(key).TrimEnd('=').Replace('+','-').Replace('/','_')!=p.PublicKey)
            throw new FormatException("key");
        if(p.ServerName.Length>253||!Host.IsMatch(p.ServerName)||!Regex.IsMatch(p.ShortId,@"\A(?:[0-9a-f]{2}){1,8}\z"))
            throw new FormatException("reality");
    }
    public static void CheckReplacement(TcpGrant next,TcpGrant? previous)
    {
        if(previous is not null&&(next.Sequence<previous.Sequence||(next.Sequence==previous.Sequence&&next!=previous)))
            throw new FormatException("profile rollback");
    }
    public static string Config(TcpGrant p,string adapter,string? uplink=null)
    {
        Validate(p);
        if(!Regex.IsMatch(adapter,@"\Afctcp[0-9a-f]{8}\z"))throw new FormatException("adapter");
        return JsonSerializer.Serialize(new {
            log=new {loglevel="none"},
            inbounds=new[]{new {tag="tun",protocol="tun",settings=new {name=adapter,MTU=1280}}},
            outbounds=new[]{new {tag="vpn",protocol="vless",settings=new {vnext=new[]{new {
                address=p.Server,port=p.Port,users=new[]{new {id=p.Id,encryption="none",flow="xtls-rprx-vision"}}
            }}},streamSettings=new {network="raw",security="reality",sockopt=new {@interface=uplink??""},realitySettings=new {
                fingerprint="chrome",serverName=p.ServerName,password=p.PublicKey,shortId=p.ShortId
            }}}}
        });
    }
}
