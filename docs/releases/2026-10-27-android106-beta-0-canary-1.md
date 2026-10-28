# ANDROID-CONTROLLED-BETA / BETA-0-CANARY-1

## NL parser provenance and read-only material review — 28 October local

**OWNER_CANARY_BOUND_READONLY / BLOCKED_CRL_PROFILE_COMPATIBILITY /
LIVE_WRITES_NOT_RUN.** Input main `f499bdf80eec2022c3b58cd1db4ebfb93cafd7ed`.
Same checkpoint, documentation/evidence only; no product source or parser-limit change.
The single parser classification is **NL_VALIDATOR_ONLY_DRIFT**. The previous
MATERIALS_INVALID result below came from an auxiliary archive, not the actual forced
command, and is superseded by this exact-path review. Historical evidence is retained.
[Sanitized machine-readable receipt](2026-10-28-android106-beta-0-canary-nl-readonly.json).

### Execution-path and source provenance

Effective SSH configuration, authorized forced command and its exact exec argv were
resolved read-only. No alternate SSH ForceCommand/AuthorizedKeysCommand overrides it.
The forced command is a short-lived per-connection Python3.14.4 process; the separate
bootstrap service remains active, PID2491265/NRestarts0, unchanged start identity.
Configuration, argv, private paths and raw generic archives remain private. No forced
command was invoked against production; only its exact parser source was imported
into isolated read-only probes. The earlier helper and real gateway use different
archives: **NL_VALIDATOR_EXECUTION_PATH_DRIFT**.

| Role | Size / members | Archive SHA256 | Directory maximum |
| --- | --- | --- | --- |
| Actual forced-command gateway | 26854 / 18 | `0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450` | 14400s |
| Previous auxiliary directory validator | 26406 / 18 | `f6aa8859ab716383bf207b2ff7b302687692832b2ccb410f1aef0ada0793a9c9` | 3600s |

The receipt contains exact member/module hashes. Actual gateway's `restricted.py`
and `restricted_sync.py` did not match exact Git blobs in the searched all-ref file
history: provenance is **exact installed generic source**, not an invented source
commit. The old parser/sync modules and shared catalog matched verified Git blobs.
Actual `directory`, `timestamp`, `timestamp_ns` function source hashes **all match**
current accepted main. `MAX_TEST_LIFETIME=14400` is a local constant, not imported or
replaced; predicate is `0 < expires-issued <= MAX_TEST_LIFETIME * 1000000000`.
The auxiliary parser has a literal3600s bound. Its absent exported constant must not
be confused with actual gateway behavior. No `strings`-only inference was used.

### Exact timestamps and synthetic boundaries

Same directory SHA256 `0aa55347adaa2fbd977b6c98b812ac2443a95c6f132f030785c33c5617c3a22a`,
same family/gateway bindings and explicit `now_ns=1793145321597295579` for all three
isolated parser calls. Current accepted function source was extracted without changes;
the two installed implementations were imported from exact verified archives.

| Field | Exact value |
| --- | --- |
| issued_at | `2026-10-27T23:23:11.48947495Z` |
| expires_at | `2026-10-28T03:06:33.229230378Z` |
| issued_at nanoseconds | 1793143391489474950 |
| expires_at nanoseconds | 1793156793229230378 |
| Delta nanoseconds | 13401739755428 |
| Delta seconds | 13401.739755428 |

All parsers preserve these exact nanoseconds. Current/actual parser PASS; auxiliary
parser rejects `time / invalid_lifetime / expires_at`. Fractions1–9 digits and zones
Z/signed HH:MM are supported. The old implementation passes a fractional timestamp
through datetime, then reconstructs nanoseconds from the original fraction; the current
one parses whole seconds and adds the exact fraction. Neither truncates this directory.
The earlier13402s observation subtracted individually floored display endpoints;
it was not the exact lifetime. **TIMESTAMP_PRECISION_MISMATCH is not established.**

Disposable, network-free synthetic matrix:899/900/3599/3600/3601/10799/10800/10801/
13399/13402/14399/14400/14401 seconds, identical types and synthetic bindings only.
All three parsers ran with fixed `now_ns=1800000000123456789`; additional maximum−1ns,
maximum and maximum+1ns checks confirm exact limits. **48 checks PASS**. Current and
actual gateway accept through14400s; auxiliary through3600s. No production seed/join
URL was used in synthetic fixtures or emitted in evidence.

### CRL floor and the separate blocking contract

Profile embedded CRL27211 equals the observed installed CRL and RU current CRL;
RU stored sequence27211. SHA256 of both exact CRL payloads:
`b98c1012d045d4923e8d4242d597c0fd771c2357b10bfa898608c1868eb586c3`.
No separate NL CRL file was found at the inspected material location: the installed
source here is the profile-embedded payload, not an independent newer file. Authority,
issuer and signature checks PASS. Profile hash and minimum_crl27088 remain unchanged.
Neither CRL_PROFILE_BEHIND_INSTALLED nor CRL_MINIMUM_AHEAD is supported by these data.

Actual gateway code enforces `number >= max(previous_embedded_number, minimum_crl)`.
However, its only accepted request is `READ_ONLY_SECURITY_SNAPSHOT`; all CRL-write
requests fail **MAINTENANCE_TRANSACTION_REQUIRED**, before mutation. It validates
the embedded payload/directory and returns a snapshot, never updates minimum_crl.
Thus the owner's required "next exact accepted payload updates the floor" condition
cannot be satisfied by this command. **CRL_FLOOR_UNRESOLVED** refers specifically to
that forward-write/maintenance contract, not to unknown bytes or proven invalid
cryptography. **CRL_FLOOR_LAG_NONBLOCKING is not claimed.**

18 disposable gateway/floor checks PASS across current source, old auxiliary archive
and actual deployed archive: below/equal floors, ahead-floor rejection, replay and
changed/next payload cases. Actual snapshot replay is byte-preserving/idempotent;
next CRL and same-number/different-bytes write requests both fail the maintenance
guard without touching the fixture. The old/current generic mutating gateways do
update the floor and reject same-number/different bytes, but those results are **not**
transferred to the actual production forced command. No attempt to bypass its guard.

### No-write evidence and validation

