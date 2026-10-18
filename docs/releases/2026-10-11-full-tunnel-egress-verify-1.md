# FULL-TUNNEL-EGRESS-VERIFY-1 — incomplete acceptance, 2026-10-11

## Decision

**PARTIAL_ACCEPTANCE_NOT_PASSED; EGRESS_CLASSIFICATION=UNKNOWN.**

The one allowed ordinary UI Telemost CONNECT was consumed. Android full VPN and
Telemost packet processing were established, but the controlled ordinary-app
full-phase requests did not execute because of test-harness lifecycle failures.
There is no full-phase external nonce response to attribute to either the gateway
or Orange. No repeat CONNECT, product routing fix, APK rebuild/update, gateway
deployment, public distribution or real restricted-network FIELD was performed.

The VPN-OFF baseline does establish Orange Belgium as the phone's source ISP.
It does **not** establish Orange egress while VPN is on. Conversely, READY,
internal DNS/TCP counters and an Android default VPN route do **not** prove that
the controlled ordinary app reached the external endpoint through the gateway.

Independent source finding: **warm and cold whitelist startup are not ready**
when the direct provisioning endpoint is unavailable. Research82 requires its
authenticated foreground refresh for every new connection, including a warm
connection with cached directory. This is not fixed by retaining a valid cache.

## Evidence and scope

Local, private evidence root:
`state-client-build/field65-export16/full-tunnel-egress-verify-1/` (abbreviated `R`).
Full source IPs, exact endpoint addresses and system snapshots remain there; public
addresses are masked or represented by role in this report. No private keys or
release-signing secret are included in this report.

- `R/RESULT.json`: `b99f059f3e0855cf9ecdbf56cf7010d78b22548f5573e43886ca8a2a47c068d5`.
- `R/research-manifest.json`: `b595927a5892af1769632c6d9a74f8be678ad67858dc935b9320f2accc117b46`.
- All 163 manifest entries rechecked by byte length and SHA256; no mismatch.
- `preservation/main-tracked.patch`, `main-status.txt` retain the initial dirty
  checkout; production code in that checkout was not used as the research82 source.
- `receipts/source-and-baseline-preservation.json` verifies the previous lease
  RESULT, manifest, source bundle, APK and gateway artifact are unchanged.

The candidate source remains
`state-client-build/field65-export16/telemost-lease-continuity-1/source`.
Its runtime source is clean at the frozen commit; existing documentation changes
in that saved checkout are not a new runtime patch. New harness/evidence is
isolated under `R`. No new Git commit, branch or push in this task.

## Freshly checked identities and preflight

| Component | Observed identity |
| --- | --- |
| Android package / UID | `com.familyconnect.app.friends` / `10283` |
| Installed version | `0.1.18-research82-lease`, versionCode `82` |
| Pulled APK SHA256 | `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Frozen source commit | `fbbecb81c033557f6c29819a02b8382519465961` |
| Frozen tree | `06ca3d03620fc773d4bbb1528e2a0f193d7727a5` |
| Restricted JNI SHA256 | `743080ad01481ef2e839a1e4e92619a32956bb52bf85c7b666e6ac0ac51e8664` |
| NL loaded AND next binary SHA256 | `34704e26029bf1eee4ae7679712c673eec7989b291f1a6f47c87c2b40973d958` |
| NL PID / invocation | `415430` / `3d9e1d2923a5423e9a11afbed13648de` |
| Active directory SHA256 | `af4848c3d1fc83f60c4b38794312c974449126ae436f2914d62dbbf0c82f2041` |
| Served Family leaf SHA256 | `b347b452a5c64417cfc1d8d9c530c56783a71d274cfebde8c4a6989b66535c5f` |
| Family authority SHA256 | `d5a0d0dba0a90c6cedaf5365007edebd2e75257a0c05e4453b8fde5f1959dc18` |

Embedded `restricted-build.json` was extracted from the actual installed APK:
metadata schema2, provider `telemost`, diagnostic-only false, build tags empty,
owner diagnostic fault schema0. It matches the frozen source and pinned Xray
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` / gVisor
`v0.0.0-20260122175437-89a5d21be8f0`. Accepted native patch SHA256
`2d0a556f73cdd7fb9f0d152edf564b126ba00cfdd526bb7c3325f5051b02339b`,
builder SHA256 `c223f548be829bde2a148752a44f667984162d0f8021cb72cbf3b07a64e78449`.
The prior provenance covers the other23 unchanged research81 native libraries;
this task does not claim to rebuild them independently.

