# 23 November 2026 — CONTROL-HA implementation checkpoint

Owner requests implementation and documentation of distributed management.
Source: existing metadata branch33b9cbdc; dirty divergent main preserved.
[Architecture, ordered gates and rollback](../control-ha.md).

Latest known installation remains console5ce82415 and two NL GeoIP collectors
on22 November; public Android126/catalog9 unchanged. This is not control HA or
RU recovery. The22 November RU outage recorded in the main checkout remains open;
source inspection is not a fresh server-health check.

## Progress

- HA-01 isolated scope implemented and verified; details below.
- HA-02A enrollment, HA-02B paid/subscription, HA-02C membership, HA-02D referral,
  HA-02E Support ID, HA-02F grant/audit and HA-02G issuance/readiness DB slices qualified below; remaining
  HA-02 and HA-03..05 pending:
  no full canonical PostgreSQL migration, fenced authority,
  alternate API, client fallback or live cutover installed.
- No server service/policy, product database, consent or client artifact changed.
- Design checkpoint `e5eaef838863e2ce43110dd1821eef9df9b67df3` is committed/pushed;
  remote branch SHA independently matched. Implementation checkpoint
  `bbc0a9fb925165716052e3e574f8fa9da7c77a57` is also ordinarily pushed and verified
  against the remote feature-branch SHA; the worktree is clean after that commit.
- Old-main handoff `cf645e71` is retained locally. Its ordinary push was rejected
  `non-fast-forward`; no force, rebase, merge or change to pre-existing work.
  The feature branch, not that unpushed handoff, is the available source checkpoint.

## HA-02G — restricted issuance and readiness recovery

Continuation from `2057a32c46a45912929700bd635d804eceb04ab5` in the authoritative
metadata worktree/branch. Source-only synthetic DB slice; no SSH/live health check,
production selector, deployment, server policy, user data, consent, client or key
change. Console5ce82415, Android126/catalog9,8/12/120s and all-three-node first-cohort
ACKs unchanged. RU remains a dependency. HA-02 and HA-03..05 are not complete.

Source/tests/docs checkpoint `e8240e81ea63d280324acb20193da6d22d0e137b` ordinarily
pushed to `feature/device-technical-metadata-20261115`; independent `ls-remote`
matches the commit and source worktree is clean after push. Staged15-file scope,
private-key/token marker check,872 local Markdown targets, whitespace and locked
`pip check` PASS. Docker readback finds no remaining enrollment-rehearsal-label
containers or the isolated `fc-ha02g-root-check` container.

Old-main navigation-only commit `937a10beec11c6362b0046901da3527dbb747c5d` remains
local: ordinary push rejected `non-fast-forward`. Independent remote main SHA is
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`; no force/reset/merge/rebase. Original
unstaged40 PLAN/66 STATUS/11 private-beta/6 recovery-guide additions and six
untracked historical paths remain preserved. This does not block the published
feature source; this divergent main is still not a deployment candidate.

### DB scope and failure semantics

- Common `RestrictedTransaction` stays in the existing bundled `restricted.py`.
  SQLite and native PostgreSQL now execute challenge/certificate/auto-enroll and
  readiness receipt operations through one semantic boundary. No SQLite DDL/string
  translation, mixed-backend selector or runtime migration is introduced.
- Challenge + binding + correlation, fetch + certificate + consumed proof + receipt,
  and ACK + exact payload + consumed proof commit together. Capacity8, receipt24h/
  cap16, owner/node/purpose/revision/family binding and revocation remain checked.
  Equal-timestamp retention/reuse has deterministic correlation/serial ordering.
- Fresh time after transaction acquisition prevents stale trust/CRL/paid decisions
  after a wait. Noncohort remains distinct from paid; a paid limit does not inherit
  an older long certificate. Wire formats, publication checks and expiry are retained.
- Safe readback uses SQLite read-only URI/BEGIN or PostgreSQL repeatable-read,
  read-only transaction without writer lock. The PG schema requires matching
  enrollment/admin/paid/restricted markers; missing paid state cannot silently
  become unrestricted. Native X509 serial TEXT preserves159-bit values.
- Rollback leaves proofs usable; commit ACK loss requires readback/new proof and
  does not authorize replay. Actual PG backend termination after fetch/ACK writes
  verifies rollback, not just injected exceptions. Certificate reuse is retained.

### Qualification and retained failures

Locked control/identity environment with optional HA psycopg3.3.9; PostgreSQL17.11
uses the previously pinned digest
`sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
Private evidence is under `/tmp/fc-control-ha-20261123/`, outside Git. Commands:

```sh
python -m scripts.restricted_postgres_rehearsal --workdir /tmp/fc-control-ha-20261123/restricted-1
python -m pytest -q -ra tests/test_friends_restricted.py tests/test_readiness_receipts.py tests/test_restricted_clock_skew.py tests/test_restricted_gateway_selection.py tests/test_read_readiness_ack.py tests/test_paid_beta_readiness.py tests/test_support_ids.py tests/test_restricted_activation_policy.py tests/test_restricted_activation_http.py tests/test_restricted_correlation.py tests/test_restricted_boundaries.py tests/test_package_restricted_maintenance.py tests/test_paid_canary_crl.py tests/test_package_paid_canary_crl.py tests/test_activated_maintenance.py tests/test_gateway_publication_crypto.py tests/test_readiness_ack_artifacts.py tests/test_friends_http_runtime.py tests/test_referral_rehearsal.py tests/test_enrollment_rehearsal.py tests/test_control_channel.py
```

- `restricted-1/contracts.log`/XML: **163 PASS /0 skips**,123 restricted contracts
  plus40 enrollment,59.19s. Includes concurrent proof use/capacity, invalid/revoked
  grants, node binding, receipt retention, injected write failure/commit ACK loss,
  real backend loss, paid bounds and PG read-only snapshot/schema refusal.