- Existing owner binding `dev_fa4f7e03ca04`, HMAC resolution and private lookup/status
 artifacts unchanged. Prior exact Android106 confirmation retained; **zero lookup or
 status-operation repeats**. No selector used. Ledger subscriptions0/events0, cohort0/10;
 owner certificate rows0, valid0, horizon CLEAR. No new owner challenge/fetch since baseline.
- SQLite mode=ro/query_only/read transactions only. Identity/invite/support/grant,
 paid tables, revocation-bearing records, admission/publisher and stored CRL sequence
 unchanged. One unrelated certificate was added during ordinary production traffic;
 the prior certificate rows still match their authoritative fingerprint. Global
 certificate/readiness/challenge/chat tables are **not** claimed equal. Owner scope
 remains unchanged; observers did not call challenge/fetch/issue endpoints.
- RU/NL directory/CRL bytes, NL profile/minimum, forced-command configuration and
 service identities unchanged. Friends exact paid-aware archive unchanged, active,
 PID1002753/NRestarts0, effective/running argv match. No restart/reload, file replacement,
 gateway write, CRL action, paid event, material refresh or Android action.
- Final material readback: authority/issuer6993155s remaining, CRL10928s, directory
 10940s; strict actual parser, bindings/signatures PASS. Both hosts NTP synchronized.
 These are timestamped observations, not a perpetual live-entry authorization.
- Read-only monitor active, latest cycle28 October00:03:09 UTC; RU registry observed,
 NL registry UNAVAILABLE, not0. Console remains loopback-only/synthetic/read-only root,
 no production configuration mounts or credential environment entries. Monitoring
 itself does not collect PID/build or client telemetry; service identity was inspected
 separately. Administrative SSH was used for read-only commands, not relabeled as a
 technically restricted read-only credential.
- **96 affected pytest tests PASS,32 explicit deselections** (unrelated packaging and
 optional native/Android parity). Directory/timestamp, restricted-sync, CRL signature/
 issuer/time/number and same-number idempotency/conflict checks included. **48 parser
 +18 gateway/floor synthetic checks PASS**. No full repository/platform suite or build.
 No imported product code changed, so no CRL helper rewrite or correction packaging.
- Strict JSON, private-data/selector-pattern scan, new Markdown links, staged scope
 and `git diff --check` PASS. Only five documentation/evidence files are staged;
 pre-existing unrelated working changes remain unstaged and byte-preserved.

### Decision and next bounded action

The parser cause is resolved as **NL_VALIDATOR_ONLY_DRIFT**, with a stale auxiliary
validator left as technical debt. Actual validation remains strict14400s; no parser
correction candidate is authorized by the proven findings, and none was built/deployed.
Live entry remains **BLOCKED_CRL_PROFILE_COMPATIBILITY** because the required CRL
delivery/floor-update boundary is not established on the actual read-only command.

NEXT — separately authorize one bounded maintenance/delivery and floor-contract
reconciliation: review the exact authorized maintenance route, preserve the snapshot
endpoint's read-only guard, and establish atomic exact-payload acceptance/floor update
with a defined rollback boundary. The numeric reconciliation target is the exact
embedded/current CRL27211 (not a regenerated CRL); changing minimum_crl alone does not
prove future delivery. Do not substitute the old mutating archive, enable generic
writes, remove a safety guard or silently install credentials. This review performs
none of those corrections. **STOP; no phone opening/Connect or request for ГОТОВ.**

## Read-only owner binding and live-entry preflight — 28 October local

**OWNER_CANARY_BOUND_READONLY / BLOCKED_READONLY_PREFLIGHT / MATERIALS_INVALID /
LIVE_WRITES_NOT_RUN.** Input main `6dff337795b0545dbe9a63e5a5619ac9a13e1da8`.
Same checkpoint; no new product task or canary ID. This continuation changes only
documentation and a [sanitized receipt](2026-10-27-android106-beta-0-canary-1-readonly.json).
Server observations below use UTC, starting27 October23:31:11. No paid/live acceptance.

### Artifacts and binding

- Accepted lookup-only artifact: source `ad086c030cc77c680d924fb9c8e37faa286adc4c`,
 15 members,56017 bytes, SHA256 `63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308`.
 Regular/non-symlink, strict ZIP/JSON, exact committed member hashes, null envelope,
 absence of operational configuration/permit, import/help and private-data scans PASS.
 It was not rebuilt. Accepted unbound CRL package unchanged:24 members,138174 bytes,
 SHA256 `3c3736917efb1720b7086e57e4e8b2182fcb56734ec85b662b9bed71c15840a6`, manifest
 `704b67df66d21e198e175344932f81e4d23e2e697f15475f45656be9af476ebb`; unbound/null permit/
 absent production configuration verified read-only. No CRL helper production execution.
- Fresh private operation directory0700 outside Git/Django/web; separate random32-byte
 HMAC key0600. Selector supplied transiently without echo via stdin, never argv.
 Temporary0600 input unlinked immediately after the single lookup; exact selector
 absent from remaining operation files and process arguments. No forensic SSD erase
 claim. No selector input to PostgreSQL, Django, audit, URL, environment or shell history.
- One production lookup PASS at23:31:27; OWNER_CANARY_1=`dev_fa4f7e03ca04`.
 Unique bound identity, existing activation and non-revoked device/invite; MESH
 admission checked read-only with the existing grant logic. Exact106 accepted under
 confirm_android106: latest authenticated readiness ACK at27 October06:59:00,
 platform android, versionCode106, app_version `0.1.18-beta106-recovery`.
 No observation was updated. Full token/key/envelope remain private.
- Bound status-only package from the same exactad086c0 source:15 members,56187 bytes,
 SHA256 `ab27f3bf3d55475d752af9b3b3ed193e19832aa8df2ffb6dc7f38adb776090c0`, manifest
 `1923f3405e45112630648ebf14697fc0d3c6cc85aa0122ee6bb3f681dd842028`.
 Two independent byte-identical builds; binding=single_canary, permit=null, private
 read-only artifacts. Exact source/member checks PASS; no selector/key/config/path.
