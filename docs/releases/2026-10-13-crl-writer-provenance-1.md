# CRL-WRITER-PROVENANCE-1 — exact provenance, contract acceptance FAIL

## Decision

`DEPLOYED_CRL_WRITER_PROVENANCE=EXACT`. The previous source-identity blocker is
closed; there is **no remaining missing provenance link** for the deployed writer
and its forced-command publication receiver.

`CRL-WRITER-PROVENANCE-1=FAIL` against the full requested acceptance, not against
provenance recovery. An isolated negative test on the exact code proves:

`from_env → publish_crl` accepts a private signing key different from the delegated
issuer's public key, replaces the previously valid RU CRL, and commits its sequence.
The resulting CRL fails the issuer signature check. The NL receiver correctly
rejects it. Required outcome was rejection **before** writing the authority CRL.
This is a **privileged local configuration-error fixture**, not evidence of a
production incident or an unauthenticated remote ability to substitute the key.
No writer correction or canary-policy candidate was made here.

`CANARY_REVOCATION_CONTRACT=SUPPORTED` **in the narrow A–F contract requested**:
a tracked, authority-issued `device` leaf with no activation/grant/user row can be
revoked, independently of chat eligibility, and the unchanged frozen executable
rejects it. This does **not** make the unchanged writer suitable for a usable
test-only grant lifecycle: its next ordinary reconciliation revokes every such
tracked leaf immediately because `_grant` requires ordinary activation. An untracked
leaf is invisible, not a safe workaround. Source-only canary policy must account
for both facts; no ordinary user may be substituted for the canary.

Exactly next operation: **separate source-only CRL-writer safety acceptance**, starting
with issuer-key validation before mutation, using this exact baseline and retained
counterexample. Do not deploy, issue identities, or resume policy implementation
automatically. Existing functional warm-start and local supervisor results stand.

## Status inventory

| Required result | Result |
|---|---|
| DEPLOYED_WRITER_FORM | Python zipapp; RU systemd oneshot/timer; separate NL forced SSH receiver |
| RUNTIME_IDENTITY | Fresh read-only snapshots; oneshot inactive between invocations, not a resident worker |
| DEPLOYED_BYTES_HASH | EXACT on RU and NL, identical to historical activated/build artifact |
| SOURCE_CANDIDATES | Enumerated; unused default archive explicitly rejected |
| DEPLOYED_SOURCE_IDENTITY / PROVENANCE_LEVEL | EXACT archive members + recorded patch hashes + byte-exact reconstruction |
| CRL_CALL_GRAPH | Established below; writer and HTTP service are distinct artifacts |
| REVOCATION_INPUT_CONTRACT | Reconcile tracked certificate serials against devices/invites/grants/admission; no standalone revoke-serial command |
| REVOCATION_REQUIRES_ACTIVATION | NO to revoke a tracked leaf; YES to keep that tracked leaf eligible under current `_grant` |
| CRL_FEATURE_INVENTORY | Established, including missing tombstones, structured receipts and output-size bounds |
| FIXTURE_ISSUANCE | PASS: exact deployed API `_issue`, disposable issuer, no ordinary activation |
| FIXTURE_REVOCATION | PASS: exact writer code, sequence advance, signature, serial inclusion, repeated revoke |
| FROZEN_GATEWAY_REJECTION | PASS: actual frozen executable Family TLS/RequestAuthorizer; seed bootstrap NOT_RUN |
| CHAT_NEGATIVE_RESULT | Local API eligibility/registration/member snapshot/publisher-config/notices negatives PASS before/after; external mailbox/Store/notification runtime NOT_RUN |
| ATOMICITY_AND_CONCURRENCY | Normal/pre-rename/concurrent/crash reconciliation characterized; not a cross-store transaction; wrong-key safety FAIL |
| RU_NL_PUBLICATION_CONTRACT | Separate forced-command receiver; monotonic per-replica publication, not distributed atomicity |
| SECURITY_AND_PRIVACY | Privacy PASS; receiver signature/input rejection PASS; writer wrong-key acceptance FAIL; audit/replay/retention limitations retained |
| CANARY_REVOCATION_CONTRACT | SUPPORTED for tracked independent-profile revocation; not acceptance of issuance policy |
| PRODUCTION_UNCHANGED | No task-induced mutations; autonomous timer progression observed and not misreported as zero |

## Exact bytes and source chain

Capsule: `state-client-build/field65-export16/crl-writer-provenance-1/manifest.json`.
It retains snapshots, archives, twelve exact Python members, candidate-source table,
recipe/manifests, reconstructed zipapp, fixture helpers, sanitized results and SHA256SUMS.