- `restricted-regressions-2.log`: **521 PASS /36 explicit optional skips**,77.50s.
  Includes SQLite consumers, package maintenance/paid CRL, HTTP and owned-lab guards.
  Skips:17 locked-Go cross-language,1 accepted activated-native,1 native checker,
  1 pinned ACK artifact,15 nginx and1 pinned sync. This is not native/release PASS.
- `restricted-root-1.log`: **121 PASS /3 retained-snapshot skips**,3.97s, for
  `tests/test_restricted_maintenance.py`. Runs only in disposable UID0 Docker
  `fc-online-runtime-tests:20261105`, image89598610ee26, network disabled, read-only
  filesystem/source export and private `/run`/`/tmp`; no host root pytest or product
  state mounts. The export includes current uncommitted candidate sources, not
  merely HEAD. `pip check` and source whitespace PASS.
- Earlier `restricted-sqlite-1.log`:215 PASS/17 skips/1 failure. The added fresh clock
  sample exposed the two-value paid-expiry fixture; reject an already-denied first
  paid decision before sampling again. The repaired paid-wait contract passes in
  final regression. Interim `restricted-local-1.log`:99 PASS/60 unavailable-PG skips;
  final real-PG run includes the subsequently added concurrency/lost-ACK/retention cases.
- Broad `restricted-regressions-1.log` is **not PASS**:562 PASS/39 skips/38 failures/
  75 errors.36 failures +49 setup errors came from running root-only ownership tests
  unprivileged; the proper isolated-root run passes.2 failures +26 setup errors in
  readiness adapter packaging lacked required `FC_TEST_GO`/`FC_TEST_HTTP_ARTIFACT`.
  Those28 artifact-dependent cases remain unqualified, not fixed by changing pins
  or replacing accepted artifacts. Five static adapter checks passed, but no full
  adapter package/native acceptance is claimed. Four HA-02C baseline overlay
  failures also remain open; not rerun/reclassified in this slice.

### Crash, restore and rollback boundary

`restricted-1/receipt.json` reports `ISOLATED_RESTRICTED_POSTGRES_PASS`: actual
SIGKILL/restart discards unfinished certificate/ACK/proof updates. A stale
pre-issuance dump is restored only in another disposable container and rejected
against the known committed snapshot. Current dump restores **all16 lab tables /
36 rows** exactly before new writes. Consumed fetch/ACK and revoked-device proofs
are refused; pending fetch/ACK consume once, certificate reuse and paid bound hold,
and support/grants/revokes/paid ledger/audit/readback remain intact. This is a
synthetic known-snapshot comparison, not a production high-watermark service.

Issuer/root keys are generated only in memory and **retained, not restored**, across
the DB recovery test. This does not qualify secret recovery, independent host loss,
WAN partition, full product backup, replication/RPO0, reverse migration, CRL/FIELD
file publication, issuer fencing or failover. Existing file writers still cannot
use PG as a production backend. Raw dumps, credentials and rows remain private.
Owned containers are cleaned; a source push is not a production installation.

Rollback now: stop only the owned lab, preserve evidence; live servers were not
changed and need no restore. After future new canonical writes: fence writers,
preserve current acknowledged state and use qualified current-state/forward recovery
or a separately qualified reverse import. Never replace it with stale SQLite.
NEXT: support sender and remaining writers/CLI, CRL/files/metadata/tombstones,
all-table import/full recovery, replicas and HA-03 fencing before any live cutover.

## HA-02F — restricted grants and audit recovery

Continuation from `57e6c854af2046b7236b1fbb7476227b1b54c064` in the authoritative
metadata worktree/branch. This is a source-only DB slice, not completion of HA-02 or
a restricted serving backend. Console5ce82415 and Android126/catalog9 unchanged.
No production DB/configuration, server service, policy/8/12/120s, consent or key changes.
No SSH/live RU/NL health checks; RU dependence remains. Four prior exact-overlay
package failures remain open and were not rerun/reclassified as PASS here.

Source/tests/docs checkpoint `20129a67e2b6febd9eadd98e2c3425a070ab82a4` ordinarily
pushed to `feature/device-technical-metadata-20261115`; remote SHA independently
matched, source worktree clean after push. Staged16-file scope/private-key-token
marker check,870 local Markdown targets, whitespace and locked `pip check` PASS.
Docker readback finds no remaining containers with the HA enrollment rehearsal label.

Old-main navigation-only handoff `f38e39099112836b7b17ab1fdc72c124695ea0b1` remains
local: ordinary push rejected `non-fast-forward`; independently read remote main is
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`. No force/reset/merge/rebase. Original
unstaged additions remain40 PLAN/66 STATUS/11 private-beta guide/6 recovery guide
lines and the same six untracked historical paths. Only the metadata branch contains
published HA source; this divergent main is not a deployment candidate.

### Change and failure semantics

- Shared `RestrictedAdminTransaction`: active-registration grant/renewal, monotonic
  revision, idempotent revoke, pending audit and guarded audit completion. SQLite
  uses the same path. Explicit PG marker and native grant FK/CHECK; no backend selector.
- Expires/minimum revision must be bounded integers; family nonempty. Clock check
  occurs inside the write transaction; revision cannot wrap/convert to float.
  Device revoke still works at exhausted grant revision. This does not alter TTL policy.
- Grant renewal is not idempotent: lost commit ACK requires revision readback,
  not an automatic second renewal. Concurrent admin/device revokes serialize.
- Audit + revoke roll back together on DB/backend failure. APPLIED→INCOMPLETE is
  allowed for fail-closed compensation after lost APPLIED ACK; INCOMPLETE→APPLIED
  is refused. Existing SQLite FIELD ordering and actual CRL/file path are tested.
- PG FIELD/CRL publication still refuses before file I/O; DB-only success is not
  admission acceptance. Auto-enroll, restricted challenges/certificates/readiness,
  CRL sequence, fenced file reconciliation and support sender remain pending.

### Qualification and recovery

Same locked venv `/tmp/fc-control-ha-20261123/venv`, psycopg/psycopg-binary3.3.9,
PostgreSQL17.11 and pinned image
`postgres@sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
No dependency/version/artifact change. Commands from the authoritative worktree:

```sh
python -m scripts.restricted_admin_postgres_rehearsal --workdir /tmp/fc-control-ha-20261123/admin-2
python -m pytest -q -ra tests/test_friends_access.py tests/test_support_ids.py tests/test_support_http.py tests/test_friends_support_owner.py tests/test_friends_owner.py tests/test_friends_restricted.py tests/test_subscription_http.py tests/test_paid_beta.py tests/test_paid_beta_readiness.py tests/test_read_readiness_ack.py tests/test_referral_rehearsal.py tests/test_enrollment_rehearsal.py tests/test_paid_rehearsal.py
```

- 176 real DB contracts PASS /0 skips in40.68s:70 admin,40 enrollment,66 support.
  Risk-selected suites; unchanged referral/membership PG suites not rerun here.
- 264 consumer/operator/runner checks PASS /4 optional locked-Go skips in10.23s,
  including isolated deterministic operator.pyz and actual SQLite FIELD compensation.
  This is not full transport/platform CI; counts from separate runs are not additive.
- Actual PG backend termination verifies audit/revoke rollback. Whole-container
  SIGKILL/restart then separate current restore pass exact12 synthetic tables/20 rows.
  Consumed proof refused, pending proof consumed once, device/grant revoke and revision
  retained, payment retry duplicate, audit IDs continue. Pending audit survives as
  PENDING and is explicitly closed INCOMPLETE without reopening admission.
- Separate stale pre-revoke restore is refused by comparison with known committed
  lab state. Not full product backup, production reverse migration, replication or RPO0.
- First run `admin-1` passed176 contracts in43.74s but recovery fixture hit the real
  `ANDROID_BASELINE_REQUIRED` guard before crash/restore. Fixture preparation now
  records a valid Support ID observation before payment; requests retain all fields.
  No baseline/proof gate was weakened. Failed evidence is retained, not acceptance.

Raw logs/JUnit/credentials/dumps stay private under `/tmp/fc-control-ha-20261123/admin-1/`
and `admin-2/`, plus `admin-regressions-1.log`. Successful receipt:
`ISOLATED_RESTRICTED_ADMIN_POSTGRES_PASS`, production_writes0, owned cleanup PASS.
Rollback now: stop only this disposable lab; no live restore or gateway restart.
After any future cutover writes: fence writers and recover current state, never old
SQLite. Next within HA-02 remains restricted certificate/readiness writers,
support sender and the remaining HA-02 migration/replication gates; HA-03..05 follow.

## HA-02E — Support ID observation and recovery

Continuation from `23dfd4ba41e6641b14098e6572a418028e3dcef9` in the existing metadata
branch. Scope: Support ID backfill/observation/read models, not all support/admin
writers. Production SQLite, console5ce82415, public Android126/catalog9 and RU
serving membership unchanged. No SSH, server restart, deployment, client release,
new OS/GeoIP collection, consent change or fresh RU/NL health claim.

Source/tests/docs checkpoint `ed6a664ffe6f377caf37af173b68a0cecca3e418` ordinarily
pushed to `feature/device-technical-metadata-20261115`; independent remote SHA
matched. Staged16-file scope, credential/private-key-marker scan,868 Markdown link
targets, whitespace and locked-environment `pip check` PASS. No marked rehearsal
containers remain; source worktree was clean after the implementation push.

