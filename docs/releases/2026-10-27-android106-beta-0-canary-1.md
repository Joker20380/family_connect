# ANDROID-CONTROLLED-BETA / BETA-0-CANARY-1

## Owner-requested NL reboot — completion unconfirmed, 29 October

Canary remains **PAUSED_BY_OWNER / LIVE_WRITES_NOT_RUN**. After reporting the provider
console unusable, the owner requested availability recovery and reported pressing the
provider reboot control. Exact control/mode and operation completion are not observed.
At09:35–09:37UTC, six SSH banner checks still time out. Fresh09:36:53UTC network check:
TCP22/443 reachable, SSH banner absent, ICMP3/3 with0% loss. This does not prove that
the VM rebooted or identify the cause. Boot time, services and previous kernel journal
remain unreadable; no restored-health claim. Need provider operation status before a
second power action. No operator-issued reboot/service restart, application/config
change, canary activation, paid event, CRL or Android action. Earlier no-reboot evidence
below describes only the preceding read-only diagnosis. Raw evidence remains private.

The owner subsequently reported the server booted. Fresh09:40:08UTC external check:
TCP22/443 now time out, ICMP0/3; the09:39:25UTC RU vantage point also cannot reach SSH.
This change is not proof of successful OS startup or restored service. Six bounded SSH
probes after the boot report remain unable to connect. Need the current console boot
screen or provider operation status, not another blind restart. RU Friends HTTP remains
active; renewal timer active/waiting, latest worker result remains failed from09:27:52UTC.
No manual renewal or snapshot RPC was sent after the boot report; remote NL diagnostic
shell was not reached. No root-cause, material-readiness or canary acceptance claim.

## Owner pause and read-only NL diagnosis — 29 October

**PAUSED_BY_OWNER / LIVE_WRITES_NOT_RUN.** Canary paused at the owner's request;
only read-only server diagnosis continues. No stage0, recovery, migration or restart.

- Around09:20UTC, local ICMP4/4 replies,0% loss, mean12.4ms. From both the local
  workstation and RU host, TCP22/443 connect in approximately15–42ms. SSH supplies
  no banner within8s; the full administrative SSH attempt also times out after30s.
  The existing server-to-server forced-command snapshot already failed the same way.
- A raw no-SNI TLS probe on443 times out8s; it is **not** an authenticated VPN test
  and is not independently proof that the configured TCP/VPN protocol failed.
  Port80 refuses connections; no claim that a service was expected there.
- Last successful stored NL observation09:03:55UTC: load3.796, RAM89.92%,
  disk50.42%, uptime3972354s. At08:55:40UTC load peaked15.55; available-memory-based
  utilization then rose70.58%→89.92% by the last sample. Historical capacity is1 CPU.
  Current CPU, process, kernel/OOM and IO metrics are inaccessible through stalled SSH.
- Network reachability is present; user-space/resource or IO stall is the leading
  hypothesis, not established root cause. Earlier27 October IO stalls are historical
  context only. No claim that the disk is full, OOM occurred or a particular process
  caused this incident. Need provider out-of-band console/kernel evidence to distinguish.
- No reboot, service restart/reload, kill, configuration change or automatic repair.
  Private diagnostic evidence retained; pre-interruption documentation is preserved.
  Canary remains paused even if the server later recovers; owner resume is required.

## Live entry with a pre-existing certificate — 29 October

**LIVE_ENTRY_PREFLIGHT_FAILED / LIVE_WRITES_NOT_RUN.**
Entry main89af55432bf2f748311914a78548f9051b67e259. Same task/checkpoint.
Former `BLOCKED_EXISTING_CERTIFICATE_HORIZON` entry gate:
**SUPERSEDED_BY_PRODUCT_CONTRACT_REVIEW** by the explicit owner decision.
Stage0 version0 activation does not require zero valid certificates. Existing
`RestrictedReadiness.fetch()` rejects reuse of a retained certificate beyond the new
paid expiry and issues a paid-bounded replacement; the paid-aware CRL builder checks
every still-valid certificate against `_grant()`. Product source/packages unchanged.
The zero-valid-certificate requirement applies to final recovery, not stage0.

- Fresh09:14:18UTC: existing private HMAC binding only, same safe_ref, exact106 and
  active non-revoked device/invite PASS; subscriptions/events0/0, cohort0/10.
  Baseline safe certificate token `dc6b3aa3b462`, NotAfter `2026-10-29T11:42:38Z`,
  retained unchanged. No manual deletion, expiry/revision edit or early revocation.
- Actual09:17:07UTC: existing RU→NL account-level forced-command snapshot exits255
  with SSH banner-exchange timeout. Renewal timer is active; worker is not running,
  latest normal result `exit-code`, status1. Direct administrative SSH also times out
  before remote inspection. Cause is not established; a local-only transport issue
  is not assumed because the accepted server-to-server snapshot route also fails.
- Consequently fresh canonical/material health and the coordinated backup cannot
  be accepted. No fresh backup or bound permit was built; stage0 and phone handoff
  were not started. Earlier canonical migration remains accepted, not rolled back.
  No source/package/launcher/route change, floor operation, service restart/reload,
  paid event, readiness challenge/fetch, CRL generation/delivery or Android action.
- This is an observed failure of the already-listed preflight health requirement,
  not a new infrastructure checkpoint or additional gate. No zero-certificate wait.
  The latest renewal failure was observed, not triggered by a manual renewal run.

The complete live parameters are recorded without application: natural600s,
Connect deadline90s, post-expiry120s, CRL phase900s, post-CRL session180s,
final recovery2592000s; purpose `internal_canary`, amount_minor0, customer revenue0.
Paid replacement/new safe token, paid_until, natural-expiry/cached-certificate/session
results, CRL revoke-set count and final recovery all remain NOT_RUN.

After owner resumes the paused canary and the existing route is functional: complete only
the authorized minimal preflight and fresh private backup; then ask the owner to open
Family Connect, leave Connect unpressed and reply ГОТОВ. No activation before that
fresh reply. No automatic infrastructure repair, migration or restart is authorized here.
Sanitized documentation only: strict JSON, privacy, links, scope and diff checks PASS.
[Existing receipt](2026-10-28-android106-beta-0-canary-owner-ready.json).

## Historical certificate-horizon recheck — superseded

**BLOCKED_EXISTING_CERTIFICATE_HORIZON / LIVE_WRITES_NOT_RUN.**
Entry main6136618777a0feeaff045d57f5ffb2cc19163350; same checkpoint and binding,
no Support ID or repeated production lookup. Exactly one read-only certificate
readback: server UTC08:50:36, after the required28 October23:10:39 margin.
Device/invite active and not revoked; exact Android106 eligibility PASS.
One valid certificate: safe certificate token `dc6b3aa3b462`, latest NotAfter
`2026-10-29T11:42:38Z` (12:42:38 Europe/Brussels). Cause not established.
Same read-only transaction confirms subscriptions/events0/0 and cohort0/10.

STOP at the explicit certificate gate. Active-session check, canonical/material
preflight and fresh backup NOT_RUN; earlier infrastructure acceptance is not a fresh
readback for this continuation. No production write, permit construction/application,
paid event, activation, readiness request, CRL operation, certificate edit/deletion/
revocation, Android action, restart/reload or route/source/package change.

Stage0 parameters recorded **without application**: natural paid period600s,
owner Connect deadline90s, post-expiry observation120s, purpose `internal_canary`,
amount_minor0, customer revenue0. No additional infrastructure/source gates.
Only this report and its existing [receipt](2026-10-28-android106-beta-0-canary-owner-ready.json)
are updated; STATUS/PLAN remain unchanged because the blocker is unchanged.
Strict JSON, privacy scan, Markdown links, staged scope and diff checks PASS.
No automatic retry or stage0; any later activation still requires explicit owner command.

## Owner ГОТОВ — fresh live-entry stop, 28 October

**OWNER_READY_RECEIVED / BLOCKED_EXISTING_CERTIFICATE_HORIZON / LIVE_WRITES_NOT_RUN.**
Entry main3996fa05fcf6bef7ba660f8e78e9a614381ef274. Same BETA-0-CANARY-1;
no new PLAN ID, no new canary and no repeated migration operation.

- Fresh read-only observation20:36:58UTC: protected ledger0/0, cohort0/10,
  unchanged binding and fresh exact Android106 eligibility. One valid owner certificate
  now exists; the accepted20:20:38 readback had none. Its NotAfter is23:10:09UTC28.10
  (00:10:09 Brussels29.10), with more than1800 seconds remaining. The certificate
  horizon is blocked. Its appearance is not evidence of a Connect press; no causal
  attribution or absence of concurrent device activity is claimed.
- Canonical gateway and actual account SSH snapshot PASS; strict profile/directory
  signatures, bindings and times PASS. Renewal active/latest success, no pending
  operation, source pins exact. Publisher directory route unchanged. CRL/floor27219,
  headroom9194s. Canonical migration remains accepted; rollback is neither needed nor run.
- Stage0 stopped before any production mutation. No paid event, permit/package,
  rehearsal/write credential, backup, timer change, restart, CRL/sequence update,
  operator readiness request or Android action. The existing certificate was not
  deleted, revoked, shortened or replaced. Future exact-CRL route remains disabled
  without a permit; this readback does not activate a CRL phase.
- Private bound envelope still has permit=null. The runbook requires an explicit
  paid period and observation/stop bounds; none is supplied in the recorded live
  procedure. ГОТОВ satisfies phone readiness, not an invented duration. A new backup
  is deferred until immediately before a fully specified, fresh-gated operation.
- Read-only observer initially stopped on the new certificate, then completed a
  diagnostic-only readback. Its local sequence comparison was corrected to the
  existing one-element list shape; no production source or validation was changed.
  Strict JSON, privacy scan, Markdown links, staged scope and diff checks PASS.
  Product tests/builds are not rerun for this documentation-only result.

STOP. Keep Connect unpressed. A later NotAfter+30s readback is only a candidate
check, not automatic clearance: another issued certificate can extend the horizon.
Explicit stage0 period/observation bounds, fresh materials and a fresh canary backup
remain required before any apply. No automatic retry, activation, CRL or recovery.
[Sanitized receipt](2026-10-28-android106-beta-0-canary-owner-ready.json).

## Coordinated canonical-profile migration — 28 October

### Final pinned-venv canonical acceptance — 20:20:38UTC28.10

**READY_FOR_OWNER_LIVE / LIVE_CANARY_WRITES_NOT_RUN.**
PINNED_VENV_RUNTIME_PASS / SNAPSHOT_LAUNCHER_ACCOUNT_REHEARSAL_PASS /
CANONICAL_PROFILE_MIGRATED / RENEWAL_GATEWAY_SNAPSHOT_ALIGNED / CRL_FLOOR_ALIGNED.
This continues BETA-0-CANARY-1, not a new task or canary checkpoint. The historical
failed cutover/accepted rollback and its spent budgets remain separate evidence.

- Runtime source fix5cc52f6bf967174bdfa34ba89436c4ad3b13ca60 and rehearsal receipt
  commit18120833a8b0fedf01fb9c7df0d31fb750156d87 pushed; remote SHAs verified.
  The invocation entrypoint is preserved; resolved ELF is provenance, not a substitute.
  Exact private runtime pins were checked before rehearsal installation, before production
  snapshot activation and at final readback. CPython3.14, rns1.5.1,
  cryptography46.0.7 and pyserial3.5 PASS; isolated user-site/dependency inventory PASS.
- Real account-level SSH rehearsal PASS using the exact accepted PYZ and fresh secure
  non-authoritative production-byte copy. No floor/CRL change for rehearsal.
  Exit0/no stderr/strict schema, exact profile projection and valid directory PASS.
  Temporary key removed and rejected; original authorization bytes restored exactly;
  temporary config removed; rehearsal files private/inactive; old actual snapshot PASS.
- Repeated fresh preflight PASS with current materials; no historical hash used as a
  permit without readback. A legacy blanket systemd-job guard was narrowed to the
  observed target service: no target job, no daemon reload needed, healthy exact argv.
  Unrelated pending jobs were not operated on. A separate stable publisher read and
  strict signature/binding/time validation passed; directory validation was not weakened.
- Fresh coordinated private backups on both hosts validated, including artifacts,
  profile/directory metadata, effective units/argv, snapshot authorization/configuration,
  publisher configuration, runtime pins and rollback source. Prior backups were not reused.
  Renewal paused once, no running/pending/staged operation or lock holder.
- A new secure canonical copy was created from then-current authoritative bytes under
  the shared lock. Neither the failed prior candidate nor the rehearsal copy was reused.
  Actual gateway/snapshot read access, write denial, publisher write denial, exact metadata
  and both root atomic-write fixtures PASS. All routes were staged coherently.
- One fresh root-local permit-bound offline floor reconciliation changed only
  minimum_crl27088→27219. Embedded CRL hash/number unchanged; old live profile untouched,
  directory untouched by the operation, no RU CRL/sequence mutation or new CRL generation.
- Snapshot-only canonical activation passed the **actual SSH pre-restart gate**: exit0,
  no stderr, strict schema, aligned canonical floor and valid current directory.
  Only then renewal/gateway routes activated; cross-component route audit PASS.
- Exactly one controlled gateway restart. Accepted binary/effective/running argv,
  new invocation, no restart loop, listener and pinned TLS server identity PASS.
  Co-hosted publisher remains healthy with unchanged configuration/directory target;
  its valid signed directory rotation is accepted. No separate publisher restart/change.
- Post-cutover actual SSH snapshot PASS. Accepted non-mutating renewal evaluate reached
  the real account/transport and returned NOOP, zero file/remote writes/restarts and no
  promotion. Protected ledger0/0, cohort0/10, owner certificates0/horizon clear,
  owner binding/accepted exact106 unchanged. Friends HTTP invocation unchanged across
  this cutover; RU CRL hash/sequence unchanged. No readiness/Android/stage0 action.
- Timer resumed once and is active on canonical configuration, latest result success,
  no pending failure. Old profile moved intact to private rollback evidence, not deleted.
  Final real SSH snapshot and accepted evaluate both PASS **after old-profile retirement**.
  Five profile routes share one canonical profile/lock; future exact-CRL permit remains
  disabled. No temporary maintenance/rehearsal credential; monitoring remains active.
- Final20:20:38UTC28.10: CRL/floor27219, material headroom10170s (required≥720).
  New budgets: credential1/1, timer cycle1/1, offline floor1/1, gateway restart1/1,
  emergency rollback0/1. Rollback not needed; no second cutover/floor operation.
  77 launcher/runtime +115 snapshot/canonical/authorization/parser +70 package/directory
  checks PASS (262);29 unchanged native directory cases deliberately deselected.
  Full historical suite and Android/Linux/Windows builds NOT_RUN.

Historical NEXT at this migration milestone was the owner reply **ГОТОВ**.
That reply is received; the fresh live-entry stop above now controls continuation.
This remains preparation acceptance, not paid/live-canary execution.

### Historical pinned venv runtime continuation — source checkpoint

Source fix5cc52f6bf967174bdfa34ba89436c4ad3b13ca60 is pushed and remote SHA verified.
Actual account-level temporary-key SSH rehearsal PASS: exit0/no stderr, strict schema,
exact unchanged live-profile projection from a fresh secure non-authoritative copy,
valid existing directory and unchanged CRL/floor. The canonical locator contract was
not weakened. Runtime pins were rechecked immediately before installation.
Cleanup PASS: original authorization bytes restored exactly, removed key rejected,
temporary configuration removed, rehearsal copy/locator/launcher private and inactive,
old production snapshot actual SSH PASS. Credential budget1/1; timer/floor/restarts0/1.
No service restart, old-profile mutation, paid/readiness/Android action or stage0.
Fresh coordinated cutover gates remain pending; this is not READY_FOR_OWNER_LIVE.

