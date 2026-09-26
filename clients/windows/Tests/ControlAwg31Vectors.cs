using System.Text.Json;
using FamilyConnect;

internal static class ControlAwg31Vectors
{
    internal static void Run()
    {
        var root = Path.Combine(AppContext.BaseDirectory, "control-awg31-v1");
        byte[] Read(string name) => File.ReadAllBytes(Path.Combine(root, name));
        var raw = Read("manifest.json");
        if (ControlProtocol.Hash(raw) != "51a0e53434e46876212a09945762a970c2943020220250f219042b12c71f7039") throw new Exception("AWG31 corpus revision");
        using var manifest = JsonDocument.Parse(raw);
        var m = manifest.RootElement;
        if (!m.GetProperty("test_only").GetBoolean()) throw new Exception("Test corpus required");
        foreach (var entry in m.GetProperty("files").EnumerateObject())
        {
            var bytes = Read(entry.Name);
            if (bytes.Length != entry.Value.GetProperty("size").GetInt32() || ControlProtocol.Hash(bytes) != entry.Value.GetProperty("sha256").GetString()) throw new Exception("AWG31 corpus integrity");
        }
        using var fixture = JsonDocument.Parse(Read("TEST-ONLY-identity.json"));
        var f = fixture.RootElement;
        byte[] Key(string name) => Convert.FromBase64String(f.GetProperty(name).GetString()!);
        foreach (var v in m.GetProperty("configurations").EnumerateArray())
        foreach (bool supported in new[]{false, true})
        {
            string category; ControlProtocol.VerifiedConfiguration? verified = null;
            try
            {
                verified = ControlProtocol.VerifyConfiguration(Read(v.GetProperty("input").GetString()!), Key("anchor_b64"), Key("rns_private_b64"), Key("public_identity_b64"), f.GetProperty("wireguard_public_key").GetString()!, v.GetProperty("client_version").GetString()!, v.GetProperty("now").GetInt64(), supported);
                category = "ACCEPT";
            }
            catch (ControlRejected e) { category = e.Category; }
            if (category != v.GetProperty(supported ? "expected" : "legacy_expected").GetString()) throw new Exception("AWG31 vector "+v.GetProperty("id").GetString()+" capability="+supported+": "+category);
            if (verified != null && !JsonElement.DeepEquals(verified.State, v.GetProperty("payload"))) throw new Exception("AWG31 payload mismatch");
            if (verified != null) Refusals(verified.State);
        }
        Console.WriteLine("AWG31: 8 shared vectors x 2 capabilities passed.");
    }
    static void Refusals(JsonElement original)
    {
        var config = original.GetProperty("transport_profiles")[0].GetProperty("config").GetString()!;
        var bad = new[]{config.Replace("DisableCookies = false\n", ""),
            config.Replace("RandomTrailers = true", "RandomTrailers = yes"),
            config.Replace("DisableCookies = false", "DisableCookies = 0"),
            config.Replace("H1 = 1\n", "H1 = 5\n"), config.Replace("S1 = 32", "S1 = 11"),
            config.Replace("S1 = 32", "S1 = 48"), config.Replace("0-64", "257"),
            config.Replace("0-64", "64-0"), config.Replace("[Peer]", "PostUp = command\n[Peer]"),
            System.Text.RegularExpressions.Regex.Replace(config, "HeaderProtectionKey = [^\\n]+", "HeaderProtectionKey = "+Convert.ToBase64String(new byte[32]))};
        foreach (var invalid in bad)
        {
            var changed = System.Text.Json.Nodes.JsonNode.Parse(original.GetRawText())!;
            changed["transport_profiles"]![0]!["config"] = invalid;
            try { ControlProfiles.Validate(ControlProtocol.Parse(System.Text.Encoding.UTF8.GetBytes(changed.ToJsonString()))); }
            catch (Exception e) when (ControlProtocol.Invalid(e)) { continue; }
            throw new Exception("Invalid AWG31 protection accepted");
        }
        Console.WriteLine("AWG31: 10 protection refusals passed.");
    }
}