Old-main navigation-only handoff `6b211c9f0c0f1236e97445fe2709f2d7453efdf5` stays
local: its ordinary push was rejected `non-fast-forward`. Remote main remains
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`. No forced update, reset, merge or rebase.
Original unstaged additions remain40 PLAN/66 STATUS/11 private-beta guide/6 recovery
guide lines, with the same untracked historical files. Only the metadata branch is
published HA source; this old main is not a deployment candidate.

### Implementation and failure semantics

- Shared `SupportTransaction` serves backfill/request/inventory/lookup. Explicit
  synthetic PG purpose/version guard refuses missing/mismatched marker; no automatic
  DDL, production DSN or mixed-backend fallback. SQLite schema remains compatible.
- Request proof consumption and version observation commit together. Missing alias
  does not allocate during delivery. UPDATE/backend failure preserves the unused
  proof and previous observation. Retry before TTL can succeed after recovery;
  after commit, a fresh proof returns the same ID rather than replaying an old proof.
- Backfill and returned counts share one transaction; preserve aliases, bindings,
  revoked rows and32-attempt collision bounds. Failure midway rolls back all IDs
  and observations. Readiness never infers platform or overwrites newer request data.
- Explicit receipt-ordering parity: NULL timestamps last, correlation tie-break.
  Non-object JSON and missing/negative seen timestamps no longer count as observations.
  A malformed latest ACK does not select an older READY. Existing lookup/admission
  semantics are unchanged, including expired-grant eligibility in all-activated mode.
- PG FIELD mutation is refused before any file open. Restricted grants/readiness
  rows in this lab are read-side fixtures, not migrated grant/audit/CRL/file writers.
  Existing SQLite operator remains usable. Support sender/technical-metadata and
  remaining canonical writers are not included in this checkpoint.

### Qualification and reproducibility

Same locked environment, psycopg/psycopg-binary3.3.9 and pinned PostgreSQL17.11;
no dependency or public-version change. From the authoritative source worktree:

```sh
python -m scripts.support_postgres_rehearsal --workdir /tmp/fc-control-ha-20261123/support-1
python -m pytest -q -ra tests/test_friends_access.py tests/test_referrals.py tests/test_friends_client.py tests/test_friends_http_runtime.py tests/test_support_ids.py tests/test_support_http.py tests/test_friends_support_owner.py tests/test_friends_owner.py tests/test_friends_restricted.py tests/test_friends_chat.py tests/test_gateway_routing.py tests/test_gateway_selection.py tests/test_online_diagnostics.py tests/test_technical_metadata.py tests/test_subscription_http.py tests/test_paid_beta.py tests/test_paid_beta_readiness.py tests/test_read_readiness_ack.py tests/test_support_collector.py tests/test_enrollment_rehearsal.py tests/test_paid_rehearsal.py tests/test_referral_rehearsal.py
python -m pytest -q tests/test_support_ids.py::test_operator_artifact_is_reproducible_and_isolated
```

- 155 DB contracts PASS /0 skips in54.05s:66 support +40 enrollment +49 paid.
  This is risk-selected, not a cumulative total of all previous stages. Existing
  membership/referral PG contracts were not rerun for unchanged implementations.
- 443 consumer/runner checks PASS /21 optional skips in44.21s:16 real nginx,
  1 pinned sync archive,4 locked Go checks require their explicit environments.
  No skipped check counts as PASS or platform/full-release qualification.
- The existing reproducible operator artifact test was then expanded: `python -I`
  executes real `.pyz` backfill/inventory/lookup against a private synthetic SQLite
  registry. Expanded test1 PASS in2.33s (overlaps the443 selection, not444 distinct
  tests). Alias/app version are retained, no device identity appears in safe output.
- Actual PostgreSQL SIGKILL/restart with open uncommitted UPDATEs passes; current
  dump restores exactly12 nonempty lab tables/19 rows into a separate owned container.
  Counts:5 challenges,2 support IDs,2 devices,2 invites,1 audit,3 purpose markers,
  1 paid event,1 subscription,1 restricted grant fixture,1 readiness fixture.
  Confirmed alias/version/proof/revoke/payment state survives; uncommitted version999
  and proof consumption disappear. Pending proof works once, stale readiness cannot
  downgrade, duplicate payment stays duplicate, restored audit sequence advances.
- A real pre-observation dump is restored separately and refused by exact comparison
  with the known committed fixture. This is not a production freshness detector,
  replica/RPO0 proof, full product backup or reverse import after new writes.
- Preliminary SQLite pass49/35 skips; real runner requires zero skipped contracts.
  Private evidence: `/tmp/fc-control-ha-20261123/support-1/`,
  `support-sqlite-1.log`, `support-regressions-1.log`, `support-operator-1.log`.
  Password/env/dump/log/raw receipt and synthetic IDs stay outside Git.
- Prior four confirmed historical exact-overlay failures remain an open deployment
  gate; no old pins changed or packaging requalification claimed by operator smoke.

Rollback now: stop only ownership-checked disposable containers; live state has not
changed. Do not restore old production SQLite. Next: restricted/admin DB writers,
support sender and remaining canonical writers, metadata/tombstones/files, full
import/recovery and replication; HA-03 file/receiver fencing, HA-04 endpoints/clients
and HA-05 guarded cutover remain mandatory. No claim that RU dependency is removed.

## HA-02D — referral transactions and recovery

Continues from `1171b9dcd8a5369e2c8355e65ec480991c30d9eb` on the existing metadata
branch. This is the independent referral writer in the support/admin/referral
group; support/admin is not silently marked complete. No deployment, production
SQL/file writes, secret rotation, endpoint change or fresh server-health claim.
Console5ce82415, Android126/catalog9 and required RU serving node remain unchanged.

Source/tests/docs checkpoint `22caaf6c4d9fa0167f8e8b93d1cad64971c9a019` ordinarily
pushed to `feature/device-technical-metadata-20261115`; independent remote SHA
matches. Staged14-file scope, private-key/credential-marker scan,866 Markdown
targets, whitespace and locked-environment `pip check` PASS. No marked rehearsal
containers remained after the final run. The source worktree was clean after push.
Final contracts181/0 in99.07s; final consumer/runner selection379/21 in37.01s.

Old-main navigation-only handoff `ae71ca10e4488eb95115035d633bc0d2e17cd844` is
retained locally. Its ordinary push was rejected `non-fast-forward`; remote main
remains `cb47bf230c6795cf21f4e6948253f49aa5377ed0`. No force, merge, rebase or reset.
Pre-existing unstaged additions remain exactly40 PLAN,66 STATUS,11 private-beta
guide and6 recovery-guide lines, plus the same untracked historical files. The
metadata branch is the published source; the old main is not deployable HA runtime.

### Changes and retry contract

- `access.py` adds optional caller-owned transaction participation to the existing
  proof completion algorithm; ordinary callers retain signature verification before
  opening the transaction. `referrals.py` uses one shared SQLite/PG algorithm.
- Issue proof consumption, missing Support ID allocation and link write are one
  transaction. Claim invitation and request ledger are one transaction. Existing
  enrollment/revoke serialization also protects pool500/daily20; no lock timeout
  increase, process-global Python mutex or second canonical writer.
- Explicit synthetic PG schema has purpose/version, native FK/unique constraints
  and daily index. It is not a production DB selector or automatic SQLite import.
- Deliberate validation tightening: a request ID replay with a different sponsor
  token or inconsistent reconstructed invitation hash is rejected. Existing valid
  response shape, URL, code derivation and independent child-grant semantics stay.
- Failure before commit rolls back proof/link or invitation/claim together. A lost
  committed response does not authorize a new request or old backup: replay exact
  token/request ID with the original secret. Consumed issue proof needs a fresh
  proof, returning the existing link. No production secret is read or exported.

### Qualification

Environment: existing locked control/identity/provisioning/messenger environment,
optional HA lock psycopg/psycopg-binary3.3.9, PostgreSQL17.11 image digest unchanged.
No new package or public version. Commands run from the authoritative worktree:

```sh
python -m scripts.referral_postgres_rehearsal --workdir /tmp/fc-control-ha-20261123/referrals-2
python -m pytest -q -ra tests/test_friends_access.py tests/test_referrals.py tests/test_friends_client.py tests/test_friends_http_runtime.py tests/test_support_ids.py tests/test_support_http.py tests/test_friends_support_owner.py tests/test_friends_owner.py tests/test_friends_restricted.py tests/test_friends_chat.py tests/test_gateway_routing.py tests/test_gateway_selection.py tests/test_online_diagnostics.py tests/test_technical_metadata.py tests/test_subscription_http.py tests/test_paid_beta.py tests/test_enrollment_rehearsal.py tests/test_paid_rehearsal.py tests/test_referral_rehearsal.py
```

- 181 DB contracts PASS /0 skips:50 referral,40 enrollment,49 paid/subscription,
  42 membership. Independent connections race at actual500/20 boundaries; same
  request replay consumes one slot, same proof issues once; revoke/claim serialize.
  Failure after each write and actual backend termination roll back both records.
- 379 consumer/runner checks PASS /21 optional skips:16 real nginx,1 pinned sync
  archive,4 locked Go compatibility checks require their explicit environments.
  Not a platform/full-release PASS; no skipped contract counted as PostgreSQL PASS.
- Actual source-container SIGKILL/restart preserves current referral state exactly;
  uncommitted invite/claim disappear. Current dump restores to a fresh owned
  container:9 nonempty tables/18 rows, including3 claims,4 invitations,2 devices,
  2 support IDs,3 challenges,1 link,1 audit and2 purpose markers. Old pre-claim
  restore is refused, not promoted to authority. Activated invitation remains
  activated, pending child invitation activates after restore, consumed proofs and
  revocation remain enforced. This is not full product recovery or replication.
- Earlier SQLite-only pass:38 PASS /26 real-PG skips. First full run `referrals-1`
  passed181 contracts/recovery; first consumer run379/21. Final repeat follows the
  smaller `Access.complete(transaction=...)` implementation; intermediate evidence
  is retained rather than relabelled as final bytes.
- Private evidence stays outside Git under `/tmp/fc-control-ha-20261123/`:
  `referrals-{1,2}/` (credentials, dumps, logs, JUnit, receipt),
  `referrals-sqlite-1.log`, `referrals-regressions-{1,2}.log`.
- HA-02C's four independently reproduced historical exact-overlay failures remain
  open; those old builders were not rerun or weakened here. New deployment packaging
  and all production gates still apply. No production acceptance claimed.

Rollback now: stop only ownership-checked disposable containers; do not restore any
product DB. No server state changed. Production reverse import remains unimplemented
and blocks cutover after new writes. Next: support/admin and remaining canonical
writers/files/metadata, full shadow import/recovery, strict synchronous replication,
then HA-03 fencing, HA-04 client/API failover and HA-05 cutover.

## HA-02C — first-payment node preparation and failure consistency

Continuation from `eeb11ba7fb8e95c2d0cad300b71359417f97f77b` on the same metadata
branch. The selected scope is synthetic transport-membership transaction parity,
not live migration, service recovery, client release or provider move. Latest
known installed console5ce82415 and Android126/catalog9 remain unchanged; no fresh
RU/NL health assertion. Production still uses the accepted SQLite/runtime bytes.

Source/tests/docs checkpoint `0ed728f06acdb131ba17869e6d57a1122451e58e` ordinarily
pushed to `feature/device-technical-metadata-20261115`; exact remote SHA matched.
Staged source/doc scope, secret-marker scan, Markdown targets, whitespace and
locked-environment `pip check` PASS; final Docker readback finds no marked rehearsal
containers. No private artifacts were staged. Root navigation commit
`c62d63a2798898e2c605daafc70a50eda5605fe6` remains local: ordinary main push rejected
`non-fast-forward`, remote main still `cb47bf230c6795cf21f4e6948253f49aa5377ed0`.
Root's original40/66/11/6-line edits and untracked work are preserved; no force,
rebase, merge or accidental source deployment from that old checkout.

### Implementation and safety boundary

- `transport_membership.prepare_nodes` shares the first-payment protocol between
  SQLite's existing private command-map wrapper and explicit lab PostgreSQL exchange.
  All command entries validate before contact. The complete three-node set, payload
  token, single-device binding, pre-commit preparation and12s subprocess bound remain.
- ACK validation now rejects duplicate JSON keys, non-UTF8/non-bytes, oversized
  replies, bool/float schema and unexpected/mismatched fields. It does not retry a
  failed node or assume commit from a missing response. Existing node8s operation,
  watchdog12s and paid lease120s are unchanged; noncohort retains its separate policy.
- Native disposable schema version2 has purpose `membership-required`. First payment
  refuses a missing exchange; version1/no-transports refuses a configured exchange
  instead of claiming that preparation ran. There is no production DSN, environment/
  HTTP/CLI switch, automatic migration or alternate writer. Constructor injection
  carries the same exchange through the existing enrollment/paid transaction.
- Rollback never removes already-durable target fences. On partial prepare/ACK loss
  or transaction failure, canonical ledger/subscription remain unchanged; prepared
  target nodes deny across restart, timeout and newer noncohort snapshots. Other
  noncohort/foreign entries remain. Exact retry completes preparation and one commit;
  a committed replay skips all node calls. Terminal revoke is not undone.
- All three nodes, including RU, are still required for first cohort admission.
  Excluding an unavailable node needs a separately qualified serving-set quarantine/
  fencing protocol, not a smaller quorum silently introduced here. No HA-03 epoch
  receiver fencing, compensation/unprepare or production reverse import is supplied.

### Verification

- Final real PostgreSQL17.11/psycopg3.3.9 runner: **131 contracts PASS /0 skipped**
  in56.32s (40 enrollment +49 paid/subscription +42 membership). Membership uses real
  `Gateway` state files, locks, atomic writes/fsync and algorithms with simulated
  kernel/service/network executors; it is not three live servers or WAN acceptance.
- Lost ACK after durable prepare on each node, malformed ACKs, readback failure,
  last-step DB rollback, concurrent duplicate payment, pre-commit invisibility,
  stale snapshots, expired leases and terminal revoke/restart pass. A real owned
  PostgreSQL backend is terminated after every node ACK and uncommitted ledger/
  subscription writes: no payment survives, node denies do, exact retry succeeds.
- The unchanged PostgreSQL5s idle-in-transaction timeout terminates a delayed
  preparation after the first node; no subsequent node contact or payment occurs.
  Target deny survives and exact retry works. This explicitly exposes a lab versus
  WAN deadline limitation; the5s timeout is **not** increased to hide it.
- Inherited SIGKILL/restart, stale-backup refusal and exact current nine-table/
  twelve-row restore pass; restored proof/ledger/revoke/triggers/audit sequence hold.
  Additionally, a real pg_dump/pg_restore of a fresh membership-required schema
  refuses first payment without its exchange and preserves every row. This only
  qualifies the marker/no-fallback guard, not production node+DB backup consistency.
- Receipt `/tmp/fc-control-ha-20261123/membership-3/receipt.json` records
  `ISOLATED_PAID_POSTGRES_PASS`, `SYNTHETIC_CONTRACTS_ONLY`,
  `REFUSES_MISSING_EXCHANGE`, zero production writes and owned-container cleanup.
  Logs, source capsule, credentials, dumps and raw synthetic state stay outside Git.
- Broader changed-risk suite: **389 PASS /16 skipped /4 FAIL** in48.07s, including
  payment CLI/HTTP/readiness/release policy, registry backup, policy packaging,
  transport enforcement/membership/budgets/lifecycle/application/HTTP, subscription,
  packaged HTTP, HA shadow and runner safety. The16 skips are15 configured real-nginx
  gates and1 pinned sync-archive interoperability gate. This is not a green full suite.

### Historical package blocker and retained attempts

Commands used from the source worktree with the existing dedicated locked venv
(`/tmp/fc-control-ha-20261123/venv/bin/python`), not system or production Python:

```sh
python -m scripts.paid_postgres_rehearsal --workdir /tmp/fc-control-ha-20261123/membership-3
python -m pytest -q -ra \
  tests/test_paid_beta.py tests/test_paid_beta_cli.py tests/test_paid_beta_http.py \
  tests/test_paid_beta_readiness.py tests/test_paid_release_policy.py \
  tests/test_paid_registry_backup.py tests/test_paid_policy_package.py \
  tests/test_transport_membership.py tests/test_transport_enforcement.py \
  tests/test_transport_budget.py tests/test_transport_command_budget.py \
  tests/test_transport_lifecycle.py tests/test_transport_application_regressions.py \
  tests/test_transport_package.py tests/test_transport_http.py \
  tests/test_subscription_http.py tests/test_friends_http_runtime.py \
  tests/test_control_ha_shadow.py tests/test_enrollment_rehearsal.py tests/test_paid_rehearsal.py
