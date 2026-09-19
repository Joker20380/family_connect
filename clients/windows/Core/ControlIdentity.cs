using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;

namespace FamilyConnect;

// Broker-owned identity material. This class does not persist keys or authorize VPN use.
// A migration supplies the existing WG key; enrollment must never rotate it implicitly.
internal sealed class ControlIdentity : IDisposable
{
    const string Audience = "family-connect/enrollment/v1";
    const string Purpose = "family-connect/transport-key-binding/v1\0";
    byte[]? material;
    static readonly JsonSerializerOptions Json = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };

    ControlIdentity(byte[] source)
    {
        if (source.Length != 96) throw new ArgumentException("Invalid identity size");
        material = source.ToArray();
    }

    internal static ControlIdentity Restore(byte[] source) => new(source);

    internal static ControlIdentity Create(byte[] existingWireguardKey)
    {
        if (existingWireguardKey.Length != 32) throw new ArgumentException("Invalid WG key size");
        var bytes = new byte[96];
        try
        {
            RandomNumberGenerator.Fill(bytes.AsSpan(0, 64));
            existingWireguardKey.CopyTo(bytes, 64);
            return new(bytes);
        }
        finally { CryptographicOperations.ZeroMemory(bytes); }
    }

    byte[] Open() => material ?? throw new ObjectDisposedException(nameof(ControlIdentity));
    // Used only by the protected storage owner; caller must erase the returned copy.
    internal byte[] ExportForProtection() => Open().ToArray();

    // Caller owns this temporary copy and must erase it after materialization.
    internal byte[] WireguardPrivateKey() => Open().AsSpan(64, 32).ToArray();

    internal byte[] PublicIdentity()
    {
        var bytes = Open();
        var result = new byte[64];
        new X25519PrivateKeyParameters(bytes, 0).GeneratePublicKey().GetEncoded().CopyTo(result, 0);
        new Ed25519PrivateKeyParameters(bytes, 32).GeneratePublicKey().GetEncoded().CopyTo(result, 32);
        return result;
    }

    internal string Reference => Convert.ToHexStringLower(SHA256.HashData(PublicIdentity()))[..32];
    internal string WireguardPublicKey => Convert.ToBase64String(
        new X25519PrivateKeyParameters(Open(), 64).GeneratePublicKey().GetEncoded());

    internal byte[] EnrollmentProof(string challenge)
    {
        var bytes = Open();
        if (ControlProtocol.Base64(challenge, true).Length != 32)
            throw new FormatException("Invalid enrollment challenge");
        // This exact sorted ASCII schema is shared with device_identity.device and Android.
        var binding = new SortedDictionary<string, object>(StringComparer.Ordinal)
        {
            ["schema_version"] = 1,
            ["public_identity"] = Convert.ToBase64String(PublicIdentity()),
            ["wireguard_public_key"] = WireguardPublicKey,
            ["challenge"] = challenge,
            ["audience"] = Audience,
            ["transport"] = "wireguard"
        };
        var body = JsonSerializer.SerializeToUtf8Bytes(binding, Json);
        var domain = Encoding.ASCII.GetBytes(Purpose);
        var signer = new Ed25519Signer();
        signer.Init(true, new Ed25519PrivateKeyParameters(bytes, 32));
        signer.BlockUpdate(domain, 0, domain.Length);
        signer.BlockUpdate(body, 0, body.Length);
        binding["signature"] = Convert.ToBase64String(signer.GenerateSignature());
        return JsonSerializer.SerializeToUtf8Bytes(binding, Json);
    }

    public void Dispose()
    {
        if (material is not null) CryptographicOperations.ZeroMemory(material);
        material = null;
    }
}
