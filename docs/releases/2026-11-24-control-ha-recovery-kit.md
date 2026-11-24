# CONTROL-HA — offline recovery source and dependencies, 24 November 2026

Selected task: CONTROL-HA-20261123 / HA-02, existing complete-recovery acceptance block.
Actual cold execution PASS; complete HA-02 remains IN_PROGRESS. No product version, installation, public
artifact/catalog, gateway policy or production service change. This is not HA-03 activation.

## Actual NL2 recovery — 14:12UTC

Actual successful readback is saved at2026-11-24T14:12:14.686332UTC on the owner workstation
after the isolated NL2 process completes. Runner source
`d85cccb20524fd9b75ede0908ebbb47c339ad068` was committed, pushed and remote-SHA verified
before execution; the immutable recovered toolkit remains source8acc6bd2, not the runner
branch HEAD. Recovery uses existing Ubuntu24.04/systemd/kernel facilities on NL2, not
Docker, a new package installation, the working checkout/venv, RU, live volumes or an
installed application entrypoint. This proves a practical independent recovery host;
it does not perform a bare-metal operating-system installation.

- Restored419 source files/28 locked wheels, native10-module/binary-libpq checks,610 canonical
  rows,207 receiver decisions/82 allocations, legacy worker and mailbox. The `dependencies`,
  `canonical` and complete `fleet` results equal the accepted local readback exactly;
  original capture timestamps and security floors are not refreshed to make them valid.
- The actual transient unit reports512MiB MemoryMax, zero swap,250ms/s CPU quota,32 tasks,
  ten-minute deadline, read-only private image root, DynamicUser/private user and network
  namespaces, empty capabilities and no-new-privileges. In-process readback confirms a
  non-root identity, zero effective capabilities, only loopback and inaccessible live paths.
  Sampled memory peak was444690432 bytes, not an asserted final lifetime maximum.
- Eleven transported files total142031569 bytes: seven AES-GCM custody capsules, the toolkit,
  its independent checkpoint/bootstrap, and a private retained Python-image archive.
  NL2 independently rehashes every file and fsyncs the private custody directories14:16UTC.
  Protected parent is0700; no custody key is retained in persistent remote files. Native
  keys/checkpoints arrive over encrypted SSH stdin into unit-private temporary memory.
- A fresh negative unit changes only one key byte in memory. Native readback refuses with
  the public `ValueError` result; the scoped systemd journal confirms exit1 and unit cleanup.
  The same retained ciphertext/key mutation locally identifies `CAPSULE_AUTHENTICATION`.
  The harness first expected the lower-level `InvalidTag`, but the established loader
  intentionally wraps it; the failed harness assertion is retained, not hidden by a rerun.
- Final check2026-11-24T14:20:09UTC confirms all five production-service states, main PIDs,
  invocation IDs and restart counters exactly equal13:53UTC baselines; no recovery unit
  remains active. All21 original owner-held capsule/key/checkpoint files are byte-identical.
  Zero native dispatch, no live service restart/configuration change, no release/version change.

The first actual native attempt was safely refused because umask077 made the encrypted
bind directory0700, unreadable to DynamicUser. Only that directory became0755 beneath its
unchanged root-owned0700 parent; ciphertext files are read-only, not keys. A new unit then
passed. Do not weaken the private parent or run recovery as root to bypass this boundary.
The image derivative excludes `/app`, `/root` and `/home`;184 absolute internal symlinks
were converted to equivalent relative links for data-filtered extraction of14966 entries.
The original accepted image root and all retained inputs remain unchanged.

| Sanitized artifact | SHA256 |
| --- | --- |
| Python runtime transport archive |04f6061c0156b74f8b7a5d11baf8d0db41706454b42c2c12ab2aa3aea6beb751 |
| Closed transport manifest |892ae5104e5effbf333074ba1772ceb65e4c4a0a55e002b3707323a21a5f09cd |
| Native remote readback |d4dfce71f7538cc155e95f5dc8e691824dae377f8c95a499147d6e5a2a39dbb9 |
| Wrong-key refusal receipt |ed47688271a235aa8a5402072c0611581dc447bb600c1d78412eeacc21c7f108 |
| Separately retained published systemd runner |d290e513358addf1b9e00d904c5e8b4b89cbd6d491c93441f0cb7d0921f5dd5e |

