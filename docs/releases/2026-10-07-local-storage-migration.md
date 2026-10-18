# Local workstation storage migration — 2026-10-07

This is workstation maintenance, not a release. No application versions, installed
clients, public artifacts, invitation pages, update catalogs or gateways changed.

## Completed

- Created `/dev/nvme0n1p7` only in the previously unallocated322GiB extent on
  `/dev/nvme0n1`; the six existing partition records were verified unchanged.
- ext4 label `LinuxData`, UUID `555f6113-dfe5-4df8-9ce4-7ea92be8c1b3`, mounted at
  `/mnt/data`; UUID-based fstab automount uses `nofail`. User joker owns the data.
- Six personal folders moved into `/mnt/data/joker` with original-path symlinks.
-37 further directories moved: inactive Family Connect build trees/artifacts,
  `.fc-xhttp-build`, guitar-school, Steam/Lutris/umu data, JetBrains data/cache,
  pip and Go build caches. Exact local inventory:
  `/mnt/data/joker/migration-20261007-115441.json`.
- rsync preserved permissions, timestamps, internal hardlinks, ACLs and xattrs;
  checksum dry-run comparison completed before removing originals. Busy-process
  checks guarded the heavy-directory switches. No retained transfer backups.
- Verified joker read/write/traverse access through all37 old-path symlinks.
  Family Connect Git discovery passes. guitar-school has no discoverable Git repo;
  no Git-history validation is claimed for that directory.
- Root:156GiB total,112GiB used,36GiB available,76% used. Data:317GiB total,
  30GiB used,287GiB available. Approximately27GiB freed in the heavy-data pass.

## Remaining / limitations

Active field65-export16 (~13GiB), Codex packages/state, browser, Docker, signing-key
directory and MicroTrader were intentionally not moved. No processes were stopped.
Remaining project-tree/Codex migration needs a separate maintenance session outside
the affected tree after all writers stop. Running-container data requires a separate
explicitly scoped service-maintenance plan. No application GUI/runtime acceptance
or reboot test was performed; preserved paths do not prove every application works.
Chromium and Thunderbird already have connected Snap removable-media interfaces.

## Access and rollback

Keep opening existing paths under `/home/joker`; symlinks redirect migrated entries
to `/mnt/data/joker`. Do not delete links or unmount the volume while applications
use it. For any later rollback: stop writers, ensure root has enough space, copy the
selected target back to a temporary adjacent directory preserving metadata, compare
checksums, then replace only its symlink with the verified directory. Retain the
new-volume copy until application checks pass. Do not blindly restore the old
partition table: it predates the new filesystem and is not a data rollback.

Initial partition-table/fstab backup: `/root/disk-backup-20261007-114835`.
Verify automount after the next user-approved reboot; no reboot was initiated.
