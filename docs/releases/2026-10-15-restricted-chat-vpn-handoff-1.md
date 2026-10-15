# RESTRICTED-CHAT-VPN-HANDOFF-1

**RESULT: KNOWN_CALLER_CONFLICT_FIXED_LOCALLY.** Implemented product-source
derivative, passing local ownership/race/security tests and Java/JNI compile/link
checks. This is **not** an installed, accepted or released candidate.

`PRODUCTION_ACCEPTANCE=FAIL`; `DEVICE_ACCEPTANCE=NOT_RUN` for this derivative;
`HISTORICAL_CAUSAL_BINDING=NOT_PROVEN`. The historical owner HELLO_RECEIVE failure
is not causally attributed to chat by this fix.

## Base and delivered diff

- Starting review: `4598287c82fcc35101574f19d4df30a70a763eb9`.
- Exact retained research84 base: `f5240994869826c6a28f59e58e38256c688cf6eb`;
  research source delta SHA256
  `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7`.
- Derivative constructed from that Git tree and its eight manifest-bound research
  overlays; all 32 prior source bindings checked against this construction.
  Neither root main nor archived source snapshots were used as the development base.
- [Reproducible product patch](../../research/chat-vpn-handoff-20261015/source.patch),
  SHA256 `a9be16b5be05788d0ad1c9c19497044a68f01e733a21739a33ba4ae507189c64`.
  [Before/after per-file hashes](../../research/chat-vpn-handoff-20261015/source-manifest.json)
  bind ten files: new coordinator/tests, native main/chat/JNI, Java startup/native
  declarations, and the existing messenger-lab sharing fixture's three files.
- [Changed full files, tests and runners](../../research/chat-vpn-handoff-20261015/README.md)
  are a review projection of the working derivative. Original selected snapshots,
  frozen binaries, versions, main and workflows are unchanged. Publication commit
  SHA is neither research84 APK source SHA nor an accepted binary source identity.

## Lifecycle / ownership contract

`ReserveVPN → cancel independent chat → join opener/session/workers/underlay/JNI
cleanup → ordinary VPN bootstrap → Publish → strict-compatible chat borrowing`.

1. The gate is **process-wide**, deliberately more conservative than a per-identity
   map. Every independent chat/VPN open is serialized regardless of profile hash.
   Credential rotation retaining a broker Identity cannot bypass the gate. A VPN
   may interrupt even a different-scope independent chat; it cannot borrow it.
   This avoids deriving a weaker identity from device ID or credentials hash.
2. Borrowing is a separate decision: fresh existing `DeliveryMaterial` validation,
   identical complete profile hash, live VPN context/session, and original delivery
   expiry. Family, signing key, gateway, authority, CRL/revision material remain in
   the validated profile. No authorization, expiry, renewal or CRL policy is relaxed.
3. Reservation is atomic with chat acquire. New acquire during pending VPN returns
   unavailable rather than opening another provider session. An opening chat is
   cancelled; a late successful opener result is closed, never published as READY.
4. Independent chat stays in the occupied slot until opener completion,
   `session.Close()`, registered native request/mailbox workers, underlay closure
   and JNI global-reference disposal have completed. `done` closes last. Last
   release only initiates cancellation; it does not clear the occupied slot.
   Actual Family stream Close joins its workers; existing carrier Close waits its
   cleanupDone. No change to these protocol/carrier implementations is made.
5. `Work()` registration is serialized against sealing a closing generation.
   Native mailbox ownership covers both copy directions and bridge FD cleanup;
   request ownership covers the request's entire return path. Cancelling an HTTP
   timer is not interpreted as completion of that worker. The Java-owned socket
   endpoint remains Java-owned; cancellation closes the native peer, not an
   unrelated or potentially reused Java FD.
6. VPN cancellation/failure releases its reservation after its own cleanup. If an
   old chat cleanup still runs, that chat slot continues to block another open.
   There is no permanent WAITING_FOR_VPN state. Existing ChatCarrier detects state
   `<0`, releases its stale handle and reacquires on its next normal operation.
   ChatRuntime/ChatDeliveryService and ChatCarrier.close() are not used to pause chat.
