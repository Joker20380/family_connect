# 24 November 2026 — HA-02 writer boundary

Selected task: CONTROL-HA-20261123 / HA-02. This completes the bounded observation
needed to specify the next coherent-capture operation; it does **not** complete that
operation or add a fifth acceptance gate. Replication stays PASS; current approval,
coherent capture and full recovery remain partial. The accepted NL2 recovery is not rerun.

## Actual observation

`scripts/control_ha_writer_preflight.py` is a stdlib-only, read-only extension of the
installed census. It examines explicit known accounts, default authorized_keys, account
crontabs, `/etc/crontab` and five system cron directories, Family Connect unit cgroups,
and kernel lock records for the two existing gateway lock inodes. Commands, keys, cron
names and process arguments are hashed, not exported. No user database rows are read.
No service stop/start/freeze, signal, lock acquisition, config edit, package install,
source deployment or new snapshot occurs. A120s process alarm bounds the observation;
individual subprocesses and input sizes have tighter limits. It is not a barrier lease.

| Host | UTC observation | Units | Cgroup process records | Result |
| --- | --- | ---: | ---: | --- |
| RU | 14:39:35–14:39:37 | 32 | 6 | chat-sync service activating→inactive and timer running→waiting; other observed units unchanged |
| NL1 | 14:38:01–14:38:02 | 9 | 9 | all active; before/after observations equal |
| NL2 | 14:38:02–14:38:03 | 5 | 6 | all active; before/after observations equal |

All explicit-account crontabs are absent. System cron literal-path inspection completes
without refused entries; no Family Connect root-path matches are found. This does not
exclude indirect wrappers, user systemd units, nondefault SSH keys/ForceCommand policy,
other accounts or root administrative processes. Root authorized_keys still contains
entries without an explicit per-key forced command; this is not a determination of
effective SSH policy. NL2's restricted account has a forced command outside the literal
root-path matcher. Those cases remain coverage gaps, not silently omitted writers.

All sampled application/registration lock records are empty. The concurrent RU chat-sync
completion is direct evidence that such an observation is not global quiescence.
Unit cgroups also do not contain every forced-SSH command or externally dispatched
Docker process. `capture_permitted=false` and `all_writers_qualified=false` are unconditional
observation scope, including empty or unchanged results. A refused observation is explicit;
it never becomes an empty successful sample. `services_changed=false` means the tool
performed no mutation, not that normal production timers stopped changing state.

RU transport warning: AWG is failed (`timeout`), TCP inactive, and paid-reconcile failed
(`exit-code`) at the start and end. These match the earlier05:32 census; this action
did not cause or repair them. HTTP candidate, paid-watch and peer-worker are active.
Do not start previously failed/inactive services as a capture rollback.

At14:42:43–14:42:44 a separate bounded read-only inspection observes the exact existing
RU worker/pilot-gateway and OWNER console/PostgreSQL/system-publisher containers. All five
are running, not restarting, with zero container restart counts. The pilot gateway reports
24 ExecIDs. Follow-up Docker Unix-socket **GET-only** inspection at14:43:59UTC finds all24
retained executions `Running=false`, none disappeared, with unchanged ID sets. ExecIDs
are not a count of running operations. Neither this sample nor the worker's single current
process closes future admission or rules out a completed operation between samples.

The first RU connection using only the named Ed25519 identity is refused (`publickey`),
before any remote observation. The established agent-backed SSH invocation used by the
earlier capture succeeds with the same strict host pin. Authentication was not weakened;
the failed attempt is preserved and is not evidence that RU is unreachable.

## Minimum boundary contract

The next implementation is one coordinated maintenance boundary, not another component
backup or a generic `systemctl freeze` recipe. Existing authorization for bounded RU
management-write capture remains; current NL scope does not permit service deployment or
working-service changes. A missing installed participation mechanism must be reported,
not silently installed under read-only qualification permission.

