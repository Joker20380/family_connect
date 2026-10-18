# WHITELIST-EXACT-SELECTION-1 — PARTIAL (11–12.10.2026)

Exact offline identity-bound selection **passed at 11.10 21:27:13 UTC**. The
previous EXACT_CONNECT_SELECTION_UNVERIFIED blocker is closed for that captured
state. This is not present-time readiness: the gateway subsequently completed its
four-hour lifetime, then its automatic restarts failed at PROFILE. Observer
receipts are preserved. **READY_FOR_CLEAN_RETRY=NO**;
**FIRST_BLOCKER=GATEWAY_INVOCATION_CHANGED**; **ATTEMPT_CONSUMED=NO**.

No CONNECT, owner refresh, Activity launch, TUN or carrier startup was initiated
by this task. A separate later Activity resumption and two background provisioning
imports were observed; they are not suppressed from the accounting below. No
product patch, owner APK replacement, gateway restart/renewal/publication or FIELD.

Protected evidence: `state-client-build/field65-export16/whitelist-exact-selection-1/`
contains `RESULT.json`, `research-manifest.json`, reader sources/APKs, fixture
receipts, production-contract receipt and 176-entry `SHA256SUMS`. The 542 entries
sealed by the seven preceding stages remain unchanged. No raw owner cache/vault,
private key, complete public identity, profile or room URL was exported.

## Acceptance matrix

| Item | Result |
|---|---|
| DISPOSABLE_VALIDATION | PASS, 12 final API31 cases |
| OWNER_INSTRUMENTATION_STARTS | 1; no second run |
| TARGET_INITIALIZER_SIDE_EFFECTS | None observed during reader; later separate Activity resumption recorded |
| CACHE_BYTES_UNCHANGED | PASS over reader interval, including sidecars; not a claim after background imports |
| IDENTITY_BOUND_VALIDATION | PASS at 21:27:13 UTC, exact installed production path |
| EXACT_CONNECT_SELECTION | CONNECT_WOULD_USE_CLIENT_CACHE_bb5c8eb0…d8959 at capture, on availability-failure fallback |
| SELECTED_BYTES_HASH | b457e749…a0922; exact equality to original canonical response bytes |
| NATIVE_OFFLINE_VALIDATION | PASS, installed JNI validationCode=0; beginReady not called |
| SERVER_ACCEPTED_DIRECTORY_SET | At capture: bb5c8eb0…d8959/current seed1; final: empty, no running gateway |
| CACHE_SERVER_COMPATIBILITY | Historical CACHE_CURRENT_AND_ACCEPTED; no current acceptance claim |
| PROVISIONING_BLOCK_CONDITION | NOT_READY; role fixture passes, exclusive source scope unproved |
| COLLECTORS_READY | NO; current binary ABI bound locally, complete executable bundle not reaccepted |
| GATEWAY_STABILITY | Same invocation through 21:36 snapshot; later normal exit and five fatal startups |
| OWNER_FINAL_LIFECYCLE | Last observed 12.10 09:12:30 UTC: VPN OFF, app ON, ChatDeliveryService ON |
| READY_FOR_CLEAN_RETRY | NO |
| ATTEMPT_CONSUMED | NO; clean CONNECT not used |

## Exact subject / unchanged product bytes

- Installed `com.familyconnect.app.friends`, `0.1.18-research83-bootstrap`, code83,
  UID10283, non-debuggable. Freshly pulled APK SHA256
  `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`.
