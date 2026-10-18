# WHITELIST-CACHE-READINESS-2 — read-only cache gate

## Result

**PARTIAL. READY_FOR_CLEAN_RETRY=NO.** First blocker:
**CLIENT_CACHE_ACCESS_REQUIRES_LIFECYCLE_PERMISSION**.

Research83 has no available non-lifecycle live cache export. The installed owner
instrumentation is inactive; starting it restarts the target process, and the old
wrapper also opens FriendsActivity. Neither is authorized for this preflight.
No instrumentation, Activity, prewarm, native beginReady, provisioning refresh,
owner authentication, CONNECT, new room, full-phase request or production write
was performed. OWNER_CONNECTS=0; FULL_PHASE_REQUESTS=0; ATTEMPT_CONSUMED=NO.

Evidence: `state-client-build/field65-export16/whitelist-cache-readiness-2/`.
Safe runtime/phone snapshots, local source audit, fixture tests, RESULT and manifest
are retained separately. Previous157+2+168+21+65 sealed entries verified unchanged.
No APK/gateway rebuild or deployment; no product source changes. Proven egress and
lease continuity are not re-tested or weakened. Historical fatal cause stays UNKNOWN.

## GATEWAY_STABILITY / OBSERVER_STATE

Fresh entry19:53:08UTC and chain/runtime checks19:53 and19:58UTC agree:

- Invocation `dd70fcd8467847bea72b7aba20d3384a`, PID788144, start19:19:05UTC;
  NRestarts0, active/running. Short8s checks stable; no restart observed across checks.
- Loaded/next SHA256
  `0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`.
  Clean observer source `abc604b0f8ce431174f260ff41ef9b3b6455ba0c` unchanged.
- Actual argv matches effective unit: observer binary, existing gateway.json and
  directory export, loopback18444, duration4h, chat-services, seed-rotate-after3h.
  Unit/drop-in/environment-file hashes are saved; secret environment values are not.
- App receipt directory0700/service979; manager directory0700/root; files0600,
  retention32 per layer. Entry: zero application receipts, one manager receipt.
  That receipt is the previously controlled baseline exit0, not a new natural fatal.
  Receipt environment and ExecStopPost remain armed. No follow/journal/kernel query.

The final observer snapshot and its timestamp are recorded in RESULT. A changed
invocation/new terminal receipt overrides readiness and stops preparation. This is
bounded observation, not a guarantee against a later exit or a4h stability PASS.

Final20:02:44UTC: same PID/invocation/NRestarts and loaded/next SHA. Observer helper
bytes match the reviewed source; root-owned0644. Receipt set unchanged, no natural
fatal captured. Server expiry headroom then5683s; chain itself last probed19:58UTC.
New evidence is sealed by21 SHA256 entries; RESULT and manifest are included.

## SERVER_ACCEPTED_DIRECTORY_SET

Current directory SHA256:
`bb5c8eb04bb8fe95fd4e2d7be214ff906b1acf264b96ba2d939329e3189d8959`.
Issued `2026-10-11T19:19:09.966146309Z`; nominal expiry
`2026-10-11T23:19:05.956440503Z`. RU/NL bytes match at19:58:58–19:59:01UTC.

| Snapshot | Generation | Validity / currently accepted |
|---|---|---|
| Current bb5c8eb0…d8959 | Runtime seed1; no directory generation field | Issued19:19:09 to23:19:05 nominally; accepted by this invocation's seed contract |
| Directories belonging to previous invocations | Not restored into this process | Not accepted by this invocation |
| Future in-process seed2 | Not created/published at observation | Not in current accepted set |

This is not inferred from a publication file alone: same loaded source, actual
3h rotation argv, unchanged invocation, first publication time and overlap manager
control flow establish that only generation1 can be current before22:19:09UTC.
Its terminal event causes process termination. No owner challenge/seed join is used
as a probe, and Telemost network reachability is NOT re-proven by this inference.

`carrier/bootstrap/seed_overlap.go` retains at most two generations within one
process. If configured rotation succeeds, the previous seed remains until its own
deadline/parent shutdown, not indefinitely. It does not survive process restart.
No second accepted generation or cross-restart overlap exists in this snapshot.
Security expiry21:37:28UTC is earlier than this invocation's scheduled rotation;
nominal directory lifetime cannot extend authorization.

