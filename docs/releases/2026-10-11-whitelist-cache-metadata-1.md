# WHITELIST-CACHE-METADATA-1

## Result

**PARTIAL. READY_FOR_CLEAN_RETRY=NO.** Single first blocker:
**EXACT_CONNECT_SELECTION_UNVERIFIED**.

The metadata-only read succeeded; actual cache is not absent, expired or on an old
seed. It matches the current server directory exactly. The deliberately restricted
reader did **not** reproduce the complete identity-bound native validator. Its
signature checks and an earlier import ACK must not be upgraded into that proof.
No second instrumentation was attempted to fill this gap.

OWNER_INSTRUMENTATION_STARTS=1; OWNER_CONNECTS=0; FULL_PHASE_REQUESTS=0;
NATIVE_STARTUPS=0; task-created TELEMOST_SESSIONS=0; ATTEMPT_CONSUMED=NO.
No agent-triggered provisioning refresh, cache write, renewal, restart or publication.
Two existing background refreshes before interruption are separately disclosed below.

Evidence and retained private regression harness:
`state-client-build/field65-export16/whitelist-cache-metadata-1/`.
`RESULT.json`, `research-manifest.json` and108 SHA256 entries include receipts,
reader source/artifacts and local tests.434 earlier sealed entries verified unchanged.
Main dirty worktree/product changes are preserved, not included as a new product patch.

## Frozen product / gateway observer

Freshly pulled installed APK, not a historical signer assumption:

- Package `com.familyconnect.app.friends`, `0.1.18-research83-bootstrap`, code83,
  UID10283, non-debuggable, owner Redmi Note9Pro/API31.
- APK SHA256 `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`.
- Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Exact clean research83 source `f5240994869826c6a28f59e58e38256c688cf6eb`;
  nativecb3af31f…89e2 and embedded restricted metadata retained in manifest.
  No owner APK rebuild/reinstall, data clear, permission change or enrollment action.
- Gateway source `abc604b0f8ce431174f260ff41ef9b3b6455ba0c`;
  loaded/next `0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`.
- Entry20:09:09, owner gate20:29:45, after-reader20:30:27 and final20:37:09UTC:
  PID788144, InvocationID `dd70fcd8467847bea72b7aba20d3384a`, NRestarts0,
  start19:19:05UTC. Effective argv/config unchanged: duration4h, seed rotation3h,
  chat-services, existing loopback listener. Short bounded stability samples only.
- OBSERVER_STATE=ARMED_NOT_TRIGGERED; zero application receipts; one unchanged
  manager receipt for the earlier controlled baseline exit0. Directories0700,
  receipt files0600, retention32/layer; observer helper/source hash matches.
  No natural fatal captured; historical PROCESS_EXIT_CAUSE remainsUNKNOWN.

## DISPOSABLE_READER_CHECK

Reused the accepted incident-reader Application-substitution pattern, not its
Activity-starting wrapper. Separate package
`com.familyconnect.app.friends.cachemetadata`, targetPackage main owner.
No permissions at all, no Activity/Service/Receiver/Provider, no sharedUserId,
no DUMP/root/public provider, no target debuggable change. Signed through the
existing vault-backed protected dialog, pinned to the freshly installed signer.
Helper APK SHA256 `9fa6dcf9aa28f246b023017076c99c951687bc9d504e022cac3b9d8a5e0f8755`.

New disposable API31 non-debuggable fixture and reader shared a disposable test
signature. Six cases PASS: valid, expired, malformed, absent, legacy .bak,
pending .new. Sidecars were preserved and caused refusal, not recovery.
Same reader DEX used on owner. Application/Activity/service/network traps stayed
untouched; UID traffic0/0; process terminated; fixture packages removed.
No raw cache in instrumentation result or bounded reader-PID logcat.

Disposable JCA lacks Ed25519 and reports that check unavailable, not PASS. Exact
research83 Go validator independently accepted the synthetic valid fixture
(`compatible`). Redmi provides Ed25519 and verified the actual signed metadata.
This difference is recorded; no replacement PKI or production identity was made.
15 additional offline gate/block-transform/restore tests PASS. No full security
suite claim or change to the six historical negative-auth diagnostic assertions.

## Cache storage and read contract

