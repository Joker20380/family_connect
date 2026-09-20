using System.Text.Json;
using FamilyConnect;
internal static class FriendsCatalogChecks
{
    internal static void Run()
    {
        using var doc=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory,"fixtures","desktop-friends-catalog-v2.json")));
        var f=doc.RootElement;int count=0;
        foreach(var c in f.GetProperty("vectors").EnumerateArray())
        {
            var reply=c.GetProperty("reply");bool valid=c.GetProperty("valid").GetBoolean();
            FriendsConfiguration? result=null;
            try { result=FriendsCatalog.Verify(reply,Convert.FromBase64String(f.GetProperty("anchor").GetString()!),f.GetProperty("device").GetString()!,reply.GetProperty("country").GetString()!,Convert.FromBase64String(f.GetProperty("wireguard_key").GetString()!),c.GetProperty("floor").GetInt64(),c.TryGetProperty("previous_hash",out var hash)?hash.GetString():null); }
            catch(FormatException e) when(e.Message=="Invalid Friends configuration") { if(valid)throw new Exception("Rejected valid vector: "+c.GetProperty("name").GetString()); }
            if(valid!=(result is not null))throw new Exception("Catalog vector mismatch: "+c.GetProperty("name").GetString());
            if(result is not null && (result.Sequence!=2 || result.Tcp.Contains("DEVICE_CREDENTIAL") || result.Awg.Contains("LOCAL_DEVICE_KEY") || result.ToString().Contains(f.GetProperty("wireguard_key").GetString()!)))throw new Exception("Materialization/redaction mismatch");
            if(result is not null)
            {
                var awg=FriendsCatalog.NativeAwg(result);
                if(awg.Address!=result.Address[..^3]||awg.ToString().Contains(f.GetProperty("wireguard_key").GetString()!))throw new Exception("Native AWG address/redaction");
                using var runtime=JsonDocument.Parse(awg.Config("fcawg12345678","test-uplink"));
                var text=runtime.RootElement.GetProperty("config").GetString()!;
                if(!text.Contains("header_protection_key=")||!text.Contains("content_padding_addition=")||text.Contains("headerprotectionkey="))throw new Exception("AWG UAPI mapping");
                var grant=FriendsCatalog.NativeTcp(result,f.GetProperty("wireguard_key").GetString()!);
                if(grant.Sequence!=result.Sequence||grant.Id!=reply.GetProperty("tcp_id").GetString())throw new Exception("Native TCP mapping mismatch");
            }
            count++;
        }
        Console.WriteLine($"Friends catalog: {count} shared verification/materialization vectors passed.");
    }
}
