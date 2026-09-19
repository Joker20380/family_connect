using System.Security.Cryptography;
using System.Text.Json;
using FamilyConnect;
using Org.BouncyCastle.Crypto.Parameters;

internal static class FriendsIdentityChecks
{
    internal static void Run()
    {
        using var fixture = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory,
            "fixtures", "desktop-friends-identity-v1.json")));
        var f = fixture.RootElement;
        if (!f.GetProperty("test_only").GetBoolean()) throw new Exception("Not a test fixture");
        var bytes = Convert.FromHexString(f.GetProperty("material").GetString()!);
        using var identity = ControlIdentity.Restore(bytes);
        var nonce = f.GetProperty("challenge").GetString()!;
        if (identity.Reference != f.GetProperty("reference").GetString()
            || Convert.ToBase64String(identity.PublicIdentity()) != f.GetProperty("public_identity").GetString()
            || identity.WireguardPublicKey != f.GetProperty("wireguard_public_key").GetString())
            throw new Exception("Python identity mismatch");
        using var proof = JsonDocument.Parse(identity.EnrollmentProof(nonce));
        if (!JsonElement.DeepEquals(proof.RootElement, f.GetProperty("proof")))
            throw new Exception("Python enrollment proof mismatch");
        var copy = identity.ExportForProtection();
        CryptographicOperations.ZeroMemory(copy);
        CryptographicOperations.ZeroMemory(bytes);
        if (identity.Reference != f.GetProperty("reference").GetString()) throw new Exception("Identity not cloned");
        foreach (var invalid in new[] { "", "bad", nonce + "\n", Convert.ToBase64String(new byte[31]) })
        {
            try { identity.EnrollmentProof(invalid); }
            catch (FormatException) { continue; }
            throw new Exception("Invalid nonce accepted");
        }
        var wg = RandomNumberGenerator.GetBytes(32);
        using var migrated = ControlIdentity.Create(wg);
        if (migrated.WireguardPublicKey != Convert.ToBase64String(
            new X25519PrivateKeyParameters(wg, 0).GeneratePublicKey().GetEncoded()))
            throw new Exception("Migration replaced existing WG key");
        using var restored = ControlIdentity.Restore(migrated.ExportForProtection());
        if (restored.Reference != migrated.Reference) throw new Exception("Identity changed on restore");
        identity.Dispose();
        try { identity.EnrollmentProof(nonce); }
        catch (ObjectDisposedException) { Console.WriteLine("Windows friends identity: Python proof, clone, nonce, WG preservation, restore and dispose passed."); return; }
        throw new Exception("Disposed identity usable");
    }
}
