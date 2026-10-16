# RELIABLE-FAST-RECOVERY-LOCAL-1 — local source candidate

**RESULT=LOCAL_CANDIDATE_PASS_WITH_LIMITS; LIVE_THROUGHPUT_GAIN=NOT_PROVEN.**
The owner authorized starting the proposed isolated throughput work. This implements
and checks a narrow fast-recovery derivative, not another UI-only patch or deployment.
The prior [source-only proposal](2026-10-16-ui60-throughput-follow-up.md) and export9/10
findings remain historical evidence; neither is retroactively labelled a speed fix.

## Exact source boundary

| Identity | Value |
|---|---|
| Review checkpoint before work | `1656370c91d0a8f82a14ebd84689c62c426c6465` |
| Retained product parent inventory | `e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce` |
| New candidate cumulative inventory, not Git SHA | `bb23c58fcfe27bcb817141167eb30b9ea638145dc06c19c24de8ed4831c9bcc0` |
| Candidate patch SHA256 | `bd9fc084f6684019d62518dca08bfd08f698f68df976597959ccbf734dd5524e` |
| Local Go1.26.1 tool SHA256 | `548e61b2d08ae52043be2f1924ed3c1d2b2c41967e360f3e317667f6fa912fc2` |
| Last verified installed APK, untouched | `1bf56c381e76913d77c4dc518961020d82d2bfec33da69777a504b7569be15ef`, UI60-4/code84 |
| Last verified installed native, untouched | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Retained gateway executable, not queried/changed | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |
| New native/APK/gateway executable | NOT_BUILT; no signed/installable candidate |

Baseline and candidate are separate copies of the retained UI60-4 source. The only
product change is `carrier/reliablestream/engine.go`; two test files are added. All
other files match the retained source, including async writer/receiveQueue64, UI,
native/JNI interface, admission/ownership, security, bootstrap correlation and recovery
orchestration. Neither root main nor beta60 supplies transport behavior. The baseline
adds only the identical comparison test, not candidate product changes.
[Boundary/inventory/patch and reproducer](../../research/reliable-fast-recovery-20261016/README.md).

## Implemented policy and bounds

The existing ticker may retransmit the oldest outstanding **unsacked** block early
when at least three distinct later blocks are already selectively acknowledged and
the head has aged at least RTO/4 (250ms with the retained1s RTO). It is eligible only
before its first retry. ACK duplication alone cannot satisfy the distinct-block rule;
a SACKed but unconsumed head is not treated as lost. Only the head is accelerated,
not every hole in one burst. Actual dispatch retains the existing idle-writer/ticker
rules; no extra reader, goroutine, timer or queue is introduced.

The retransmission retains identical FRS1 epoch/sequence/payload and uses the existing
retry budget. RTO, MaxAge, MaxRetries, payload/window limits and pacing values are
unchanged. **Effective retry exhaustion can be earlier** because one allowed retry
is spent early (policy shift up to750ms at default RTO); no extra retry allowance or
deadline extension is hidden. Subsequent loss falls back to ordinary RTO. Existing
retransmit counters/events include early retries; Timeout increments still require
actual RTO expiry. No new diagnostic export field or schema is added.

## Fixed local comparison results

Same13 cases on both sources, normal3 repeats and race2 repeats, no retry-until-pass.
The virtual fixture sends1MiB of synthetic exact bytes through real engines and FRS1
encode/decode. Model assumptions:60ms each direction,6ms serialization per data block,
10ms steps and100ms ticks. **These are model completion times, not phone/SFU speed.**
All virtual rows are identical across the five repetitions per variant; byte identity
and send-window high-water≤8 hold throughout.

| Case | Baseline → candidate completion | Baseline → candidate retransmits |
|---|---|---|
| No faults |1040→1040ms|0→0|
| One missing head |2040→1340ms|1→1|
| One missing middle block |2020→1320ms|1→1|
| Eight periodic head losses |9460→3160ms,2.99× model completion speedup|8→8|
| Three simultaneous holes |2040→1720ms|3→3|
| First retry also lost |3040→2340ms|2→2|
| Final block lost, no later SACK evidence |2060→2060ms|1→1|
|80ms added head reordering |1610→1610ms|0→0|
|400ms added head reordering |4170→3160ms|0→8 redundant retries|
|400ms additional reverse ACK delay |3840→3840ms|0→0|
| ACK outage before450ms |1980→1980ms|8→8|
| Duplicate ACKs |1040→1040ms|0→0|
| Receiver consumption delayed until450ms |1430→1430ms|0→0|

For one missing head, maximum no-delivery interval falls1060→360ms; for periodic
head loss1200→400ms. Long reordering is a real tradeoff, not a clean-loss win:
8 early copies are unnecessary;7 receiver duplicates are observed before the fixture
ends (the final delayed original is outside that completion boundary). Do not report
that as zero overhead or as proof of actual packet loss. No adaptive reordering/RTT
estimator is implemented. Reverse ACK delay/outage and tail loss do not improve.

The real in-memory `Stream` adapter separately transfers129600 identical bytes after
one dropped head, exercising the actual async writer/receiver pipeline. Baseline
normal times1201/1200/1201ms, race1201/1202ms; candidate normal401/401/400ms,
race401/402ms. Each has one retransmit; baseline has one RTO timeout, candidate zero.
These elapsed times include local handshake/scheduling and are not mobile goodput.

Five new focused unit tests cover distinct SACK evidence, duplicate ACK suppression,
grace/single-shot/RTO fallback, reordered original/slow consumer, foreign epoch and
cumulative ACK handling, and exhaustion bounds. Fifteen inherited targeted regression
test functions run once normally and once with race, including byte-exact faults,
backpressure/cancellation, malformed ACKs and first-failure-before-cleanup. All pass;
no race report. [Results](../../research/reliable-fast-recovery-20261016/results.json)
and [synthetic test logs](../../research/reliable-fast-recovery-20261016/test-logs/)
retain actual repeat counts; parent/subtest PASS events are not advertised as that
many independent experiments.

Checks use existing Go1.26.1 offline, CPUQuota50%, GOMAXPROCS1/-p1,2GiB memory cap,
75°C start guard/85°C cutoff and finite stage/batch limits. Peak CPU temperature80°C;
all six commands exited normally. No emulator. No retry, thermal-guard override or
unrelated transport/race/PKI suite is used to inflate the result.

## Remaining gates and final state

This establishes a local recovery benefit under selected data-loss conditions, **not
the primary cause of the owner's low download speed**. Next: validate reordering cost
and the complete local Family TLS/mux/VP8 path, including mixed-version peers, before
any native/APK/gateway candidate build or separately authorized live comparison.
No window/pacing tuning has been combined with this change. The separate scheduled
cutover/stale-directory restoration problem is not repaired by early retransmission.

Phone/gateway are untouched and not freshly polled. Installed UI60-4 and its private
same-code backup remain retained; new native/APK/server bytes are not produced.
Actions: one isolated source candidate, one fixed six-command test batch; ADB/SSH,
sign/install/rollback/CONNECT/export/restart/deployment/current4h changes0. Public
APK/catalog/main/workflow changes0. Earlier exact-pair PASS_BOUNDED is not reassigned;
historical causes, chat handoff, supervisor, FIELD-1 and release stay at prior scope.
