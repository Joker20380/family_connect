# CONTROL-HA — native renewal settlement, 24 November 2026

## Scope and decision

Continuation of selected CONTROL-HA-20261123 / HA-02. This closes a specific source-level
capture gap: **a successful SSH/RPC exit is not completion of a multi-request renewal**.
The installed `DurableOperation.acquire` returns successfully while `owner.json` remains
`ACQUIRED`. A per-request admission gate alone can therefore drain between renewal requests.
Even `RESUMED`, `ABORTED` or `CLEANING` is not a reason to erase that journal or declare idle.
Only the existing authorized native workflow may complete/clean its transaction.

Replication remains PASS; current trust/approval, coherent all-writer capture and independent
custody/final recovery remain the same three partial HA-02 gates. No HA-03, cutover, service
deployment, SSH/key/policy change, client version, public artifact or signing-sequence change.
Working OWNER image bindings remain at their previous observation; no running container changed.

## Read-only installed bindings

Only previously resolved NL1/NL2 profile routes were followed, using existing strict SSH pins.
No application handler was dispatched, application module imported on a server, product DB/key/
profile read, journal changed, native lock acquired or service restarted. Small fixed configs
and bounded pinned source files were retained privately. Double reads check file identity,
content hash and metadata; this is observation, not independent source approval.

- NL1 snapshot `6dd51ead36a977abd4e6afee978d81df229ac767a6315bc4b2347328bde60c84`,
  commit `c9c0a4de55f455e0788e7b519383c0cb0743fc96`.
- NL2 snapshot `4373585a7a16499ee0cae95fca2beb644f799153345ab4677ae0f2a927e18657`,
  commit `ae2737f375fc48c4e026a87166a221e978fbbf1c`.
- Each snapshot has25 manifest members with matching hashes and18 exact committed files.
  Generated directory/entry/permit records and the parser projection are distinguished; the
  projection's original source hash matches its commit. This is not runtime import qualification.
- Both fixed snapshot configs pin their profile locators and root-owned renewal helper scripts.
  Helpers preserve their existing `-E -s -B` Python/node/config command. The two node configs pin
  all14 renewal modules; each aggregate source hash and individual module hash matches.
- Common renewal API archive:
  `1f1d2c8e56119c58a44fd3edf7cedf167f6761b7c81a6023e8b600a6049720e4`.
- NL1 node-config hash: `3513a9608534c3a4fe86479d9a04e80ec325408ecfa4837eeecb212c6f3df211`.
  NL2: `77fb7f68fb7f7fc9618542350d4d0b3c4ad4b0fb012dfd5a5c1f09b1fd1c322f`.

At19:38:13UTC both selected state directories contain only `operation.lock`, `completed.json`
and `archive`, with no `owner.json` or residual transaction entries, in two equal observations.
Kernel directory/lock identities are retained privately. **No live lock was acquired**; absence
of an owner at sampling is not a stable capture interval, proof of no external work or an
authorization to activate the guard. Historical archive contents were not read or validated.

## Implementation and bounded behavior

`control.capture_renewal.RenewalState` verifies a pinned private node config, its exact state
path and the kernel identities of that directory and existing `operation.lock`. All path
components reject symlinks. Owner/mode0700/0600 and regular-file/single-link rules remain strict.
It does not create a missing native lock, repair permissions, change product data or finish a
transaction. Missing, replaced, unsafe or unfamiliar state fails closed.

After normal admission drain, the guardian takes the existing native lock exclusively with
zero wait. Busy native work refuses the interval. While holding it, any owner, pending file,
start-intent or unknown root entry refuses settlement. A quiet state allows only the existing
lock and optional completed ledger/archive. This is a quiescence check, **not historical archive
integrity verification**. The config, directory, lock and top-level metadata are rechecked before
the final HELD acknowledgment. Concurrent uncoordinated replacement invalidates the receipt.

Guardian schema2 adds an explicit nullable renewal binding per participant. Root guardians are
allowed only with an explicit settlement binding, UID/GID0, empty supplementary groups and a
root coordinator. Existing sealed-source/runtime/namespace/peer checks remain mandatory; no
arbitrary command is added. Schema1 retains its prior shape and non-root behavior, but cannot
claim renewal settlement. Duplicate gate/native lock identities and duplicate state paths refuse.

Native locks live in guardian children, not an indefinitely running coordinator. Existing
5s drain/2s hold/7s total watchdog limits remain, under normal kernel scheduling. Channel EOF,
failure or deadline releases the locks; final joint ACK still bounds any accepted interval.
Every receipt continues to say `capture_permitted=false` and does not assert all-writer closure.
Manual root writes that bypass advisory locks still require the explicit bounded coordination
window; this is not a security boundary against the trusted administrator.

