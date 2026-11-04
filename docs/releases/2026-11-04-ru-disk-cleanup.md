# RU disk cleanup — 4 November 2026

Owner requested removal of unnecessary disk usage on RU185.251.89.19.
Selected scope: host archived journals only; no queued implementation task resumed.

At12:21UTC, ran `journalctl --vacuum-time=14d` after inventory and approval.
This removes old archived host journals (shared system history), not just Family
Connect entries. Active journals and the most recent14 days were retained; no
rotation, configuration change or persistent retention policy was introduced.
Vacuum reported2.1GiB freed; journal usage fell from about2.5GiB to477.2MiB.

| Root filesystem | Before | After |
| --- | --- | --- |
| Used bytes | 23052984320 | 20795240448 |
| Available bytes | 6940483584 | 9198227456 |
| Used percentage | 77% | 70% |
| Available, rounded | 6.5GiB | 8.6GiB |

Immediate available-space gain2257743872 bytes (~2.10GiB), subject to live writes.
Before/after AWG PID2205322, TCP1908885, HTTP2630476 and host peer-worker1141138
are unchanged, active, NRestarts0. No service restart or VPN end-to-end acceptance.

Docker images/containers/volumes, neighbouring application services, product state,
keys/profiles, release staging, backups and private evidence were not deleted.
APT archives16KiB and root pip cache6.3MiB offered little benefit and were left alone.
Family Connect tree about3.0GiB includes2.2GiB state-product-https, deliberately kept.
No broad Docker prune, autoremove, temporary-directory purge or application-log truncate.

No versions, release assets, catalogs, deployment or server policy changed. No rollback
artifact for discarded old journals: deletion is irreversible. Remaining: monitor disk
growth; any Docker/application artifact removal needs its own ownership/reference review.
The earlier TLS-renewal failure is not repaired or requalified by disk cleanup.