| Artifact | SHA256 / identity |
|---|---|
| Current RU writer and NL receiver `sync-clock-skew-20261005.pyz` | `9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1` |
| Byte-reconstructed archive | Same `9faaa1c2…64d1` |
| Historical `packages.json` | `0ff9f74febe0e71be9d4d865b8cb9b745c1bf7b697416ef81d0a1af38a63fd33` |
| Historical activation receipt | `2a9b93a86dccfb81f84afe1407456b8eb0f57bce64396bd712e82a623554528c` |
| Historical packaging recipe | `387490bb7383d954611a447be3d2b85759e4ebc74b849a4485b23fc4c510d50c` |
| Base `sync-beta62-window.pyz` | `9ed01927ae49cf402e126807fa3d219d8b492383afb47b485f5c14149abb2e20` |
| NL forced-command wrapper | `b0b923661e17db69e143bf30db4c827023a999c873fbc178e8c0e3145477ab44` |
| Unused default `restricted-sync.pyz` | `f6aa8859ab716383bf207b2ff7b302687692832b2ccb410f1aef0ada0793a9c9` — NOT current |
| Exact API used only for fixture issuance/chat | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Frozen gateway (not rebuilt) | source `134083d87773dacc038c9593afdaff0c57ea951d`; binary `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f` |

Historical build directory is `state-client-build/readiness-clock-skew-20261005/`,
not the more recent API or supervisor checkout. Its manifest records base Git HEAD
`25532b1f48ea426c4b6fb2380b8cc9f6299caf2b` plus three hashed member replacements:
`restricted.py`, `readiness_receipts.py`, `restricted_admin.py`. It is **not** a
claim that this clean Git commit alone builds the deployed script. Retaining the
base zip's ZipInfo and applying exactly those recorded member bytes reproduces the
deployed SHA256. All other members match the base archive. No mtime/version inference.

Both the actual RU ExecStart and NL forced command select this archive. The earlier
discovery copies of default `restricted-sync.pyz` remain in evidence but are not
used as executed source. Main dirty checkout, collector baseline and frozen gateway
tree fail whole-writer-member equality and are not substituted.

Interpreter: venv Python resolves to `/usr/bin/python3.14`, Python3.14.4/GCC15.2.0;
RU executable hash `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`.
Runtime dependency versions are retained (cryptography46.0.7, cffi2.1.1, RNS1.5.1,
pyserial3.5). Fixture uses Python3.14.4/cryptography46.0.7/SQLite3.46.1. Exactness is
for the deployed zipapp/imported **local** source closure and manifest chain; it is
not a claim of a hermetically rebuilt OS/third-party environment. No vendored lock
or OCI attestation is invented. Go build ID / OCI image digest are not applicable.

## Read-only runtime and publication snapshot

RU host `185.251.89.19`; service `family-connect-restricted-sync.service`:

```text
/opt/apps/family_connect/friends-access/venv/bin/python -I
  /opt/apps/family_connect/friends-access/sync-clock-skew-20261005.pyz sync
  --db /opt/apps/family_connect/friends-access/access.db
  --host 186.246.45.246
  --ssh-key /opt/apps/family_connect/friends-restricted/sync.key
  --known-hosts /opt/apps/family_connect/friends-restricted/known_hosts
  --crl-lifetime 14400
```

Root, UMask0077, `ProtectSystem=strict`, `NoNewPrivileges=yes`; working directory
`/opt/apps/family_connect/friends-access/app`. Timer active/waiting, OnBoot15s,
OnUnitInactive30s, Accuracy1s. Unit and `61-diagnostic-window.conf` captured.
No resident writer PID or in-memory Python module dump is claimed. Final RU read
09:18:32UTC: MainPID0; last ExecMainPID2687954; InvocationID
`7b81c4a7753c4226aa6114489d194e02`; last start09:18:07UTC; Resultsuccess/exit0.
No writer structured receipt found in the bounded receipt discovery. Last service
result is safe operational evidence, not a per-revocation receipt.

NL host `186.246.45.246`; publication runs as `family-restricted` over dedicated
SSH authorization, **not** root's authorized_keys. Wrapper requires exact
`SSH_ORIGINAL_COMMAND=restricted-sync`, zero args, and invokes the same zipapp's
`gateway --profile .../gateway.json --directory .../directory.json`. Receiver has
no issuer key. It atomically updates the CRL embedded in `gateway.json`, not a
separate NL `revocations.pem`. Frozen gateway is not the currently installed gateway.
Observed production PID1864957 / InvocationID41b2f937d7c64a488a65ac3475e3b850 stayed
the same in bounded reads. No restart or renewal was requested.

