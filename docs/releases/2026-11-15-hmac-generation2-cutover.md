# HMAC generation2: authorized production cutover

Status at preparation checkpoint: **IN_PROGRESS / NOT_SWITCHED**.
Owner authorization references qualified source
`61b00409e24b92651678b817d2a6f5d4796948f9` and documentation
`ca076b7e87e4d6af3d28b2dcd70d0010574c5f8a`.
[Runbook](../operators/hmac-generation.md) ·
[Historical rehearsal](2026-11-15-hmac-migration-rehearsal.md).

Only the eight-file HMAC delta plus alias module, protected manifests and two
pseudonymization keys are in scope. No metadata schema/API/UI, beta126, paid126,
catalog or complete PR/main deployment is authorized by this cutover.

## Fresh preparation

At11:44UTC all eight installed source inputs match the qualified baseline. Both
active key copies compare equal inside the process and differ from the retained
prepared generation2 key. No key value or identifier mapping is published.
The worker socket exists with its expected owner and0660 access. Effective unit
fragments/drop-ins and ownership were captured privately; configuration backups
contain24 local and24 RU files, with verified encrypted round trips.
Free space: RU7452MiB, local root13136MiB, staging volume26922MiB.

Production panel image remains
`sha256:61e4df54f1e1b83011b03427ec96e8941f9060173f7f756cbb4f1979fac81ad7`.
Qualified minimal candidate remains
`sha256:e44c342383f53feea8414f51033264079b7bfa86247c0b69e8dda2ad2510245d`.
These observations do not claim candidate activation.

Fresh online SQLite copies pass integrity checks; PostgreSQL restores with
`--exit-on-error` in a network-isolated tmpfs container. Six encrypted data/key/
manifest round trips pass. Fresh copies contain66 canonical devices/4 canonical
events and8 pinned support contacts (the previous rehearsal had7).
All checked references map with0 missing/conflicts. Real-copy replay preserves
16 non-binding records,2 request identities,8 pins, baseline/cursor and restart;
0 messages sent. Panel replay preserves6262 subscription snapshots,4 events,
959704 inventory rows,106197 audit rows and0 labels; existing cardHTTP200,
no event duplicates, historical immutability enforced, partial activation rejected.
These are pre-pause observations, not the final paused coverage frontier.

## Pending activation gates

Drain collectors and worker in runbook order. Require socket existence before
SIGTERM, inactive/exit0, released store lock and normal socket disappearance within
40s. Never delete the socket for PASS. Then pause chat-sync, refresh consistent
copies/full coverage, install matching aliases/minimal overlays, switch both keys
and resume verified projections, original cursor and timers. Record actual results
here, including any BLOCKED gate and safe recovery, before claiming SWITCHED.

Public beta125 and paid108/119/123/125 remain unchanged. Metadata release still
needs the signed candidate, compatible ARM64 upgrade125→126, exact paid descriptor
and installed APK→API→panel qualification. No real notification receipt is claimed
without a new naturally occurring event.