```

The recorded workdir already exists: use a fresh private `/tmp` path for a new
rehearsal. The second command intentionally retains the four failures below;
do not remove them from the result or call this a green release suite.

All four failures are `tests/test_transport_package.py`: closed overlay/tamper,
exact RU diagnostic overlay, PR15 lifecycle and v2 node-forward package. They fail
with `UNRELATED_PAID_DELTA` or `POLICY_CHANGE_FORBIDDEN`: strict historical packagers
do not accept HA-02B's current paid/policy source as an old exact overlay. No guard,
historical hash, installer, archive or public release was changed to hide the failure.

Verified baseline reproduction from a separate source capsule at exact
`eeb11ba7fb8e95c2d0cad300b71359417f97f77b` produces the **same4 failures /2 passes**.
The working directory/import roots and paid/policy/membership bytes were checked
against that commit; the initial invocation from the current worktree is not used
as baseline proof. Evidence: `membership-baseline-packages-verified.log`. This is
not a new HA-02C regression, but it remains a deployment/package gate; a separately
reviewed closed HA runtime is required rather than weakening old overlay pins.

First SQLite-focused run:55 PASS /22 PostgreSQL skips (not PostgreSQL acceptance).
First real runner:130 PASS and recovery PASS. The extended run:130 PASS /1 failure
because the timeout fixture expected generic `OperationalError`, while psycopg
correctly raises `IdleInTransactionSessionTimeout` (different exception family).
The test now expects that exact server error, retaining the5s timeout and all deny/
rollback assertions; final131 cases and restores pass. Failed attempts remain in
`membership-{1,2,3}/`, `membership-sqlite-1.log`, `membership-regressions.log` and
the baseline logs under `/tmp/fc-control-ha-20261123/`.

### Next and rollback

Next HA-02 slice: remaining canonical support/admin/referral writers, followed by
metadata/tombstones/files, full import/backup and PostgreSQL/Patroni replication.
Production membership scheduling/wiring and new runtime package qualification stay
open. HA-03 receiver fencing, HA-04 API/client failover and HA-05 guarded cutover
remain mandatory. No copied SQLite becomes a second writer.

Current rollback stops only disposable tests; production needs no restore. After
future acknowledged writes, fence writers and preserve the current state before
forward recovery or qualified reverse import. Do not restore old SQL/node caches,
clear `prepared` or automatically extend a payment to make recovery appear green.

## HA-02B — paid ledger, subscription and recovery checkpoint

Owner continuation explicitly prioritizes rollback on failure. This is a source
checkpoint on the existing metadata branch, **not** production deployment or
completion of HA-02. No release/version/catalog change. Rollout remains blocked
on remaining writers, full import/recovery, strict replication and HA-03..05 gates.

Source/tests/docs `a62b5b2e3ef58598a062e19289c2c06642c3af78` ordinarily pushed to
`feature/device-technical-metadata-20261115`; independent remote SHA matched.
Final staged scope/private-key marker scan, local documentation targets and
whitespace checks PASS; locked environment `pip check` PASS. Final runner-only
rerun13 PASS. No marked rehearsal containers remain after the final readback.
Root navigation checkpoint `e95ddcdb5a2da556557403b781076218d97af0d1` remains local:
ordinary main push rejected `non-fast-forward`; remote main is still
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`. No force/rebase/merge. Root's existing
40/66/11/6-line documentation edits and untracked work are preserved exactly;
the verified metadata branch is the published source, not that old main.