Receipts: `owner-entry*`, `embedded-restricted.json`, `gateway-loaded-next-entry.json`,
`preflight-{entry,armed,live,final}-{nl,ru,pass}.json`. Loaded/next binary and
arguments agree, served chain and directory binding pass, authority/grants remain
unchanged, revocation floor/CRL21209 and revision floor1 remain enforced. Final NL
preflight reports directory headroom8040s and credential headroom7990s. The observed
directory was issued08:46:42.429026860UTC, with expiry12:46:38.409786209UTC. The
Family leaf expiry is12:45:48UTC, within the existing four-hour policy. No credential
renewal or arbitrary TTL increase was needed during this task.

The served-chain probe verifies the server certificate, **not client mTLS or
application READY**. Client authorization is evidenced separately by the actual
successful authenticated refresh/import and selected live session startup. An
exact pre-entry client-private leaf expiry was not independently exported.
Publisher/configuration and its existing publication were not replaced.

## Four separate paths

| Layer | Observed state and meaning |
| --- | --- |
| `UNDERLAY_STATE` | Validated cellular LTE, Orange Belgium AS47377; IPv4 available, IPv6 unavailable in baseline |
| `FULL_VPN_STATE` | Android VPN actually established during the single episode; OFF after cleanup; external full-phase egress unproved |
| `ACTIVE_CARRIER` | Explicit Telemost during episode, no Auto→AWG; none for full VPN after cleanup |
| `MESSENGER_ROUTE` | DIRECT at READY and end; intermediate route label `—` in ticks6–12, then DIRECT; not full VPN proof |

ChatDeliveryService was running during the selected trial. Instrumentation startup
and termination affected the owner app process/service lifecycle; after the helper
finished, a snapshot showed chat service absent. The ordinary app was subsequently
opened and the final snapshot verifies app ON and ChatDeliveryService ON. This
report does not conceal those transitions or claim uninterrupted messenger service.

## Android VPN runtime and source path

Device is API31 / Redmi Note9Pro. Connected runtime snapshots show:

| Property | Observed value |
| --- | --- |
| VPN interface / network | `tun1` / network257 |
| Underlying network | network255, cellular; system-reported, not an app-wide process bind |
| TUN addresses | `10.79.0.2/32`, `fd79:fc::2/128` |
| MTU | `1280` |
| IPv4 / IPv6 routes | `0.0.0.0/0`, `::/0` |
| Advertised DNS | `10.79.0.1` |
| UID coverage | `0–99999`, VPN owner UID10283; test app UID10405 included |
| Bypassability | `false` |
| Allowed/disallowed app lists | Neither set in source; runtime inclusive UID range agrees |
| Always-on / lockdown settings | Unset in captured settings, not enabled for this test |
| Private DNS settings | Mode/specifier unset; default behavior, not changed by this task |

Exact-source path: `AutomaticVpnOwner.open()` calls `VpnService.prepare`, starts
the service and establishes a blocking guard TUN. `RestrictedTunnelEngine` uses
the required authenticated directory selection, native bootstrap/HELLO/dedicated
READY, then replaces the guard via `Builder.establish()` and attaches the TUN fd.
Native `main.go` duplicates that fd, starts the fdbased packet adapter with MTU1280
and transitions to state2 / packet-ready. This preserves Android cancellation
ownership; it is not an independent native harness launch.

`AutomaticVpnOwner.replace()` establishes the next TUN before closing the previous
descriptor. `block()` installs another guard. Explicit disconnect releases it.
Actual connected diagnostics have IPv4 DNS/TCP activity and rejected IPv6/UDP
counters, establishing that the native TUN packet path ran. Those are background
packets without the planned nonce attribution, not acceptance traffic.

### Socket and network-binding audit