PINNED_RUNTIME_SOURCE_READY / LIVE_WRITES_NOT_RUN. The owner authorizes preserving
the working venv invocation entrypoint and a fresh secure non-authoritative rehearsal
copy. The prior realpath-only model pinned the correct base ELF but lost the venv
context. The new builder preserves entrypoint identity in both shebang and exec argv,
pins the bounded secure symlink chain/final ELF, configuration and installed inventory,
and rejects writable roots/packages, unsafe links, dependency drift and injection.
Runtime probes execute as the actual snapshot account with isolated flags, fixed clean
environment and root working directory. CPython3.14/prefix/user-site and exact
rns1.5.1/cryptography46.0.7/pyserial3.5 checks PASS: PINNED_EXISTING_VENV_READY.
Accepted snapshot help PASS; unsuitable base missing-RNS failure reproduced/rejected.
No package member changed; retained coordinated artifacts remain exact, not rebuilt.
77 launcher/runtime +115 snapshot/canonical/credential/parser +70 package/directory
tests PASS.29 unchanged native directory cases deliberately deselected; no full suite
or platform build. Local fixture umask defect corrected and tests rerun successfully.
Mandatory actual SSH rehearsal, fresh backup/copy/floor and cutover remain NOT_RUN
at this source checkpoint; budgets0/1. No paid/readiness/Android/stage0/RU mutation.
The authorized next gates must complete before READY_FOR_OWNER_LIVE or phone instructions.

### Historical launcher continuation — 19:38:59UTC28.10

**BLOCKED_SNAPSHOT_LAUNCHER_REHEARSAL / LIVE_WRITES_NOT_RUN.**
Actual temporary-key SSH rehearsal **NOT_RUN: prerequisites blocked**. Not ready for
owner live. This remains BETA-0-CANARY-1; no new task or canary checkpoint.

The owner accepts the previous rollback and grants a new bounded rehearsal/migration
budget. Source fixdd926aefccc978b9e73d9353d7bdf442f5374a8e
(`fix: pin executable in canonical snapshot launcher`) is pushed; remote SHA verified.
Every new production budget remains0/1. Previous spent budgets are historical
and have not been reset or confused with this continuation's counters.

- `scripts/build_profile_snapshot_launcher.py` requires an absolute canonical regular
  executable, exact private stat/hash pin, target-account execute/traverse access and an
  actual isolated CPython3.14 invocation. Version text, relative/argument-bearing paths,
  wrappers, unsafe modes and caller extra fields fail with typed errors. Optional
  diagnostic version never enters argv. No production path/account/pin is embedded.
- The launcher executes exactly the validated interpreter, `-I`, `-B` and exact package.
  argv-aware quoting is parsed back and the complete generated launcher is checked.
  It uses isolated direct exec, not shell interpolation or `sh -c`. Original-command
  restrictions and all required SSH restrictions are preserved. Read-only rehearsal
  mode rejects renewal/write payloads before package execution and uses no disk spool.
-53 launcher tests PASS, including the actual previous version-as-command regression,
  direct real-process read-only launcher execution, malformed input, argv tamper,
  account permission, private pins and restricted key/command checks.101 existing
  snapshot/canonical-profile checks,2 package checks,14 existing credential/parser checks
  and68 Python directory checks PASS:238 focused checks total.29 native directory cases
  are deliberately deselected; their unchanged previous accepted result is retained.
  No full historical suite or Android/Linux/Windows client build.
- Retained snapshot/renewal/maintenance/gateway hashes and sizes match the owner's exact
  accepted values. All17 extracted renewal package members also match on both hosts.
  Coherent artifacts are unchanged fromc9c0a4d; this utility/test change is outside all
  packaged source inventories. No production candidate rebuilt or substituted.
- Parsed working forced-command argv and target-account executable/stat/runtime probes
  independently resolve the same absolute Python3.14 target. Corrected production and
  read-only launchers/configuration/pins were retained privately **locally**, not installed.
  No executable path, metadata or account identity appears in committed evidence.
- Prerequisite1: using that resolved target changes the virtual-environment import
  context. The accepted snapshot PYZ `--help` exits1 under the real snapshot account with
  `ModuleNotFoundError: No module named 'RNS'`. The same exact PYZ with the currently
  working route's interpreter passes. This is deployment/runtime context, not artifact
  drift or evidence that the snapshot source itself is broken. No dependency installation,
  symlink substitution, extra argv, environment override or runtime modification was made.
- Prerequisite2: accepted `Locator.validate_reader()` under the same actual account
  rejects a locator targeting the authoritative old profile with `LOCATOR_PATH_CONFLICT`:
  that profile shares the independent publisher boundary. Its ownership/mode also do not
  match the secure canonical reader contract. Pointing the unchanged package there cannot
  satisfy the requested old-profile rehearsal without changing a required contract.
  No copying/aliasing the old profile to pretend it is that route; no weakened validation.
- Therefore no rehearsal key/line was installed, and no actual temporary-key forced
  command was attempted. Direct account-level probes are explicitly **not** claimed as
  the mandatory SSH rehearsal. Fresh production backup, canonical copy, reconciliation,
  renewal pause, pre-restart snapshot activation and gateway restart are all NOT_RUN.
- Fresh read-only production gate at19:38:59UTC: old renewal timer active/latest success,
  no pending operation; old gateway/publisher route healthy; original production snapshot
  actually invoked through its real account/transport: exit0/no stderr/strict schema.
  CRL27219/floor27088, material headroom12668s, ledger0/0/cohort0/10,
  owner certificates0/horizon clear/binding unchanged, accepted Android106 retained.
  No RU material mutation, Friends restart, paid/readiness/Android action or stage0.

Required follow-up is an explicit compatible interpreter/environment and old-profile
rehearsal design. Do not silently rebuild/substitute artifacts, weaken the canonical
boundary, spend a cutover budget without the real SSH gate, or ask the owner to open the app.
STOP. This is source correction plus diagnosed prerequisites, not completed migration.

### Historical accepted rollback from the previous production attempt

**BLOCKED_PROFILE_CUTOVER_ROLLED_BACK / LIVE_WRITES_NOT_RUN.**
**NOT READY_FOR_OWNER_LIVE.** No second production attempt is authorized.

### Final coordinated attempt and rollback — 19:14:58UTC28.10

- The exact accepted renewal API/source and narrowly projected accepted gateway source
  were packaged fromc9c0a4de55f455e0788e7b519383c0cb0743fc96. All four artifacts have
  two byte-identical builds, member manifests, privacy/import/help and license checks.
  No client release/version/catalog changed; installed active binaries are restored to
  their exact pre-cutover identities. New packages remain inactive private assets.
- Fresh preflight observed normal scheduled renewal COMMITTED, CRL/sequence27219,
  floor27088, materials14335s, paid ledger0/0/cohort0/10, owner certificates0, horizon clear.
  Both root-private coordinated backups validated. Inactive configuration corrections
  restored the exact accepted transport target and ensured last-sorting gateway override.
  These did not change active routes or spend a restart/timer budget.
- One renewal timer pause confirmed no running or pending renewal and no lock holder.
  The canonical copy used exact fresh bytes and the shared root-controlled lock; gateway,
  snapshot and publisher read access/write denial passed. Renewal/maintenance root atomic
  fixtures passed. Directory remained at its original path/metadata/publisher contract.
- One root-local single-use bounded operation reconciled the **offline** copy floor
  27088→27219. Embedded CRL bytes/number, old live profile and directory were unchanged.
  No external maintenance credential, new CRL or RU material write occurred.
- Renewal, snapshot and gateway target configurations were activated while renewal stayed
  paused. The route audit passed before the one controlled gateway restart. The new
  binary/profile route, stable process/listener, group access, valid regenerated directory
  and publisher all passed; canonical floor27219 matched embedded CRL27219.
- The single actual canonical snapshot forced command then exited127: the fixed launcher
  contained the Python **version string**, not its absolute executable. The snapshot
  package did not run. Therefore source/library fixtures were insufficient launch proof;
  this is an operator fixed-configuration defect, not accepted migration or a reason to
  weaken validation. Renewal's non-mutating post-cutover evaluate was not reached.
- Required emergency rollback restored exact old renewal configuration, snapshot wrapper
  and gateway overrides, used one emergency gateway restart, verified the old snapshot
  route, and resumed the timer on the old source/pins. No second cutover or floor operation.
  The canonical copy is now private/inactive; the old live copy remains authoritative.
  Maintenance configuration is inactive; no maintenance/write SSH credential exists.
- Post-rollback readback: old gateway/source/config healthy; publisher valid on unchanged
  directory route; renewal timer active/latest success; no pending renewal; old snapshot
  response/SSH restrictions restored. Live profile bytes exactly match fresh pre-cutover.
  Live CRL27219/floor27088; offline inactive copy remains27219/27219. Minimum material
  lifetime14110s at19:14:58UTC. Directory hash changed only through legitimate publication.
- Friends source/config/invocation unchanged across this attempt; RU CRL/sequence unchanged.
  Ledger0/0, cohort0/10, owner certificates0, binding/horizon unchanged. Exact Android106 is
  the retained accepted observation, not a new phone action. No stage0/readiness/paid action.

Validation:478 affected Python checks plus focused native gateway/publisher suites and
deterministic artifacts PASS; one isolated actual-package copy/floor plus simulated
cutover/rollback fixture PASS. Production snapshot acceptance **FAILED** as above.
Strict JSON/privacy/Markdown-links/staged-scope/whitespace checks apply to this closeout.
Raw evidence/configuration/backup/permit and material contents remain private, outside Git.

Spent budgets: renewal pause/resume1/1; gateway cutover1/1; emergency rollback1/1;
offline floor reconciliation1/1. Profile migration is **not accepted**. The rollback route
is already active, not a pending recovery action. A future attempt needs the launcher
correction, end-to-end fixed-command rehearsal and explicit renewed production budgets.
STOP in this same checkpoint. Do not start stage0 or ask the owner to open the app.

### Historical source-stage observations before this rolled-back attempt

**Historical SOURCE_IN_PROGRESS; not the current production result.**
Continuation from44392427b8082f21cfe3d6c321efd86938e9cb63 in the same checkpoint.
The owner supersedes the cancelled snapshot-only proposal with one coordinated
profile route for renewal, gateway, snapshot, bounded maintenance and future exact CRL
delivery. The publisher directory must remain independent and unchanged.
[Sanitized migration receipt](2026-10-28-android106-beta-0-canary-canonical-profile.json).

### Fresh graph and first source step

- Read-only inventory confirms all13 deployed renewal source members match local
  accepted source and controller/node pins. Renewal timer active, latest service success,
  inspected NL owner/plan/files markers absent. No stage/promote RPC invoked.
- Gateway executable remains96754942e7518233bc702277d860b0c9b740fb7553c9742b2ae642a0746fe367.
  The retained accepted binary matches that running identity. Its credential loader
  accepts only owner-private mode; the new reader-group contract therefore requires
  a narrowly qualified reader-source change, not merely an argv substitution.
- Fresh entry observes RU/NL CRL27216/floor27088, paid ledger0/0, owner certificates0,
  certificate horizon clear, minimum material headroom11254s. These are time-bounded
  observations, not a write permit or a refreshed Android observation. No Android action.
- `control/friends/profile_store.py` introduces a root-controlled locator, existing
  shared-lock validation, CAS/metadata/permit rechecks, same-directory exclusive temp,
  metadata-before-write, fsync/replace/readback and transaction receipt callbacks.
  Renewal/equal-or-higher CRL, floor-only and strictly increasing exact-CRL builders
  align the target floor. The directory port exposes no mutation operation and accepts
  valid forward publisher rotations; invalid post-write directory causes exact profile
  rollback without restoring/chmod/chown of directory material.
- Existing bounded maintenance delegates its atomic replacement to the shared primitive.
  Its legacy same-parent/byte-identity assumptions have **not yet** been replaced;
  neither the historical package nor this intermediate source is a migration permit.

### Bounded validation and unfinished gates

45 new core tests and124 existing maintenance tests PASS in an isolated root container,
without network or production-state mounts. This includes all3 exact retained snapshot
contract checks and the existing14400 parser matrix.3 package tests PASS, including
byte-identical synthetic committed-source builds and import/help/manifest checks.
The first container invocation lacked Git for package fixtures; those3 fixture errors
were corrected by running the package suite in the existing locked host environment.
The initial optional snapshot skips were eliminated by supplying the hash-verified
generic archive; no production material was passed to tests. No full historical suite,
Linux/Windows tests or Android build.

This is a **source checkpoint, not release or migration acceptance**. Remaining:
accepted renewal integration and pins; canonical gateway/snapshot readers; maintenance
and exact-CRL integration; full affected-source gates; committed-source deterministic
production-candidate artifacts; fresh preflight and private backup; one coordinated
timer pause/cutover/resume; bounded floor reconciliation; old-route retirement; final
readback and owner readiness. No secure production parent/group/lock/locator, backup,
credential or permit created; no profile/directory/RU/paid write, timer pause, service
restart, Android action, readiness request or canary stage0. Current production versions
and routes remain the rollback baseline; no deployment rollback is needed at this step.
Do not substitute source-unit success for end-to-end reader/writer alignment.

### Accepted renewal method integration and source closeout

The first source checkpoint `f81757fda45b8943cd74fb66b4e9438d8ffd931f` was pushed
to main and its remote SHA verified. The next bounded source change modifies the
exact inventoried renewal implementation, not a substitute controller:

- NL construction requires a root-controlled locator whose digest is pinned in fixed
  node configuration. The canonical profile and independently managed directory are
  resolved separately. Missing canonical configuration fails closed.
- Stage validates the renewal target through the shared module and normalizes the
  floor to the incoming embedded CRL. Lower numbers and changed bindings are rejected.
  Existing signed expired-predecessor recovery remains validated by the original
  renewal validator; the incoming profile must still be current. No new RPC action.
- Canonical promote and rollback hold the same profile lock used by the shared store,
  use its atomic replacement and exact metadata, and leave the directory read-only.
  Post-write directory/validation failure restores exact previous profile bytes.
  Existing operation journal, archive/cleanup, promote replay and scheduled NOOP
  semantics are preserved in synthetic integration.
- No new artifact, locator or source pin has been activated on either server. Direct
  legacy fixture construction remains separate from the configured production path;
  it is not proof that an old live node has migrated.

Latest bounded checks: **173 root transaction/maintenance/exact-snapshot tests PASS**,
including4 canonical renewal integrations; **127 renewal/exact-CRL/package tests PASS**.
One optional test needing the explicit accepted native source/toolchain was not run.
The first host CRL attempts saw the sandbox's remapped ownership of the temporary
ancestor and failed the intended secure-parent guard. The unchanged suite passed
outside that sandbox with a private fixture base; no guard was weakened. The synthetic
publisher fixture was corrected to use temp+rename, and journal assertions to inspect
the existing completed/archive state rather than already-cleaned owner markers.
Total **300 PASS,1 optional native skip** is not the full migration completion gate.

Fresh16:48:44UTC readback observes RU/NL CRL27218, floor27088, minimum headroom13855s,
paid ledger0/0, cohort0/10, owner certificates0, unchanged owner certificate/readiness
scope and binding. The active accepted schedule completed a normal renewal; its
COMMITTED receipt and candidate CRL hash match the newly observed materials.
Friends started16:39:56UTC; the normal renewal receipt is16:39:57UTC. New runtime
invocations therefore do not constitute a checkpoint restart or a PID-only blocker.
Gateway binary/config, Friends source/config/runtime, publisher route and snapshot
forced-command authorization/source remain the same. Fresh ownership/modes/link/
extended-metadata comparison passes. This checkpoint generated no CRL and made no
RU, profile, directory, paid, Android or readiness write. Do not describe the materials
as byte-identical throughout the session: the legitimate scheduled writer advanced them.

