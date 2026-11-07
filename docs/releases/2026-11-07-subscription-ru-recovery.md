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
The Docker CI export explicitly includes the exact2077c271 Git object closure needed
to reconstruct the accepted v2 node. Host-checkout success alone missed this fixture
requirement; restored-export reproduction must retain7fa86e75… and reject tampering.
Existing native/renewal snapshot contracts and owner/interpreter checks remain intact.

Addressed unit gates cover63-record no-op query count, bounded lock wait, killed child
descendants/no late write, strict full-query parsing, existing expiry/revision/membership
contracts, exact historical package inputs/tamper, and strict per-node pins. Real native
qualification uses63 synthetic identities,19/48/5 registrations with overlap, one paid
member, actual systemd units/preflight, fc-friends UID/sandbox and bounded resources.
It includes overlapping watcher/reconcile/register, open traffic, expiry/offline paid
cutoff/noncohort, enrollment ACK/replay, application failure/recovery and ≥360s steady
window. Intentional fault scenarios respect the actual five-starts/120s rate limit;
the limit is not removed to accelerate qualification.

Exact payload source0be45494242d97cd4ebe21e06085f836813d71ae, harnessdeca5618:
real systemd/native **PASS**,374.777s steady window/18 overlapping central cycles;
same actual service PIDs throughout. The later CI fixture correction changes no node
bytes. Native hashes match fresh installed Xray26.3.27/AWG on all three production
nodes. Isolated nodes use0.6CPU/448MiB, versus observed production2CPU/about2GiB.

| Evidence on the exact recovery payload | Measured result |
| --- | --- |
| Maximum successful pass RU / NL1 / NL2 | 0.646 /1.197 /0.106s |
| Maximum useful-progress interval RU / NL1 / NL2 | 2.646 /3.197 /2.106s |
| Natural expiry: AWG / TCP / open mux | 2.318 /2.182 /0.216s after deadline |
| Center-loss cutoff: AWG / TCP / open mux | 4.191 /3.919 /1.971s after finite lease |
| Held lock / slow engine controlled failure | 8.410 /8.475s; exit-code, not watchdog; no late child write |
| Enrollment unavailable/lost ACK/restart/replay, recovery, terminal denial | PASS on synthetic canonical data |

Node archive SHA2564948e888579c42fdb4697b23a10bcb256f76b8de7fe52b8aa618e25bd9b28e4d;
gateway69f32dbfdf0db5f57fb598d58935b5f2b098e53d0c0e2ac24517ad299ced26bf;
recovery tar5f82efd60ac6e027bf1154b8cae364bd3edb0dc444921e30e7f56d7d16d6019c;
full inventoryb1433795ecf837f7b3592fc5312190fb0480e0ef5896a575847937aba3fa1ab5.
These are qualification results, not production recovery or user traffic evidence.
They belong to the first payload, not to the subsequently merged NL1-compatible build.

## Concurrent NL1 change preserved

During CI, main advanced to f30536c7 with the separately authorized NL1 load fix
(source780f0898). Its strict full-set parsers, final post-TCP AWG snapshot, drift and
malformed-input regressions and independent mailbox cap are preserved, not overwritten.
The combined sweep performs three constant-count queries rather than127, with the
same shared8s operation budget and change-only actuation. The mailbox change is not
part of the recovery archive or delivery. A new exact node payload and full native
qualification are required for this merged implementation; prior measurements above
are retained only as historical evidence. Final payload, CI and installed receipts
will be attached to the task PR without a cosmetic documentation-only head.

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