The complete search is retained in `receipts/network-binding-source-full.txt`.
These are classifications of callsites, not an assertion that every branch ran.

| Use in frozen source | Classification / scope |
| --- | --- |
| Native bridge `fcRestrictedProtect` → `VpnService.protect(fd)` / underlay sockets | `REQUIRED_FOR_CARRIER`; only the transport-owned fd |
| `AutomaticVpnOwner.resolver`, restricted transport resolver selection with `NET_CAPABILITY_NOT_VPN` | `REQUIRED_FOR_CARRIER`; bootstrap/provider DNS, not Android ordinary app DNS |
| `FriendsAccessAndroid.directPost` → `ChatNetworkAndroid.openHttps` → selected underlay `Network.openConnection` | Required authenticated setup/control dependency, `REQUIRED_FOR_CARRIER`; this is the whitelist startup blocker |
| `ControlRnsAndroid` / Python RNS protected-fd callback | `REQUIRED_FOR_CARRIER`/control; owned socket only |
| `ChatCarrier` / Python chat callback → `ChatNetworkAndroid.bindSocket(fd)` | `BYPASS_OF_USER_TRAFFIC` limited to the deliberate messenger DIRECT path D; not a whole-app VPN exclusion or browser bind |
| `AutomaticNormalEngine` WireGuard socket protect | `REQUIRED_FOR_CARRIER` for that separate transport, not the selected Telemost episode |
| `VpnHealth` socket binding | VPN-network/interface-bound health probe, not an underlay bypass |
| `ChatActivity` NOT_VPN network callback | Availability observation, not traffic binding |

No product callsite sets `addAllowedApplication`, `addDisallowedApplication`,
`allowBypass`, `setUnderlyingNetworks` or `bindProcessToNetwork` in the inspected
installed-source paths. No broader custom `Network.getSocketFactory()` ordinary
app routing was found. The ordinary test app uses the standard Android stack and
has no protect/bind/custom Network or internal Family/Mux calls. Chrome is a
separate ordinary app. `No per-app bypass=PASS` refers to VPN policy for ordinary
apps; it does not deny the explicitly distinguished DIRECT messenger sockets.

## Controlled endpoint and VPN-OFF baseline

Used the already authorized owned RU server, separate from the NL gateway. Three
temporary TLS listeners: IPv4-only19443, IPv6-only19444 and dual-family/normal19445.
They reuse the existing publicly verifiable certificate; no PKI/key creation,
trust-all TLS or private key transfer. Only planned random nonces are accepted.
Records contain nonce, timestamp, source IP/port, address family, protocol and a
bounded test label/User-Agent; no cookies or user payload retention.

Certificate has the server's IPv4 SAN, not its IPv6 literal. The test app's IPv6
test uses standard TLS peer verification against that existing certificate identity
while connecting to the IPv6 address; it does not bind a custom Android Network.
The normal handler uses an IPv4-literal URL, so this setup is **not** a DNS-based
dual-stack/Happy-Eyeballs proof. Resolver tests use randomized names with a DNS-only
public wildcard resolver service; no owned authoritative DNS oracle was deployed.

Phone baseline while VPN OFF:

- Ordinary test app IPv4 and normal HTTPS succeed, as does a separate Chrome HTTPS
  request. All three controlled phone records have the same Orange source IPv4.
- Independent RIPE IP/ASN lookup: masked source `94.*`, **AS47377 Orange Belgium SA**.
  NL gateway's known public IP is independently attributed to **AS57043 HOSTKEY**.
- IPv6 attempt fails with `ENETUNREACH`; underlay IPv6 is UNAVAILABLE in this test.
- System DNS lookup, explicit UDP DNS and explicit TCP DNS succeed in baseline.
  Captured cellular resolver addresses are local evidence, not proof of VPN DNS.
- Two additional endpoint records are laptop TLS preflights, not phone acceptance.

Orange here means **actual baseline source public-IP ownership**, not a chosen
speedtest server, browser geolocation or DNS-provider label. No speedtest ran.

## One live episode and harness failure

Times below are UTC, 2026-10-11. User interaction was automated through the ordinary
Activity/dial control, not by invoking the engine. One CONNECT, zero reconnects.

