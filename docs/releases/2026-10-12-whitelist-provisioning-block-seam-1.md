# WHITELIST-PROVISIONING-BLOCK-SEAM-1 — local PASS

## Scope and result

`PROVISIONING_BLOCK_CONDITION=READY` **for the tested research-only condition**.
This is not a warm-start/live/whitelist FIELD result. Owner and gateway were not
contacted or modified by this task. `ATTEMPT_CONSUMED=NO`.

Evidence and reproducible tools:
`state-client-build/field65-export16/whitelist-provisioning-block-seam-1/`.
`RESULT.json`, `research-manifest.json`, `SHA256SUMS`, `source.patch` and the
`receipts/` directory contain the detailed records. The candidate is in the
isolated `source/` checkout, not the main dirty product worktree. No commit or
branch was created. 277 sealed entries from recovery and proven egress evidence
were rehashed successfully; their files and the proven egress harness are unchanged.

| Result | Value |
|---|---|
| PROVISIONING_CALL_GRAPH | PASS — restricted-readiness fetch and ACK role |
| SOURCE_SCOPE_EXCLUSIVITY | PASS — no common HTTP/network/protect/bind gate |
| CONTROL_RECORD_SECURITY | PASS — private, bounded, versioned, atomic files |
| OWNER_ONLY_BINDING | package / UID / version / source / APK / signer / nonce |
| BOUNDED_TTL_AND_ATTEMPTS | 900 seconds; maximum 32 blocked logical entries |
| DISPOSABLE_INTEGRATION | PASS — API31 and API35, non-debuggable targets |
| ZERO_PROVISIONING_SERVER_REQUESTS | PASS — zero in armed/restart-armed phases |
| TELEMOST_UNDERLAY_UNAFFECTED | PASS — substitute HTTPS control, not real Telemost |
| ORDINARY_NETWORK_UNAFFECTED | PASS — ordinary Android HTTPS |
| CHAT_UNAFFECTED | PASS — running ChatDeliveryService, authenticated chat registration, mailbox control |
| CACHE_BYTES_UNCHANGED | PASS — encrypted committed file hashes before/after |
| NO_FAKE_IMPORT_OR_ACK | PASS — typed Unavailable; no provisioning HTTP/ACK |
| RESTART/CRASH/CLEANUP_SAFETY | PASS within described fixture/model coverage |
| PUBLIC_BUILD_ABSENCE | PASS — active implementation/assets/API absent |
| COLLECTORS_READY | YES, **local fixture only**; fresh live arm remains required |
| PROVISIONING_BLOCK_CONDITION | READY |
| OWNER_INSTALL / OWNER_INSTRUMENTATION / OWNER_GATE_ARM / OWNER_CONNECT | NOT_RUN |
| PUBLIC_RELEASE / REAL_RESTRICTED_NETWORK_FIELD | NOT_RUN |

## Preserved baseline — historical identities, not fresh runtime observations

Previous acceptance identified research83/code83, package
`com.familyconnect.app.friends`, UID10283, APK
`7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`, source
`f5240994869826c6a28f59e58e38256c688cf6eb`. Last owner state was VPN/app/chat OFF.
No phone command was used to re-observe or change that state here; every ADB
operation targeted a newly created disposable emulator explicitly.

Historical gateway observer: source `abc604b0f8ce431174f260ff41ef9b3b6455ba0c`,
binary `0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`,
invocation `26e8634a47e24d60b6f7f55a58f7282a`, PID1168539/NRestarts0, directory
`9c84fc89a605976bf00d297c9374d30db8bd6f172f3f3b804f497e8be2519a51`.
These are sealed recovery observations, **not claims about the current server**.
SSH, renewal, restart, publication and server configuration changes: zero.

No changes to Telemost, Family TLS, Reliable/Mux, lease renewal, admission,
trust/revocation/floors, routes/protect/bind, Codec2, UI, messenger contents or
production API/server responses. Historical Reliable failures and the six
negative-auth diagnostic assertions remain separate OPEN issues; this is not
a claim that the full security or UI suite is green.

## Actual call graph and role boundary

Paths/line references below are relative to the isolated source. Four wire paths
belong to the role: readiness challenge, fetch, ACK challenge and ACK. They are
emitted only by `FriendsReadinessProtocol.fetch/acknowledge`, invoked by the two
`FriendsAccessAndroid.restrictedReadiness/readinessAck` methods.

