using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using FamilyConnect;

internal static class FriendsConfigurationVaultChecks
{
    internal static void Run()
    {
        if (!OperatingSystem.IsWindows()) { Console.WriteLine("SKIP Friends configuration DPAPI runtime (non-Windows host)."); return; }
        var root=Path.Combine(Path.GetTempPath(),"fc-config-vault-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(root);
        using var identity=ControlIdentity.Restore(Enumerable.Range(0,96).Select(i=>(byte)i).ToArray());
        using var fixture=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory,"fixtures","desktop-friends-catalog-v2.json")));
        var f=fixture.RootElement;var anchor=Convert.FromBase64String(f.GetProperty("anchor").GetString()!);
        const string alice="S-1-5-21-1-2-3-1001",bob="S-1-5-21-1-2-3-1002";
        JsonElement Reply(string country,string name="valid_nl")
        {
            var item=f.GetProperty("vectors").EnumerateArray().Single(v=>v.GetProperty("name").GetString()==name);
            var node=JsonNode.Parse(item.GetProperty("reply").GetRawText())!;
            node["device"]=identity.Reference;node["country"]=country;node["address"]=country=="ru"?"10.84.0.2/32":"10.83.0.2/32";
            return JsonSerializer.SerializeToElement(node);
        }
        int checks=0;
        void Reject(Action action)
        {
            try { action(); }
            catch(Exception e) when(e is IOException or CryptographicException or FormatException) { checks++;return; }
            throw new Exception("Unsafe configuration accepted");
        }
        try
        {
            var first=FriendsConfigurationVault.Accept(root,alice,identity,anchor,"nl",(floor,hash)=>{
                if(floor!=0||hash is not null)throw new Exception("Unexpected first floor");return Reply("nl"); });
            FriendsConfigurationVault.Accept(root,alice,identity,anchor,"ru",(floor,hash)=>{
                if(floor!=2||hash!=first.CatalogHash)throw new Exception("Missing shared floor");return Reply("ru"); });
            Parallel.For(0,8,i=>{
                if(!OperatingSystem.IsWindows())throw new PlatformNotSupportedException();
                string country=i%2==0?"nl":"ru";
                FriendsConfigurationVault.Accept(root,alice,identity,anchor,country,(floor,hash)=>{
                    if(floor!=2||hash!=first.CatalogHash)throw new Exception("Concurrent floor lost");return Reply(country); });
            });
            string path=FriendsConfigurationVault.ConfigPath(root,alice);var saved=File.ReadAllBytes(path);
            if(System.Text.Encoding.UTF8.GetString(saved).Contains("tcp_id"))throw new Exception("Plaintext cache");
            Reject(()=>FriendsConfigurationVault.Accept(root,alice,identity,anchor,"nl",(_,_)=>Reply("nl","valid_flags")));
            if(!saved.SequenceEqual(File.ReadAllBytes(path)))throw new Exception("Rejected replacement modified cache");
            Reject(()=>FriendsConfigurationVault.Accept(root,alice,identity,anchor,"nl",(_,_)=>throw new IOException("network denied")));
            if(!saved.SequenceEqual(File.ReadAllBytes(path)))throw new Exception("Network error modified cache");
            string other=FriendsConfigurationVault.ConfigPath(root,bob);
            File.Copy(path,other);File.Copy(path+".initialized",other+".initialized");
            Reject(()=>FriendsConfigurationVault.Accept(root,bob,identity,anchor,"nl",(_,_)=>throw new Exception("Corrupt cache reached network")));
            File.WriteAllBytes(path,new byte[]{1,2,3});
            Reject(()=>FriendsConfigurationVault.Accept(root,alice,identity,anchor,"nl",(_,_)=>throw new Exception("Corrupt cache reached network")));
            File.Delete(path);
            Reject(()=>FriendsConfigurationVault.Accept(root,alice,identity,anchor,"nl",(_,_)=>throw new Exception("Missing cache recreated")));
            File.WriteAllBytes(path,saved);File.Delete(path+".initialized");
            Reject(()=>FriendsConfigurationVault.Accept(root,alice,identity,anchor,"nl",(_,_)=>throw new Exception("Missing marker recreated")));
            Console.WriteLine($"Friends configuration DPAPI: save/resume, parallel/global floor and {checks} refusal checks passed.");
        }
        finally { Directory.Delete(root,true); }
    }
}