| Event | Time |
| --- | --- |
| UI instrumentation process started | 10:14:23.676 |
| Late before-connect snapshot | 10:21:14.947 |
| Single UI CONNECT | 10:21:14.962 |
| Full VPN / Telemost READY | 10:21:39.404 |
| Full-phase ordinary-app launch intent | 10:25:08.013 |
| Before deliberate cleanup | 10:26:40.109 |
| VPN OFF | 10:26:40.566 |

Selected client tag
`d522f27ed1bfd691c8443bae58bc6c3bbe96242a37ee219e64b9af7db5f3c048`,
connection `5c75d749-b011-47ce-91a5-c80d4dc91deb`. Startup attempt1 records
SUCCESS/STARTUP/NONE and the current directory fingerprint. Observation after READY
lasted300.705s. Selected native state2 and terminalNONE persist until deliberate
test stop; no selected unexpected close or automatic recovery was observed.

Deviations, not hidden successful acceptance:

1. `startActivitySync` did not return until the ordinary owner Activity was later
   foregrounded. The coordinator's225s READY wait had already expired. No native
   session had started during the initial wait. A requested Java stack dump was
   refused because root was required; no permission bypass was attempted and the
   exact Android blocking stack is not proven.
2. Uninstalling only the UI helper did **not** abort the already-running
   instrumentation. Foregrounding the normal owner app to restore app/chat
   unblocked its one pending dial click. That late CONNECT is included in the
   count, not described as a new test or hidden retry.
3. Initial finite endpoint/firewall/observer windows had elapsed. Only those test
   resources were rearmed for the same connection. No production gateway restart.
4. `am start -W` for the ordinary probe reused its existing baseline Activity.
   Its `onCreate` did not run again, no `full-app.json` was produced, and the
   coordinator waited110s before timeout. The full-phase browser launch was never
   reached. The owner's existing300s observation ended normally during that wait.
5. Endpoint evidence contains only the two laptop preflights and three phone
   baseline records: **zero full-phase nonces**. Gateway collectors contain no
   usable matching full-phase Mux/outbound/return chain. Two bounded journal
   snapshots also timed out; there is no complete selected server-episode journal.

Background counters at the end: protected148/denied0, DNS30, TCP30, active8/peak15,
UDP denied18, IPv6 denied10; internal diagnostics report DNS responses30/errors0,
TCP open32/errors0, sent84,894 and received179,334 bytes. These demonstrate activity
only. They are not substituted for the absent ordinary-app nonce chain.

After the episode, a **zero-network, zero-CONNECT** Android fixture reproduced
the probe launch defect: plain `am start` delivers an intent to the old Activity
without a new record. `-f 0x10008000` (new/clear test Activity task) runs `onCreate`.
The fixture intentionally has no request entries and exits with a JSON-array
error; its acceptance is launch/record creation, not networking. Driver corrected
for future use; as-run driver retained under `preservation/`. No application data
or cache was cleared. UI instrumentation startup/cancellation is still an open
harness gate, so the whole live harness is **not** declared ready for reuse.

## IPv6, DNS and recovery boundaries

IPv6 is already fail-closed by design: both default routes are installed and
`wholedevice.Session.Allow` refuses non-IPv4 destinations. The packet converter
has local coverage, and rejected IPv6 counters incremented live. However, the
underlay itself had no available IPv6 and the planned full-phase IPv6 nonce was
not sent. This is not a live dual-stack leak test. No speculative IPv6-disable fix.

The existing whole-device adapter permits IPv4 TCP and DNS, not arbitrary UDP.
Non-DNS UDP/QUIC is rejected rather than sent directly. Full default-route capture
must not be interpreted as support for every Internet protocol or a tested QUIC
fallback; this task made no transport/media changes.

DNS source path: Android advertises synthetic resolver `10.79.0.1`; UDP/TCP port53
packets go through the TUN adapter, bounded Family/Mux DNS query and gateway
resolver. Actual gateway configuration is system stub `127.0.0.53`, with public
upstream resolvers in the saved snapshot, DNS-over-TLS disabled on that gateway
stub. Resolver configuration/internal counters do not identify who resolved the
absent full-phase nonce. Android Private DNS settings were not changed; no explicit
strict DoT mode was configured in captured settings. TCP DoT would use the ordinary
TCP path if selected, but it was not independently exercised or claimed PASS.