| Caller | Entry/network client | When / before CONNECT / background |
|---|---|---|
| Resumed, activated FriendsActivity | 60-second runnable → FriendsRestricted.prewarm → start(false) | Before CONNECT; while resumed |
| Successful registration | FriendsActivity → prewarm | After initial activation, before CONNECT |
| Profile acquisition | FriendsAccessAndroid.profile → prewarm | After normal profile/configuration acquisition |
| Explicit restricted CONNECT | RestrictedTunnelEngine.connect → FriendsRestricted.ready → start(true) | Before NativeRestricted.beginReady |
| Orchestrator recovery | Same RestrictedTunnelEngine.connect → ready | Same shared selection/refresh transaction |
| Concurrent readiness callers | FriendsRestricted.running CompletableFuture | Share one in-flight transaction |
| Restart import reconciliation | FriendsRestricted.start → ReadinessProduct.restart/publish | May ACK prior receipt before a new fetch |
| Successful/failed refresh result | ReadinessProduct.publish → readinessAck | End of the same transaction |
| Process initialization | FamilyApplication only wraps language context | No readiness refresh/network initializer |
| ChatDeliveryService | ChatRuntime → chat registration/events/mailbox | **No direct readiness refresh caller** in this source |
| Service-only chat fallback | ChatCarrier.acquire → cache.usable → native chat acquire | Uses existing cache, not a separate direct readiness fetch |

The last row is not exercised as a carrier in this task. In the disposable fixture,
native chat acquisition is a fail-fast safety trap and its counter stays zero.
Background `prewarm` was exercised while the real ChatDeliveryService was running;
it was not falsely attributed to that service itself.

Network clients for direct readiness: FriendsAccessAndroid → directPost →
ChatNetworkAndroid.openHttps → Android Network.openConnection. The gate precedes
the protocol and this entire dial boundary. The common client, network selector,
SocketFactory, protect/bind and mailbox client are unchanged.

**Role exclusions:** first enrollment/activation, AWG/TCP configuration, ordinary
API calls, chat registration/events/mailbox and updates are not the restricted
directory-provisioning role and are not blocked. This does not establish a
new-device/cold-start mechanism or remove those separate dependencies.

## Implementation and exact source

Source base: `f5240994869826c6a28f59e58e38256c688cf6eb` plus complete `source.patch`.
Canonical changed-file inventory digest:
`d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7`.
The manifest lists all eight changed/new source paths and SHA256 values.

- Research implementation: `src/provisioningResearch/.../ProvisioningWindow.java`
  and `ProvisioningTestGate.java`.
- Other variants: `src/provisioningDisabled/.../ProvisioningTestGate.java`, an
  inert permit with **no arm/inspect/cleanup/storage implementation**.
- Two role methods check a permit before calling the existing protocol.
- A transaction permit around `FriendsRestricted.start` covers vault/cache work,
  refresh, import and ACK. Arm is rejected with `PROVISIONING_BUSY` while a previous
  unblocked transaction is in flight. No network is performed under the gate lock.
- In a blocked transaction only: skip persistent `cache.attempt` backoff write,
  restart ACK and publish/ACK; feed the existing `Unavailable` exception into
  the unchanged `RestrictedBootstrap.refresh` safe-cache path. Record a local
  failure result, not an ACK. The validator and selection policy are unchanged.
- Build/source guards validate the exact delta and the reused native manifest.
  The existing public Friends provenance guard is not weakened. A disposable
  signing flag is rejected for the research field artifact.

The original clean-source native guard correctly rejected the first dirty-delta
build. A separate research reuse guard now verifies the preserved native bytes
against their original source and the new Java delta independently. Build failure
receipts are retained; it was not bypassed by pretending that native was rebuilt.

## Control/security/cleanup contract

`noBackupFilesDir/provisioning-research-v1/`, mode0700; AtomicFile `control` and
`commit`, mode0600, UID and size checked. Control JSON is <=4096 bytes; commit
stores its digest. Fields: schema1, provisioning_only role, runtime binding,
random 256-bit nonce, wall/monotonic arm time, absolute expiry, boot count,
blocked count, state. No endpoint, token, key, profile or user identity material.

