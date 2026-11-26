# HA-02 OWNER boot/resume — 26 November 2026

## Scope and provenance

Immediate priority: restore support and subscription notifications, then coherent capture.
Input feature d35db9d97a5088b15183c26ce4e0459053f71cb8 and main
be7ef1a834545ab2cf32350600500a94724e29db, both clean. Installed source remains
57c19b1ccc5f97b650ed1e2382c40286bec7c950; support archive SHA256
621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739.
No product version, release or catalog change. Bounded support/controller recovery is recorded below.

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
cannot admit or change the refusal outcome. Initially source-only; installed during the recovery below.

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

## Working recovery — 16:57 UTC

Installed recovery tooling source14d4dfadb212346a251bb9698246ba8dbdef8876 has all nine applicable
exact-SHA workflows SUCCESS: native45858924374, phase045858924449, Linux control45858924561,
Linux candidate45858924426, Android45858924419, console45858924520, messenger45858924393,
notifications45858924619 and voice45858924474. Downloaded native artifact15137712614 SHA256
`29cb893f1c96e7bc0d937b56b9716015cf6ce63eb65c7bcdd486275a8e265ac3` independently verifies
323 executed cases/zero skips/failures/errors and the exact source SHA. Public-source tar SHA256
`cb9f2b92055b9b517c7d148c554e1bf718dffd99593b1e03a5438fd547e4ff49`; all370 files independently
match on OWNER/NL1. Immutable tooling capsules use `ha02-tools-14d4dfad` / `tools-14d4dfad`.
Product archive remains accepted621009b8 and its accepted57c19b1c source; no client version bump.

OWNER operation `/opt/family-connect-support/ha02-forward-20261126-01`, participant
`/var/lib/family-connect-support/ha02-forward-20261126-01`; NL1 operation
`/opt/apps/family_connect/state-ha02/forward-support-20261126-01`. Previous root plan, authority,
history and every receipt are retained. Current OWNER PID757814/start1751064 on boot2c09aa6c…,
active/running/NRestarts0, exact accepted archive/runtime sampled. New authority SHA256
`b9b9667164742c545552bca9a16aea0fb3c5d66f9ca8ff7d105bba8e0273e059`. New linked mailbox generation
`98aaff1185c7bb33999d9591c0bd9d2880207ec339ca29c38f45aef1f6a6eb72`, NL1 PID3705 unchanged.
Independent root endpoint confirms exact consumed request/ticket and OPEN_LOCAL_ONLY. Fresh
preflight retained CPU100%/MemoryMax768MiB and sufficient available memory before reclosure.
No other mailbox clients were restarted. Repeating the same OWNER recovery succeeds without
another process or authority. No old authority/marker edited or deleted; no data restored.

Independent process/IPC/SQLite reader, separate from the resume implementation, confirms21 records,
all12 decoded message records exactly equal, identity/other records retained, cursor4
and identical cursor record, jobs0. Only support-bindings changed during normal refresh. Five
pre-existing gate markers in the new plan remain; live pending count7 is not a claim of seven new
UNKNOWN outcomes. The old seven UNKNOWN outcomes remain historical evidence. All60 original root
records compare exactly with the retained snapshot. A first reader demanded equality of the whole
pending directory while runtime operations were active; that assertion was too strict. Correct
readback explicitly checks preservation of every prior marker and separately reports live count.

Normal subscription notifications invocation16:57:26–16:57:27UTC: return0, Result=success,
ExecMainCode1/ExecMainStatus0; oneshot inactive/dead afterwards is expected. Timer enabled,
active/waiting with next deadline. No artificial user messages were created. Startup diagnostic
directory is installed and private; candidate authority still fails closed on later PID/boot changes.

### Retained operational refusals and bounded correction

Initial rollover orchestration refused GENERATION_SOURCE_PIN before advancing: the orchestration
imported the helper from the tools capsule, while the immutable plan pinned its staged copy. NL1
remained closed/drained with old opening invalidated; OWNER was not started. The already qualified
staged endpoint was used for the same immutable operation, not a new permit or modified plan.
Its advance response then encountered UNSAFE_CONTROL_FILE after effect. Fresh current-generation
readback (not replay of the old ticket) proved the transition applied and remained closed/drained.
Retained response SHA256 `47a0b621e9ae96eaaf4ffdb0e94740d9f83b6b189ba77085aa9c61dba8b23c17`
has the exact nonce/new manifest; later ownership996/nlink1 verified. Original transient link count
was not sampled, so its unique live cause is not asserted. The hardlink publication window in
`admission.write` was reproduced synthetically: exclusive target briefly has two links before
temporary-name removal; the old reader rejected it before the completed receipt was available.

Follow-up source makes tool-origin controllers inject the exact pinned staged helper, checking
equality with their own source. Bounded response reading waits only for the safe two-link publication
window to close; no unsafe bytes are consumed. Persistent extra links, wrong owner/permissions,
missing response and changed inputs remain refused/unknown. Fresh regression checks cover both
advance/resume from a separate tools path, staged drift, transient/persistent publication and unsafe
response files. This follow-up is not silently substituted into the accepted operation's source pins.
Final focused locked/native follow-up selection56 PASS/0 skips in95.04s; its exact-source CI is
pending at this source checkpoint (the working14d4dfad nine-workflow result remains separate).

Rollback is code-only with independently reclosed/drained/invalidated mailbox and retained current
data, never an older store restore or direct old-process restart. An already accepted support
instance must not be interrupted merely to install the controller follow-up. Future boot/resume
uses a fresh linked operation with the corrected tooling after its exact-source CI. Terminal failure
remains explicit and closed; old --recover remains code rollback and --pause remains remote-only.

## Remaining HA-02

Fresh16:35UTC RU/NL1/NL2 census retained under `20261126-capture-preflight-02`:32/9/5 units,
all four RU database schema observations unchanged from14:38 census; no default Friends stores on
NL1/NL2 does not mean no node state. RU directory-sync service/timer changed during observation:
this is evidence of live scheduling, not a common stable interval. Current prior OWNER overlay
candidate sources still match all10 repository inputs, but neither OWNER common gate nor all
manual/direct-ORM paths are thereby installed or attested. No fleet capture was attempted while
repairing the support incident. One NEXT remains actual coherent capture plus independent reader
and normal participant resume, not another inventory milestone.

Root handoff run contains no signer/custody/floor decision records; earlier accessible private
records likewise establish no independent HA signer/custodian/off-origin destination. This must
not delay support recovery. The24-file preparation manifest is not a coherent backup.
Common all-writer interval, real encrypted kit, independent exact-kit validation, all-participant
resume and full isolated machine-loss restore remain unaccepted/NOT_RUN. Three original HA-02
criteria remain partial; isolated replication PASS retained. Onboarding required/OPEN; HA-03 not started.
