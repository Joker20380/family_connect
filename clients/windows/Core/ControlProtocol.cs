using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;

namespace FamilyConnect;

public sealed class ControlRejected(string category) : FormatException(category)
{
    public string Category { get; } = category;
}

// Carrier-independent verification only. This class grants no application authority:
// revision/chain acceptance and durable recovery belong to the future journal.
public static class ControlProtocol
{
    internal const string ConfigPurpose = "family-connect/control-config/v1";
    internal const string AckPurpose = "family-connect/control-ack/v1";
    internal static void Require(bool condition) { if (!condition) throw new FormatException("invalid control data"); }
    internal static bool Matches(string text, string pattern) => Regex.IsMatch(text, "\\A(?:"+pattern+")\\z", RegexOptions.CultureInvariant);
    internal static string Text(JsonElement value) => value.GetString() ?? throw new FormatException("missing string");
    internal static long Integer(JsonElement value, long minimum = 0)
    {
        Require(value.ValueKind == JsonValueKind.Number && Matches(value.GetRawText(), "-?[0-9]+"));
        Require(value.TryGetInt64(out var number) && number >= minimum); return number;
    }
    internal static void Fields(JsonElement value, string fields)
    {
        Require(value.ValueKind == JsonValueKind.Object);
        Require(value.EnumerateObject().Select(p => p.Name).ToHashSet(StringComparer.Ordinal).SetEquals(fields.Split(' ')));
    }
    internal static JsonElement Parse(byte[] raw)
    {
        // Reject duplicates recursively, including escaped spellings of the same key.
        using var doc = JsonDocument.Parse(raw, new JsonDocumentOptions { MaxDepth = 64 });
        void Visit(JsonElement value)
        {
            if (value.ValueKind == JsonValueKind.Object)
            {
                var names = new HashSet<string>(StringComparer.Ordinal);
                foreach (var p in value.EnumerateObject()) { Require(names.Add(p.Name)); Visit(p.Value); }
            }
            else if (value.ValueKind == JsonValueKind.Array) foreach (var item in value.EnumerateArray()) Visit(item);
        }
        Visit(doc.RootElement); return doc.RootElement.Clone();
    }
    internal static byte[] Base64(string text, bool canonical = false)
    {
        Require(Matches(text, "[A-Za-z0-9+/]*={0,2}"));
        var bytes = Convert.FromBase64String(text);
        if (canonical) Require(Convert.ToBase64String(bytes) == text);
        return bytes;
    }
    internal static string Hash(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));
    internal static bool Signature(byte[] key, byte[] signature, string purpose, byte[] body)
    {
        if (key.Length != 32 || signature.Length != 64) return false;
        var signer = new Ed25519Signer(); signer.Init(false, new Ed25519PublicKeyParameters(key, 0));
        var domain = Encoding.UTF8.GetBytes(purpose+"\0");
        signer.BlockUpdate(domain, 0, domain.Length); signer.BlockUpdate(body, 0, body.Length);
        return signer.VerifySignature(signature);
    }
    // ACK strings are constrained to ASCII below. Python json.dumps escapes neither
    // '+' nor '/', whereas the default .NET JSON encoder does escape '+'.
    internal static byte[] AckCanonical(JsonElement body, bool omitId = false)
    {
        using var stream = new MemoryStream();
        using (var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping }))
        {
            writer.WriteStartObject();
            foreach (var p in body.EnumerateObject().OrderBy(p => p.Name, StringComparer.Ordinal))
            {
                if (omitId && p.Name == "ack_id") continue;
                writer.WritePropertyName(p.Name);
                if (p.Value.ValueKind == JsonValueKind.Number) writer.WriteNumberValue(Integer(p.Value));
                else p.Value.WriteTo(writer);
            }
            writer.WriteEndObject();
        }
        return stream.ToArray();
    }
    public static JsonElement VerifyAck(byte[] raw)
    {
        try
        {
            Require(raw.Length <= 4096); var outer = Parse(raw); Fields(outer, "body signature");
            var body = outer.GetProperty("body");
            Fields(body, "schema_version device public_identity envelope_hash config_id sequence status error timestamp ack_id");
            Require(Integer(body.GetProperty("schema_version")) == 1);
            Integer(body.GetProperty("sequence")); Integer(body.GetProperty("timestamp"));
            Require("RECEIVED REJECTED APPLIED COMMITTED ROLLED_BACK FAILED".Split(' ').Contains(Text(body.GetProperty("status"))));
            Require("NONE SIZE CLOCK SIGNATURE MALFORMED SCHEMA TARGET SIGNER STRUCTURE LEASE CLIENT_VERSION UNSUPPORTED_TRANSPORT_VERSION REPLAY PREVIOUS_HASH APPLY HEALTH RECOVERY ROLLBACK".Split(' ').Contains(Text(body.GetProperty("error"))));
            Require(Matches(Text(body.GetProperty("envelope_hash")), "[0-9a-f]{64}"));
            Require(Matches(Text(body.GetProperty("ack_id")), "[0-9a-f]{64}"));
            var id = body.GetProperty("config_id");
            Require(id.ValueKind == JsonValueKind.Null || Matches(Text(id), "[a-zA-Z0-9_-]{1,64}"));
            var key = Base64(Text(body.GetProperty("public_identity")), true); Require(key.Length == 64);
            Require(Hash(key)[..32] == Text(body.GetProperty("device")));
            Require(Signature(key[32..], Base64(Text(outer.GetProperty("signature"))), AckPurpose, AckCanonical(body)));
            Require(Hash(AckCanonical(body, true)) == Text(body.GetProperty("ack_id")));
            return body.Clone();
        }
        catch (Exception e) when (Invalid(e)) { throw new ControlRejected("REJECT"); }
    }
    internal static bool Invalid(Exception e) => e is FormatException or JsonException or InvalidOperationException or ArgumentException or KeyNotFoundException or CryptographicException or Org.BouncyCastle.Crypto.CryptoException or OverflowException;
    static byte[] Decrypt(byte[] cipher, byte[] privateKey, byte[] publicIdentity)
    {
        Require(privateKey.Length == 64 && publicIdentity.Length == 64 && cipher.Length >= 96);
        var shared = new byte[32];
        new X25519PrivateKeyParameters(privateKey, 0).GenerateSecret(new X25519PublicKeyParameters(cipher, 0), shared, 0);
        Require(shared.Any(b => b != 0));
        var derived = HKDF.DeriveKey(HashAlgorithmName.SHA256, shared, 64, SHA256.HashData(publicIdentity)[..16]);
        try
        {
            var token = cipher[32..];
            Require(CryptographicOperations.FixedTimeEquals(HMACSHA256.HashData(derived[..32], token[..^32]), token[^32..]));
            using var aes = Aes.Create(); aes.Key = derived[32..];
            return aes.DecryptCbc(token[16..^32], token[..16], PaddingMode.PKCS7);
        }
        finally { CryptographicOperations.ZeroMemory(shared); CryptographicOperations.ZeroMemory(derived); }
    }
    internal static Version VersionValue(string text)
    {
        Require(Matches(text, "(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,5})"));
        return Version.Parse(text);
    }
    public sealed record VerifiedConfiguration(JsonElement State, string Digest);
    public static VerifiedConfiguration VerifyConfiguration(byte[] raw, byte[] anchor, byte[] rnsPrivate,
        byte[] publicIdentity, string wireguardPublicKey, string clientVersion, long now)
    {
        if (now < 0) throw new ControlRejected("CLOCK");
        if (raw.Length > 65536) throw new ControlRejected("SIZE");
        byte[] cipher;
        try
        {
            var outer = Parse(raw); Fields(outer, "ciphertext signature");
            cipher = Base64(Text(outer.GetProperty("ciphertext")));
            if (!Signature(anchor, Base64(Text(outer.GetProperty("signature"))), ConfigPurpose, cipher)) throw new ControlRejected("SIGNATURE");
        }
        catch (ControlRejected) { throw; }
        catch (Exception e) when (Invalid(e)) { throw new ControlRejected("MALFORMED"); }
        JsonElement state;
        try
        {
            var plain = Decrypt(cipher, rnsPrivate, publicIdentity);
            try { state = Parse(plain); } finally { CryptographicOperations.ZeroMemory(plain); }
            Require(state.ValueKind == JsonValueKind.Object);
            if (!state.TryGetProperty("schema_version", out var schema) || schema.ValueKind != JsonValueKind.Number || schema.GetRawText() != "2") throw new ControlRejected("SCHEMA");
            if (!state.TryGetProperty("audience", out var audience) || audience.ValueKind != JsonValueKind.String || Text(audience) != ConfigPurpose ||
                !state.TryGetProperty("recipient", out var recipient) || recipient.ValueKind != JsonValueKind.String || Text(recipient) != Hash(publicIdentity)[..32]) throw new ControlRejected("TARGET");
            if (!state.TryGetProperty("signer_key_id", out var signer) || signer.ValueKind != JsonValueKind.String || Text(signer) != Hash(anchor)) throw new ControlRejected("SIGNER");
            if (state.TryGetProperty("transport_profiles", out var profiles) && profiles.ValueKind == JsonValueKind.Array)
                foreach (var p in profiles.EnumerateArray())
                    if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty("transport", out var t) && t.ValueKind == JsonValueKind.String && Text(t) == "amneziawg" && p.TryGetProperty("transport_version", out var v) && v.ValueKind == JsonValueKind.String && Text(v) == "3.1") throw new ControlRejected("UNSUPPORTED_TRANSPORT_VERSION");
            ControlProfiles.Validate(state);
        }
        catch (ControlRejected) { throw; }
        catch (Exception e) when (Invalid(e)) { throw new ControlRejected("STRUCTURE"); }
        if (Text(state.GetProperty("wireguard_public_key")) != wireguardPublicKey) throw new ControlRejected("TARGET");
        if (now < Integer(state.GetProperty("issued_at")) || now >= Integer(state.GetProperty("expires_at"))) throw new ControlRejected("LEASE");
        if (VersionValue(Text(state.GetProperty("min_client_version"))) > VersionValue(clientVersion)) throw new ControlRejected("CLIENT_VERSION");
        return new(state, Hash(raw));
    }
}