Directory v1 has **no independent signature, revision, generation or CRL floor**.
Trust comes from authenticated delivery plus signed issuer/Family certificates/CRL
and grant/binding checks. Calling this an independently signed directory would be
incorrect. Safe family/gateway/seed hashes are saved; no room URL is exported.
Bindings match current profile and signed delegation. Profile revision floor1;
CRL floor22247 at the final paired trust check, not a directory field.

## CLIENT_CACHED_DIRECTORY / CACHE_SERVER_COMPATIBILITY

| State | Exact fingerprint | Validity / selection evidence |
|---|---|---|
| CLIENT_CACHED_DIRECTORY | UNKNOWN | Not decrypted or read; current bindings/floors/denial/expiry UNKNOWN |
| SERVER_CURRENT_DIRECTORY | bb5c8eb0…d8959 | Identified and synchronized |
| SERVER_ACCEPTED_DIRECTORY_SET | Current invocation seed1 only | Source/runtime contract above; no old-process seed |

**CACHE_SERVER_COMPATIBILITY=CACHE_UNKNOWN**, not CACHE_EXPIRED and not
CACHE_VALID_BUT_NOT_ACCEPTED. The last server-side authenticated fetch was18:08:31UTC,
ACK18:08:32UTC, research83/import READY, revision3/minimum CRL22046, response expiry
19:09:37UTC. That historical response is expired. Its ACK contains no directory
fingerprint and cannot establish the current encrypted cache or native selection.
No successful fresh import or client headroom is inferred from current server health.

Frozen research83 source audit:

- `RestrictedVault.java`: private no-backup AES-GCM/AndroidKeyStore AtomicFile.
  No externally readable metadata companion or public cache provider.
- Main manifest: non-exported DiagnosticsProvider and services; release is not
  debuggable. Debug Activities and ownerDiagnostic fault receiver are not enabled
  by this research83 artifact (embedded diagnostic_only=false/fault_schema0).
- `DiagnosticsProvider.java`: only explicitly shared, bounded diagnostics files;
  no live vault RPC. Existing diagnostics are not a current cache readback.
- Existing EgressOwner is instrumentation, not an attach-only read endpoint.
  `observer.py` starts instrumentation then FriendsActivity. Both were left idle.
  Fresh ADB state finds no active instrumentation or EGRESS_SNAPSHOT receiver.

Only package/version/hash/process/services/framework and helper installation state
were read on the phone. No key, identity material, private profile, messages or
contacts were read. No permission change, run-as, root or export bypass was attempted.

## EXACT_CONNECT_SELECTION / AUTHENTICATED_PREPARATION_REFRESH

Research83 source remains `f5240994869826c6a28f59e58e38256c688cf6eb`:
`FriendsRestricted.ready → RestrictedBootstrap.refresh → Selection.copy →
RestrictedTunnelEngine → NativeRestricted.beginReady(response)`.

On successful refresh, the verified/imported returned B is cloned and passed
directly to native; there is no later cache A reread at that boundary. On a typed
availability failure only, `cache.usable(now)` is read under the vault lock and
validated for expiry/native trust. Authorization failure tombstones usability.
Monotonic issued_at/revision/CRL and equal-issued content conflict checks remain.
This is source-contract verification, **not** CONNECT_WOULD_USE_B evidence for the
unread current owner cache. A pending single-flight selection is likewise not
observable through the permitted export surfaces.

AUTHENTICATED_PREPARATION_REFRESH=NOT_PERFORMED; REFRESH_RETURNED_B,
IMPORT_COMMITTED_B and exact current CONNECT selection are NOT_PROVEN. Unknown cache
is not a proven mismatch authorizing a blind refresh. Existing prewarm/Activity
wrappers would violate this task's lifecycle restriction. WARM_CACHE_STAGED=NO.
WHITELIST_COLD_START_READY=NO; no cache deletion/new-device simulation was attempted.

## CHAIN_AND_HEADROOM

Fresh strict server-only TLS at19:58UTC: hostname/SNI
`gateway.family-connect.test`, actual served DER equals profile; chain PASS.
Leaf SHA `06c2c41ea3a95edd637f3ccd0bf87e2f9f0c2258f982430314f1cd36753d1a17`;
authority SHA `d5a0d0dba0a90c6cedaf5365007edebd2e75257a0c05e4453b8fde5f1959dc18`.
Leaf AKI equals authority SKI; signature valid; leaf not revoked. Authority/root
delegation signature verified, sequence10/minimum revision1; owner grant revision3,
revoked0. Server chain PASS is not CLIENT_MTLS_ADMISSION, which is NOT_ATTEMPTED.

