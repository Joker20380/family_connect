using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using FamilyConnect;

internal static class FriendsAccessChecks
{
    sealed class Handler(Func<HttpRequestMessage, HttpResponseMessage> respond) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken token)
            => Task.FromResult(respond(request));
    }
    static HttpResponseMessage Json(object value) => new(HttpStatusCode.OK) {
        Content = new StringContent(JsonSerializer.Serialize(value), Encoding.UTF8, "application/json") };

    internal static async Task Run()
    {
        using var identity = ControlIdentity.Restore(Enumerable.Range(0, 96).Select(i => (byte)i).ToArray());
        string nonce = Convert.ToBase64String(Enumerable.Range(0, 32).Select(i => (byte)i).ToArray());
        int proofs = 0;
        var handler = new Handler(request => {
            string path = request.RequestUri!.AbsolutePath;
            if (path == "/friends/challenge") return Json(new { challenge = nonce, expires_at = 1120,
                audience = "family-connect/enrollment/v1" });
            using var body = JsonDocument.Parse(request.Content!.ReadAsStringAsync().GetAwaiter().GetResult());
            using var expected = JsonDocument.Parse(identity.EnrollmentProof(nonce));
            if (!JsonElement.DeepEquals(body.RootElement, expected.RootElement)) throw new Exception("Proof not sent");
            proofs++;
            return path == "/friends/activate" ? Json(new { device = identity.Reference, status = "active" })
                : Json(new { url = "https://185.251.89.19:8443/invite/#" + new string('a', 64), pool_limit = 500, remaining = 499 });
        });
        using (var client = new FriendsAccessClient(identity, handler, () => 1000))
        {
            await client.Activate("FC-" + new string('A', 32));
            if (!(await client.Referral()).EndsWith(new string('a', 64)) || proofs != 2)
                throw new Exception("Activation/referral mismatch");
        }
        int rejected = 0;
        async Task Reject(Func<HttpRequestMessage, HttpResponseMessage> reply, string code)
        {
            using var client = new FriendsAccessClient(identity, new Handler(reply), () => 1000);
            try { await client.Referral(); }
            catch (FriendsAccessError e) when (e.Message == code) { rejected++; return; }
            throw new Exception("Bad response accepted");
        }
        await Reject(_ => new(HttpStatusCode.TemporaryRedirect) { Headers = { Location = new Uri("https://example.com/") } }, "service_unavailable");
        await Reject(_ => new(HttpStatusCode.Forbidden), "access_rejected");
        await Reject(_ => Json(new { challenge = nonce, expires_at = 1000, audience = "family-connect/enrollment/v1" }), "invalid_response");
        await Reject(_ => Json(new { challenge = nonce, expires_at = 1121, audience = "family-connect/enrollment/v1" }), "invalid_response");
        await Reject(_ => Json(new { challenge = nonce, expires_at = 1120, audience = "other" }), "invalid_response");
        await Reject(_ => new(HttpStatusCode.OK) { Content = new StringContent("{\"x\":1,\"x\":2}") }, "invalid_response");
        await Reject(_ => new(HttpStatusCode.OK) { Content = new StringContent(new string('x', 65537)) }, "invalid_response");
        if (identity.Reference.Length != 32) throw new Exception("Client disposed owner identity");
        Console.WriteLine($"Windows friends HTTP: activation/referral and {rejected} rejection checks passed.");
    }
}