Source-defined path: target Context `getNoBackupFilesDir()` plus
`restricted-readiness.enc`. `RestrictedVault` normally uses AtomicFile; its
`openRead()` may recover .bak/remove .new, so it was never called.
Reader opens the committed file O_RDONLY/O_NOFOLLOW with bounded regular-file/UID
checks, decrypts into memory with the existing non-exportable AES key, and uses the
exact strict JSON parser copied from research83. No key creation/export or identity
vault read. No `cache.Store/Refresh`, `FriendsRestricted.ready`, native load/startup,
Activity/service or provisioning API invocation.

Envelopev1: version byte,12-byte IV, AES-GCM ciphertext/tag; existing alias also
supplies AAD. Wrapper: response, denied, next_attempt, optional receipt_context.
Receipt context stores opaque challenge/fetch references, **not import/ACK time**;
those references are not exported. Committed cache is written only by the normal
validated import/backoff/denial/receipt flow. No separate recovery sidecar was present.

## OWNER_LIFECYCLE_INTERRUPTION / CACHE_ACCESS

Immediately before: correct installed package/hash/UID, VPN OFF, no active owner
audio recording/camera/play operation, existing Activity resumed but idle, keyboard
hidden; app PID19925 and ChatDeliveryService present. No Activity was launched.
One exact-package force-stop, helper install, one instrumentation start20:30:10UTC,
metadata read20:30:13UTC, helper removal. Application construction/onCreate suppressed;
network-death StrictMode on both reader threads. UID TX/RX delta0/0.

**CACHE_BYTES_UNCHANGED=PASS**: committed size3301, SHA256
`57575c268d81feca3dd7b214502504603019aae1b3b572e240f04f91bba3898d` before/after;
same inode/size/mtime/ctime, .bak/.new absent before/after. This does not claim the
whole Android data directory or access time was unchanged. Filesystem mtime20:25:20
is not asserted as an internal import timestamp.

Bounded lifecycle events corroborate reader PID11444 and no newly created Activity
or service. No arbitrary raw system/user logs retained. Helper removed; runner
exited; main APK/UID unchanged. Final20:37:08UTC: **VPN OFF; app process absent;
ChatDeliveryService OFF**. Android package stopped flag was false after instrumentation,
distinct from process absence. No safe non-networking restoration contract was proved:
ChatDeliveryService starts ChatRuntime; Activity can prewarm. Neither was restarted.

## CLIENT_CACHED_DIRECTORY / SERVER_ACCEPTED_DIRECTORY_SET

| State | Exact fingerprint / generation | Validity / acceptance |
|---|---|---|
| Client committed directory | bb5c8eb04bb8fe95fd4e2d7be214ff906b1acf264b96ba2d939329e3189d8959 | Current directory, one seed |
| Server current RU/NL | Same bb5c8eb0…d8959 | Current invocation seed1 |
| Server accepted set | This directory/seed1 only at snapshot | Source/runtime proof before configured rotation, not an owner authentication probe |
| Previous invocation seeds | Not retained | Not accepted by current process |

Compact JSON bytes match server raw directory hash; independently sorted semantic
hash also matches RU/NL: `ba4f157954bc8c76e1006c0a7d84c82b94cd01b7f2dce3388bb1f59da7d3d3a1`.
Directoryv1 has no independent signature/generation/revision/floor fields. Do not
confuse runtime seed generation1 with a signed directory generation.
Issued19:19:09.966146309UTC, nominal expiry23:19:05.956440503UTC.
In-process rotation would retain old seed only until its existing deadline;
there is no restart-persistent overlap. At these observations rotation had not occurred.

Delivery: issued20:25:15UTC, expires21:37:28UTC; revision3, minimum CRL22295,
issuer sequence10, revision floor1, denied=false. Family/gateway safe hashes match
current signed delegation/profile; issuer signature against installed control anchor,
authority/leaf/CRL signatures valid; cached leaf not revoked. AES-GCM valid.

**CACHE_SERVER_COMPATIBILITY=CACHE_CURRENT_AND_ACCEPTED**, specifically exact
directory/seed routing compatibility. Full current cache usability/client mTLS is
not established by this classification; owner authentication was NOT_ATTEMPTED.
No raw profile/certificate, identity, room URL, token or payload was exported.

## Background refresh and EXACT_CONNECT_SELECTION

