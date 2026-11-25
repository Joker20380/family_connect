# HA-02 — short OWNER publication database boundary

Date:25 November2026. Task:CONTROL-HA-20261123 / HA-02. This is a source and bounded working
qualification checkpoint, **not a release, full OWNER drain, capture acceptance or HA-03 cutover**.
Current queue: [PLAN](../PLAN.md); state: [STATUS](../STATUS.md).

## Boundary and dependencies

The [native publication settlement rehearsal](2026-11-25-control-ha-publication-settlement.md)
already shows that an HTTP ACK or dead sender does not prove a PostgreSQL COMMIT finished.
This change adds a separate, brief database boundary rather than treating process exit as proof.
It reuses the qualified [publisher dispatcher hold](2026-11-25-control-ha-dispatcher-hold.md)
and [console ingress lease](2026-11-25-control-ha-console-ingress.md); it does not replace their
rollback or qualify the remaining external effects. The
[stopped replacement/revert executor](2026-11-25-control-ha-owner-replacement.md) is unchanged.

- `scripts/control_ha_publication_fence.py`: a fresh, exclusively owned autocommit connection,
  fixed OWNER endpoint/database in the CLI, PostgreSQL17 only. No DML, schema changes, COMMIT,
  foreign backend cancellation, product marker deletion or backup restore.
- `EXCLUSIVE MODE NOWAIT` on `public.console_auditrecord` and `public.console_systemmessage`
  conflicts with both existing update transactions and the `ROW SHARE` lock held by
  `SELECT FOR UPDATE` before publication HTTP. Ordinary SELECT remains possible. A weaker
  SHARE lock would not fence that pre-HTTP operation. Busy tables refuse without waiting.
- Checks bind exact persistent public relations/OIDs, backend identity, active transaction and
  both granted locks. Unknown/unrecognized publication states refuse; aggregate counts only.
- PostgreSQL17 `transaction_timeout=2000ms` bounds the entire transaction independently of the
  controller, including repeated SELECT activity. Idle-in-transaction timeout also2000ms;
  statement timeout200ms, lock timeout1ms. Library deadlines must be integer200..5000ms;
  the composed working probe requires2000ms. No timeout fallback for older PostgreSQL.
- `scripts/control_ha_owner_publication_probe.py`: pins the original three healthy containers,
  records private full prestates, holds the publisher scheduler for at most12 seconds, then
  checks that no publishing child is active before closing new console TCP admission for5 seconds.
  Only no child or the exact bound `sleep 10` child is accepted; existing children are not killed.
  A verified sleep child may naturally exit while its parent is stopped, so it is not required
  to remain alive after the database probe. Both independent guards must still validate.
- The probe creates a nonprivileged `console` user Docker exec, with source and target identity
  checked before start; intent/exec ID are persisted first. It runs the standalone fence source
  transiently, validates bounded sanitized output and explicit ROLLBACK, then releases both guards
  and compares full effective configuration/runtime. It never starts/stops/replaces a workload.

Neither a successful database boundary nor zero unknown rows proves a remote HTTP handler,
support transport or unregistered manual writer has settled. Receipts explicitly retain
`external_settlement_proven=false` and `capture_permitted=false`; the composed receipt also
keeps support settlement and manual admission false. No data capture is performed.

## Validation

