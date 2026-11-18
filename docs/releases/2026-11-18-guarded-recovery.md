# 18 November 2026 — guarded RU / MESH recovery

## Scope and customer-visible failure

The owner explicitly requested recovery after the read-only incident report.
This is not a PR44 deployment or a change to installed transport/runtime bytes.
The ordinary RU recovery was already executed in another session at12:18UTC;
this session detects it before any stop and does not repeat it.

At12:38:51UTC the original started PIDs/invocations remain stable, NRestarts0,
68 revisions match, actual/expected AWG20 and TCP20 sets match and attempt age is2s.
All eight protected tables, generation2 material, command map and effective units
match the saved baseline. The first failure survives with its original inode/hash
under `transport-failure.20261118-0149.preserved.json`.
The existing fresh27-table backup and isolated paid-projection restore passed;
off-host AES-GCM backup has a verified decrypt roundtrip. No live DB was restored.
This is server-side continuity, not a new physical-client HTTPS acceptance.

The owner's “не удалось получить список серверов” is an additional failure before
tunnel setup. Android `FriendsActivity.connectNow` maps a failed
`FriendsAccessAndroid.profile` request to this message. Explicit Amsterdam choices
fetch `/friends/gateway-configuration/nl-amsterdam-1` and
`/friends/gateway-configuration/nl-amsterdam-2` from the shared RU HTTPS service.
Consequently, running Amsterdam AWG/TCP daemons did not make the VPN usable while
RU HTTP remained fenced. There is no demonstrated provider-block explanation for
the original stop. Both recovery publishers subsequently reached real Telemost READY.

All times below are UTC. The original read-only diagnosis remains a historical
snapshot; the owner subsequently authorized the guarded recovery recorded here.

| Node / expected role | Actual unit | First incident event | Established cause | User path / minimal recovery |
| --- | --- | --- | --- | --- |
| RU / shared provisioning and renewal | `family-connect-friends-http-candidate.service` | 17 November20:41:01 | Common renewal quiesce/fence after `STALE_NODE_STATE` | Configuration delivery for all gateways; finish ownership recovery, commit current materials/directories, then start HTTP |
| Amsterdam1 / MESH gateway | `family-connect-restricted-bootstrap.service` | 17 November20:41:06.786 | Same renewal stop before credentials expired; no initiating reboot or restart-limit event | MESH; reconcile the unprepared operation, normal fresh renewal, start only after replicated commit/readback |
| Amsterdam2 / MESH gateway | `family-connect-restricted-bootstrap.service` | 17 November20:41:11 | Same renewal operation and fence | Same procedure, checked independently on the canonical second Amsterdam |
| RU / AWG and TCP admission | `family-connect-paid-watch.service`, `family-connect-friends-awg.service`, `family-connect-friends-tcp.service` | 18 November01:49:35 | Decision-state fsync8.548s exceeds8s operation deadline; dependent transports stop | Ordinary RU VPN; fresh backup/restore qualification, RU-only fence/drain and coordinated unchanged-runtime start |
| RU / MESH control role, not exit gateway | Bootstrap unit is `not-found` | Not an incident | This role does not require an NL bootstrap process | Do not install/enable an NL gateway just to make the panel row green |

The initial concurrent registry writer behind `STALE_NODE_STATE` and the underlying
cause of the long fsync remain UNKNOWN. A single causal chain joining those two
incidents is not established. Neither an old PASS nor source-main proves recovery.

## Expired unprepared MESH completion

Installed runtime is the fcb31164 maintenance capsule, not source main. Its normal
expired rollback terminal requires a same-operation plan, absent in this incident.
The new explicit operator helper completes only an all-acquired, never-prepared,
uncommitted STALE_NODE_STATE operation with expired leaf predecessors.

- Default `reconcile` still rejects expired credentials. Its explicit predecessor
  option validates signatures, current authority, grant bindings and absence of
  pending revocations; both predecessor leaves must already be expired.