- `paid_beta.py` adds semantic paid operations without duplicating admission,
  payment/release validation or event state transitions. SQLite stays the default;
  its first-payment transport preparation remains mandatory when configured.
  Native `paid_postgres.py` is an explicit synthetic-only/no-transports schema,
  with immutable ledger, cohort10, binding and terminal-revoke triggers.
- Personal subscription proof consumption and paid projection now share the
  enrollment transaction. A projection savepoint preserves consumed-proof behavior
  on missing/corrupt schema or SQL failure without committing a PostgreSQL aborted
  transaction. No noncohort/allow response replaces a failed read. A failed/unknown
  outer commit is not asserted successful; no alternate SQLite write is attempted.
- All three transport projections share semantic reads; wire shape, entitlement
  boundaries, paid/noncohort separation and8/12/120s remain unchanged. No transport
  receiver, legacy archive pin or production/client dependency lock is changed.
- **89 contracts PASS /0 skipped** on real PostgreSQL17.11/psycopg3.3.9 and SQLite:
  40 enrollment +49 paid/subscription/parity cases. Concurrent duplicate/event-ID
  conflict/last-cohort-slot/proof races, rollback after ledger append, exact ledger
  and all-node decision parity, latest Android observation/mesh revoke, identity
  revoke, natural grace expiry, coherent concurrent reads, marker guards, native
  update/delete/truncate refusal and direct-writer trigger concurrency pass.