Effective server authority/leaf/grant/CRL limiting expiry **21:37:28UTC**. At19:58:48
leaf headroom5919s; final paired CRL22247/DER hash and directory match RU/NL. Current
profile hash changes with normal CRL synchronization (22237→22247), not a task
renewal or directory change. No trust/floor rollback or TTL adjustment occurred.

Required existing guard is **strictly more than1200s**, from the prior clean retry's
`clean_gate.require_preflight`, retaining the900s scoped fault window and cleanup
margin, not inventing a new TTL. SERVER_HEADROOM_SUFFICIENT=YES at observation.
CLIENT_EFFECTIVE_HEADROOM=UNKNOWN, so overall HEADROOM_SUFFICIENT=UNKNOWN pending
the same cache access gate. Renewal was unnecessary for server headroom and not
performed; it would not solve the missing client cache evidence.

## PROVISIONING_BLOCK_CONDITION / COLLECTORS_READY

Existing condition was inspected and **not applied**: source-IPv4 map + exact
restricted-readiness/challenge/ACK paths,503 availability failure, hash-guarded
restore,900s auto-restore. Current RU ingress has one expected location, no old
denial marker, hash128d4cdd…4e76. No reload, firewall or live owner request.

Offline fixture executes the existing transform/restore with local files and
mocked command runner: target paths match; unrelated paths/default addresses are
not targeted; concurrent config prevents overwrite; restore is byte-exact and
idempotent. No nginx/systemd command actually runs in this fixture. This is not a
new server syntax/live reachability PASS. Telemost DNS/signaling/media are not
targets of that rule; current network reachability remains untested.

**PROVISIONING_BLOCK_CONDITION_READY=NO** for immediate execution: the old source
scope is stale and an IP-scoped condition does not prove exclusivity for other
users behind shared NAT. No old address is reused or new blocking mechanism deployed.
This is recorded as an unfulfilled later gate, not a reason to bypass cache access.

**COLLECTORS_READY=PARTIAL / NOT_ARMED.** Existing incident/first-close/gateway/egress
sources parse locally; unchanged probe and owner-helper APKs are still installed
and match their proven artifacts. Prior deterministic A/B/timeout/replay lifecycle
evidence remains PASS and is not re-run. Fatal observer is active.
The old gateway collector pins baseline5e877eb1, not observer0ccaaf81, and needs
fresh symbol/layout/PID binding before use. The old owner collector opens Activity
and is not safe to invoke unchanged here. No collectors/endpoints are started,
no manual gate is displayed, and no live readiness PASS is manufactured from syntax.

## Final gates and cleanup

| Required gate | Result |
|---|---|
| Stable current invocation / observer armed / loaded-next-config | PASS in bounded snapshots |
| Served chain / current publication | PASS |
| Complete credential headroom | UNKNOWN: server sufficient, current client material unread |
| Exact client cache / accepted-set membership / exact selection | UNKNOWN |
| Provisioning block / Telemost availability | NOT_READY / UNKNOWN |
| No conflicting restricted owner | UNKNOWN beyond framework VPN OFF |
| Collectors before future gate | PARTIAL; not running |
| Attempt unused | PASS |

Final phone19:59:01UTC: package `com.familyconnect.app.friends`,
`0.1.18-research83-bootstrap`/code83/UID10283, same process19925, non-debuggable.
APK SHA `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8` binds
unchanged signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`
and prior exact embedded/source/native provenance. VPN OFF; app ON;
ChatDeliveryService ON. Messenger route, pending native/prewarm and owner admission
cannot be proven absent by service presence; they remain UNKNOWN, not blamed on chat.

Five final offline guard/fixture tests PASS, including unknown client headroom not
being replaced by server chain, all14 mandatory gates, fatal precedence and safe
restore. No full product/security suite claim; historical six negative-auth
diagnostic assertions and Reliable/call investigations remain separate.

No owner state was changed; no helper was installed/launched/removed. Existing
helpers, cache/enrollment/AWG/publisher/history, observer/receipts and rollback are
preserved. Temporary fixture directory auto-removed. No gateway/API/mailbox restart,
renewal, manual publication or cleanup mutation. No FIELD or APK distribution.

**One next operation:** obtain explicit permission for narrowly metadata-only
instrumentation cache inspection with a controlled target lifecycle interruption
and restoration, without Activity/prewarm/refresh/native startup/CONNECT. Do not
run the existing Activity-starting observer wrapper. This task does not authorize
that interruption or consume the clean attempt.