- Four disposable synthetic checks PASS: exact packaged status with a test-only
 synthetic token mapping (no production identity copied into a fixture), exact
 packaged apply→PERMIT_REQUIRED and lookup→BOUND_LOOKUP_FORBIDDEN, and unchanged
 original HMAC resolution/status on a separate synthetic binding. Package bytes
 were not modified by those tests. No production apply or second production lookup.
- One production bound status PASS at23:32:31 using the real private HMAC key:
 same binding, activation_active=true, cohort=false, version0, event_count0,
 effective_state/paid_allow/paid_until=null. Ledger remains subscriptions0/events0,
 cohort0/10. No owner slot has been enrolled.

### Freshness and the blocking result

Friends active/running, exact paid-aware archive
`dcd769986a1da7cb1662c0f73d18a88e9f73485a977db937ca5b1428c1fd1029`, effective/running
argv match, MainPID1002753, NRestarts0. This is a fresh observation, not reuse of
the historical CP2 PID. Publisher capability and historical core/policy fingerprints
match. SQLite mode=ro/query_only/read transaction: integrity, foreign keys, exact
paid schema and empty ledger PASS. NTP/NTPSynchronized=yes, resources sufficient,
no pending service/package transaction observed; read-only HTTP liveness PASS.

Certificate horizon: valid_certificate_count=0, latest_valid_expiry=null,
latest_remaining_seconds=0 — **CERTIFICATE_HORIZON_CLEAR**. No certificate issuance,
deletion or expiry modification; no readiness challenge/fetch.

RU issuer/authority signatures, CRL issuer/signature/number, strict directory
time/family/gateway validation PASS. At23:34:16, authority/delegation remaining
6994952s, CRL12725s, directory12737s; all exceed720s. Stored CRL sequence27211 matches.
NL has byte-identical CRL and directory, matching authority/family/gateway bindings;
signatures and wall-clock validity PASS, NTP synchronized. However, its **installed
strict directory parser rejects stage=time, predicate=invalid_lifetime,
field=expires_at**. Directory issued23:23:11, expires03:06:33 next UTC day; full
lifetime13402s. RU strict parsing passes those bytes; NL strict parsing does not.
No validator was weakened or production package changed to obtain PASS.

NL profile minimum_crl=27088, installed signed CRL number27211. A lower floor is
recorded as a compatibility question, not asserted by itself to prove invalid
cryptography; it is not the future exact-payload acceptance proof requiring the
generated number. The independent NL directory rejection already blocks entry.
Thus **MATERIALS_INVALID / BLOCKED_READONLY_PREFLIGHT**, not a short remaining-TTL
MATERIALS_REFRESH_REQUIRED and not READY_FOR_OWNER_LIVE. No refresh, CRL generation,
delivery, sequence increment, gateway repair or write credential/permit installation.

### Monitoring and no-write proof

Read-only timer active/waiting, last completed cycle27 October23:36:29 successful.
Latest RU snapshot observed/fresh (19s at inspection); NL snapshot fresh (16s) with
registry UNAVAILABLE, never false0. The existing monitor reports service state,
not paid build/PID; those were verified separately in this preflight. Client
telemetry remains NOT_COLLECTED. Console loopback-only, synthetic backend guard
present, no production write adapter or SSH/canary credential mount/home credential.
The existing external administrative SSH channel is not claimed to be least-privilege.
No monitoring configuration or PostgreSQL record was changed by this checkpoint.

Before/after read-only observations preserve paid rows/events, devices, invites,
grants, revocation state, admission, publishers, certificates, restricted challenges
and readiness results; service PID/start/NRestarts unchanged. RU CRL number/hash,
directory hash and NL profile/hash/minimum_crl/directory unchanged across inspection.
Concurrent chat_challenges/chat_sequence changes were observed (target chat_challenges
also changed); **no whole-registry or all-target-tables byte equality is claimed**.
They are outside the read-only commands performed here; the restricted challenge,
readiness and certificate fingerprints are unchanged. No Android action or Friends
restart, deployment, payment, enrollment, production subscription/event or CRL write.

Private observer-only dry-run corrections preceded successful readbacks (namespace
collision, a non-exported legacy validator constant, and a local credential-path
permission probe). No extra owner lookup/status and no production repair resulted.
Strict JSON, scoped selector/secret scans, Markdown links, staged scope and whitespace
checks PASS at closeout; full historical suites/platform builds were not run.

**STOP. NEXT — review NL directory lifetime validation and gateway floor compatibility;
any correction requires separate authorization, then fresh read-only recheck.**
Do not ask the owner to open the app or reply ГОТОВ yet. Stage0 requires
READY_FOR_OWNER_LIVE plus the owner's explicit ГОТОВ and a fresh production backup;
no automatic lookup repeat, activation, CRL phase or phone procedure.

## Exact-payload CRL delivery — source-only gate

**LIVE_ENTRY_SOURCE_READY / CRL_HELPER_UNBOUND_READY / PRODUCTION_LOOKUP_NOT_RUN /
LIVE_WRITES_NOT_RUN.** Input main `11b99a6cae1c9c8722b266bd773caa821d3e3a61`;
accepted bounded-dispatch source `ad086c030cc77c680d924fb9c8e37faa286adc4c` unchanged.
Same BETA-0-CANARY-1; no new top-level task. No production access or operational action.

### Source and authority boundary

- New helper/packager and their tests only; minimal existing restricted_admin refactor
  extracts pure build_crl_payload. It reads a query-only snapshot, computes the existing
  paid-aware deny set, signs once and returns PEM, number/timestamps/serial metadata.
  It does not change any DB row or file. Existing publish_crl delegates to it and keeps
  its public/operator behavior, including valid lifetime choices and monotonic floor.
- Canary lifetime900s; generated number=max(previous CRL number, stored sequence)+1.
  Expected certificate must be newly revoked; other newly added serials require
  independently proven current deny/revision/family reasons. Allowed unrelated
  certificates are excluded. Serial output uses HMAC(decimal serial) short tokens
  privately; sanitized receipts never expose raw serials or CRL contents.
- Immutable bound-envelope contract is tested only with synthetic values: alias,
  operation_id, HMAC device/safe_ref, version3/count3/expired, exact certificate token
  and <=300s generation window. Two payment events followed by explicit expire,
  current Android106 eligibility, non-revoked device/invite, paid denial and valid
  authority/revision/family/identity-bound certificate are required. No other cohort
  member is allowed. No helper operation can change paid/identity/invite/grant state.