The3550-byte runner from exact publishedd85cccb2 is also retained/read back/fsynced in
the private NL2 directory after qualification, so constructing a later transient unit
does not require the original checkout or a Git download. Its imports are in the verified
kit. This is a separate source receipt; the original eleven-file transport manifest is
unchanged. The owner must still supply independently retained keys/access and trusted pins.

Private owner evidence: `control-ha/20261124-recovery-hosts-01`; private NL2 custody:
`/opt/apps/family_connect/ha-recovery/20261124-host-01`. Do not commit the runtime, archive,
keys, raw receipts or databases.50 focused tests PASS; previous242 local tests are not
rerun or claimed as a new platform/whole-system gate. No package or persistent daemon
was installed. Cleanup is complete; on a future aborted run, stop only its exact transient
unit and retain encrypted custody/evidence. Never restore a laboratory DB over production.

Practical host/tool availability and remote execution are now qualified. Remaining:
coherent all-writer/in-flight capture, independently approved current checkpoint, independent
off-laptop custody of recovery keys/access, and final complete OWNER-PG/post-ACK/stale-copy
readback from that coherent point. Remote ciphertext alone does not survive loss of the
only key/access holder. These are the same three partial HA-02 gates; replication remains
PASS. This historical-snapshot readback is not full recovery, production HA or HA-03.

## Bounded NL2 recovery runner

The [systemd runner](../../scripts/control_ha_recovery_systemd.py) adapts the accepted
offline native probe to existing NL2 tooling instead of installing Docker/bubblewrap.
Exact scoped paths and a separate transient unit prefix reject production-unit/path
substitution. It uses a read-only retained Python image, DynamicUser, private network/user/
device namespaces, no capabilities, no-new-privileges, AF_UNIX only and hidden live paths.
Limits:512MiB memory, no swap,25% of one CPU,32 tasks,600s runtime,5s kill deadline,
idle I/O/priority19. KillMode=control-group covers descendants when the unit stops;
the ten-minute deadline bounds an orphan after SSH loss, not immediate disconnect detection.
The only writable application tree is a320MiB private temporary filesystem. Encrypted
capsules/toolkit are read-only; custody keys and independent checkpoints enter over stdin,
not argv, the journal or a persistent input directory. There is no release-signing key.

50 focused toolkit/runner tests PASS. Actual NL2 recovery is still pending at this source
checkpoint. The first no-data isolation probe refused interface enumeration through
AF_NETLINK because the configured AF_UNIX-only policy correctly denied that family;
read `/proc/self/net/dev` instead. No private input was exposed by the failed probe.
The retained image's absolute internal symlinks must be converted to equivalent relative
links before safe data-filtered extraction, with a separate transport hash. Original image
and custody inputs remain unchanged. No installed image entrypoint is executed.

This is a prerequisite of the same recovery gate, not full coherent/off-site acceptance.
Rollback stops only the exact transient recovery unit, drops its temporary memory and
preserves encrypted custody/source receipts; never restore over live state or restart
production services. Source tests are not proof of actual cgroup/mount isolation.

## Current host authorization and preflight

Owner answers “да” to the explicit current NL1/NL2 HA-02 preflight and isolated-recovery
question, without changes to working services. This resolves the13:50UTC ambiguity below;
it is not a future checkpoint-content approval or production cutover permission.
AGENTS now records the exact scope and retirement of the old Amsterdam address.

Fresh strict-pinned SSH probes complete13:53:43/13:53:44UTC. Existing id_ed25519 and
accepted known_hosts files are used, with BatchMode, IdentitiesOnly and no trust scan.
Both are x86_64/two-CPU hosts with cgroup-v2 and successful ephemeral mount/PID/network
namespace probes. No package installation, persistent remote file, live data read,
restart, new user or production configuration change occurs.

| Host | OS | Available RAM | Free disk | Full pressure, avg10 memory / I/O |
| --- | --- | ---: | ---: | --- |
| NL1 | Ubuntu26.04.1 |843923456 bytes |37511114752 bytes |1.32% /7.12% |
| NL2 | Ubuntu24.04.5 |1539735552 bytes |38119591936 bytes |0.00% /0.00% |