- Existing immutable rebase intent preserves the original transaction/owner and
  current registry digest. Only the RU ownership comparison is rebound; no DB,
  authority, grant, profile or directory is restored or rewritten by this step.
- Each node independently checks its exact owner, expected state, stopped readers
  and an allowlist excluding preparation, staging and commit artifacts before using
  the installed no-op rollback and fenced-terminal methods.
- Durable controller binding replaces no plan: it explicitly records unprepared
  completion. Existing fenced cleanup archives the evidence and releases ownership.
  The helper never starts a reader. Normal fresh renewal remains mandatory.
- Partial node finalization is replayable; unfinished nodes, active readers, changed
  owner/profile/intent, unexpected artifacts and invalid predecessors fail closed.

Qualification:27 selected tests pass on current source and again against the
fcb31164 source capsule matching installed production-node/controller/grant hashes.
These tests qualify the explicit helper, not user traffic. The live application
and subsequent verification are recorded separately below.

## Applied recovery and retained guards

1. Preserve the already recovered RU watcher/AWG/TCP; do not repeat their restart.
   Pause/drain only credential-renewal and restricted sync writers/readers. Take a
   fresh current registry backup, integrity/FK-check it, and retain node/controller
   state privately. Encrypted off-host copy decrypts byte-for-byte; no DB is restored.
2. Reconcile the exact acquired, never-prepared operation
   `scheduled-1794948040-548f317346ab83ca`. All three node dry-runs pass; finish
   sequentially at12:54:54/57/59. Controller completion at12:55:22 records
   `ROLLED_BACK_READERS_STOPPED`, archives evidence and clears ownership. Restricted
   database snapshot equality still holds. This is a no-op unprepared rollback,
   not restoration of historical records or expired credentials.
3. With each NL gateway still stopped, configure a new bounded publisher generation
   against current locator/profile/inode bindings. Both installed publishers create
   and authenticate actual READY rooms, then publish current directories. Preserve
   the first NL1 pre-publication attempt instead of deleting/reusing its O_EXCL
   marker; its local capture/configuration error is not evidence of provider blocking.
4. Run installed normal renewal under `owner-mesh-recovery-20261118` with explicit
   authorization. Both new leaf certificates and shared CRL27373 are valid from
   13:02:08 until17:02:08. Authority remains unchanged, valid through
   16 January2027 22:36:48. All three reconciliation receipts match.
5. The installed resume policy preserves the prior inactive NL state. Consequently,
   directory publication initially waits for an unchanged predecessor and records
   `NEW_DIRECTORY_NOT_READY`; the bounded controller call expires with a durable
   commit already replicated. Read back that state rather than rerunning renewal or
   rolling back. Start each gateway only after its same-operation committed plan,
   current-material and three-way reconciliation checks: NL1 at13:05:14 and NL2
   at13:05:15. Resume the existing committed transaction from `NL2_RESUMED`.
   Cleanup finishes COMMITTED at13:09:54; original first-cause evidence is retained.
6. Start RU HTTP at13:10:04 after terminal commit and ownership cleanup. Retire both
   temporary publisher configurations into root-only evidence after proving each
   normal gateway published a new directory. Restore originally active renewal and
   directory-sync timers; leave the originally inactive restricted-sync timer alone.
   No enable/unmask/reset-failed, runtime replacement, PR44 deployment or authority
   rotation is performed.

The completion helper is delivered only to the administrative interpreter for this
explicit operation. Installed maintenance/gateway/ordinary transport files and unit
contents are not replaced. After a durable commit the valid recovery direction is
roll-forward reconciliation, not old DB/certificate rollback. Failed guards require
fresh readback; never clear an owner, failure, transaction, deny or cache to proceed.

## Fresh verification