- No default/live configuration, host, key, credential, readback transport or bound
  package is installed. Public CLI is help/manifest only; it cannot run prepare,
  deliver, commit or accept operational input. Future configuration/transport injection
  must be fixed and operator-reviewed, never supplied via public input. Existing
  sync lock identity must be verified by that future configuration, not guessed here.
- Existing gateway returns directory only. Acceptance additionally requires trusted
  authenticated readback of exact payload SHA256, installed CRL number and minimum_crl.
  Plain directory output is not treated as that proof. Existing strict directory
  parser checks time/family/gateway/seeds; no new signature or wire schema is invented.

### Immutable operation and delivery

Preparation holds the configured existing restricted-sync lock and opens authoritative
DB read-only. Exclusive0700 operation directories and0600 regular/non-symlink/single-link
files retain PEM, exact canonical compact JSON request (only revocations), hashes,
generation metadata, prior local hashes/sequence, safe revoke tokens and private
fingerprints. Journal updates are authenticated, atomic and parent-fsynced. Key and
canonical device/selector/certificate body are never persisted in the journal.

Generation_count=1 for every prepared operation. Existing directory prevents any
second generation, including after a partial preparation crash. Payload/request bytes
are hash-checked on every resume, never recomputed for retry. Request<=20000 bytes,
PEM<=16384, returned directory<=8192; duplicate/nonfinite JSON is rejected.

| State/outcome | Continuation |
|---|---|
| PREPARED |One delivery of saved request bytes |
| DELIVERY_IN_PROGRESS after crash |DELIVERY_UNRESOLVED; no resend |
| NOT_SENT with proven pre-execution failure |TRANSPORT_NOT_SENT; one exact-byte retry, at most2 attempts |
| Generic exit/timeout/lost/partial output |UNKNOWN / DELIVERY_UNRESOLVED; readback only |
| Definitive pre-apply rejection |REMOTE_REJECTED; no retry |
| Valid exact gateway acceptance |REMOTE_ACCEPTED; local commit only |
| Local commit begun |LOCAL_COMMIT_IN_PROGRESS; reconcile files/DB |
| Remote accepted, local I/O failure |LOCAL_COMMIT_FAILED / REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED; retain all evidence |
| Readback/hash/sequence complete |COMMITTED; idempotent local readback |

The adapter contract does not equate an arbitrary SSH exit with NOT_SENT or REJECTED.
Actual gateway tests prove same number/same bytes idempotency and reject same number/
different bytes (typed adapter outcome CRL_PAYLOAD_CONFLICT), bad signature/issuer,
rollback number and invalid time/lifetime. Gateway mutation followed by lost/invalid
directory output is uncertainty, not proof of pre-apply rejection.

### Local commit and crash reconciliation

After remote acceptance: recheck prior CRL/hash/sequence and relevant paid/event/device/
invite/certificate/authority fingerprint; fsync local temp files, persist in-progress
journal, set exact sequence, atomically replace CRL/directory, fsync parents, commit
SQL, read back exact bytes/sequence and mark COMMITTED. Newer/conflicting local state
is not overwritten. No payload regeneration or second delivery repairs local failure.

| Restart case | Action |
|---|---|
| A: DB old, CRL old, directory old |Commit exact saved payload/response |
| B: DB new, CRL new, directory new |Validate and mark COMMITTED |
| C: DB old, CRL exact new |Finish sequence/directory from saved evidence |
| D: DB new, CRL exact old baseline |Install saved CRL/directory without incrementing again |
| E: Unknown/conflicting number or hash |LOCAL_COMMIT_CONFLICT; no generation/delivery |

Current directory hash must match exact old or validated new bytes in every case.
UNKNOWN trusted readback proving exact installed payload transitions REMOTE_ACCEPTED;
old payload remains unresolved, with no automatic resend; conflicts fail READBACK_MISMATCH.

Typed results: PASS, LOCK_BUSY, INVALID_PERMIT, PRECONDITION_FAILED,
CRL_GENERATION_FAILED, CRL_GENERATION_ALREADY_COMPLETED, CRL_EXPECTED_SET_MISMATCH,
CRL_UNEXPECTED_REVOCATION, TRANSPORT_NOT_SENT, TRANSPORT_FAILED,
CRL_DELIVERY_UNRESOLVED, CRL_PAYLOAD_CONFLICT, REMOTE_REJECTED,
GATEWAY_VALIDATION_FAILED, DIRECTORY_VALIDATION_FAILED, LOCAL_PRECONDITION_CHANGED,
REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED, LOCAL_COMMIT_FAILED, LOCAL_COMMIT_CONFLICT,
READBACK_MISMATCH. Receipts use only the prescribed sanitized allowlist; no stderr,
raw exception, profile, directory, URL, host, private path or key is returned.

### Source validation

| Gate | Result |
|---|---|
| New CRL helper / package tests |95 /3 PASS |
| Existing canary / paid backend / preparation |79 /76 /2 PASS |
| Existing restricted/admin/sync/directory/window tests |206 PASS,29 existing optional Go/native skips,4 explicit native deselections |
| PostgreSQL console / Django check / migration drift |118 PASS / PASS / no changes detected |
| Syntax / strict JSON / private-content scan / scoped links / staged scope / diff checks |PASS |
| Production registry/lookup/binding/CRL/delivery/paid writes |NOT_RUN |

Tests exercise the actual existing gateway against synthetic local files, not live
transport. A first run's3 isolated-sync tests rejected a venv site path inside checkout;
unchanged tests passed using the same accepted dependencies copied to an external
disposable venv. No production/path workaround or test assertion weakening. No native
build, Android action, full historical suite, Linux/Windows task or Friends restart.
Console tests used a separate disposable local PostgreSQL test DB.

Accepted lookup-only artifact remains unchanged:15 members/56017 bytes/SHA256
`63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308`.
Its source inventory excludes the changed restricted_admin and new helper; no rebuild
is needed. The final unbound CRL package receipt follows below.
No bound envelope/activation/expire/recovery permit is built.

