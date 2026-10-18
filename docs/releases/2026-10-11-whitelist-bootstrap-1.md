# WHITELIST-BOOTSTRAP-1 — research83; live dedicated startup failed

**Later operator clarification:** an incoming call occurred during this trial.
[Offline voice-call review](2026-10-11-whitelist-dedicated-join-1.md) finds no saved
underlay/call timeline capable of confirming or excluding causation. Treat the
attempt as potentially confounded, not proof of a Reliable/dedicated defect. The
observations below remain intact; no historical receipt was overwritten. One clean
repeat is separately authorized, not yet run; no timeout/product change follows.

**Later clean preparation:** after operator confirmation that the call ended,
preflight stopped before any CONNECT because the gateway exited and automatically
restarted with a new directory. Product bytes unchanged; zero new CONNECTs, clean
attempt not consumed. Latest cleanup observed15:19:53UTC; see the linked report's
pre-CONNECT supplement rather than treating the14:15 state below as current.

11 October 2026. **LOCAL TARGETED PASS; RESEARCH83 INSTALLED; ONE LIVE ATTEMPT FAILED.**
This is not a restricted-network FIELD result. Research82 full-device egress remains
proven. The new warm-start acceptance did not reach dedicated client READY or send
full-phase requests; it does not prove a routing regression or an Orange leak.

## Continuation — authoritative final state, 14:15 UTC

Evidence: `state-client-build/field65-export16/whitelist-bootstrap-1-continuation/`.
Use its `RESULT.json`, `research-manifest.json`, `SHA256SUMS`, receipts and protected
paired snapshots. The earlier local-only phase below is retained as history.

### Source, APK and gateway

- Isolated clean source `f5240994869826c6a28f59e58e38256c688cf6eb`, tree
  `630464f630044b0d72afed4ae5b375f21bfd3d01`; base research82 `fbbecb81`.
  Authorized local source-freeze commits only; no push/main-tree commit.
- Installed `0.1.18-research83-bootstrap`, code83, package
  `com.familyconnect.app.friends`, UID10283. One in-place update, no data clear,
  uninstall/re-enrollment. Owner app/chat briefly stopped for installation and
  explicitly reopened. No public distribution or invitation/catalog changes.
- Signed APK SHA256 `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`.
  Same signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Pulled installed bytes/signature checked, not inferred from the build output.