| Surface | Required proof before capture | Unsafe substitute |
| --- | --- | --- |
| Friends HTTP | close new mutating admission, then acknowledge completion of every already admitted operation including external side effects | stopping/freezing threads while a DB/file/SSH operation is halfway through |
| RU timers, operator/CLI and SSH entrypoints | bind effective source/config/account dispatchers to the boundary; stop new dispatch and drain admitted commands; explicitly coordinate manual deployment/admin work | stop only HTTP, infer no writers from an empty cron/lock sample, or assume unknown wrappers participate |
| Legacy worker/Docker gateway | stop admitting cycles; prove already dispatched gateway work settled independently of the client process and retain pending queue/idempotency state | assume a timed-out `docker exec` client killed the server-side command, or treat retained ExecIDs as running jobs |
| OWNER PG/synthetic/publisher | inhibit participating mutation/dispatch while establishing the PG transaction snapshot and synthetic/file point under the same boundary | combine independently timed pg_dump and seed.lock snapshots |
| RU/NL1/NL2 files and receivers | establish a provable overlapping capture interval after drain; keep deny enforcement/watchdogs operating and use the existing short local deadlines | hold gateway registration/application locks for an unbounded fleet SSH round trip |

Review anchors: Friends HTTP currently uses a four-request semaphore in
`deploy/friends/access-api.py`, not a fleet admission/drain protocol. The legacy worker
handles TERM by waiting for its bounded cycle (`deploy/product-peer-worker/worker.py`);
the configured70s Docker stop and90s unit stop are not a short capture lock.
`control/product/gateway_adapter.py` has3s Docker-client timeouts, not remote cancellation
acknowledgements. `control/friends/transport_gateway.py` must retain its8s operation /
12s watchdog safety boundary. These are source-design constraints, not newly attested
runtime-loaded byte equivalence; retained source pins and effective installed bindings
must be checked before any corresponding live operation.

Mandatory qualification: deny new admission while draining; preserve queued requests and
idempotency IDs; refuse busy/unknown participants and nonoverlapping captures; test coordinator
loss, timeout and rollback without renewing expired grants or disabling deny enforcement.
No indefinite maintenance flag or source-side busy-wait is acceptable. An independent
deadline must release only this operation's own boundary even if SSH disappears. A short
lock deadline alone does not settle operations that already crossed an external dispatcher.

After this boundary is qualified, perform one coherent capture, obtain approval of that
exact checkpoint independently of the generating tool, qualify off-laptop key/access
custody, and run the final combined OWNER/canonical/fleet post-ACK and stale-copy recovery.
These are still the same three partial HA-02 gates. No HA-03 fencing/cutover is selected.

## Validation, evidence and rollback

62 focused tests PASS:
`python -m pytest -q tests/test_control_ha_writer_preflight.py tests/test_control_ha_installed_census.py`.
Coverage includes bounded reads, symlink refusal, cron errors versus absence, scoped cgroup
traversal, process-ID reuse, redaction, lock waiters/inode matching, disappearing processes,
and refusal to authorize capture from empty/unchanged observations. No historical full
suite, production deployment, application release/version or public artifact change is claimed.
Four documentation files /1014 local links and whitespace checks PASS. External URLs are
listed by the documentation checker, not fetched or qualified as live public artifacts.

Private evidence and all three one-off observation drivers are retained under
`~/.local/share/family-connect/control-ha/20261124-writer-preflight-01/` (0700/0600).
Source pins are retained separately from result hashes. The preflight source SHA256 is
`730e411e147b182aa81eab9dbb4cde2163dfa13bb9d919a1db23437f500d005a`.
RU/NL1/NL2 report hashes respectively:

- `b340e42c2cd7561bbb76167ac0a76c737b502891951448d6fe134518b5c590ec`
- `72abb4a67ceb096aaa158b84aa1c0cccec9aa56e98d2f23284028c46a6be1c87`
- `e28f8c3f3f7a242e15023803170cde47d215e1fbd93e4cdb374dddf99c01b8d0`

Docker exec readback hash:
`aa7213ac54135cad2686e9c986ac1247f4d1c817e73e3d0772bb31fcd2bfb4a0`.
These checksums bind evidence; they are not independent checkpoint approval or recovery keys.

Rollback for this observation is process exit only: no daemon, installed file, held lock,
service state or timer setting was changed, and all observation processes have returned.
Preserve existing ciphertext custody and all private evidence. Any future live boundary
must separately record prestate and restore only that prestate; never use product DB
restoration, enabling old failed services, or disabling watchdogs as its rollback.