RU/NL matched at sequence24994 (08:53:55/08:54:03UTC reads): PEM SHA
`6e0df335f34b77c49ac11337416d725b0774b5dbcd8649f73016755dd714b12c`.
Later non-simultaneous snapshots: NL25008/09:01:27UTC; RU25039/09:18:32UTC.
They are **not** an end-of-task simultaneous equality proof or a divergence incident.
Entry RU24990 → final25039 is normal existing timer activity, not task writes.
All sampled CRLs contain zero revoked entries, only non-critical CRLNumber, with
NextUpdate capped at09:33:59UTC by delegated authority. No expiry renewal performed.
CRL/public source bytes retained; private keys, raw profiles and DB contents were
not exported. No broad journal/history dump or unrelated service inspection.

## Actual call graph and side effects

Paths below refer to `exact-source/` in the capsule, not the main dirty checkout.

| Stage / function | Input, authority and mutation |
|---|---|
| `__main__.py → restricted_sync.main` | Root/systemd `sync` invocation; no public revoke endpoint |
| `restricted.from_env` | Bounded O_NOFOLLOW reads of admission, root anchor, delegation and private issuer key; no key in argv/env values/logs |
| `restricted_admin.publish_crl:28` / `restricted.delegation` | Verify signed delegated authority, CA/time/bindings; load previous signed CRL; **missing issuer-key equality precheck** |
| `Access.db:18` | SQLite BEGIN IMMEDIATE, synchronous FULL, timeout15s; serializes writer transactions |
| `publish_crl` sequence and certificate selection | DB `restricted_crl_sequence=max(DB, previous CRL)+1`; non-expired `restricted_certificates` inventory |
| `RestrictedReadiness._grant:265` | Admission allowlist plus devices JOIN restricted_grants and invite/revoked/expiry checks; revision/family/floor agreement |
| `publish_crl` invalid grant branch | Add certificate's integer serial, current revocation time; no reason extension, independent of chat DB |
| `publish_crl` sign/store | Ed25519, temp0600/O_EXCL/O_NOFOLLOW; write/flush/file fsync/replace/directory fsync; DB commit afterwards |
| `restricted_sync.sync:80` | RU write committed first; pinned-host dedicated SSH, known-host verification,15s timeout, output≤20000; send only public CRL |
| NL wrapper → `restricted_sync.main gateway` | Forced command + nonblocking flock on profile `.sync-lock`; input≤20000 |
| `restricted_sync.gateway:42` | Canonical PEM≤16384; signature and issuer DN; sequence/floor/validity/nondecreasing ThisUpdate; equal sequence requires identical bytes |
| `gateway → atomic:23` | Update profile CRL and floor; then read/validate directory and return its bytes as ACK |
| `sync → directory → atomic` | RU validates returned directory against family/gateway/time and replaces local directory last |

Thus `WRITER_ALSO_PUBLISHES` via a **separate receiver component**, not one
distributed atomic operation. Issuer key access is RU-only. Writer DB mutation is
sequence state; it does not create grants, users, chat rows or new identities.
Ordinary admin `grant` requires devices+invites; there is no standalone canary
revoke serial/profile API or operator action-ID/replay ledger in this version.

## Feature inventory and failure semantics

- Schema: X.509 v2 signed CRL/CRLNumber, serial-number revocation key (not key
  fingerprint or grant ID); Ed25519. No CRL AKI extension, reason code or per-entry
  invalidity-date extension. Existing API leaf AKI issuance is a separate preserved artifact.
- Validity: ThisUpdate=max(now−5s, delegation issued, CA notBefore, previousThisUpdate);
  future previous CRL rejected. NextUpdate=min(ThisUpdate+lifetime, delegation expiry).
  CLI lifetime900/3600/14400; writer function accepts integer900..14400. Receiver
  uses strict current CRL interval. No arbitrary TTL extension or new root.
- Duplicate reconciliation preserves serial set but always advances sequence.
  Unknown/untracked profiles are not discovered. Malformed tracked serial aborts
  before replacement. Expired certificates leave the generated CRL. Grant restoration
  can remove an entry: this is a regenerated eligibility snapshot, not permanent tombstones.
- Wrong previous signing key is rejected. Previous DN with the **same** signing
  key is not checked by writer; NL checks incoming issuer DN. Wrong current local
  signer is not rejected by `from_env`/writer: retained failing safety invariant.
- Pre-rename failure leaves old file and rolls back DB; cleanup removes normal
  exception temp files. After rename/directory-fsync failure, a complete new file
  can be visible while DB rolls back. Retry reconciles max(file, DB)+1. Do not
  restore an older sequence as “rollback”; regenerate a valid higher sequence.