- Embedded schema2 native provenance matches final source/tree; provider Telemost,
  diagnostic=false, tags empty, fault schema0. JNI SHA256
  `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
  23 other packaged native libraries remain byte-identical to82, including AWG/audio.
- Gateway loaded/next SHA256
  `5e877eb1355ed4a65bda31be0594299c70002c7a3e96f9d7a528e9e1bb6fe81f`;
  PID596825, invocation `521233dfc63c49ffac08eeefa567e788`, NRestarts0.
  One coordinated activation, no extra cleanup restart. Same-key AKI renewal uses
  accepted4h policy, no new PKI/key/grant or arbitrary TTL extension.
- RU/NL directory SHA256
  `831abdd213022076ce91b3ebb7537dcb0fbe35fd184dd63b0cae79f81928b36f`.
  Served chain PASS at14:15:34UTC, security headroom12821s; CRL21620/floor21620,
  identity revision floor1. Same authority `d5a0d0db…dc18`; leaf `3ac25859…0274`.
  Server-chain preflight is not dedicated client mTLS/READY.
- Optional seed rotation enabled at3h within the existing4h process limit:
  at most one replacement/two live seeds, same Broker and original old expiry.
  No live rotation was reached in this short failed episode.

### Local acceptance and integration correction

Full Gradle integration found that the first archived candidate had replaced the
existing `RestrictedStartup` diagnostic projector. Corrected before signing: the
new coordinator is `RestrictedBootstrap`; original projector and tests restored
byte-for-byte from82. No UI or diagnostic weakening. Final source rebuilt cleanly.
74 Gradle JVM tests/12 classes, 48 focused JVM tests, 15 actual FriendsRestricted
gate scenarios, fresh-fixture Go race×3 plus authenticated overlap race×5 PASS.
Packaged JNI isolated fixture PASS without owner CONNECT. Availability-condition
scope/restore tests4 PASS. Existing deterministic ordinary-app harness APKs unchanged.

Do not label the whole suite green: Android lint is FAIL (one pre-existing
`ChatAudio.java:108 MissingPermission`,45 warnings, zero new errors); reproduced
on unchanged research82, no suppression/patch. Six historical auth diagnostic
assertions and baseline busy-wire-error equality remain separate known failures.
Earlier sandbox listener restriction and aged disposable-fixture lifetime failures
are retained; fresh valid fixtures were used for the passing bounded race tests.

### Exactly one physical CONNECT

All collectors and test app were ready/armed before the operator gate. A real
authenticated refresh obtained the current usable protected cache before the
condition; no manually fabricated cache. One VPN-OFF ordinary-app request determined
the current source IP for narrowly scoping the condition (not a browser check).
Only this source's restricted-readiness/challenge/ack endpoints returned503;
other API/chat routes were not blocked. This models provisioning unavailability,
not a real whitelist network and not an endpoint-wide outage.

| UTC | Observed boundary |
| --- | --- |
| 14:03:27.667 | Single physical CONNECT; explicit Telemost/NL, connection `ccf7607c-81c9-49a5-9ee0-2733cafbc885` |
| 14:03:28.366 | Provisioning challenge503; no upstream request |
| 14:03:28.733 | Receipt ack-challenge503; no upstream request |
| 14:03:35.959 | Android reports `CACHED_VALID_REFRESH_UNAVAILABLE`, cacheUSABLE, CONNECTING |
| 14:03:46.292 | Gateway seed `bootstrap_family_auth` |
| 14:03:46.294 | Authorized holder lease issued, deadline14:13:46.294 |
| 14:03:58.654 | Gateway room READY/descriptor issued; **not Android dedicated READY** |
| 14:03:59.265 | Bootstrap handoff; client starts dedicated join at14:03:59.574 |
| 14:04:14.576 | Client `GATEWAY_JOIN/RECOVERY_JOIN_FAILED`; first-close `UPPER_CLOSE` |
| 14:04:14.774 | Orchestrator FAILED/BOOTSTRAP_UNAVAILABLE; native startup45.844s, `DEDICATED_CONNECT`, causeUNKNOWN |
| 14:04:18.656 | Same server session: `RELIABLE_HANDSHAKE_TIMEOUT`, close-sourceRELIABLE_EXHAUSTION, handshake age20s |
| 14:04:18.663 | Server `gateway_session_failed`, FAMILY_TLS_ERROR; cleanup completed |
| 14:05:25.368 | Android DISCONNECTED after cancellation; no second CONNECT |

Paired session tag `f6a7df33f2dd9860ef72ae581304946ab70b6171fe60d5db20febf143a897e0c`.
No ACTIVE, dedicated client READY, ordinary full-phase requests or lease renewals.
The request nonces remained armed; endpoint logs contain only desktop preflight and
VPN-OFF calibration, not full-phase traffic. Failure occurred well before lease
deadline. It is not an expiry or observed auth/revocation rejection.

The earlier client join failure precedes the server handshake timeout by4.080s.
Server timeout is therefore not established as the initiating cause. Exact join
substage/network error is absent in existing Android projection (`causeUNKNOWN`);
do not infer WebSocket failure solely from a roughly15s interval. Saved transport
evidence requires separate first-divergence analysis, without tuning Reliable here.
Server cleanup reaches `Broker.finish`; release follows by existing code contract.
Direct holder-release telemetry was not enabled, so no independent slot census is
claimed. Ownership safety remains covered by local tests.

**Harness accounting correction:** fast operator input happened before `manual.py`
checked its initial OFF assertion. Original immutable `live-result.json` defaulted
to OPERATOR_GATE_TIMEOUT, but the actual error was AssertionError while CONNECTING.
This label is incorrect, not a real timeout or zero CONNECT. Read-only observer and
server evidence continued and captured the real failure. No full request was sent
before READY. The prepared same-connect continuation was **not executed** after
the operator reported failure. No second CONNECT/retry. Future harness work must
arm state observation before printing the gate and accept the first observed
transition; no input injection or test-app lifecycle rewrite is justified.

### Current acceptance fields

| Field | Result |
| --- | --- |
| CURRENT_DIRECT_DEPENDENCIES | Existing graph below; direct refresh attempted, availability-only valid-cache fallback now observed |
| MINIMUM_PRE_TELEMOST_BOOTSTRAP | Enrolled identity + protected authenticated delivery + valid signed Family trust objects |
| SAFE_CACHE_POLICY | Local PASS; actual current cache selected under scoped503; server seed auth PASS |
| DIRECTORY_OVERLAP_POLICY | Finite same-Broker overlap local PASS; enabled3h/4h, live rotation NOT_RUN |
| WARM_START_WITH_PROVISIONING_BLOCKED | FAILED before dedicated READY; fallback/seed auth only PASS |
| STALE/EXPIRED/REVOKED_NEGATIVE_CASES | Targeted local PASS; invalid/expired/revoked/floor denial stays fail closed |
| COLD_START_DESIGN | Public descriptor alone insufficient for existing device mTLS; no new mechanism implemented |
| COLD_START_RESULT | NO; clean/expired bootstrap fixture fails closed; owner data not cleared |
| FULL_TUNNEL_EGRESS_PRESERVED | Research82 proof retained and packet implementation unchanged;83 live egress NOT_RUN |
| SECURITY_PROPERTIES_PRESERVED | Targeted local PASS; seed authentication observed; not a whole-suite or uninterrupted-session claim |
| WHITELIST_WARM_START_READY | NO — end-to-end acceptance not achieved |
| WHITELIST_COLD_START_READY | NO |
| WHITELIST_ARCHITECTURE_READY | PARTIAL |
| REAL_RESTRICTED_NETWORK_FIELD | NOT_RUN |

### Cleanup and rollback

Evidence captured before stopping observers/endpoints. Original ingress bytes
restored (SHA256 `128d4cdd3988ee0d187e61009d6e603311a3e7e876ac1d1d9fc8d00e66e44e76`),
temporary condition log/helper/timer removed after local preservation. Own endpoint,
firewall rules and bounded collectors removed. No extra gateway restart; loaded/next
remain matched.14:15:32UTC fresh device receipt: research83 hash/UID unchanged,
VPN OFF, app ON/foreground, ChatDeliveryService ON. Instrumentation finished;
unchanged deterministic helpers remain installed idle (no uninstall). No cache,
enrollment, AWG, publisher or history reset; whole-history byte equality not claimed.

No rollback performed automatically. Research82 signed APK, native/source bundle and
gateway34704e26 remain retained for an explicitly planned rollback; Android code83→82
downgrade is **not** assumed supported without data loss. A future approved rollback
must use a permitted higher-code in-place build or a verified safe platform procedure,
never uninstall/data clear. Keep current monotonic trust/credentials, not expired
old leafs. Gateway prior activation/drop-ins and ownership-safe runbook are retained.
No public release, invitation download update, tester delivery or Krasnodar FIELD.

## Earlier local-only phase — historical observations and contract

The following records predate the continuation above; their unbuilt/undeployed
status and expired served-chain observation are historical, not the final state.

### Preserved base and entry observations

Evidence root: `state-client-build/field65-export16/whitelist-bootstrap-1/`.
Isolated candidate: `source/`; main dirty worktree and earlier artifacts preserved.
The candidate is an archive plus explicit patch, **not a clean Git commit**.
`SOURCE.json`, `source-files.json`, `candidate.patch`, `source-candidate.tar.gz`
identify the complete local source without pretending that the base commit includes
these changes. Frozen research82 product files remain unchanged; its later historical
documentation edits are also preserved.

Fresh installed owner observations at12:14:02 and13:04:10UTC:

- Package `com.familyconnect.app.friends`, UID10283;
  `0.1.18-research82-lease`, versionCode82.
- APK SHA256 `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18`.
- Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Embedded native source `fbbecb81c033557f6c29819a02b8382519465961`, tree
  `06ca3d03620fc773d4bbb1528e2a0f193d7727a5`.
- Embedded JNI SHA256 `743080ad01481ef2e839a1e4e92619a32956bb52bf85c7b666e6ac0ac51e8664`;
  metadata schema2, Telemost, diagnostic=false, no build tags, fault schema0.
- Gateway loaded/next SHA256 remains
  `34704e26029bf1eee4ae7679712c673eec7989b291f1a6f47c87c2b40973d958`.
- Entry PID415430/invocation`3d9e1d2923a5423e9a11afbed13648de`, NRestarts0.
  Directory `af4848c3d1fc83f60c4b38794312c974449126ae436f2914d62dbbf0c82f2041`,
  expiry12:46:38.409786209UTC; served-chain PASS at entry, headroom1900seconds.
- Entry/final authority SHA256
  `d5a0d0dba0a90c6cedaf5365007edebd2e75257a0c05e4453b8fde5f1959dc18`;
  gateway leaf `b347b452a5c64417cfc1d8d9c530c56783a71d274cfebde8c4a6989b66535c5f`.

**Current security gate changed naturally during local work, not by deployment:**
the existing bounded gateway process has `Restart=always`; at12:47:08UTC its
next invocation starts, PID560914, invocation`59019a14cf8b41d0847f82e3de7d58cf`,
NRestarts1, same loaded/next bytes. No agent restart command was issued.
New directory `a3d90af108144d0e54045dd1538cedcb6e6ae551ff5b6a43d4ce2b3eccaf9aa5`
is issued12:47:10.759124177UTC, expires16:47:08.470621214UTC, and normal sync
propagates it to RU. This does **not** renew the Family leaf.
Final live read-only preflight at13:05:56UTC is BLOCKED: served-chain
`CERTIFICATE_EXPIRED`, headroom−1208seconds; CRL/minimum CRL21492, leaf not revoked.
RU publication preflight PASS is not client authentication or a healthy NL chain.
The accepted AKI same-key renewal runbook is required before any later live gate.
No TTL, issuer, grant or certificate was changed in this task.

## CURRENT_DIRECT_DEPENDENCIES

The relevant current path is `RestrictedTunnelEngine.up` →
`FriendsRestricted.ready` → refresh/import/selection →
`NativeRestricted.beginReady` → `DeliveryMaterial/ValidateDelivery` →
`bootstrap.Recover` → seed admission → Family TLS →
`ChallengeAfterCleanup`/dedicated descriptor → dedicated Family/Mux READY → TUN.
The last stages and the TUN implementation are unchanged.

| ROLE | DESTINATION CATEGORY | PATH | REQUIRED WHEN / TRUST PROVIDED |
| --- | --- | --- | --- |
| First enrollment, invitation, identity binding | Own authenticated Friends control | Direct before VPN | Required for a new identity; enrollment proof/grant and device key binding; not supplied by Telemost |
| Readiness challenge + proof-bound delivery | Own HTTPS provisioning, restricted-readiness endpoints | Explicit underlay before startup | Research82 always requires success. Candidate still attempts once, but permits availability-only fallback for valid protected cache; fresh identity proof and authenticated publication when available |
| Restart/import receipt ACK | Same own control | Direct, bounded | Diagnostics; success not an authorization prerequisite. Existing receipt behavior preserved |
| Cache import and validation | Local Android Keystore-protected storage / native | Local | Always; root delegation, certificate, CRL, identity, directory and persistent floors |
| Telemost rendezvous/signalling/ICE/media | Telemost provider and its negotiated connectivity services | Underlay to Telemost | Required; supplies reachability only, never Family authorization |
| Provider-name resolution | Underlay resolver available to carrier | Underlay | Required as needed for provider hosts; no own provisioning hostname is a substitute |
| Seed Family authentication and broker admission | Expected Family gateway through cached Telemost seed | Telemost | Always; TLS1.3/mTLS, role, identity, Family/gateway, current server CRL/floors, fresh admission |
| Dedicated room creation | Telemost provider, requested by NL broker | Gateway Internet | Required after successful admission; not a phone→own-provisioning dependency |
| Dedicated Family/Mux, active lease renewal | Current holder/session on NL | Telemost protected session | Always; existing authenticated renewal and security deadlines unchanged |
| NL→RU directory/CRL publication sync | Existing server control/sync infrastructure | Server-side authenticated path | Required when publication changes; not phone underlay reachability |
| Messenger DIRECT / service-only fallback | Existing mailbox/control services | Independent direct or restricted service path | Not full VPN proof or a substitute startup authorization path; untouched |

Per scenario: warm valid-cache reconnect can use the candidate availability policy;
usable-but-newer-publication refresh still selects B; stale room outside overlap,
expired certificate/CRL/delegation/directory, or empty cache cannot be repaired by
declaring network failure. Certificate renewal and newly required security state
still require authenticated delivery. This task does not create offline enrollment.

## MINIMUM_PRE_TELEMOST_BOOTSTRAP

An enrolled device needs its existing private identity in the vault; app trust
anchor; root-signed issuer delegation; identity-bound client certificate;
issuer-signed current-enough CRL and floors; and an authenticated directory with
Family, expected gateway, Telemost seed URL, issued/expiry times. The room URL
alone neither authorizes a device nor supplies the TLS client certificate.

Important correction to terminology: **directory v1 / the outer readiness JSON
are not independently signed**. Their origin is authenticated HTTPS delivery and
the protected cache. On Android this is AES-GCM with Android Keystore key, fixed
AAD, atomic no-backup storage. Delegation, certificate and CRL signatures are
separate and remain verified. This is the documented BOOT-1 trust boundary, not
a newly invented signature or a new PKI. Arbitrary JSON/file injection is not an
authorized way to construct the cache.

## SAFE_CACHE_POLICY

Implemented in the isolated candidate only:

1. One bounded authenticated refresh attempt remains first; single-flight,
   cancellation, consumer deadline and background backoff remain intact.
2. Only classified socket timeout/unreachable/reset/DNS failures or HTTPS429/5xx
   permit considering the existing cache. Generic malformed-body IO, TLS trust
   errors, protocol/binding errors, rejected imports and AUTH do not qualify.
   The existing challenge diagnostic code is retained; a separate availability
   bit prevents TLS exceptions from masquerading as an offline-fallback permit.
3. Selection under the existing vault lock re-reads the protected persisted state,
   rejects sticky denial/missing/corrupt state, checks exclusive outer expiry and
   runs the unchanged native validator. No network operation occurs under that lock.
4. Native validates the exact selected bytes again at `beginReady`. Signature,
   identity/role, revision/delegation/CRL floors, validity bounds and directory
   binding are not replaced with a network-availability judgment.
5. A successful B import supplies **B's bytes**, not a later cache reread A or C.
   Persistent monotonic issuer sequence, revision, CRL, issued-at and directory
   generation rules remain. Late A cannot replace B. Rejected B does not authorize
   fallback to A on that attempt.
6. A cached fallback records `CACHED_VALID_REFRESH_UNAVAILABLE`; it does not forge
   a successful fresh fetch/ACK. The receipt still records failed fetch. Existing
   bounded diagnostic ACK attempts are retained (up to15+30+15seconds for restart
   ACK, fetch, import ACK; restricted candidate budget remains200seconds).
7. Unreceived revocation information is not claimed locally known. Current server
   `SessionAuthorizer` reloads credentials and rechecks identity/role/CRL/floors
   before admission/handoff; dedicated authentication/renewal retain their checks.
   Locally known denial/revocation or expired material fail closed, not extended.

No client-appointed deadline, TTL increase, heartbeat authorization, cache clearing,
new key, extra admission owner or data-plane change is introduced.

## DIRECTORY_OVERLAP_POLICY

Research82 server has one seed per process; restarting it retires the old room.
The previous usable-A/current-B incident is therefore an availability mismatch,
not proof that signature checks should be bypassed or all expiry removed.

Candidate broker adds optional `--seed-rotate-after` (default0 = legacy behavior).
Within one process it creates **at most one replacement / two seed carriers**.
Creation and READY complete before B publication. A remains served until A's
original deadline; B has its own deadline clipped by parent process lifetime.
Configuration must leave more than creation+READY timeout before A's TTL ends.
No retries or repeated room pool. Failed replacement creation keeps A; publication
failure is fatal. Old timer/cleanup belongs only to its seed; both use the same
Family callback and Broker, so one identity does not gain a second admission slot.
The HTTP directory writer no longer holds the manager mutex while writing a response.

This is finite **compatible-trust in-process overlap**, not authority rollback,
revocation grace, persistence over a restart, or service past a certificate/grant
deadline. Forced shutdown or failed carrier can still destroy availability.
No automatic coordination of a trust-changing restart is claimed. Existing server
publication sync must propagate B; its success is not inferred from local export.

Compatibility: v1 directory/wire unchanged; no new command sent to an old peer.
Old clients retain mandatory refresh and normal authorization. New client + old
server can use an existing valid/reachable seed but has no overlap feature.
New server without the option stays legacy. Only an explicitly configured updated
server provides the locally tested overlap.

## COLD_START_DESIGN / COLD_START_RESULT

`COLD_START_RESULT = NOT_IMPLEMENTED / FAIL_CLOSED_AS_EXPECTED`.
Empty-cache or newly unenrolled Telemost-only startup is not enabled.

A future public, root/delegation-signed bootstrap descriptor could carry only
Family/gateway identity, provider seed, generation/expiry, authority binding and
minimum floors. It must use the existing trust authority, no universal credential,
private key or anonymous Internet gateway. Replay, rollback, revocation and rotation
bounds need the same scrutiny as a readiness delivery.

Descriptor alone is insufficient today: seed admission uses Family mTLS, which
needs an unexpired device certificate and CRL. A previously enrolled device could
receive the complete protected bootstrap material during accepted enrollment; that
is pre-provisioned warm state, not genuinely empty cold start. A new/expired device
would need a separately reviewed identity-proof/enrollment path before mTLS. No
such wire protocol or unauthenticated service is added here.

## Provisioning through an established tunnel

After full TUN READY, ordinary default-network HTTPS to existing provisioning
can traverse the already proven Telemost→NL egress; existing
`FriendsAccessAndroid(context)` differs from the explicit-direct constructor.
This can support a future optional post-READY refresh without a new remote-control
API. Seed exchange itself is admission control, not arbitrary TCP/Mux forwarding.
It cannot fetch the prerequisites for its own mTLS handshake.

No post-READY refresh scheduler or active-session certificate replacement is added
in this candidate. Cache upgrades when the normal authenticated refresh later
succeeds. Offline operation remains bounded by the existing security deadlines;
renewing the broker lease does not renew certificate/CRL/grant material.

## Local acceptance matrix

| Case | Local result / evidence scope |
| --- | --- |
| A valid A + available refresh | PASS: loopback HTTP-delivered B imported; selected bytes B |
| B valid cache + unavailable provisioning | PASS: actual refused loopback connection, validated cached bytes selected; real FriendsRestricted gate also tested |
| C expired cache + unavailable | PASS: exclusive controlled-clock expiry, no snapshot |
| D revoked/denied cache + unavailable | PASS: persisted denial and signed revoked CRL rejected; real Family server rejects revoked identity |
| E invalid signature/binding | PASS: real native signed-delivery negative tests, TLS/protocol/import failure never fallback |
| F old generation within overlap | PASS: old seed transfers packets and real Family-authenticated descriptor after B publication; same broker |
| G old generation outside overlap | PASS: controlled-clock directory expiry and old carrier close; B/new admission remains owned |
| H fresh B with existing A | PASS: exact fresh snapshot reaches native-input boundary |
| I late A after B | PASS: rollback rejected; snapshot concurrency test retains B despite later cache C |
| J empty/new cache Telemost-only | PASS of expected fail-closed result; cold readiness NO, not a cold-start success |
| K provisioning recovers | PASS: next real loopback delivery upgrades cache without enrollment; subsequent opens/recreation retain floors |

Evidence: `receipts/jvm-before-contract.log` has three expected failing assertions
(missing availability fallback and TLS/availability distinction), after correction
of fixture plumbing. `receipts/jvm-final.log`: **45 JVM tests PASS** including
existing wire/proof/recovery regressions. `refresh-candidate.json`: **15 real
FriendsRestricted/RestrictedCache/ReadinessProduct scenarios PASS**, including
single-flight, cancellation, caller expiry and exact-snapshot race.
HTTP selection tests use synthetic material and an actual controlled loopback
network failure; cryptography is separately verified with native signed fixtures.
They are not presented as a physical Android VPN/Telemost observation.

`go-targeted-race.log`: bootstrap/wholedevice/broker/CLI race ×3 PASS; tests requiring
external fixture environment were not evidence from that first run.
`go-bootstrap-final.log`: selected overlap/mandatory negative-auth race **×5 PASS**
with freshly ProductStore-issued disposable real Family TLS profiles, not skipped.
Shared-owner test proves no parallel identity slot and no stale seed cleanup of
the newer holder. Renewal/security tests in `go-authenticated-targeted.log` pass,
but that mixed command is **FAIL**, not a green suite: a pre-existing busy-exchange
wire-error equality assertion fails intermittently. It also fails on unchanged
research82 in `go-baseline-diagnostic-assertions.log`.

The six historical `auth_test.go:86` diagnostic assertions remain FAIL on the
unchanged baseline; mandatory security rejection is confirmed separately (no
descriptor, no authenticated admission, zero provider calls). They are not removed,
weakened or silently counted as passing. See `docs/testing/negative-auth-diagnostics-open.md`.
The full suite is **not claimed green**.

Real modified Android classes compile against Android35 and research82 compiled
API (`android-java-api.log`). This is a Java/API check, not APK acceptance.

## Build, live gates and rollback

Affected executables if released: Android app (startup selection) and broker
(optional finite seed overlap). Neither has been rebuilt/signed/installed/deployed
as a new research release. No versionCode has been reserved or changed.

The normal Android compile invocation reaches `verifyFriendsRestrictedInputs` and
fails `Restricted source metadata mismatch`: this archive is not an independent
clean Git checkout, while the supplied research82 JNI metadata correctly describes
research82. The guard was **not disabled**, no metadata relabelled and no APK built.
A separate clean candidate source-freeze commit and source-bound native build are
needed. Creating that commit requires explicit user permission; main dirty worktree
must not be committed. The next task also reserves a free code, rebuilds/verifies
normal native and embedded metadata, signs with the same vault signer via the local
protected dialog, and performs only the authorized in-place update.

Before the one physical CONNECT: renew expired Family leaf through accepted
same-key AKI runbook (no TTL extension), verify loaded/next, current RU/NL directory,
served chain and sufficient credential headroom. Obtain valid owner cache via normal
authenticated delivery **before** inducing a controlled provisioning-only failure.
Prepare the existing deterministic egress app/readonly observer/collectors first.
Provisioning-only denial must be scoped to restricted-readiness ingress and owner
underlay, not arbitrary phone networking, chat, AWG or Telemost. This temporary
condition has not been installed or locally ingress-tested yet.

Then one operator physical Telemost/full VPN CONNECT, no input injection; assert
classified unavailable refresh + cached snapshot → dedicated READY → ordinary
test app nonce → TUN/Mux/same Telemost session/NL outbound → endpoint NL source.
No manual reconnect, no hidden normal transport fallback, no retries to success.
Save evidence, remove only introduced test resources/condition, VPN OFF/app+chat ON.
No new public APK, tester delivery or restricted FIELD is authorized.

Current rollback is simply not deploying the isolated candidate: installed code82
and loaded/next gateway bytes are unchanged. A future deployed rollback must retain
identity/cache floors and compatible current trust/publication, not restore an expired
certificate or earlier DB state. Do not restart a gateway merely to tidy evidence.

## Final current results and cleanup

- `WARM_START_WITH_PROVISIONING_BLOCKED = LOCAL_PASS / LIVE_NOT_RUN`.
- `STALE/EXPIRED/REVOKED_NEGATIVE_CASES = LOCAL_PASS` with the limitations above.
- `FULL_TUNNEL_EGRESS_PRESERVED = RESEARCH82_PROVEN / PACKET_CODE_UNCHANGED`;
  candidate egress not newly measured. Prior two RELIABLE_EXHAUSTION/recovery events
  remain a separate OPEN issue; no RTO/retries/buffers/media changes.
- `SECURITY_PROPERTIES_PRESERVED = TARGETED_LOCAL_PASS`, not full-suite PASS.
- `WHITELIST_WARM_START_READY = NO` for installed research82 / pending candidate live.
- `WHITELIST_COLD_START_READY = NO`.
- `WHITELIST_ARCHITECTURE_READY = PARTIAL`.
- `REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN`.

Final owner check13:04:10UTC: VPN OFF, app ON, ChatDeliveryService ON, same
APK/package/UID/signer. No CONNECT, install, permission change, uninstall, data clear,
re-enrollment, manual gateway restart, firewall/proxy rule or endpoint was performed.
No live collectors were created. Existing deterministic egress harness is untouched.
Local regression fixtures and candidate source are retained separately; private keys,
owner enrollment/cache/AWG/publisher/history are neither modified nor published.
