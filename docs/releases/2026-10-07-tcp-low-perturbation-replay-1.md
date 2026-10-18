# TCP-LOW-PERTURBATION-REPLAY-1 — PASS

PASS means the bounded replay and proportional decision gate completed, NOT that
TCP is proven defect-free or the historical initiating cause is known.

## Historical reconstruction

Validation source remains `6d1bddaa886d7320faa7b8ea978a55167c5c0981` plus test-only
overlays. Preserved failed invocation was TCP-only in a fresh process after
force-stop/application-data clear. Previous independent TCP trials passed including
cancel/revoke tails; their PIDs2870/3907 differ from failing PID4416. No prior Auto
activity in that same process is supported or added to this replay.

After permission grants, activity launch and synthetic profile checks, the method
runs TCP → stop/clean → WG → stop/clean → TCP → stop/clean → AWG → stop/clean → TCP,
then cancel/revoke and final cleanup. Historical failure was in the final TCP
traffic call, BEFORE that iteration's cancel/revoke. Exact request ordinal/family
and failed predicate cannot be inferred from HTTP12/DNS24 counts.

Historical guest timestamps: first TCP13:09:55.310, WG13:10:10.250, second
TCP13:10:10.500, AWG13:10:24.269, final TCP13:10:24.516, underlying system default
to eth013:10:24.636, AssertionError13:10:24.783 at traffic:26/caller:43, return to
wlan013:10:25.762. This correlation does NOT prove a network-caused assertion.
Complete historical and older cleanup-masked receipts remain intact; their causes
are not declared equal.

## Instrumentation and constraints

One test APK selects observer mode once through an instrumentation argument:
- A/minimal: original predicates with separate status/body labels. Successful HTTP
  path has no network queries, JSON, response parser or diagnostic output.
- B/rich: prior traffic body retained byte-for-byte after dispatch, including its
  existing network snapshots and successful receipts; no extra verbosity added.
- C/original-like: original message-less JUnit assertions and socket/read/write
  behavior, retaining safe cleanup and failure-only capture.

A/C retain the existing response buffer, primitive stage/count fields and a few
monotonic timing milestones. Only on failure are status/body lengths parsed and
bounded category, masked80-character prefix/suffix, EOF/reset/timeout, socket
addresses, selected/default/explicit-bound network information, VPN state, routes
and timing emitted. Diagnostic exceptions remain suppressed on the initiating
exception. No secrets/full arbitrary payloads, per-packet logs, hot-path route
polling, added wait or HTTP retry. C is original-like, not identical old bytecode:
safe catch/cleanup, counters and clock reads remain.

Original connect/read timeouts10000/15000ms,8192-byte cap, six requests per traffic
call,18 HTTP requests per complete lifecycle, status/body predicates and DNS
assertions unchanged. Source guards verify hot-path exclusions, original limits,
unchanged B body, and runtime/fixture source isolation. Only isolated investigation
androidTest source extended; main-checkout previous diagnostics match their earlier
integration hashes. No runtime/version/RTP/Reliable/ACK or fixture source change.

## Fixed matrix and results

Plan fixed before execution:60 complete lifecycle attempts,20 per mode. First
three original-like trials reconstruct the consecutive-trial shape; the remainder
balances/interleaves modes. Each force-stops both packages, clears disposable app
data, starts fresh peers and a fresh instrumentation process; emulator is reused.
No HTTP/trial silently retried. User connection interruption did not stop the
running matrix or duplicate/restart trials.

| Mode | Complete PASS | Failures | JUnit median | Range | Final TCP→eth0 within1.5s |
| --- | ---: | ---: | ---: | --- | ---: |
| A minimal | 20/20 | 0 | 47.338s | 44.790–49.354s | 19/20 |
| B rich | 20/20 | 0 | 47.439s | 42.072–49.106s | 19/20 |
| C original-like | 20/20 | 0 | 47.200s | 43.047–51.130s | 17/20 |

Total60/60 PASS,1080 fixture HTTP completions,60 distinct test PIDs. All logs show
the exact five-transport sequence and complete method success including cancel/
revoke. A/C emit zero success receipts; B emits360. Historical final-TCP underlying
default transition occurs55/60: e.g. original-like trial1 final TCP14:32:14.884,
eth014:32:14.958, wlan014:32:16.138, PASS. No live failure category or failing
response/network receipt exists to interpret. Diagnostic/cleanup regressions7/7
JVM and7/7 Android; test build/source/whitespace guards PASS. Prior unchanged exact
HTTP fixture audit24/24, concurrency4, remains applicable; no fixture fix.