Local closed guardian capsule:
`2c37bdb7d0a62b593b4c8b80fdd77b234240d89c0dd464d3ea51aa486fa21fde`.
It includes the new settlement module. It is not installed or independently approved.
The earlier receiver capsule `4e9ab90f…` is unchanged.

## Verification

**264 tests PASS /0 skips**, Python3.14.4, in38.88s:
`test_capture_renewal_state.py`, `test_capture_launch.py`, `test_capture_group.py`,
`test_capture_gate.py`, `test_capture_receivers.py`, `test_capture_profile.py`,
`test_capture_renewal.py`. Tests cover native-lock contention, journal/residual refusal,
config/pin/type/permission failures, final-ACK replacement, immutable binding copies,
schema1 compatibility, schema2 root restrictions, closed packages and host-fixture refusal.
Four changed documentation files/1048 local-link targets and whitespace checks pass;
listed external URLs are not claimed as HTTP-verified public artifacts.

**Native isolated stand PASS19:36:37.746217–19:36:58.590756UTC.**
`tests/fixtures/capture_launch/renewal.py` uses exact retained installed modules from both nodes:

- `credential_renewal.py`: `7023c93815fab82460f5e539d6ba9e356e67a39543b0981d6526d589c18d22c9`.
- `production_transport.py`: `596120f562ea50ea13a29f143393db3688eeab845bf2fa19f47499fc0012c7ef`.

The actual native lock/acquire code reproduces successful RPC followed by an open transaction:
the legacy request gate drains, but the new pinned root guardian refuses the interval and
preserves the owner. For a separate initially idle synthetic state, root+UID993 participants
hold the actual native lock through a joint interval. Native acquisition reports busy inside,
idle afterward and idle after the guardian deadline even while the coordinator is still alive.
No fixture deletes an unfinished owner to turn its test green.

Image `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`, Python3.13.17,
cryptography46.0.7. Network disabled, read-only rootfs, fresh16MiB tmpfs, no live mounts or Docker
socket; only closed source and the two retained modules per node mounted. Caps CHOWN/SETUID/
SETGID/KILL, no DAC override; no-new-privileges,64 PIDs,256MiB,1 CPU. The first attempt omitted
KILL and failed when the root supervisor signaled its different-UID child; its receipt remains.
Only that disposable stand's child-management capability was corrected; no permissions widened.
All owned stand containers removed. The first read-only journal observation also refused due
to directory access-time drift; the retry compares identity/mode/size/mtime/ctime, not atime.

**Limits:** synthetic configuration/state and two real native implementations are tested, not
full installed `node.main`, actual sudo/helper execution, installed Python/site packages,
systemd completion, live profile data or cross-node capture. No native cleanup is claimed tested
here. Full dependency/dispatch approval and external-operation evidence remain necessary.

## Evidence, rollback and next gate

Private root0700, source/config/receipts0600:
`~/.local/share/family-connect/control-ha/20261124-profile-closure-8vf9etma/`.
Successful stand: `native-i7_b2t2z/`; initial failure: `native-7nnljy12/`. Raw configs, source
capsules, kernel identities and receipts remain outside Git. Sanitized checksums:

- Provenance receipt: `89b46ed24a077b0835b6e65f63a7f1ac7c964489421c96bcd3d4954889058409`.
- Native receipt: `9526f5a83f25d93f1c7ca0f3a45b056d2b32b96e7d35deb33d1b7e9094a94dfe`.
- Native stdout: `d8c2831f075f6425ce552feb39297327dec7bdbc5fbefffa4d23fcf4ca9b4b2e`.
- Native fixture: `bd09ef54d3bdb03bdb692d9edb7116a03f524613c4a8fbc9e81be487a5744fee`.

No installed rollback is needed. A future approved rollout must retain old immutable capsule/
binding pins and undo only the guardian binding, never DB/profile/journal history or recovery
SSH. Reverting to schema1 removes this settlement proof and invalidates capture readiness.
Never delete an owner/pending marker or restart failed services to force a PASS. Keep paid-watch.

Next within HA-02: actual Python/site-package/sudo/unit binding and remaining AWG/mailbox/support
external completion; bounded manual product-write/deployment coordination; independently approved
activation of the exact runtime/source/gate/image bindings, real latency/overlap and coherent
capture; independent current checkpoint/key custody and final combined recovery. Do not repeat
this completed source-chain observation or native-lock stand as pending work. No new stage added.