Recovery source contract: `AutomaticConnection.closeCandidate()` calls
`owner.block()` before old candidate teardown; the owner establishes the replacement
guard before closing the old fd. Orchestrator RESTORING/retry/FAILED paths retain
the guard, with release on explicit disconnect. JVM recovery-order tests and the
real packet converter pass locally. They are **not** real-device ordinary-app
requests during RESTORING. No verified production82 per-session-only interruption
mechanism was available; shared gateway pause/restart/broad firewall interruption
was not used. Underlay was not disabled with airplane mode to fabricate fail-closed.

| Classification | Result |
| --- | --- |
| `IPV4_EGRESS` | UNKNOWN during full VPN; baseline UNDERLAY separately proven |
| `IPV6_EGRESS` | UNKNOWN during full VPN; source/local BLOCKED, baseline UNAVAILABLE |
| `IPV6_LEAK` | UNKNOWN, no available-IPv6 live challenge |
| `DNS_EGRESS` | UNKNOWN during full VPN; gateway path source/local contract only |
| `FAILOVER_LEAK` | NOT_TESTED; live interruption NOT_LIVE_TESTED |

## Startup dependency graph / whitelist model

Roles are used instead of publishing private provisioning URLs.

| HOST / role | PURPOSE | NETWORK_PATH | REQUIRED_WHEN |
| --- | --- | --- | --- |
| Friends invitation/provisioning | Enrollment and initial identity/trust setup | Direct underlay HTTPS | First enrollment |
| Friends authenticated restricted endpoint | Challenge, signed directory fetch, readiness ACK | Explicit NOT_VPN HTTPS | Cold start with empty/stale cache **and warm new connection/recovery** |
| Telemost API/signaling/provider media endpoints | Bootstrap room, signaling, ICE/SFU/media carrier | Protected transport sockets over underlay | New Telemost carrier, after required directory selection |
| Underlay resolver / provider DNS | Resolve direct setup/provider hosts where named | Underlay, transport-owned sockets | Before carrier where resolution needed |
| NL Family broker/admission | HELLO, trust/admission checks, dedicated Family/Mux | Telemost carrier | New session after bootstrap |
| Existing Family/Mux renewal service | Authenticated same-holder lease continuation | Existing tunnel; no separate phone provisioning request for each renewal | Normal accepted active-session renewal before deadline |
| Messenger direct control/relay | Chat DIRECT and its service-specific alternatives | Messenger-owned direct sockets, separately scoped fallback | Messenger; not full VPN startup/egress proof |

`FriendsRestricted.ready()` always awaits `start(context, true)` and returns the
fresh selection. If the joined prewarm did not attempt refresh, it runs a required
refresh again. A required fetch failure does not return cached directory merely
because the cache remains usable. `FriendsAccessAndroid.directPost()` uses the
explicit underlay HTTPS path. Thus an already enrolled client with a good cache
still cannot start a new tunnel in the model “Telemost allowed, provisioning
blocked.” Warm here means a new connection, not an already-running session.

The active renewal service has a different contract: it reuses authenticated
Family/Mux and current holder/session; it does not extend certificate/grant/CRL
validity or remove security deadlines. No startup-dependency fix was attempted
by skipping authorization or silently allowing stale security data.

## Local acceptance and preserved lease behavior

- 54 JVM tests PASS: orchestrator, explicit Telemost, restricted recovery, trace and
  cache suites. Initial missing test-resource classpath was a harness failure,
  corrected without product changes.
- `go test -race -count=3` on `wholedevice`, `tcpforward`, `roombroker`: PASS.
- Actual pinned Xray/gVisor packet converter `go test -race -count=3 ./packet`:
  PASS outside sandbox. Initial missing accepted adapter patch and sandbox
  loopback denial are retained as failed setup attempts, not hidden product fixes.
