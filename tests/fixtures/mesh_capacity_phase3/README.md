# MESH capacity phase 3 — isolated Linux laboratory

Parent: `state-client-build/mesh-capacity-20261020/build.json`, verified byte-for-byte
before copying. No Git branch, push, production rebuild, APK, keys or routing change.
Run from repository root. `prepare.py` creates a **new** capsule; it must not overwrite
an existing capsule. `prepare.py --build` runs local race checks before building.

The live binary has explicit `MediaPolicy` A/B and `KeepalivePhaseMS` 0/1000 settings,
configured before media connection. A/0 preserves the parent's writer/ticker;
A/1000 shifts only the first keepalive deadline, retaining the 2s periodic timer.
B/0 advances the same Pion packetizer by monotonic elapsed time **before** the sample,
then sends that sample with duration zero. Empty advances emit no RTP, consume no
sequence/PictureID, and do not reassign retransmission timestamps. No new packetizer,
pacer, fragmentation, TLS packing, receive deadline, window or Mux credit change.

Examples (network approval required):

```
python3 tests/fixtures/mesh_capacity_phase3/run.py ExampleC --mode C --media A --rate 125000 --sizes 16448 --seconds 20
python3 tests/fixtures/mesh_capacity_phase3/run.py ExampleR --mode R --media B --send 32 --receive 32 --count 256
```

These are **not instructions to restart the completed experiment**. Inspect current
STATUS, manifests, reservations and remaining budget before any separately authorized
continuation. Never reuse a phase name or silently discard a failed reservation.

`run.py` reuses the existing NL disposable-room / isolated issuer workflow, with
owned `capacity3-20261020-*` directories and `family-connect-capacity3-20261020-*`
units. No user room or production private key is used. Remote resource limits remain
CPU50%, memory220MiB, tasks96, runtime510s; each C/R/T transfer is bounded180s and
individual inherited P requests150s. C observation includes12s drain, not useful
throughput added to a20s send numerator. No rate escalation beyond1Mbit/s here.

All attempts reserve source and outgoing-wire allowance against new128/256MiB totals.
The first Pion interceptor counts every outgoing RTP/RTCP attempt, including NACK
retransmission, plus64B conservative packet allowance; receiver RX is not added.
Media tracing holds at most100000 events in memory and emits only after the measured
phase and carrier close. Overflow is explicit; absence in a truncated trace is not
evidence of loss. This tracer must not become an application fallback.

Packet identities use carrier sender/message/fragment and payload-body hashes; SFU
RTP/SSRC/PictureID rewrites are learned from matching identities, never assumed equal.
Each clock's `ns` is process-local monotonic. Do not subtract endpoint clocks as
one-way delay. `analyze.py` retains the observed mapping separately from inferred
timestamp-only joins. It also recalculates every parent attempt, including P816's
excluded protocol error, without modifying the parent evidence.

P exports Mux counters from creation through final close on **both endpoints**.
Any nonzero counter cancels that endpoint's phase. Six lab-only reason counters
identify the existing increment sites: stale OPEN, unknown/retired stream, invalid
stream state, stale DNS query, invalid server DNS kind, absent/completed DNS call.
No validation is suppressed and no protocol fix is mixed with B.

`local_tls.py` uses a separate local-only source copy, ephemeral in-memory test
certificates and observation wrappers. It proves byte-exact application/TLS/bridge/RS
boundaries in both directions, excluding retries by sequence. It does not alter the
live binary and does not implement a packing fix. Initial failed local observations
and their corrected retests are retained.

Cleanup belongs to `run.py`'s `finally`: close local worker, stop only the owned unit,
collect results, verify owned executable absent, remove owned remote stage and local
room URL/issuer/credentials. Provider room metadata deletion is not supported by the
reused workflow; report normal session closure, not unverified metadata deletion.

Results, source/binary inventory, raw packet events, counters, resources, both
configurations, session receipts, network and selected ICE/SFU paths live under
`state-client-build/mesh-capacity-phase3-20261020/`. The single consolidated report is
`docs/releases/2026-10-20-mesh-capacity.md`.