At that source checkpoint live migration was NOT_RUN. Still required at that point:
controller/transport fixed-configuration and source-pin integration; actual gateway
reader compatibility; actual snapshot canonical routing; bounded maintenance's
canonical layout and renewable-directory redesign; all cross-component/package gates;
fresh coordinated backup and permit; the single pause/cutover/resume and bounded
floor operation; old-route retirement and final live acceptance. Budgets remain0 used.
No READY_FOR_OWNER_LIVE classification or phone procedure is authorized by these tests.

### Canonical bounded maintenance integration

Renewal source checkpoint `4523476201249123fc7c02ee7fb6b01f97561fb0` is pushed;
remote main SHA verified. This next source increment replaces the **active fixed**
maintenance configuration with a strict schema requiring a pinned canonical locator.
Legacy direct configuration remains only for historical synthetic regression fixtures;
the production configuration loader rejects it. No runtime caller path/identity/action
override or new scheduled renewal RPC is introduced.

Both bounded actions use the shared profile store, target builders and renewal lock.
The existing single-operation permit, authenticated journal, one-attempt limit, CAS,
readback and idempotent replay remain. Directory observations validate publisher pins,
metadata, bindings and forward progression, rather than requiring immutable directory
bytes/inode. The permit's directory digest is retained as an observation, not a CAS on
renewable material. Valid rotations before preparation or during replacement pass;
invalid post-write directory/binding/progression/contract causes exact **profile-only**
rollback. Directory bytes, metadata and publisher are never restored or modified.

Latest affected checks: **202 root transaction/renewal/maintenance/snapshot tests PASS**
and **127 host renewal/exact-CRL/package tests PASS**, with the same one optional native
compatibility skip. Total **329 PASS,1 skip**; no full historical/platform build.
The first local attempt found contract tuple/list serialization and an automatically
indexed synthetic directory. Contract serialization is canonicalized; the shared
metadata guard explicitly accepts the structural directory-index flag only on
directories, still rejecting policy/mutability flags and indexed regular files.
Six focused flag checks and23 bounded canonical maintenance checks cover these changes.

**SOURCE_IN_PROGRESS; live migration NOT_RUN.** No production action since the recorded
read-only observation, which must be refreshed before any permit. Controller transport/
pins, actual gateway and snapshot reader integration, coherent deterministic packages,
cross-component route qualification and every coordinated production gate remain.
All checkpoint production budgets are still0 used. No partial migration or owner-live
acceptance is implied; no stage0 or phone instruction.

### Canonical snapshot source and package contract

Maintenance checkpoint `db7174e78de98fa5b7e04828499764c1cedb876a` is pushed and its
remote SHA verified. Canonical snapshot source now uses a strict root-controlled fixed
configuration with a pinned locator and pinned renewal-helper executable contract.
The security snapshot returns the **same exact bytes/schema** as the retained accepted
archive for equivalent materials; no private key, extra profile fields or changed
response envelope. It opens no writer lock, creates no lock/journal and cannot write
the secure profile as the configured reader. Profile replacement during a snapshot
fails closed rather than returning a mixed observation. Valid publisher rotation passes.

Existing bounded credential-renewal dispatch remains a separate exact envelope to
the fixed pinned helper, with bounded input/output/time and a clean process environment.
Snapshot requests cannot invoke it. Unknown actions, path/config overrides, duplicate
fields and noninteger schema values are rejected; the exact forced-command guard remains.
No new general write route, external credential or production authorization change.

**224 root tests PASS**, including22 new snapshot route/access/compatibility checks;
**5 snapshot/maintenance package tests PASS**, including two identical synthetic
committed-source builds, member hashes, licenses/notices, import/help and privacy checks.
The initial snapshot collection error was a reserved pytest parameter name, corrected
locally before the passing run. The earlier124 other host tests retain their recorded
PASS plus one optional native skip; they are not counted as a new execution here.
These are source/fixture gates, not installed or production-candidate package claims.

Remaining: gateway reader, renewal controller/transport pins and configuration,
committed-source coherent artifacts, all active/staged route proofs and the coordinated
production procedure. No production migration, pause, restart, floor operation, paid,
Android, readiness or canary action by this checkpoint. Material observations must be
refreshed for any future permit. READY_FOR_OWNER_LIVE remains false.

### Gateway secure reader and committed-source capsules

Snapshot checkpoint `ff792db15e03690c977b2bdb154ab6b56d48abaa` is pushed; remote SHA
verified. The tracked gateway credential-loader file is byte-identical to the retained
accepted gateway source at entry (hash782bb9cd43ff2c4668efcbfef5aebdef8b29e2f8bb4b9cd5686754baebbc7732).
The narrow reader change admits the canonical root-owned group-read contract only
through a descriptor-based guard: secure ancestry, exact parent/file metadata,
no symlink or hardlink, no nested mount, no actual xattrs or unsupported policy flags,
bounded read and file/parent identity rechecks. Existing owner-private loading remains
for the explicit rollback route; no automatic path fallback or directory writer is added.
Other target platforms fail closed on this new group-read mode; no client build or
desktop feature/release work is performed.

Qualification uses the accepted gateway's Go1.26.1 toolchain, cached pinned dependencies,
an isolated root container without external network, and fresh disposable Family TLS
fixtures. **12 focused native tests with26 subcases PASS**, covering reader read-only
access, unrelated publisher denial, negative metadata/link/xattr inputs, mount-boundary
rejection, Family TLS initialization/reload, and existing mTLS/binding/lease controls.
The initial local guard rejection came from overlayfs's xattr sizing probe reporting
space for hidden internal entries while the actual name list is empty. The guard now
checks the bounded **returned list**, as the Python reader does; actual xattrs/ACLs remain
rejected and are exercised negatively. No production permission was weakened.

Two byte-identical builds of each unbound Python capsule from the exact snapshot commit:

| Capsule | SHA256 | Bytes | Members |
| --- | --- | --- | --- |
| Bounded maintenance | `9afd6a7903bf88b98be4f5247697935e904942d780fe5e954049152fd60994f0` | 201792 | 26 |
| Canonical snapshot | `49e91005fdad21ba71b20d233fe042a3968b87d5dba2a8b188a0d581416f61cb` | 167573 | 26 |

Exact member/manifest hashes, import/help, absent operation permits/production config,
privacy and licenses/notices PASS. These are retained **unbound intermediate artifacts**,
not the historical maintenance package and not a permission to deploy partially.
Gateway executable and renewal controller/node artifacts remain to be assembled and
qualified as a coherent set with fixed route/source pins. No new production binary,
locator, permission, reader group, backup, timer pause, restart or floor operation.
The recorded live observation remains time-bounded; fresh production preflight is still
required. Same checkpoint, no migration acceptance, no owner phone procedure.

### Renewal fixed-route source and deterministic package contract

Gateway reader checkpoint `c309bff9f267bf5250495a3c1ca8e777af52cec8` is pushed and its
remote SHA verified. The accepted renewal modules now resolve SSH endpoints, exact
remote command, reader service allowlists and health targets from fixed root-controlled
configuration rather than embedded deployment details. Missing routes fail closed;
there is no historical default. The forced endpoint and RPC envelope stay exact, SSH
uses pinned key/known-host paths and strict checking, ignores ambient SSH config and
receives a clean environment. No action, target, unit or path is accepted from RPC input.

Node configuration requires the fixed service list; the original role-specific stop/
resume order, resume-intent guard, operation journal and source-pin checks remain.
Normal scheduled mode is still only credential renewal; floor reconciliation is not
added to that API. The directory publisher implementation/configuration is untouched.
Health reads derive their systemd object from the fixed timer, with exact unit escaping.

The new deterministic renewal capsule covers **all13 accepted source members**, exact
inventory hash, the shared profile API archive and its manifest hash. It contains no
production configuration, permit, key or operational endpoint, and carries licenses/
notices. Two identical synthetic committed-source builds, every member/hash, isolated
imports and controller/node CLI help PASS; missing source fails closed. This is a
package-construction gate, not an assertion that production controller pins changed.

Validation: **20 new fixed-route checks +27 existing renewal checks PASS**. The prior
optional native-compatibility skip was run separately using the accepted gateway source
and Go1.26.1: two existing synthetic identities remain compatible through authority/
credential renewal. It builds only the disposable validation executable, not an Android
or desktop client. **2 renewal packaging checks PASS**; the4 canonical renewal/store
integrations were rerun and PASS. Recorded affected Python test inventory is now
**376 PASS,0 skips**, plus the12 native gateway tests/26 subcases. No full historical
suite or production RPC was run. Fresh concrete fixed-config construction/route checks,
coherent committed-source artifacts and every live migration gate still remain.

### Exact renewal API provenance qualification

The preceding source checkpoint `643115451c0db9454dab3b76c05874d012b2b43c` is pushed
and remote-verified. A further read-only inventory found that both deployed renewal
nodes use accepted API archive
`e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7`, whose required
members match source `edca5447418141cb44c0706e26d1973d7defd397`. This is not the newer
paid-aware Friends API. The earlier synthetic package checks did not qualify that
live dependency; no package from that intermediate design was installed.

The renewal packager now hash-verifies and preserves all nine needed accepted API
members, with only the existing parser projection and the new shared profile store.
Unneeded old HTTP/client entrypoints are omitted; the library has an inert entrypoint
and no production configuration. Substituting current Friends API source fails closed.
Three deterministic/package/import/negative checks PASS. An isolated root container
also constructs the actual pinned NL node in a clean interpreter from the packaged
archive, verifies all13 source pins and canonical profile/directory/shared-lock routes,
and proves that the API imports come from the verified archive descriptor, not cached
repository modules. That check PASS; it performs no renewal promotion or live RPC.
Two initial fixture defects (missing private state directory and list/tuple expectation)
were corrected and rerun, without changing production-source guards.

Recorded affected Python inventory is now **378 PASS,0 skips**, plus the previously
qualified12 native gateway tests/26 subcases. Production routes, artifacts and all
mutation budgets remain unchanged. Concrete fixed configuration, coherent final
packages and the full coordinated live gates remain open; no READY claim.

### Accepted gateway source projection and privacy gate

Exact renewal API checkpoint `20ce0cbbdc57b7a366756fc9739589cbc34f24ad` is pushed and
remote-verified. Building the accepted gateway plus the canonical reader exposed an
operational endpoint embedded in the **accepted baseline binary itself**. The first
two byte-identical candidate binaries failed the required no-operational-endpoint
package gate. They remain private, uninstalled and unsuitable for deployment.

The bounded accepted-source projection now requires exact startup/service source
hashes and replaces only that embedded endpoint with an explicit fixed startup
argument. Enabled services without a valid fixed target fail closed; disabled services
cannot carry a target. Service names, loopback mailbox target and accepted external
target must remain unchanged in deployment configuration. No DNS/request-provided
target, new listener, publisher change or Friends restart is introduced. This source
projection applies to the frozen accepted gateway tree, not unrelated current client
source. The manifest records its base inventory and exact committed delta.

Three projection tests and one native fixed-service-map test PASS. The12 canonical
reader/TLS/lease checks (26 subcases) were also run against the actual frozen accepted
source with the narrow delta, not merely current repository source: PASS. Recorded
affected Python inventory381 PASS; native inventory13 tests/26 subcases. Coherent
rebuild/manifest/privacy checks and exact effective-argv route equivalence remain
required before any mutation. Production budgets are still entirely unspent.

### Coherent committed-source artifact qualification

Source `c9c0a4de55f455e0788e7b519383c0cb0743fc96` is pushed and remote-verified.
Each coherent artifact was built twice byte-identically; all manifest/member hashes,
required import/help checks, absence of production configuration/credentials and
licenses/notices PASS. No release tag, catalog publication or installation.

| Artifact | SHA256 |
|---|---|
| Renewal source/API capsule | `c2ce2b01ac15cbb553692579e7a03b6bc7ad97f2159906ed884c3fda490a40c0` |
| Canonical snapshot | `6dd51ead36a977abd4e6afee978d81df229ac767a6315bc4b2347328bde60c84` |
| Bounded maintenance | `c134eb6b56f01a4a54829b73c3259ba15886f603726058cc5f29afd3778b2a2d` |
| Gateway binary | `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef` |
| Gateway archive with source manifest/notices | `a20f68ec89c05a5fafa5885cbc77e32bbf440239e5b0dc5bc79d5f52d734ea74` |

The renewal inventory is
`a9fbd201ae4a8b0db2eb81c65f878ba020861368ffabd2ea658ad443faa6a33f` and its exact
accepted-API-plus-shared-core archive is
`ab0bcbd06d4b5978da3aa5550fc305b7cfa78492c8b64870135087c51593efbd`.
The gateway manifest binds accepted source inventory
`33de05072f68097669a38ce3d41f378deecd62375c61d48e85150b6fb95a8580` plus the exact
committed seven-member reader/fixed-endpoint delta; publisher implementation unchanged.
The separate upstream exact-payload CRL helper source inventory was not changed;
its downstream canonical profile writer is the shared bounded maintenance action.

Additional parser14400/directory suite:97 PASS using disposable host-native validators,
not Android/client builds or live challenge/fetch. Fresh read-only production observation
has8537s minimum material headroom, CRL27218/floor27088, unchanged owner binding/certificate
scope, zero paid ledger/cohort and active successful renewal schedule. A suitable existing
reader group covers the required readers; the gateway reader is also the existing
publisher and needs profile read access only. No group/account or production path changed.
All artifacts remain **unbound/uninstalled**, and all mutation budgets remain unspent.

### Private backups and inactive production staging

After a new read-only gate with7512s material headroom, validated root-private backups
and immutable inactive artifacts were created on both authorized gateways. RU backup23
files; NL backup34 files. Configuration, accepted source/API, service/timer definitions,
gateway binary/argv, snapshot authorization/wrapper, profile/directory bytes and original
metadata are retained privately. Every backup copy was read back and hash-checked.
No backup, configuration, key or material body is committed or uploaded to Django.

Backup manifest hashes:
- RU: `6a22e5819b245787587a81dd36897a7fd58851a7f0ba4e25bcebf2d7f0cb5cc1`.
- NL: `0d32fe35eb74522f79846143b63804baa9ff1332c65bad06b9438c9d03265b0a`.

Installed inactive artifacts pass exact source/package hashes and import/help smoke
under the production interpreter. **No active configuration changed**, no canonical
profile copy created, no timer paused, no gateway/Friends restart, no floor/CRL/paid/
Android/readiness action. Old accepted readers/writer remain authoritative together;
there is no partial migration. Existing reader group remains unchanged.

An initial private staging harness Path/string guard failed before its first write.
Read-only reconciliation proved both destination trees absent. The guard was corrected,
read-only prewrite checks passed, and staging then completed. This did not spend a
cutover, pause or floor-operation budget. Additional accepted-source publisher/cache/
timestamp checks:5 native tests with16 subcases PASS; no publisher source change.

Current classification: **COORDINATED_CANONICAL_PROFILE_STAGED_INACTIVE**, not READY.
Exact staged-config and rollback qualification, fresh quiescence, canonical copy,
single bounded reconciliation and coordinated cutover/final acceptance remain open.

## Split-boundary writer inventory — 28 October