Runtime binding includes actual package, UID, PackageInfo version84, source-delta
digest, APK SHA256 and signer digest. Wrong/malformed/mismatched records do not
activate a block. APK updates invalidate the old record. Same-boot process death
does not reset the counter/expiry; reboot invalidates it. Clock rollback and
monotonic expiry cannot extend it. Control and digest torn writes become inactive,
not a permanent block. Replaying an old record against the current digest fails;
this is not a claim of protection from arbitrary same-UID/root storage replacement.

900 seconds derive from existing maximum CONNECT budget300s, prior bounded
observation300s, operator preparation120s, cleanup60s and evidence margin120s.
This is a **test-control** TTL, not certificate/directory/lease TTL. Limit32 covers
the resumed UI's at-most15 periodic entries in that window plus bounded startup,
recovery and concurrent calls. These are logical gate entries, not HTTP responses.
The 32nd entry is blocked and consumes the window; later calls operate normally.
Collector acceptance rejects CONSUMED/EXPIRED/CLEANED or an observation past expiry.

Arm is not a one-shot HTTP failure. Repeated fetch and ACK attempts remain blocked
through the window. Caller cancellation does not silently disarm it. Explicit
cleanup, matching the current nonce, writes CLEANED without touching cache.
Lost cleanup/helper death cannot create an unbounded block. The bounded tombstone
and digest may remain in private noBackup storage; no unbounded history is kept.

The separate control APK has only an instrumentation declaration, no exported
Activity/Service/Receiver/Provider, and no INTERNET permission. It checks its own
signer against target, exact expected APK hash and package before invoking control.
It never refreshes, imports, opens Activity, creates identity or invokes native.

**Important observed platform limit:** API31 userdebug permitted wrong-signer
instrumentation to inspect the target despite its non-debuggable manifest. This
before receipt is preserved. The official helper now performs an explicit signer
check; wrong signer is rejected before gate access on that same fixture. Android
production signature isolation was not inferred from the userdebug experiment.
This is an operator-controlled seam, not a sandbox against malicious privileged
ADB/instrumentation or arbitrary code already executing as the target UID.

## Local acceptance and counters

45 targeted Java tests PASS: 12 new controlled-clock gate cases plus existing
cache/bootstrap/refresh/product tests. 14 existing operator/credential guards
PASS. Coverage includes disarmed operation, repeated blocks, process/helper death,
boot identity, clock rollback/expiry, max attempts, malformed/torn control,
binding mismatch, stale nonce/record, write failure, 24 concurrent entries,
late-result exclusion by busy transaction and real safe-cache fallback.

Non-debuggable disposable API31 and API35 targets execute the real candidate
FriendsRestricted/Access/protocol/cache/native offline validator path. Only fixture
endpoint literals, observational counters and a no-carrier safety trap differ;
their diffs are preserved separately. The candidate APK contains none of those
fixture changes. Synthetic identities/CA/cache and real local HTTPS are used;
the server verifies device signatures and returns normal signed validation input.
An existing x86 Python support runtime is reused with the current candidate's
Python app/common modules; fixture runtime hashes are recorded.

| Server HTTP path/category | DISARMED, per API | ARMED, both APIs total | CLEANED, per API |
|---|---:|---:|---:|
| readiness challenge | 1 | 0 | 1 |
| readiness fetch | 1 | 0 | 1 |
| ACK challenge | 1 | 0 | 1 |
| ACK | 1 | 0 | 1 |
| underlay substitute | — | 2 | — |
| ordinary HTTPS | — | 2 | — |
| chat registration | — | 2 | — |
| chat/mailbox HTTPS control | — | 2 | — |

Armed phases: `FriendsAccessAndroid` provisioning dial counter0; server count0;
typed Unavailable for direct fetch/ACK; production prewarm and CONNECT/recovery
**pre-native selector** use the validated cache; eight concurrent selections return
identical bytes; cancellation rejected; encrypted cache SHA unchanged. Real
ChatDeliveryService runs and authenticated chat registration completes. Its store
remains present; no native chat acquire occurs. Mailbox control is a substitute,
not an end-to-end message delivery claim.

The zero dial probe is before URL/Network connection creation, combined with source
control-flow proof. No separate DNS packet capture is claimed; the actual production
endpoint is an IP literal. Other fixture traffic is deliberately allowed.

Both API31 and API35 actual reboots expire the record; subsequent real provisioning
works. Same-signer helper, wrong APK, stale cleanup, helper exit and force-stop
tests PASS. Full-pipeline response races are bounded by the tested transaction
lease; late result behavior is additionally exercised at the deterministic core
boundary. No real Telemost/session/TUN/Activity is started by the fixture.

