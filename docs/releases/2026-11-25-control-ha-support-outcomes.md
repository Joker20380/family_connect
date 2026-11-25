# 25 November 2026 — independent OWNER/NL1 support outcome census

## Actual result: observed, not settled

At18:39:39–18:39:40UTC a read-only paired observation compares the working encrypted OWNER
support store with the independently read NL1 mailbox spool. Result **OBSERVED_UNFENCED**:
`external_settlement_proven=false`, `activation_ready=false`, `capture_permitted=false`.
This resolves what evidence currently exists; it does not close the old-work settlement gate.
The [qualified replacement supervisor](2026-11-25-control-ha-support-replacement.md) is unchanged
and is not launched on working support. No kill-policy-only change or replacement occurs.

The local store has21 encrypted records,12 messages and2 support-request records with valid
message links. Five incoming messages are recorded received. Seven outgoing envelopes are
retained: two ordinary messages marked `recipient_stored`, five outgoing stored-receipt messages
marked `relayed`. No attempt token is active at the sampled moment. There are **zero retained
incoming raw ACK records**: the installed `Chat.receive`/`Store.accept_stored_receipt` path verifies
the receipt and changes status but does not retain its signed packed bytes for independent replay.
Local status is therefore a historical application observation, not a new independently replayed
recipient proof. No user message text, identity, address or key is included in this report.

NL1 has **zero exact matches for these seven ciphertext hashes**, and zero additional spool rows
from this sender outside the request. All seven absences are classified **unknown**, not lost,
undelivered, delivered, canceled or settled. A recipient purge and ordinary retention expiration
can produce the same absence. Lack of a row also does not exclude a request waiting to commit.
Local snapshots before and after the remote read match; this is not a continuous writer fence
or a coherent fleet snapshot. No retransmission, receipt synthesis, purge or uncertainty clearing
is used to make the observation pass.

## Source and read-only contract

`scripts/control_ha_support_outcomes.py` reads native SQLite with `mode=ro`, query-only and trusted
schema disabled, no checkpoint on close, zero busy timeout, bounded rows/bytes and a query deadline.
It requires regular private single-link files, rollback-journal headers and exact table columns;
symlinks, sidecars, unexpected schemas and busy databases refuse. It never opens `Store` or `Spool`
on working data, changes journal mode, takes an application owner lock or calls delivery methods.
Decryption occurs only in the privileged local process, not on NL1; keys and plaintext never leave
that process. The sender public key is checked against the encrypted identity, and packed-message,
recipient, request and retained-envelope bindings are checked without changing any row.

Only the bounded private challenge, public sender hash and ciphertext fingerprints/lengths are sent
over the existing strict-pinned SSH connection to authorized NL1. The remote observer runs from
stdin in memory, matches the node public key and four installed source digests, verifies the same
mailbox process before/after and compares actual native spool rows. Its result binds the complete
nonce-bearing request digest. It returns counts, never spool bodies or unrelated users' records.
The local assessor refuses forged/count-inconsistent/unbound responses and cannot issue an
activation or capture permit, even with matching local snapshots and a present exact ciphertext.

Observed NL1 source pins:

| Source | SHA-256 |
| --- | --- |
| `messenger/server.py` | `01c4d94b9bce9b7137c4f9cc25eba3046bd57ac41f81ff683ad317a6b323077c` |
| `messenger/relay.py` | `2108e024353158b271ccce9289c3755a4b64f5f9d130d1e55ec79dac6bdff4ac` |
| `messenger/membership.py` | `a0c7513ceed6e58e83026066db5b3d01a595c408424185e9ebc8e21bd89cc4b4` |
| `messenger/codec.py` | `c8909a6cd4647ca5a23dd19ed85c427f1ff72bc98c057ef4a543900ab2ca5ea0` |

The relay/server/membership match the repository's corresponding source; the installed codec pin
is observed separately, not silently replaced by the newer repository codec. Neither source tree
nor the running mailbox is modified. No private signing or identity key is read on NL1.