- Source/native/APK/gateway are unchanged; prior same-holder authenticated two-
  renewal live evidence remains intact. This short episode did not reach the
  scheduled renewal lead time: **new live renewal boundary NOT_RUN**.
- The six historical negative-auth diagnostic assertions remain known FAIL;
  mandatory rejection was previously established. They were not weakened, and no
  global suite-green claim is made. No UI/Invitation/Dashboard marathon ran.

Logs and test counts: `receipts/local-tests.json`, `local-java.log`, `local-go.log`,
`local-packet-unsandboxed.log`, `probe-launch-before-after.json`.
No demonstrated product routing defect, therefore no failing-before/pass-after
product patch or production APK rebuild. Only the test-app launch bug has a local
before/after fixture. Its fix does not repair or prove network egress.

## Acceptance matrix

| TEST | RESULT |
| --- | --- |
| Android full VPN actually established | PASS |
| Browser/test app captured by TUN | UNKNOWN |
| Active carrier is Telemost | PASS |
| IPv4 exits via NL gateway | UNKNOWN |
| IPv6 exits via NL or is safely blocked | UNKNOWN |
| DNS exits safely | UNKNOWN |
| Gateway ↔ external nonce correlation | UNKNOWN |
| No per-app bypass | PASS |
| No direct egress during recovery | UNKNOWN |
| Lease renewal preserved | PASS |
| Warm start usable under whitelist model | FAIL |
| Cold start usable under whitelist model | FAIL |

Lease PASS is unchanged bytes/protocol plus local regression and preserved prior
evidence, **not a newly observed live renewal**. Per-app PASS is policy audit and
actual UID coverage, not proof that the failed full-phase app request traversed TUN.
IPv6 UNKNOWN deliberately does not promote a source/local blocking contract to a
completed ordinary-app live challenge.

```
FULL_TUNNEL_FUNCTIONAL = PARTIAL
WHITELIST_ARCHITECTURE_READY = NO
WHITELIST_WARM_START_READY = NO
WHITELIST_COLD_START_READY = NO
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```

## Evidence-first cleanup and remaining gates

The helper retained its before-cleanup snapshot before the deliberate VPN stop.
Endpoint/collector output was copied before removing those test resources.
The remaining server/helper cleanup
receipts are `cleanup-endpoint.json`, `cleanup-gateway.json`, `helpers-removed.json`.
The final owner receipt at10:35:31UTC verifies **VPN OFF, app ON,
ChatDeliveryService ON**, same research82 APK/UID. Both test helper packages absent.

Temporary listeners, exact task-owned v4/v6 firewall rules, cleanup timers and
observer processes were stopped; task-owned remote staging files removed on the
two authorized hosts. Some finite transient observer units had already expired or
reported failed status; this is retained, not presented as successful tracing.
Production gateway stays active with the same PID/invocation/hash, NRestarts0;
loaded/next preflight agrees. No cleanup gateway restart. Existing AWG/TCP, identity,
publisher/history, enrollment, cache and user data preserved. No app uninstall/data
clear/re-enrollment of the owner app, credential replacement or public artifact publication.

Rollback: no new product version/deployment to roll back. Keep research82 and its
matching gateway, not research81. UI rollback draft remains separate. Historical
unexpected disconnections and prior persistent-stream evidence gap remain OPEN;
this failed egress acceptance explains neither retroactively.

Next work is explicitly **unfinished**: validate UI-helper startup/cancellation and
ordinary Activity lifetime before a separately authorized new episode; use the
fresh-task driver, current finite preflight, independent ordinary app/browser
nonces and a working Mux/outbound correlation observer. Then verify DNS/IPv6 and
safe per-session recovery without a shared-gateway interruption. Startup under a
blocked provisioning endpoint additionally needs a reviewed authenticated
bootstrap design; keeping cached directory is not an implemented solution.

**Human answer:** it is not yet established whether an ordinary external website
sees NL gateway or Orange while this full VPN is on. Orange is proven only in the
VPN-OFF baseline. Calling either “no leak” or “direct leak” now would be unsupported.
Real whitelist FIELD is additionally blocked by mandatory direct startup refresh,
even if the missing egress tests subsequently pass.
