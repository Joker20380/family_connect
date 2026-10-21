# Dedicated Mux profiles via authenticated Family TLS ALPN

Status: implemented; actual compatibility matrix/local correctness PASS. Completed
three-pair owner experiment: **INCONCLUSIVE**, not an accepted speed/default128
release. Manual return confirmed20.10: new authenticated LEGACY64/65536 session,
next-session128 OFF; no reinterpretation of the former B3 session. Closure evidence in
the [Mux report](../releases/2026-10-20-mesh-mux-credit.md). Not a public release.

## Decision and security boundary

Keep certificate claim `protocol=family-connect-5n3-test-v1` and its `Protocol`
constant unchanged. Generic `Configuration`/`Open`, seed/bootstrap and HTTP/control
sessions continue advertising only that ALPN. Only dedicated TCP/DNS data sessions
use `MuxConfiguration`/`OpenMux`. A capable client advertises, in preference order:

1. `family-connect-mux-credit128-v1` → CREDIT128,131072 bytes per stream/direction.
2. `family-connect-5n3-test-v1` → LEGACY64,65536 bytes per stream/direction.

An enabled data gateway advertises the same list; disabled advertises only legacy.
The final ALPN is authenticated by the successful TLS1.3 handshake. `NewMux` accepts
only a completed session with one of the two exact profiles; its window is immutable.
Empty/unknown/no-common ALPN and certificate/authorization errors fail closed, with
no reconnect-as-legacy fallback. Legacy is a mutually selected normal profile.
Family, role, public-key binding, revision, CRL, validity and floors are unchanged.
No identity reissue, root operation, enrollment or authorization grant is needed.
Lease revalidation accepts either already-negotiated data ALPN but still rechecks
current authorization; disabling128 cannot reinterpret an active128 session as64.

| Client | Gateway | Final contract |
|---|---|---|
| actual beta94 | actual b9 | LEGACY64 |
| actual beta94 | new,128 enabled | LEGACY64 |
| new | actual b9 | LEGACY64 |
| new | new,128 enabled | CREDIT128 |
| new | new,128 disabled | LEGACY64 |

The local cross-process fixture uses actual accepted old sources, not two new
implementations impersonating old peers. Negative ALPN/auth tests are separate.

## Mux semantics

The frame encoding (version2, kind, stream ID, length, payload) is retained. The
application negotiation and allowed window semantics change: initial send/receive
credit, receive ring, index wrap, maximum WINDOW_UPDATE increment and cumulative
overflow validation all derive from the negotiated profile. DATA remains <=16KiB;
Family payload/batching, default ReliableStream8-slot window/RTO/retries and RTP A0
are unchanged. Read returns exactly capacity actually freed from the receive ring.
No speculative credit return, arbitrary peer window, dynamic resizing or256KiB.
Existing single writer, control priority, round-robin DATA and stream lifecycle
remain; no other rejected optimization is included.

## Operator controls and rollback

Reuse the existing protected `FC_DIAGNOSTIC_CONTROL_DIR` on NL. Directory must be
owned by service UID,0700, not a symlink; files are regular0600 same-owner, bounded
to32bytes and opened without following symlinks. `mux-profile` is `LEGACY64` or
`CREDIT128`; absent configuration defaults legacy. Invalid nonempty values fail
setup. Capture at data-session creation, not on every stream or packet.
`mux-counters` ON/OFF gates the existing bounded export, equally for both profiles.
No remote API/UI/provisioning override or unprivileged application write access.

Disable128 for new sessions atomically; let active128 sessions finish or use normal
Disconnect/Connect. A b9 executable rollback interrupts active sessions but the new
client normally negotiates LEGACY64 on its next session. Preserve current security
materials and use fresh transition guards; never restore an old security snapshot.

## Retained memory, not a whole-process bound

Receive ring is64/128KiB per stream **per endpoint**. Send credit is an integer,
not an additional preallocated window. One queued DATA per stream is <=16KiB.

| Streams/session | LEGACY64 rings | CREDIT128 rings | DATA queues upper bound |
|---:|---:|---:|---:|
|16|1MiB|2MiB|256KiB|
|32|2MiB|4MiB|512KiB|
|64 dedicated maximum|4MiB|8MiB|1MiB|

Socket-copy staging adds up to16KiB per active copy direction; control/DNS queues,
TLS buffers, shared RS retained packets, carrier assembly/reorder, socket/kernel
buffers, goroutine stacks and metadata are separate and unchanged. The broker
allows at most32 outstanding setups including live sessions: at64 streams each,
one broker can retain128MiB legacy or256MiB128 rings alone, plus up to32MiB queued
DATA, staging and all other layers. These are component sums, not RSS promises.
Multiple brokers/processes/users add their own allocations; no global allocator
budget is introduced. Live unit readback: MemoryMax/MemoryHigh=infinity,
TasksMax357. Thus stream/session bounds do **not** establish a hard whole-process
memory cap or multi-user capacity acceptance. Physical RSS is reported separately.

## Implementation provenance

Isolated capsule `state-client-build/mux-profile-20261020/`; reusable patches,
tests and operator workflows in `tests/fixtures/mux_profile/`. Base is sealed94/A0
and b9/1011, not repository main. Beta95 is owner-only; tester stays ordinary94.
Previous read-alignment, SACK-hole, queue-retry, deadline and cleanup patches stay
separate. See final source manifests and hashes in the Mux report.
