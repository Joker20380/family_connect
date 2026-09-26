using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Text;
using Org.BouncyCastle.Crypto.Parameters;

namespace FamilyConnect;

// Called only by the storage owner under its protected root (LocalSystem broker in
// production). The caller supplies an owned key copy, never a UI-provided secret.
[SupportedOSPlatform("windows")]
internal static class FriendsIdentityVault
{
    static readonly object Gate = new();
    static readonly byte[] Marker = Encoding.ASCII.GetBytes("FC-FRIENDS-IDENTITY-1\n");
    internal static string IdentityPath(string root, string sid) => Path.Combine(root,
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(sid))) + ".friends-identity.dpapi");
    internal static string MarkerPath(string root, string sid) => IdentityPath(root, sid) + ".initialized";

    static bool Present(string path)
    {
        try
        {
            var attributes = File.GetAttributes(path);
            if ((attributes & (FileAttributes.Directory | FileAttributes.ReparsePoint)) != 0)
                throw new IOException("Unsafe identity entry");
            return true;
        }
        catch (FileNotFoundException) { return false; }
    }

    internal static bool HasState(string root, string sid) =>
        Present(IdentityPath(root, sid)) || Present(MarkerPath(root, sid));

    static byte[] ReadBounded(string path, int limit)
    {
        using var file = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        if (file.Length < 1 || file.Length > limit) throw new IOException("Invalid identity size");
        var data = new byte[(int)file.Length];
        file.ReadExactly(data);
        if (file.ReadByte() != -1) throw new IOException("Identity changed during read");
        return data;
    }

    static void WriteNew(string path, byte[] data)
    {
        var temporary = Path.Combine(Path.GetDirectoryName(path)!, Guid.NewGuid().ToString("N") + ".friends.tmp");
        try
        {
            using (var file = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            { file.Write(data); file.Flush(true); }
            File.Move(temporary, path, false); // Never replace another writer's identity.
        }
        finally { File.Delete(temporary); }
    }

    internal static ControlIdentity Load(string root, string sid, bool create, Func<bool, byte[]> wireguardKey)
    {
        lock (Gate)
        {
            var directory = new DirectoryInfo(root);
            if (!directory.Exists || (directory.Attributes & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Unsafe identity root");
            string path = IdentityPath(root, sid), marker = MarkerPath(root, sid);
            bool exists = Present(path), marked = Present(marker);
            // Mark the first creation before storing a usable identity. Interrupted
            // creation/deletion must not silently mint a new remotely-bound identity.
            if (exists != marked) throw new IOException("Identity recovery required");
            if (!exists && !create) throw new FileNotFoundException("Identity not enrolled");
            if (marked && !ReadBounded(marker, Marker.Length).SequenceEqual(Marker))
                throw new IOException("Invalid identity marker");
            var key = wireguardKey(!exists && create);
            var entropy = SHA256.HashData(Encoding.UTF8.GetBytes("family-connect/friends-identity/v1\0" + sid));
            byte[]? plaintext = null;
            ControlIdentity? identity = null;
            try
            {
                if (key.Length != 32) throw new IOException("Invalid existing WG key");
                if (exists)
                {
                    plaintext = ProtectedData.Unprotect(ReadBounded(path, 4096), entropy, DataProtectionScope.CurrentUser);
                    identity = ControlIdentity.Restore(plaintext);
                    var expected = Convert.ToBase64String(new X25519PrivateKeyParameters(key, 0).GeneratePublicKey().GetEncoded());
                    if (identity.WireguardPublicKey != expected) throw new IOException("WG identity mismatch");
                }
                else
                {
                    identity = ControlIdentity.Create(key);
                    plaintext = identity.ExportForProtection();
                    var ciphertext = ProtectedData.Protect(plaintext, entropy, DataProtectionScope.CurrentUser);
                    WriteNew(marker, Marker);
                    WriteNew(path, ciphertext);
                }
                var result = identity;
                identity = null;
                return result!;
            }
            finally
            {
                identity?.Dispose();
                CryptographicOperations.ZeroMemory(key);
                if (plaintext is not null) CryptographicOperations.ZeroMemory(plaintext);
            }
        }
    }
}