- Actual installed signer SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Source `f5240994869826c6a28f59e58e38256c688cf6eb`, saved checkout clean;
  ARM64 native `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
- Only separate helper `com.familyconnect.app.friends.exactselection` installed
  and removed. Signed helper SHA256
  `f71e7cd0b6d8a1e7c08401e6807859d3b552e22f10ada024bc3be6f07acb9b84`.
  No permissions, exported components, shared UID or main-APK debuggable change.
  Existing vault-backed signer used through protected local dialog.
- Gateway observer source `abc604b0f8ce431174f260ff41ef9b3b6455ba0c`, binary
  `0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`.
  Loaded/next agreed during validation. Final **loaded=NONE/MainPID0**; next binary
  still exactly the observer. No transport, lease, trust-policy or timing change.

## Production boundary and privacy

The helper reflects into the **installed target classes**, not a simplified
validator. `FriendsIdentityVault.load()` uses target Context and existing identity
in memory. Existing vault/key and absent `.bak`/`.new` are required before load;
there is no creation/enrollment fallback. Identity handle is closed in `finally`.

Original `getNoBackupFilesDir()/restricted-readiness.enc` is opened with
O_RDONLY/O_NOFOLLOW. The committed encrypted envelope is decrypted in memory;
original AtomicFile recovery is not called. `FriendsRestricted.cache(context,
identity)` supplies its actual detailed validator. A read-only Storage adapter
returns those original clear bytes to production `RestrictedCache.detailed`; its
write callback rejects writes (observed attempts0).

The exact existing offline boundary is:

`RestrictedBootstrap.cached → RestrictedCache.usable(now) → production detailed
validator → NativeRestricted.validationCode → fcRestrictedValidationCode →
wholedevice.DeliveryValidationCode/ValidateDelivery`.

The installed library has a pure validation API. It was loaded and called; that
is not native session startup. JNI_OnLoad only stores the VM. No beginReady,
DeliveryMaterial, socket, service or TUN attachment was invoked. The ordinary
`RestrictedTunnelEngine` passes the selected response returned by `FriendsRestricted.ready`
into beginReady; this task stops before both ready/refresh and beginReady.

This proves the **availability-failure fallback candidate**, not unconditional
offline startup: research83 still attempts/joins authenticated refresh. Successful
refresh returns its newly accepted response; AUTH rejection never uses cache.
No expected server hash was passed into the helper or substituted for selection.

Production Application/provider initialization was source-reviewed: language
attachment and existing provider onCreate paths do not start networking. The
tested instrumentation uses a plain Application and skips onCreate. It does not
hide a network-producing initializer. StrictMode network-death checks and UID
TX/RX=0/0 corroborate the source audit during the reader. Explicit temporary byte
arrays/validator captures were zeroized; production identity was closed. This is
not a claim to wipe every immutable JVM/crypto-library allocation.

## Full validation and exact bytes

All nine requested checks PASS as a conjunction of actual production validation:
schema, signature, family, gateway, identity, revision, floors, time and cached
revocation state. Native code0 additionally returned on the exact original response.
`ValidateDelivery` verifies root-signed issuer delegation, authority/client leaf,
leaf key/URI/device/family/role/protocol/revision, signed CRL/time/non-revocation,
issuer floor, directory binding and effective limiting expiry.

Directory v1 has no independent signature or numeric generation. Signature PASS
refers to the existing delivery/delegation trust contract, not an invented directory
signature. Floor PASS refers to committed delivery/issuer checks; no new import or
anti-rollback decision was simulated. This is offline validation, not current server
client-mTLS or application admission.

| Bytes at 21:27:13 UTC | Value |
|---|---|
| Original encrypted cache | 3301 bytes |
| Raw SHA256 before and after | `57575c268d81feca3dd7b214502504603019aae1b3b572e240f04f91bba3898d` |
| Original canonical response / selected bytes SHA256 | `b457e7491eaaf18ac0b396b5ded03f7ac9144152c65d72f949535fa9af9a0922` |
| Selected directory SHA256 | `bb5c8eb04bb8fe95fd4e2d7be214ff906b1acf264b96ba2d939329e3189d8959` |
| Delivery revision / minimum CRL | 3 / 22295 |
| Effective expiry | 11.10 21:37:28 UTC |

Selected bytes equal original response bytes by Arrays.equals, not merely digest.
The intended transformation is decrypt envelope → production parse wrapper →
canonical `response` UTF-8. Raw ciphertext therefore correctly differs from native
input. Cache and identity-vault file size/hash/inode/mtime/ctime and absent sidecars
were unchanged across the run. No whole-data-directory immutability claim is made.

## Disposable validation

API31 non-debuggable fixture uses byte-identical installed research83 DEX and exact
f5240994 production JNI compiled only for disposable x86_64. Owner and fixture
reader DEX are identical. Positive, foreign identity, wrong family, wrong gateway,
invalid signature, stale revision, stale signed issuer floor, expired, malformed,
absent, sticky denial and valid-after-failures cases PASS. Production rejection
does not mutate cache/vault or attempt refresh/new identity/native startup.

An initial disposable-only reporting bug rejected revision0 after production had
already rejected it correctly. Only helper metadata reporting was corrected; old
artifacts/results retained, then all12 passed before touching owner. No security
assertion was relaxed. Fifteen existing local guard/block/physical-gate fixtures
also pass. No complete product-suite-green claim or change to the six known
negative-auth diagnostic assertions.

## Lifecycle and network accounting

21:27:13 reader PASS → helper removed → 21:27:16 exact target stopped, no process,
service, VPN, resumed Activity or active media. No ordinary launcher was used.

At **21:28:30**, a distinct FriendsActivity creation/resumption and ordinary process
PID18951 appeared. Source/caller of that launch is **NOT_ESTABLISHED**; it is not in
task commands, and is not attributed to the user without evidence. RU records show
restart ACK21:28:31, authenticated fetch/import/ACK21:28:37–38 and21:34:31–32.
Resumed Activity's production prewarm path explains why ordinary foreground
operation can refresh; it was not invoked by the reader.

Thus task-initiated CONNECT/Telemost/native startup/TUN/provisioning refresh/Activity
counts are each0, and reader traffic0/0, but **whole-task provisioning count is not
zero: at least two later background fetches are confirmed**. Post-reader service-only
Telemost/native activity is not exported; no whole-task zero is asserted for it.
Final observed VPN remains OFF and no clean CONNECT was initiated. Cache unchanged
applies only to the reader interval; later ACKs have no digest and do not authorize
claiming the same current serialized bytes. No second reader was run.

The ordinary app/chat process was not force-stopped: the requested restoration
authorization permits it only while no ordinary user process exists. Final
12.10 09:12:30 UTC app/chat ON, VPN OFF is recorded honestly, not cosmetically reset.

## Gateway, chain and natural exit evidence

Entry and post-reader snapshots: invocation `dd70fcd8467847bea72b7aba20d3384a`,
PID788144, start11.10 19:19:05 UTC, NRestarts0, observer armed/no terminal receipt.
Current seed1 and RU/NL directory equal selectedbb5c…d8959. Same-invocation bounded
overlap is not restart overlap. No client authentication or owner carrier was opened.

Strict SNI/served DER/profile/AKI-SKI verification PASS at21:36:19 UTC, leaf
06c2c41e…d1a17, authorityd5a0d0db…9dc18; RU/NL CRL22424/DER hash equal. However
limiting expiry21:37:28 left only68s, below the retained1200s clean-gate bound
(existing900s condition/90s operator gate plus safety, not a new TTL). Renewal was
prohibited and not performed. These credentials are now expired; the nominal
directory23:19 expiry could not extend them.

There is a gap between bounded evening checks and the next observed state on
12.10 09:12 UTC; no continuous observation is claimed. The observer preserved:

| Invocation/event | Exact evidence |
|---|---|
| dd70…3384a, 11.10 23:19:05.963 UTC | `normal_stop`, RUN/DEADLINE, parent DEADLINE, fatal=false, elapsed14400042ms |
| Same invocation, systemd | exit0/success, actual exit23:19:05 UTC; matches configured `--duration 4h` |
| ef6dc81878f34a1ba76f6ed4a171f6ab, 23:19:36.243 UTC | first new fatal: returned_error, PROFILE/CREDENTIALS_REJECTED, elapsed30ms, cleanup completed |
| Same fatal, systemd | exit1/exit-code, PID910762, NRestarts1 |
| Four subsequent automatic startups | same PROFILE/CREDENTIALS_REJECTED before seed publication; last23:21:37.238 UTC |
| Final state | failed/failed, MainPID0, last invocationc1ad4d4486e94a2cb3a0f6f87e080d7d, NRestarts6 |

**PROCESS_EXIT_CAUSE=PROVEN at the typed PROFILE/CREDENTIALS_REJECTED boundary for
these new failures.** Captured startup expiry21:37:28 precedes first fatal by6128s;
production ServerTLS→familysession.Configuration rejects expired authority/CRL.
Expired credential state is independently established. The receipt does not encode
which individual cryptographic subcheck ran first; do not invent a finer exception.
The preceding four-hour exit was normal, not a fatal Reliable/provider failure.
Historical pre-observer exits remain UNKNOWN, not retrospectively explained.

All13 available exact application/systemd JSON receipts copied with original SHA
verified, mode0600 in protected evidence; server retention0700/32 per layer remains.
No artificial exit, manual restart, broad journal query or recovery was performed.
Current accepted directory set is **empty**: no runtime serves even the unchanged
on-diskbb5c…d8959 file. Observer is installed and has triggered, not a currently
running armed process. Cache preparation stopped at this discovery.

## Remaining gates / cleanup / one next operation

Local provisioning transform restricts only exact provisioning roles, excludes
Telemost/media/DNS, restores after900s and rejects conflicting edits. Source-IP
exclusivity is unproved; no rule was activated. Current observer binary's Go/DWARF
layout and Mux symbols were extracted and pinned locally; the old live wrapper
still pins baseline and the client incident bundle is not reaccepted. Therefore
block condition NOT_READY and collectors NO, not a silent PASS.

Helper and task-owned disposable emulator/data/test signing key/temporary Go cache
removed; harness/APKs/provenance/fatal receipts retained. Research83, owner cache,
identity/enrollment, AWG, publisher/history, existing rollback and observer preserved.
No public APK/distribution, transport fix, preparation refresh, CONNECT or FIELD.

**One next operation:** separately scoped operational gateway credential-recovery
preflight for the proved PROFILE/CREDENTIALS_REJECTED failure, using the accepted
same-key runbook. Do not start CONNECT or infer readiness from that future repair.

READY_FOR_CLEAN_RETRY=NO; FIRST_BLOCKER=GATEWAY_INVOCATION_CHANGED;
ATTEMPT_CONSUMED=NO. Cold-start/whitelist FIELD and dedicated join are not proven by
this offline task; prior full-tunnel egress and lease evidence are unchanged.
