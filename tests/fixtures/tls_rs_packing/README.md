# TLS→RS packing — isolated laboratory, 21 October 2026

Pinned parent: completed phase3 capsule and binary inventory. Never edit the parent,
production package, gateway, Android, keys, routing or release catalogs. All live
runs use original media A/0, Mux64 and default RS payload/RTO/retries. The phase3
clock candidate remains separate and disabled. Window8 means8/16 on both peers;
window32 means32/32 on both peers. No ALPN or wire-format negotiation is added.

From repo root: `prepare.py`, `finish_source.py`, `finish_drain.py`, then `prepare.py --build`.
The last command runs race tests and builds one binary in a new private capsule.
Loopback tests may require outside-sandbox approval. Failed attempts are retained.
Do not rebuild a reserved capsule; each A/B pair must share the build hash.
Repairs in this run retained complete v1/v2 source/binary inventories before v3.
V2 only fixed the32B fixture allowlist. V3 fixes false drain-success after an RS
terminal and gives BOTH P policies a finite2s passive ACK settlement before drain
and abort; it does not change the packing worker, RS or media. V1/V2 measurements
remain attributed to their hashes, with late shutdown warnings separated from
application body completion. A new P8 pair validates v3; no previous trial is erased.

A retains the existing pipe reader → RS SendContext boundary. B0/B2 replace only
the outbound byte-stream adapter with four copied16KiB FIFO blocks plus one16KiB
worker buffer. Full blocks dispatch immediately, oldest-byte partial deadlines are
0/2ms. One existing outbound worker serializes RS sends; two bridge workers total,
no goroutine per Write. net.Pipe remains the inbound ordered stream. A is selected
when context policy is absent. This is lab-only code, not an application fallback.

Write returns local acceptance, not carrier write or remote acknowledgement.
The FIFO owns its copies; buffer-full Write blocks with its write deadline and
session cancellation. RS SendContext uses the session context, never the2ms timer.
No coalescer lock is held while waiting for RS. Terminal send failures wake waiters
and stop the bridge. Explicit `LabDrain(ctx)` flushes accepted bytes and waits for
the existing RS send depth to reach zero; this is not proof of remote application
consumption. Ordinary Close is abortive, as in the parent; correctness is established
by receiver body checks and within-run ciphertext hashes, not by Close returning.

Tail age includes time behind a blocked RS worker. Coalescing timer wait, RS call
wait, FIFO Write backpressure and eligible dispatch delay are separate counters;
they may overlap. `DeadlineOvershootNS` includes preceding worker/backpressure
time and is NOT a pure scheduler metric. Diagnostic histograms cap at256 keys
plus an overflow key(-1); byte counters and SHA256 remain complete.

Synthetic P requests use graceful FIN/EOF/Close on BOTH A/B, with completion in the
full interval. The local initial abort-before-FIN test produced a late protocol
counter; it is preserved, not suppressed. P also adds32B idle and concurrent-bulk
controls. These harness changes are common controls, not changes to production Mux.

Physical runner: `run.py PHASE --mode T|P --packing A|B2 --send 8|32 --receive 16|32`.
Every run creates a disposable room/issuer, guarded resource-limited NL process,
same Linux client; it reserves source and outgoing-media budget before starting.
No receiver RX double-counting; both outgoing RTP/RTCP boundaries include retries
and conservative packet allowance. Cleanup is in finally; provider room metadata
deletion is not supported, normal connection closure is verified instead.

`analyze.py` retains every attempt, computes receiver-monotonic T and full P
goodput, per-direction slot use, hashes and protocol counters. Raw artifacts stay
private in `state-client-build/tls-rs-packing-20261021/`. Final results belong in
the existing consolidated mesh-capacity report, STATUS and PLAN, not a new release.

Post-network `post_local.py` uses a separate validation source copy, never the frozen
physical binary. The corrected queued-write stall test retains the original failed
fixture and exposes retry-byte amplification with denser DATA, despite unchanged
attempt counts. Memory accounting includes capped histograms, timers and pipe ends;
it is a retained-heap model, not an RSS guarantee. This remains a product gate.

Readback found an unexplained production process/profile-hash transition between
v2 and v3, not within any test phase. Binary/flags stayed equal; no production write
exists in the laboratory operator. Finalization retains both observed epochs and
does not claim full-run profile equality or revert the newer state. Each A/B pair
uses one epoch. `verification.json` closes the budget and prevents additional runs.