The first post-commit package audit found IP constants in unused catalog-validation
functions. It was rejected by the capsule's no-IP gate and retained privately, not
delivered. A packaging-only follow-up extracts exact committed source segments for
the five required strict-parser functions and their two stdlib imports; no function
is rewritten, no authority/parser policy is relaxed. The full source blob hash,
selected names and exact segment hashes are recorded in source_projections, alongside
ordinary member hashes. Unused catalog/profile code and all IP constants are excluded.
AST equality, isolated import/help and deterministic package tests PASS. No accepted
lookup artifact or backend source is changed by this packaging correction.

### Deterministic unbound CRL package

Requested source commit: `ce09b96e9e00a9d8e23a31acbb4fdb906442cd28`
(`feat: add exact-payload CRL delivery for owner canary`). The subsequent packaging
correction is `8ba535d49c4e914a0aee0cacdd20405733bbe53f`; both ordinary pushes had
their remote main SHA independently verified. No published history was rewritten.

| Field | Verified result |
|---|---|
| Exact final package source |`8ba535d49c4e914a0aee0cacdd20405733bbe53f` |
| Binding / operation permit / production configuration |unbound / null / absent |
| Members / size |24 /138174 bytes |
| SHA256 |`3c3736917efb1720b7086e57e4e8b2182fcb56734ec85b662b9bed71c15840a6` |
| Source manifest SHA256 |`704b67df66d21e198e175344932f81e4d23e2e697f15475f45656be9af476ebb` |
| Two independent builds / fixed timestamps and modes |Byte-identical / PASS |
| Exact source/member/selected-segment hashes / AST equality |PASS |
| Strict JSON / IP-private scan / Python syntax |PASS |
| External-cwd help/manifest and isolated import smoke |PASS, Python3.14.4 |
| generate/deliver/commit/lookup CLI probes |DENIED; no registry opened |
| License/notices |LICENSE + THIRD_PARTY_NOTICES.md included; runtime dependencies not vendored |
| Original accepted lookup-only package |UNCHANGED; not rebuilt |

[Sanitized source manifest, all member hashes and projection provenance](2026-10-27-android106-beta-0-canary-1-crl-unbound.json).
Both final archives are retained read-only in private ignored evidence; rejected
pre-projection builds remain separate and must not be used. No archive is published,
bound, uploaded or executed against a registry. No private configuration, credential,
owner/certificate token, Support ID, CRL payload or production endpoint is included.

Source gate DONE. Status remains LIVE_ENTRY_SOURCE_READY / CRL_HELPER_UNBOUND_READY /
PRODUCTION_LOOKUP_NOT_RUN / LIVE_WRITES_NOT_RUN. This proves synthetic source behavior,
not production CRL delivery or live canary acceptance.

**STOP. NEXT — production read-only owner lookup and binding, not automatically.**
No production key/configuration installed, no CRL publication or local live files
changed, no CP2 redeployment or gateway/Android change. Historical evidence retained.

## Historical bounded recovery dispatch — source-only continuation

**SOURCE_READY_WITH_EMERGENCY_RECOVERY / LIVE_NOT_RUN.** Input main
`3a5e91d06977eb86fa78dec386477518fb5a0bfc`; accepted emergency source
`49bdd794cce32075d93691daa0b9f9cc7f7dffcf`. Same checkpoint, no new PLAN ID.
Only the practical dispatch guard, focused tests/docs and local lookup-only package
change. This is not completion of the broader live-entry preparation.

- New recovery first apply accepts `period_start<=server_now` and
  `server_now-period_start<300`: execution at start or1..299 seconds later can pass.
- Preserve exact `paid_until-period_start==2592000`, inclusive static period-start
  bounds `not_before<=period_start<=not_after`, half-open execution window
  `not_before<=server_now<not_after`, and `0<not_after-not_before<=300`.
- Never rebase or extend the signed-off payload: expiry is30 days from permit start,
  not30 days from delayed execution. Backend receives original period fields.
- Future dispatch, delay>=300s or a closed execution window fails typed
  `RECOVERY_DISPATCH_WINDOW_CLOSED` without inserting an event. Invalid duration or
  static period bounds still fail `INVALID_RECOVERY_PERIOD`; invalid window length
  still fails `INVALID_EXECUTION_WINDOW`.
- Normal four-stage path, version/state/certificate/eligibility guards, backend
  authority and terminal marker remain unchanged. Identical terminal recovery replay
  bypasses new-event dispatch checks; changed payload remains `EVENT_ID_CONFLICT`.
- Certificate/CRL state is not modified. Internal purpose/zero amount, sanitized
  receipts and non-paid fingerprints remain unchanged.

### Dispatch validation

| Gate | Result |
|---|---|
| Canary operator tests |79 PASS |
| PostgreSQL console tests / affected paid backend / preparation |118 /76 /2 PASS |
| Django system check / migration drift |PASS / no changes detected |
| Staged syntax / strict JSON / private-content scan |PASS |
| Staged Markdown local links / anchors |444 /23 PASS |
| Scoped staged diff / git diff --check |PASS |
| Production lookup/registry/binding/write permits/live operations |NOT_RUN |

Both recovery versions cover dispatch0/1/150/299s, unchanged payload/expiry and
actual server applied_at. Negative tests cover future start,300/301s delay, shortened
execution window, out-of-bounds period start and invalid duration/window length;
rejections preserve registry snapshots. CLI tests use the server clock at0/1/299s,
reject300s and prove no rebase. Existing idempotency/terminal/normal-path tests PASS.
Console tests use a separate disposable local PostgreSQL test DB; no running-console
upgrade, backend deployment or production connection is performed.
Unrelated unstaged operational notes remain untouched, including one pre-existing
missing Markdown anchor found by the working-tree check; the staged link gate passes.

### Dispatch lookup-only artifact

Source/tests/docs committed and pushed as
`ad086c030cc77c680d924fb9c8e37faa286adc4c`; remote main SHA independently verified.
Two independent builds from that exact committed source are byte-identical.