**OWNER_CANARY_BOUND_READONLY / BLOCKED_PROFILE_WRITER_CONFLICT /
LIVE_WRITES_NOT_RUN.** Continuation from `9205588dbe33a1e94ad862a425d335c0ff76bc94`,
not a new checkpoint. [Sanitized receipt](2026-10-28-android106-beta-0-canary-split-boundary.json).

The required writer gate fails **before source redesign or layout migration**.
The fresh read-only inventory establishes an existing legitimate credential-renewal
writer of the exact NL profile, distinct from the proposed bounded maintenance route.
Its RU timer is active/waiting, the latest scheduled service result is successful,
and the fixed controller configuration explicitly approves the leaf/CRL schedule.
The deployed transport uses the existing `CREDENTIAL_RENEWAL_RPC` branch of the
forced command, whose root helper is authorized by the existing exact rule. No RPC,
renewal evaluation, stage, promotion or restart was invoked by this checkpoint.

| Material / route | Observed reader or writer |
|---|---|
| Profile | Existing authorized renewal node stages and atomically replaces it |
| Profile reader | Running gateway references the same live profile in its effective argv |
| Directory | Existing publisher exports via sibling temporary file and rename |
| Snapshot operation | Reads profile and directory; read-only snapshot contract unchanged |
| Existing lock | Present and unchanged; no new lock or lock substitution |

The snapshot **operation** remains read-only. This does not imply that the entire
forced-command endpoint lacks the separately authorized credential-renewal RPC branch.
The relevant source path is `dispatch` → `stage` / `promote` → atomic `replace` of
the configured live profile. All13 node source hashes match the fixed node inventory
and the RU controller's expected NL source identity:
`c67332cfff9aeafd90690c13518f55a75ef9687ceadb464624263657ff005ff2`.
The deployed dispatcher SHA256 is
`4052d7dc0deda7cd5d50df044ed9abb59e0dfc5102162345066273ca7f82f6b0`;
profile-writer implementation SHA256 is
`02fec6882af79210cdf949e892f132f0bb24088bf8b13faddbe160f0fbf8f588`.
The root helper, gateway source and transport hashes are retained in the sanitized
receipt; private configurations, paths, account data and authorization remain private.
No open material descriptors were observed at the bounded FD readback; this is not
evidence of no writers because short-lived writers open files only during operations.
The inspected node owner/plan/files transaction markers were absent at that
observation; this is not a claim about every coordinator journal.

Moving only snapshot and maintenance to a copied profile would leave the existing
renewal writer and gateway reader on the old profile. The required conclusion that
only future maintenance writes the profile is therefore false. Per the owner stop
policy, **BLOCKED_PROFILE_WRITER_CONFLICT** is the result; layout separability is
NOT_QUALIFIED, not an invented claim that a coordinated redesign is impossible.
Do not disable renewal or repoint its configuration under this checkpoint.

No product source/test/package change, layout migration, route switch, secure-profile
creation, safety backup, permit, temporary credential, maintenance transaction or
rollback. Shared parent mode/owner/group, publisher permissions/configuration, current
profile/directory/lock bytes and metadata, snapshot authorization and running services
remain unchanged. Maintenance budget0/1; no profile/RU/CRL/paid/readiness/Android writes,
no restart/reload. Accepted owner-aware source73ae964 and historical package75dd8dec
were audited unchanged, including manifest/member hashes; no package was used in
production and no replacement package was built. Source suites are NOT_RUN because
the explicit pre-source gate stopped the work, not reported as a new source PASS.

Fresh entry already observed coherent signed RU/NL CRL27216 and RU sequence27216,
advanced from the prior27215 receipt by activity outside this checkpoint. Floor27088
and current CRL/directory hashes are unchanged between this checkpoint's fresh
before/after observations. Final readback minimum material lifetime13266s; signatures,
issuer/bindings and actual parser PASS. Ledger0/0, cohort0/10, owner certificates0,
certificate horizon CLEAR, binding unchanged, accepted exact106 retained (no new
phone observation/lookup/status call). Protected registry/policy/publisher and owner
certificate/readiness fingerprints are unchanged; ordinary unrelated chat/readiness
activity is disclosed separately rather than claiming whole-DB equality.
Read-only monitoring remains active; no production mutation was performed.

Validation: fresh private inventories/strict JSON, exact source and historical
package member hashes, private harness syntax, privacy/selector scan, Markdown links,
selective staged scope and whitespace checks. No full historical suite or platform
build. Existing unrelated work is preserved outside the commit.

NEXT: separately authorize a coordinated profile-path/ownership design including
the existing credential-renewal writer and gateway reader while preserving the
publisher's directory path and strict guards. No layout correction, renewal change,
phone instruction or stage0 activation automatically. READY_FOR_OWNER_LIVE is not met.

## Secure parent classification — 28 October

**OWNER_CANARY_BOUND_READONLY / BLOCKED_MATERIAL_PARENT_HARDENING_UNSAFE /
LIVE_WRITES_NOT_RUN.** Continuation from `bc6ea113b5f1e42e0faee6ad4c12987dead4befe`,
not a new checkpoint. [Sanitized receipt](2026-10-28-android106-beta-0-canary-parent-hardening.json).

Fresh read-only classification is exactly **B: GROUP_WRITE_REQUIRED_BY_LEGITIMATE_WRITER**.
The material parent owner differs from the effective owner of the running gateway
that exports the live seed directory. That non-root process belongs to the parent's
write-enabled group, has no effective DAC-override capability and uses the exact live
directory as its configured export target. Parent ACL/xattrs/unsupported flags are
absent, there is no world write or alternate owner-write permission for this process,
and upper-ancestor/mount/canonical-path checks pass. The private inventory retains
account/group membership, process credentials and security context without publishing
those identifiers. Profile, directory and existing lock remain private regular
single-link service-owned files. The read-only snapshot command is a separate reader,
not evidence that the directory has no other legitimate writer.

Provenance of the required writer is verified independently of current-main assumptions:

| Evidence | SHA256 / result |
|---|---|
| Running executable = retained accepted binary | `96754942e7518233bc702277d860b0c9b740fb7553c9742b2ae642a0746fe367` |
| Retained source inventory, all279 members verified | `33de05072f68097669a38ce3d41f378deecd62375c61d48e85150b6fb95a8580` |
| Gateway entry source | `aff554747a2c1a2f50e68c6a94b5299ede76c18442462e0dd7ae0f4436d34552` |
| Directory-cache source | `79ab44cd607742080b53a78d46f8a0732dc201af9db15407aa2092731e110de5` |
| Seed-manager source | `2e465921849c3aaa9832512417be3c9bd9de1f8fabc4330aa772aa5497dbed2b` |

The running argv enables directory export. In the verified source, the publisher
calls `Cache.Store`; this creates a sibling temporary file and renames it over the
live directory export. Both require parent write/execute permission. No Git revision
is embedded in this binary; provenance is the matched retained binary/source inventory,
not an invented current-main build claim. Relevant unit/drop-ins, process identity,
deployed maintenance source and snapshot forced-command inventories were inspected
privately. A required non-root writer is sufficient to disprove safe category A;
there is no claim to discover arbitrary privileged programs outside this bounded audit.

An isolated, network-disabled synthetic DAC probe confirms atomic export succeeds
with the group-write bit and fails with permission denied after removing only that
bit. This changes disposable fixture permissions only; production chmod was never
attempted. One initial read-only inventory probe had an escaping error and failed
before execution; its corrected remote source was syntax-checked before successful
readback. No source guard was modified or bypassed.

Per the owner decision, category B stops before safety backup and any permission
change. Parent correction0/1, maintenance operation0/1, permission rollback0;
no fixed configuration, bound permit/package, temporary credential, CRL generation,
RU mutation, paid event, readiness call, Android action or service restart/reload.
No rollback is needed because nothing was applied. The accepted maintenance source
`73ae9645564b0d4e2891b42d532fede1954de109` and unbound package75dd8dec remain exact;
the historical root-only package remains forbidden. The accepted369 affected tests
were not rerun for this documentation/read-only checkpoint. New checks are immutable
artifact/source audit, isolated DAC proof, strict JSON/privacy/link/scope/whitespace
validation; no full historical suite or platform build.

Final authoritative readback: ledger0/0, cohort0/10, owner certificates0, retained
binding unchanged and no repeated lookup/status call. Existing authenticated Android106
acceptance is retained, not a new phone observation. CRL27215, RU sequence27215,
NL floor27088 and exact signed CRL/directory hashes remain unchanged. Signatures,
bindings and actual parser pass; minimum material lifetime6315s at final readback.
Parent/live bytes and metadata, owner-specific certificate/readiness state, protected
registry/policy/publisher state, Friends/NL services and snapshot authorization are
unchanged. Unrelated concurrent chat/readiness activity is reported separately, not attributed
to this checkpoint. Read-only monitoring remains active; NL registry remains explicitly
UNAVAILABLE rather than zero. READY_FOR_OWNER_LIVE is not reached.

NEXT: separately authorize review of a secure material-layout/writer boundary that
preserves the live directory publisher while satisfying the committed maintenance
guard. Do not simply remove its needed group permission, change ownership or weaken
the guard. No automatic correction, app-open instruction or stage0 activation.

## Owner-aware fresh production preflight — 28 October

**OWNER_CANARY_BOUND_READONLY / BLOCKED_MAINTENANCE_ROUTE_UNAVAILABLE /
LIVE_WRITES_NOT_RUN.** Same BETA-0-CANARY-1; source gate DONE, production floor
reconciliation NOT_RUN. [Sanitized receipt](2026-10-28-android106-beta-0-canary-ownership-maintenance.json).

Source commit `73ae9645564b0d4e2891b42d532fede1954de109` pushed; remote SHA verified.
Two independent unbound builds from that exact commit are byte-identical:

| Property | Result |
|---|---|
| Binding / permit / production configuration | unbound / null / absent |
| Members / bytes | 25 / 174944 |
| SHA256 | `75dd8dec59062a6cb73c785dcd8e539b23ab03260fcd48898bb9330cb1ca9f6c` |
| Manifest SHA256 | `3a3a6d5bc94ccd979a31e8524fbd350622617de201a653fbac4a305c3f325cd6` |
| Manifest/member hashes, deterministic metadata, import/help | PASS |
| Operational invocation without a permit | DENIED / INVALID_PERMIT |

The historical a39ea951 package remains byte-identical and prohibited for production.
No bound maintenance package or time-bound permit was built in this continuation.

Fresh read-only production observations at three points across126s confirm the
accepted Friends process and source/argv/unit/runtime/health baseline. No repeat
owner lookup/status; the private binding remains unchanged, exact106 is the prior
accepted authenticated observation. Paid ledger0/0, cohort0/10, owner certificates0
and scoped readiness unchanged. RU sequence/CRL and NL embedded CRL27215 match;
NL minimum remains27088. Exact CRL hash
`43210026e66566ff8b7ebf3695e2485fcfeb3e166cb347ffa3be123998b18b15`, directory hash
`ceb4f6baab137b8d079f2cfc88c3a4a9cfce676d32505629f505bd9d6a3bac31`.
Signature/issuer/bindings/actual parser PASS; minimum remaining material lifetime7667s
at final readback. This observation is not a lasting material-freshness guarantee.

**Blocking predicate: MATERIAL_PARENT_GROUP_WRITABLE.** Profile, directory and the
existing synchronization lock have the expected service ownership, private file
modes, single links and no unsupported extended metadata. However, the immediate
material parent permits group writes. The committed guard requires non-group/world-
writable parents and correctly rejects it. Pinning its current metadata does not
make this unsafe mode acceptable. The initial private observer also tested an extra
snapshot-account equality assumption; it was replaced by explicit service-owner
metadata qualification without changing the source guards. The final localized
failure is the parent-write predicate, not file ownership or missing-lock ambiguity.
No numeric owner/group values, account names or operational paths are published.

Stopped before fresh backup, fixed config installation, write permit, temporary key
or production transaction. Attempts0/1; rollback not needed; no active maintenance
credential was installed. No chmod/chown of live objects or parents, no CRL generation,
sequence change, RU write, paid event, readiness call, Android action, restart/reload
or snapshot-route mutation. Final readback proves protected registry and owner scope,
service/process and snapshot configuration, material bytes/floor and metadata unchanged.
Only unrelated concurrent chat challenge/sequence activity changed; global table
identity is not claimed. The read-only monitor remains active and current; NL registry
is explicitly UNAVAILABLE, not zero.

NEXT: separately authorize a secure material-parent boundary correction or an
alternative reviewed route preserving the trust requirements. Do not weaken validation
or modify live ownership/permissions automatically. Repeat fresh preflight afterwards.
READY_FOR_OWNER_LIVE is not reached; no instruction to open the app or reply ГОТОВ.

## Owner-aware maintenance source gate — 28 October

Continuation from `8acd6b0a242685d18da6ec79a72ed2f57493b775`, same checkpoint.
**OWNER_AWARE_MAINTENANCE_SOURCE_READY / LIVE_WRITES_NOT_RUN.** The historical
package `a39ea9515f7a7ed3b674322a6d4e007d2a230b3f90366390a28e0c92e81b114c`
is retained unchanged and must not be used against service-owned material files.

The fixed private configuration now separates root-private control objects from
explicitly pinned live profile, directory and existing lock metadata. Exact outer
fields are profile/directory/sync_lock/operations/journal_key/package_sha256/
operation_id, each material's uid/gid/mode, and material_boundary. To pin the boundary
without adding outer fields, material_boundary is a strict descriptor containing
path, uid, gid, mode, device and inode. These are private configuration fields;
no production values belong in this report or package. No caller/environment override.
Modes are strict integers; live files and lock must be private, regular, single-link,
non-symlink files. Secure root ancestors, a pinned root-or-service-owned boundary,
non-writable parents and no descendant mount/symlink escape are required. Operations
are outside that boundary and remain root-private. The lock must already exist;
maintenance never creates or replaces it.

Atomic control writes remain root-private. Profile replacement creates an exclusive
same-directory temporary file, assigns the pinned service metadata before writing,
fsyncs, rechecks content/metadata/directory/window/journal, replaces and reads back.
Existing targets are never chowned/chmodded or written in place. Unsupported xattrs
(including ACLs) and file flags are rejected, not silently stripped. The automatic
extent-layout flag is not treated as a user access attribute. Rollback uses the same
metadata-preserving primitive. MAC-protected journals bind the configuration and
material/parent metadata, directory and lock identities. Before/target bytes with
wrong metadata fail recovery without repair. Root-owned fixtures remain supported
only with explicit matching configuration. Crypto, permit, profile, idempotency,
snapshot read-only and paid-state semantics are unchanged.

New typed guards: MATERIAL_METADATA_MISMATCH,
MATERIAL_EXTENDED_METADATA_UNSUPPORTED, MATERIAL_TEMP_METADATA_FAILED and
MAINTENANCE_ROUTE_UNAVAILABLE. Sanitized responses expose no owner metadata.

Validation:124 maintenance tests PASS in a root-isolated, network-disabled container
with disposable ownership fixtures;245 package/restricted-sync/gateway/exact-payload
CRL/directory/paid-readiness tests PASS,33 existing native/extended-parity deselections.
Total369 PASS, including the previous320 affected tests and49 ownership/schema
regressions. Packaging tests run in the local locked environment because the isolated
console image has no Git executable; no gate is skipped. Production, paid/canary,
Android and service restart actions NOT_RUN. The new committed-source package must
pass two independent identical builds before production preflight begins.

## Fresh service baseline and maintenance ownership boundary — 28 October

