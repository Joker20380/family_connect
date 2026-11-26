# HA-02: stopped support capture and custody allocation — 26 November 2026

This is component engineering, **not an accepted coherent fleet backup**. Product
source57c19b1c and support archive621009b8 remain unchanged. The accepted handoff and
historical WORKERS_REMAIN/UNKNOWN remain accepted and UNPROVEN respectively.

## Owner allocation and read-only preflight

Joker is the designated dedicated HA signer and keeper of independent fingerprint,
request-hash, sequence and CRL-floor records. This does not approve a checkpoint.
The selected ciphertext destination is NL2 `/opt/apps/family_connect/ha-recovery/`,
with a new immutable actual-checkpoint-ID directory for each accepted kit. Existing
`20261124-host-01` remains untouched. Never place plaintext recovery/signing keys there.

17:57UTC strict-pinned SSH readback: parent root:root0700; ancestors root:root0755,
no symlinks;37,505,351,680 free bytes and3,063,689 free inodes. The first connection
using the default known_hosts correctly refused; the successful read used the existing
dedicated NL2 pin file, not a new trust-on-first-use key. No destination write or
durability/readback test has occurred; capacity/read-only observation is not custody.

Read-only block-device inventory finds **no attached external medium**. The only disk
is `/dev/nvme0n1`, Micron2300 NVMe1024GB,1,024,209,543,168 bytes, non-removable NVMe.
Its ext4 partitions are `/dev/nvme0n1p6` at `/` and `/dev/nvme0n1p7` at `/mnt/data`.
The same internal disk also has EFI at `/boot/efi`, an unmounted partition without
UUID and three unmounted NTFS partitions. Exact UUIDs/model/mountpoints remain in
the private `media-inventory.json`, not the public repository. None is external custody.
No mount, format, cleanup or key generation/use occurs. The only outstanding owner
choice is the actual external key/registry/backup-access medium; connect/select it
for a fresh model/UUID/mountpoint and trusted-environment check. Engineering continues.
Earlier24-file preparation and44-reference custody request remain historical,
unchanged preparation, not superseded approval or a coherent encrypted kit.

## Separate stopped-component contract

`control_ha_support_stopped` requires an accepted exact support process/authority,
checks loaded runtime and independently recloses/drains/invalidates NL1 before
sending bounded PID/start/boot-bound SIGTERM. It does not force termination or
restart a failed candidate. Same-operation retries reconcile retained intent.
A terminal failure, changed identity, unclean exit, cold-boot-only absence or an
unexplained stopped unit cannot qualify. The new private operation retains the
original pre-stop marker bytes before normal runtime shutdown removes its own
successfully completed lifetime marker. All historical pending/UNKNOWN remains.

Capture then requires independently observable clean same-boot exit, empty
unit/cgroup/service account and the old remote generation still invalidated/closed.
It holds both existing gate locks exclusively while reading exact store, runtime,
encryption-key file, accepted recovery records, authority, gate and stop records.
The private local component includes sensitive bytes; it must never enter Git/CI
or NL2 in plaintext. Capture neither deletes markers nor changes ordinary
`Gate.drain`: that API still refuses unsettled history.

A standalone reader imports no collector code. It independently derives the
required source set, verifies every exact byte/hash and directory membership,
checks clean unit/cgroup exit, retained authority/history and remote-ticket bindings.
Unrecognized/missing/extra/changed files refuse. The completion interval is closed
before locks are released; partial output lacks a complete receipt and is preserved.
Retry rereads the same complete component, rather than assuming packer success.

The root descriptor/shared-mapping census detects currently observed unmanaged
writers, but is explicitly **non-atomic** and does not fence future privileged
writers. This component is not full manual/CLI/direct-ORM coverage, independent HA
trust, an offline recovery format or a common RU/NL1/NL2/OWNER capture. The independent
component reader requires the stopped source to remain available; the later full-kit
reader/isolated restore must instead work without original hosts.

Forward resume uses the existing linked procedure with fresh process authority and
mailbox generation, never edited old PID/boot or reopened invalidated tickets. See
[repeatable boot/resume](../operators/support-boot-resume.md). It preserves old records,
data, queue/cursor and floors. A component snapshot cannot authorize startup or restore.

## Qualification and observed state

CPython3.14 isolated venv uses control/identity/provisioning/HA and hashed messenger
lockfiles.11 native tests PASS/0 skips in45.03s, including actual user-systemd/RNS
stop/copy/reader/linked resume with synthetic nonempty notifications/cursor42;
lost responses after reclosure, intent and signal; reader failure retaining partial
output; actual SIGKILL of the copying controller and same-operation recovery;
ordinary-drain refusal, busy stopped gate, direct writable descriptor/shared mapping,
changed/missing bytes, symlink/FIFO and forged settlement refusal. No synthetic
operation contacts real users. Initial9PASS/1FAIL exposed a test assumption that the
normally completed lifetime marker must remain; exact pre-stop history retention was
added rather than weakening drain. Intermediate10PASS and final11PASS logs remain private.
Focused stopped/resume/rollover/startup regression:43 PASS/0 skips in109.56s.
Operation directories reject unrelated contents while retaining interrupted atomic
receipt temporaries; resuming never deletes those partial records.
Final directory-reuse/partial-receipt regression:11 PASS/0 skips in38.37s.
Exact source `2f4f83dd51cd3814a2da631cb3d95140af5c2a90` is ordinarily pushed and remote-SHA
verified. All four triggered workflows PASS: phase0, Linux control preview, Android
readiness contract and native support. Native run45875688212 has342 PASS/0 skips,
including all11 stopped-support cases. Artifact15145396353 exact ZIP SHA256
`396275282464f190b04ab6b9e77d8aea25f8c3c016784e798627825156586ccb` and its exact-SHA
receipt/XML were independently checked.373 staged source files match on OWNER/NL1.

