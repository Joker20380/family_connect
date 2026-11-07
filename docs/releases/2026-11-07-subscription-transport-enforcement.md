# SUBSCRIPTION-TRANSPORT-ENFORCEMENT — 7 November 2026

**Historical receipt; kit withdrawn from enablement by independent review.**
Do not enable archive `d6e5dd679dec671dd9ec992f23057cd869580aa71ec34f8ad3c19f5f1eb89f3c`.
The preserved results below do not prove the combined shipped systemd/preflight path
and do not approve noncohort expiry on controller loss. See the
[corrective task](2026-11-07-subscription-enforcement-fix.md); do not reassign these
measurements to its new artifacts.

## Scope and provenance

Base: remote main `a258e93347ba34fb876cc21f6bcae628e9b6c7b8`, closed PR1–3,
installed `android-paid-108-119-v1`. Separate integration worktree; original dirty
checkout and cold-provisioning work preserved. Normal final-head CI/review/merge
receipts are recorded in the task PR, not a cosmetic post-CI documentation commit.
**Production transport enablement has not occurred.** No paid event, cohort, identity,
period, phone/APK, MESH/G4/renewal or production service mutation in this task.

APK119 remains source `b2a37fe989294018ab08060bdebfa46d741d11d5`, SHA256
`52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d`.
No Android production inputs changed; this is not new Android acceptance.

## Built kit (private, disabled by default)

`scripts/package_paid_transport.py` builds over the **observed** serving HTTP archive
`4bcbd7ed0dcc756965f5eb60aa340c8d5d638513a0af64ca93b50affce86b7fb` and gateway
`8e536367a391661f003d0725afc13f69c45a9e43bb1763b61fd21ce0b998035a`.
It rejects altered baseline inputs or unrelated HTTP changes. Complete before/after
member inventory is retained. HTTP changes are exactly the post-proof configuration
guard plus policy/reconciler modules. Existing paid_beta, bootstrap, renewal and all
other serving members retain their original bytes. Ordinary source packaging also
includes the new policy module. It is not a rollout of an old feature-branch snapshot.

| Artifact | SHA256 |
| --- | --- |
| friends-http.pyz | `4ebb35334e9d4e39a5682c435da9b5585bcf26573c5f825f6636367c0de542f3` |
| paid-reconcile.pyz | `933ca0f967c761266c840da7cbac8999680c0f0df1b03c2cee31766ba9b970be` |
| paid-transport.pyz | `a2e4918b229569c10249350913a30e5a68880b2a0d3d8da647194efd9630eb55` |
| awg-gateway.py | `a90ea908d1da8c44822a30f5d02128a5a11139f5e961e1c8acfcd9aa7e78e855` |
| prepare_paid_transport.py | `935a5c47d069e5414b51cad8ddb46649110c9d3a8decd1c2272747a664e81798` |

The kit includes systemd watch/dependency/TCP-preflight and bounded central timer
templates. Final central unit adds5s stop/control-group kill to the tested40s cycle
budget; native Python/gateway/archive bytes are identical to the native-tested kit.
Exact per-file inventory, deployment paths, commands, source SHA binding and private
receipts accompany the retained kit; no credentials or product databases are in Git.

## Canonical authority and node behavior

One SQLite read transaction first pins its snapshot, then takes one server now.
Missing/damaged paid schema is an error, never noncohort. Identity/invite authorization
and the canonical paid predicate remain independent. Configuration guards run after
proof; own status/subscription/control paths are unaffected. The existing pinned SSH
registration channel carries exact device/WG/TCP decisions, not a new signing scheme.

Nodes fsync intent before actuation, reject old revisions/binding conflicts/terminal
restoration, preserve unknown peers/users and retain registration mapping. Exact replay
does not renew its lease. AWG live peers and TCP persisted users are reconciled and
read back from actual engines. TCP removal uses a **whole Friends TCP service restart**
to terminate old flows/mux. Other TCP users on that node reconnect; this is not a
per-user seamless operation. Partial failure stops both ordinary transports. Watchdog
and BindsTo prevent a crashed/stuck watcher leaving engines indefinitely running.
Reboot invalidates known leases by boot ID; monotonic deadlines bound wall-clock rollback.