**OWNER_CANARY_BOUND_READONLY / BLOCKED_MAINTENANCE_ROUTE_UNAVAILABLE /
LIVE_WRITES_NOT_RUN.** Continuation from `d1fec6420cc534f12bbc5965087fa54db1112c95`;
no new task ID. [Sanitized receipt](2026-10-28-android106-beta-0-canary-maintenance-baseline.json).
The earlier PID-only stop below is historical and superseded by this owner-authorized
baseline adoption. Source `7ce43ead7fdaace18cb1730e8d0e6a04f881dcb0` and its unbound
package `a39ea9515f7a7ed3b674322a6d4e007d2a230b3f90366390a28e0c92e81b114c` remain
unchanged; no source correction, rebuild or deployment was performed.

### Friends baseline accepted

Classification: **CLEAN_RESTART_ACTOR_UNRESOLVED**. Adoption:
**FRESH_FRIENDS_BASELINE_ACCEPTED_WITH_UNATTRIBUTED_CLEAN_RESTART**.
Three observations scheduled at0/60/120s (123.74s including final read overhead)
retain PID2744086, start4913682774688 monotonic microseconds, InvocationID, NRestarts0,
active/running state, exact paid-aware archive, effective/running argv and environment
fingerprints. All7 fragment/drop-in file hashes/sizes/numeric modes, runtime packages,
service user/group/working-directory and sole listener ownership match accepted CP2
configuration. Health PASS; no pending unit job or daemon reload required.

Attribution was bounded to a240s window around the current process start. Unit and
manager journal reads and boot-history retrieval timed out; current boot ID was
observed privately. Available package/unattended-upgrade logs and retained deployment
receipts contain no matching entry. No raw messages, unrelated shell histories or
command bodies were exported. Actor and a complete absence of historical tracebacks
are **not established**. Stable protected state and no contradictory current failure
satisfy the owner's adoption rule; PID difference alone no longer blocks work.
One local harness comparison initially differed only in octal-mode string spelling;
numeric comparison confirmed all hashes/modes unchanged. It was not production drift.

### Fresh authoritative material state

- SQLite mode=ro/query_only/read transaction: integrity/FKs/exact paid schema PASS;
 subscriptions0/events0, cohort0/10; bound owner has no paid rows and no certificates.
 Certificate horizon CLEAR; existing binding unchanged; no new selector lookup/status.
- Current RU CRL number and stored sequence27215; NL embedded CRL27215, minimum27088.
 Exact signed RU/NL CRL SHA256
 `43210026e66566ff8b7ebf3695e2485fcfeb3e166cb347ffa3be123998b18b15`.
- Exact RU/NL directory SHA256
 `ceb4f6baab137b8d079f2cfc88c3a4a9cfce676d32505629f505bd9d6a3bac31`.
 Issuer/authority signatures, family/gateway bindings and actual14400s parser PASS.
 Monotonic coherent rotation since historical27211 is accepted read-only; no old permit
 or historical payload is reused. **CRL_FLOOR_RECONCILIATION_REQUIRED**,27088→27215.
- Final readback remaining lifetimes: issuer/authority6956290s, RU CRL10156s,
 RU directory10168s, NL authority6956292s, NL CRL10158s, NL directory10169s. All exceed720s.
 Freshness alone does not establish READY_FOR_OWNER_LIVE while the route is blocked.

### Route unavailable without an ownership-contract correction

Both current NL profile and directory are regular files with mode0600 and the same
**non-root service owner**. The accepted maintenance `Configuration.read()` requires
`st_uid == owner_uid`; the production loader constructs `Configuration` with default
owner0, and offers no authorized owner override. Its atomic replacement creates a
root-owned file. Installing that exact package cannot preserve the current ownership
contract simply by supplying the fresh hashes/permit.

Backup preparation therefore stopped at the live-file ownership check **before**
creating the remote backup directory, fixed configuration, bound permit/package,
SSH key or transaction. Follow-up read-only proof confirms those remote paths absent.
No chown/chmod, source edit, guard weakening, account change or snapshot substitution
was attempted. Private local planning evidence is retained; production apply attempts
remain **0/1**. Rollback NOT_REQUIRED; credential removal NOT_APPLICABLE_NOT_INSTALLED.
This is not MATERIALS_INVALID or a renewed Friends PID blocker.

### Preservation, validation and next boundary

After-readback PASS: profile/directory/CRL bytes and floor unchanged; snapshot archive,
authorized-key configuration, forced-command configuration and current NL service
unchanged during this checkpoint. Friends accepted baseline unchanged. Protected
devices/invites/support/grants/revocations/admission/publisher/paid ledger and RU
sequence preserved; owner certificate/readiness fingerprints unchanged. Unrelated
chat challenge/sequence activity is disclosed; no global database-equality claim.
Read-only monitoring timer active, fresh RU/NL snapshots imported; NL registry remains
UNAVAILABLE, not0. Local console remains synthetic-only. No new production write
credential, paid event, readiness call, CRL generation/delivery, Android action or restart.

Only documentation/sanitized evidence changes are committed. Strict JSON, private-data
scan, links, staged scope and whitespace checks PASS; private read-only harness syntax
PASS. Accepted320 affected tests/33 native deselections are historical source evidence
and were not rerun for this operational/documentation continuation. No full suite or
platform build was run; existing unrelated changes remain unstaged.

**STOP. NEXT — separately authorize an owner-aware maintenance source contract**:
validate the exact service-owned live files and preserve their owner/group/mode through
replacement/rollback, while retaining root-private configuration, key and journal and
all existing cryptographic/path guards. Do not change live ownership to fit the package
or disable the guard. Repeat fresh preflight after that source gate; no automatic
maintenance retry, material refresh, stage0 or phone instruction.

## Bounded maintenance package and preflight stop — 28 October

**OWNER_CANARY_BOUND_READONLY / BLOCKED_MAINTENANCE_PRECONDITION_CHANGED /
LIVE_WRITES_NOT_RUN.** Same checkpoint. Input main644f656; source commit
`7ce43ead7fdaace18cb1730e8d0e6a04f881dcb0` pushed and remote SHA verified before
packaging/preflight. [Sanitized receipt](2026-10-28-android106-beta-0-canary-maintenance.json).
The source gate below is historical preparation, not an independent active NEXT.

### Exact unbound package

- Source `7ce43ead7fdaace18cb1730e8d0e6a04f881dcb0`;25 members,164110 bytes.
- SHA256 `a39ea9515f7a7ed3b674322a6d4e007d2a230b3f90366390a28e0c92e81b114c`.
- Manifest SHA256 `1bf017a48703e9f62cc0ed1a2651d7b23c9df09f9f2c11d8692f1efb33d818cb`.
- Two independent builds byte-identical; binding=unbound, operation permit=null,
 production configuration absent. Exact committed members/source projection hashes,
 deterministic ZIP metadata, private artifact permissions and import/help/manifest
 smoke PASS. Unbound operational invocation returns INVALID_PERMIT without config/DB access.
- Full member hashes are in the receipt. No production bound package, permit, key,
 profile/directory, device selector or host configuration is present. Existing accepted
 lookup and exact-payload CRL artifacts remain unchanged and were not rebuilt.

### Fresh read-only preflight and mandatory stop

Fresh RU SQLite mode=ro/query_only/read transaction: integrity/FKs/schema PASS;
subscriptions0/events0, cohort0/10. Paid-aware archive remains
`dcd769986a1da7cb1662c0f73d18a88e9f73485a977db937ca5b1428c1fd1029`, effective/running
argv match; publisher/admission unchanged. Service active/running, liveness PASS,
NTP/NTPSynchronized=yes. However, its process identity no longer matches the accepted
read-only baseline:

| Service observation | Accepted baseline | Fresh preflight |
| --- | --- | --- |
| MainPID | 1002753 | 2744086 |
| ExecMainStartTimestampMonotonic (microseconds) | 4877589183478 | 4913682774688 |
| NRestarts | 0 | 0 |

This proves a different process/start identity; NRestarts0 does **not** prove no
intervening restart. Cause/actor are **not established** by this read-only observation.
No restart, reload or deployment was issued by this checkpoint. We did not accept
the new process as a replacement baseline or retry the preflight automatically.

Per the owner stop policy: **MAINTENANCE_PRECONDITION_CHANGED**, reason
FRIENDS_SERVICE_IDENTITY_CHANGED. No subsequent NL execution/material inspection,
owner certificate recheck, backup, production permit/package or temporary credential
installation. Therefore the earlier owner horizon and NL material/floor observations
are retained as historical input, **not claimed freshly revalidated**.

Maintenance apply attempts **0/1**; reconciliation **NOT_RUN**; rollback **NOT_RUN**
(nothing written). Last accepted floor27088, intended target27211; there is no new
post-write floor observation and no CRL_FLOOR_ALIGNED acceptance. No maintenance key
was generated/installed, so removal is NOT_APPLICABLE, not a fictitious removal PASS.
No new production write credential exists from this checkpoint. No CRL generation/
delivery/number allocation, RU mutation, subscription/event, readiness call, Android
action or application deployment. Global production equality is not claimed across
the intervening process change. Existing administrative access was used read-only.

### Validation and next boundary

320 affected tests PASS,33 explicit native deselections; deterministic package and
syntax/strict JSON/privacy/link/staged-scope/whitespace gates PASS. Only bounded
maintenance source/tests and sanitized docs are committed; unrelated existing work
remains unstaged. No full historical suite or platform build was run.

**STOP. NEXT — review the intervening Friends service change and explicitly accept
a fresh production baseline before resuming read-only preflight.** If authorized to
continue, exact NL materials, lifetime, owner horizon and zero ledger must all pass
again before backup/permit/credential installation. No automatic rebind, refresh,
transaction retry or phone instruction. Stage0 and owner Connect remain NOT_RUN.

## Bounded NL maintenance source gate — 28 October

Input main `644f65617f6d4d26e34954e1e8c0704e9811156c`; same checkpoint, no new task ID.
**MAINTENANCE_SOURCE_READY / PRODUCTION_RECONCILIATION_NOT_RUN.** This source gate
does not assert production freshness, install a credential or reconcile the floor.

### Separate bounded contract

New [maintenance module](../../control/friends/restricted_maintenance.py) and
[committed-source packager](../../scripts/package_restricted_maintenance.py), with
[transaction tests](../../tests/test_restricted_maintenance.py) and
[packaging tests](../../tests/test_package_restricted_maintenance.py).
Existing restricted-sync, snapshot archive, parsers, paid backend and Android source
are unchanged. The existing14400-second validation limit is not widened.

- Exact permit field set, strict integer/hash/operation checks, duplicate/nonfinite
 JSON rejection and server-time execution window<=300s. One operation per immutable
 package; caller cannot choose action, path, payload, floor, number or operation.
- `reconcile_current_floor` requires identical incoming/embedded CRL bytes and number;
 only minimum_crl changes semantically. Other profile fields and exact directory
 bytes are preserved. No CRL generation/sequence allocation or registry access.
- `apply_exact_crl` accepts only a permit-bound number strictly above both previous
 CRL and floor, with signature/issuer/time/lifetime/directory checks before mutation.
 This action is synthetic-only in the present authorization.
- Root-owned fixed external configuration; no CLI/environment path override. The
 package has a public fixed loader convention, but contains no production configuration,
 actual operational paths/host, credentials, profile, directory or device binding.
- Root-private0700 operation directory,0600 files, owner/parent/symlink/hardlink checks,
 existing profile sync-lock, exact before/target/request/permit backups, atomic fsync
 journal with HMAC. States PREPARED/APPLYING/COMMITTED/IDEMPOTENT/ROLLED_BACK/UNKNOWN/
 CONFLICT. Partial/pre-existing operations are never silently regenerated or rebound.
- Profile stage fsynced on the same filesystem, state/window CAS checked again before
 APPLYING/atomic replacement, then validated readback. Failure after replacement
 restores exact backup bytes; rollback failure or unknown conflicting state stops.
 No overwrite of a concurrent unknown profile. No directory or service mutation.
- Production configuration fixes maximum apply attempts=1. Exact committed replay
 or readback of an already installed target does not apply again. A synthetic-only
 two-attempt fixture proves a retry of a known untouched before-state; replace-started
 uncertainty is never treated as proof of no write. Production does not enable that retry.
- Exact private response maps to the existing paid CRL helper's `TrustedReadback`;
 public sanitization omits directory bytes, CRL/profile, raw operation ID and secrets.
- Temporary credential-line construction requires a fixed Python/package command,
 timeout, no PTY/forwarding/agent/X11/user-rc; caller SSH commands are rejected.
 Removal preserves other authorization lines exactly. These are source/synthetic
 policy proofs, **not** a claim that a production key has been installed or removed.

### Source validation and package boundary

**320 affected tests PASS;33 explicit native/Android parity deselections.** Selection:
maintenance/package tests, exact-payload CRL helper/package, restricted gateway/admin,
paid readiness and directory/timestamp tests. The retained exact snapshot archive
`0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450` was imported only
into disposable synthetic fixtures: snapshot response fields preserved, mutation
request denied, snapshot remains read-only after synthetic floor reconciliation.
The13-value lifetime matrix retains maximum14400s; no native build or full suite.

Deterministic unbound and bound-*synthetic-fixture* packages are covered by tests,
including manifest/member hashes, source-only projection provenance, fixed ZIP times/
modes, import/help, null-permit action denial and arbitrary-command rejection. Source
commit packaging will be built twice independently and recorded in the next receipt.
No production bound permit exists. Existing lookup/CRL helper artifacts are not rebuilt.

NEXT within this authorization: commit/push source, exact unbound package, then fresh
read-only production preflight. A changed profile/floor/hash, expired material, ledger
change or other failed gate means STOP before backup/credential/transaction. Never
refresh or rebind automatically. No paid enrollment, new certificate, phone action,
CP2 deployment, restart/reload, or actual canary stage is authorized here.

## NL parser provenance and read-only material review — 28 October local

**OWNER_CANARY_BOUND_READONLY / BLOCKED_CRL_PROFILE_COMPATIBILITY /
LIVE_WRITES_NOT_RUN.** Input main `f499bdf80eec2022c3b58cd1db4ebfb93cafd7ed`.
Same checkpoint, documentation/evidence only; no product source or parser-limit change.
The single parser classification is **NL_VALIDATOR_ONLY_DRIFT**. The previous
MATERIALS_INVALID result below came from an auxiliary archive, not the actual forced
command, and is superseded by this exact-path review. Historical evidence is retained.
[Sanitized machine-readable receipt](2026-10-28-android106-beta-0-canary-nl-readonly.json).

### Execution-path and source provenance

Effective SSH configuration, authorized forced command and its exact exec argv were
resolved read-only. No alternate SSH ForceCommand/AuthorizedKeysCommand overrides it.
The forced command is a short-lived per-connection Python3.14.4 process; the separate
bootstrap service remains active, PID2491265/NRestarts0, unchanged start identity.
Configuration, argv, private paths and raw generic archives remain private. No forced
command was invoked against production; only its exact parser source was imported
into isolated read-only probes. The earlier helper and real gateway use different
archives: **NL_VALIDATOR_EXECUTION_PATH_DRIFT**.

| Role | Size / members | Archive SHA256 | Directory maximum |
| --- | --- | --- | --- |
| Actual forced-command gateway | 26854 / 18 | `0120dad028ead353b8b83a600538f3e578b2b46ddf871bf16e97529f9449f450` | 14400s |
| Previous auxiliary directory validator | 26406 / 18 | `f6aa8859ab716383bf207b2ff7b302687692832b2ccb410f1aef0ada0793a9c9` | 3600s |