7. Borrowed consumer release does not close VPN. VPN cancellation invalidates its
   borrowed contexts and cleanup joins their workers. Pointer-generation checks,
   monotonic native handles and idempotent releases prevent old callbacks/releases
   from removing a new reservation/session. No lock is held across worker joins.
   Chat no longer takes ownerMu, eliminating the former chatMu → ownerMu dependency;
   the VPN side does not acquire chatMu.
8. Java passes the **remaining existing connection budget** through JNI. Reservation,
   drain and subsequent open share one native cancellation timer. No new full
   timeout is appended; the existing Java deadline cap and 120s ExchangeTimeout
   are not increased. Waiting happens in the native startup goroutine, not in begin
   on the UI thread. Failed drain emits `ownership_drain_failed`, state 3 and the
   existing STARTUP diagnostic category. Ordinary successful drain emits
   `ownership_cleanup_complete`; no identifiers/payloads are added.
9. Local cleanup is **not** proof of server holder deletion. ChallengeAfterCleanup
   remains the final guard. No server protocol, single-holder/capacity, Reliable,
   Mux, DNS, seed-supervisor or protect/network-binding implementation changed.
   No automatic retry of chat registration or another non-idempotent request added.

## Before / after and fixed regression matrix

The first check on unmodified research84 is the source-bound caller contract:
[before](../../research/chat-vpn-handoff-20261015/results/before-contract.log)
fails four ownership assertions, whereas
[after](../../research/chat-vpn-handoff-20261015/results/after-contract.log)
passes the same five assertions. This proves the missing caller integration;
**it is not execution of the original JNI on a host**. Separately, the unchanged
real Broker/Family-TLS B test records same-identity ACTIVE wait, zero HELLO, bounded
client/server failure and no holder eviction
([before B receipt](../../research/chat-vpn-handoff-20261015/results/before-admission.log)).

After implementation, tests call the **production Coordinator**, not an independent
test model. The native adapters call the same compiled implementation. The broker
integration uses the previous real Broker/Exchange/requestTransport/Family-TLS
fixture with synthetic certificates and in-memory carrier. It observes local
cleanup completion while server cleanup remains held; the server still blocks
HELLO, then records old release sequence 15 → new grant 17 → one received HELLO.
No real room, provider request, credential mutation or owner activity occurs.

| Required case | Local result / observation |
|---|---|
| A chat-first READY | PASS: old chat invalidated, new independent open denied, full cleanup joined, VPN published, chat borrows; real HELLO succeeds after server cleanup |
| B VPN-first READY | PASS: multiple borrowed consumers, no independent chat create, repeated chat release leaves VPN alive |
| C opening/concurrent | PASS: cancelled opener returning a late session is closed, not published; 40 simultaneous acquire/reserve schedules per suite, 160 total |
| D cleanup gate | PASS: hold session.Close and a registered worker separately; neither READY nor JNI dispose is allowed before the corresponding completion |
| E cancel/failure | PASS: before reserve, during/after cleanup, simulated startup failure and bounded wait timeout; reservation released, draining owner still excludes opens, later chat recovers |
| F disconnect/stale generation | PASS: borrowed worker drain, multiple consumers, repeated release, stale publish/release versus replacement VPN; session/dispose callbacks once |
| G profile/security | PASS: changed hashes cannot bypass serialization/borrow; expired delivery and failed VPN rejected; unchanged real delivery binding/trust/expiry/revocation and Family admission tests pass |
| Existing broker A–D | PASS including expected blocked B; holder eviction/capacity/admission invariant unchanged |

Fixed execution: **one normal + three race repetitions** per suite, no retry-until-pass.
Four packages: restrictedowner, bootstrap, wholedevice and familysession.
[Runner receipts and executable hashes](../../research/chat-vpn-handoff-20261015/results/host-matrix.json),
[compiled source hashes](../../research/chat-vpn-handoff-20261015/results/compiled-source.json),
[counts](../../research/chat-vpn-handoff-20261015/results/counts.json) and complete small
test logs are published. Counts include parent/subtest PASS lines, not extra
independent acceptance scenarios. All eight test runs and eight builds exited 0.

