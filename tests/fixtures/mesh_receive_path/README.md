# MESH receive-path continuation —20 October2026

## Completed finite deadline and one physical A/B/A

The deployable delta is `finite-deadline.patch` against exact normal92:
SHA256 `7055282b78759c6eda10bc7cac0f938ae1d2b896a02c414b85e97807524e084d`.
`deadline.py prepare` copies the verified source into an ignored private capsule
and applies this patch. Use a fresh `RTP_DEADLINE_OUT` for independent reproduction;
`run`, `stress`, `integration` execute new delta,20 repeats, and affected packages
under race. Integration needs ordinary local socket access. No live operation is
part of these commands; do not run the sealed old canary/PERF launchers.

`deadline_test.go` compares autonomous A100/B125 using controlled clocks and
recorded structural arrivals, plus real Pion read-deadline/close tests. The same
reader owns reorder/VP8, no new packet queue or workers. Real timeouts clear the
queue during silence; equality expires before arrival. Payload ownership, CRC,
bounded pools, wrap, window256, stale gaps, replacement, slow consumer and close
are checked. `arrival_tradeoff_test.go` runs on the **unchanged A0** source: A0 can
heal arbitrarily late without an intervening arrival; finite service cannot after
its deadline. This intentional tradeoff is not hidden as universal recovery.

Final38 delta,760 repeated,170 integration checks PASS/6 opt-in skips;8 A0 tradeoff
and clean-reapply38 PASS. Earlier450 unchanged checks reused. Initial failed
fixtures/build attempts remain in the private capsule with successful reruns.
Autonomous B125 still conditionally rescues1294;614/1127 remain incomplete.
All finite replay RTP queues empty, but truncated VP8/partial carrier state remains
bounded under existing contracts; the report lists it rather than claiming zero.

`deadline_build.py`, `deadline_sign.py`, `deadline_upgrade.py` preserve exact92
ancestry/package/key and guard forward93 install. `deadline_rollback.py` prepares
normal94 with exact92 native; signing/upgrade support `--baseline`. These are
side-effecting private operators, **not commands to rerun after completion**.
No safe normal-build policy selector existed, so93→94 performs policy rollback
without downgrade. Both builds169 checks PASS, no performance tags or new UI/API.

`deadline_physical.py` reuses the authorized bounded Android-TUN HTTP1.1 meter,
ordinary diagnostics and topology/socket gate; it does not pretend missing PERF
snapshots passed the old two-sided PERF gate. One A1/B/A2 cell each completed:
single0.568/0.631/0.567, aggregate1.275/1.322/1.254Mbit/s,9/9 bulk,18.1875MiB with
controls. B's positive difference is not repeatable mechanism-supported speed
acceptance. Current94/A0, exactb9/1011/PID unchanged; no public release or push.
`deadline_evidence.py` only summarizes retained files and applies sanitized final
JSON evidence; owner94 export covers A2, not missing A1/B Android counters. Its
historical90 incident and cumulative1 Mux error/25 RS timeouts are not new B faults.

Private capsule: `state-client-build/rtp-deadline-20261020/` (not Git).
Final report: `docs/releases/2026-10-20-mesh-receive-path.md` and `.deadline.json`.
No further budget scan or pacing work is scheduled by this completed experiment.

## Historical late-arrival replay continuation (ordinary92 / exactb9)

`late_arrival.py prepare` verifies the92 source inventory, APK and current b9
source/binary, then copies **only for tests** to ignored
`state-client-build/rtp-late-arrival-20261020/carrier`. Set `RTP_LATE_OUT` to a fresh
private directory for another reproduction. It substitutes the clock/budget and
a read-only queue observer in exact accepted `rtp.go`; this is not deployable code.
`late-arrival-input.json` contains sanitized retained process-local points/arrivals
from the existing capture, without payload, private identities or credentials.
1294 includes reconstructed enqueue times (`release.ns - wait_ns`); it is not a
complete captured reader prefix.597 has no such clock and remains the earlier
structural model with unknown final6s, never assigned invented recorded timings.

`late_arrival.py run` runs `late_arrival_test.go` under race on that exact source:
100/200/350/500ms plus smaller110/125ms sweeps, frame/carrier byte-exact **synthetic**
payloads, real-loss/control/duplicate/conflict/wrap/epoch/window/multiple-hole cases.
The clock is test-global, intentionally serialized, not a concurrent production
timer. Original encoded payload sizes/marker bits are not all captured; observed
frame boundaries and accepted packetizer constrain the synthetic inputs. Unknown
orphan tails never become invented complete frames. Metrics include transient
pre-drain queue peaks and retained payload capacity, not total RSS or real sizes.

`late_arrival.py regressions` runs independent unmodified92/b9 race suites.
The b9 suite requires the existing `FC_EXPECT_SEED_OBSERVABILITY=1` expectation;
the wrapper sets it. `gateway-regressions` reruns that stage alone. Local Pion
process/socket tests may require ordinary outside-sandbox execution. Failed logs
are retained, not overwritten. `late_arrival_evidence.py readback` is strictly
read-only ADB/authorized-NL verification; `summarize` seals the current accepted
test receipts, source/dependency hashes and sanitized evidence. No operator
transition, automatic install, signing, bulk request or secret read is invoked.

