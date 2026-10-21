# MESH throughput — two-sided observation continuation

Follow-up20.10: [receive-path localization](2026-10-20-mesh-receive-path.md) uses
saved **beta90** evidence to identify DATA597 retry2's Android frame discard and
partial-assembly capacity signal. New paired91/b9 observation localizes614/1127/1294
RTP gaps/late arrivals before local frame discard. Current capacity=0, prompt
consume/ACK controls; no functional speed candidate accepted. Ordinary92 trace-off
return is installed; b9/1011 ancestry preserved. Historical negatives are not
retroactively accepted.

Follow-up19.10: [recurrent-closure diagnosis and beta90](2026-10-19-tunnel-restart-fix.md)
supersedes only the current runtime/installed-version state. Normal90 removes
extended Android trace; a separate exact-base seed1011 gateway containment is
deployed. The A/B/A measurements and both rejected speed patches below remain
historical negatives, not retroactively accepted fixes.

## Result —19 October2026 UTC

**PARTIAL: two-sided localization delivered; one minimal speed candidate tested
and REJECTED. No throughput improvement is accepted.** Original NL gateway was
restored15:28:56UTC; strict TLS/runtime/directory checks and final Android-TUN
DNS/HTTPS/identity checks PASS15:30–15:31UTC. The owner phone retains observation-only
beta89 installed over88, not an accelerated APK. No push or public distribution.

Source checkpoint: `8da6fd58b328ac3defe77c11fb6fc8fec15b8109` (local only), based on
the pushed76df691 checkpoint. This commits exact-base overlays/fixtures, **not** a
claim that main is a clean source for the installed APK. Machine-readable results:
[`2026-10-19-mesh-throughput-trace.evidence.json`](2026-10-19-mesh-throughput-trace.evidence.json).

## Scope and baseline

Owner task continues pushed checkpoint
`76df691961aa88a46b73e7a355687fa6f9a3c457`. Local main/HEAD and `origin/main`
readback agree; initial worktree clean. `/home/joker/PycharmProjects/family_connect`
is the existing symlink to `/mnt/data/PycharmProjects/family_connect`, not another
repository. No reset, merge, new branch, push or public release.

Read-only14:10UTC runtime receipt verifies installed beta88/code88 APK
`968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`, restricted
native `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`, and NL
loaded gateway `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`.
NL process3074051, restart count4; this is a later invocation than the prior
13:18 rollback, not a new deployment by this task. all_activated and management
pins match; renewal timer waiting, no pending renewal owner. CRL27130/leaf valid
until16:01:16UTC at this read. A later switch requires fresh validity/readiness.

Accepted gateway inventory `aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483`
and the exact observation overlay are reverified/reproduced; observation inventory
`bc3721ec8c30c6fb304c478b22398926fe3bfc0c576216c49ed53809d78c3051` matches. Android
starts from sealed beta88, not main. Its Family receive-observer, wholedevice
admission/DNS and Telemost source differences are preserved by input-checked
zero-fuzz hunks, not replaced by the gateway tree.

Private receipts and sources: `state-client-build/mesh-throughput-trace-20261019/`.
Baseline receipt SHA256 `8e9552bcb17d14a1957e4a1b6bea4953315f36f34e6776ef724e8b3e0cf10a4d`.
Prior rejected alignment patch/tests/evidence remain unchanged. SendContext is
not re-investigated as stop-and-wait. No identity, admission, authority, floor,
API, wire, timing, queue/window/credit or routing change is authorized by the
observation patch itself.

## Observation implementation and acceptance boundary

New bounded metadata trace uses512 entries per recorder, explicit count/overwrite,
process-local `time.Now` monotonic origin plus separate wall anchor. Logical DATA
key is existing session tag, hashed ordered ReliableStream epoch pair (direction)
and sequence; local origins/tokens are not cross-host wire identifiers. Initial
submission, retries/reason and original submission time, media enqueue/last-fragment
local write, DATA decode/completion, new/duplicate/stale/rejected input, ready head,
consume and ACK input/base/released slots/bytes are distinct events. Receiver
carrier-completion metadata is enabled by `fc_perf_diagnostic`, not ownerDiagnostic.