- At13:10:33 the existing enrolled probe obtains HTTP200 challenges and signed
  configuration responses for RU and both explicit Amsterdam choices through public
  TLS. The packaged Android anchor verifies all three; private identity keys are
  unchanged. No enrollment, access grant or new user identity is created.
- Panel readback at13:13:13 contains RU observation/import13:11:20/21,
  Amsterdam1 13:11:22/23, Amsterdam2 13:12:06/07; all transport collection attempts
  are `ok`. HTTP, AWG/TCP and both NL bootstrap rows match direct active states.
  RU bootstrap remains correctly `not_found`. Installed “MESH · bootstrap” mapping
  still names only `family-connect-restricted-bootstrap.service`.
- At13:17:15 RU watcher/AWG/TCP retain their12:18 PIDs/invocations and NRestarts0.
  Exact20 AWG and20 TCP sets,68 applied revisions and2.469s attempt freshness pass.
  All eight protected tables, transport identities/membership/terms/prepared state,
  generation2 material, command map and effective units match the saved baseline.
  The original failure hash remains preserved; no new active failure file exists.
- Scheduled renewal13:13:00–13:13:14 exits0. Directory-sync13:17:05–13:17:11 and
  paid reconciliation13:16:46–13:16:50 exit0. These inactive oneshots are healthy;
  their timers are active. Next scheduled renewal observed at13:28:00.
- At14:14:49/50 both NL bootstrap processes remain active with the13:05 invocations,
  NRestarts0, unchanged gateway executable hash and boot-disabled policy. No reboot,
  outstanding owner or temporary publisher configuration is present. Their normal
  directories remain current through17:05:14/15. Ordinary AWG/TCP are also active;
  this is not a claim that every ordinary transport invocation stayed unchanged.
- The historical probe's loopback bootstrap refresh fails with
  `control_unavailable`; its SSH forward is closed and failure evidence retained.
  It is not counted as a passed test. The actual public test instead uses the freshly
  authenticated HTTPS readiness directory, native-import validation and an
  intentionally unreachable ordinary broker, with no SSH tunnel.
- Amsterdam1 public MESH passes at14:11:48; Amsterdam2 independently passes
  at14:25:11. Each proves bootstrap and dedicated family auth, four HTTPS requests,
  three DNS requests and its own expected Amsterdam egress. Both native probes exit0
  and are reaped; identity keys remain unchanged, with no public-test SSH forwards.
- Final14:37:59–14:38:00 RU readback retains the12:18 transport invocations and
  13:10 HTTP invocation, all NRestarts0; exact20/20 sets and68 revisions still match,
  attempt age1.084s. The original failure evidence remains intact. Renewal's latest
  scheduled run14:28:03–14:28:13 exits0, next14:43:03; directory-sync and paid
  reconcile also exit0. No diagnostic journal/ionice process or pending systemd job
  remains. Panel imports14:36:51/54/56 match all three current nodes, attempts `ok`.
- Do not extend the13:17 protected-table equality claim indefinitely after reopening
  HTTP. A later strict comparison correctly detects two changed `support_sender`
  fields in `chat_bindings`, with no added/removed rows or other changed columns.
  The other seven protected tables remain byte-equivalent by fingerprint, including
  devices, invites and paid terms/events. The later writer is not attributed by
  this readback; preserve these live changes rather than restoring the backup.
  This is explicitly recorded, not suppressed to manufacture an equality PASS.

Remaining acceptance: the owner's affected device/network retry. Successful scheduled evaluation is
not proof of the next future credential-rotation cycle. The recurrence causes above
remain open operational risks; no storage/root-cause fix or observations-v1 rollout
is claimed by this recovery.

Source/checkpoint commits are local. Ordinary push remains rejected because the
existing local main and remote main diverge; no force push, reset or unrelated merge
is used to conceal that. Operational restoration does not depend on a source push.

See [fresh incident diagnosis](2026-11-18-mesh-ru-incident.md) and
[sanitized recovery verification](2026-11-18-guarded-recovery.receipt.json).
