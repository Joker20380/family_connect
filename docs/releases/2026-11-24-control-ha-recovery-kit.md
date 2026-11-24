# CONTROL-HA — offline recovery source and dependencies, 24 November 2026

Selected task: CONTROL-HA-20261123 / HA-02, existing complete-recovery acceptance block.
Actual cold execution PASS; complete HA-02 remains IN_PROGRESS. No product version, installation, public
artifact/catalog, gateway policy or production service change. This is not HA-03 activation.

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
Still required: recovery-host OS/tool availability, off-machine independent custody, actual
approval-authority workflow, final coherent checkpoint and combined post-ACK/stale-copy
readback. No new lettered stage, live cutover or automatic next task is introduced.

Host prerequisites: Linux amd64, working unprivileged user/PID/network namespaces, bubblewrap,
the already authenticated Python3.13 image rootfs, private free disk and trusted separate
checkpoints/keys. This is not bare-metal/off-site qualification. No repository source is
substituted for an independently approved product checkpoint.

Rollback is an ordinary source revert. A failed namespace is stopped by its owning process;
keep its private log and failed capsule/checkpoint, then use a new scratch destination. Never
remove original images/containers, run production entrypoints, or write a lab DB to a live
target. There is no service/version rollback because no installation is performed.
