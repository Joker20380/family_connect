# FULL-TUNNEL-EGRESS-VERIFY-1 — physical operator episode, 2026-10-11

## Result and scope

**FULL_TUNNEL_EGRESS_PROVEN.** Ordinary Android test-app IPv4 HTTPS traffic
uses Android TUN → Telemost → NL gateway. The controlled endpoint sees the
gateway's public source IP, **AS57043 HOSTKEY (`186.246.*.*`)**, not the previously
verified VPN-OFF **AS47377 Orange Belgium (`94.*`)** source.

This is an actual ordinary-socket round trip, not READY, an internal Family API,
a messenger route, native harness or gateway-originated substitute. Two distinct
nonces receive complete TLS1.3/HTTPS responses. The controlled DNS lookup also
reaches the gateway and returns a valid answer. No product change was made.

This does **not** establish browser behavior, IPv6 egress, leak-free recovery,
uninterrupted connectivity, arbitrary UDP/QUIC support or real whitelist FIELD.
Two unexpected closes occur later; both automatically recover. Their cause remains
open. Provisioning remains a separate blocking direct-network dependency.

## Acceptance matrix

| TEST | RESULT |
|---|---|
| Harness lifecycle | PASS — existing A/B/onNewIntent/timeout/replay evidence reused; actual executions1/2/3 in same process |
| OPERATOR_CONNECT | PASS — one physical CONNECT, zero injected events |
| ANDROID_FULL_VPN | PASS — actual framework VPN + TUN + dedicated READY |
| ACTIVE_CARRIER | TELEMOST — explicit selection, restricted native session |
| TEST_APP_REQUEST | PASS — IPv4 and normal HTTPS, fresh nonces, complete responses |
| TUN_CAPTURE | PASS — ordinary socket TUN address/port, inclusive UID routes, matched native Mux destination/session |
| NL_GATEWAY_CORRELATION | PASS — streams5/7, exact session tag, timed outbound SYN/return tuples, endpoint source ports/nonces |
| REMOTE_SOURCE_ASN | AS57043 HOSTKEY; masked IPv4 `186.246.*.*` |
| IPV4_EGRESS | GATEWAY |
| BROWSER_EGRESS | NOT_RUN — no reserved nonce or destination-port traffic within180s |
| DNS_EGRESS | GATEWAY — one controlled lookup; not every Android/browser DNS mode |
| PER_APP_ROUTING | TEST_APP_PASS_BROWSER_NOT_RUN; broad cross-app claim remains unverified |
| IPV6_EGRESS | UNAVAILABLE — no global underlay IPv6 before CONNECT |
| IPV6_LEAK | NOT_APPLICABLE_FOR_THIS_EPISODE — not an IPv6 PASS |
| FAILOVER_LEAK | NOT_TESTED — no ordinary test request during RESTORING |
| Lease renewal preserved | PASS for unchanged bytes/prior evidence; current live renewal NOT_RUN |
| Provisioning whitelist dependency | DIRECT_REQUIRED |
| FULL_TUNNEL_EGRESS | PROVEN |
| WHITELIST_WARM_START_READY | NO when provisioning endpoint is unavailable |
| WHITELIST_COLD_START_READY | NO when provisioning endpoint is unavailable |
| WHITELIST_ARCHITECTURE_READY | NO for that whitelist model |
| REAL_RESTRICTED_NETWORK_FIELD | NOT_RUN |

UNDERLAY_STATE is cellular IPv4; the established Orange baseline is reused without
another phone baseline request. FULL_VPN_STATE is established during acceptance,
OFF after cleanup. MESSENGER_ROUTE is DIRECT, separately observed; this is neither
the full VPN route nor evidence against the proven ordinary-app route.

## Frozen identities and trust

Fresh device/runtime checks precede preparation and follow cleanup. Exact identities:

| Item | Identity |
|---|---|
| Package / UID | `com.familyconnect.app.friends` / `10283` |
| Installed version | `0.1.18-research82-lease` / code82 |
| APK SHA256 | `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Source | `fbbecb81c033557f6c29819a02b8382519465961` |
| Source tree | `06ca3d03620fc773d4bbb1528e2a0f193d7727a5` |
| Restricted native SHA256 | `743080ad01481ef2e839a1e4e92619a32956bb52bf85c7b666e6ac0ac51e8664` |
| Gateway loaded AND next | `34704e26029bf1eee4ae7679712c673eec7989b291f1a6f47c87c2b40973d958` |
| Gateway PID / invocation | `415430` / `3d9e1d2923a5423e9a11afbed13648de` |
| Directory SHA256 | `af4848c3d1fc83f60c4b38794312c974449126ae436f2914d62dbbf0c82f2041` |
| Served Family leaf SHA256 | `b347b452a5c64417cfc1d8d9c530c56783a71d274cfebde8c4a6989b66535c5f` |
| Authority SHA256 | `d5a0d0dba0a90c6cedaf5365007edebd2e75257a0c05e4453b8fde5f1959dc18` |

Installed embedded `restricted-build.json` was extracted again: schema2,
providerTelemost, diagnostic_only=false, build_tags=[], fault_schema0, exact source,
native, pinned Xray/gVisor/patch/builder identities retained in the receipt.
No APK/native/gateway build, signer operation, deployment or version change.
Saved research82 checkout has no new runtime diff. Main dirty work is preserved.

Directory issued08:46:42.429UTC, expires12:46:38.409UTC; served leaf expires12:45:48.
Pre-arm minimum server/security headroom3456s; final leaf headroom2723s.
Entry/armed/final preflights PASS, active directory/publication and chain unchanged.
Live CRL/floor advances21343→21350→21372; revision floor1. Floors are not frozen
or rolled back. Preflight server-chain validity alone is not called client auth;
actual foreground refresh SUCCESS, FAMILY_AUTH_READY and session establishment
provide the live client-authentication evidence. No manual credential renewal.

## Prepared harness and physical gate

Existing separate probe APK SHA256
`08513088e63fe924a2df6c04926bada9147b8f0ad4116ca384d914b5579e08c5`
and read-only owner-observer APK SHA256
`0eaa93cd1e9e1ac689413d3a1cda33e56dc965996e8a63bef80db3a4a918a3a7`
were installed unchanged; no signing/rebuild. Helper UIDs10410/10411; product UID
unchanged. Prior local lifecycle proof covers A/B exactly once, same process,
onNewIntent, timeout, following run success and replay rejection; no redundant redo.

TEST_APP_READY, OBSERVER_READY, GATEWAY_COLLECTOR_READY, EGRESS_ENDPOINT_READY all
precede the literal manual CONNECT gate. Unique runs are ARMED only, without early
network execution. Operator chooses existing Telemost/NL/full VPN and physically
connects once. Observer has no CONNECT/DISCONNECT capability; no input injection,
accessibility workaround, permission modification or programmatic Chrome launch.

Physical startup11:48:50.435UTC → full CONNECTED11:49:15.441; observer VPN_READY
11:49:15.508. Gate additionally requires CONNECTED, vpn_capture_open,
restricted_readiness READY, native_state2, VALID session correlation and successful
startup. Framework VPN network258/tun1 corroborates it, not just the VPN icon.

## Ordinary app → TUN → gateway → endpoint → app

Runtime: tun1 addresses `10.79.0.2/32`, `fd79:fc::2/128`; MTU1280; IPv4 `0.0.0.0/0`
and IPv6 `::/0`; DNS `10.79.0.1`; UID range0–99999 includes probe10410;
bypassable=false; underlying cellular network255. Test app uses default Java Socket
and default TLS socket factory with endpoint verification, not protected/bound
sockets, NOT_VPN network selection or internal Family/Mux APIs.

| Request | App interval UTC | TUN source port | Mux stream | NL SYN UTC | Response |
|---|---|---|---|---|---|
| FULL-V4 | 11:49:16.316–11:49:17.559 | 40172 | 5 | 11:49:16.482679 | 492bytes complete |
| FULL-NORMAL | 11:49:17.638–11:49:19.725 | 49198 | 7 | 11:49:17.775694 | 500bytes complete |

Both ordinary sockets have local address10.79.0.2, VPN=true and the observed TUN
LinkProperties. Distinct endpoint destination ports identify these requests, not
chat/provisioning/background counters. Both Mux opens use the same Mux object and
Telemost session `5a7608d3…e121309`, matching the client session.

Gateway-interface SYN and bidirectional TCP tuple, including source port, match
each endpoint receipt. Converted Mux timestamps precede corresponding wire SYNs by
0.371ms/0.302ms. Endpoint nonce and source tuple match the fully returned app JSON.
Full run IDs, request nonces, times, ports, exact session tags and IPs are retained
privately. Nonce mapping is explicit: app run_id is32hex; URL/request_nonce is
FULL-V4-/FULL-NORMAL- plus that ID; response nonce preserves the app's existing ID
contract. No payload logging, cookies or user tracking.

The initial automated reader unnecessarily required an additional syscall event;
that optional probe emitted none, so its raw receipt says UNKNOWN. It did **not**
lose the required correlation: both exact Mux/session opens, wire SYN/return tuples,
endpoint source ports/nonces and app responses were already captured. Read-only
reconciliation of those same records plus gateway wall/monotonic calibration proves
the chain. Original raw receipt is retained, not rewritten; no request or CONNECT
was repeated. Missing syscall probe output is not represented as collected data.

“Normal HTTPS” uses the normal/dual-family listener at a literal IPv4 URL; it is not
a hostname/Happy-Eyeballs test. Browser nonce has its own URL/port. During the180s
manual browser window, neither that nonce nor its gateway port appears; browser
confirmation is NOT_RUN, not a failed browser routing assertion.

## DNS, IPv6 and excluded claims

Controlled DNS11:51:24.371–11:51:25.394: ordinary unbound DatagramSocket from
10.79.0.2:43916 to advertised TUN DNS10.79.0.1, fresh32hex qname, gateway MUX_DNS
request20 on the same session, successful89-byte answer (rcode0, one answer).
This establishes the specific query's gateway path, not a generic counter increase.
Frozen gateway exchangeDNS uses TCP to the first resolver in `/etc/resolv.conf`:
NL systemd-resolved stub127.0.0.53; configured recursive candidates1.1.1.1/8.8.4.4.
Which recursive upstream answered this query was not separately packet-captured.
Private DNS mode/specifier are unchanged (read setting null); no universal DoT/DoH
claim is made from the explicit controlled query. No direct Orange DNS demonstrated.

No global underlay IPv6 was present before CONNECT; no IPv6 nonce sent. Both routes
are present, but this episode is not an IPv6 egress/leak PASS. No live carrier fault
injection or extra app requests during recovery. Existing local fail-closed contract
remains prior evidence, not a new live leak-free recovery result.

## Unexpected closes and automatic recovery

After successful HTTPS and DNS, two natural first-closes are retained:

| First close UTC | Observed mechanism | Automatic CONNECTED UTC |
|---|---|---|
| 11:54:03.755 | RELIABLE_RETRY_EXHAUSTED / RELIABLE_EXHAUSTION | 11:54:42.302 |
| 11:58:52.522 | RELIABLE_RETRY_EXHAUSTED / RELIABLE_EXHAUSTION | 12:00:01.990 |

Same UI connection ID, new native session tags; exactly one initial operator
CONNECT and no manual reconnect. Both old histories and diagnostic first-close
delivery state are saved. This identifies a terminal mechanism, **not its root
cause**, and does not recategorize historical incidents as lease expiry. A bounded
gateway-journal read timed out; no server-side causal attribution is invented.
No code/config/retry/pacing/renewal change or retry-until-green followed.
No accepted renewal was required/observed before these session closes; previous
research82 two-renewal proof is preserved, not repeated or contradicted by assumption.
Six historical negative-auth diagnostic assertion failures remain separate/open.

## Cleanup, preservation and next work

Evidence is saved before stopping test resources. First180s disconnect wait ends
while automatic restoration is in progress. Later ordinary CANCELLED transition
12:00:31.093 → VPN_RELEASED12:00:31.394 → DISCONNECTED12:00:31.424 is observed;
no programmatic disconnect. Read-only observer finishes only after confirmed OFF.
Final12:01:12.151UTC receipt: **VPN OFF, app ON, ChatDeliveryService ON**.
Instrumentation startup/finish can restart the owner process; uninterrupted chat
service uptime is not claimed, final service restoration is verified.

Temporary endpoint/listeners/firewall rules/BPF/TCP collectors/staging removed.
Gateway same PID/invocation, loaded/next bytes and NRestarts0; no extra restart.
Two helpers retained installed idle, instrumentation stopped: uninstall was forbidden.
Product UID/data/cache/enrollment/AWG/publisher/history preserved. Prior163+124
manifest files rehashed unchanged. Total controlled app response payload1081bytes;
no speedtest or network scan. No public release/APK distribution/real restricted FIELD.

Evidence root:
`state-client-build/field65-export16/full-tunnel-egress-verify-1-manual/`.
Canonical `RESULT.json`, `research-manifest.json`, exact private records and receipts
are retained. Principal receipts: `scenario-armed`, `manual-gate`, `ready-gate`,
`app-egress-proof` (raw conservative result), `app-correlated-pass` (complete wire
join), `dns-result`, `browser-result`, `final-integrity`, final owner/preflight/cleanup.

Retained regression workflow: unchanged prior probe/owner APKs; current `device.py`,
`observer.py`, `owner_reader.py`; prepare/arm then `manual.py live` with physical
operator gate only; `reconcile.py` analyzes captured tuples without another request;
`dns_once.py` requires the still-ARMED DNS run; `browser_wait.py` observes a manual
URL; physical disconnect precedes `cleanup_device.py`. Existing output directories
are immutable evidence, not rerun targets. A future separately authorized episode
must use a fresh root/nonces and verify identities/headroom anew. Never use the old
continuation's injection-based scenario or uninstall-based cleanup scripts.

Next separate tasks: direct authenticated provisioning startup dependency under
the whitelist model; root-cause analysis of retained unexpected closes; optional
browser/IPv6/recovery-egress coverage. No routing defect is established here.

**Обычный Android-трафик реально проходит через TUN → Telemost → NL gateway.**
