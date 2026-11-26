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
Native skips are NOT qualification. Diagnostic commit889ef66e0e6dd36c5a5bdbc1d47b1647a9f4c5d9:
all four applicable exact-SHA CI SUCCESS (native45849023762, Android45849023698,
Linux control45849023662, phase045849023655). New transition source requires its own CI.

## Forward transition qualification (not working installation)

`control_ha_support_resume` creates a new immutable root operation, entry/authority paths and
linked plan, retaining old authority/reservations and pending markers. It distinguishes new-boot
absence from proven clean same-boot exit; neither settles historical uncertainty. Independent NL1
reclosure/drain/invalidation is mandatory before starting any new writer. `control_ha_mailbox_rollover`
stages a new closed-on-restart manifest and advances the existing installed native fence without
restarting working NL1 or admitting old links. Its limits remain100% CPU/768MiB; fresh memory preflight
requires at least256MiB available. Busy/changed inputs refuse with retained evidence.

Fresh process authority is issued once through the checked existing startup procedure. A distinct
OWNER_FORWARD_RESUME witness does not misrepresent the old graceful handoff witness. Response loss
is reconciled through independent readback; repeated same operation is idempotent. Terminal failure
cannot restart or open. Controller interruption before authority expiry resumes the same process;
after expiry, START_AUTHORITY_MISSING plus exact absent-process evidence permits a new linked
attempt in another root/generation, retaining the ended attempt and every marker/receipt.

Focused locked native final selection48 PASS/0 skips in225.52s.
Actual-root OWNER/NL1 disposable fixture: root-forward-native-02 PASS/1 in50.33s;
extended root-forward-native-03 PASS/1 in76.63s. Includes genuine new OWNER PID, immutable old
authority, nonempty synthetic notification queue/cursor42 unchanged, authenticated fresh NL1
generation without process restart, duplicate resume, synthetic support/peer packets, remote
restart closing admission/new ticket, stale ticket refusal and OWNER restart refusing old authority
with a persisted START_AUTHORITY_CHANGED receipt. No real users received qualification messages.
Working NL1 PID3705/source/config unchanged; fixtures stopped and scoped cleanup verified.

Retained first root-forward-native failure is fixture accounting, not WORKERS_REMAIN: old process
exited0 with workers0/stores closed, but unreferenced systemd unit accounting was garbage-collected
before sampling. Harness now uses the existing accepted supervisor/RemainAfterExit lifetime.
No exit-proof condition was weakened; failed evidence remains private alongside successful runs.

Stopped OWNER private state readback:21 encrypted records, notification cursor4/jobs0;
incoming received5, outgoing relayed5/recipient_stored2. Historical7 UNKNOWN retained in original
evidence, not reclassified by these counters. Snapshot manifest15 files/213687bytes SHA256
`6af197e022ef0cbc59478e62736c7b99fd50de1c29bbeb13eea1b776ebfd77c8`;
store DB SHA256 `2e557d3d2dc811461f349b004d4979790698c324097fe091a552f523740c8109`.
Temporary duplicate key removed after equality check; original untouched. This stopped snapshot
is incident preparation, not a coherent all-participant kit or independent custody.

Subsequent boot procedure: first preserve records and prove accepted predecessor process absent;
prepare a new OWNER root/participant with `--prepare-from`/`--participant`; construct fresh NL1
manifest from that exact new plan and prior accepted binding; stage rollover then activate with
independent readback. Copy retained predecessor-reclosure and verified channel into new OWNER root;
run resume with `--root`/`--mailbox-channel`, then independently verify IPC/runtime and normal
notifications oneshot/timer. Reuse the same operation only while its bound process/ticket survives;
otherwise fail closed and prepare a qualifying linked new attempt. Never edit old authority, delete
markers, auto-retry terminal failure, restore old data or use remote pause as local-store barrier.

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