## Qualification and failure reproduction

**26 tests PASS/0 skips in0.35s**:22 new outcome-census contracts plus4 existing native relay tests.
The preliminary19 pass is retained but not added to this final count.

The new native TCP/SQLite test admits an envelope at the relay, closes the sender connection,
observes an empty spool while that request waits, then allows the native `Spool.put` to commit.
The envelope appears after the sender is gone. Both observations remain unfenced, never settled.
Separate native tests commit then recipient-purge or retention-expire the same envelope: both
produce `absent_unknown`, without inferring the reason from current absence. This directly rejects
closed-TCP, empty-spool and zero-local-attempt shortcuts for the remaining handoff boundary.

Other checks cover exact present-envelope binding, conflicting sender/recipient/hash, orphan sender
rows, source identity mismatch, changed local snapshots, forged remote claims/nonces/counts,
plaintext/identifier-free summaries, unchanged native DB bytes/schema/mtime/sidecars, and refusal
of unsafe/symlink/busy/sidecar/schema inputs. These tests do not fake an external settlement PASS.

Private evidence stays in `/tmp/fc-ha-support-settlement-20261125`. The nonce-bearing paired manifest
is root-only; no product DB, key, raw source capsule, message, envelope ID or private manifest enters Git.

| Evidence | SHA-256 |
| --- | --- |
| Qualified outcome observer source | `26f3d492b3cd0d5cd2ea34b88471e9a8ce89ae93c4fb1b220369b510c99d2b03` |
| Preliminary19 JUnit | `128f7ffc2afb45b838e870fc5712c33a3d9e421d6adcd32767b4086bf9d76ab4` |
| Final26 JUnit | `9a1c2ac7739e20129979d9c5a733bf7f93f5fd076d6a06da0a4abd9933891c90` |
| Initial local-only census | `cc7edfa0c774b5863a2deb5bca81aa21dfdf8c242793ebb714674bdf457a30e8` |
| Actual paired readback | `f1aa5ca7624eb909126e355c2a453624d3e4f0198144b7bc77a5c4e5c2949495` |

## Working state, rollback and next boundary

OWNER remains active/running PID2022541/0 restarts, original19 sources/3 unit files/15 effective
fields and unchanged process binding. NL1 mailbox remains active/running PID3705/0 restarts under
fc-mailbox; the node public pin matches OWNER input and four source hashes are unchanged. Existing
control-group/SIGKILL/40s OWNER and15s mailbox policies
are not exercised or changed. No service stop, injection, dispatcher mutation, owner lock, product
write, replay or data restoration occurs. The observer only releases its read transaction on exit;
there is no working deployment to roll back. Private evidence is retained on refusal as well.

GUI sudo authentication works, password not captured; terminal closed and timestamp invalidated.
No sudoers/polkit change, permanent privilege, retired-host contact, RU/NL2/container/MicroTrader
operation, HA-03 or public-version change. Candidate remains
`9d7bf840f3455d0ef2e7653dc9289aac2f0d77c9f2a0a8e305c786f7ddb80489`, not rebuilt or installed.

Next within the **same** old-work settlement gate: qualify a bounded independent NL1 mailbox
admission/drain boundary covering delayed support-origin PUT and support-recipient purge callbacks,
with controller-death/abort behavior and continued service for unrelated identities. A snapshot or
SQLite lock alone is insufficient. Bind that boundary to the OWNER quiescent generation and
replacement commit, preserve all historical unknowns and verify the real handoff before activation.
Do not ask the owner to certify unknown delivery or erase uncertainty; no extra owner action is
needed for the next technical qualification. After authorized installed readback, remaining
manual/OWNER coverage, coherent capture, independent trust/custody/approval/full recovery remain.
Same three HA-02 gates partial; isolated replication PASS. No new gate or HA-02 completion claim.
