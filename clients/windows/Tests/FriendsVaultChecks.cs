using System.Security.Cryptography;
using FamilyConnect;

internal static class FriendsVaultChecks
{
    internal static void Run()
    {
        if (!OperatingSystem.IsWindows()) { Console.WriteLine("SKIP Windows DPAPI vault runtime (non-Windows host)."); return; }
        var root = Path.Combine(Path.GetTempPath(), "fc-friends-vault-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        var key = RandomNumberGenerator.GetBytes(32);
        const string alice = "S-1-5-21-1-2-3-1001", bob = "S-1-5-21-1-2-3-1002";
        int creates = 0, checks = 0;
        byte[] Existing(bool create) { if (create) creates++; return key.ToArray(); }
        void Reject(Action action)
        {
            try { action(); }
            catch (Exception e) when (e is IOException or CryptographicException or ArgumentException) { checks++; return; }
            throw new Exception("Invalid identity state accepted");
        }
        try
        {
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, alice, false, Existing); });
            if (Directory.EnumerateFileSystemEntries(root).Any() || creates != 0) throw new Exception("Resume creates state");
            string reference;
            using (var identity = FriendsIdentityVault.Load(root, alice, true, Existing)) reference = identity.Reference;
            if (creates != 1) throw new Exception("Create count");
            string path = FriendsIdentityVault.IdentityPath(root, alice), marker = FriendsIdentityVault.MarkerPath(root, alice);
            var ciphertext = File.ReadAllBytes(path);
            using (var resumed = FriendsIdentityVault.Load(root, alice, false, Existing))
                if (resumed.Reference != reference) throw new Exception("Restart identity mismatch");
            Parallel.For(0, 8, _ => {
                if (!OperatingSystem.IsWindows()) throw new PlatformNotSupportedException();
                using var same = FriendsIdentityVault.Load(root, alice, true, Existing);
                if (same.Reference != reference) throw new Exception("Concurrent identity change");
            });
            if (creates != 1 || !File.ReadAllBytes(path).SequenceEqual(ciphertext)) throw new Exception("Resume replaced stored identity");
            using (var other = FriendsIdentityVault.Load(root, bob, true, Existing))
                if (other.Reference == reference) throw new Exception("Shared user identity");
            string otherPath = FriendsIdentityVault.IdentityPath(root, bob);
            File.WriteAllBytes(otherPath, ciphertext);
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, bob, true, Existing); });
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, alice, true, _ => RandomNumberGenerator.GetBytes(32)); });
            File.WriteAllBytes(path, new byte[] { 1, 2, 3 });
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, alice, true, Existing); });
            if (!File.ReadAllBytes(path).SequenceEqual(new byte[] { 1, 2, 3 })) throw new Exception("Corrupt identity overwritten");
            File.WriteAllBytes(path, ciphertext);
            File.Delete(path); // Simulated missing blob after interrupted creation/deletion.
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, alice, true, Existing); });
            if (File.Exists(path)) throw new Exception("Missing identity regenerated");
            File.WriteAllBytes(path, ciphertext);
            File.WriteAllText(marker, "invalid");
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, alice, true, Existing); });
            File.Delete(marker);
            Reject(() => { using var unused = FriendsIdentityVault.Load(root, alice, true, Existing); });
            if (File.Exists(marker)) throw new Exception("Missing marker recreated");
            Console.WriteLine($"Windows DPAPI friends vault: create/resume/concurrency, SID binding and {checks} fail-closed scenarios passed.");
        }
        finally { CryptographicOperations.ZeroMemory(key); Directory.Delete(root, true); }
    }
}