- **366 regression/runner checks PASS /20 optional skips** in47.97s, covering
  Access/support, paid policy/membership/enforcement, HA shadow/backup, packaged
  HTTP, restricted/chat/referral/subscription, technical metadata/GeoIP and runners.
  The skipped15 real-nginx,1 pinned sync archive and4 locked-Go compatibility gates
  are unchanged and not represented as release acceptance. Runner checks include
  six inherited isolation/ownership/driver tests and seven restore-comparison tests.
- Final rehearsal: `python -m scripts.paid_postgres_rehearsal --workdir
  /tmp/fc-control-ha-20261123/paid-3` using the existing dedicated locked venv and
  pinned official image from HA-02A. Source, stale-restore and current-restore
  containers use disposable private state and ownership-checked cleanup; no SSH,
  live export, server restart or product write.
- Real SIGKILL/restart retains committed payment/grace/revoke and consumed proof,
  drops an uncommitted ledger/invitation write and returns the original payment
  for same-ID/payload retry. An older backup taken **before those payments** is
  restored only into another disposable container and explicitly REFUSED against
  current state; accepting it would lose acknowledged events/revocation.
- Latest dump restores every row in all nine lab tables:2 challenges,1 device,
  1 invite,1 Support ID,1 audit row,3 events,1 subscription,2 schema-marker rows
  (12 total). Payment replay adds nothing, proof replay is refused, revoked state
  persists, restored immutability triggers reject updates and audit sequence
  advances. This is not the full product schema, metadata/file/CRL restore,
  reverse migration, host-loss durability or replicated RPO0.
- Before cutover, rollback means stopping only the lab/shadow; unchanged production
  needs no restore. After new-store writes, fence writers, preserve acknowledged
  current state and use verified forward recovery or a separately qualified reverse
  import. Old SQLite restoration is not a safe shortcut. No production reverse
  importer exists yet; do not switch writers assuming this lab provides one.

Failed attempts retained outside Git: the first SQLite regression caught malformed
empty event schema returning200 instead of503 after a generic `SELECT *`; explicit
column reads restore fail-closed behavior (162 passed /1 failed before correction).
The first real run passed78 cases and failed one fixture expecting a binding error
on an already terminal-revoked row, where SQLite correctly rejected revocation
first. The binding fixture now uses an active row; the terminal test remains
separate. The corrected run passed89; the final run additionally verified restored
triggers and audit sequence. No production failure/restore occurred.

Private evidence: `/tmp/fc-control-ha-20261123/paid-{1,2,3}/`,
`paid-sqlite-first.log`, `paid-regressions.log` and each run's log. Dumps, credentials,
JUnit, SQL rows and raw test evidence remain local; only safe sources/tests/docs
are published. Read [remaining writer gates and recovery rules](../control-ha-storage.md).

## HA-02A — enrollment repository checkpoint, not complete HA-02

- Source/tests/docs checkpoint `9d1219d89b462e3ba87daa6e1e560dc1f238ce8b`
  ordinarily pushed to `feature/device-technical-metadata-20261115`; exact remote
  branch SHA independently matched. Staged scope/private-key markers, local
  documentation links and whitespace checks pass; no build output/private state.
- Old-main navigation checkpoint `a22efc6e3f1be5a813ac6469b9f80ce6c5543463`
  remains local. First push failed transient DNS; one ordinary retry was rejected
  `non-fast-forward`. Remote main remains `cb47bf230c6795cf21f4e6948253f49aa5377ed0`.
  No force/rebase/merge; the pre-existing40/66/11/6-line documentation changes and
  untracked root work remain untouched. Use the published feature-branch source.
- Shared `Access` domain logic now uses semantic transaction operations for invite,
  challenge, activation, status and device revocation. SQLite remains the default;
  existing API signatures, proof/binding validation,TTL100s and challenge limit8
  remain. The boundary stays in `access.py` to preserve closed artifact inventories;
  historical archive pins/overlays are not rewritten.
- `enrollment_postgres.py` is explicit synthetic-only injection, loopback/fixed
  disposable DB+role, versioned schema marker, native SQL and transactional locking.
  Legacy `db()` paths refuse instead of becoming mixed PostgreSQL/SQLite writers.
  No production DSN/HTTP switch or server configuration is added.
- Real PostgreSQL17.11 official image
  `postgres@sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`;
  psycopg/psycopg-binary3.3.9 pinned in an optional HA lockfile. Existing production
  and client dependency locks remain unchanged. Dependency notices updated.
- **40 SQLite/PostgreSQL contracts PASS /0 skipped** in the real runner. Includes
  eight competing independent connections spending one proof, two identities
  spending one invitation,16 simultaneous challenge requests respecting limit8,
  status replay, revoked/expired/wrong-device rejection, rollback after the last
  activation step, Support ID collision, lost-response status recovery, bounded
  lock refusal, schema mismatch and no silent SQLite fallback.