The receipt contains exact member/module hashes. Actual gateway's `restricted.py`
and `restricted_sync.py` did not match exact Git blobs in the searched all-ref file
history: provenance is **exact installed generic source**, not an invented source
commit. The old parser/sync modules and shared catalog matched verified Git blobs.
Actual `directory`, `timestamp`, `timestamp_ns` function source hashes **all match**
current accepted main. `MAX_TEST_LIFETIME=14400` is a local constant, not imported or
replaced; predicate is `0 < expires-issued <= MAX_TEST_LIFETIME * 1000000000`.
The auxiliary parser has a literal3600s bound. Its absent exported constant must not
be confused with actual gateway behavior. No `strings`-only inference was used.

### Exact timestamps and synthetic boundaries

Same directory SHA256 `0aa55347adaa2fbd977b6c98b812ac2443a95c6f132f030785c33c5617c3a22a`,
same family/gateway bindings and explicit `now_ns=1793145321597295579` for all three
isolated parser calls. Current accepted function source was extracted without changes;
the two installed implementations were imported from exact verified archives.

| Field | Exact value |
| --- | --- |
| issued_at | `2026-10-27T23:23:11.48947495Z` |
| expires_at | `2026-10-28T03:06:33.229230378Z` |
| issued_at nanoseconds | 1793143391489474950 |
| expires_at nanoseconds | 1793156793229230378 |
| Delta nanoseconds | 13401739755428 |
| Delta seconds | 13401.739755428 |

All parsers preserve these exact nanoseconds. Current/actual parser PASS; auxiliary
parser rejects `time / invalid_lifetime / expires_at`. Fractions1–9 digits and zones
Z/signed HH:MM are supported. The old implementation passes a fractional timestamp
through datetime, then reconstructs nanoseconds from the original fraction; the current
one parses whole seconds and adds the exact fraction. Neither truncates this directory.
The earlier13402s observation subtracted individually floored display endpoints;
it was not the exact lifetime. **TIMESTAMP_PRECISION_MISMATCH is not established.**

Disposable, network-free synthetic matrix:899/900/3599/3600/3601/10799/10800/10801/
13399/13402/14399/14400/14401 seconds, identical types and synthetic bindings only.
All three parsers ran with fixed `now_ns=1800000000123456789`; additional maximum−1ns,
maximum and maximum+1ns checks confirm exact limits. **48 checks PASS**. Current and
actual gateway accept through14400s; auxiliary through3600s. No production seed/join
URL was used in synthetic fixtures or emitted in evidence.

### CRL floor and the separate blocking contract

Profile embedded CRL27211 equals the observed installed CRL and RU current CRL;
RU stored sequence27211. SHA256 of both exact CRL payloads:
`b98c1012d045d4923e8d4242d597c0fd771c2357b10bfa898608c1868eb586c3`.
No separate NL CRL file was found at the inspected material location: the installed
source here is the profile-embedded payload, not an independent newer file. Authority,
issuer and signature checks PASS. Profile hash and minimum_crl27088 remain unchanged.
Neither CRL_PROFILE_BEHIND_INSTALLED nor CRL_MINIMUM_AHEAD is supported by these data.

Actual gateway code enforces `number >= max(previous_embedded_number, minimum_crl)`.
However, its only accepted request is `READ_ONLY_SECURITY_SNAPSHOT`; all CRL-write
requests fail **MAINTENANCE_TRANSACTION_REQUIRED**, before mutation. It validates
the embedded payload/directory and returns a snapshot, never updates minimum_crl.
Thus the owner's required "next exact accepted payload updates the floor" condition
cannot be satisfied by this command. **CRL_FLOOR_UNRESOLVED** refers specifically to
that forward-write/maintenance contract, not to unknown bytes or proven invalid
cryptography. **CRL_FLOOR_LAG_NONBLOCKING is not claimed.**

18 disposable gateway/floor checks PASS across current source, old auxiliary archive
and actual deployed archive: below/equal floors, ahead-floor rejection, replay and
changed/next payload cases. Actual snapshot replay is byte-preserving/idempotent;
next CRL and same-number/different-bytes write requests both fail the maintenance
guard without touching the fixture. The old/current generic mutating gateways do
update the floor and reject same-number/different bytes, but those results are **not**
transferred to the actual production forced command. No attempt to bypass its guard.

### No-write evidence and validation

- Existing owner binding `dev_fa4f7e03ca04`, HMAC resolution and private lookup/status
 artifacts unchanged. Prior exact Android106 confirmation retained; **zero lookup or
 status-operation repeats**. No selector used. Ledger subscriptions0/events0, cohort0/10;
 owner certificate rows0, valid0, horizon CLEAR. No new owner challenge/fetch since baseline.
- SQLite mode=ro/query_only/read transactions only. Identity/invite/support/grant,
 paid tables, revocation-bearing records, admission/publisher and stored CRL sequence
 unchanged. One unrelated certificate was added during ordinary production traffic;
 the prior certificate rows still match their authoritative fingerprint. Global
 certificate/readiness/challenge/chat tables are **not** claimed equal. Owner scope
 remains unchanged; observers did not call challenge/fetch/issue endpoints.
- RU/NL directory/CRL bytes, NL profile/minimum, forced-command configuration and
 service identities unchanged. Friends exact paid-aware archive unchanged, active,
 PID1002753/NRestarts0, effective/running argv match. No restart/reload, file replacement,
 gateway write, CRL action, paid event, material refresh or Android action.
- Final material readback: authority/issuer6993155s remaining, CRL10928s, directory
 10940s; strict actual parser, bindings/signatures PASS. Both hosts NTP synchronized.
 These are timestamped observations, not a perpetual live-entry authorization.
- Read-only monitor active, latest cycle28 October00:03:09 UTC; RU registry observed,
 NL registry UNAVAILABLE, not0. Console remains loopback-only/synthetic/read-only root,
 no production configuration mounts or credential environment entries. Monitoring
 itself does not collect PID/build or client telemetry; service identity was inspected
 separately. Administrative SSH was used for read-only commands, not relabeled as a
 technically restricted read-only credential.
- **96 affected pytest tests PASS,32 explicit deselections** (unrelated packaging and
 optional native/Android parity). Directory/timestamp, restricted-sync, CRL signature/
 issuer/time/number and same-number idempotency/conflict checks included. **48 parser
 +18 gateway/floor synthetic checks PASS**. No full repository/platform suite or build.
 No imported product code changed, so no CRL helper rewrite or correction packaging.
- Strict JSON, private-data/selector-pattern scan, new Markdown links, staged scope
 and `git diff --check` PASS. Only five documentation/evidence files are staged;
 pre-existing unrelated working changes remain unstaged and byte-preserved.

### Decision and next bounded action

The parser cause is resolved as **NL_VALIDATOR_ONLY_DRIFT**, with a stale auxiliary
validator left as technical debt. Actual validation remains strict14400s; no parser
correction candidate is authorized by the proven findings, and none was built/deployed.
Live entry remains **BLOCKED_CRL_PROFILE_COMPATIBILITY** because the required CRL
delivery/floor-update boundary is not established on the actual read-only command.

NEXT — separately authorize one bounded maintenance/delivery and floor-contract
reconciliation: review the exact authorized maintenance route, preserve the snapshot
endpoint's read-only guard, and establish atomic exact-payload acceptance/floor update
with a defined rollback boundary. The numeric reconciliation target is the exact
embedded/current CRL27211 (not a regenerated CRL); changing minimum_crl alone does not
prove future delivery. Do not substitute the old mutating archive, enable generic
writes, remove a safety guard or silently install credentials. This review performs
none of those corrections. **STOP; no phone opening/Connect or request for ГОТОВ.**

## Read-only owner binding and live-entry preflight — 28 October local

**OWNER_CANARY_BOUND_READONLY / BLOCKED_READONLY_PREFLIGHT / MATERIALS_INVALID /
LIVE_WRITES_NOT_RUN.** Input main `6dff337795b0545dbe9a63e5a5619ac9a13e1da8`.
Same checkpoint; no new product task or canary ID. This continuation changes only
documentation and a [sanitized receipt](2026-10-27-android106-beta-0-canary-1-readonly.json).
Server observations below use UTC, starting27 October23:31:11. No paid/live acceptance.

### Artifacts and binding

- Accepted lookup-only artifact: source `ad086c030cc77c680d924fb9c8e37faa286adc4c`,
 15 members,56017 bytes, SHA256 `63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308`.
 Regular/non-symlink, strict ZIP/JSON, exact committed member hashes, null envelope,
 absence of operational configuration/permit, import/help and private-data scans PASS.
 It was not rebuilt. Accepted unbound CRL package unchanged:24 members,138174 bytes,
 SHA256 `3c3736917efb1720b7086e57e4e8b2182fcb56734ec85b662b9bed71c15840a6`, manifest
 `704b67df66d21e198e175344932f81e4d23e2e697f15475f45656be9af476ebb`; unbound/null permit/
 absent production configuration verified read-only. No CRL helper production execution.
- Fresh private operation directory0700 outside Git/Django/web; separate random32-byte
 HMAC key0600. Selector supplied transiently without echo via stdin, never argv.
 Temporary0600 input unlinked immediately after the single lookup; exact selector
 absent from remaining operation files and process arguments. No forensic SSD erase
 claim. No selector input to PostgreSQL, Django, audit, URL, environment or shell history.
- One production lookup PASS at23:31:27; OWNER_CANARY_1=`dev_fa4f7e03ca04`.
 Unique bound identity, existing activation and non-revoked device/invite; MESH
 admission checked read-only with the existing grant logic. Exact106 accepted under
 confirm_android106: latest authenticated readiness ACK at27 October06:59:00,
 platform android, versionCode106, app_version `0.1.18-beta106-recovery`.
 No observation was updated. Full token/key/envelope remain private.
- Bound status-only package from the same exactad086c0 source:15 members,56187 bytes,
 SHA256 `ab27f3bf3d55475d752af9b3b3ed193e19832aa8df2ffb6dc7f38adb776090c0`, manifest
 `1923f3405e45112630648ebf14697fc0d3c6cc85aa0122ee6bb3f681dd842028`.
 Two independent byte-identical builds; binding=single_canary, permit=null, private
 read-only artifacts. Exact source/member checks PASS; no selector/key/config/path.
- Four disposable synthetic checks PASS: exact packaged status with a test-only
 synthetic token mapping (no production identity copied into a fixture), exact
 packaged apply→PERMIT_REQUIRED and lookup→BOUND_LOOKUP_FORBIDDEN, and unchanged
 original HMAC resolution/status on a separate synthetic binding. Package bytes
 were not modified by those tests. No production apply or second production lookup.
- One production bound status PASS at23:32:31 using the real private HMAC key:
 same binding, activation_active=true, cohort=false, version0, event_count0,
 effective_state/paid_allow/paid_until=null. Ledger remains subscriptions0/events0,
 cohort0/10. No owner slot has been enrolled.

### Freshness and the blocking result

Friends active/running, exact paid-aware archive
`dcd769986a1da7cb1662c0f73d18a88e9f73485a977db937ca5b1428c1fd1029`, effective/running
argv match, MainPID1002753, NRestarts0. This is a fresh observation, not reuse of
the historical CP2 PID. Publisher capability and historical core/policy fingerprints
match. SQLite mode=ro/query_only/read transaction: integrity, foreign keys, exact
paid schema and empty ledger PASS. NTP/NTPSynchronized=yes, resources sufficient,
no pending service/package transaction observed; read-only HTTP liveness PASS.

Certificate horizon: valid_certificate_count=0, latest_valid_expiry=null,
latest_remaining_seconds=0 — **CERTIFICATE_HORIZON_CLEAR**. No certificate issuance,
deletion or expiry modification; no readiness challenge/fetch.

RU issuer/authority signatures, CRL issuer/signature/number, strict directory
time/family/gateway validation PASS. At23:34:16, authority/delegation remaining
6994952s, CRL12725s, directory12737s; all exceed720s. Stored CRL sequence27211 matches.
NL has byte-identical CRL and directory, matching authority/family/gateway bindings;
signatures and wall-clock validity PASS, NTP synchronized. However, its **installed
strict directory parser rejects stage=time, predicate=invalid_lifetime,
field=expires_at**. Directory issued23:23:11, expires03:06:33 next UTC day; full
lifetime13402s. RU strict parsing passes those bytes; NL strict parsing does not.
No validator was weakened or production package changed to obtain PASS.

NL profile minimum_crl=27088, installed signed CRL number27211. A lower floor is
recorded as a compatibility question, not asserted by itself to prove invalid
cryptography; it is not the future exact-payload acceptance proof requiring the
generated number. The independent NL directory rejection already blocks entry.
Thus **MATERIALS_INVALID / BLOCKED_READONLY_PREFLIGHT**, not a short remaining-TTL
MATERIALS_REFRESH_REQUIRED and not READY_FOR_OWNER_LIVE. No refresh, CRL generation,
delivery, sequence increment, gateway repair or write credential/permit installation.

### Monitoring and no-write proof

Read-only timer active/waiting, last completed cycle27 October23:36:29 successful.
Latest RU snapshot observed/fresh (19s at inspection); NL snapshot fresh (16s) with
registry UNAVAILABLE, never false0. The existing monitor reports service state,
not paid build/PID; those were verified separately in this preflight. Client
telemetry remains NOT_COLLECTED. Console loopback-only, synthetic backend guard
present, no production write adapter or SSH/canary credential mount/home credential.
The existing external administrative SSH channel is not claimed to be least-privilege.
No monitoring configuration or PostgreSQL record was changed by this checkpoint.

Before/after read-only observations preserve paid rows/events, devices, invites,
grants, revocation state, admission, publishers, certificates, restricted challenges
and readiness results; service PID/start/NRestarts unchanged. RU CRL number/hash,
directory hash and NL profile/hash/minimum_crl/directory unchanged across inspection.
Concurrent chat_challenges/chat_sequence changes were observed (target chat_challenges
also changed); **no whole-registry or all-target-tables byte equality is claimed**.
They are outside the read-only commands performed here; the restricted challenge,
readiness and certificate fingerprints are unchanged. No Android action or Friends
restart, deployment, payment, enrollment, production subscription/event or CRL write.

Private observer-only dry-run corrections preceded successful readbacks (namespace
collision, a non-exported legacy validator constant, and a local credential-path
permission probe). No extra owner lookup/status and no production repair resulted.
Strict JSON, scoped selector/secret scans, Markdown links, staged scope and whitespace
checks PASS at closeout; full historical suites/platform builds were not run.

**STOP. NEXT — review NL directory lifetime validation and gateway floor compatibility;
any correction requires separate authorization, then fresh read-only recheck.**
Do not ask the owner to open the app or reply ГОТОВ yet. Stage0 requires
READY_FOR_OWNER_LIVE plus the owner's explicit ГОТОВ and a fresh production backup;
no automatic lookup repeat, activation, CRL phase or phone procedure.

## Exact-payload CRL delivery — source-only gate

**LIVE_ENTRY_SOURCE_READY / CRL_HELPER_UNBOUND_READY / PRODUCTION_LOOKUP_NOT_RUN /
LIVE_WRITES_NOT_RUN.** Input main `11b99a6cae1c9c8722b266bd773caa821d3e3a61`;
accepted bounded-dispatch source `ad086c030cc77c680d924fb9c8e37faa286adc4c` unchanged.
Same BETA-0-CANARY-1; no new top-level task. No production access or operational action.

### Source and authority boundary

- New helper/packager and their tests only; minimal existing restricted_admin refactor
  extracts pure build_crl_payload. It reads a query-only snapshot, computes the existing
  paid-aware deny set, signs once and returns PEM, number/timestamps/serial metadata.
  It does not change any DB row or file. Existing publish_crl delegates to it and keeps
  its public/operator behavior, including valid lifetime choices and monotonic floor.
