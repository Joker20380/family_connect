using System.Net;
using System.Text;
using System.Text.Json;
using static FamilyConnect.ControlProtocol;

namespace FamilyConnect;

// Device credentials stay with the protected owner, never the UI/diagnostic reply.
internal sealed class FriendsConfiguration(string country, long sequence, string hash, string address, string tcp, string awg)
{
    internal string Country { get; } = country;
    internal long Sequence { get; } = sequence;
    internal string CatalogHash { get; } = hash;
    internal string Address { get; } = address;
    internal string Tcp { get; } = tcp;
    internal string Awg { get; } = awg;
    public override string ToString() => $"FriendsConfiguration({Country}, {Sequence})";
}

internal static class FriendsCatalog
{
    const long MaxSequence = 9007199254740991;
    const string Sample = "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=";
    static string S(JsonElement e, string name) => Text(e.GetProperty(name));
    static void Key(string value) { var raw = Base64(value, true); Require(raw.Length == 32); }
    static string Ip(string value)
    {
        Require(IPAddress.TryParse(value, out var ip) && ip.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork && ip.ToString() == value);
        return value;
    }
    static int Number(string text, int low, int high)
    {
        Require(Matches(text, "[0-9]{1,5}") && int.TryParse(text, out _));
        int value = int.Parse(text); Require(value >= low && value <= high); return value;
    }
    static void Tcp(JsonElement p)
    {
        Fields(p, "type server port id public_key server_name short_id");
        Require(S(p, "type") == "vless-reality-v1" && S(p, "id") == "DEVICE_CREDENTIAL");
        // Reuse the existing strict credential validator without accepting any Xray config.
        TcpProfile.Validate(new TcpGrant(1, Sample, 1, 1, S(p, "server"), checked((int)Integer(p.GetProperty("port"), 1)),
            "11111111-1111-4111-8111-111111111111", S(p, "public_key"), S(p, "server_name"), S(p, "short_id")));
    }
    static void Awg(string template)
    {
        Require(Encoding.UTF8.GetByteCount(template) <= 8192 && !template.Contains('\0'));
        Require(template.Split("LOCAL_DEVICE_KEY").Length == 2 && template.Split("ASSIGNED_ADDRESS").Length == 2);
        Require(System.Text.RegularExpressions.Regex.IsMatch(template, "(?m)^PrivateKey = LOCAL_DEVICE_KEY$") &&
            System.Text.RegularExpressions.Regex.IsMatch(template, "(?m)^Address = ASSIGNED_ADDRESS$"));
        var sections = new Dictionary<string, Dictionary<string, string>>();
        Dictionary<string, string>? current = null;
        foreach (var raw in template.Split('\n'))
        {
            var line = raw.Split('#')[0].Trim(); if (line.Length == 0) continue;
            if (line.StartsWith('['))
            {
                Require(line is "[Interface]" or "[Peer]");
                current = new(); Require(sections.TryAdd(line, current)); continue;
            }
            int split = line.IndexOf('='); Require(current is not null && split > 0);
            string name = line[..split].Trim(), value = line[(split+1)..].Trim();
            Require(value.Length > 0 && current!.TryAdd(name, value));
        }
        Require(sections.Count == 2 && sections.ContainsKey("[Interface]") && sections.ContainsKey("[Peer]"));
        var face = sections["[Interface]"]; var peer = sections["[Peer]"];
        var parameters = "Jc Jmin Jmax S1 S2 S3 S4 H1 H2 H3 H4 I1 I2 I3 I4 I5".Split(' ');
        var extra = "HeaderProtectionKey ContentPaddingAddition RandomTrailers DisableCookies".Split(' ');
        Require(face.Keys.All(k => parameters.Contains(k) || extra.Contains(k) || "PrivateKey Address DNS MTU ListenPort".Split(' ').Contains(k)));
        Require(peer.Keys.All(k => "PublicKey PresharedKey Endpoint AllowedIPs PersistentKeepalive".Split(' ').Contains(k)));
        Require(face["PrivateKey"] == "LOCAL_DEVICE_KEY" && face["Address"] == "ASSIGNED_ADDRESS");
        foreach (var dns in face["DNS"].Split(',')) Require(IPAddress.TryParse(dns.Trim(), out _));
        if (face.TryGetValue("MTU", out var mtu)) Number(mtu, 1280, 1500);
        if (face.TryGetValue("ListenPort", out var listen)) Number(listen, 0, 65535);
        Key(face["HeaderProtectionKey"]); Require(Base64(face["HeaderProtectionKey"]).Any(b => b != 0));
        string padding = face["ContentPaddingAddition"]; Require(Matches(padding, "[0-9]{1,5}(?:-[0-9]{1,5})?"));
        var range = padding.Split('-'); Require(Number(range[0], 0, 256) <= Number(range[^1], 0, 256));
        foreach (var flag in new[] { "RandomTrailers", "DisableCookies" })
            if (face.TryGetValue(flag, out var value)) Require(value is "true" or "false");
        var old = face.Where(p => parameters.Contains(p.Key)).ToDictionary(p => p.Key, p => p.Value);
        for (int i = 1; i <= 4; i++)
        {
            Number(face["S"+i], 12, 256); Require(face["H"+i] == i.ToString());
            old["H"+i] = (i+10).ToString(); // Older validation below checks remaining AWG grammar only.
        }
        if (face.GetValueOrDefault("RandomTrailers") == "true") Require(Enumerable.Range(1, 4).Select(i => face["S"+i]).Distinct().Count() == 1);
        Key(peer["PublicKey"]); if (peer.TryGetValue("PresharedKey", out var psk)) Key(psk);
        Require(peer["AllowedIPs"].Split(',').Select(x => x.Trim()).ToHashSet().SetEquals(new[] { "0.0.0.0/0", "::/0" }));
        var endpoint = peer["Endpoint"].Split(':'); Require(endpoint.Length == 2); Ip(endpoint[0]);
        int port = Number(endpoint[1], 1, 65535);
        if (peer.TryGetValue("PersistentKeepalive", out var keep)) Number(keep, 0, 65535);
        AwgProfile.Validate(new AwgGrant(1, Sample, 1, 1, peer["PublicKey"], endpoint[0], port, 4, old));
    }
    internal static FriendsConfiguration Verify(JsonElement reply, byte[] anchor, string device, string country, byte[] wireguardKey,
        long floor = 0, string? previousHash = null)
    {
        try
        {
            Require(country is "ru" or "nl" && floor >= 0 && floor <= MaxSequence && wireguardKey.Length == 32);
            // Reparse even injected/locally loaded JsonElements to reject nested duplicate properties.
            reply = Parse(Encoding.UTF8.GetBytes(reply.GetRawText()));
            Fields(reply, "device country address tcp_id catalog"); Require(S(reply, "device") == device && S(reply, "country") == country);
            var envelope = reply.GetProperty("catalog"); Fields(envelope, "payload signature");
            Require(Encoding.UTF8.GetByteCount(envelope.GetRawText()) <= 16384);
            var payload = Base64(S(envelope, "payload"), true); Require(payload.Length > 0 && payload.Length <= 8192);
            Require(Signature(anchor, Base64(S(envelope, "signature"), true), "family-connect/invited-test/v1", payload));
            var value = Parse(payload); Fields(value, "schema sequence access gateways");
            Require(Integer(value.GetProperty("schema")) == 2 && S(value, "access") == "invite-test");
            long sequence = Integer(value.GetProperty("sequence"), 1); Require(sequence >= floor && sequence <= MaxSequence);
            string hash = Hash(payload);
            if (previousHash is not null) Require(Matches(previousHash, "[0-9a-f]{64}") && (sequence != floor || hash == previousHash));
            var gateways = value.GetProperty("gateways"); Require(gateways.ValueKind == JsonValueKind.Array && gateways.GetArrayLength() == 2);
            var profiles = new Dictionary<string, JsonElement>();
            foreach (var item in gateways.EnumerateArray())
            {
                Fields(item, "country tcp awg"); var region = S(item, "country"); Require(region is "ru" or "nl" && profiles.TryAdd(region, item));
                Tcp(item.GetProperty("tcp")); Awg(S(item, "awg"));
            }
            string address = S(reply, "address"), credential = S(reply, "tcp_id");
            Require(address.EndsWith("/32")); var ip = Ip(address[..^3]); var bytes = IPAddress.Parse(ip).GetAddressBytes();
            Require(bytes[0] == 10 && bytes[1] == (country == "ru" ? 84 : 83));
            Require(!(bytes[2] == 0 && bytes[3] <= 1) && !(bytes[2] == 255 && bytes[3] == 255));
            Require(Guid.TryParseExact(credential, "D", out var id) && id != Guid.Empty && id.ToString("D") == credential);
            var selected = profiles[country];
            string tcp = selected.GetProperty("tcp").GetRawText().Replace("DEVICE_CREDENTIAL", credential);
            string awg = S(selected, "awg").Replace("LOCAL_DEVICE_KEY", Convert.ToBase64String(wireguardKey)).Replace("ASSIGNED_ADDRESS", address);
            return new(country, sequence, hash, address, tcp, awg);
        }
        catch (Exception e) when (e is not OutOfMemoryException) { throw new FormatException("Invalid Friends configuration"); }
    }
    internal static TcpGrant NativeTcp(FriendsConfiguration profile, string devicePublicKey)
    {
        var p = ControlProtocol.Parse(System.Text.Encoding.UTF8.GetBytes(profile.Tcp));
        ControlProtocol.Fields(p,"type server port id public_key server_name short_id");
        if (p.GetProperty("type").GetString() != "vless-reality-v1") throw new FormatException("Invalid TCP transport");
        string S(string name) => ControlProtocol.Text(p.GetProperty(name));
        // This grant is in-memory native input after signed-catalog/HTTPS verification,
        // not an exported legacy activation file. No synthetic operator signature.
        var grant = new TcpGrant(1,devicePublicKey,profile.Sequence,1,S("server"),
            checked((int)ControlProtocol.Integer(p.GetProperty("port"),1)),S("id"),S("public_key"),S("server_name"),S("short_id"));
        TcpProfile.Validate(grant); return grant;
    }
}