ACK reasons distinguish receive, consume, duplicate, refresh and handshake. ACK
wire has base/mask but no local token: correlator retains possible matches, never
inventing a unique one or subtracting NL/Android clocks. Last-fragment local media
write is not SFU delivery. Retained/SACKed bytes are not physical bytes in flight.
Existing DATA/window/Mux counters remain; their overlapping waits are not summed.

Native `wholedevice` snapshot -> existing JNI stats JSON -> strict Android projection
-> DiagnosticRing ordinary export -> Python correlator is exercised synthetically.
Periodic sampler exports use checksum-bound1800-byte chunks, scoped by stream,
origin, session and capture; no journald settings change or per-packet I/O. Parser
errors/missing parts are retained, not translated into packet loss. Android also
emits projected chunks outside transport/state locks for bounded live collection.

This is instrumentation, **not an accelerated build**. Native observation is under
`fc_perf_diagnostic`, not `fc_owner_diagnostic`. The private research packaging
gate permits that exact tag only; ordinary public packaging and owner/fault-tag
rejections remain. No fault injection, old UI, canary selection or enrollment.

| Artifact | Exact identity / disposition |
|---|---|
| Installed APK | `0.1.18-beta89-mesh-trace`, code89, `com.familyconnect.app.friends` |
| APK SHA256 | `b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856` |
| Restricted native | `3ca3119ac12c9a3a61b5ebb1ee0244650db39dc36743e355d35bf523b53ef992` |
| Same signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Android source delta inventory | `fe547c53e4d0dfe2db880bde3b89624a13997d32d13916bd4a4dae9f38e2316d` |
| Observation gateway | `f8e6ff0761468672258c3fdd2b69c8c0aefe4ae7ada1fb48e64641191ded71bf` |
| Observation source inventory | `472327a6449a0b866223e21de6c07a17c85f5e1e2e79c0b4507c1dd4ad580e9c` |
| Rejected SACK-hole gateway | `125895bea85a94622e196ac12e4e14d499aac55c93a83121d272d20fa74479b9` |
| Rejected source inventory | `3d0a49fb36624226c1ca1a8095ec8b7500b06a28eb8b17f77c768735f0a5916d` |

Existing APK file:
`state-client-build/mesh-throughput-trace-20261019/delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk`.
Android12+/arm64,16KiB alignment verified. Owner ordinary Disconnect preceded
`adb install -r`;88→89 completes14:40:47UTC. Same UID10283, signer/package, installed
APK/native hashes and existing identity/key-binding/Support ID proof/READY verified.
No uninstall, data clear, invitation, new activation or individual secret in APK.
Only restricted native changes among12 libraries; all eight beta88 recovery source
files are byte-identical. Build receipt precedes signing; signing receipt precedes
installation: their earlier `installed:false` fields are not final runtime status.

## Local validation

- Synthetic normal/lost-original/retry, consumed+lost-ACK/duplicate, head-gap and
  ready-head wait, delayed local ACK write, ACK base release, epoch reuse and ring
  overflow pass. Real Stream adapter callback/queue/export wiring passes under race.
- Synthetic Go envelope -> compiled Java DiagnosticRing/export/chunks -> parser
  yields four two-sided logical DATA, no parser/correlation error. This is local
  evidence, not a phone capture or physical throughput acceptance.
- Nine parser tests cover split/interleaved streams, conflicts, checksum/error
  preservation, missing chunks, snapshot deduplication, duplicate consume semantics,
  ambiguous ACK matches and ordinary export.
- First compile overlapped source authoring; vet failure retained, stable-source
  rerun passed. Loopback socket denials and Gradle daemon denial in the sandbox
  are retained; affected checks rerun outside sandbox, not bypassed in production.