## Native isolated evidence

Disposable internal networks, synthetic canonical registry, original supplied profiles,
real AmneziaWG/Xray, verified TLS hostname/certificate and nonce/egress echoes. No
production endpoints/identity/payments. Resources are bounded and removed by exact
task labels. Source fixtures are `pilot/transport_enforcement_fixture.py` and
`scripts/test_paid_transport_native.py`; private full and fault receipts are retained.

Observed production and tested native bytes agree:

- AWG CLI: `906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278`.
- amneziawg-go: `e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f`.
- Xray26.3.27: `4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940`.

| Scenario | Result / actual boundary |
| --- | --- |
| Fresh noncohort, active, grace | PASS: real AWG/TCP TLS/nonce/egress |
| Explicit expire, old issued profile | PASS: denied; unrelated mux user reconnects |
| Already-open AWG/TCP/mux1/mux2 | PASS:2.441/2.011/0.065/0.054s after explicit apply start |
| Natural grace expiry, automatic watcher | PASS:4.056/3.636/1.729/1.663s after deadline |
| Center loss, no new snapshot | PASS:2.934/2.481/0.525/0.520s after120s lease deadline |
| Recovery and renewal after expired | PASS: real profiles work again |
| Terminal revoke/new payment/old allow | PASS: rejected; no restored profile |
| Late real gateway registration | PASS: rejected, durable state unchanged |
| Restart actual gateway after denial | PASS: retained mapping does not restore access |
| Partial TCP restart failure after persistence | PASS: both engines stop; foreign TCP also stops; denial survives restart; forward renewal restores |
| Corrupt cache | PASS: watcher exits/fail-closes engines |
| Duplicate/lost ACK semantics | PASS unit: same intent/revision, no lease extension |
| Control HTTPS after paid expiry | PASS real HTTP handler over isolated verified TLS, fresh challenge/proof; own status/subscription200, wrong hostname rejected |

Real Xray stop/start takes about0.40s in this isolated fixture. It is not a production
restart-duration guarantee. Early cold-REALITY fixture probes hit the old3s connect
budget; verified TLS/nonce assertions stayed intact while the fixture uses8s/20s
positive budgets. Original failed receipts are retained, not relabeled PASS.
Native fixtures substitute only systemctl orchestration with actual bounded child
engine processes; real production systemd watchdog stop timing remains a rollout
readback, not a newly performed production restart.

Additional63-identity native capacity run PASS:3.725s full apply under0.6CPU gateway
limit; natural cutoff2.649/2.124/0.141/0.141s, center-loss cutoff3.149/2.456/0.515/0.527s.
Separate actual **user-systemd transient units**, not production services: SIGSTOP of
the12s-watchdog process stopped both BindsTo dependents in12.223/12.244s. Native
engine behavior and supervisor dependency timing are distinct tests, not a claim
that the production root manager was deliberately crashed or restarted.

## Recommended profile (owner decision still required)

`paid-transports-v1`: central30s after completion,40s cycle+5s stop; node2s tick,
12s watchdog/5s stop;120s maximum lease;5s permitted clock skew. Conservative budgets:
25s after an already-known paid/grace boundary,150s from the last successful snapshot
on center loss,200s for any canonical change including a new cohort during an in-flight
old snapshot. These are designed bounds under functioning OS/systemd, not measured
production SLA. Noncohort still needs no payment, but its cached identity admission
also expires: otherwise an old noncohort snapshot could conceal later enrollment.
**Thus center loss disconnects all known registered AWG/TCP clients, not just cohort.**
This explicit availability/collateral trade-off is part of the single enablement decision.