Result: conditional1294 recovery at110/125+, but614/1127 remain incomplete;
200+ worsens following-message latency. All constant-only policies, including
baseline100, fail a **finite silence-hold requirement** because expiry is
arrival-driven.125 is a hypothesis, not an implemented/selected live candidate.
Serialized deadline service and physical A/B/A remain unfinished. Do not use this
as evidence that125 cannot help or that a speed fix has been accepted. Prior
observation/candidate recipes below must not be automatically redeployed.

Exact starting pair: beta90 `68cbcccf…` / native `dd722ead…`, accepted b9/1011
`b9ae8807…`. Main is not a clean source for either artifact. This fixture never
uses the rejected read-alignment, SACK-hole or queue-retry functional deltas.
No PERF-3B/canary, new registration, IPv6, hosting migration, push or release.

`preserve.py` verifies exact inventories and copies bounded old evidence privately.
The normal owner beta90 export now preserves the selected A1 head; `saved_episode.py`
joins its lifecycle boundaries with the prior NL capture, including overwrite and
parser errors. It does not discard the old unknown TUN gap or invent the missing
terminal six seconds. `saved_head_test.go` reproduces late5981/frame discard and
partial-assembly retention; its full-pool suffix is explicitly a local model.

`prepare.py` makes fresh exact-source observation copies; it applies existing
hash-pinned performance/receiver overlays once, excludes the old89 version change,
and preserves platform-specific source differences. `android-observation.patch`
and `gateway-observation.patch` are sealed final deltas against exact90/b9, **not
patches for main or a previously instrumented tree**. Verify `source-pins.json`
inputs, apply with zero fuzz to a fresh copy, then verify every output hash.

The receive ring has256 monotonic points plus128 pinned pre-capacity points and
explicit overwritten/later-capacity counters. It records reader/reorder/VP8/carrier
boundaries, not payload or physical NIC observations. No synchronous packet I/O.
The archive projection explicitly accounts for trimmed media context; absence is
never a packet-loss conclusion. Existing512-point ReliableStream trace remains.

`validate.py` tests default/performance builds under race, compiled Java projection,
ordinary DiagnosticRing, bounded chunk export and existing correlator. The initial
Java classpath failure is preserved; `--java-only` reruns only that affected stage.
`correlate_receive.py` binds RTP only within a node/origin/track/timestamp, then
uses observed carrier IDs across nodes. Missing/ambiguous headers remain unknown.
ACK token is local; no cross-node timestamp subtraction or SFU RTP equality.

`build_android.py`, `sign.py`, `upgrade.py` reuse pinned accepted offline workflows.
Code91 is observation-only, same signer/package, install-r only. No overwrite of
90/91 signed APKs, downgrade or data clearing. `build_gateway.py` verifies the
tested exact source and unchanged1011 files. `rollout.py` creates a new ordinary
scoped transition; only its exact currentb9 backup is rollback, not old4b. Reread
current security materials before application; never replay a consumed intent.

`measure.py small` requires one valid64KiB request, two-sided DATA/consume and NL
release, intact capture and stable TUN. Only then `measure.py baseline` runs one
single2MiB + two parallel2MiB cell using the existing phone-side HTTP1.1 meter.
All failures remain; no retry bypass.150s/request,32MiB variant limit,64MiB overall
task limit. Local body hashes are observed values, not independent origin digests.

First small gate retained its failed topology guard. `classify_startup.py` uses
the fresh ordinary91 export to distinguish initial blocking→working TUN from
recovery. `measure.py small-return` then passed on stable tun1;
`measure.py baseline small-return` ran exactly one6MiB cell. `physical_summary.py`
preserves three concrete frame-discard lifecycles, two slow receive/ACK controls,
coverage gaps and cumulative zero capacity. Do not turn missing ring events into
packet loss or tune the100ms deadline to rescue one late packet.

`discarded-frame-candidate.patch` is **local-only, not in91 or the deployed
observation gateway**. It frees only identified irrecoverable partial frames and
uses the existing bounded recent-message lifetime to reject late fragments.
`abandon_frame_test.go` checks repeated loss/retry, valid-fragment duplicate safety,
bounds/expiry and concurrent pruning. Passing these tests is not physical speed
acceptance; live use requires the paired baseline gate and mechanism evidence.
The actual baseline did not show capacity pressure; this candidate was not deployed.
`normal.py` reuses pinned accepted build/sign/upgrade workflows for ordinary code92,
with exact90 source/native and no functional candidate. It restores the copied
private build metadata after the preserved first provenance-check failure; it
does not bypass that verifier. No downgrade, data clearing or public distribution.
`normal-source.patch` applies only to hash-pinned exact90 source; its resulting92
changes version metadata only. `normal_control.py` passively watches TUN then uses
the accepted small HTTPS control, without pressing Connect or resuming bulk.

Private raw logs/exports/keys remain under ignored `state-client-build/` or the
existing protected vault. See the [current report](../../../docs/releases/2026-10-20-mesh-receive-path.md)
for installed/deployed status; source/build presence is not deployment evidence.