**226 tests PASS,0 skipped;49 new cases.** Python3.14.4/pytest9.1.1. Root checks use the
control/identity environment with psycopg3.3.9; panel checks use Django5.2.18/psycopg3.3.6 and
all17 installed panel lockfile pins match. Docker29.1.3/API1.52; pinned PostgreSQL17.11 image
`sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.

Root selection,143 PASS (33 new probe cases +63 ingress +47 dispatcher):

```sh
python -m pytest -q tests/test_control_ha_owner_publication_probe.py tests/test_control_ha_ingress.py tests/test_control_ha_dispatcher_hold.py
```

Panel selection,83 PASS (16 new fence cases +3 extended settlement +44 messages +20 admission),
from `control_plane/`, against an isolated disposable pinned PostgreSQL with synthetic credentials:

```sh
python -m pytest -q tests/test_publication_fence.py tests/test_publication_settlement.py tests/test_system_messages.py tests/test_capture_admission.py
```

The native PostgreSQL cases verify conflicting old work is not canceled; ordinary reads remain
possible; row state survives; unknown state refuses; wrong DB/nonfresh transaction/bad deadlines
refuse; repeated SELECT cannot renew the total deadline. Real child SIGSTOP and SIGKILL leave
the server independently releasing locks/backend, and resumed stale checks fail. Three existing
native HTTPS + deferred-FK COMMIT cases now also verify the fence refuses before backend
settlement, including after sender death. A later database-only PASS still cannot authorize capture.
The root tests include Docker exec scope/stream validation, recorded identity before start,
timeouts/unconfirmed results, busy publisher refusal before ingress, and both-guard abort cleanup.

The first panel run had80 PASS/3 FAIL: two tests did not filter virtual-XID ExclusiveLock from
relation locks, and one expected generic OperationalError rather than TransactionTimeout.
Corrected test expectations; original failed evidence retained. The final panel run has83 PASS.

## Working result and rollback

At **12:31:37.763708–12:31:37.773484UTC**, the working publication database locks are held for
about9.8ms under the composed admission guards. Explicit ROLLBACK is acknowledged and the
dedicated connection closes. This is a short database observation, not a continuous capture
interval or external settlement proof. Aggregate status shape is recognized with no unknowns.

All three original containers remain healthy, with identical IDs/PIDs/start times, effective
configs/mounts/network policies and0 restarts. Console `/health/` returns200 before/after;
publisher scheduler resumes; both guard helpers exit0; all six ingress helpers are absent;
both collector timers remain active. Original image pins are unchanged:

| Role | Image SHA256 |
| --- | --- |
| console | `5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a` |
| system_publisher | `50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab` |
| postgres | `18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73` |

The first composed working attempt at12:25UTC aborted **before any database exec was created
or dispatched**. Its exact refusal reason was not retained by that runner revision; do not
attribute it to PostgreSQL or call it PASS. Independent readback verified original runtime/config,
health, resumed scheduler and all five helpers absent before the new attempt. The runner now
retains a sanitized abort stage/reason and checks publisher idle immediately after the hold,
before ingress closure. That improvement does not retroactively establish the first failure cause.

Invoke only after checking current pins, scopes and independent guards; use a fresh empty0700
private journal and the already qualified ingress tool image, on the implementation branch:

```sh
python -m scripts.control_ha_owner_publication_probe --journal /absolute/private/journal --ingress-image sha256:QUALIFIED_IMAGE
```

Normal rollback is ROLLBACK on the probe's own connection, exact ingress-table removal, and
dispatcher resume/reaping through the existing guards. Server transaction expiry independently
bounds a successfully started transaction to2 seconds. Existing ingress expiry bounds each
inserted element to5 seconds and dispatcher rescue bounds its hold to12 seconds.
**These limits start at their respective operation boundaries, not at a possibly lost host request.**
An unresolved Docker exec/helper dispatch can start later: keep every intent/ID and reconcile
actual state before retry, capture, replacement or declaring rollback complete. Do not repeat
an exec start, clear unknown markers, kill publication children, flush firewall rules, terminate
foreign database sessions or restore product DB backups to get a clean result.

No durable image/config installation, server policy change, remote RU/NL operation, product
version bump, public installer/catalog or invitation-page change. Source push is not deployment.

## Evidence and unchanged exit gates

Private root locator: `/tmp/fc-ha-publication-fence-current`; `final/panel.xml`,
`final/unit-qualified.xml` and `final/working-second/` are authoritative. First aborted working
attempt and its explicit reconciliation remain in `final/working/`. Raw effective configs,
credentials, database/user data, exec/helper journals and synthetic run state stay outside Git/CI.
Only safe sources/tests/documentation and these digests are committed:

| Artifact | SHA256 |
| --- | --- |
| Fence source | `67fdf7d4d3f3b919c38b370acc02bf292c72a477e33318ec7f59e25127c17466` |
| Composed probe source | `3b6cd3732b67771f3c42500626dbeea2c4a62ec82719ad9df4b143e579f95340` |
| Panel JUnit | `af6c1fab731ab3c30b1b595b9761f0b7176c010000a33c1ae047dee397a4ede5` |
| Root JUnit | `fb494126d046ab0857ff53e5ae0fbbbddb3d1fe7a738692e37711e8f5e4e76f6` |
| Working composed receipt | `258371c24e2173b2a14343224e62a2d0d0cfe16cdd57e7b1631d42c9783fa082` |
| First abort reconciliation | `defb1be544df424cf2d0e5094679527fa6645c9f27573705c82a9df43eab85f9` |
| Final health/timers/helpers | `29f421274ce59f52f5a99c66ed6f6f5570043556662768a5512e61583ba0d3d8` |

Next: external publication/support/manual settlement, then real gate/runtime attestation and
guarded startup/abort with the already qualified ingress/dispatcher/stopped-replacement components.
Remaining fleet participation, coherent all-writer/all-store capture, independent custody/trust/
approval and final combined current recovery remain. Replication is PASS in isolation; the
same three other HA-02 acceptance gates are partial. No new stage, numerical progress estimate,
HA-03 cutover or automatic RU-independent failover is claimed.
