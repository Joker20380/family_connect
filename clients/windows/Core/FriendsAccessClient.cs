using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace FamilyConnect;

internal sealed class FriendsAccessError(string code) : Exception(code);

// Used off the UI thread by the persisted identity owner. No key creation or VPN apply.
internal sealed class FriendsAccessClient : IDisposable
{
    readonly HttpClient http;
    readonly ControlIdentity identity;
    readonly Func<long> clock;
    const int Limit = 65536;
    internal FriendsAccessClient(ControlIdentity identity, Func<long>? clock = null)
        : this(identity, new HttpClientHandler { AllowAutoRedirect = false }, clock) { }

    // Handler injection is for isolated tests; the production constructor disables redirects.
    internal FriendsAccessClient(ControlIdentity identity, HttpMessageHandler handler, Func<long>? clock = null)
    {
        this.identity = identity;
        this.clock = clock ?? (() => DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        http = new HttpClient(handler) { BaseAddress = new Uri("https://185.251.89.19:8443"),
            Timeout = TimeSpan.FromSeconds(12) };
    }

    async Task<JsonElement> Post(string path, object body, CancellationToken token)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(token);
        deadline.CancelAfter(TimeSpan.FromSeconds(12));
        var requestToken = deadline.Token;
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, path);
            request.Content = new ByteArrayContent(JsonSerializer.SerializeToUtf8Bytes(body));
            request.Content.Headers.ContentType = new("application/json");
            using var response = await http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, requestToken);
            if (response.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden or HttpStatusCode.Conflict)
                throw new FriendsAccessError("access_rejected");
            if (response.StatusCode == HttpStatusCode.TooManyRequests)
                throw new FriendsAccessError("rate_limited");
            if (response.StatusCode != HttpStatusCode.OK) throw new FriendsAccessError("service_unavailable");
            await using var stream = await response.Content.ReadAsStreamAsync(requestToken);
            using var buffer = new MemoryStream();
            var chunk = new byte[4096];
            int count;
            while ((count = await stream.ReadAsync(chunk, requestToken)) > 0)
            {
                if (buffer.Length + count > Limit) throw new FriendsAccessError("invalid_response");
                buffer.Write(chunk, 0, count);
            }
            return ControlProtocol.Parse(buffer.ToArray());
        }
        catch (FriendsAccessError) { throw; }
        catch (OperationCanceledException) when (token.IsCancellationRequested) { throw; }
        catch (OperationCanceledException) { throw new FriendsAccessError("request_timeout"); }
        catch (HttpRequestException e) when (e.HttpRequestError == HttpRequestError.SecureConnectionError)
        { throw new FriendsAccessError("tls_failed"); }
        catch (HttpRequestException) { throw new FriendsAccessError("network_unavailable"); }
        catch (Exception e) when (ControlProtocol.Invalid(e)) { throw new FriendsAccessError("invalid_response"); }
        catch (Exception) { throw new FriendsAccessError("service_unavailable"); }
    }

    async Task<JsonElement> Proof(string purpose, string invitation, CancellationToken token)
    {
        var challenge = await Post("/friends/challenge", new {
            public_identity = Convert.ToBase64String(identity.PublicIdentity()),
            wireguard_public_key = identity.WireguardPublicKey, purpose, invitation
        }, token);
        try
        {
            ControlProtocol.Fields(challenge, "challenge expires_at audience");
            long now = clock(), until = ControlProtocol.Integer(challenge.GetProperty("expires_at"), 1);
            if (until <= now || until - now > 120 || challenge.GetProperty("audience").GetString() != "family-connect/enrollment/v1")
                throw new FormatException();
            return ControlProtocol.Parse(identity.EnrollmentProof(ControlProtocol.Text(challenge.GetProperty("challenge"))));
        }
        catch (Exception e) when (ControlProtocol.Invalid(e)) { throw new FriendsAccessError("invalid_response"); }
    }

    internal async Task Activate(string invitation, CancellationToken token = default)
    {
        if (invitation is null || invitation.Length > 128) throw new FriendsAccessError("invalid_invitation");
        var normalized = invitation.Trim().ToUpperInvariant().Replace("-", "");
        if (normalized.StartsWith("FC", StringComparison.Ordinal)) normalized = normalized[2..];
        if (!Regex.IsMatch(normalized, "\\A[0-9A-F]{32}\\z")) throw new FriendsAccessError("invalid_invitation");
        var result = await Post("/friends/activate", await Proof("activate", invitation, token), token);
        try
        {
            ControlProtocol.Fields(result, "device status");
            if (result.GetProperty("device").GetString() != identity.Reference || result.GetProperty("status").GetString() != "active")
                throw new FormatException();
        }
        catch (Exception e) when (ControlProtocol.Invalid(e)) { throw new FriendsAccessError("invalid_response"); }
    }

    internal async Task Register(CancellationToken token = default, string invitationToken = "")
    {
        string invitation="";
        if(invitationToken.Length>0){
            if(!System.Text.RegularExpressions.Regex.IsMatch(invitationToken,@"\A[0-9a-f]{64}\z"))throw new FriendsAccessError("access_rejected");
            var claim=await Post("/friends/referral/claim",new{token=invitationToken,request_id=identity.Reference},token);
            try{
                ControlProtocol.Fields(claim,"invitation status");
                invitation=claim.GetProperty("invitation").GetString()??"";
                if(!System.Text.RegularExpressions.Regex.IsMatch(invitation,@"\AFC-(?:[A-F0-9]{4}-){7}[A-F0-9]{4}\z") || claim.GetProperty("status").GetString() is not ("issued" or "activated"))throw new FormatException();
            }catch(Exception e) when(ControlProtocol.Invalid(e)){throw new FriendsAccessError("invalid_response");}
        }
        var result=await Post("/friends/activate",await Proof("activate",invitation,token),token);
        try {
            ControlProtocol.Fields(result,"device status");
            if(result.GetProperty("device").GetString()!=identity.Reference || result.GetProperty("status").GetString()!="active")throw new FormatException();
        } catch(Exception e) when(ControlProtocol.Invalid(e)){throw new FriendsAccessError("invalid_response");}
    }

    internal async Task<string> Referral(CancellationToken token = default)
    {
        var result = await Post("/friends/referral/issue", await Proof("refer", "", token), token);
        try
        {
            ControlProtocol.Fields(result, "url pool_limit remaining");
            var url = ControlProtocol.Text(result.GetProperty("url"));
            if (!Regex.IsMatch(url, "\\Ahttps://185\\.251\\.89\\.19:8443/invite/#[0-9a-f]{64}\\z")
                || ControlProtocol.Integer(result.GetProperty("pool_limit"), 1) != 500
                || ControlProtocol.Integer(result.GetProperty("remaining")) > 500)
                throw new FormatException();
            return url;
        }
        catch (Exception e) when (ControlProtocol.Invalid(e)) { throw new FriendsAccessError("invalid_response"); }
    }

    internal async Task<(JsonElement Response, FriendsConfiguration Profile)> Configuration(
        string country, byte[] anchor, long floor = 0, string? previousHash = null, CancellationToken token = default)
    {
        if (country is not ("ru" or "nl")) throw new FriendsAccessError("invalid_input");
        var response = await Post("/friends/configuration/" + country, await Proof(country, "", token), token);
        var privateKey = identity.WireguardPrivateKey();
        try { return (response, FriendsCatalog.Verify(response, anchor, identity.Reference, country, privateKey, floor, previousHash)); }
        catch (FormatException) { throw new FriendsAccessError("invalid_response"); }
        finally { System.Security.Cryptography.CryptographicOperations.ZeroMemory(privateKey); }
    }

    public void Dispose() => http.Dispose(); // The caller retains ownership of the identity.
}