The public host runner uses the existing baseline carrier snapshot plus the actual
new coordinator and test fixtures. Its executed protocol/Family/wholedevice mechanisms
are bound by the earlier research84 comparisons; it is not a frozen binary test or
an assertion that the entire baseline tree equals research84. The native builds use
the full retained research84 derivative, not that host carrier staging directory.

Preliminary setup failures are retained: default Go environment could not resolve
stdlib and tried an unwritable default cache; explicit private GOCACHE and retained
GOPATH fixed the environment. Initial native build rejected absent VCS metadata;
the isolated derivative uses explicit `-buildvcs=false`, with source hashes recorded
instead. No behavioral test failed and was hidden. A first successful compile set
is retained separately; final builds use canonical STARTUP rather than inventing
a new startupdiag stage. Error classification itself is unchanged.

## Java / JNI / native compatibility

[Final build receipt](../../research/chat-vpn-handoff-20261015/results/android-build.json):
Go 1.26.1, Android arm64/API26, NDK 28.2.13676358; normal, fc_owner_diagnostic and
fc_messenger_lab c-shared compile/link PASS. Java 17 source/target compilation of
NativeRestricted, RestrictedTunnelEngine, unchanged ChatCarrier, and adjusted
MessengerLabActivity PASS. Dependencies come from retained research84 compiled
classes, SDK35 and cached Gson; this is not a fresh complete Gradle/APK build.
Generated JNI headers pass C prototype checks for production and lab entrypoints.

| Local test library | SHA256 |
|---|---|
| normal | `00d1c80f2f097b69621556fa718f1ed862a57617a176fb7a0eff9f2cdc32c652` |
| fc_owner_diagnostic | `d6e66dc8ae0d284c7d83533ee20a1b25e0458c96f488c4ab7f5bbf5c907f11cd` |
| fc_messenger_lab | `136e7b1dde3f58c79a55cce2ea2dfe4d25d8f6c0e0c7aee1a261a658ccc78ca6` |

The existing cached patched Xray source from native-packet-tests is the build input;
this task does not independently re-attest its full upstream Git ancestry. No new
dependency/PKI work or native packaging/signing metadata is created. Libraries stay
local, are not APKs, and must not replace the historical native binary identity.
The lab sharing helper no longer fabricates VPN ownership from a live chat session;
it follows reserve/drain/new local fixture open/borrow. It is compiled, **not run**.

## Remaining limitations and publication

- No JNI execution, actual Android FD/global-reference lifetime measurement,
  emulator/device test, TUN/DNS/HTTPS test, provider signaling/media test or UI-thread
  runtime validation. Host cleanup assertions cover production coordinator hooks;
  native adapter correctness additionally relies on source review and build checks.
- Before-case caller evidence is a failing source contract plus real server B, not
  an Android reproduction. A–G host successes do not retroactively prove chat owned
  the historical owner session. Historical causal binding remains NOT_PROVEN.
- Historical source objects absent from published ancestry remain absent. Selected
  before/after files and patch are readable; full retained tree, SDK/dependency caches,
  reference class directory and build binaries remain local. Host matrix is runnable
  from the published source snapshots; Android reconstruction also requires those
  explicitly listed retained inputs. No local /tmp link is offered as public evidence.
- Source diff, source inventory, tests, runners, bounded logs, report, STATUS/PLAN
  and publication index are the only publication scope. No frozen snapshots,
  root product source, workflow, main, support export or credential file is changed.
- Review-branch paths do not match client APK/deployment workflow path gates;
  ordinary sandbox CI may run. No acceptance workflow is manually invoked.

**PRODUCTION_UNCHANGED:** owner CONNECT/reconnect/export/native poll, ADB/SSH/runtime
interventions, APK installs, process restarts, deployments, real provider actions,
credential mutations, triggers and releases **all 0**. Product source changes are
local to the authorized derivative; no device or production acceptance is promoted.
Diagnostic error classification remains a separate, unimplemented next task.