- Stable observation race run273 test passes; affected socket integration rerun
  outside sandbox228 passes/6 opt-in skips. Candidate279 race passes plus228
  socket integration passes/6 skips. No attempt to repair unrelated tests.
- Android build/169 JVM recovery, cooldown, manual-Disconnect, revocation,
  startup/ownership/floor/resource-lifecycle checks PASS. No GitHub CI/public
  release run. Local tests are not repeated physical recovery or overnight acceptance.
- Off/on wire transcript SHA256 identical:
  `9798fa9ce79950fa2126ab348854afdb443e7f738acd070bfd1ca63088e04211`.
  Paced256KiB/40ms TLS+Mux model, three runs each: off3.914–3.925Mbit/s,
  on3.939–4.082. Median CPU one-core11.45%→14.42%, allocations5757→8566;
  observation has measurable CPU/allocation overhead, not zero cost or a speedup.
- Final parser/analyzer11 tests PASS. Initial test assumption of exact6ms sleep
  was corrected to the measured >=6ms bound; terminal null streams and missing
  legacy counters are explicitly covered. Missing counters remain unknown.
- Full512-point Java ring with retained history is135596bytes; ring+incident
  export271213bytes, within existing limits. Secret/payload projection tests pass.
- Exact gateway, Android and candidate overlays reproduced in a fresh `/tmp`
  tree with matching inventories. Patch context whitespace is preserved; ordinary
  files pass `git diff --check` excluding serialized `.patch` files.

## Ordinary rollout and natural recovery

Observation deployed14:42:33UTC/PID3111501. Immediate readback found publication
still propagating; no repeat deployment. Fresh14:45 readback passed. Normal renewal
had independently refreshed limiting leaf/CRL expiry to18:31:41UTC at14:31; no
authority, validity policy or floors were changed for measurement.

First small64KiB exchange passes:114 complete two-sided logical DATA,10NL/3Android
snapshots, zero parser/correlation errors and exact production-PID socket attribution.
Only then A1 bulk starts. Candidate's first deployment attempt stops at the RU
`RENEWAL_RUNNING` guard before any NL mutation. Readback confirms unchanged
PID/hash/profile, absent deploy-intent and completed renewal; guarded resumed
switch succeeds15:05:42UTC/PID3126744. No guard was removed.

The first candidate small exchange returns200/65536bytes but TUN changes during
automatic reconnection: retained as failed stability gate, not bulk acceptance.
The separate stable small gate passes with88 two-sided blocks before B bulk.
Candidate B later reaches `RELIABLE_RETRY_EXHAUSTED`; both parallel HTTP200 bodies
end early with curl18. `dedicated_resources_closed` is observed15:20:16.618UTC.
No intentional loss/outage was injected. No further B cells run.

Candidate rollback to observation15:21:23UTC/PID3137321; small return gate passes
with90 two-sided blocks, followed by complete A2. The same Android native process
origin persists while native session tags and TUN interfaces change; reconnection
requires no new Connect/registration by this task. These natural re-establishments
are observed, but no new full Android incident export proves every recovery-state
transition, cooldown or overnight behavior physically. Keep that limit explicit.

## Physical before / candidate / return

Same phone LTE underlay313, NL/IPv4, verified MESH TUN, HTTP/1.1 fresh connections,
identity encoding, continuously read/hash body on phone. No overlapping control
HTTPS requests. Each phase has distinct media/RS session; observation code is
identical except the one-line functional candidate. Actual Mux streams117/137
are A1 singles;129/131 and143/145 are its two parallel pairs, each handing about
2.106MB. NL process sockets independently match all requested endpoints; background
phone flows are also visible and are not mislabelled as benchmark streams.

| Phase | Single2MiB Mbit/s | Parallel2×2MiB aggregate Mbit/s | Outcome |
|---|---|---|---|
| A1 observation baseline | 0.579953;0.775184 | 1.109971;0.968382 | 6/6 complete |
| B non-head SACK fast-retry | 0.188107 | not a valid throughput result | 1/3 complete;2 truncated |
| A2 restored observation | 0.543238;1.508598 | 1.054508;1.369010 | 6/6 complete |