| Field | Verified value |
|---|---|
| Source commit |`ad086c030cc77c680d924fb9c8e37faa286adc4c` |
| Binding / envelope |`lookup_only` / null |
| Members / size |15 /56017 bytes |
| SHA256 |`63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308` |
| Strict manifest / exact member hashes / committed-source equality |PASS |
| Non-wrapper source members unchanged from accepted49bdd794 |PASS |
| Python syntax / strict JSON / private-selector scan |PASS |
| Import and --help smoke outside repository import path |PASS |
| Historical c5f2346c artifact unchanged |PASS |
| Bound/write-permit archive / production registry opened |NOT_BUILT / NOT_OPENED |

Both new artifacts are read-only inside private ignored evidence. Historical
artifacts/evidence remain untouched. Smoke executes only --help; no lookup, status,
apply or registry connection. No binding, credential or permit is included.

**STOP. NEXT — obtain the exact-payload CRL delivery helper contract, complete its
source gate, then read-only owner lookup/binding and coordinated phone preparation.**
The helper contract was not supplied in this continuation and is not invented.
No production lookup, binding, CRL generation/publication, Android action, payment,
enrollment, Friends restart or CP2 change. Live phone operations wait for owner ГОТОВ.

## Historical emergency recovery source gate —49bdd794

**SOURCE_READY_WITH_EMERGENCY_RECOVERY / LIVE_NOT_RUN.** Input main
`68b99ac667c78fa6f20f95ffa443cdbd7d1a5ef7`, accepted previous product source
`28657bf9e53411a4cdaff44d8ad5ebfb252046e0`. Same BETA-0-CANARY-1 under the existing
Android critical path. Only source/tests/docs and local lookup-only packaging;
no production registry/lookup, binding, enrollment, real payment, CRL publication,
Android action, Friends restart/deployment, CP2 backend change or desktop work.

### Exact recovery contract

- Normal activate0/activate1/expire2/activate3 sequence retained. Separate permit
  action recover is allowed only at expected_version1 or2, matching current
  subscription version and paid-event count. Versions0/3, explicit expiry and
  terminal revoke cannot start emergency recovery.
- First/second activation must already exist; all prior events are payments.
  Subscription stored state active, effective_state expired and paid_allow false
  prove natural expiry. Existing backend rechecks exact Android106 eligibility,
  non-revoked device/invite and existing admission restrictions. Full bound HMAC
  token/safe_ref/alias and no-other-cohort-member guards remain unchanged.
- Exact30 days: period_start=server_now, paid_until=server_now+2592000. First apply
  rejects a past/future start rather than rebasing the permit. Static bounds require
  period_start within not_before..not_after, execution within the half-open window,
  and window length1..300 seconds. Other durations fail INVALID_RECOVERY_PERIOD.
- Certificate inventory must exist and have no bound row with expires>server_now.
  Certificates, expiry/revision and non-paid tables remain unchanged. Future live
  procedure must wait any issued certificate's NotAfter+30 seconds; that wait and
  phone/serial observation are not performed or claimed by this source gate.
- Delegate to existing paid_beta.apply_event(event_type=payment), unchanged schema,
  APK attestation and authority. The transient reference is
  internal-canary-recovery:<event_id>; backend stores its SHA256, not raw text.
  No new event type, field, table, identity, invite or entitlement machine.
- Terminal detection reads reference_hash against SHA256 of that prefix plus each
  existing event ID. Find the incoming event first, then check the terminal marker,
  then run guards for a new event. A different ID after recovery fails
  RECOVERY_TERMINAL, including old normal-event replays. Same ID/backend payload
  returns the existing event; changed payload fails EVENT_ID_CONFLICT. Replay is
  permitted after window/entitlement expiry and does not extend the original period.
- After version1 recovery: active/version2/count2 and
  NATURAL_PHASE_ABORTED_OWNER_RECOVERED. After version2 recovery:
  active/version3/count3 and CRL_PHASE_ABORTED_OWNER_RECOVERED. The checkpoint's
  normal path is permanently closed after either branch. Classification is derived
  from immutable event order, not a replay caller's changed expected_version.
- Safe wrapper output adds branch emergency_recovery; purpose internal_canary and
  amount0 stay non-revenue. Raw authoritative backend event/receipt is unchanged.
  No selector, canonical device, HMAC key, raw reference, invite or certificate body
  enters the sanitized output. Transactional non-paid fingerprints are checked;
  unexpected trigger side effects roll back the whole new event.
- CRL number/entries are not generated, published, removed or rolled back. An old
  expired serial may stay in CRL; proving a future new certificate has a different
  unlisted serial is live acceptance, not a source-checkpoint side effect.

### Required validation

| Gate | Result |
|---|---|
| All canary operator tests, including normal path |68 PASS (30 existing +38 emergency cases) |
| Existing PostgreSQL console tests |118 PASS in separate disposable test DB |
| Existing affected paid backend tests |76 PASS |
| Existing preparation tests |2 PASS |
| Django system check / migration drift |PASS / no changes detected |
| Staged source syntax / strict JSON / secret-private scan |PASS |
| Markdown local links / anchors |446 /23 PASS |
| Staged scope / working and staged diff --check |7 files / PASS |
| Production lookup/registry access/binding/live procedure |NOT_RUN |

Emergency tests cover both versions, active/valid-certificate/revoked/explicit-expire
denial, exact period/start/window, token/alias/safe_ref/device/eligibility guards,
sanitized zero-amount classification, unchanged identity/invite/support/certificates/
CRL sequence, transactional rollback, concurrent replay, payload conflict, terminal
normal-path/recovery rejection and exact server-clock CLI behavior. Existing normal
expire/final certificate guards still PASS. Tests use generated synthetic identities
only. Packaging tests now build only lookup_only archives and smoke --help; no bound
permit archive is created even by those packaging fixtures.

The console image/schema/configuration was not rebuilt/restarted/migrated in this
source checkpoint. No historical full suite, CP2 source/package gate, Linux or Windows
gate repeated. Prior production counts0/0 remain accepted input, not a fresh live read.
Source commit `49bdd794cce32075d93691daa0b9f9cc7f7dffcf`
(`feat: add terminal emergency recovery for owner canary`) pushed to main; remote
SHA verified before packaging. Prior lookup artifact c25447d9… stays immutable
historical evidence and was independently verified unchanged.
Pre-existing123 added lines in unrelated working-tree edits and untracked work are
preserved outside this source commit; private validation evidence remains ignored.