Both lack Docker, bubblewrap and umoci but provide Python, unshare, setpriv and systemd-run.
Do not install dependencies into working hosts to fit the laptop harness. Select NL2 for
testing an existing-systemd isolated, resource-limited recovery process; defer heavy work
on NL1. All observed Family Connect services are active. NL2 server-load has11 existing
restarts; this is a baseline, not a restart caused by these probes. Service invocation/PID
baselines and raw preflight receipts remain private under owner custody
`control-ha/20261124-recovery-hosts-01`. No continuous-health claim is made from one sample.
This preflight alone is not recovery or a coherent capture and closes no full HA-02 gate.

## Next live action — host scope reconciliation

24 November13:50UTC continuation checks the remaining practical prerequisites, not
another source/dependency rehearsal. Current owner-supplied `AGENTS.md` names
RU185.251.89.19 and NL186.246.45.246 as authorized gateways, excluding186.246.51.201.
The [collector](../../control_plane/apps/console/collector.py) and
[retained fleet inventory](2026-11-24-control-ha-installed-inventory.md#actual-installed-paths-and-source)
identify NL1 185.10.158.212 and NL2 185.10.158.196 and explicitly retire186.246.45.246.
[Earlier NL1 health](2026-11-13-amsterdam1-health.md) and
[NL2 admission authorization](2026-11-02-second-nl-ordinary.md#authorization-and-trust)
are historical evidence, not a silent amendment of the current instruction.

Ask the owner to confirm these two current NL targets for scoped HA-02 prerequisite
checks and isolated recovery without changes to working services. Until reconciled,
do not contact the retired address or substitute the current hosts. No SSH, remote
health/capacity check, custody transfer, new key trust, service stop or installation
occurred in this review. Their current availability and recovery suitability are
NOT_CHECKED, not failed. No claim that a new VPS or hosting change is necessary.

After confirmation, use existing strict SSH pins for a read-only capacity/tool/isolation
and effective-writer preflight. Select a bounded isolated recovery destination only if
it does not expose live volumes, activate credentials/dispatchers or threaten production
capacity. Separately reconcile all writer/queue entrypoints across the same fleet before
a coherent capture. The [writer checklist](../control-ha-files.md#writer-freeze-and-activation-checklist)
is not a stop-services recipe: preserve paid-watch8s/12s budgets and leases, and abort
before interruption if coverage or a disconnect-safe rollback guard is unavailable.
Host permission is not approval of the content of a future signed checkpoint.

Same remainder: independent trust, coherent all-writer/in-flight capture and complete
off-machine/final recovery are partial; isolated replication PASS. This review closes
none of those gates and introduces no new substage. Existing actual test results below
are unchanged, not rerun or promoted to whole-system acceptance. Documentation checks
cover local links and whitespace only; external URLs are not HTTP-verified. No version,
release, deployment or production rollback is involved; revert only this documentation
if the target decision changes, preserving all prior private custody and evidence.

## Actual execution — 12:31:38UTC

Source8acc6bd2be51d941f6a1eda3aea6f6a3da82cca9 was committed, pushed and independently
remote-SHA verified before execution. The accepted fourth attempt completes at
2026-11-24T12:31:38.391132Z. The standalone bootstrap runs in the retained console image
and restores419 exact committed source files plus28 wheels. A new CPython3.13 venv installs
every locked distribution offline with hashes and passes `pip check`; all distribution
origins and10 recovery entry modules resolve only to restored source/new venv. Binary
psycopg/libpq180006 is available. Original `/app`, checkout, developer venv, Docker socket,
host home and live volumes are not exposed to the namespace.

Authenticated actual retained-data results, not synthetic replacements:

- Canonical:610 rows/35 import data tables;66 migrated plus3 explicit new device identities,
  4 paid-event identities,20 referral links/63 claims, issuer/admission/sender/routing and
  empty metadata observations pass without generating new authority.
- RU/NL1/NL2:207 duplicate decisions retain their exact state;12 terminal denials and3 paid
  clock cases pass.82 peer allocations retain their floors; NL2's sequence gap remains8,
  so next allocation is9. No native engine command executes and no lease is renewed.
- Legacy worker:3 retained jobs are already expired at their capture time; duplicate,
  durable retry/restart and expiry refusal pass using in-memory adapters on a copied DB.
  No real gateway command or external-command-fence claim.
- Mailbox:9 retained files preserve sequence456216,56 dynamic and3 static members, native
  key/bootstrap/volume bindings at capture time. No daemon/spool activation.

The audit hook records zero network/process dispatch attempts. The namespace exits normally;
no daemon is started. All21 original custody inputs are byte-identical after qualification.
Two additional fresh-namespace negative checks PASS: changing one kit byte refuses before
creating restore output; changing the independent store checkpoint refuses native readback.
Neither test alters the original checkpoint/capsules.242 focused tests PASS,0 skips; two
existing Starlette/AnyIO deprecation warnings do not indicate validation failures.

| Accepted evidence | SHA-256 |
| --- | --- |
| Source/wheel kit | `95f29f3e3d698283552c41e1b3148797c96091b0a45aa0684700a31bdb7bcd76` |
| Actual cold receipt | `f7054e2783626860292fd6cf0bf30eff8090037df8914a3d8be0b1bf8f5c620b` |
| Actual negative receipt | `8dfbfae0d2429cc3f2f42947a5e30448f1afdcc3ec0d5c8f4868b319bb237e6f` |

Private evidence: owner's `control-ha/20261124-recovery-kit-01/attempt04`; source/wheel kit
has no product data. Independent kit/bootstrap pins and original custody keys stay under
the separate owner-private `control-ha-keys` location; short-lived copied inputs are private.
Earlier failed attempts are retained, not overwritten. Local separate custody is NOT proof
of off-machine survival or independent owner approval. The different historical capture
times are NOT a coherent fleet checkpoint. This run does not repeat actual OWNER-PG/post-ACK
restore; that earlier result and the final joint recovery gate remain explicitly distinct.

## Scope and trust boundary

The previous [image-loss qualification](2026-11-24-control-ha-image-custody.md) retained the
three OWNER images but still relied on the developer's source checkout and installed Python
packages for canonical/fleet recovery tooling. This change removes that dependency for the
explicit native checks below. It does not bootstrap the recovery host operating system.

`scripts/control_ha_recovery_kit.py` uses only the standard library. It collects regular files
from an explicit committed Git object, never dirty/untracked work or private state. Included
scope is Python/SQL under control, device_identity, provisioning, messenger and scripts;
the two canonical SQLite schema manifests; the native allocator/worker and two shared
desktop profile/version parser sources; and the
control, identity and HA lockfiles. Other deployment configuration, databases, profiles,
source capsules, credentials, keys and runtime state are excluded.

All28 distributions are pinned by the existing lockfiles. Downloaded linux/amd64 CPython3.13
wheels must have exactly that name/version set. Missing, duplicate, extra, mismatched or
unsafe wheel members fail closed. A deterministic tar contains the source, wheels, exact
hash-bearing install requirements and a closed member manifest. A separate checkpoint binds
purpose, Git commit, archive, manifest and standalone bootstrap hashes. This is integrity
custody, not an independent owner approval/signature or a new trust root. The checkpoint and
bootstrap must be delivered by a trusted path; taking both from an untrusted archive is unsafe.

Restoration verifies all bytes before creating a new0700 directory, writes0600 exclusive
regular files and refuses existing output, symlink paths and nonprivate parents. It never
executes an archive member. The package itself contains safe source/dependencies, not product
state; private recovery inputs and their keys remain outside Git and separate from the kit.

## Cold execution gate

`scripts/control_ha_recovery_cold.py` runs in the retained console image rootfs using
bubblewrap with all namespaces unshared, capabilities dropped and a cleared environment.
Only the kit, separately pinned bootstrap/checkpoint,21 explicitly named custody files and
an owned scratch directory are mounted. The working repository, developer venv, Docker
socket, original volumes and host home are not mounted; the image's `/app` is hidden.

The image's Python independently verifies/restores the kit, creates a new venv and uses
pip with `--no-index --require-hashes --only-binary=:all:` plus `pip check`. No wheel building,
package-index fallback or existing site-packages are allowed. The probe verifies all28 exact
versions and origins in the new venv and imports10 explicit recovery entry modules from the
restored source. A Python audit hook refuses network/process dispatch during native probes.

Required retained-data checks, not merely imports:

- Authenticate the original encrypted four-store and RU external capsules with separate
  keys/pins; validate schemas/consent-only projection and native canonical alias, issuer,
  referral, routing and sender checks at the original capture time.
- Authenticate all three node capsules; run native receiver duplicate/stale/terminal-denial,
  lease-clock and next allocator sequence checks on private copies, without engine commands.
- Authenticate the legacy worker capsule; preserve native source pins, exercise durable
  retry/restart/expiry on a copied DB with in-memory adapters, never real gateways.
- Authenticate the mailbox capsule and check its native membership, key/bootstrap/volume
  and sequence bindings at capture time, without starting Reticulum or restoring the spool.

These retained points have different timestamps. Successful checks would close this source/
Python-dependency availability gap, NOT establish a coherent cross-store capture or current
forward approval. OWNER native Django/image probes remain the separate accepted image check.

Initial preparation:239 focused tests PASS,0 skips (32 new toolkit checks and adjacent canonical,
capsule, node, worker, mailbox and OWNER-image contracts). Actual execution was then pending;
it subsequently passes above with242 tests. No runtime PASS is inferred from tests alone.
Private artifacts are retained under the owner's
`control-ha/20261124-recovery-kit-01`, with independent pins outside that kit directory.

## Failed qualification attempts and corrections

First actual attempt from source7222367599efb5da5195ad7eeb0c91c178a2e191 authenticates
the kit but bubblewrap refuses before any image program executes: `/work` cannot be created
on the read-only image root. The correction places every new input/work mountpoint beneath
the private `/tmp` tmpfs and adds a command-topology regression test. The failed attempt and
its checkpoint remain private evidence, not an overwritten success. Corrected cold execution
was pending at this correction; no production action or rollback was involved.

The second attempt from22c24c58255a0f1625f03fff8b6868743c33ed82 independently restores417
sources, installs all28 hash-locked wheels with no index and passes `pip check`. It then
refuses an absent transitive `clients` import: provisioning shares the desktop profile and
version parsers. The correction includes only `clients/desktop/profile_config.py` and
`clients/desktop/updates.py`, not a desktop GUI/install/runtime. A subprocess regression
imports the complete entry set using only copied committed sources and checks every loaded
project module's origin. No source-path fallback is added. Keep the second failed receipt;
the complete corrected cold native-data run was still pending at that point.

The third attempt fromec31ac0f0961cd0d385b6a6b2bf70a4fc2955d89 restores419 source files
and passes the complete offline dependency/import set. Native canonical preflight then
correctly rejects the probe's human-readable checkpoint label: its contract requires32 hex
characters. The correction derives that readback-only reference deterministically from both
authenticated store/file hash maps. It neither weakens the existing validator nor creates
forward approval authority. A native canonical fixture regression verifies the reference,
identical retained rows and `independent_forward_trust=False`. Preserve the failed receipt;
the corrected complete gate subsequently passes from a new committed kit as recorded above.

## Remaining acceptance and rollback

The fixed four HA-02 gates remain: replication PASS in isolation; current independent
approval/trust, coherent all-writer/in-flight capture and final complete recovery are partial.
Still required: independent off-laptop recovery-key/access custody, actual approval-authority
workflow, final coherent checkpoint and complete combined post-ACK/stale-copy
readback. No new lettered stage, live cutover or automatic next task is introduced.

Host prerequisites: Linux amd64, working unprivileged user/PID/network namespaces, bubblewrap,
the already authenticated Python3.13 image rootfs, private free disk and trusted separate
checkpoints/keys. This is not bare-metal/off-site qualification. No repository source is
substituted for an independently approved product checkpoint.

Rollback is an ordinary source revert. A failed namespace is stopped by its owning process;
keep its private log and failed capsule/checkpoint, then use a new scratch destination. Never
remove original images/containers, run production entrypoints, or write a lab DB to a live
target. There is no service/version rollback because no installation is performed.