Single rate uses bytes×8/curl full-request seconds/1e6. Parallel uses total bytes
over the common phone uptime interval, not summed rates or two independent times.
Setup/TTFB included; no body-only rate or HTTPS-as-RTT claim. All responses were200;
no403/429 bypass. B failures contain515447 and446144bytes rather than2MiB each.
Traffic observed across matrices and four small gates:28486711bytes (27.167MiB);
intended upper bound30.25MiB, plus one final215-byte control. Per-variant32MiB and
combined64MiB limits respected,150s/request stricter than180s. No traffic remains.
Cloudflare response hashes are retained evidence, not independently verified
origin hashes or physical byte-exact acceptance.

## Correlation completeness and dominant delay

A1:937 logical DATA with initial submission/new receive/single consume on both
nodes; A2:787; B:671. Larger two-sided counts can include incomplete lifecycles.
The trace is bounded: A1 NL31592 distinct events with6368 interior gaps; Android
12288 with23264 gaps. Prefixes/overwrite counters are saved. Absence is never loss.
All A1/A2 performance chunks reconstruct; B has70NL/27Android intact snapshots,
plus one preserved parser error for a49152-byte **legacy** `diagnostic/lifecycle`
journald fragment. It is not a missing perf snapshot. Raw stream metadata/errors
remain private; no journal configuration changes or repeated broad journal reads.

B observes13 duplicate receives and13 duplicate-reason ACK generations, without
double consume. Sequence863 is received again164.616ms after its one consume;
sequence745 duplicates while waiting behind head741 and is consumed only later.
These are expected retry/ACK behavior, not a duplicate-delivery defect. Missing
duplicate events in the more incomplete A traces do not establish zero duplicates.

Across A1's130s local sample span, the ready NL sender waits a full RS window95.72s;
42.61s is head-unconfirmed with later SACKed blocks,7.36s head-SACKed. Android
ready-head→consume p90=0.878ms/max7.532ms; completion→decode p90=0.221ms/max2.974ms;
ACK generation→confirmed local carrier write p90=7.166ms/max25.349ms. NL accepted
ACK/base processing is locally prompt, not a demonstrated bookkeeping failure.
First-submission→firstACK p90=1216.78ms; release p90=1254.86ms, measured on NL only,
never last-retry RTT. Retry/new DATA bytes2.048/14.380MB. A2 reproduces ready-window
wait66.96s/110s, head-unconfirmed/later-SACK wait31.51s and retry/new1.384/12.740MB.

Mux credit is a concurrent contributor: A1 singles' ready-but-zero-credit times
24.17s and17.91s; parallel streams also wait for RS scheduling and WINDOW_UPDATE.
These waits overlap RS stalls and are **not additive delay shares**. Retained,
SACKed, unconfirmed and local queued bytes remain separate; none is declared
physical in-flight bytes. NL receive RTP counters are reverse-direction only.

**Supported localization:** repeated head-gap/recovery and useful sender-window
stalls, with per-stream credit waits; not slow Android consume or local ACK-write
in the observed spans. Initial DATA enqueue/local media writes, later Android
receive/consume and ACK/base events are all in saved evidence. This does not locate
an exact SFU/network loss point or uniquely assign an arrival to a retry. ACK
base/mask may match multiple receiver generations; tokens are process-local.

## One targeted change — rejected

Baseline `fastRetransmit` required `sequence == state.base`, >=3 later SACKed
positions, age>=RTO/4 and no prior retry. A1 contains95 non-head timeout retries
whose other guards already held;71 wait another>300ms,23 have two-sided lifecycle
evidence. A2 reproduces38 opportunities,29>300ms,13 two-sided. Examples983/984,
1018/1019 and1181/1182 preserve the initial send, retry and one consume. Normal
non-retried16KiB controls from the same session are retained in `localization.json`.
This establishes a concrete recovery-delay mechanism, not the entire average rate.