Before operational changes,47 root-prestate files were retained privately; manifest
SHA256 `e2103e712fc05094b55d5bc6dc763c6a479997f51414932139520a38e0a80d40`.
17:57UTC prestate support PID757814 was active/running; notifications success/0 and
timer waiting. Subsequent bounded working operation is recorded below.

## Actual component stop, capture and forward resume

The operation owns only its temporarily stopped notifications timer and its capture
locks. Its before/intent/stop/run/restore receipts remain private. The already-running
notification oneshot was allowed to finish successfully before support shutdown.
The accepted support runtime was verified, NL1 recloses/drains/invalidates the old
ticket, and PID757814 exits normally with status0 after bound SIGTERM. No SIGKILL,
marker removal, authority edit, old-data restore or ordinary live drain is performed.

First controller result is `STOPPED_SUPPORT_REFUSED / UNSAFE_CONTROL_FILE` after
stop-intent and normal exit, before the final stopped receipt. This failure is retained,
not silently replaced with success. Independent absence readback proves clean same-boot
exit; the same operation reconciles closed NL1 and records the stopped proof without
another signal. The exact transient file causing this refusal is **not established**
by the retained original response; do not claim a unique root cause from exit78 or
attribute this to historical WORKERS_REMAIN. No terminal failure is erased or restarted.

Real component SHA256:
`e4eace1a5e37fdc2914fa5e8eaf495bf21026932bd55b68b3faf88160cb0d264`.
It contains86 entries and494713 file bytes across the declared exact roots, including
16 pre-stop/current marker records. Closed/drained lock interval is
**18:46:52.496839–18:46:53.730133UTC**,1.233294391s. Root descriptor/shared-mapping
census reports no continuing observed writer; service/cgroup/account absence and
closed invalidated NL1 are checked before/after the interval. The standalone reader
passes inside the barrier and again independently before resume. This remains a
private sensitive local support component, not a full encrypted fleet kit. It includes
the store key and must not be uploaded to NL2 or Git in plaintext.

Fresh OWNER plan SHA256 `8bab4157c43c6864d0e6f7db6933ce221e529d33c7d6bf79df86f64f86c095d9`
and mailbox manifest `08bcc151c61b3e19fdab7b4606432d3188271e14f51597fa8ab659caf73db570`
bind new generation `0b21197a2582b9ae3ce2f6449907890343f71dea8cca87a283bc4c66c5e24824`.
The authenticated predecessor-reclosure bytes are retained with SHA256
`482b927b22290187bc949cd5fcd7b8d226467127614108c0515e848da23d6f38`.
New NL1 resource preflight preserves100%/768MiB; the earlier fresh sample has738640KiB
available. Rollover performs its own fresh minimum256MiB check. NL1 PID3705 never restarts.

Existing linked resume returns `FORWARD_RESUME_OPEN_CAPTURE_DENIED`; repeated same
operation returns the same result without restarting. At18:52:14UTC separate readback
proves support **PID1051719**, start2431377, active/running/NRestarts0 on the current
boot, exact archive621009b8 and new authority SHA256
`04fb7553363830e2b873b019e173cd82ccecf92be0b78f31e71964b8dfa57a86`.
IPC works; authenticated NL1 ticket/consumed-request/OPEN_LOCAL_ONLY bindings agree.
All21 logical records/12 messages are retained;19 non-binding/non-cursor records compare
exactly, cursor4 and its anchor are preserved, jobs0. The old accepted operation,
authority and16 captured markers compare byte-for-byte; all60 original root records
also remain unchanged. New successful runtime admission does not settle old UNKNOWN.

Normal existing notifications invocation **18:50:15–18:50:16UTC** completes success/0,
inactive/dead as expected for oneshot. Timer is restored enabled/active/waiting.
No real test messages are created. `/proc/locks` confirms no exclusive admission or
operation lock remains; only the new support PID's normal shared lifetime lock exists.
RU/NL2 working services, OWNER panel containers, enforcement and resource limits are
unchanged. Current GET-only OWNER source/admission census still reports2/10 matching
source files per console/publisher and unresolved manual/direct-ORM admission.
The component predates the new authority/generation and is now retained history.
Do not combine it with later RU/NL1/NL2 captures and call that a common checkpoint.
The actual fleet cycle needs a fresh support snapshot bound to that cycle's current
predecessor and overlapping closed interval, followed by another normal linked resume.

Private allocation follow-up request SHA256
`5082fe64b0e27cfcbb985984e6cffe890b44e198bac2f8908b0db444d9dfa390` binds the selected
roles/destination and four exact prior/preflight references; a separate reader verifies
those bytes. It explicitly has no actual checkpoint manifest/signature request, key
creation or custody acceptance. A real request must bind the still-uncreated full kit.
No common OWNER gate activation, full encrypted kit, independent custody transfer or
full isolated machine-loss restore is claimed.

## Remaining gate / one NEXT

One current NEXT is the actual coherent encrypted RU/NL1/NL2/OWNER capture, exact-set
independent reader and verified normal resume. Integrate stopped support with installed
OWNER/all-writer closure and intersecting closed/drained intervals; qualify failures
without weakening UNKNOWN or enforcement. After acceptance, complete independent
custody and full source-host-free restore with current/post-ACK/stale-state rejection.
The prior HA-02 journal/import/full-recovery blocks remain partial; isolated replication
PASS is retained. HA-03 cutover remains out of scope. FLEET-PRODUCTION-ONBOARDING-1
remains mandatory and open, not replaced by these preparations.
