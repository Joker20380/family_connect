using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using static FamilyConnect.ControlProtocol;

namespace FamilyConnect;

// Schema2 profile validation, kept separate from the legacy activation schemas.
internal static class ControlProfiles
{
    static readonly string[] AwgFields = "Jc Jmin Jmax S1 S2 S3 S4 H1 H2 H3 H4 I1 I2 I3 I4 I5".Split(' ');
    static string S(JsonElement value, string key) => Text(value.GetProperty(key));
    static void Id(string value) => Require(Matches(value, "[a-zA-Z0-9_-]{1,64}"));
    static IPAddress Ip(string value)
    {
        var ip = IPAddress.Parse(value);
        // .NET also accepts abbreviated/octal IPv4 addresses; the Python parser does not.
        if (ip.AddressFamily == AddressFamily.InterNetwork) Require(ip.ToString() == value);
        Require(!value.Contains('%')); return ip;
    }
    static void Key(string value, bool canonical = false, bool nonzero = false)
    {
        var bytes = Base64(value, canonical); Require(bytes.Length == 32 && (!nonzero || bytes.Any(b => b != 0)));
    }
    internal static void Validate(JsonElement state)
    {
        Fields(state, "schema_version config_id revision issued_at expires_at recipient audience wireguard_public_key min_client_version previous_config_hash signer_key_id gateways transport_profiles");
        Id(S(state, "config_id")); Integer(state.GetProperty("revision"), 1);
        var issued = Integer(state.GetProperty("issued_at"), 1); var expires = Integer(state.GetProperty("expires_at"), 1);
        Require(expires > issued && expires-issued <= 86400);
        Key(S(state, "wireguard_public_key"), true, true); VersionValue(S(state, "min_client_version"));
        var previous = state.GetProperty("previous_config_hash"); Require(previous.ValueKind == JsonValueKind.Null || Matches(Text(previous), "[0-9a-f]{64}"));
        var gateways = state.GetProperty("gateways"); var profiles = state.GetProperty("transport_profiles");
        Require(gateways.ValueKind == JsonValueKind.Array && gateways.GetArrayLength() is >=1 and <=8);
        Require(profiles.ValueKind == JsonValueKind.Array && profiles.GetArrayLength() is >=1 and <=8);
        var endpoints = new Dictionary<string, (string, long)>(StringComparer.Ordinal);
        foreach (var g in gateways.EnumerateArray())
        {
            Fields(g, "gateway_id endpoint port"); Id(S(g, "gateway_id"));
            var host = S(g, "endpoint"); var ip = Ip(host); var bytes = ip.GetAddressBytes();
            Require(ip.ToString() == host && !IPAddress.IsLoopback(ip) && !ip.Equals(IPAddress.Any) && !ip.Equals(IPAddress.IPv6Any) && !ip.IsIPv6Multicast && !(bytes.Length == 4 && bytes[0] is >=224 and <=239));
            var port = Integer(g.GetProperty("port"), 1); Require(port <= 65535);
            Require(endpoints.TryAdd(S(g, "gateway_id"), (host, port)));
        }
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var p in profiles.EnumerateArray())
        {
            Fields(p, "profile_id gateway_id transport transport_version config");
            Id(S(p, "profile_id")); Id(S(p, "gateway_id")); Require(ids.Add(S(p, "profile_id")));
            var config = S(p, "config"); Require(config.Length > 0 && Encoding.UTF8.GetByteCount(config) <= 16384);
            var transport = S(p, "transport"); var version = S(p, "transport_version");
            Require(transport is "wireguard" or "amneziawg" or "vless-reality");
            Require(version == (transport == "amneziawg" ? "2.0" : "1"));
            var endpoint = transport == "vless-reality" ? Tcp(config) : WireGuard(config, transport == "amneziawg");
            Require(endpoints.TryGetValue(S(p, "gateway_id"), out var expected) && endpoint == expected);
        }
    }
    static (string, long) Tcp(string text)
    {
        var p = Parse(Encoding.UTF8.GetBytes(text)); Fields(p, "type server port id public_key server_name short_id");
        Require(S(p, "type") == "vless-reality-v1"); var host = S(p, "server"); Require(Ip(host).AddressFamily == AddressFamily.InterNetwork);
        var port = Integer(p.GetProperty("port"), 1); Require(port <= 65535);
        Require(Guid.TryParseExact(S(p, "id"), "D", out var id) && id != Guid.Empty && id.ToString() == S(p, "id"));
        var key = S(p, "public_key"); Require(Matches(key, "[A-Za-z0-9_-]{43}"));
        var raw = Base64(key.Replace('-', '+').Replace('_', '/')+"=", true); Require(raw.Length == 32 && raw.Any(b => b != 0));
        var name = S(p, "server_name"); Require(name.Length <= 253 && Matches(name, "(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z]{2,63}"));
        Require(Matches(S(p, "short_id"), "(?:[0-9a-f]{2}){1,8}")); return (host, port);
    }
    static long Number(string text, long low, long high)
    {
        Require(long.TryParse(text, System.Globalization.NumberStyles.AllowLeadingSign, System.Globalization.CultureInfo.InvariantCulture, out var value) && value >= low && value <= high); return value;
    }
    static (string, long) WireGuard(string text, bool awg)
    {
        Require(!text.Contains('\0'));
        var sections = new Dictionary<string, Dictionary<string, string>>(StringComparer.Ordinal);
        Dictionary<string, string>? current = null; string section = "";
        foreach (var raw in Regex.Split(text, "\\r\\n|[\\n\\r\\v\\f\\x1c-\\x1e\\x85\\u2028\\u2029]"))
        {
            var line = raw.Split('#', 2)[0].Trim(); if (line.Length == 0) continue;
            if (line.StartsWith('['))
            {
                Require(line is "[Interface]" or "[Peer]"); section = line[1..^1];
                current = new(StringComparer.Ordinal); Require(sections.TryAdd(section, current)); continue;
            }
            var parts = line.Split('=', 2); Require(current != null && parts.Length == 2);
            var key = parts[0].Trim(); var value = parts[1].Trim();
            var allowed = section == "Interface" ? "PrivateKey Address DNS MTU ListenPort" : "PublicKey PresharedKey Endpoint AllowedIPs PersistentKeepalive";
            Require(allowed.Split(' ').Contains(key) || (section == "Interface" && awg && AwgFields.Contains(key)));
            Require(value.Length > 0 && current!.TryAdd(key, value));
        }
        Require(sections.Count == 2); var i = sections["Interface"]; var p = sections["Peer"];
        Require(i["PrivateKey"] == "LOCAL_DEVICE_KEY" && text.Split("LOCAL_DEVICE_KEY").Length == 2);
        Key(p["PublicKey"]); if (p.TryGetValue("PresharedKey", out var psk)) Key(psk);
        foreach (var address in i["Address"].Split(','))
        {
            var bits = address.Trim().Split('/'); Require(bits.Length <= 2); var ip = Ip(bits[0]);
            if (bits.Length == 2) Number(bits[1], 0, ip.AddressFamily == AddressFamily.InterNetwork ? 32 : 128);
        }
        foreach (var dns in i["DNS"].Split(',')) Ip(dns.Trim());
        Require(p["AllowedIPs"].Split(',').Select(x => x.Trim()).ToHashSet().SetEquals(new[]{"0.0.0.0/0", "::/0"}));
        var at = p["Endpoint"].LastIndexOf(':'); Require(at > 0);
        var host = p["Endpoint"][..at].Trim('[', ']'); Ip(host); var port = Number(p["Endpoint"][(at+1)..], 1, 65535);
        if (i.TryGetValue("MTU", out var mtu)) Number(mtu, 1280, 1500);
        if (i.TryGetValue("ListenPort", out var listen)) Number(listen, 0, 65535);
        if (p.TryGetValue("PersistentKeepalive", out var keep)) Number(keep, 0, 65535);
        if (awg) ValidateAwg(i);
        return (host, port);
    }
    static void ValidateAwg(Dictionary<string, string> fields)
    {
        foreach (var name in AwgFields.Take(7))
        {
            var value = fields[name]; Require(Matches(value, "[0-9]{1,5}"));
            Number(value, 0, name == "Jc" ? 12 : name.StartsWith('J') ? 1280 : 256);
        }
        Require(long.Parse(fields["Jmin"]) <= long.Parse(fields["Jmax"]));
        var ranges = new List<(long Low, long High)>();
        foreach (var name in AwgFields.Skip(7).Take(4))
        {
            var value = fields[name]; Require(Matches(value, "[0-9]{1,10}(?:-[0-9]{1,10})?"));
            var parts = value.Split('-'); var low = Number(parts[0], 5, uint.MaxValue); var high = Number(parts[^1], low, uint.MaxValue);
            Require(!ranges.Any(r => low <= r.High && r.Low <= high)); ranges.Add((low, high));
        }
        foreach (var name in AwgFields.Skip(11))
        {
            if (!fields.TryGetValue(name, out var value)) continue;
            int position = 0, size = 0;
            foreach (Match m in Regex.Matches(value, "<(?:b 0x([0-9a-fA-F]+)|(r|rd|rc) ([0-9]{1,4})|(t))>"))
            {
                Require(m.Index == position);
                if (m.Groups[1].Success) { Require(m.Groups[1].Length % 2 == 0); size += m.Groups[1].Length / 2; }
                else size += m.Groups[2].Success ? int.Parse(m.Groups[3].Value) : 4;
                position += m.Length;
            }
            Require(position == value.Length && size is >=1 and <=1280);
        }
    }
}