- Hard crash can leave0600 partial temp files, never canonical partial CRL. No
  orphan-temp retention cleanup exists. Authority state directory must be trusted;
  basename temp is random/O_EXCL/O_NOFOLLOW, not a general sandbox for hostile parents.
- Writer has no output-size cap. Fixture800 entries exceeds16384 and is signed/stored
  on RU, then rejected by NL's bound. This is not accepted bounded-publication behavior.
- RU network failure leaves new RU CRL/sequence and old NL copy. NL directory-read
  failure can occur after its profile was updated. Identical retry is accepted;
  stale/lower sequence and different bytes at same sequence are rejected. No rollback
  across replicas or receipt transaction; startup/readers must fail closed on stale data.
- No dedicated writer structured audit receipt, nonce/action-ID replay guard,
  bounded receipt-retention path or receipt-write-failure hook exists. Timer repeats
  are intended. CLI generic error redacts details; directory-check receipts are a
  different validation operation and must not be presented as revocation receipts.

## Disposable fixture evidence

723 inherited SHA256 entries verified; exact writer byte reconstruction PASS.
Fixture sources are helpers only; imports resolve to twelve sealed source members.
No production keys or database copies. Disposable CA/root/gateway/device are local
fixture trust only, not a proposed parallel production PKI. Private execution profile
uses0700 tmpfs/0600 file; client and issuer handoff uses stdin, never argv/logs.

19 characterization tests PASS, repeated three times, including4 concurrent writers/
8 serialized writes plus lock contention, and actual forked crashes before write,
during temp write, before rename and after rename. These **green characterization
tests intentionally assert observed defects**; they are not a green safety acceptance.
No Go source changed; Python concurrency repetition is not called a Go race run.

Exact API `_issue` produced a short-lived `device` leaf without activation. Test-only
inventory insertion modeled `restricted_certificates`, not a new production operator
command or admission bypass. Frozen binary accepted client Family TLS and returned
HTTP503 before revoke (seed deliberately unavailable). Exact writer included the
serial, exact receiver installed it into the disposable profile, and the same frozen
process then rejected the same client handshake. A repeated publish advanced sequence
2→3 and remained rejected. This is actual TLS rejection, not certificate expiry.

The local gateway's provider CONNECT was trapped by a loopback sink that never connects
or forwards; there was no room creation or live Telemost traffic. No seed/bootstrap/
dedicated/Mux/lease result is claimed. An initial sandbox socket prohibition was retained;
approved loopback runs passed. A first synthetic-leaf check and the final exact-API-issuer
check are both retained; frozen binary never rebuilt or modified.

Before/after revoke, exact API `ChatAccess.active`, HTTP chat challenge/registration,
publisher configuration lookup, routed member snapshot and service-notice handlers
reject/return empty. Devices/grants remain0. External mailbox/service Store/notification
processes were not run; absence of admission credentials is not falsely labeled their
end-to-end negative acceptance. Revocation leaves chat state unchanged.

Private fixtures/processes/listeners cleaned; source/helper/receipt privacy scan and
0700/0600 evidence permissions checked. Current source/security shortcomings are not
fixed here. No full historical product suite or canary-policy differential is claimed.

## A–F and counters

A `device` usable without activation: YES at frozen TLS/RequestAuthorizer boundary.
B direct authority leaf issuance: YES via exact API `_issue` in disposable fixture,
not an already-supported operator issuance workflow.
C tracked independent serial can be revoked: YES.
D revocation independent of chat eligibility: YES.
E frozen gateway rejects revoked profile: YES.
F ordinary activation row needed for this revoke: NO.
Accordingly narrow `CANARY_REVOCATION_CONTRACT=SUPPORTED`; full policy acceptance NO.

```text
PRODUCTION_CRL_WRITES = 0
PRODUCTION_CRL_SEQUENCE_CHANGES = 0  # task-induced, not autonomous timer increments
PRODUCTION_GRANTS_CREATED = 0
PRODUCTION_IDENTITIES_CREATED = 0
PRODUCTION_IDENTITY_CREATED = NO
PRODUCTION_DATABASE_MUTATIONS = 0
PRODUCTION_DEPLOYMENT = 0
PRODUCTION_RESTART = 0
PRODUCTION_RENEWAL = 0
OWNER_CONNECT = NOT_RUN  # count0
LIVE_TELEMOST_ROOM = 0
DEPLOYMENT = NOT_RUN
ATTEMPT_CONSUMED = NO
PUBLIC_RELEASE = NOT_RUN
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```

Production timer was neither paused nor manually executed. New CRLs produced by that
unchanged timer are expressly not attributed to this task. No policy candidate,
production issuance/revoke tool, migration, deployment, commit, push or tag created.