### Deterministic emergency-capable lookup artifact

| Field | Exact result |
|---|---|
| Source commit | `49bdd794cce32075d93691daa0b9f9cc7f7dffcf` |
| Binding | `lookup_only` (envelope null) |
| Members |15 |
| Size |56021 bytes |
| SHA256 | `c5f2346cd4d46a6bf3875e2181e81027c7db43f62b886161756230b6499adc31` |
| Independent builds |2; byte-identical PASS |
| Strict manifest / exact inventory / member hashes |PASS |
| Members match exact committed source |PASS |
| Existing backend/identity modules match accepted28657bf source |PASS |
| Python syntax / private-selector scan / local import-help smoke |PASS |
| Production registry opened / bound permit archive / live operation |NOT_RUN / NOT_BUILT / NOT_RUN |

Both newly named local artifacts are retained read-only in private ignored evidence;
no historical archive was replaced. Only sanitized package metadata is committed.
This artifact includes the recovery source but cannot perform a bound operation:
lookup_only does not carry a device binding or operation permit. Smoke used --help,
not lookup/status/apply, and did not open any registry. No automatic next-stage run.

**STOP. NEXT — production lookup, binding and coordinated owner-phone live procedure.**
Do not start that next stage automatically; this checkpoint grants no live execution.

## Historical continuation from55c6a24 — local upgrade and bounded operator

**CHECKPOINT / LOCAL_CONSOLE_UPGRADED / CANARY_OPERATOR SOURCE_READY / LIVE NOT_RUN.**
Same task and same sole OWNER_CANARY_1 authorization; no new top-level PLAN ID.
The owner has supplied the four live goals and the final same-identity recovery
target of server_now+30 days. The continuation stops at the suggested component
paths; short live windows, reviewed CRL delivery and physical-phone coordination
have not been supplied. They were not guessed.

### Local console upgrade

- Private backups: PostgreSQL custom dump and the complete synthetic volume, taken
  while the local console was stopped. Online PG dump remains consistent while the
  separate read-only inventory monitor runs. PG disposable restore/open and SQLite
  disposable restore/integrity/FK checks PASS. Files0600/directory0700; no backup,
  DB, credentials or private receipt committed.
- `.env`, inventory HMAC key and operator credentials backed up privately and
  verified byte-identical after upgrade. No credentials printed or regenerated.
- Source-only preparation and local image rebuild completed; running migration
  now0006. Django system check and migration drift PASS. Console health PASS;
  HTTP remains127.0.0.1:8765, PostgreSQL has no published port.
- First local start stopped before Django because a restrictive umask produced
  root-owned source files unreadable by the non-root console user. Preparation now
  sets only copied allowlisted generic source files0644/directories0755 beneath
  private `.local`0700. Original source/private permissions unchanged. Rebuild and
  local start PASS. This was not a production restart or a paid-service failure.
- Running image ID: `sha256:1e28103e380a4acd5143f7055feb49ad6019ebe2fd01b142fd37f06d336752d9`.
  Application payload is the accepted55c6a24 console source; the preparation fix
  changes context permissions, not the entitlement authority or Android artifact.
-50 synthetic device bindings and synthetic registry devices/invites/support/paid
  tables preserved; all prior workflow rows preserved. Existing3 payment records
  now have default customer_payment.559 prior audit rows compared to the restored
  backup and retained unchanged;8 concurrent inventory.import records were appended
  at the comparison readback. Projection observation timestamps refresh normally.
- No real-owner DeviceProjection or synthetic substitute created. Production
  write actions remain absent: Django still opens only the guarded synthetic
  registry. No production DB is mounted or copied into Django.

### Canary-only source boundary

`control/friends/paid_beta_canary.py` delegates status/activation/expiry, idempotency
and conflict detection to the unchanged `control.friends.paid_beta`. It provides
read-only transient-stdin lookup, then full HMAC-token-bound status and a fixed
single-operation permit. No runtime write selector/reference/event/time override;
no revoke/grace/delete/migrate/restart/CRL operation. Exceptions/receipts do not echo
the selector, key, raw device or registry path.

The bounded workflow has at most four new events: initial activation, activation
after natural expiry, explicit expire with a still-valid certificate, and recovery
after all retained target certificates expire. Each operation needs a separately
reviewed exact envelope (server execution window at most15 minutes; no default
paid duration; ceiling31 days). Existing paid backend remains the only state machine.
Guards reject a second cohort member, stale versions/counts, bad bindings, invalid
Android eligibility and non-paid table changes. Duplicate permits return the
original event plus fresh status, never an implicit renewal.

`scripts/package_paid_canary_operator.py` exports only allowlisted committed
sources with source hashes/license/dependency metadata and an optional immutable
safe envelope. Repeated builds are byte-identical; dirty source, DBs, `.env`, keys,
private selector and other operator modules are excluded. No production-bound
envelope/package or owner token has been created. No package was uploaded/executed
on a gateway. There is no new Django production adapter or receipt importer; any
future import must validate a strict sanitized safe_ref-keyed receipt, not create
a fake DeviceProjection or authoritative subscription copy.

Committed lookup-only artifact (not bound to an owner and not deployed): source
`28657bf9e53411a4cdaff44d8ad5ebfb252046e0`,15 members,52921 bytes, SHA256
`c25447d92bcc3edd0b26889734465e759cbb5a682697f055a3d64a847a894e8e`.
Independent repeat build byte-identical; internal source-manifest hashes and local
CLI import/help PASS, no registry opened. Both private artifacts retained read-only.

### Validation and remaining boundary

-118 PostgreSQL console tests PASS on the rebuilt image in a separate disposable
  test database: purpose defaults, zero canary acceptance/customer rejection and
  analytics separation included. System/drift checks PASS.
-76 existing affected paid backend tests PASS using the retained control/identity
  environment. No CP2 source/package gate or repository full suite repeated.
-30 new canary wrapper/packaging tests +2 restrictive-umask tests PASS, including
  real synthetic backend transitions, denial/recovery/idempotency/conflict, guarded
  stage/window/certificate/binding/eligibility rejection, unrelated-trigger rollback,
  strict input/no echo and packaged subprocess readback.