Important new observation: RU receipts show existing app background fetches20:20:20
and20:25:15UTC with import ACKs20:20:21 and20:25:20. Last ACK is research83 READY,
orchestrator_usable=true, revision3/CRL22295/expiry21:37:28 matching reader metadata.
These occurred before the controlled stop, not in the reader. Source has the
resumed-Activity refresh timer and five-minute backoff; no new Activity/prewarm was
started by this task. Exact caller of these background requests is not independently
tagged. They are **provisioning**, not merely assumed chat sync.

Therefore initiated refreshes=0 but observed background refreshes=2, not a blanket
claim of zero network activity throughout the whole task. The old18:08 receipt
cannot stand in for this actual cache. No preparation-only refresh was performed.

Research83 source: `FriendsRestricted.ready` joins/starts required refresh;
`RestrictedBootstrap.refresh` returns fresh accepted response B directly on success,
or calls `cache.usable(now)` only for an availability failure, never AUTH denial.
`RestrictedTunnelEngine` passes that returned response to native. The sole stored
fallback candidate is proven B=bb5c8eb0…d8959; no substitute A was injected.

However `cache.usable` invokes full `NativeRestricted.validationCode` bound to
`ControlIdentity.publicIdentity()`. `wholedevice.ValidateDelivery` additionally
checks device reference, certificate public key/URI/EKU/claims, time and CRL
constraints. This reader intentionally did not read identity material or invoke
native, and its metadata decoder is not that validator. The earlier ACK has no
cache digest; it corroborates import but is not a complete current validation replay.
Thus **EXACT_CONNECT_SELECTION=CONNECT_SELECTION_UNKNOWN**, with candidate B known;
not CONNECT_WOULD_REQUIRE_REFRESH, and not proof of cache invalidity. Claiming
unconditional CONNECT_WOULD_USE_B would exceed the evidence.

## CHAIN_AND_HEADROOM / offline remaining gates

Strict hostname/SNI/served DER verification PASS20:36:59UTC; leaf06c2c41e…d1a17,
authorityd5a0d0db…9dc18; AKI/SKI and configured profile match. Authority, grants and
CRL metadata remain valid. Client mTLS/application admission NOT_ATTEMPTED.
RU/NL paired20:33:39–43UTC: same directory and CRL22310/DER hash; ordinary CRL
sync continued (NL floor22316 at closeout), not an agent renewal/publication.
Security ceiling21:37:28UTC bounds both captured client delivery and server chain.
At final20:37:09 headroom3618s exceeds the existing clean-gate1200s requirement;
directory expiry cannot extend it. No arbitrary new timing policy.

PROVISIONING_BLOCK_CONDITION=NOT_READY. Existing source-IP plus exact provisioning
role503 transform/restoration passes fixture tests, leaves Telemost/DNS/media outside
the rule, restores after900s, and rejects conflicting config edits. Fresh exclusive
source scope is unproved; no owner block was activated or live reachability inferred.

COLLECTORS_READY=NO. Fatal observer is ready; existing egress harness is retained.
Older gateway collector still pins5e877eb1…fe81f rather than observer0ccaaf81…2667a;
its offsets/current binding are not validated. Old client observer wrapper starts
Activity and was not used. Pure physical-gate fixtures pass, but no gate was shown.
No conflicting active owner process/session can persist at the final stopped state;
no native/Telemost start was created here. Prior background routing is not rewritten.

## Closeout / one next operation

No restart/renewal/transport patch, artificial fatal, owner startup, live egress or
FIELD. Observer/receipts/rollback remain. Only this helper, disposable emulator data,
temporary Go cache and disposable signing key were removed. Harness, fixture APKs,
owner/helper provenance and evidence retained; previous helpers and owner
cache/enrollment/AWG/publisher/history preserved. No APK publication/distribution.

READY_FOR_CLEAN_RETRY=NO; FIRST_BLOCKER=EXACT_CONNECT_SELECTION_UNVERIFIED;
ATTEMPT_CONSUMED=NO. WHITELIST_COLD_START_READY=NO; FIELD=NOT_RUN.

**One next operation:** separately scoped metadata-only identity-bound cache
validation/exact-selection proof, without CONNECT or refresh. This task's single
owner instrumentation authorization is exhausted; do not run another reader under it.
