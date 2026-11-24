# CONTROL-HA — offline recovery source and dependencies, 24 November 2026

Selected task: CONTROL-HA-20261123 / HA-02, existing complete-recovery acceptance block.
Preparation PASS; actual cold execution pending. No product version, installation, public
artifact/catalog, gateway policy or production service change. This is not HA-03 activation.

## Scope and trust boundary

The previous [image-loss qualification](2026-11-24-control-ha-image-custody.md) retained the
three OWNER images but still relied on the developer's source checkout and installed Python
packages for canonical/fleet recovery tooling. This change removes that dependency for the
explicit native checks below. It does not bootstrap the recovery host operating system.

`scripts/control_ha_recovery_kit.py` uses only the standard library. It collects regular files
from an explicit committed Git object, never dirty/untracked work or private state. Included
scope is Python/SQL under control, device_identity, provisioning, messenger and scripts;
the two canonical SQLite schema manifests; the native allocator/worker sources; and the
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

Preparation:239 focused tests PASS,0 skips (32 new toolkit checks and adjacent canonical,
capsule, node, worker, mailbox and OWNER-image contracts). Actual execution is pending;
no runtime PASS is inferred from tests. Private artifacts are retained under the owner's
`control-ha/20261124-recovery-kit-01`, with independent pins outside that kit directory.

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
