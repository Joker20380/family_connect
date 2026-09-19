using System.Text.Json;
namespace FamilyConnect;

// LocalSystem broker facade. Network calls remain bounded and use persisted identity;
// only public invitation links and verified native grants leave this owner.
internal static class FriendsOwner
{
    internal static void Activate(string sid, string invitation, CancellationToken token)
    {
        using var identity = Store.FriendsIdentity(sid, true);
        using var client = new FriendsAccessClient(identity);
        client.Activate(invitation, token).GetAwaiter().GetResult();
    }
    internal static string Referral(string sid, CancellationToken token)
    {
        using var identity = Store.FriendsIdentity(sid, false);
        using var client = new FriendsAccessClient(identity);
        return client.Referral(token).GetAwaiter().GetResult();
    }
    internal static TcpGrant Tcp(string sid, string country, CancellationToken token)
    {
        using var identity = Store.FriendsIdentity(sid, false);
        using var client = new FriendsAccessClient(identity);
        // The Friends catalog uses update.pub, not the legacy activation signing key.
        var anchorPath = Path.Combine(AppContext.BaseDirectory, "update.pub");
        if (new FileInfo(anchorPath).Length > 128) throw new IOException("Invalid packaged anchor");
        var anchor = ControlProtocol.Base64(File.ReadAllText(anchorPath).Trim(), true);
        var config = FriendsConfigurationVault.Accept(Store.Root, sid, identity, anchor, country,
            (floor, hash) => client.Configuration(country, anchor, floor, hash, token).GetAwaiter().GetResult().Response);
        return FriendsCatalog.NativeTcp(config, identity.WireguardPublicKey);
    }
}