- Canary lifetime900s; generated number=max(previous CRL number, stored sequence)+1.
  Expected certificate must be newly revoked; other newly added serials require
  independently proven current deny/revision/family reasons. Allowed unrelated
  certificates are excluded. Serial output uses HMAC(decimal serial) short tokens
  privately; sanitized receipts never expose raw serials or CRL contents.
- Immutable bound-envelope contract is tested only with synthetic values: alias,
  operation_id, HMAC device/safe_ref, version3/count3/expired, exact certificate token
  and <=300s generation window. Two payment events followed by explicit expire,
  current Android106 eligibility, non-revoked device/invite, paid denial and valid
  authority/revision/family/identity-bound certificate are required. No other cohort
  member is allowed. No helper operation can change paid/identity/invite/grant state.
- No default/live configuration, host, key, credential, readback transport or bound
  package is installed. Public CLI is help/manifest only; it cannot run prepare,
  deliver, commit or accept operational input. Future configuration/transport injection
  must be fixed and operator-reviewed, never supplied via public input. Existing
  sync lock identity must be verified by that future configuration, not guessed here.
- Existing gateway returns directory only. Acceptance additionally requires trusted
  authenticated readback of exact payload SHA256, installed CRL number and minimum_crl.
  Plain directory output is not treated as that proof. Existing strict directory
  parser checks time/family/gateway/seeds; no new signature or wire schema is invented.

### Immutable operation and delivery

Preparation holds the configured existing restricted-sync lock and opens authoritative
DB read-only. Exclusive0700 operation directories and0600 regular/non-symlink/single-link
files retain PEM, exact canonical compact JSON request (only revocations), hashes,
generation metadata, prior local hashes/sequence, safe revoke tokens and private
fingerprints. Journal updates are authenticated, atomic and parent-fsynced. Key and
canonical device/selector/certificate body are never persisted in the journal.

Generation_count=1 for every prepared operation. Existing directory prevents any
second generation, including after a partial preparation crash. Payload/request bytes
are hash-checked on every resume, never recomputed for retry. Request<=20000 bytes,
PEM<=16384, returned directory<=8192; duplicate/nonfinite JSON is rejected.

| State/outcome | Continuation |
|---|---|
| PREPARED |One delivery of saved request bytes |
| DELIVERY_IN_PROGRESS after crash |DELIVERY_UNRESOLVED; no resend |
| NOT_SENT with proven pre-execution failure |TRANSPORT_NOT_SENT; one exact-byte retry, at most2 attempts |
| Generic exit/timeout/lost/partial output |UNKNOWN / DELIVERY_UNRESOLVED; readback only |
| Definitive pre-apply rejection |REMOTE_REJECTED; no retry |
| Valid exact gateway acceptance |REMOTE_ACCEPTED; local commit only |
| Local commit begun |LOCAL_COMMIT_IN_PROGRESS; reconcile files/DB |
| Remote accepted, local I/O failure |LOCAL_COMMIT_FAILED / REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED; retain all evidence |
| Readback/hash/sequence complete |COMMITTED; idempotent local readback |

The adapter contract does not equate an arbitrary SSH exit with NOT_SENT or REJECTED.
Actual gateway tests prove same number/same bytes idempotency and reject same number/
different bytes (typed adapter outcome CRL_PAYLOAD_CONFLICT), bad signature/issuer,
rollback number and invalid time/lifetime. Gateway mutation followed by lost/invalid
directory output is uncertainty, not proof of pre-apply rejection.

### Local commit and crash reconciliation

After remote acceptance: recheck prior CRL/hash/sequence and relevant paid/event/device/
invite/certificate/authority fingerprint; fsync local temp files, persist in-progress
journal, set exact sequence, atomically replace CRL/directory, fsync parents, commit
SQL, read back exact bytes/sequence and mark COMMITTED. Newer/conflicting local state
is not overwritten. No payload regeneration or second delivery repairs local failure.

| Restart case | Action |
|---|---|
| A: DB old, CRL old, directory old |Commit exact saved payload/response |
| B: DB new, CRL new, directory new |Validate and mark COMMITTED |
| C: DB old, CRL exact new |Finish sequence/directory from saved evidence |
| D: DB new, CRL exact old baseline |Install saved CRL/directory without incrementing again |
| E: Unknown/conflicting number or hash |LOCAL_COMMIT_CONFLICT; no generation/delivery |

Current directory hash must match exact old or validated new bytes in every case.
UNKNOWN trusted readback proving exact installed payload transitions REMOTE_ACCEPTED;
old payload remains unresolved, with no automatic resend; conflicts fail READBACK_MISMATCH.

Typed results: PASS, LOCK_BUSY, INVALID_PERMIT, PRECONDITION_FAILED,
CRL_GENERATION_FAILED, CRL_GENERATION_ALREADY_COMPLETED, CRL_EXPECTED_SET_MISMATCH,
CRL_UNEXPECTED_REVOCATION, TRANSPORT_NOT_SENT, TRANSPORT_FAILED,
CRL_DELIVERY_UNRESOLVED, CRL_PAYLOAD_CONFLICT, REMOTE_REJECTED,
GATEWAY_VALIDATION_FAILED, DIRECTORY_VALIDATION_FAILED, LOCAL_PRECONDITION_CHANGED,
REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED, LOCAL_COMMIT_FAILED, LOCAL_COMMIT_CONFLICT,
READBACK_MISMATCH. Receipts use only the prescribed sanitized allowlist; no stderr,
raw exception, profile, directory, URL, host, private path or key is returned.

### Source validation

| Gate | Result |
|---|---|
| New CRL helper / package tests |95 /3 PASS |
| Existing canary / paid backend / preparation |79 /76 /2 PASS |
| Existing restricted/admin/sync/directory/window tests |206 PASS,29 existing optional Go/native skips,4 explicit native deselections |
| PostgreSQL console / Django check / migration drift |118 PASS / PASS / no changes detected |
| Syntax / strict JSON / private-content scan / scoped links / staged scope / diff checks |PASS |
| Production registry/lookup/binding/CRL/delivery/paid writes |NOT_RUN |

Tests exercise the actual existing gateway against synthetic local files, not live
transport. A first run's3 isolated-sync tests rejected a venv site path inside checkout;
unchanged tests passed using the same accepted dependencies copied to an external
disposable venv. No production/path workaround or test assertion weakening. No native
build, Android action, full historical suite, Linux/Windows task or Friends restart.
Console tests used a separate disposable local PostgreSQL test DB.

Accepted lookup-only artifact remains unchanged:15 members/56017 bytes/SHA256
`63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308`.
Its source inventory excludes the changed restricted_admin and new helper; no rebuild
is needed. The final unbound CRL package receipt follows below.
No bound envelope/activation/expire/recovery permit is built.

The first post-commit package audit found IP constants in unused catalog-validation
functions. It was rejected by the capsule's no-IP gate and retained privately, not
delivered. A packaging-only follow-up extracts exact committed source segments for
the five required strict-parser functions and their two stdlib imports; no function
is rewritten, no authority/parser policy is relaxed. The full source blob hash,
selected names and exact segment hashes are recorded in source_projections, alongside
ordinary member hashes. Unused catalog/profile code and all IP constants are excluded.
AST equality, isolated import/help and deterministic package tests PASS. No accepted
lookup artifact or backend source is changed by this packaging correction.

### Deterministic unbound CRL package

Requested source commit: `ce09b96e9e00a9d8e23a31acbb4fdb906442cd28`
(`feat: add exact-payload CRL delivery for owner canary`). The subsequent packaging
correction is `8ba535d49c4e914a0aee0cacdd20405733bbe53f`; both ordinary pushes had
their remote main SHA independently verified. No published history was rewritten.

| Field | Verified result |
|---|---|
| Exact final package source |`8ba535d49c4e914a0aee0cacdd20405733bbe53f` |
| Binding / operation permit / production configuration |unbound / null / absent |
| Members / size |24 /138174 bytes |
| SHA256 |`3c3736917efb1720b7086e57e4e8b2182fcb56734ec85b662b9bed71c15840a6` |
| Source manifest SHA256 |`704b67df66d21e198e175344932f81e4d23e2e697f15475f45656be9af476ebb` |
| Two independent builds / fixed timestamps and modes |Byte-identical / PASS |
| Exact source/member/selected-segment hashes / AST equality |PASS |
| Strict JSON / IP-private scan / Python syntax |PASS |
| External-cwd help/manifest and isolated import smoke |PASS, Python3.14.4 |
| generate/deliver/commit/lookup CLI probes |DENIED; no registry opened |
| License/notices |LICENSE + THIRD_PARTY_NOTICES.md included; runtime dependencies not vendored |
| Original accepted lookup-only package |UNCHANGED; not rebuilt |

[Sanitized source manifest, all member hashes and projection provenance](2026-10-27-android106-beta-0-canary-1-crl-unbound.json).
Both final archives are retained read-only in private ignored evidence; rejected
pre-projection builds remain separate and must not be used. No archive is published,
bound, uploaded or executed against a registry. No private configuration, credential,
owner/certificate token, Support ID, CRL payload or production endpoint is included.

Source gate DONE. Status remains LIVE_ENTRY_SOURCE_READY / CRL_HELPER_UNBOUND_READY /
PRODUCTION_LOOKUP_NOT_RUN / LIVE_WRITES_NOT_RUN. This proves synthetic source behavior,
not production CRL delivery or live canary acceptance.

**STOP. NEXT — production read-only owner lookup and binding, not automatically.**
No production key/configuration installed, no CRL publication or local live files
changed, no CP2 redeployment or gateway/Android change. Historical evidence retained.

## Historical bounded recovery dispatch — source-only continuation

**SOURCE_READY_WITH_EMERGENCY_RECOVERY / LIVE_NOT_RUN.** Input main
`3a5e91d06977eb86fa78dec386477518fb5a0bfc`; accepted emergency source
`49bdd794cce32075d93691daa0b9f9cc7f7dffcf`. Same checkpoint, no new PLAN ID.
Only the practical dispatch guard, focused tests/docs and local lookup-only package
change. This is not completion of the broader live-entry preparation.

- New recovery first apply accepts `period_start<=server_now` and
  `server_now-period_start<300`: execution at start or1..299 seconds later can pass.
- Preserve exact `paid_until-period_start==2592000`, inclusive static period-start
  bounds `not_before<=period_start<=not_after`, half-open execution window
  `not_before<=server_now<not_after`, and `0<not_after-not_before<=300`.
- Never rebase or extend the signed-off payload: expiry is30 days from permit start,
  not30 days from delayed execution. Backend receives original period fields.
- Future dispatch, delay>=300s or a closed execution window fails typed
  `RECOVERY_DISPATCH_WINDOW_CLOSED` without inserting an event. Invalid duration or
  static period bounds still fail `INVALID_RECOVERY_PERIOD`; invalid window length
  still fails `INVALID_EXECUTION_WINDOW`.
- Normal four-stage path, version/state/certificate/eligibility guards, backend
  authority and terminal marker remain unchanged. Identical terminal recovery replay
  bypasses new-event dispatch checks; changed payload remains `EVENT_ID_CONFLICT`.
- Certificate/CRL state is not modified. Internal purpose/zero amount, sanitized
  receipts and non-paid fingerprints remain unchanged.

### Dispatch validation

| Gate | Result |
|---|---|
| Canary operator tests |79 PASS |
| PostgreSQL console tests / affected paid backend / preparation |118 /76 /2 PASS |
| Django system check / migration drift |PASS / no changes detected |
| Staged syntax / strict JSON / private-content scan |PASS |
| Staged Markdown local links / anchors |444 /23 PASS |
| Scoped staged diff / git diff --check |PASS |
| Production lookup/registry/binding/write permits/live operations |NOT_RUN |

Both recovery versions cover dispatch0/1/150/299s, unchanged payload/expiry and
actual server applied_at. Negative tests cover future start,300/301s delay, shortened
execution window, out-of-bounds period start and invalid duration/window length;
rejections preserve registry snapshots. CLI tests use the server clock at0/1/299s,
reject300s and prove no rebase. Existing idempotency/terminal/normal-path tests PASS.
Console tests use a separate disposable local PostgreSQL test DB; no running-console
upgrade, backend deployment or production connection is performed.
Unrelated unstaged operational notes remain untouched, including one pre-existing
missing Markdown anchor found by the working-tree check; the staged link gate passes.

### Dispatch lookup-only artifact

Source/tests/docs committed and pushed as
`ad086c030cc77c680d924fb9c8e37faa286adc4c`; remote main SHA independently verified.
Two independent builds from that exact committed source are byte-identical.

| Field | Verified value |
|---|---|
| Source commit |`ad086c030cc77c680d924fb9c8e37faa286adc4c` |
| Binding / envelope |`lookup_only` / null |
| Members / size |15 /56017 bytes |
| SHA256 |`63ffe0f1ac4dad0c15a94558423de4eab2a5aff754167e8108d75064bb95d308` |
| Strict manifest / exact member hashes / committed-source equality |PASS |
| Non-wrapper source members unchanged from accepted49bdd794 |PASS |
| Python syntax / strict JSON / private-selector scan |PASS |
| Import and --help smoke outside repository import path |PASS |
| Historical c5f2346c artifact unchanged |PASS |
| Bound/write-permit archive / production registry opened |NOT_BUILT / NOT_OPENED |

Both new artifacts are read-only inside private ignored evidence. Historical
artifacts/evidence remain untouched. Smoke executes only --help; no lookup, status,
apply or registry connection. No binding, credential or permit is included.

**STOP. NEXT — obtain the exact-payload CRL delivery helper contract, complete its
source gate, then read-only owner lookup/binding and coordinated phone preparation.**
The helper contract was not supplied in this continuation and is not invented.
No production lookup, binding, CRL generation/publication, Android action, payment,
enrollment, Friends restart or CP2 change. Live phone operations wait for owner ГОТОВ.

## Historical emergency recovery source gate —49bdd794

**SOURCE_READY_WITH_EMERGENCY_RECOVERY / LIVE_NOT_RUN.** Input main
`68b99ac667c78fa6f20f95ffa443cdbd7d1a5ef7`, accepted previous product source
`28657bf9e53411a4cdaff44d8ad5ebfb252046e0`. Same BETA-0-CANARY-1 under the existing
Android critical path. Only source/tests/docs and local lookup-only packaging;
no production registry/lookup, binding, enrollment, real payment, CRL publication,
Android action, Friends restart/deployment, CP2 backend change or desktop work.

### Exact recovery contract

- Normal activate0/activate1/expire2/activate3 sequence retained. Separate permit
  action recover is allowed only at expected_version1 or2, matching current
  subscription version and paid-event count. Versions0/3, explicit expiry and
  terminal revoke cannot start emergency recovery.
- First/second activation must already exist; all prior events are payments.
  Subscription stored state active, effective_state expired and paid_allow false
  prove natural expiry. Existing backend rechecks exact Android106 eligibility,
  non-revoked device/invite and existing admission restrictions. Full bound HMAC
  token/safe_ref/alias and no-other-cohort-member guards remain unchanged.
- Exact30 days: period_start=server_now, paid_until=server_now+2592000. First apply
  rejects a past/future start rather than rebasing the permit. Static bounds require
  period_start within not_before..not_after, execution within the half-open window,
  and window length1..300 seconds. Other durations fail INVALID_RECOVERY_PERIOD.
