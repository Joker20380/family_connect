# 15 November 2026 — owner laptop disk maintenance

## Selected scope and outcome

The owner ultimately selected freeing the system filesystem `/` and stopped further
cleanup of `/mnt/data`. This is local host maintenance, not a Family Connect release,
deployment, platform acceptance or authorization to resume the engineering queue.
No client/server version, installer, update catalog or public download changed.

| Filesystem | Session-entry available space | Final observed available space |
| --- | --- | --- |
| System ext4, `/` | about1.1GiB,100% reported used | about19GiB,89% used |
| LinuxData ext4, `/mnt/data` | about408MiB,100% reported used | about27GiB,92% used |

Values are rounded live `df -hT` observations, not an exact sum of deletion receipts.
The root-space improvement includes a reserve adjustment as well as cache deletion.

## Completed root actions

- Removed19 disabled Snap revisions through Snap; current versions and user data
  were retained. Their4.153GiB archive total is not entirely an immediate disk gain:
  some files also had links in Snap's download cache.
- Removed only regular Snap download-cache files older than7days. Preflight found
  about4.575GiB immediately reclaimable; this must not be double-counted with the
  disabled-revision archive total.
- Reduced root ext4's reserved-block percentage from5% to1%:2078412 to415682
  reserved4096-byte blocks. This makes about6.343GiB available to ordinary users
  while retaining about1.586GiB for root; it does not delete data.
- Removed9 inactive cached app-server-daemon releases,3,958,206,464 allocated bytes
  (3.686GiB). Retained current0.162.1 and previous0.162.0, all standalone releases,
  running executables, conversations, configuration and worktrees. The package
  install lock was held and the current pointer checked throughout.
- Docker builder pruning with an age filter first reclaimed0B. The subsequent
  unused build-cache-only prune, retaining1GB, reported1.676GB reclaimed. No image,
  container or volume pruning was run; final running-container count remained18.

Old test VM images in `/var/tmp` were inspected but not moved, compressed or deleted.
No application or container service was stopped or restarted by this maintenance.

## Earlier data-partition work and mount investigation

There is one physical approximately1TB SSD. LinuxData is a separate322.3GiB partition
on it, with about317GiB filesystem capacity, already persistently mounted at
`/mnt/data`. Home folders, the Family Connect checkout and several application
cache/data directories already link there. No new mount was needed for LinuxData.

Before the owner narrowed the scope, about25.894GiB of recognized Go build-cache
files older than7days were removed from this partition. Only ordinary single-link
files matching Go's hashed cache layout were eligible. An initial user-level pass
stopped on container-owned cache files; the administrator continuation reported
15.932GiB removed. Subsequent `/mnt/data` investigation was read-only and then
stopped. Source capsules, keys/profiles, databases, evidence and emulator images
were not selected for deletion.

The435.5GiB NTFS partition contains Windows, rather than an empty new disk. It was
mounted read-only for identification and then unmounted, without deleting data.
The separate36.7GiB `New Volume` is nearly empty but has NTFS's dirty/check-required
flag. Its normal read-write mount was refused by the kernel. No force option,
formatting, dirty-flag clearing or write repair was used. A non-writing `ntfsfix`
inspection passed its limited metadata checks; that does not clear the dirty flag
or substitute for Windows `chkdsk`.

`New Volume` is left temporarily mounted read-only at `/mnt/extra`. The attempted
persistent setup stopped before changing `/etc/fstab`; the original was backed up
as `/etc/fstab.before-extra-20261115`. The original LinuxData automount entry remains.
No automatic write-mount or filesystem repair is a queued next action.

## Verification, recovery and limitations

Final root `df -hT`:156GiB total,136GiB used,19GiB available,89% used.
Docker reports18 running containers, as at the initial inspection. This is not
application-level health testing. No repository test suite was run for cache-only
host maintenance; documentation receives link and whitespace checks separately.

Caches regenerate/download as needed; the next build may be slower. Removed Snap
or cached application versions require re-downloading for an older-version rollback.
If separately requested, the root reservation can be restored with `tune2fs -m 5`
on the verified root device; doing so reduces ordinary-user available space again.
The temporary NTFS read-only mount can be unmounted when not in use. Do not force
it writable; Windows filesystem checking or any repurposing needs a separate
explicit decision. No further cleanup, repartitioning or migration is started.

Existing unrelated edits are preserved. At entry the local main branch was already
ahead6/behind205; this maintenance does not authorize merging or rewriting it.
