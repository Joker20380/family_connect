# OWNER console/publisher installed component — 27 November03:10UTC

Task CONTROL-HA-20261123 / HA-02. `owner-console-publisher-7a91d127` is INSTALLED
and checked as a component, **not full OWNER/all-writer or common-capture PASS**.
Mandatory owner-collectors-b7f4cbd2/observer8b9355db remains accepted and unchanged.
[Earlier availability, exact NL1 failure and NL2 traffic recovery](2026-11-27-owner-all-writer-next.md)
is historical pre-install evidence, not a conflicting current pending-install state.

## Exact installed bindings

- Source: `7a91d1278eda8594e448e5794e183e313aed8440`, retained12-file overlay.
- OCI archive: `42ffb2afbe8e0752507ecf6c9842c19a7e3ab1b308d568f9082320b71cf4b6d1`.
- Console image: `sha256:3af9fbf95b36b33f1c0414ac41b84687f502391e311ff0bc35658cbf50da5cb1`;
  container `fb1e6e6455f706cc212b5e55e3ed0ff6894bfa3652afd2df8c24514cf048a5b2`.
- Publisher image: `sha256:35158514371e2a321643dbfe4b64b9a87a9b85b32228a5184d2c95e3b8ac19e8`;
  container `505d10bc520a787859f0d528400e4043ff32fc87af8513e1ed5947854a20536f`.

Both running namespaces independently match all12 file SHA256/size pins. Effective
configuration is compared against the original; only image and reviewed gate env/mount
additions differ. Existing data volumes, localhost8765, support socket, credentials,
security/resource settings and workload commands remain. No base Compose/seed_demo
startup, product database restore, PostgreSQL recreation or support restart occurs.
PostgreSQL retains its original container/PID/volume; no new migration is pending.

Separate persistent gates under `/var/lib/family-connect/capture/` are `owner-console`
(10001:10001) and `owner-publisher` (1000:1000), mounted at `/run/family-connect-capture`.
Directory/pending0700, locks0600, host/container device/inode identities match.
The prior exact7a91d127 four-workflow/native image qualification is reused only after
independent verification of the retained OCI closure, not as evidence of deployment.

## Installed checks and preservation

- Closed HTTP503, reopened200. Both fresh processes with FC_CONTROL_CAPTURE_GATE unset
  discover the mounted gate. Unscoped direct ORM, closed admitted work, four management
  commands and conflicting overrides refuse before the database-I/O sentinel runs.
- Both normal no-environment admitted ORM reads succeed and close the real connection.
  Migration plan has all entries applied. A later publisher cycle timestamp proves a
  completed loop after closure, not just a live PID. No test message/business write.
- Real login, overview/subscriptions/payments/two existing cards/logout PASS.22
  business/fleet/authorization/migration tables retain identical counts/row digests.
  Automatically updated observations and normal login/session changes are explicitly
  excluded from equality, not claimed frozen. No data/queue/cursor rollback occurs.
- Old containers are retained stopped under journal-bound names; no forced stop was
  requested. Their PostgreSQL client backends are absent before candidate startup.
  Earlier guarded publication readback has draft/queued/unknown/refused0,published1;
  that short boundary is not a remote-settlement or capture permit.
- Docker events match create/start/exec_die0 for three normal inventory imports, three
  probe imports and one technical-metadata import. Recent complete ledgers total14
  console and4 publisher execs, including checks; bounded daemon history is not an
  exhaustive historical census. Actual strict local drain passes on both new empty
  gates only. No historical marker is removed or reclassified as settled.
- Initial resumed and later automatic monitor/probe services succeed0; own holds only
  removed, timers enabled/active/waiting. Notifications complete0 at03:07:01UTC.
  Observer8b9355db preserves supportPID240065/boot/start, archive, authority, NL1
  generation, cursor and history. Root119 and inventory21 (3+12+6)/probe14 retain exact
  bytes/inode/mtime; support33 is separately unchanged. Histories remain unsettled.

Support runtime directory remains fc-support:fc-support-ipc0750, with matching actual
host/container mount identity. Its existence before console startup is still mandatory:
this installation does NOT fix or qualify automatic reboot startup. At03:10UTC MESH
PIDs2011396/2786473 remain active, NRestarts1/0; bounded traffic PASS is not sustained stability.

## Retained refusals

Private journals retain, rather than flatten into PASS: an active-child publication
probe refusal; operation01's stopped-network runtime mismatch before candidate creation
and normal original-container/panel recovery; an attached read-only exec client timeout
with later server exit0; isolated tmpfs output-copy refusal; and a live health-exec
stop refusal. Stopped proposals subsequently use strict effective-config equivalence:
two positive/eight mutation-negative cases pass. Corrected root-authorized namespace
output readback passes three isolated success/error/empty-output cases.

Operation03 records exec IDs before dispatch and separates server terminal state from
output. The39-table read-only digest query exceeds the client wait but finishes
naturally; its later query-bound cancellation matches no backend and cancels nothing.
Late Docker GC of that exec metadata is a retained limitation, not invented evidence;
its output is preserved and the22-table later comparison is separately bounded.
A verifier's digest-string versus SHA256/size-object comparison refuses after startup;
independent readback proves all12 hashes/sizes equal. Only verification is corrected,
not candidate bytes. The expiring user-hold controller leaves timers stopped; unchanged
unit bindings/own hold records are checked before explicit resume. No retry loop or
foreign backend cancellation is used to hide these commissioning failures.

## Rollback and remaining NEXT

Private `/mnt/data/fc-owner-next-20261127/root/owner-install03` retains fresh prestate,
proposals, exact per-role replacement manifests/receipts and original stopped IDs.
Code-only rollback uses the existing qualified stopped replacement/revert procedure:
hold affected dispatchers, finish/bound known work, stop the candidate without force,
check identities, revert its journal and start the retained original only after checking
the support runtime mount. Never run both generations, restore product DB/queue/cursor,
replay old support Resume or invoke base Compose seed_demo. Preserve every phase record.
No client version, installer, public catalog or release tag changes.

Concrete remaining gap: host `collector_admission.cycle_lock()` and inventory direct
admission still depend on inherited FC_CONTROL_CAPTURE_GATE outside containers;
direct `collect_technical_metadata.collect()` has no independent gate. These manual/
no-environment paths need qualified mandatory role bindings and source closure. Recent
Docker terminal receipts and stopped old containers do not settle every older external
UNKNOWN. No fresh common RU/NL1/NL2/OWNER capture is attempted before that gate closes.
The subsequent cycle must hold proven barriers, take a new stopped-support snapshot,
independently verify and normally resume. Gate.drain stays strict; e4eace1a is history.
Custody Joker/NL2/KeePassXC and historical Family-Connect.kdbx remain known/nonblocking;
actual external copy/laptop-loss access are not inferred and no secret records are read.
