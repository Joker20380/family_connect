# MESH renewal: active-session integration / 5 November2026

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

## Qualification checkpoint

Source `f7d092041d550683d1d98ad6b6a1b68558cffac1` was pushed and its remote SHA
verified. Its isolated real-runtime continuity/DNS run passed twice for both leaf and CRL;
API27/API35 each passed five scoped emulator checks (no physical installation). The broad
native race gate passed the five affected packages; bootstrap retained the same six baseline
diagnostic-counter failures. Final qualification does not claim an all-green release gate.

A cleanup follow-up makes whole-device Close join maintenance and its callback before native
owner disposal. Internal fail-close uses a non-joining stop path to avoid joining itself.
The confirmed JNI callback no longer takes the global owner mutex held by Disconnect:
the captured owner's cancellation, exact session and coordinator ownership fence publication.
Focused cleanup and replacement-owner tests pass with `-race -count=10`. This follow-up
requires fresh ABI builds/API checks; the earlier platform receipts alone do not qualify it.

At source-checkpoint preparation, Android JVM **66 tests PASS** in CredentialRefresh,
RestrictedGateway, ReadinessRefresh, RestrictedCache, RestrictedRecovery and
ConnectivityOrchestrator. Native integration qualification and Android API27/API35 ABI/runtime
checks are being completed; this paragraph is not a completed platform acceptance claim.

The real-runtime fixture uses two real Family TLS handshakes (original control and dedicated
data), bindGateway, Broker monitor/lease timer, the same gateway configure/handlers and
SessionMaintenance as runtime. It uses disposable identity/CRLs, local echo and a pinned
test HTTPS service with certificate verification enabled. No mock deadline setter is used.
Positive tests use10s synthetic leases and12s initial security bounds, followed by two
successors; production lifetimes/timeouts are unchanged. Root DNS qualification uses only
an isolated network namespace with a local port53 fixture, not external DNS/Internet.

Development failures retained: the initial HTTPS fixture used a name outside the existing
pinned-service allowlist and was rejected; fixed only the fixture. A not-ready reply could
be discarded by immediate control RESET; explicit receipt before teardown fixes that path.
The original4s synthetic lease left less than one complete exchange at its80% renewal
point under race/continuous traffic and expired fail-closed; the positive fixture now allows
the protocol to complete without changing production bounds. The separate real lease-expiry
negative deliberately retains a short deadline. Parallel direct control opens retain the
existing bounded busy rejection; after the credential stream drains a lease request succeeds.
The normal owner serializes both jobs and does not create a parallel control-open loop.

Raw evidence is ignored under `state-client-build/mesh-renewal-integration-20261105/`.
No production profiles, private identifiers, test keys or build output belong in Git.
Inherited bootstrap diagnostic-counter failures remain a mandatory reported gate, with
baselinebea0421 evidence in the previous exchange report; no disabled test or all-CI claim.

## Next stage — NOT executed

After completing this integration qualification, stop. Coordinated **online publication**
is separate work: eligibility limited to compatible same-holder leaf/CRL renewal; single
writer, per-node preparation/readback, durable decision, crash-at-each-transition recovery
and reconciliation across both NL nodes. Keep quiesced machinery for ineligible/emergency
changes and never roll back to expired material. Only after its acceptance may exact-source
platform releases and identical running gateway binaries be considered. Scheduled-renewal
traffic on both real nodes and physical/field allowlist acceptance remain later gates.

Rollback here is a normal source follow-up revert, not a server action. No installed build
changed. Never overwrite beta118 or remove maintenance stops to make this candidate live.
