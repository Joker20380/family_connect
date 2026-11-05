# MESH renewal: active-session integration / 5 November2026

## Current continuation pointer

The later isolated packet-runtime/recovery work is recorded in the
[same online incident](2026-11-05-mesh-online-renewal.md#isolated-core-runtime-continuation-froma30966c).
It reuses actual SeedManager/Family TLS/mux/broker/maintenance through packaged
entrypoints, with a separate driver and real supervisor. This report's older999s
evidence remains bound to its original source; it is not re-labelled as acceptance
of the new package. Full G1–G4 and Android split tunneling remain unaccepted.
The later [G1 revoke continuation](2026-11-05-mesh-online-renewal.md#g1-revoke-continuation)
adds actual revoke/late-approval/TLS denial and survivor traffic on the isolated package
stand; it does not retroactively broaden this report's Android or two-renewal evidence.

## Scope and baseline

Continuation of the existing Android MESH stability incident, not a new PLAN task.
Entry HEAD equals the supplied `d4de324d4c81e23d6d4da1114c763c5441824335` exactly;
no later source delta. The pre-existing four dirty documents and six untracked files
are preserved. This is **source/integration qualification, not production activation**.

Android installed/opt-in118, invitation/updater113/catalog7, paid admission/cohort/boot
activation and desktop versions remain unchanged. No phone installation, server access,
maintenance timer, certificate TTL, publication/quiescence guard, catalog or release key
is changed. Both NL binaries remain last-observed70e6c0fc; no new live readback is claimed.
Separate paired-DNS and WebSocket incidents remain OPEN.

## Dependency/capture map

| Consumer before this change | Original capture | Integration |
| --- | --- | --- |
| Friends readiness/cache/vault | Per-node signed delivery and persistent300s refresh cooldown; only startup passed it to native | Existing connection-owner polling consumes the same node-scoped single-flight readiness future; encrypted cache/root validation remain in place |
| RestrictedTunnelEngine/JNI owner | Final selected gateway, native handle, initial profile hash and trust anchor | Delivery carries that handle; native revalidates against the original pinned anchor and holder/gateway, queues only on that live session, updates borrowing fingerprint only after confirmed exchange |
| Whole-device client | Secured/mux captured once; independent lease-maintenance goroutine | One SessionMaintenance owns both lease work and a single-slot credential queue on the same session; no new reconnect supervisor |
| Family native session | Original TLS handshake and original security expiry | Atomic generation/authorization/bound access; original ConnectionState remains unchanged; current Authorization is separately authenticated |
| Gateway lease handler | Immutable SessionAuthorizer(ConnectionState) and SecurityDeadline value | Each offer, request and final confirmation reads one locked current authorization generation and bound, with fresh policy/revocation validation |
| Broker setup monitor | Original control-session authorize closure rechecked every second | Original control proof retained for history/startup; an identity-bound active gateway authorization accessor replaces its use for active monitoring, under setup authorization synchronization |
| Lease expiry/cancellation | Real resettable lease timer, broker ownership/state, original receipt sequence | Unchanged lifetime/sequence rules; native guarded commit is serialized with broker and lease locks and checks active ownership, cancellation and unexpired lease |
| Chat borrowing | Hash of initial complete profile in the existing VPN coordinator | Confirmed callback may refresh only that VPN/session's hash; no replacement session/other gateway can receive a late result; existing borrowed sessions retain their contexts |

Before ACTIVE/data binding, challenge/create/claim/activation continue to use the original
control admission proof. This is not permission to replace arbitrary authentication with
an unauthenticated file read. Production control admission is the existing signed Family
profile path; no new ProductStore watcher/subscription authority is introduced. Revocation
still requires current signed policy publication and the existing monitor interval.

## Delivery, generation and serialization

The Android helper polls from the existing connection owner, not a new service/thread
supervisor. It consumes only a completed per-selected-node readiness result, never the
other node's chat prewarm. Disconnect retires its pending delivery without cancelling a
shared readiness fetch; copied material is wiped. The JNI entry captures the exact native
owner, validates with its original root and refuses missing/closed/replaced owners. Full
device/family/gateway/key constraints are rechecked natively. A confirmed callback cannot
mutate a different owner even if the asynchronous work finishes after Disconnect.

Candidate preparation precedes wire activity: unchanged, malformed, stale, wrong-binding
or non-extending local material is ignored. One bounded queue, one in-flight exchange and
at most32 distinct candidate fingerprints per session prevent unbounded bookkeeping;
duplicate candidates never start another exchange. Fingerprints/private profiles are not
emitted in diagnostics. Successful/unsuccessful attempted candidates are not retried in a
loop. The existing lease task drives the queue and retains its normal bounded retry policy.

Port2 first negotiates a bounded canonical readiness offer inside the authenticated mux.
Both peers must have the same next generation/CRL digest/floor before the native exchange.
Unready/mismatched peers explicitly acknowledge the refusal without resetting data or
extending the old bound. Old peers reject the unconfigured port and retain their hard bound.
A refused candidate is not automatically retried: later publication requires a new eligible
candidate or eventual normal recovery. The future online publisher must provide overlap;
this stage does not claim liveness for arbitrary out-of-order publication.

`WithAuthorization` holds the native security lock across a consumer's snapshot, fresh
signed-policy check and operation. Snapshot identity/certificate/generation/deadline cannot
mix pre/post-commit values. Fresh policy is a denial gate, never evidence of native renewal.
The lock order is native security → broker → lease; setup monitor/installation additionally
serialize through the setup authorization lock before accessing native state. The network
exchange does not hold these locks. At commit the latest policy is rechecked and expired,
revoked, cancelled or non-ACTIVE ownership cannot be revived. The native partial-commit
contract remains fail-closed. Lease extension happens through the original receipt protocol,
not by copying a locally loaded profile's expiry.

Original TLS evidence remains immutable. A signed native commit can be observed as a new
generation; the control reserve prevents a concurrent lease transaction inside the credential
exchange. If its final confirmation is lost/corrupt, the native session and broker worker
close rather than continuing on an ambiguous authorization. A completed delivery callback
is published only after the exchange finishes, not at profile load or preflight.

Whole-device Close joins maintenance and its callback before native
owner disposal. Internal fail-close uses a non-joining stop path to avoid joining itself.
The confirmed JNI callback no longer takes the global owner mutex held by Disconnect:
the captured owner's cancellation, exact session and coordinator ownership fence publication.
Android polling also captures the owner handle locally for JNI delivery; a concurrently
cleared/replaced engine handle cannot retarget a result between validation and delivery.

## Integration result and source provenance

The requested runtime integration is implemented and its positive/negative native checks
pass. **This is an integration candidate, not a release/full-CI PASS:** the mandatory
bootstrap package still fails the same six inherited diagnostic-counter assertions.
Nothing is deployed and no production incident is declared resolved by these local tests.

Completed logical source changes, each ordinarily pushed and remotely verified:

- `f7d092041d550683d1d98ad6b6a1b68558cffac1`: active authorization, gateway/broker,
  Android delivery, serialized maintenance and real-runtime acceptance.
- `6dcd727aa4e8c6a8e1161a091c5c56afae053580`: joined maintenance disposal; no JNI global
  owner lock in the confirmed callback; shutdown/replacement tests.
- `b46bff44a47df3191df489ad78d2a20098dcd650`: Android captures the JNI delivery handle.

Concurrent commit `d976e51f715aa2e96e83c2eaa321326c7cdbb4b1` adds only the separate VPN
health report and STATUS/PLAN notes. Its runtime delta againstb46bff4 is empty; it and the
original unstaged work are preserved. Final platform receipt records this documentation
HEAD; ARM64 provenance recordsb46bff4. No source was reverted to make qualification pass.

## Real bounds and useful traffic

The real-runtime fixture uses two real Family TLS handshakes (original control and dedicated
data), bindGateway, Broker monitor/lease timer, the same gateway configure/handlers and
SessionMaintenance as runtime. It uses disposable identity/CRLs, local echo and a pinned
test HTTPS service with certificate verification enabled. No mock deadline setter is used.
Positive tests use10s synthetic leases and12s initial security bounds, followed by two
successors; production lifetimes/timeouts are unchanged. Root DNS qualification uses only
an isolated network namespace with a local port53 fixture, not external DNS/Internet.

Final native run on6dcd727 (carrier/native sources unchanged inb46bff4/d976e51), UTC on
5 November2026. Every row uses **one original TLS/mux and original TCP socket** throughout:

| Bound case | Original security / original lease | Generation1 commit → new bound | Generation2 commit → new bound | Observed after generation1 bound | Live lease / successful payloads |
| --- | --- | --- | --- | --- | --- |
| Leaf | 11:25:57 / 11:25:55.641494815 | 11:25:45.997403585 → 11:26:09 | 11:25:57.312722454 → 11:26:21 | 11:26:09.155005998 | 11:26:15.343688363 /792 |
| CRL | 11:26:21 / 11:26:19.671731874 | 11:26:09.946731247 → 11:26:33 | 11:26:21.249370857 → 11:26:45 | 11:26:33.158912431 | 11:26:39.335953448 /822 |

At generation2 commit the original security and original lease deadlines have already
passed. At the last observation the generation1 bound has also passed. The fixture asserts
the unchanged mux pointers, exactly one accepted echo socket before explicitly opening a
new flow, byte-for-byte traffic and increasing payload count across the second crossing.
Original TLS peer serial remains2; authenticated peer serial becomes6, generations0→1→2.
The old control authorizer now rejects its expired handshake certificate, while the active
broker monitor and real lease timer continue authorizing the renewed full setup.

After both crossings, new TCP byte echo, DNS through the actual mux DNS handler and HTTPS
with a pinned disposable root/hostname verification all PASS. No insecure TLS verification,
fake native security deadline or mock lease timer is used. The HTTPS net.Conn adapter has
no stream-level socket deadline setter; the Family session's real cryptographic timer and
the bounded test context remain active. This is not physical Android/provider field traffic.

## A–F acceptance and exact check scope

| Scenario | Observed result |
| --- | --- |
| A | Leaf and CRL wall-clock cases retain TLS/mux/TCP across original security and real lease expiry; new TCP/DNS/verified HTTPS PASS |
| B | Two authenticated successors per session; generation and actual deadline checked atomically at each commit; original handshake evidence unchanged |
| C | Unchanged/invalid candidate rejected before exchange;20 duplicate deliveries produce only one callback/generation; closed owner refuses more work; failed/unready candidate has no retry loop |
| D | Client commit held while signed CRL revokes predecessor/successor, broker Cancel, Disconnect or real1.5s lease expiry occurs; late commit fails, no security/lease extension, broker/native/resources close |
| E | Different CRL or legacy peer refuses preflight without extending its original bound; corrupt/lost final confirmation after partial commit closes both native sessions and full setup |
| F | Parallel direct control open receives the existing bounded busy rejection; after credential control drains, lease renewal succeeds. Normal owner serializes jobs; no new control admission quota. Handler/socket/buffer and maintenance shutdown checks pass |

- Go1.26.1 broad `-race -count=1` onf7d0920 with fresh disposable ProductStore fixtures:
  familysession66 PASS/2 skip, tcpforward178/1, roombroker142/24, wholedevice26/0,
  restrictedowner15/0. Counts include parent records. Bootstrap105 PASS/1 skip,
  six failing child assertions plus their failing parent; see mandatory failure below.
  Skips are20 root canonical-profile cases, four DNS cases requiring isolated port53,
  three opt-in performance/process cases and one Python-publication harness. No skip
  substitutes for the new integration DNS gate, which ran explicitly below.
- Real-runtime continuity `-race`, isolated network-none container with only
  NET_BIND_SERVICE: leaf+CRL twice onf7d0920, then once on6dcd727; **six sessions,
  twelve authenticated renewals**, DNS/HTTPS PASS with zero skips. Container image
  `family-connect-renewal-tests:20261030`, digest
  `sha256:ca61f885607656ea89f5726853761c4c533d050faf26b71853575c24ca1ed123`.
- Final cleanup follow-up: all wholedevice/restrictedowner tests `-race -count=1` PASS;
  `TestCloseJoinsSessionMaintenance` (Disconnect/internal failure) and
  `TestConfirmedVPNProfileCannotReachAnotherOwner`, `-race -count=10` PASS.
  Candidate/unready/legacy/partial-commit runtime tests `-race -count=5` PASS;
  DenialBeforeCommit and ConcurrentControlDrains `-race -count=5`:30 PASS records,
  zero fail/skip. Go vet passes all six broad packages and the changed cleanup packages.
- Android JVM repeated after the final Java change: **66 PASS, zero fail/skip**:
  ConnectivityOrchestrator31, CredentialRefresh4, ReadinessRefresh3, RestrictedCache15,
  RestrictedGateway6, RestrictedRecovery7. No full Android suite claim.
- Official local ARM64 builder onb46bff4 passes its mandatory packet `-race -count=3`,
  pinned Xray/patch and16KiB page-alignment build. No diagnostic tags or release signing.
- API27/API35 final candidate: **five targeted checks per API PASS, zero fail/skip**;
  earlierf7d0920 and6dcd727 also passed. Only fresh disposable emulators are used, then
  stopped by their exact owned serials; no phone or unrelated emulator action.

API scope is the3 CredentialRefreshRuntimeTest cases (JNI symbol/invalid retired handle,
owner-bound future lifecycle, node/prewarm separation) plus RestrictedGatewayStorageRuntimeTest
prepare/recover in two separate instrumented processes, one check each. Android Keystore
storage/isolation is exercised. Real authenticated renewal traffic is the native fixture,
not a claim of running a live MESH session inside these Android emulator tests.

Final local qualification artifact SHA256 (not a replacement public118):

| Artifact | SHA256 |
| --- | --- |
| ARM64 libfc_restricted.so | aa82a552d0665ca44ceec078e349bcafd1c5e693c1ff1ca1a544df4ecc66a2b6 |
| Emulator x86_64 libfc_restricted.so | 7321612a5bcb2b771600f407fde7eb11a79cd8ebf0929be02c5a7280604c16eb |
| Disposable emulator friends APK | 1c3205a68353ef0b160d5228b8de732671dc58914153805cc653840579a06827 |

The APK retains version118 solely as a local debug-key qualification build; it is **not**
the published/installed118 artifact and must not replace that immutable version. JNI bytes
inside its ZIP are compared exactly with the freshly built x86_64 library before tests.

### Mandatory inherited failure and retained limitations

`TestProductIdentityOverBootstrapCarrier/{unknown,wrong-family,revoked,wrong-gateway,
stale-crl,stale-revision}` fails with
`successful exchange or rejected TLS emitted exchange failure`. The child failure set is
identical to baselinebea0421 in
`state-client-build/mesh-renewal-exchange-20261105/baseline-bootstrap.jsonl`.
The tests are not disabled or weakened; this gate remains **FAIL**, not an all-green CI
or permission to release. The assertion is diagnostic accounting, not observed unauthorized
admission. Fixing/requalifying it remains required before a later release decision.

Development failures retained: the initial HTTPS fixture used a name outside the existing
pinned-service allowlist and was rejected; fixed only the fixture. A not-ready reply could
be discarded by immediate control RESET; explicit receipt before teardown fixes that path.
The original4s synthetic lease left less than one complete exchange at its80% renewal
point under race/continuous traffic and expired fail-closed; the positive fixture now allows
the protocol to complete without changing production bounds. The separate real lease-expiry
negative deliberately retains a short deadline. Parallel direct control opens retain the
existing bounded busy rejection; after the credential stream drains a lease request succeeds.
The normal owner serializes both jobs and does not create a parallel control-open loop.
Local build harness errors are also retained: missing pinned checkout path, an x86 patch
applied from the wrong Git discovery root, and duplicate incremental Gradle JNI merger
state. Corrected pinned path/isolated patch root and rerun build tasks pass without changing
product source, signing, minSDK or suppressing gates.

Raw evidence is ignored under `state-client-build/mesh-renewal-integration-20261105/`.
No production profiles, private identifiers, test keys or build output belong in Git.
Relevant receipts: `native-regression.jsonl`, `final-isolated-runtime.log`,
`final-denial-control-race.jsonl`, `cleanup-race.log`, `final-owner-race.log`,
`final-negative-race.log`, `final-android-jvm.log`, `candidate-arm64-build.log`,
`candidate-api/android-runtime-receipt.json` and its API-specific instrumented logs.
`final-isolated-runtime.log` SHA256:
`838e6bdee006c1d8b881cdc57d4d1df084d6b3203b889363fced8ee0ce594a88`;
`native-regression.jsonl` SHA256:
`fd51cd4a58a82fe294249403ecfe14eff63212a04419c5ee34da2b6157030105`.

## Next stage — NOT executed

This integration stage stops here. Coordinated **online publication** is separate work:

1. Define eligibility for same-holder/family/gateway/authority leaf/CRL successors, sufficient
   overlap and identical peer CRL/floor. Publish readiness only once corresponding server
   material is ready; no blind replay of an already refused candidate.
2. One fenced writer owns an operation; prepare and verify exact revisions/checksums on
   both authorized NL nodes. Persist a durable decision before exposing committed material.
3. Reconcile crash/restart at every prepare/decision/publish/readback transition; resume
   idempotently from the recorded decision, never invent a new decision from a local file.
   Mixed-node/partial-publication, revocation and stale-writer faults must fail closed.
4. Prove both-node readback and runtime renewal with continuous traffic, then make a
   separate release/activation decision after all mandatory gates, including bootstrap.

None of these publication/activation steps ran. Keep quiesced machinery for ineligible/emergency
changes and never roll back to expired material. Only after its acceptance may exact-source
platform releases and identical running gateway binaries be considered. Scheduled-renewal
traffic on both real nodes and physical/field allowlist acceptance remain later gates.

Rollback here is a normal source follow-up revert, not a server action. No installed build
changed. Never overwrite beta118 or remove maintenance stops to make this candidate live.