Candidate removes **only** that head-only condition. No window, ACK/RTO, credit,
pacing, batching, wire or crypto changes; SACKed blocks remain retained until
cumulative consume ACK. Deterministic1–5-hole test fails on baseline, passes after;
age/three-SACK/one-attempt/byte-exact/release bounds and race regressions pass.

Physical improvement is **not confirmed**: B retry/new bytes4.024/3.208MB,
firstACK p90=2729ms, release p90=4330ms, terminal retry exhaustion and two failed
requests. A2 returns to completed requests. Media sessions/ACK/retry conditions
differ; neither the full regression nor the best A2 result is uniquely attributable
to code. Candidate therefore REJECTED and retained only as a negative experiment.
Do not include it or the earlier read-alignment patch in baseline automatically.

## Final state, rollback and remaining fact

Original accepted gateway4b722d…8fab7 restored15:28:56UTC, PID3142658, invocation
`560d88eec8024976b59b802f98d78971`. Fresh15:30:37 strict TLS/leaf/runtime and RU/NL
directory checks pass; directory
`5c38d1acbc3faba48bbffe6c0e018109156839d560b5e023a1cb5d38fa905090`.
Same unit/argv/profile, current credential history; limiting expiry18:31:41UTC at
readback with automatic renewal unchanged. Final215-byte HTTPS control passes,
NL exit and production-PID socket observed; time_total0.830391s is not RTT.
Existing identity/key bindings/Support ID, nonrevocation and CLEANED history pass.

NL perf counters are now **off**; beta89 Android bounded observation remains on.
No sampler/bulk/transition owner remains. Existing backup/receipts record both
rollbacks; do not replay already-used transition intents. No APK downgrade: a
normal same-signer/package code>=90 build can remove observation later while
preserving recovery/data. Public/catalog/invitation-page versions are unchanged;
beta88 remains the existing private delivery candidate, not held for this task.

Remaining specific fact for an accepted speed fix is a repeatable improvement
under comparable media delivery/ACK conditions without retry exhaustion. Current
two-sided evidence narrows the delay to recovery/window/credit interactions but
does not identify where between NL local media-write and Android completion (or
on return ACK transit) loss/delay occurs. No second speculative tuning, new general
profiler, permission handoff or reactivation is proposed as a substitute for work.

| Requested result | Status |
|---|---|
| SOURCE_AND_RUNTIME_BASELINE | exact inputs/readback PASS; local checkpoint8da6fd5 |
| ANDROID_RECEIVER_TRACE | ordinary native→JNI→projection/export path PASS_PHYSICAL |
| NL_SENDER_ACK_TRACE | initial/retry/ACK/base/ready-stall evidence PASS_PHYSICAL |
| CORRELATION_COMPLETENESS | bounded/partial, explicit gaps; perf chunks reconstruct |
| DOMINANT_DELAY | repeated head-gap/recovery + window/credit; exact network loss point unknown |
| TARGETED_CHANGE | one-line SACK-hole candidate REJECTED after physical comparison |
| THROUGHPUT_BEFORE_AFTER | A1/B/A2 above; no accepted gain |
| RECOVERY_PRESERVED | unchanged recovery sources/169 tests; natural reconnect observed, limited physical scope |
| IDENTITY_PRESERVED | same signer/package/UID plus existing identity/key/Support ID READY |
| APK_OR_SERVER_ARTIFACT | installed observation89; original4b722d server restored |
| SPB_IPV6_SEPARATE_STATUS | NOT_RUN; Amsterdam DEFERRED_BY_OWNER |
| FINAL_RESULT | PARTIAL_LOCALIZED_CANDIDATE_REJECTED_SAFE_STATE_RESTORED |

## IPv6 and unchanged delivery

Amsterdam IPv6 = **DEFERRED_BY_OWNER** until hosting changes. Prior FAQ/support
draft is historical, not a current action. SPb IPv6 = **NOT_RUN**; no known node
is silently relabelled Petersburg and no exit-country change is made. Unchanged
beta88 remains available to existing users; this experiment does not gate it.
