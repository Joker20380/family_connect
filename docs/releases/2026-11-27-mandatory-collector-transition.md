# Mandatory collector / support maintenance transition — 27 November 2026

## Prepared successor, not yet installed

Current accepted service remains `ha02-forward-20261127-panel01`, support archive
621009b8 and unchanged installed collector192343eb. Panel/dependencies normal
baseline is accepted. The brief separate MESH incident was recovered on unchanged
gateway bytes; see [operational evidence](2026-11-27-mesh-recovery.md).

The new explicit baseline name is `owner-collectors-b7f4cbd2`. Its exact source
binding is collector commit `b7f4cbd2b96750cb9c97eee61f27a9881d5b4bdb`:

| Path | SHA256 |
| --- | --- |
| control/capture_gate.py | da28d940e2e17e2dbb1fbbde8cc04c59d29cffc8762ada717135504e2ffa4906 |
| provisioning/owner_capture.py | b7b1fb3ffe69d9428cb419a30d2473a2bb73a6ffb2e7c6390b6878afc953a45d |
| provisioning/support_bindings.py | afba534e17ec3a57f5431bd611d66b94a56f7e5f969e167ca5afe2834d430bc2 |
| provisioning/subscription_collector.py | 3bb9954c8edfba64f4b2aeb63fb174669fa2fc8e37f71c193c9a18da895193cb |

The original192343eb variant/pins and original19-file baseline manifest remain
unchanged. Old panel01 plan, authority, source capsule and receipts are not rewritten.
New tooling selects only an explicitly reviewed source variant for observation,
stopped capture or absent-predecessor preparation; it never silently upgrades a plan.

## Compatibility qualification

The new observer checks current source closure before cursor IPC/SSH, exact live
PID/boot/start/argv/cgroup, unchanged archive/authority/accepted history, retained
runtime attestation and the independently observed NL1 consumed request/open fence.
Its production mandatory mode checks the independent binding in a fresh isolated
Python process with no unit environment. It does not call Resume.run, terminal
reconciliation, attestation injection or recovery record writers. Failure is read-only.

The isolated native transition starts from a genuinely accepted192343eb forward
operation with nonempty queue/cursor/history, switches exact collector source only,
observes twice without changing history bytes/mtimes or live binding, and proves
unknown/changed/missing/extra sources refuse before IPC/SSH. Live prepare refuses.
Stopped support captures and independently verifies/repeats with the successor
selection, preserving data/markers and strict unsettled drain. Forward recovery
uses a new operation/authority and retains queue/cursor/predecessor bytes. Both clean
exit and simulated prior-boot accepted evidence are covered; the latter qualifies
the BOOT_CHANGED branch with real systemd stop/new-process startup, not a physical
reboot of the owner's live host.

Initial targeted run:16 passed. Broader local/native exact-source CI and fresh
installed readback remain required before activation. Source preparation is not an
installed result or common HA capture. No old completed Resume.run is used as health.

## Installation and recovery boundary

The intended new collector operation starts from a fresh panel01 observation, not
the interrupted pre-boot plan. Preserve original units, projections, gate inode pins
and private source rollback bytes. Hold only the two root collector timers, wait for
their existing invocations to finish, and keep strict collector admission/operations
barriers during the bounded source/binding transition. Do not stop support, replace
its archive/authority or change the NL1 generation. Qualify installed refusal before
I/O, normal service/timer cycles and read-only compatible observation before acceptance.

Retain a prestate/source rollback path; never restore projection/database/cursor
contents or clear historical markers. After any partial install, reconcile recorded
phases and exact bytes before another mutation; do not blindly replay preparation.
Keep the new qualified maintenance capsule alongside the old immutable capsules.
Console/publisher12-file installation, manual/external-dispatch closure, fresh common
capture/independent verification/normal resume remain subsequent work in the same NEXT.
Separate inventory3+12, probe14 and support33 markers remain unresolved history.
