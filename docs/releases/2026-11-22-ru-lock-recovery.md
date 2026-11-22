# 22 November 2026 — RU evening recurrence: lock deadline

## Scope and result

The owner reports another stop, continuing the RU restoration request. RU
watcher/AWG/TCP are recovered with unchanged runtime, units, deadlines and restart
policy. Server recovery gates PASS; permanent prevention and owner-device tunneled
traffic remain OPEN. No client version, public artifact, catalog, release tag or
PR45 deployment. All times below are UTC; RU systemd displays MSK (UTC+3).

## Fresh failure and impact

- **21 November21:55:08.269231:** first failure is
  `TRANSPORT_OPERATION_DEADLINE`, mode `watch`, phase `lock`, boundary `body`,
  `TimeoutError`, elapsed8.000318s against8s. Stage counts contain only `lock:1`;
  native call list is empty. TCP exits21:55:10, AWG21:55:11. At22:27 watcher retry
  count is54 and reconciliation has failed; a running/retrying watcher does not
  mean VPN engines are serving.
- First-failure SHA256:
  `702a7d79b5967e7478eb83804144c9bf543ec009ed0a5fee654750e700f4b8a7`.
  This is a distinct event from the afternoon TCP-query timeout and prior fsync
  failure. Do not substitute those incidents' causal attribution.
- Installed `apply()` acquires `application.lock` before `apply_serialized()` can
  acquire `registration.lock`; both use nonblocking `flock` polling inside the
  operation deadline. The first-lock-only receipt is consistent with waiting for
  application serialization. `watch()` routes errors through `fail_closed()`,
  which records failure and stops both engines. The historical lock owner and
  underlying cause of the8s wait were not captured; no specific writer, kernel
  stall or provider fault is established.
- Shared HTTP and both NL AWG/TCP/MESH are active at entry. Both NL MESH already
  have NRestarts1 and starts22:11:18/22:11:40, preceding our intervention; no claim
  of uninterrupted whole-night MESH availability. Renewal is `COMMITTED` with
  null first cause. RU still serves shared configuration/control: working NL data
  paths are not independence from RU configuration and authorization services.
- Entry disk availability is7.102GB (77% used). Current memory/pressure samples
  and22:30 absent lock holders cannot reconstruct conditions at21:55. No broad
  journal scan or destructive storage operation is performed.

## Guarded recovery and checks

1. **21 November22:32:44:** runtime, command-map and first-failure pins PASS;
   fresh27-table SQLite backup, integrity/foreign-key checks, isolated restore
   fingerprints and all-node paid projections PASS. Off-host AES-GCM backup and
   decrypt roundtrip PASS. No live DB restore, new identity or profile replacement.
2. **22:34:30:** fence only RU commands, preserve NL entries, drain reconcile and
   stop RU watcher/AWG/TCP; require MainPID/ControlPID0, no jobs or live handlers.
   Preserve68 decision records,20 peers, cached deny state, bindings and configs.
3. **22:34:31–33:** archive the exact original failure by hard link as
   `transport-failure.20261121-215508.preserved.json`, re-arm only under stopped
   guards and start RU trio; restore the exact original command map. HTTP and
   peer-worker are unchanged by recovery. Recovered units have NRestarts0.
4. **23:04:39:** strict30-minute audit PASS: original recovered PIDs/invocations,
   exact20 AWG/20 TCP entries,68 applied revisions, attempt age2.269s. All eight
   protected tables, identities/membership/terms/prepared state, generation2 files,
   effective units and runtime pins remain unchanged. Original failure is archived
   with the expected hash and no new active failure latch exists. HTTP/peer-worker
   continuity passes at this audit, before the later scheduled rotation.
5. **23:04:39–43:** all six public challenge/configuration requests return200;
   configurations for RU and both NL choices verify against the client anchor.
   Existing identity key bytes remain unchanged. This is not tunneled DNS/HTTPS
   or physical-client acceptance.
6. **23:04:44–23:06:14:** low-priority, read-only `/proc/locks` sampling completes
   in90.061s,864 polls at approximately100ms,84 ownership segments. Longest sampled
   segment is0.9334s, owned by the watcher; other segments also show paid reconcile
   owners. No segment reaches1s and no new failure appears. Sampling can miss brief
   releases/reacquisitions and does not identify who held the lock at21:55. The
   sampler exits; no permanent observer or automatic recovery is installed.
7. **22 November01:06:41–47:** RU trio retains its22:34 invocations, active with
   zero restarts and no new failure, over2.5hours later. Both NL ordinary
   watcher/AWG/TCP invocations remain unchanged from entry. Reconciliation,
   renewal and directory-sync last executions succeed and timers remain active.
   Panel imports01:06:13/15/18 report all relevant services active, transport `ok`.
8. **01:07:57–01:08:02:** repeat all six public requests after the rotation below:
   HTTP200 and all three configuration signatures PASS; existing identity unchanged.
   Current server reachability is verified, not sustained stability acceptance.

## Separate scheduled rotation, not recovery-induced NL restart

Between the strict audit and final readback, the pre-existing authorized leaf/CRL
schedule completes a different operation at **21 November23:33:18**. The latest
receipt matches the current transaction, `COMMITTED`, null first cause; all three
reconciliation entries are `PROMOTED`. Gate authorization is
`OPERATOR_APPROVED_LEAF_CRL_SCHEDULE`, `RENEWAL_READY`, `zero_downtime:false`,
`pre_stop_sessions:UNKNOWN`. NL MESH starts23:33:07/09 and HTTP23:33:14; their
invocations change. Therefore the earlier HTTP/MESH continuity statements apply
only through the pre-rotation audit, not the final snapshot. Existing schedules
were neither replaced nor manually triggered by this recovery. No zero-downtime
or absence-of-session-impact claim is made for this maintenance.

## Runtime, evidence and remaining work

Installed transport remains legacy
`125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c`;
inner `control/friends/transport_gateway.py` hash is
`1800894a8e561b0eb77759931e6813e8c7ad4c9e2ead1b24c7c2b7ba15e8bee3`.
Other unchanged runtime pins are documented in the
[20 November report](2026-11-20-ru-recovery.md#exact-runtime-and-evidence).
No runtime package rollback is needed because none was deployed.

Raw evidence and encrypted backup/key stay ignored under
`state-client-build/ops-incident-20261121-r2/` and
`state-client-build/ops-recovery-20261121-r2/`; remote recovery state stays at
`/opt/apps/family_connect/private-ru-recovery-20261121-r2`.
No keys, profiles, command map, registry DB or raw evidence is committed.

Permanent recurrence prevention is **not implemented**. A qualified follow-up must
distinguish lock wait, native-query and durability deadlines, preserve entitlement
and fail-closed guarantees, and establish the historical long-hold cause before
claiming a permanent fix. No deadline increase, fail-open bypass or unqualified
restart loop is substituted. Owner reconnect and actual tunneled traffic remain
NOT_RUN in this task; a configuration200 is not a VPN traffic test.

On another failure, preserve the new receipt, fence only RU, drain and stop the RU
trio under the same guards. Do not roll back live registry/cache, overwrite earlier
evidence or generically stop HTTP/NL. This report does not authorize queued product
implementation, observations-v1 rollout or new scheduled recovery.

The source branch was already divergent; remote `main` readback before this
checkpoint is `cb47bf230c6795cf21f4e6948253f49aa5377ed0`. Only this task's new
documentation is staged; older uncommitted work is preserved. Ordinary push outcome
is reported separately; no force push, history rewrite or unrelated merge is used.
