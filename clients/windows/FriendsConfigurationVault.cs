using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace FamilyConnect;

// Trusted root and validated SID supplied by the LocalSystem owner, never by a UI request.
// Returned credentials are for native materialization only, not a pipe reply.
[SupportedOSPlatform("windows")]
internal static class FriendsConfigurationVault
{
    static readonly object Gate = new();
    static readonly byte[] Marker = Encoding.ASCII.GetBytes("FC-FRIENDS-CONFIGURATION-1\n");
    internal static string ConfigPath(string root, string sid) => Path.Combine(root,
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(sid))) + ".friends-configuration.dpapi");
    static bool Present(string path)
    {
        try { var a = File.GetAttributes(path); if ((a & (FileAttributes.ReparsePoint | FileAttributes.Directory)) != 0) throw new IOException("Unsafe configuration entry"); return true; }
        catch (FileNotFoundException) { return false; }
    }
    static byte[] Read(string path, int limit)
    {
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        if (stream.Length < 1 || stream.Length > limit) throw new IOException("Invalid configuration size");
        var result = new byte[(int)stream.Length]; stream.ReadExactly(result);
        if (stream.ReadByte() != -1) throw new IOException("Configuration changed");
        return result;
    }
    static void Write(string path, byte[] raw, bool replace)
    {
        string tmp = Path.Combine(Path.GetDirectoryName(path)!, Guid.NewGuid().ToString("N")+".friends.tmp");
        try
        {
            using (var stream = new FileStream(tmp, FileMode.CreateNew, FileAccess.Write, FileShare.None)) { stream.Write(raw); stream.Flush(true); }
            if (replace) File.Replace(tmp, path, null); else File.Move(tmp, path, false);
        }
        finally { File.Delete(tmp); }
    }
    internal static FriendsConfiguration Accept(string root, string sid, ControlIdentity identity, byte[] anchor,
        string country, Func<long, string?, JsonElement> fetch)
    {
        lock (Gate)
        {
            if (country is not ("ru" or "nl")) throw new FormatException("Invalid country");
            var directory = new DirectoryInfo(root);
            if (!directory.Exists || (directory.Attributes & FileAttributes.ReparsePoint) != 0) throw new IOException("Unsafe configuration root");
            string path = ConfigPath(root, sid), marker = path+".initialized";
            bool exists = Present(path), marked = Present(marker);
            if (exists != marked) throw new IOException("Configuration recovery required");
            var entropy = SHA256.HashData(Encoding.UTF8.GetBytes("family-connect/friends-configuration/v1\0"+sid));
            byte[]? raw = null; var key = identity.WireguardPrivateKey();
            try
            {
                var cache = new Dictionary<string, JsonElement>();
                long floor = 0; string? hash = null;
                if (exists)
                {
                    if (!Read(marker, Marker.Length).SequenceEqual(Marker)) throw new IOException("Invalid configuration marker");
                    raw = ProtectedData.Unprotect(Read(path, 131072), entropy, DataProtectionScope.CurrentUser);
                    if (raw.Length > 65536) throw new IOException("Invalid configuration size");
                    var saved = ControlProtocol.Parse(raw); ControlProtocol.Require(saved.ValueKind == JsonValueKind.Object);
                    foreach (var item in saved.EnumerateObject())
                    {
                        var profile = FriendsCatalog.Verify(item.Value, anchor, identity.Reference, item.Name, key);
                        cache.Add(item.Name, item.Value);
                        if (profile.Sequence > floor) { floor = profile.Sequence; hash = profile.CatalogHash; }
                        else if (profile.Sequence == floor && profile.CatalogHash != hash) throw new IOException("Conflicting catalogs");
                    }
                    if (cache.Count is < 1 or > 2) throw new IOException("Invalid configuration cache");
                    CryptographicOperations.ZeroMemory(raw); raw = null;
                }
                var response = fetch(floor, hash);
                var accepted = FriendsCatalog.Verify(response, anchor, identity.Reference, country, key, floor, hash);
                cache[country] = response;
                raw = JsonSerializer.SerializeToUtf8Bytes(cache);
                if (raw.Length > 65536) throw new IOException("Invalid configuration size");
                var encrypted = ProtectedData.Protect(raw, entropy, DataProtectionScope.CurrentUser);
                if (!marked) Write(marker, Marker, false);
                Write(path, encrypted, exists);
                return accepted; // Durable save must succeed before caller can apply anything.
            }
            finally { CryptographicOperations.ZeroMemory(key); if (raw is not null) CryptographicOperations.ZeroMemory(raw); }
        }
    }
}