No observed failure-probability difference (0/20 each). Small samples and shared
emulator/time dependencies do not establish statistical equivalence or exclude
a rare race. Earlier richer48/48 remains a separate experiment. Fixed60 satisfies
the minimum; extending an approximately50-minute replay to100 would add substantial
time without a captured failure to investigate. This is not proof of perfect TCP.

## Environment and limits

Dedicated emulator-5560, API35 Google APIs x86_64, fingerprint
`google/sdk_gphone64_x86_64/emu64xa:15/AE3A.240806.043/12960925:userdebug/dev-keys`;
emulator37.2.12.0/build16428233 matches old receipts. Cold boot, snapshots disabled,
headless SwiftShader,2048MiB, two guest CPUs. Host12 CPUs/12 affinity CPUs;
GOMAXPROCS unset/no new override; one-minute load0.555–1.816; ADB `device` throughout.
Historical per-trial host load is unknown. Sixty distinct test processes, one
reused emulator. Route sample once before each invocation outside traffic: first17
main-table samples, subsequent43 bounded all-table samples. Existing eth0/wlan0
paths persist. Default/VPN transitions are extracted after runs from existing
logcat, not traffic polling. No route was changed or forced.

Installed runtime SHA256 verified before each trial, before/after matrix and
before final regression invocation:
`7bf76976ada6cb35e7178c23892c88688a8ab956a755a3e8e43a8f1be45e26c1`.
Only test instrumentation installed once, SHA256:
`fa9b1b81a9fc170dabc7f92591c5a6b75274fa09a210b617a2f53c9c6f5347d8`.
Application package NEVER replaced/reinstalled. Historical runner reinstalled
runtime/test packages between trials; that package-manager activity is deliberately
not recreated under the explicit current constraint.

Exact historical scheduling, background-validation timing, boot/cache age and
packet-level state cannot be reconstructed. There is no old packet/response
capture. Nevertheless known app/process/profile lifecycle, image/runtime, transport
order, permissions, assertions and the temporally relevant network transition are
reproduced closely enough for this bounded risk decision. No unknown prior Auto
state or artificial failure sequence was invented.

## Classification and gate

Historical classification: **NON_REPRODUCED_HISTORICAL_FAILURE**. Original predicate
and root cause remain unknown. Production TCP is not implicated by causal evidence;
neither beta69-specific regression nor exoneration of all possible defects is
claimed. Previously verified beta68/beta69 relevant runtime source is identical;
no independent beta68 binary trial is newly claimed.

**Should this historical TCP failure continue blocking ANDROID-HARNESS-ACCEPTANCE-1?
NO.** Bounded minimal/original-like replay did not reproduce it, relevant network
transition remains represented, runtime unchanged, fixture deterministic in audit,
cleanup fixed/regression-tested, no causal evidence against production. Keeping
the isolated receipt as sole blocker is no longer proportionate. Preserve it as
unresolved historical risk, not a proven fixed defect. A new failure still fails.

Harness acceptance may resume from test-only source review. Replacement validation
SHA, required exact-source local acceptance and BOTH complete hosted workflows
remain separate mandatory gates. This does not accept the harness or authorize
freeze signing/publication/deployment by itself.

No new commit/replacement SHA/version/beta70/tag/push/CI/signing, physical-device/
Redmi action, gateway change or runtime deployment. Emulator stopped; fixture
ports51820/51821/51900/51902 clear. Nothing deployed needs rollback. Investigation
source/APK remain isolated; main checkout prior test overlay and unrelated dirty
work preserved. Concurrent read-only VPN-audit documentation preserved as well.

## Evidence and next step

Evidence: `state-client-build/field65-export16/tcp-low-perturbation-replay-1/`:
`matrix-results.json`, `summary.json`, `decision.json`, `environment.json`, per-run
environment/results/instrumentation/logcat/peer logs, failure-only JSON,
`network-timelines.json`, `historical-sequence.txt`, APK/build/source guards,
historical/iteration SHA256 receipts and seven-test regression receipts.

Exactly one recommended next step: resume ANDROID-HARNESS-ACCEPTANCE-1 from review
of the test-only correction, carrying historical and bounded-replay evidence
forward without treating this result as final release acceptance.
