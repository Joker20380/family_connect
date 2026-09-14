using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using FamilyConnect;

internal static class ControlVectors
{
    internal static void Run()
    {
        var root = Path.Combine(AppContext.BaseDirectory, "control-v1");
        var manifestBytes = File.ReadAllBytes(Path.Combine(root, "manifest.json"));
        if (ControlProtocol.Hash(manifestBytes) != "c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd") throw new Exception("Unexpected conformance corpus revision");
        using var manifest = JsonDocument.Parse(manifestBytes);
        var m = manifest.RootElement;
        if (!m.GetProperty("test_only").GetBoolean()) throw new Exception("Test corpus required");
        foreach (var file in m.GetProperty("files").EnumerateObject())
        {
            var raw = File.ReadAllBytes(Path.Combine(root, file.Name));
            if (raw.Length != file.Value.GetProperty("size").GetInt32() || ControlProtocol.Hash(raw) != file.Value.GetProperty("sha256").GetString()) throw new Exception("Corpus integrity: "+file.Name);
        }
        using var fixture = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(root, m.GetProperty("fixture_identity").GetString()!)));
        var f = fixture.RootElement;
        byte[] Key(string name) => Convert.FromBase64String(f.GetProperty(name).GetString()!);
        int configurations = 0, acknowledgements = 0;
        foreach (var vector in m.GetProperty("configurations").EnumerateArray())
        {
            string category; ControlProtocol.VerifiedConfiguration? verified = null;
            try { verified = ControlProtocol.VerifyConfiguration(File.ReadAllBytes(Path.Combine(root, vector.GetProperty("input").GetString()!)), Key("anchor_b64"), Key("rns_private_b64"), Key("public_identity_b64"), f.GetProperty("wireguard_public_key").GetString()!, vector.GetProperty("client_version").GetString()!, vector.GetProperty("now").GetInt64()); category = "ACCEPT"; }
            catch (ControlRejected e) { category = e.Category; }
            var expected = vector.GetProperty("expected");
            if (category != expected.GetProperty("category").GetString()) throw new Exception("Configuration "+vector.GetProperty("id").GetString()+": "+category);
            if (verified != null && (!JsonElement.DeepEquals(verified.State, expected.GetProperty("payload")) || verified.Digest != expected.GetProperty("envelope_sha256").GetString())) throw new Exception("Configuration payload/hash mismatch");
            configurations++;
        }
        foreach (var vector in m.GetProperty("acknowledgements").EnumerateArray())
        {
            string category; JsonElement? body = null;
            try { body = ControlProtocol.VerifyAck(File.ReadAllBytes(Path.Combine(root, vector.GetProperty("input").GetString()!))); category = "ACCEPT"; }
            catch (ControlRejected e) { category = e.Category; }
            var expected = vector.GetProperty("expected");
            if (category != expected.GetProperty("category").GetString() || (body is JsonElement b && !JsonElement.DeepEquals(b, expected.GetProperty("body")))) throw new Exception("ACK "+vector.GetProperty("id").GetString()+": "+category);
            acknowledgements++;
        }
        int structural = 0;
        var valid = m.GetProperty("configurations").EnumerateArray().First(v => v.GetProperty("id").GetString() == "valid-wg").GetProperty("expected").GetProperty("payload");
        void RejectMutation(Action<JsonObject> mutate)
        {
            var value = JsonNode.Parse(valid.GetRawText())!.AsObject(); mutate(value);
            try { ControlProfiles.Validate(ControlProtocol.Parse(System.Text.Encoding.UTF8.GetBytes(value.ToJsonString()))); }
            catch (Exception e) when (ControlProtocol.Invalid(e)) { structural++; return; }
            throw new Exception("Invalid schema2 structure accepted");
        }
        foreach (var field in new[]{"revision", "issued_at", "expires_at"})
        {
            RejectMutation(v => v[field] = true); RejectMutation(v => v[field] = 0);
        }
        RejectMutation(v => v["expires_at"] = 1000);
        RejectMutation(v => v["expires_at"] = 87401);
        RejectMutation(v => v["min_client_version"] = "00.2.9");
        RejectMutation(v => v["wireguard_public_key"] = Convert.ToBase64String(new byte[32]));
        RejectMutation(v => v["previous_config_hash"] = "bad");
        RejectMutation(v => v["extra"] = 1);
        RejectMutation(v => v["gateways"]!.AsArray().Add(v["gateways"]![0]!.DeepClone()));
        RejectMutation(v => v["transport_profiles"]!.AsArray().Add(v["transport_profiles"]![0]!.DeepClone()));
        foreach (var host in new[]{"127.0.0.1", "0.0.0.0", "224.0.0.1", "::1", "::", "ff02::1", "198.51.100.01"})
            RejectMutation(v => v["gateways"]![0]!["endpoint"] = host);
        RejectMutation(v => v["gateways"]![0]!["port"] = true);
        RejectMutation(v => v["transport_profiles"]![0]!["gateway_id"] = "missing");
        RejectMutation(v => v["transport_profiles"]![0]!["transport_version"] = "2.0");
        var profile = valid.GetProperty("transport_profiles")[0].GetProperty("config").GetString()!;
        foreach (var config in new[]{profile+"PostUp = command\n", profile+"PublicKey = duplicate\n", profile.Replace("LOCAL_DEVICE_KEY", Convert.ToBase64String(new byte[32])), profile.Replace("MTU = 1280", "MTU = 1279"), profile.Replace("0.0.0.0/0, ::/0", "0.0.0.0/0"), profile.Replace(":51820", ":51821"), profile.Replace("10.77.0.4/32", "10.77.0.4/33")})
            RejectMutation(v => v["transport_profiles"]![0]!["config"] = config);
        Console.WriteLine($"{structural} additional schema2 refusal checks passed.");
        Console.WriteLine($"::notice title=Native control conformance::{configurations} configurations, {acknowledgements} ACKs passed; manifest SHA256 {ControlProtocol.Hash(File.ReadAllBytes(Path.Combine(root, "manifest.json")))}");
    }
}
