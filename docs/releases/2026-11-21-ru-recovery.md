# 21 November 2026 — RU recurrence: TCP query timeout

## Scope and result

The owner reports RU services stopped again, continuing the restoration request.
Only RU watcher/AWG/TCP are recovered, without replacing installed bytes or changing
timeouts, timers, restart policy, identities or entitlement data. Server-validation
checks PASS. Actual owner-device tunneled traffic and permanent prevention remain
OPEN. No client version, public installer, catalog, release tag or PR45 deployment.
Times are UTC; RU systemd timestamps are MSK (UTC+3).

## New failure, not yesterday's fsync event

- First failure at14:53:23.359800 belongs to the watcher invocation restored on
  20 November. Reason `COMMAND_TIMEOUT`, mode `watch`, phase `engine_query`,
  family `tcp-query`, `TimeoutExpired`. Total8.352705s, operation budget8s.
- First AWG query starts3.204519s into the operation and takes1.288361s. TCP query
  starts4.493706s in, with3.506311s remaining, and times out after3.858899s.
  Two/eight major faults are recorded for these respective calls. There is no
  decision-state fsync call in this attempt's receipt. The cause of the initial
  delay and TCP query timeout remains unknown; page faults alone do not prove it.
- Unit readback places TCP exit at14:53:25 and AWG timeout exit at14:53:30. At17:14
  both have PID0; watcher has238 retries, paid reconciliation failed. A retrying
  watcher is not transport recovery. Fresh first-failure SHA256:
  `e0c1f7fce5bc146bc565a9396a6afe93e730c98afb18a9bbc85c59e7de7b3786`.
- Shared HTTP and both NL AWG/TCP/MESH are active at entry. Current MESH transaction
  is `COMMITTED`, first cause null; scheduled renewal and directory sync succeed.
  RU provides shared control, so current NL availability is not independence from
  configuration delivery or renewed authorization on RU.
- The old bounded observer stopped on20 November; its unchanged trace is not
  evidence of a21 November kernel stack. Do not reuse the old fsync attribution.

## Guarded restoration and verification

1. **17:17:51:** runtime/command-map/failure pins PASS; new27-table registry backup,
   integrity/foreign-key checks, isolated restore fingerprints and all-node paid
   projections PASS. Off-host AES-GCM backup and decrypt roundtrip PASS. No live
   database restore, profile replacement or user/invitation creation.
2. **17:18:52:** RU-only command fence with unchanged NL entries; drain reconciler,
   stop watcher/AWG/TCP and require MainPID/ControlPID0, no transport jobs/handlers.
   Preserve68 decision records and20 peers, bindings, deny state and configs.
3. **17:18:53–54:** hard-link the original failure as
   `transport-failure.20261121-145323.preserved.json`, re-arm only under stopped
   guards, start the three RU units, restore the exact original command map.
   HTTP and peer-worker retain their original PIDs/invocations. NRestarts0.
4. **17:19:35 and17:20:49:** strict original-start continuity PASS, exact20 AWG and
   20 TCP entries, all68 revisions applied; attempt ages1.918/0.758s. All eight
   protected tables, transport identities/membership/terms/prepared state,
   generation2 files, command map and effective units remain unchanged.
5. **17:19:36–40:** all six public TLS challenge/configuration requests return200.
   RU and both Amsterdam configuration signatures verify against the client anchor
   using the existing test identity; identity keys unchanged. Not a tunneled
   DNS/HTTPS test or physical-client acceptance.
6. **17:20:51–53:** NL service invocations remain unchanged from entry and ordinary
   attempts are fresh `applied`. Paid reconciliation succeeds17:20:23–26 and its
   timer is active. Renewal succeeds17:16:52–17:17:03; directory sync is sampled
   during a normal running oneshot, not classified as failed. Panel imports
   17:20:10/12/15 show RU AWG/TCP/HTTP and both NL AWG/TCP/MESH active, transport `ok`.
7. **17:21:38–40:** third strict recovery audit PASS, same original process
   invocations,20/20 sets,68 applied revisions, all eight protected tables unchanged,
   attempt age0.782s. Directory sync17:21:23–28 and reconciliation17:21:31–34 finish
   successfully. No `journalctl`/`ionice` processes remain; I/O PSI avg10 falls to
   some5.39/full3.52. No new active failure latch. This is short-term verification.

## Bounded diagnosis and limits

After restoration, one low-priority journal query for14:52:55–14:54:00 is bounded
to8s with a1s kill grace. It exits124 with no usable manager events; not a clean
journal or an initiating-watchdog finding. No repeated journal scan is performed.
Three small `/proc` samples at17:19:48–50 show about63.29% CPU I/O-wait; final I/O
PSI avg10 some62.84/full49.23. Available RAM is about1.1GiB and disk at entry has
6.74GB available (78% used). These follow the diagnostic read, which may itself
contribute load; do not assert these are measurements of the14:53 outage or proof
of a provider-host/storage fault. They establish a current responsiveness risk.

## Runtime, evidence and stop path

Installed RU transport remains legacy
`125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c`.
Gateway, reconciler, HTTP and effective units match the unchanged pinned artifacts
in the [20 November report](2026-11-20-ru-recovery.md#exact-runtime-and-evidence).
No package rollback is needed because no package was deployed.

Fresh private evidence and encrypted backup/key are retained under ignored
`state-client-build/ops-incident-20261121/` and `state-client-build/ops-recovery-20261121/`;
remote backup/state is in `/opt/apps/family_connect/private-ru-recovery-20261121-r1`.
No raw private evidence, database, keys or command map enters Git.

If a new failure occurs, preserve its receipt, fence only RU, drain and stop the
RU trio safely. Do not restore old registry/cache, overwrite earlier failures,
stop NL/HTTP generically, bypass durability or increase deadlines as a substitute
for a qualified fix. Owner reconnect/real traffic, root-cause attribution and a
qualified permanent change remain OPEN; short successful checks are not sustained
stability acceptance. No automatic monitoring/restart schedule is installed.

The existing `main` was already divergent and the preceding ordinary push was
rejected. This task uses an isolated documentation checkpoint, preserving older
uncommitted work; no force push, reset or unrelated merge. The new push outcome
is reported separately and is not an operational recovery gate.
