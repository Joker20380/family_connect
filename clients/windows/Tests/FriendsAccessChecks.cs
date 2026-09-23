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
        int proofs = 0, claims = 0;
        var handler = new Handler(request => {
            string path = request.RequestUri!.AbsolutePath;
            if(path=="/friends/referral/claim"){
                using var claim=JsonDocument.Parse(request.Content!.ReadAsStringAsync().GetAwaiter().GetResult());
                if(claim.RootElement.GetProperty("request_id").GetString()!=identity.Reference||claim.RootElement.GetProperty("token").GetString()!=new string('a',64))throw new Exception("Incorrect invitation claim");
                claims++;return Json(new{invitation="FC-"+string.Join("-",Enumerable.Repeat("ABCD",8)),status="issued"});
            }
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
            await client.Register(invitationToken:new string('a',64));
            await client.Register();
            if (!(await client.Referral()).EndsWith(new string('a', 64)) || proofs != 4 || claims != 1)
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
        await Reject(_ => new(HttpStatusCode.TooManyRequests), "rate_limited");
        await Reject(_ => throw new TaskCanceledException(), "request_timeout");
        await Reject(_ => throw new HttpRequestException(HttpRequestError.SecureConnectionError), "tls_failed");
        await Reject(_ => throw new HttpRequestException(HttpRequestError.ConnectionError), "network_unavailable");
        await Reject(_ => new(HttpStatusCode.ServiceUnavailable), "service_unavailable");
        await Reject(_ => Json(new { challenge = nonce, expires_at = 1000, audience = "family-connect/enrollment/v1" }), "invalid_response");
        await Reject(_ => Json(new { challenge = nonce, expires_at = 1121, audience = "family-connect/enrollment/v1" }), "invalid_response");
        await Reject(_ => Json(new { challenge = nonce, expires_at = 1120, audience = "other" }), "invalid_response");
        await Reject(_ => new(HttpStatusCode.OK) { Content = new StringContent("{\"x\":1,\"x\":2}") }, "invalid_response");
        await Reject(_ => new(HttpStatusCode.OK) { Content = new StringContent(new string('x', 65537)) }, "invalid_response");
        if (identity.Reference.Length != 32) throw new Exception("Client disposed owner identity");
        using var catalogFixture = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(AppContext.BaseDirectory,"fixtures","desktop-friends-catalog-v2.json")));
        var fixture = catalogFixture.RootElement;
        var anchor = Convert.FromBase64String(fixture.GetProperty("anchor").GetString()!);
        foreach(var failure in new[] { "", "device", "signature", "country", "denied" })
        {
            int requests = 0;
            var reply = System.Text.Json.Nodes.JsonNode.Parse(fixture.GetProperty("vectors")[0].GetProperty("reply").GetRawText())!;
            reply["device"] = failure == "device" ? new string('0',32) : identity.Reference;
            if(failure == "country")reply["country"] = "ru";
            if(failure == "signature")reply["catalog"]!["signature"] = Convert.ToBase64String(new byte[64]);
            using var client = new FriendsAccessClient(identity, new Handler(request => {
                requests++;
                using var body = JsonDocument.Parse(request.Content!.ReadAsStringAsync().GetAwaiter().GetResult());
                if(request.RequestUri!.AbsolutePath == "/friends/challenge")
                {
                    if(body.RootElement.GetProperty("purpose").GetString() != "nl")throw new Exception("Wrong purpose");
                    return Json(new { challenge=nonce, expires_at=1120, audience="family-connect/enrollment/v1" });
                }
                if(request.RequestUri.AbsolutePath != "/friends/configuration/nl")throw new Exception("Wrong path");
                if(failure == "denied")return new(HttpStatusCode.Forbidden);
                return Json(reply);
            }), () => 1000);
            bool accepted=false;
            try { var result=await client.Configuration("nl", anchor); accepted=true; if(result.Profile.Address!="10.83.0.2/32")throw new Exception("Wrong assignment"); }
            catch(FriendsAccessError e) when(e.Message == (failure == "denied" ? "access_rejected" : "invalid_response")) { }
            if(accepted != (failure == "") || requests != 2)throw new Exception("Configuration HTTP verification mismatch");
            try { await client.Configuration("../ru",anchor); throw new Exception("Invalid country accepted"); }
            catch(FriendsAccessError e) when(e.Message=="invalid_input") { }
            if(requests!=2)throw new Exception("Invalid input sent to network");
        }
        Console.WriteLine($"Windows friends HTTP: activation/referral and {rejected} rejection checks passed.");
    }
}
