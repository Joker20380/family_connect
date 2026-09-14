# Short matched HTTPS diagnosis — 2026-09-12

Repository baseline4cb1423 with uncommitted Stage5/GUI implementation preserved.
Diagnostic-only session; production code, profiles, keys, helpers, server, catalog
and release versions unchanged. No remote CI/commit/release/device install.
Installed TCP component0.1.0, Linux app0.2.7, published desktop0.2.9/catalog8,
gateway0.2.1 retain their previous versions. Prior402 Python tests are not a new
run in this session; only the two operator diagnostic scripts were syntax-checked.

## Question and method

Previous ready-TUN smoke passed DNS3/3 and routing/cleanup but HTTPS4/6, with two
curl28 timeouts. This follow-up compares direct and VPN paths to the same endpoints
without DNS/CDN selection changing inside the series.

Targets: numeric Cloudflare1.1.1.1 and api.ipify.org pinned to104.26.12.205, resolved
before connecting. Both TLS hostname/certificate checks remain enabled. Each run
uses3 rounds ×2 targets ×2 paths, sequential requests, alternating direct/TUN order.
No concurrency/load increase, packet capture, UDP fault, offload/MTU/timeout change.

- Python run: root SO_MARK64630 bypasses TUN for direct sockets; VPN sockets bind to
  fctcp75850269. Kernel route selection verified for both paths. Verified TLS with
  HTTP/1.1 and absolute5s request deadline. Returned direct egress differs from the
  gateway; every successful VPN response reports185.251.89.19.
- Curl run: actual installed curl8.18.0, original connect3s/total5s limits, pinned
  --resolve and IPv4; direct socket binds physical uplink via SO_BINDTODEVICE, VPN
  socket binds TUN. Route get with output-interface constraint verified direct
  selection. Every response negotiated HTTP/2; egress proof confirms separate paths.

Each run starts only from no active WG/AWG/TCP session or policy ownership conflict,
waits for TUN/routes/DNS readiness, and installs a120s systemd service-stop watchdog.
Existing installed service/profile only; no import, profile readout or deployment.
Both runs took approximately6 seconds including readiness/cleanup (24 requests total).

## Results

| Run | Direct | TUN | Median total direct / TUN | Maximum total direct / TUN |
|---|---|---|---|---|
| Python TLS/HTTP1.1 |6/6|6/6|0.290 /0.590s|0.352 /0.654s|
| curl TLS/HTTP2 |6/6|6/6|0.207 /0.577s|0.286 /0.627s|

Curl TUN local TCP acceptance was0.42–0.86ms; TLS completed0.343–0.472s after start.
These connect times describe the local TUN TCP stack, not gateway reachability.
Direct curl TLS completion was0.090–0.152s. `time_starttransfer` is curl's measurement;
Python `first_byte_s` records completion of HTTPResponse.begin (response headers),
so it must not be treated as a precise first-byte timestamp.

Outer ss snapshots: Python19 samples, up to7 SYN-SENT/57 ESTAB, retrans fields in14;
curl18 samples, up to12 SYN-SENT/58 ESTAB, retrans fields in18. These include background
full-tunnel connections and do not identify the external flow of an individual probe.
The presence of retrans fields is not a count of lost packets or a causal explanation
of the earlier curl timeouts. No payload/credentials or raw socket listing retained.

## Interpretation and remaining debt

**24/24 passed; previous timeouts did not reproduce.** Both HTTP1.1 and HTTP2 can work
under these short conditions. This does not prove a protocol-version cause, rule out
DNS in other cases, fix the earlier timeouts, or establish long-run reliability.
Pinning excluded resolver/CDN-address variability in these runs; the earlier numeric
Cloudflare timeout also shows why DNS alone cannot be assumed to explain all failures.

Do not increase timeouts or change offload/routing/transport parameters based on this
passing sample. TD-1 remains open: bounded failed-request/outer-flow attribution is
needed when the failure recurs. Long load/device campaigns remain deferred. Continue
Stage5 coordinated GUI/core packaging and scoped CI; AWG3.1 migration remains TD-2.
Independent control entry/alternate gateway acceptance remains Stage6.

## Cleanup and evidence

Both runs: service stopped, TUN absent, ownership marker absent, full IPv4/IPv6 rules
match pre-test baseline, table64630 empty, gateway route restored. Watchdog timers
stopped after verified cleanup. Script exit0 means cleanup succeeded; individual
connectivity success is recorded separately in each row and summary.

- [Python result](2026-09-12-matched-https-python.json)
- [Curl result](2026-09-12-matched-https-curl.json)
- Local operator scripts: `/tmp/fc-matched-https/run.py`, `curl-run.py`.

Changed files: this report, the two result JSON files, docs/STATUS.md, docs/PLAN.md,
docs/ROADMAP.ru.md and docs/README.md. No product-source change or binary rollback.
All existing uncommitted implementation work is retained.

Diagnostic script SHA256:

- `run.py`: `26f77562adf2b768c0c4dec35fb7abdbcff1671049c17af85669beddd665601f`
- `curl-run.py`: `4fd9cbc82e2c539154188cda6775ac0d79156ab11ec94afe15a6ca18236b2a52`