- Actual source-container SIGKILL/restart preserves committed identity/TCP ID,
  revocation and unused invitation, refuses consumed proof, drops an uncommitted
  insert and accepts a fresh reconnect with the same identity. fsync,
  full_page_writes and synchronous_commit are checked on; this is single-instance
  crash evidence, **not** host-loss RPO0, replication or hardware power-loss proof.
- Binary pg_dump restores into a second fresh owned container in one transaction.
  All five enrollment tables are nonempty and compare exactly:3 invites,2 devices,
  3 challenges,2 Support IDs,1 audit row. Restored identity sequence advances.
  This does not qualify paid/metadata/CRL backup or a production SQLite import.
- **353 consumer tests PASS /20 skipped**: Access/support, paid ledger/policy,
  old HA shadow/backup, packaged HTTP, restricted/chat/referral/subscription,
  technical metadata and GeoIP. Skips:15 explicitly configured real-nginx gates,
  1 pinned sync-archive interoperability gate,4 locked-Go compatibility cases.
  No claim of a complete release gate. A separate HTTP/runner rerun passes25
  tests /16 optional skips;5 of these are new runner safety tests. Final runner-only
  suite passes6 tests, adding refusal of a mismatched driver before container start.
- Initial unit run:165 PASS,19 PostgreSQL skips,1 fixture failure because the
  identity is already base64 text; corrected the fixture. First real PostgreSQL
  run:42 PASS,1 test used the deliberately refused legacy `db()` interface;
  replaced that assertion with the semantic transaction check, not a fallback.
  First broader collection lacked LXMF; installed the existing provisioning and
  messenger lockfiles in the same isolated `/tmp` venv. `pip check` passes.
- Private evidence under `/tmp/fc-control-ha-20261123/enrollment-1..5` retained;
  final `enrollment-5` passes contracts/crash/restore and removes both owned
  containers/anonymous volumes. Dumps, credentials, synthetic keys and raw logs
  are not committed. The runner is pinned to the local Docker socket and checks
  ownership before destructive cleanup; no existing panel container is touched.
- SIGTERM during a real pytest child: parent exits143, test child is gone and
  the owned container is absent. An earlier cleanup assertion expected capitalized
  Docker wording; independent readback confirmed removal, then the corrected
  case-insensitive exact-error check passed. No runtime cleanup change was needed.

[Exact writer inventory/remaining work](../control-ha-storage.md) ·
[Reproducible runner](../../deploy/control-ha/README.md#ha-02a-isolated-postgresql-enrollment).

## HA-01 implementation and validation

- `control/friends/control_shadow.py`: one read-only SQLite snapshot, schema/all
  table HMACs and existing paid-policy projections for RU/NL1/NL2. Dedicated
  synthetic HMAC key; no raw rows or identities in the manifest, no write/migration.
- `control/friends/control_quorum.py`: loopback-only verified mTLS, linearizable
  reads, revision CAS, replay/conflict/expiry rejection and lost-ACK readback.
  It is not a product leader lease or a replication adapter for application data.
- `scripts/control_ha_rehearsal.py`: three real etcd children, disposable CA,
  synthetic SQLite and owned-process cleanup. No production config or credential.
- etcd3.7.4 official archive SHA256
  `a0d47d07d081c12611fe69dc81a16ae8dd758401c0fe3a83d508823a1dac558e`;
  binary SHA256 `6fcf4a133e477a2340c59a287461b4988f0ed5c7559ff4750a8695ac41ae5a2a`.
  Source/version pins are committed, downloaded binaries are not.
- **61 focused tests PASS**: shadow, paid-registry backup, transport enforcement,
  membership. Dependencies installed from control/identity lockfiles in an isolated
  venv; `pip check` PASS. No full historical/platform release suite claimed.
- First unit pass exposed an incorrect synthetic key length; fixed without
  relaxing32-byte validation. First live rehearsal failed strict X.509 verification
  (missing Authority Key Identifier). Added AKI/SKI and KeyUsage to disposable
  certificates; did not disable verification, mTLS or downgrade TLS.
- Two subsequent real rehearsals PASS. Final run adds direct per-member readback
  after recovery, disallowing fallback to a healthy neighbour as acceptance proof.
  Leader SIGKILL → next confirmed shadow publication **1.766s** on this laptop;
  earlier less-strict rehearsal1.611s. Neither is a production availability promise.
- Minority linearizable read refuses; publication refuses before attempting a
  write. Confirmed manifest survives two crashed members and their return. Stale
  CAS is refused, unauthenticated TLS clients rejected. Only own children stopped.
- Separate real SIGTERM check stops the runner during startup: exit143, all three
  owned child PIDs gone; final61-test rerun PASS. This does not promise SIGKILL cleanup.
- Private local evidence: `/tmp/fc-control-ha-20261123/rehearsal-1`,
  `tls-diagnostic`, `rehearsal-2`, `rehearsal-3`. These contain only synthetic state
  and ephemeral test credentials; retain locally, never commit raw directories.

[Reproducible commands and limits](../../deploy/control-ha/README.md).

## Remaining work — not a production HA acceptance

HA-02 must finish **all** canonical writers beyond the qualified enrollment,
paid/subscription, membership, referral and Support ID slices: restricted/admin and support sender, separate metadata
tombstones, remaining writers/CLI and filesystem coordination. Full import, PostgreSQL replication and
Patroni/RPO0 gates are not implemented by this checkpoint.
Then HA-03 receiver-enforced fencing, HA-04 multi-endpoint clients and HA-05 live
shadow/cutover and real failure acceptance. No alternate API is serving users;
RU remains a shared dependency. No provider replacement or live outage test done.

## Rollback

Only source and disposable local rehearsal state exist at this checkpoint.
Stop rehearsal children; keep private logs outside Git. Do not restore a product
DB or replace deployed archives to undo this work.