MESH keeps its existing predicate/material limits. Both serving binaries were read
as `70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6`, matching
the [accepted common capsule](2026-11-04-unified-mesh-stability.md#exact-common-build-and-qualification),
not assumed equal to today's main. At14:49:29UTC the live common certificate/CRL window
was13:27:32–17:27:32UTC. Existing Family session I/O uses the minimum security deadline;
paid revoke itself does not publish a CRL. Already-issued material may therefore last
up to its old4h ceiling, not200s. No historical publisher is wired, no online-renewal/G4
change is made. Faster MESH revocation is an external CRL-publisher policy dependency,
not silently claimed by this AWG/TCP kit.

## Read-only impact and controlled rollout

14:54:08UTC canonical read, mapped against retained per-node inventory: RU19 bindings,
NL1 48, NL2 5; every observed AWG binding maps to canonical WG/TCP identity. Cohort
counts1/1/0, currently denied0/0/0; these are dated observations, not permanent counts
or active-flow counts. All nodes reported NTP synchronized and zero embedded `[Peer]`
stanzas. Unknown bindings must stop preparation, not be deleted. Current entitlement
does not need payment or modification to enable the kit.

Private per-node plan: fresh inventory/fingerprints/nonempty consistent backup;
stage exact checksummed kit; stop only ordinary AWG/TCP, install their fence/units,
initialize from a fresh canonical snapshot; start watch/engines, central bounded
reconciler and guarded API. Preserve actual serving interpreter/ExecStart arguments,
catalogs, identity and MESH services. Confirm all-node ACK/runtime/persisted sets and
control path. Then repin external subscription collector to the new API archive,
preserving HMAC, and require fresh authenticated local readback. Re-evaluate impact
immediately before enablement; stop on any source/mapping/policy drift.

Rollout has a maintenance interruption on each node; Xray changes interrupt all of
that node's TCP users. Code rollback never restores a ledger backup or deletes deny
state. Keep node fences when reverting API; if node code must be reverted, stop/mask
AWG/TCP and leave them stopped until a forward-fix/fresh canonical reconciliation.
Unfenced restart of historical code is not a safe rollback.

## Installed local panel and gates

Local http://127.0.0.1:8765/subscriptions/ updated with image
`sha256:54f4144978b4cfc792b548158b4ee0cd1cdc114ec40ef20b873c2eee0e796c53`.
Existing PostgreSQL/volumes/users/HMAC/env/subscription pin and synthetic registry
retained, with private consistent pg_dump and rollback image. Existing seed_demo
refreshed only50 DeviceProjection.observed_at fields; comparison against the restored
isolated backup confirms every other projection field unchanged. Paid records, release
metadata, cohort, identities and user/group memberships are unchanged.

Fresh authenticated HTTP200/no-store readback15:18:37UTC: server observed15:18:29UTC,
63 devices,1 cohort, serving archive4bcbd7ed unchanged. Each RU/NL1/NL2 observation
reports **not_installed**, not disabled access. This is no production rollout.
226 panel tests, Django check/migration drift checks and50 focused policy/HTTP/package/
collector tests PASS. Browser Chromium157: actual authenticated desktop1440 and390px,
filters/pagination/long details/focus, synthetic empty/active/grace/expired/revoked/
noncohort/stale/collection/import-error states PASS; private screenshots visually
inspected. UI labels distinguish text states, real/demo and latest attempt/data time.
Review regression: a node error with an old server clock remains an error, never
relabelled merely stale; previous successful node data is shown separately. Node
details expose decision/application/lease UTC times, reason and archive provenance.

Hosted applicable checks/review/merge and final source/remote SHA are attached to the
task PR. Production enablement, physical whitelist/COLD_BOOTSTRAP_GAP, Android natural
expiry/identity UI/mixed-network and new physical event tests remain NOT_RUN here.

## Next client release design only

Android119 is not rebuilt. For a later separately authorized client release propose:
one readable state heading + access-until in local time with explicit timezone; separate
last-confirmed server time and offline warning; access-event wording rather than bank
payment claim; expandable event/revision diagnostics; accessible Refresh progress and
screen-reader labels. New events still arrive only on subscription screen open/Refresh;
ordinary app launch may deliver already persisted events, not independently fetch new
payments. No new background transport or adjacent task is started.
