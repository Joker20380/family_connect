# SUBSCRIPTION-ENFORCEMENT-FIX — 7 November 2026

## Scope and provenance

Separate worktree from actual remote main `1cbe8fbf0de1924e9326125e1932078b5b1f56ee`.
PR1–4 remain closed. The PR4 artifact
`d6e5dd679dec671dd9ec992f23057cd869580aa71ec34f8ad3c19f5f1eb89f3c` is **not eligible
for enablement**; its files/receipts are retained privately. No new production
restrictions are enabled. No real payment, cohort, identity, period, phone/APK,
G4/renewal or cold-provisioning mutation. APK119 retains its original source
`b2a37fe989294018ab08060bdebfa46d741d11d5`; no Android production input changes.
Final source SHA/CI/review/merge receipts belong in the task PR, without a cosmetic
post-CI documentation head. Private paths, bindings and raw evidence are not published.

## Corrected execution contract

- `application.lock` serializes registration/reconciliation/watcher through the entire
  operation. `registration.lock` protects durable state/config planning and readback,
  but is released before synchronous TCP restart. Exact installed ExecStartPre uses
  only the latter lock; it cannot wait on its parent application's lock.
- Planning freezes one expected access set. Actual AWG/TCP sets are verified against
  it. A deadline crossing causes bounded replanning, including when preflight itself
  removes an expired user. Genuine mismatches remain failures, not unconditional PASS.
  Durable decisions precede application/ACK; partial restart failure remains fail-closed.
- Canonical paid_beta remains the sole subscription authority. First payment, after
  validation and inside the existing write transaction, prepares every serving node.
  ACK means a persisted per-device fence plus actual denial/readback, not a payment.
  Only all-node ACK permits canonical insertion/commit. Unavailable nodes or lost ACK
  roll back canonical writes; the target's already prepared fences remain across
  restart and stale noncohort messages. Exact replay returns the canonical receipt
  before eligibility/preparation as before. Existing cohort is not enrolled twice.
  First enrollment can hold the SQLite writer for up to36s of node waits (12s each)
  plus local work; other writes may temporarily wait/fail, not bypass the fence.
- Noncohort has no paid lease timeout, but known identity deny and prepared/paid
  membership cannot revert to ordinary noncohort. Paid leases retain wall/monotonic/
  boot bounds. Renewed expired access can return; terminal revoke cannot.
- Real TCP membership changes restart the shared Xray service to terminate existing
  streams, including multiplexed sessions. Other TCP users briefly reconnect. No-op
  reconciliation and renewal without a membership change do not restart it.

## Proof boundaries and reproduction

`tests/test_transport_application_regressions.py` fails twice on the unmodified base:
child preflight cannot acquire the lock, and deadline crossing raises
`ENGINE_READBACK_MISMATCH`. Both failures are preserved in private baseline receipts.
The corrected tests include renewal after crossing and no extra restart.

`scripts/test_paid_transport_systemd.py --kit PRIVATE_KIT --report PRIVATE_RECEIPT`
executes the built node archive and exact gateway/units/drop-ins with **real PID1
systemd255**, actual systemctl/ExecStartPre, AWG and Xray26.3.27. Three disposable
nodes use private PID/mount/network/cgroup namespaces, no host mounts/socket/ports,
bounded CPU/memory; synthetic canonical registry and the built paid operator only.
TLS verifies certificate/name and nonce/egress. No engine restart shim is used.
The fixture HTTPS origin now handshakes in per-connection threads rather than
blocking its accept loop on REALITY camouflage connections; no TLS verification or
product timeout is relaxed. Earlier fixture failures are retained, not counted PASS.

Final isolated run: **PASS**, built kit2, actual systemd/preflight on all three nodes;
all owned test containers/networks cleaned up. Positive TLS/nonce probes retain
verification; after a full AWG engine restart the fixture allows20s connection/25s
total to cover its handshake/SYN retransmission, not to extend product execution or
paid deadlines. The earlier8s restoration probe failed and is retained as such.

| Final-kit check | Result / measured evidence |
| --- | --- |
| Real TCP set change/restart/ExecStartPre while watcher runs | PASS, no deadlock |
| TCP-before-deadline/AWG-after deterministic crossing; restored allow | PASS, no false engine mismatch |
| Natural expiry of already open streams | AWG3.496s; TCP2.184s; mux0.182s after deadline |
| Central outage / managed lease cutoff | AWG3.720s; TCP2.565s; mux0.624s; ordinary noncohort still passes TLS/nonce |
| Unavailable node, lost preparation ACK, retry | PASS; no canonical payment until all-node ACK |
| Pending preparation across real service restart and stale noncohort | PASS; target remains fenced |
| Renewal + duplicate | PASS; no additional restart when set unchanged |
| Concurrent registration/reconciliation/watcher | PASS |
| Exact injected ExecStartPre failure and forward recovery | PASS; failure does not yield false ACK |
| Retained profile after engine restart + renewed allow | PASS, complete positive probe11.361s |
| Terminal revoke + real service restart | PASS, forbidden access stays absent; noncohort works |

Scoped canonical/HTTP/packaging/regression tests: **147 PASS**. Built Django image,
real isolated PostgreSQL subscription/application tests: **40 PASS**, nine existing
static/cache-directory warnings. Public-docs all gate and diff whitespace: PASS.
No historical runtime matrices or benchmarks are relabelled as final-kit results.

