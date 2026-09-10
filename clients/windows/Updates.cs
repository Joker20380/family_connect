using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
namespace FamilyConnect;
internal sealed record AppUpdate(string Version,long Sequence,long ExpiresAt,string Url,string Sha256,long Size);
internal static class Updates
{
    const string Catalog="https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/pilot.json";
    static readonly byte[] Domain=Encoding.UTF8.GetBytes("family-connect/app-update/v1\0");
    static readonly HttpClient Http=new(){Timeout=TimeSpan.FromSeconds(60)};
    static string Store=>Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"FamilyConnect","updates");
    static void Fields(JsonElement value,params string[] names){
        if(value.ValueKind!=JsonValueKind.Object||!value.EnumerateObject().Select(p=>p.Name).Order().SequenceEqual(names.Order()))throw new InvalidDataException("Invalid update fields");
    }
    static void Unique(JsonElement value){
        if(value.ValueKind==JsonValueKind.Object){var seen=new HashSet<string>();foreach(var property in value.EnumerateObject()){if(!seen.Add(property.Name))throw new InvalidDataException();Unique(property.Value);}}
        if(value.ValueKind==JsonValueKind.Array)foreach(var child in value.EnumerateArray())Unique(child);
    }
    static Version ParseVersion(string value){
        if(!System.Text.RegularExpressions.Regex.IsMatch(value,@"\A(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\z"))throw new InvalidDataException();
        return Version.Parse(value);
    }
    internal static (AppUpdate Update,string Digest) Verify(byte[] raw,byte[] publicKey,long now){
        if(raw.Length>65536||publicKey.Length!=32)throw new InvalidDataException();
        using var outer=JsonDocument.Parse(raw);Unique(outer.RootElement);Fields(outer.RootElement,"payload","signature");
        byte[] payload=Convert.FromBase64String(outer.RootElement.GetProperty("payload").GetString()!);
        byte[] signature=Convert.FromBase64String(outer.RootElement.GetProperty("signature").GetString()!);
        var verifier=new Ed25519Signer();verifier.Init(false,new Ed25519PublicKeyParameters(publicKey,0));
        verifier.BlockUpdate(Domain,0,Domain.Length);verifier.BlockUpdate(payload,0,payload.Length);
        if(!verifier.VerifySignature(signature))throw new InvalidDataException("Untrusted update");
        using var document=JsonDocument.Parse(payload);var data=document.RootElement;Unique(data);
        Fields(data,"schema","sequence","version","issued_at","expires_at","artifacts");
        long sequence=data.GetProperty("sequence").GetInt64(),issued=data.GetProperty("issued_at").GetInt64(),expires=data.GetProperty("expires_at").GetInt64();
        string version=data.GetProperty("version").GetString()!;ParseVersion(version);
        if(data.GetProperty("schema").GetInt32()!=1||sequence<1||issued<1||issued>now||expires<=now||expires-issued<=0||expires-issued>90*86400)throw new InvalidDataException("Expired update");
        var artifacts=data.GetProperty("artifacts");Fields(artifacts,"linux","windows");
        AppUpdate? update=null;
        foreach(string platform in new[]{"linux","windows"}){
            var artifact=artifacts.GetProperty(platform);Fields(artifact,"url","sha256","size");
            string name=platform=="linux"?$"FamilyConnect-Linux-{version}.tar.gz":$"FamilyConnect-Setup-{version}-pilot-unsigned.exe";
            string url=artifact.GetProperty("url").GetString()!,sha=artifact.GetProperty("sha256").GetString()!;
            long size=artifact.GetProperty("size").GetInt64();
            if(url!=$"https://github.com/Joker20380/family_connect/releases/download/v{version}/{name}"||!System.Text.RegularExpressions.Regex.IsMatch(sha,@"\A[0-9a-f]{64}\z")||size<1||size>512*1024*1024)throw new InvalidDataException();
            if(platform=="windows")update=new(version,sequence,expires,url,sha,size);
        }
        return (update!,Convert.ToHexString(SHA256.HashData(payload)));
    }
    static void SafePath(string path){if((File.Exists(path)||Directory.Exists(path))&&File.GetAttributes(path).HasFlag(FileAttributes.ReparsePoint))throw new InvalidDataException("Unsafe update storage");}
    public static async Task<AppUpdate?> Check(string currentVersion){
        using var response=await Http.GetAsync(Catalog,HttpCompletionOption.ResponseHeadersRead);response.EnsureSuccessStatusCode();
        using var input=await response.Content.ReadAsStreamAsync();using var output=new MemoryStream();
        byte[] buffer=new byte[8192];int count;
        while((count=await input.ReadAsync(buffer.AsMemory()).AsTask().WaitAsync(TimeSpan.FromSeconds(30)))>0){if(output.Length+count>65536)throw new InvalidDataException();output.Write(buffer,0,count);}
        long now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        var (update,digest)=Verify(output.ToArray(),Convert.FromBase64String(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"update.pub")).Trim()),now);
        Directory.CreateDirectory(Store);SafePath(Store);
        string path=Path.Combine(Store,"state.json"),lockPath=Path.Combine(Store,"lock");SafePath(path);SafePath(lockPath);
        using var gate=new FileStream(lockPath,FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None);
        if(File.Exists(path)){
            using var previous=JsonDocument.Parse(File.ReadAllBytes(path));var state=previous.RootElement;Unique(state);Fields(state,"sequence","digest","last_now");
            long floor=state.GetProperty("sequence").GetInt64();
            if(floor<1||update.Sequence<floor||now<state.GetProperty("last_now").GetInt64()||(update.Sequence==floor&&digest!=state.GetProperty("digest").GetString()))throw new InvalidDataException("Update rollback");
        }
        string temp=Path.Combine(Store,Guid.NewGuid()+".json");
        byte[] stateBytes=JsonSerializer.SerializeToUtf8Bytes(new{sequence=update.Sequence,digest,last_now=now});
        using(var stream=new FileStream(temp,FileMode.CreateNew,FileAccess.Write,FileShare.None)){stream.Write(stateBytes);stream.Flush(true);}
        File.Move(temp,path,true);
        return ParseVersion(update.Version)>ParseVersion(currentVersion)?update:null;
    }
    public static async Task<string> Download(AppUpdate update){
        if(DateTimeOffset.UtcNow.ToUnixTimeSeconds()>=update.ExpiresAt)throw new InvalidDataException("Expired update");
        Directory.CreateDirectory(Store);SafePath(Store);string path=Path.Combine(Store,Guid.NewGuid()+".exe");
        try{
            using var response=await Http.GetAsync(update.Url,HttpCompletionOption.ResponseHeadersRead);response.EnsureSuccessStatusCode();
            if(response.RequestMessage!.RequestUri!.Scheme!="https")throw new InvalidDataException();
            using var input=await response.Content.ReadAsStreamAsync();
            using(var output=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None)){
                using var hash=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);byte[] buffer=new byte[65536];long total=0;int count;
                while((count=await input.ReadAsync(buffer.AsMemory()).AsTask().WaitAsync(TimeSpan.FromSeconds(30)))>0){total+=count;if(total>update.Size)throw new InvalidDataException();hash.AppendData(buffer,0,count);await output.WriteAsync(buffer.AsMemory(0,count));}
                output.Flush(true);
                if(total!=update.Size||!Convert.ToHexString(hash.GetHashAndReset()).Equals(update.Sha256,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Update checksum mismatch");
            }
            return path;
        }catch{File.Delete(path);throw;}
    }
    public static void LaunchInstaller(string path,AppUpdate update){
        SafePath(path);using(var input=File.OpenRead(path)){
            if(input.Length!=update.Size||!Convert.ToHexString(SHA256.HashData(input)).Equals(update.Sha256,StringComparison.OrdinalIgnoreCase)||DateTimeOffset.UtcNow.ToUnixTimeSeconds()>=update.ExpiresAt)throw new InvalidDataException();
        }
        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(path){UseShellExecute=true,Verb="runas"});
    }
}
