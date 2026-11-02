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
        AssignedCatalogs();
        SelectedGateways();
    }

    private static void SelectedGateways()
    {
        using var document=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory,"fixtures","friends-selection-v3.json")));
        var fixture=document.RootElement;
        var anchor=Convert.FromBase64String(fixture.GetProperty("anchor").GetString()!);
        var key=Convert.FromBase64String(fixture.GetProperty("wireguard_key").GetString()!);
        foreach(var sample in fixture.GetProperty("cases").EnumerateArray()){
            FriendsConfiguration? accepted=null;
            string target=sample.GetProperty("target").GetString()!;
            try { accepted=FriendsCatalog.Verify(sample.GetProperty("reply"),anchor,fixture.GetProperty("device").GetString()!,target,key,sample.GetProperty("floor").GetInt64(),sample.TryGetProperty("previous_hash",out var hash)?hash.GetString():null); }
            catch(FormatException) { }
            if((accepted is not null)!=sample.GetProperty("valid").GetBoolean())throw new Exception("Selection vector mismatch: "+sample.GetProperty("name").GetString());
            if(accepted is not null){
                if(accepted.GatewayId!=target||accepted.Country!="nl")throw new Exception("Gateway/country binding");
                FriendsCatalog.NativeTcp(accepted,fixture.GetProperty("wireguard_key").GetString()!);
                FriendsCatalog.NativeAwg(accepted);
            }
        }
        Console.WriteLine("Friends explicit selection: shared positive/negative vectors passed.");
    }

    private static void AssignedCatalogs()
    {
        using var document = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory, "fixtures", "friends-multinode-v2.json")));
        var fixture = document.RootElement;
        var anchor = Convert.FromBase64String(fixture.GetProperty("anchor").GetString()!);
        var wireguard = Convert.FromBase64String(fixture.GetProperty("wireguard_key").GetString()!);
        var device = fixture.GetProperty("device").GetString()!;
        long floor = 0;
        string? hash = null;
        int count = 0;
        foreach (var sample in fixture.GetProperty("cases").EnumerateArray())
        {
            var reply = sample.GetProperty("reply");
            var sequence = sample.GetProperty("sequence").GetInt64();
            var accepted = FriendsCatalog.Verify(reply, anchor, device, "nl", wireguard, floor, hash);
            using var tcp = JsonDocument.Parse(accepted.Tcp);
            var host = sample.GetProperty("host").GetString()!;
            if (accepted.Sequence != sequence || tcp.RootElement.GetProperty("server").GetString() != host
                || !accepted.Awg.Contains("Endpoint = " + host + ":"))
                throw new Exception("Assigned physical gateway mismatch");
            bool rejected = false;
            try { FriendsCatalog.Verify(reply, anchor, device, "nl", wireguard, sequence + 1); }
            catch (FormatException) { rejected = true; }
            if (!rejected) throw new Exception("Assigned catalog downgrade accepted");
            floor = accepted.Sequence;
            hash = accepted.CatalogHash;
            count++;
        }
        if (count != 3 || floor != 6) throw new Exception("Missing assignment/rollback vectors");
        Console.WriteLine("Friends multi-node: 3 assigned catalogs and 3 downgrade rejections passed.");
    }
}