## Corrected artifacts and local panel

New private `paid-transport-v2.tar.gz`:
`75832d0c71dcef2e085dcc95a250dc6da2e62400b3a2b992ec4ea8161116d97c`.
Full per-file/per-archive-member inventory:
`0fc06beff6bafcdc85c9caf65e179ca1134718ae009bc5d7a631440079b9430f`.
[Sanitized artifact hashes](evidence/subscription-enforcement-fix-kit.json) bind the
HTTP/operator/reconciler/node bytes tested; source commit provenance accompanies the
private inventory and PR. Eight private delivery/rollback shell blocks pass `bash -n`;
none were executed on production. The accepted paid108/119 CLI stays installed there.

Local `http://127.0.0.1:8765/subscriptions/` updated only for schema2 observations
(unmanaged noncohort has no paid TTL; pending membership is distinct). Historical
schema1 remains readable. Existing styling, filters, roles, secrets/HMAC, PostgreSQL,
volumes, immutable payment/release/cohort records and synthetic identity registry
are preserved by before/after fingerprints and private backup. Initial updated image:
`d3529a01d60bcfba968e56eba2713627cfeee0c1096b11d376278277a256a6d5`.
Authenticated HTTP200/no-store readback and desktop1440/mobile390 screenshots pass;
no horizontal overflow. Screenshots and raw observations stay private.

Fresh observation **7 November16:45:29UTC**, attempt16:45:31UTC:63 devices,
1 active cohort member,62 noncohort; all three nodes explicitly **not installed**.
Read-only16:45:08UTC mapping: RU19/19, Amsterdam1 48/48, Amsterdam2 5/5 peer mappings;
cohort bindings1/1/0, currently denied0/0/0. This is dated deployment impact, not a
new payment or a claim that production restriction works. Recheck before enablement.

### Final technical-label correction

PR5 merged as `3683fed3506e32b5795fd93601a78fdfe5e73199` after six applicable
hosted runs passed on299b4845. Remote main and identical merged tree were verified.
Post-merge authenticated readback exposed a hardcoded transport “Schema1” label.
The panel-only follow-up records actual schema in append-only import-attempt audit
metadata and displays it beside the corresponding successful observation. Historical
records without schema remain unchanged and are labelled unknown, not guessed.
No new migration, subscription authority, archive change or native requalification.

Built image subscription/application tests: **41 PASS**, ten existing static/cache
warnings. Current installed local image:
`6093606ad14d38737f28522074296e7cee916e629c20975a1d645d8b971d15d7`.
Fresh17:14:39UTC canonical readback and all three actual schema2 transport observations
pass authenticated HTTP200/no-store;63 devices/1 active cohort, enforcement remains
not installed. Original protected fingerprints and retained screenshot history match.
Final follow-up hosted checks/merge are recorded in its PR, without a cosmetic head.
The prepared tar, full inventory, committed source299b4845 and native evidence above
remain the exact delivery artifacts; they are not relabelled with a UI-only source SHA.

## Recommended profile and operational impact

`paid-transports-v2`: central cycle every30s after completion (40s +5s stop budget),
node tick2s/watchdog12s/stop5s, maximum managed lease120s, skew5s, known natural
deadline budget25s, central loss managed cutoff150s, canonical managed change200s
including a preceding in-flight snapshot. These are conservative operating budgets,
not a measured production SLA. Noncohort does **not** have these paid expiry budgets.
First cohort entry is fenced before commit, not eventually discovered after payment.

Ordinary central outage preserves unrelated noncohort. Local watcher crash/timeout,
corrupt state/bindings or genuine application failure still stop both ordinary engines
through BindsTo/stop_all, including their noncohort users. This is an explicit local
integrity failure, not the normal central-outage path. Forward recovery starts the
watcher and both engines and requires fresh verified readback.

MESH paid predicate and existing cert/CRL path are unchanged: prior materials/sessions
may remain until the existing minimum certificate/CRL/authority expiry (up to4h in the
existing supply). No automatic paid CRL publication or new renewal/publisher path.

## Delivery and rollback boundary

The private per-node plan retains the observed HTTP baseline
`4bcbd7ed0dcc756965f5eb60aa340c8d5d638513a0af64ca93b50affce86b7fb`
and gateway `8e536367a391661f003d0725afc13f69c45a9e43bb1763b61fd21ce0b998035a`.
Packaging rejects unrelated API/paid changes: remove the exact configuration guard
and first-enrollment hook and the old serving bytes must match. Bootstrap/renewal
are not replaced from arbitrary HEAD. HTTP/operator/reconciler share the same policy.

At a future approved enablement: verify fresh source/binding/native inventory, take
the prescribed consistent nonempty backup, pause operator writes, stage matching
operator plus private complete-node commands before enabling central configuration.
Install node code/preflight/watch only with ordinary engines stopped, retain mapping,
initialize verified canonical state, require all-node readback and control HTTPS.
Preserve panel HMAC; move source pins together with their actual deployment.

Rollback never restores old ledger or deletes durable membership/deny state.
Stop new paid operations before API/operator rollback. Keep node fencing; if node
code itself must roll back, stop and mask ordinary AWG/TCP, retain denial evidence,
and recover via verified forward fix before unmasking. Do not boot an unfenced
historical gateway or restore an old TCP config containing forbidden users.

The only next decision after green checks and normal merge is whether to deliver
this corrected prepared variant. Production enablement is not part of this task.