- Certificate inventory must exist and have no bound row with expires>server_now.
  Certificates, expiry/revision and non-paid tables remain unchanged. Future live
  procedure must wait any issued certificate's NotAfter+30 seconds; that wait and
  phone/serial observation are not performed or claimed by this source gate.
- Delegate to existing paid_beta.apply_event(event_type=payment), unchanged schema,
  APK attestation and authority. The transient reference is
  internal-canary-recovery:<event_id>; backend stores its SHA256, not raw text.
  No new event type, field, table, identity, invite or entitlement machine.
- Terminal detection reads reference_hash against SHA256 of that prefix plus each
  existing event ID. Find the incoming event first, then check the terminal marker,
  then run guards for a new event. A different ID after recovery fails
  RECOVERY_TERMINAL, including old normal-event replays. Same ID/backend payload
  returns the existing event; changed payload fails EVENT_ID_CONFLICT. Replay is
  permitted after window/entitlement expiry and does not extend the original period.
- After version1 recovery: active/version2/count2 and
  NATURAL_PHASE_ABORTED_OWNER_RECOVERED. After version2 recovery:
  active/version3/count3 and CRL_PHASE_ABORTED_OWNER_RECOVERED. The checkpoint's
  normal path is permanently closed after either branch. Classification is derived
  from immutable event order, not a replay caller's changed expected_version.
- Safe wrapper output adds branch emergency_recovery; purpose internal_canary and
  amount0 stay non-revenue. Raw authoritative backend event/receipt is unchanged.
  No selector, canonical device, HMAC key, raw reference, invite or certificate body
  enters the sanitized output. Transactional non-paid fingerprints are checked;
  unexpected trigger side effects roll back the whole new event.
- CRL number/entries are not generated, published, removed or rolled back. An old
  expired serial may stay in CRL; proving a future new certificate has a different
  unlisted serial is live acceptance, not a source-checkpoint side effect.

### Required validation

| Gate | Result |
|---|---|
| All canary operator tests, including normal path |68 PASS (30 existing +38 emergency cases) |
| Existing PostgreSQL console tests |118 PASS in separate disposable test DB |
| Existing affected paid backend tests |76 PASS |
| Existing preparation tests |2 PASS |
| Django system check / migration drift |PASS / no changes detected |
| Staged source syntax / strict JSON / secret-private scan |PASS |
| Markdown local links / anchors |446 /23 PASS |
| Staged scope / working and staged diff --check |7 files / PASS |
| Production lookup/registry access/binding/live procedure |NOT_RUN |

Emergency tests cover both versions, active/valid-certificate/revoked/explicit-expire
denial, exact period/start/window, token/alias/safe_ref/device/eligibility guards,
sanitized zero-amount classification, unchanged identity/invite/support/certificates/
CRL sequence, transactional rollback, concurrent replay, payload conflict, terminal
normal-path/recovery rejection and exact server-clock CLI behavior. Existing normal
expire/final certificate guards still PASS. Tests use generated synthetic identities
only. Packaging tests now build only lookup_only archives and smoke --help; no bound
permit archive is created even by those packaging fixtures.

The console image/schema/configuration was not rebuilt/restarted/migrated in this
source checkpoint. No historical full suite, CP2 source/package gate, Linux or Windows
gate repeated. Prior production counts0/0 remain accepted input, not a fresh live read.
Source commit `49bdd794cce32075d93691daa0b9f9cc7f7dffcf`
(`feat: add terminal emergency recovery for owner canary`) pushed to main; remote
SHA verified before packaging. Prior lookup artifact c25447d9… stays immutable
historical evidence and was independently verified unchanged.
Pre-existing123 added lines in unrelated working-tree edits and untracked work are
preserved outside this source commit; private validation evidence remains ignored.

### Deterministic emergency-capable lookup artifact

| Field | Exact result |
|---|---|
| Source commit | `49bdd794cce32075d93691daa0b9f9cc7f7dffcf` |
| Binding | `lookup_only` (envelope null) |
| Members |15 |
| Size |56021 bytes |
| SHA256 | `c5f2346cd4d46a6bf3875e2181e81027c7db43f62b886161756230b6499adc31` |
| Independent builds |2; byte-identical PASS |
| Strict manifest / exact inventory / member hashes |PASS |
| Members match exact committed source |PASS |
| Existing backend/identity modules match accepted28657bf source |PASS |
| Python syntax / private-selector scan / local import-help smoke |PASS |
| Production registry opened / bound permit archive / live operation |NOT_RUN / NOT_BUILT / NOT_RUN |

Both newly named local artifacts are retained read-only in private ignored evidence;
no historical archive was replaced. Only sanitized package metadata is committed.
This artifact includes the recovery source but cannot perform a bound operation:
lookup_only does not carry a device binding or operation permit. Smoke used --help,
not lookup/status/apply, and did not open any registry. No automatic next-stage run.

**STOP. NEXT — production lookup, binding and coordinated owner-phone live procedure.**
Do not start that next stage automatically; this checkpoint grants no live execution.

## Historical continuation from55c6a24 — local upgrade and bounded operator

**CHECKPOINT / LOCAL_CONSOLE_UPGRADED / CANARY_OPERATOR SOURCE_READY / LIVE NOT_RUN.**
Same task and same sole OWNER_CANARY_1 authorization; no new top-level PLAN ID.
The owner has supplied the four live goals and the final same-identity recovery
target of server_now+30 days. The continuation stops at the suggested component
paths; short live windows, reviewed CRL delivery and physical-phone coordination
have not been supplied. They were not guessed.

### Local console upgrade

- Private backups: PostgreSQL custom dump and the complete synthetic volume, taken
  while the local console was stopped. Online PG dump remains consistent while the
  separate read-only inventory monitor runs. PG disposable restore/open and SQLite
  disposable restore/integrity/FK checks PASS. Files0600/directory0700; no backup,
  DB, credentials or private receipt committed.
- `.env`, inventory HMAC key and operator credentials backed up privately and
  verified byte-identical after upgrade. No credentials printed or regenerated.
- Source-only preparation and local image rebuild completed; running migration
  now0006. Django system check and migration drift PASS. Console health PASS;
  HTTP remains127.0.0.1:8765, PostgreSQL has no published port.
- First local start stopped before Django because a restrictive umask produced
  root-owned source files unreadable by the non-root console user. Preparation now
  sets only copied allowlisted generic source files0644/directories0755 beneath
  private `.local`0700. Original source/private permissions unchanged. Rebuild and
  local start PASS. This was not a production restart or a paid-service failure.
- Running image ID: `sha256:1e28103e380a4acd5143f7055feb49ad6019ebe2fd01b142fd37f06d336752d9`.
  Application payload is the accepted55c6a24 console source; the preparation fix
  changes context permissions, not the entitlement authority or Android artifact.
-50 synthetic device bindings and synthetic registry devices/invites/support/paid
  tables preserved; all prior workflow rows preserved. Existing3 payment records
  now have default customer_payment.559 prior audit rows compared to the restored
  backup and retained unchanged;8 concurrent inventory.import records were appended
  at the comparison readback. Projection observation timestamps refresh normally.
- No real-owner DeviceProjection or synthetic substitute created. Production
  write actions remain absent: Django still opens only the guarded synthetic
  registry. No production DB is mounted or copied into Django.

### Canary-only source boundary

`control/friends/paid_beta_canary.py` delegates status/activation/expiry, idempotency
and conflict detection to the unchanged `control.friends.paid_beta`. It provides
read-only transient-stdin lookup, then full HMAC-token-bound status and a fixed
single-operation permit. No runtime write selector/reference/event/time override;
no revoke/grace/delete/migrate/restart/CRL operation. Exceptions/receipts do not echo
the selector, key, raw device or registry path.

The bounded workflow has at most four new events: initial activation, activation
after natural expiry, explicit expire with a still-valid certificate, and recovery
after all retained target certificates expire. Each operation needs a separately
reviewed exact envelope (server execution window at most15 minutes; no default
paid duration; ceiling31 days). Existing paid backend remains the only state machine.
Guards reject a second cohort member, stale versions/counts, bad bindings, invalid
Android eligibility and non-paid table changes. Duplicate permits return the
original event plus fresh status, never an implicit renewal.

`scripts/package_paid_canary_operator.py` exports only allowlisted committed
sources with source hashes/license/dependency metadata and an optional immutable
safe envelope. Repeated builds are byte-identical; dirty source, DBs, `.env`, keys,
private selector and other operator modules are excluded. No production-bound
envelope/package or owner token has been created. No package was uploaded/executed
on a gateway. There is no new Django production adapter or receipt importer; any
future import must validate a strict sanitized safe_ref-keyed receipt, not create
a fake DeviceProjection or authoritative subscription copy.

Committed lookup-only artifact (not bound to an owner and not deployed): source
`28657bf9e53411a4cdaff44d8ad5ebfb252046e0`,15 members,52921 bytes, SHA256
`c25447d92bcc3edd0b26889734465e759cbb5a682697f055a3d64a847a894e8e`.
Independent repeat build byte-identical; internal source-manifest hashes and local
CLI import/help PASS, no registry opened. Both private artifacts retained read-only.

### Validation and remaining boundary

-118 PostgreSQL console tests PASS on the rebuilt image in a separate disposable
  test database: purpose defaults, zero canary acceptance/customer rejection and
  analytics separation included. System/drift checks PASS.
-76 existing affected paid backend tests PASS using the retained control/identity
  environment. No CP2 source/package gate or repository full suite repeated.
-30 new canary wrapper/packaging tests +2 restrictive-umask tests PASS, including
  real synthetic backend transitions, denial/recovery/idempotency/conflict, guarded
  stage/window/certificate/binding/eligibility rejection, unrelated-trigger rollback,
  strict input/no echo and packaged subprocess readback.
- Source closeout:11 staged source/test/doc files; Python syntax,448 local link
  targets, added-content privacy scan, strict private JSON and both staged/working
  `git diff --check` PASS. Unrelated pre-existing123 added lines and untracked work
  remain outside the commits. Private backups, credentials and historical evidence
  retained, never staged. Source commit pushed and remote SHA verified before this
  artifact-receipt closeout.
- Production lookup, binding, activation, expiry, live Connect/session, CRL delivery,
  recovery/reactivation and Android state readback remain **NOT_RUN**. No customer
  payment/enrollment, CP2 deployment/restart/migration, gateway/publisher/admission
  mutation or Android/Linux/Windows change. No canary slot occupied yet.

**Historical NEXT at28657bf/68b99ac — obtain the remainder of the live procedure and
coordinate the owner phone.** The final30-day active
and connect-capable owner state is a required future gate, not a claimed result.

## Historical result and scope at55c6a24

**CHECKPOINT / PAYMENT_PURPOSE SOURCE_READY / LIVE NOT_RUN.** Input main:
`6d5202128ebfda6b60446d4f85cd7d9e5f2323fc`. This is a substep of the existing Android
critical path, not a new top-level project or CP3. CP2 is owner-accepted **DONE /
PAID-AWARE EMPTY-COHORT BACKEND SERVING / PUBLISHER CAPABILITY PRESERVED /
REAL PAYMENT AND ENROLLMENT NOT_RUN**. Its deployment/migration/restarts and
source/package gates were not repeated.

The sole authorized production target is designated **OWNER_CANARY_1**. Planned
allocation is one permanent internal slot out of ten, leaving nine customer slots
after enrollment. No row or reservation was created: this allocation is not yet
an observed backend state. No alternate production identity was used. The private
administrative selector was not passed to tools, copied into operator files or
persisted in Git/docs/PG/audit/URLs/sessions/logs/screenshots/receipts/event IDs/
external references. No device-token mapping is invented: administrative lookup
and HMAC binding are NOT_RUN.

## Implemented operational metadata

- `PaymentRecord.purpose`: `customer_payment` / `internal_canary`; default and
  existing rows remain customer payments. Existing confirmation metadata is preserved.
- Customer amounts remain positive. Internal canary must have zero amount, is not
  a customer payment/revenue, and retains the existing currency field as zero-value
  metadata only. Model/form validation and PostgreSQL constraints fail closed.
- Purpose is immutable from creation, including before confirmation. Existing
  confirmed-record/intent/audit immutability, reference uniqueness and permissions
  remain in force. No payer/bank/secret/selector fields were added.
- Customer-payment analytics exclude canaries; a separate confirmed-canary-record
  counter is explicit, not a count of devices/cohort slots. Operational activity
  still counts operations, not revenue.
- Russian form/detail/preview screens, admin filter, new metadata audit rows and
  administrative receipt wrapper expose the purpose. Raw authoritative backend
  receipt is not modified; synthetic integration still produces `event_type=payment`
  with existing idempotency and one request/event behavior.

Friends `paid_beta` remains the only entitlement authority. No changes to its
schema/state machine/cap10/idempotency/challenge/fetch/certificate boundary, client,
protocol, keys, invitation or activation semantics. The console remains synthetic
for write workflows; production inventory remains read-only. No production device
was copied into a synthetic projection to bypass that separation.

## Validation and installation boundary

- 23 new PostgreSQL tests PASS: purpose defaults/constraints, pre/post-confirmation
  immutability, analytics separation, metadata-only no-enrollment, form/admin/receipt
  rendering, unchanged synthetic backend activation/idempotency, migration of an
  existing confirmed payment and repeated migrate with a fresh migration loader.
- 118 console tests PASS in a separate disposable PostgreSQL test database with
  per-test synthetic registry copies. The first repeated-migration test reused a
  stale MigrationExecutor cache; the test was corrected and rerun successfully.
  No live schema was affected by that test failure.
- Migration drift check PASS; Django system check PASS. These are console checks,
  not a CP2 package/source gate, full repository suite or Android live acceptance.
- No running-console upgrade, production registry lookup/write, device interaction,
  CP2 restart, CRL publication or gateway change. Android106 was not rebuilt or changed.
  Installed APK/state and actual live session behavior were not reverified here.

Migration0006 is source-ready and tested, **not installed into the running console**.
No real payment/customer enrollment or owner-canary activation was performed.
Do not roll a nonempty paid cohort back to a pre-paid backend or delete paid/audit
rows. Neither test migrations nor SQLite fixtures constitute live recovery evidence.

## Live completion gates still open

| Gate | Result |
|---|---|
| Exact authorized-device lookup/HMAC binding and Android106 observation | NOT_RUN |
| Internal owner enrollment and production activation | NOT_RUN |
| Readiness/certificate paid boundary and successful MESH Connect | NOT_RUN |
| Natural expiry; new challenge/fetch/reconnect denied | NOT_RUN |
| Already-active session behavior after expiry | NOT_RUN |
| Paid-aware CRL generation and gateway propagation | NOT_RUN |
| Recovery/reconciliation and repeat activation on the same identity/invite | NOT_RUN |
| Android identity/activation/settings/history preservation | NOT_RUN |

The submitted procedure ends at the `purpose` choices. A live expiry period,
observation/CRL propagation/session stop bounds and safe recovery sequence were
not supplied. They must be agreed before mutating the owner's production access;
this checkpoint does not invent a period, assume a CRL deployment path or substitute
synthetic results for the authorized physical-device canary.

## Source closeout

The staged scope contains19 source/test/documentation files only. Staged Python
syntax,455 local Markdown links/anchors, added-content secret/private-data scan,
strict JSON validation of the local sanitized validation summary, and
`git diff --check` / `git diff --cached --check` PASS. Pre-existing unrelated
working-tree changes and private/historical evidence remain untouched and unstaged.

**Historical NEXT at55c6a24 — obtain the remaining live procedure.**
Only OWNER_CANARY_1 is eligible; no customer payment/enrollment, alternate identity,
CP2 redeployment, Linux/Windows work or new top-level PLAN ID.
