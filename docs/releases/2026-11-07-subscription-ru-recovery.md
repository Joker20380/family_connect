# SUBSCRIPTION-RU-RECOVERY — bounded forward recovery

## Provenance and incident

Base remote main2077c271d43d3bbe09f76e70934947bcc3fb51c6; separate recovery branch.
Original v2 origin299b4845 and archive75832d0c remain immutable. The prior
[enablement incident receipt](https://github.com/Joker20380/family_connect/pull/6#issuecomment-6711874492)
supersedes the earlier positive154-second sample. RU watchdog12s fired at
19:04:02UTC7 November; watcher stopped and ordinary AWG/TCP masked. Durable state,
HTTP/operator and NL lease refresh were retained. New paid operations remain paused
until the recovery completion gate. No real ledger write or phone operation is needed.

Production evidence establishes watchdog termination with an Xray child, not the exact
preceding phase. Retained journals cannot establish whether lock contention or a query
dominated that interval. Source reproduction establishes127 engine queries for63
canonical records, repeated unchanged AWG writes, blocking flock and no total budget.
This is a demonstrated failure class, not an invented retrospective root-cause timestamp.

## Correction

- Single monotonic8s operation covers serialization waits, planning, commands,
  restart/preflight, readback and deadline convergence. Child groups are killed/reaped
  on timeout; systemd failure cleanup replaces pending restart with stop.
- Exact Xray26.3.27 full inbounduser response and AWG allowed-ips snapshots replace
  per-device queries. Unchanged63-record sweep needs two engine queries, no actuation.
  Changed AWG set gets final readback; unknown entries are preserved, binding conflicts
  and query errors remain failures. Empty successful protobuf response is distinguished
  from failed query/malformed data using the actual installed engine contract.
- Natural deadline crossing replans under the same budget. Finite leases, durable
  membership, terminal deny, noncohort semantics and paid108/119 remain unchanged.
- Packaged privileged preflight runs under real production base-unit context; only
  preflight gains root, Xray retains fc-friends/NoNewPrivileges/ProtectSystem=strict.
- Metrics contain phase durations and completed-progress gaps, no personal identifiers.
  Watchdog12s, lease120s and central30s profile are not increased.
- Strict complete per-node archive pins allow observable mixed-version rollout.
  No panel layout, users, HMAC, volumes or canonical subscription logic changes.

## Packaging and gates

`scripts/package_transport_node_recovery.py` accepts only exact installed v2 node and
gateway hashes. It changes node/gateway/preflight, preserves policy bytes and records
full nested inventory plus source SHA/dirty status. HTTP/operator/reconciler are not
part of this forward package; their previously installed hashes/PID must stay unchanged.
The final committed-byte rebuild must equal qualified payload bytes. Historical
artifacts are never overwritten or assigned the new source SHA.

Addressed unit gates cover63-record no-op query count, bounded lock wait, killed child
descendants/no late write, strict full-query parsing, existing expiry/revision/membership
contracts, exact historical package inputs/tamper, and strict per-node pins. Real native
qualification uses63 synthetic identities,19/48/5 registrations with overlap, one paid
member, actual systemd units/preflight, fc-friends UID/sandbox and bounded resources.
It includes overlapping watcher/reconcile/register, open traffic, expiry/offline paid
cutoff/noncohort, enrollment ACK/replay, application failure/recovery and ≥360s steady
window. Intentional fault scenarios respect the actual five-starts/120s rate limit;
the limit is not removed to accelerate qualification.

Final exact-byte qualification, maxima, hosted CI/review/merge and operational receipts
are attached to the recovery PR and retained privately. A source checkpoint is not a
claim of recovery. Delivery gate: RU≥360s stable, then sequential NL on the same payload,
protected-data equality, all-node current readback/panel and compatible CLI restored.

## Operational boundaries

Accepted collateral TCP reconnect on real composition change remains. Duplicate state
and renewal without set changes do not restart Xray. Local watchdog/state/engine failure
can stop both ordinary transports; ordinary center loss preserves noncohort. Existing
MESH cert/CRL boundary, control HTTPS and baseline108/119/replay remain separate.
Eight seconds is a healthy-OS operation budget, not a guarantee against uninterruptible
kernel/storage failure; systemd/watchdog remains independent fail-closed containment.

RU forward recovery preserves state/prepared/deny/mappings; it never reruns initial
preparation or manually rewrites deadlines. The central full enrollment set remains
three nodes while only the target's application is temporarily fenced. If recovery
fails, keep affected transports stopped/masked; no ledger rollback or old gateway bypass.
Final receipt records outage interval, actual process/units/hashes, two successive
cycles and lease renewal, and separates set readback from actual user traffic.
No user authenticated request or production end-to-end traffic is PASS without an
actual authorized test. G4/renewal, APK119, cold provisioning and adjacent tasks are excluded.
