# RU availability recovery — 17 November 2026

**RECOVERED_CAUSE_OPEN at00:02UTC.** The owner's explicit request to restore RU
authorizes only the existing guarded recovery after the16 November22:07 watchdog
cascade. It does not select a new observer, runtime patch, APK, key rotation or paid
policy. The [initiating incident evidence](2026-11-16-ru-recurrence.md#new-recurrence--16-november2207utc)
is preserved. Recovery is not proof that its initiating stall has been fixed.

Entry source/remote main is `86663dfea4ce9758948acb3dab5c8a5ebfb3cf05`, following
ordinary PR38/PR39 merges. Source merge7123b95e has all ten workflows PASS, including
Android133670910620; documentation merge86663dfe has phase0 PASS. These earlier CI
results are not a new execution of this documentation-only recovery receipt.
The dedicated worktree fast-forwards without altering the dirty primary checkout.

## Fresh guards and backups

At23:54:30UTC16 November, AWG is failed/timeout, TCP inactive and watcher in its
automatic restart loop. Current command map, archive/effective-unit/ownership guards
pass,7,320,997,888 bytes are free, and both active HMAC key copies agree inside the
process. Generation2 manifest SHA256 remains
`8602e6526ca1ec0e408c99a7ca37aedc4413b417f392e32096d5167517fcdcb8`.
No secret, raw identity, mapping or configured SSH command is emitted.

| Accepted component | SHA256 |
| --- | --- |
| RU transport node | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| RU gateway | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| Effective watcher unit | `659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e` |
| HTTP | `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` |
| Operator | `19efd0b46fb145dcef06a9a092ee0d8ee4d062d09d99b1b0e0065425be02d90f` |
| Reconciler | `ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa` |
| Panel image | `5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da` |

At23:54:49UTC a fresh consistent canonical backup passes isolated restoration of
all27 tables, exact fingerprints/integrity/FK checks and all three exact-runtime
paid projections. Backup SHA256:
`27af271b21ee44a66f6b123047743b369ff26922c181b63045bf5a05d4180099`.
The paused backup is encrypted off-host with a separately retained local key;
190,103 encrypted bytes, SHA256
`217f9769b096826ceab4e1d1141b78d4bcd87184298725e42d2c7c475b8fa1d0`.
Decryption/digest roundtrip passes. No live DB is replaced by a backup.

## Pause, start and renewal

At23:55:32UTC the RU-only central command fence, reconcile drain and grouped
watcher/AWG/TCP stop prove PID/control PID0, no relevant jobs and zero gateway
handlers. NL command entries remain unchanged and their renewal path stays enabled.
Retained66 records/20 peers pass preflight. The original first-failure file is
preserved byte-for-byte while stopped, SHA256
`80639df0b1666340813885ccf92ccb10ed435291088bab6d6ad1b1e2c5c1531b`.

Unchanged watcher/AWG/TCP start at23:56:22UTC; the complete original three-node
command map is restored. Fresh process anchors are watcher3176861, AWG3176865 and
TCP3176877. HTTP2935828 and peer3967036 retain their entry processes. Support/panel,
NL services and paid reconciler timer are not restarted. No MESH service, transport
deadline, dependency, persistence rule or paid admission policy is changed.

The first observation reader fails with FileNotFoundError because a reused wrapper
selects the prior incident's convergence anchor. Its empty stdout/error receipt is
retained. Correcting only that filename to this recovery's actual `started.json`
allows the original strict PID/invocation/restart and data assertions to run.
No convergence anchor is created, process mismatch accepted, or assertion removed.

Six strict successful observations at23:58:21,23:59:18,23:59:55,00:00:31,00:01:08 and
00:01:45UTC span203.900s. Every observation has66 applied records and exact20 AWG/20
TCP actual and persisted bindings. The initial cohort lease deadline1794873610 is
crossed and advances to1794873812 through ordinary reconciliation. All five process
anchors remain unchanged, NRestarts0, revisions applied and command map restored.
This is more than an active-service or single startup check; no client traffic test
or new payment, term change or message is performed.

## Preservation and final readback

At00:02:29UTC the final strict check again passes actual/persisted sets, revisions,
transport identity/membership/terms/prepared state, effective units, HMAC2 files,
archived first failure and every protected canonical fingerprint. Fresh protected
counts are devices66, invitations121, subscriptions/events1/4, chat bindings/service
senders53/1 and referral links/claims19/59. These counts accompany fingerprint
comparisons, not historical expected values substituted for a fresh baseline.

At00:02:31UTC the working panel contains recent ordinary RU/NL transport imports,
RU inventory, subscriptions on HTTP4e2df679 and metadata, all source reads successful.
NL registry `not_collected` remains the intended source boundary. The panel image
and read-only aliases mount are not replaced. IPC history/cursor reads pass; original
baseline/cursor position4, baseline time1794660500, four excluded events and matching
anchor remain, with no source error or selected-device jobs. Real new notification
delivery remains NOT_OBSERVED. No baseline reset or historical dispatch is triggered.

The retained metadata row remains revoked, epoch6/sequence116, zero groups and no
geographic projection. The read-only panel probe initially used an incorrect Django
module name; that local reader error is retained and corrected to the installed
project's `fc_control_plane.settings`. PostgreSQL statement timeout2s and process
alarm10s bound the corrected read. No application row is changed by the probe.

Verified HTTPS still serves unchanged signed catalog9, SHA256
`ccad442cd87bbb9a880383de4641f2f1aacc0296944de193923e0c1b1f4ddd29`.
Public signed APK4f288cbb, sourceba3e9370, exact paid-v2 and previous108/119/123/125
admissions remain as in the [release receipt](2026-11-16-android126-publication.md).
No phone operation, build, signing or publication is repeated.

## Limits and recovery posture

Availability is restored on accepted bytes. The original watchdog stall remains
CAUSE_OPEN: this recovery does not identify its blocked syscall/process or prove a
durable recurrence fix. No broad journal scan, live pressure reproduction, new
observer, deadline relaxation or automatic recovery loop is introduced. Preserve
the bounded incident evidence and current generation2/data. If another failure
occurs, use fresh guards/backup and the [guarded procedure](../operators/subscriptions.ru.md),
not an old DB/key rollback or a watcher-only restart.

This is an operational receipt and the author's own scoped review, not independent
approval, a new runtime qualification or a physical VPN-traffic PASS.
Documentation validation covers seven files/883 links with zero errors and passes
whitespace review. Private recovery scripts, receipts, backups and keys stay outside
Git; this change adds only documentation, not a production deployment.