Reproducible commands, from the repository root (ADB stages only on the disposable
serials encoded in these scripts):

```sh
R=state-client-build/field65-export16/whitelist-provisioning-block-seam-1
python3 "$R/local_tests.py"
python3 "$R/prepare_build.py"
sh "$R/build_android.sh" assembleResearchProvisioning assembleRelease
python3 "$R/fixture_build.py"
python3 "$R/helper_build.py"
python3 "$R/disposable_android.py" 31
python3 "$R/disposable_android.py" 35
python3 "$R/fixture_server.py"
# Install fixture only on emulator-5592 / emulator-5594; reverse local tcp:18443.
# am instrument -w -r -e mode sequence <fixture>/com.familyconnect.app.SeamFixture
# Modes restart/reboot require the preceding sequence/checkpoints, not owner state.
python3 "$R/helper_fixture.py"
python3 "$R/artifact_guards.py"
python3 "$R/collector_fixture.py"
```

The fixture must be generated with fresh synthetic validity, and each initial
sequence uses a clean **disposable** target. Do not run its seeder/clear commands
against the owner. Fixture install commands and exact server counters are saved.
No owner private data is used. Earlier fixture packaging mistakes (duplicate DEX/
resources and an incorrect emulator property name) were fixed locally; their logs
are retained, and they never caused an owner action.

## Collectors

Safe `FCProvisioningGate` events expose schema/source/random generation/state/
expiry/count only. The parser rejects source/generation/time/state/counter mismatch,
consumption and an expired observation. It was checked against actual Android gate
logs, not only synthetic JSON. An arm receipt is insufficient for a future PASS:
blocked events, zero provisioning server requests, exact cached/native input,
admission/HELLO/dedicated, gateway nonce egress and first-close evidence remain required.

The existing collector generator is exercised offline against observer hash
`0ccaaf81…2667a` and its sealed ABI/symbol offsets. Stale binary/invocation fails.
The local generator requires a supplied fresh preflight invocation instead of
hard-coding the recovery PID. The first-incident/operator gate and proven external
egress harness remain unchanged. BPF attachment/listeners/current runtime freshness
are **not live-validated in this task**; no collector was started on owner/gateway.

## Research artifact — built/signed, not installed or distributed

- `EXIT-research84-provisioning-seam-arm64.apk`, versionCode84,
  `0.1.18-research84-provisioning-seam`, same package, non-debuggable, minimum API31.
- APK SHA256: `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Control helper SHA256: `cc567785dac456ce8eee91a1d00b08825e88986f67225218c0cf280e32b27064`.
- Native **reused, not rebuilt**: `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`,
  original f5240994 source/restricted-build metadata retained truthfully.
- New embedded `provisioning-seam-build.json` declares the Java delta, research-only
  seam and native reuse. It is absent from the public release control artifact.
- Public release APK guard confirms no active Window implementation, control API,
  storage path, log tag or seam metadata; its no-op permit remains inert.
- Signing used the accepted vault-backed local protected dialog and expected
  existing signer. No plaintext signing material, owner install or public upload.

## Cleanup, limits and next operation

Evidence saved before local teardown. The control helper was removed from the
disposable target; both newly created emulators and local HTTPS endpoint were
stopped. Disposable AVD images are removed after process checks. Harness, source,
signed research artifacts and evidence remain. No owner cache/enrollment/history/
publisher/AWG change; no gateway observer/receipt/rollback removal or restart.

This seam models **DIRECT RESTRICTED PROVISIONING UNAVAILABLE only**. It does not
model DPI, arbitrary IP filtering, Orange behavior, Telemost availability in a
restricted mobile network, loss, throttling or cold start. No general whitelist
architecture PASS or renewed egress/lease proof is claimed.

`OWNER_CONNECTS=0`, `FULL_PHASE_REQUESTS=0`, `ATTEMPT_CONSUMED=NO`.
`READY_FOR_CLEAN_RETRY` is not promoted by these local tests: current gateway,
credentials, accepted directory and owner cache have not been freshly checked.

**Exactly one next operation:** a separate fresh gateway/credential/cache preflight
and, only if its prerequisites pass, the controlled owner in-place update/arm plus
one physical manual warm-start CONNECT with provisioning blocked. Not executed here.