- Source closeout:11 staged source/test/doc files; Python syntax,448 local link
  targets, added-content privacy scan, strict private JSON and both staged/working
  `git diff --check` PASS. Unrelated pre-existing123 added lines and untracked work
  remain outside the commits. Private backups, credentials and historical evidence
  retained, never staged. Source commit pushed and remote SHA verified before this
  artifact-receipt closeout.
- Production lookup, binding, activation, expiry, live Connect/session, CRL delivery,
  recovery/reactivation and Android state readback remain **NOT_RUN**. No customer
  payment/enrollment, CP2 deployment/restart/migration, gateway/publisher/admission
  mutation or Android/Linux/Windows change. No canary slot occupied yet.

**Historical NEXT at28657bf/68b99ac — obtain the remainder of the live procedure and
coordinate the owner phone.** The final30-day active
and connect-capable owner state is a required future gate, not a claimed result.

## Historical result and scope at55c6a24

**CHECKPOINT / PAYMENT_PURPOSE SOURCE_READY / LIVE NOT_RUN.** Input main:
`6d5202128ebfda6b60446d4f85cd7d9e5f2323fc`. This is a substep of the existing Android
critical path, not a new top-level project or CP3. CP2 is owner-accepted **DONE /
PAID-AWARE EMPTY-COHORT BACKEND SERVING / PUBLISHER CAPABILITY PRESERVED /
REAL PAYMENT AND ENROLLMENT NOT_RUN**. Its deployment/migration/restarts and
source/package gates were not repeated.

The sole authorized production target is designated **OWNER_CANARY_1**. Planned
allocation is one permanent internal slot out of ten, leaving nine customer slots
after enrollment. No row or reservation was created: this allocation is not yet
an observed backend state. No alternate production identity was used. The private
administrative selector was not passed to tools, copied into operator files or
persisted in Git/docs/PG/audit/URLs/sessions/logs/screenshots/receipts/event IDs/
external references. No device-token mapping is invented: administrative lookup
and HMAC binding are NOT_RUN.

## Implemented operational metadata

- `PaymentRecord.purpose`: `customer_payment` / `internal_canary`; default and
  existing rows remain customer payments. Existing confirmation metadata is preserved.
- Customer amounts remain positive. Internal canary must have zero amount, is not
  a customer payment/revenue, and retains the existing currency field as zero-value
  metadata only. Model/form validation and PostgreSQL constraints fail closed.
- Purpose is immutable from creation, including before confirmation. Existing
  confirmed-record/intent/audit immutability, reference uniqueness and permissions
  remain in force. No payer/bank/secret/selector fields were added.
- Customer-payment analytics exclude canaries; a separate confirmed-canary-record
  counter is explicit, not a count of devices/cohort slots. Operational activity
  still counts operations, not revenue.
- Russian form/detail/preview screens, admin filter, new metadata audit rows and
  administrative receipt wrapper expose the purpose. Raw authoritative backend
  receipt is not modified; synthetic integration still produces `event_type=payment`
  with existing idempotency and one request/event behavior.

Friends `paid_beta` remains the only entitlement authority. No changes to its
schema/state machine/cap10/idempotency/challenge/fetch/certificate boundary, client,
protocol, keys, invitation or activation semantics. The console remains synthetic
for write workflows; production inventory remains read-only. No production device
was copied into a synthetic projection to bypass that separation.

## Validation and installation boundary

- 23 new PostgreSQL tests PASS: purpose defaults/constraints, pre/post-confirmation
  immutability, analytics separation, metadata-only no-enrollment, form/admin/receipt
  rendering, unchanged synthetic backend activation/idempotency, migration of an
  existing confirmed payment and repeated migrate with a fresh migration loader.
- 118 console tests PASS in a separate disposable PostgreSQL test database with
  per-test synthetic registry copies. The first repeated-migration test reused a
  stale MigrationExecutor cache; the test was corrected and rerun successfully.
  No live schema was affected by that test failure.
- Migration drift check PASS; Django system check PASS. These are console checks,
  not a CP2 package/source gate, full repository suite or Android live acceptance.
- No running-console upgrade, production registry lookup/write, device interaction,
  CP2 restart, CRL publication or gateway change. Android106 was not rebuilt or changed.
  Installed APK/state and actual live session behavior were not reverified here.

Migration0006 is source-ready and tested, **not installed into the running console**.
No real payment/customer enrollment or owner-canary activation was performed.
Do not roll a nonempty paid cohort back to a pre-paid backend or delete paid/audit
rows. Neither test migrations nor SQLite fixtures constitute live recovery evidence.

## Live completion gates still open

| Gate | Result |
|---|---|
| Exact authorized-device lookup/HMAC binding and Android106 observation | NOT_RUN |
| Internal owner enrollment and production activation | NOT_RUN |
| Readiness/certificate paid boundary and successful MESH Connect | NOT_RUN |
| Natural expiry; new challenge/fetch/reconnect denied | NOT_RUN |
| Already-active session behavior after expiry | NOT_RUN |
| Paid-aware CRL generation and gateway propagation | NOT_RUN |
| Recovery/reconciliation and repeat activation on the same identity/invite | NOT_RUN |
| Android identity/activation/settings/history preservation | NOT_RUN |

The submitted procedure ends at the `purpose` choices. A live expiry period,
observation/CRL propagation/session stop bounds and safe recovery sequence were
not supplied. They must be agreed before mutating the owner's production access;
this checkpoint does not invent a period, assume a CRL deployment path or substitute
synthetic results for the authorized physical-device canary.

## Source closeout

The staged scope contains19 source/test/documentation files only. Staged Python
syntax,455 local Markdown links/anchors, added-content secret/private-data scan,
strict JSON validation of the local sanitized validation summary, and
`git diff --check` / `git diff --cached --check` PASS. Pre-existing unrelated
working-tree changes and private/historical evidence remain untouched and unstaged.

**Historical NEXT at55c6a24 — obtain the remaining live procedure.**
Only OWNER_CANARY_1 is eligible; no customer payment/enrollment, alternate identity,
CP2 redeployment, Linux/Windows work or new top-level PLAN ID.
