# HA-02 OWNER boot/resume — 26 November 2026

## Scope and provenance

Immediate priority: restore support and subscription notifications, then coherent capture.
Input feature d35db9d97a5088b15183c26ce4e0459053f71cb8 and main
be7ef1a834545ab2cf32350600500a94724e29db, both clean. Installed source remains
57c19b1ccc5f97b650ed1e2382c40286bec7c950; support archive SHA256
621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739.
No product version, release, catalog or deployment change.

Owner entered sudo authentication locally via the normal password dialog; root readback ran
with euid0 in the same PTY. No password retained/printed, no sudoers/polkit/NOPASSWD changes.
Private evidence: `~/.local/share/family-connect/control-ha/20261126-owner-resume-01` (outside Git/CI).
Original plan snapshot:60 files/241823 bytes, plus effective units and boot journals;
initial manifest SHA256 `769bd6e71561a58fa68705eec033e283ef0c6f077f42ac713620f8025da81584`.
Original entry, authority, dropin and installed collector were additionally retained separately.
This is incident evidence, not a coherent backup or independent trust acceptance.

## Proven causes

Support attempted PID4509 at12:04:20UTC on boot `2c09aa6c-4e1c-4ee9-98aa-d636ad9462f0`:
exit78/NRestarts0, now MainPID0. Root-owned0644 authority binds accepted PID3790078/start130682912
on old boot `edabe487-c37c-4dae-8c98-8b56fef2bd46`. Its SHA256 is
`afb1c670d8f66dcfab17c5b7d8a6547114ef1bcfa8ad77b759a32eacd22316af`; entry SHA256
`2578ce989b24ddfce49c600d480001aa7babe0925a235b7dcc7fb6d9d66d4b19`. Both predate reboot;
archive still matches accepted bytes. Read-only installed admission probe as fc-support with
real paths/owner returns START_AUTHORITY_CHANGED without executing the candidate. Old boot
cannot satisfy exact current-process equality. This is stale authority, not missing/unreadable
file or candidate execution failure. stderr/stdout=null explains the absent journal reason;
exit78 alone was not used as diagnosis. No terminal-failure/recovery-intent in this root run.
Historical WORKERS_REMAIN remains UNPROVEN and is not identified with this incident.

Notifications failed/1; timer active/waiting. Installed collector equals repository SHA256
`6bfe32119ecfcfe40212c1bf3d588495dac9cf82671faf7beb182537add50955`. Its first operation reads
notification_cursor through the support UNIX socket, before SSH source collection. Socket absent;
bounded root connect probe returns ENOENT. Generic journal “Subscription source unavailable;
checkpoint and queue retained” therefore does not establish an SSH failure. No real message
or collector write was generated. After recovery, actual oneshot success must still be verified;
permanent active/running is not required for this service.

## Source-only diagnostic and checks

Entry adds optional `--refusal-directory` before existing positional arguments. Receipts contain
allowlisted reason, phase, current process binding, path digests and available archive digest.
Candidate exception/exit differs from authority refusal. No arbitrary exception text, environment,
keys, user messages or locals. Private no-symlink directory, exclusive lock, limit128 records;
exclusive0600 files at most2048 bytes, fsynced, never overwrite old evidence. Diagnostic failure
cannot admit or change the refusal outcome. This option is not yet installed in working service.

Local locked Python3.14:16 diagnostic tests PASS; with handoff checks24 PASS/18 SKIP in0.42s.
Native skips are NOT qualification. Source889ef66e0e6dd36c5a5bdbc1d47b1647a9f4c5d9 is pushed and
remote SHA verified. Native CI45849023762 and Android wire45849023698 PASS; phase0/Linux remain
in progress at this documentation checkpoint. No claim that this diagnostic restores the service.

## Recovery gate and remaining HA-02

Recovery NOT_RUN. No markers/authority edited/deleted, no service restarted, no remote reclosure.
Old witness/reservation stays history, not permission for another process. Need resumable forward
operation with independently observed NL1 reclosure/drain/invalidation, new linked generation
and fresh process authority. Check IPC/history/UNKNOWN/queue/cursor/floors; qualify stale boot,
controller interruption, response loss and duplicate operation with nonempty synthetic queues.
Terminal failure stays explicit and closed, not an automatic retry loop. Existing --recover is
code rollback; --pause is not forward resume. Failed recovery may leave support closed: no older
data snapshot or old successful witness may reopen it. Original source and receipts remain intact.

Root handoff run contains no signer/custody/floor decision records; earlier accessible private
records likewise establish no independent HA signer/custodian/off-origin destination. This must
not delay support recovery. The24-file preparation manifest is not a coherent backup.
Common all-writer interval, real encrypted kit, independent exact-kit validation, all-participant
resume and full isolated machine-loss restore remain unaccepted/NOT_RUN. Three original HA-02
criteria remain partial; isolated replication PASS retained. Onboarding required/OPEN; HA-03 not started.
