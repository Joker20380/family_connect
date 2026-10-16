# BROWSER-ADMISSION-LOCAL-1 — mechanism reproduced; live attribution remains bounded

Date:17 October2026 local. Parent publication:f04e5ad4d23fe8afaad33880caaca2a73e6c690c.
Continuation of [export11 investigation](2026-10-17-speed-candidate-web-traffic-failure-1.md),
not a new device trial. Owner clarification: search still returns results while most
sites/static assets fail. This is partial connectivity reported in UI, not a saved
HTTP response receipt, measured throughput, or proof of universal DNS health.

**RESULT=LOCAL_ADMISSION_MECHANISM_REPRODUCED_ON_BOTH_SOURCES.**
**OWNER_FAILED_REQUEST_TO_QUOTA_BINDING=NOT_PROVEN.**
No transport/product patch, APK/native/gateway build, signing/install, SSH/ADB,
CONNECT, new export, rollback, restart, credential action, emulator or native-stat poll.

## Exact inputs and unchanged installed boundary

| Identity | SHA256 |
|---|---|
| Last verified installed APK | `28543d4690327e29a6eb6a60e52fa50232a407663ed7e610f1434cd56f86193d` |
| Embedded native | `f25124ba1c94a0c6f4258e8b67488e8febf9a1c9e88cb2073790564c3a1f4729` |
| Current client cumulative inventory | `211b127d545af5c129acc93bf0ff78cac3af93707aad8def27bb6da830e2ae86` |
| Last verified loaded gateway | `5de40b9ce9c15aac85475df05c449bddf2ecfe61a1928fa3844b4a8446b33047` |
| Gateway source inventory | `3693f70552d27365a56eb9f625f8afe03c01f7e513acdc04cb31e107f52d837e` |
| Previous UI60-4 client source inventory | `e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce` |
| Retained export11 | `bcc5a08d4638550c136b7c97243cb18a8a071eac1ff7022a8993c46b48a83c30` |

Publication SHA is not source inventory or binary identity. Previous sources are the
retained UI60-4 derivative, not root main or beta60. Relevant admission, DNS and lease
source bytes match both versions and the separately retained gateway derivative.
The different reliable engines are genuinely compiled in separate test runs.

## What is now demonstrated locally

Real Family TLS → ReliableStream → mux → wholedevice forwarding carries trusted
fixture HTTPS/HTTP1.1, with exact response-body checks. Reliable defaults stay unchanged,
no loss is injected. Synthetic local endpoints replace provider media and external
destinations; no actual browser/TUN/gVisor or cellular network is run.

| Condition | Observed result, same on previous and current source |
|---|---|
|32 established idle TLS connections | Existing search3/3 and existing asset1/1 succeed |
| Additional new connection | TLS fails before origin HTTP; wholedevice `limit_denied` increments |
| DNS at32 | Matched synthetic UDP DNS succeeds; TCP DNS is refused by shared TCP slots |
| Control open at32 | Local `ErrStreamLimit`, no server control callback |
| Close one established connection | New HTTPS/static request succeeds without session restart |
|40 sequential application closes | Every response exact; packet/mux/socket counts return to0 after each |
|40 sequential origin closes | Same, no retained slot leak in this fixture |
|40 sequential application TCP resets | Same, no retained slot leak in this fixture |
|31 data streams plus1 held control stream | New data refused by mux, existing search works |
| Release that control stream | New HTTPS succeeds without reconnect |

The last condition exposes a second observation gap: `packet.limit_denied` stays0
because the wholedevice slot was available, but `Mux.OpenTCP` rejects on the shared
stream budget before recording `OpenErrors`. Consequently adding only the old packet
counter to export would still miss that distinct refusal path. No counters are changed
in this investigation. Zero exported open errors does not exclude local rejection.

`MaintainLease` uses the same `Mux.OpenTCP` budget. A full data budget can therefore
prevent control-stream admission as demonstrated here. The fixture callback is NOT
the real lease protocol; no live lease starvation or historical ten-minute cutoff is
attributed to this result. Existing expiry/retry/auth policies remain untouched.

## What this means for the owner observation

Export11 S2 retained32 active/peak TCP connections. The local test reproduces the
combination “existing search works, new sites/assets cannot connect” at that occupancy
and removes it by releasing a slot. This is stronger than simply observing a numeric
limit, but it does not recover missing per-request phone evidence. We do not know
whether this search used an old connection, HTTP2, cached resources or another path.

The32 cap and local refusal behavior exist before the speed candidate. No claim that
fast retransmit introduced this cap or caused these website failures. No promise that
rolling back cures the inherited behavior. Initial TLS/connect/response stages of the
actual failed origins remain unobserved; QUIC/IPv6 restrictions and destination-specific
failures are not ruled out by one working search engine or aggregate DNS responses.

The tested normal closure paths reclaim slots: a universal connection leak is NOT
demonstrated. Real browser keepalive, half-close, loss, gVisor or app-specific retention
may differ. The10 owner-client mux protocol errors are NOT reproduced/explained by
these tests. A separate local observation: race-mode origin-close cases retain26
current-source and30 previous-source **server** protocol errors despite40 exact HTTPS
bodies and complete slot/socket cleanup in each. Client counters remain0 throughout;
all normal-mode lifecycle counters are0. These aggregates show why protocol-error
counts need stage/side attribution; they do not prove corruption or explain the owner's
client-side10 errors. No new claim that all such events are harmless.
Earlier S1 reliable handshake failure and late post-OFF S2 terminal remain distinct;
the new local result does not rewrite either first failure or historical A/B causality.

## Validation and evidence limits

Five leaf cases × (normal2 + race1) × two source variants = **30 PASS**, fixed in advance.
**1,140 synthetic HTTPS bodies** verified, including720 sequential closure cases.
Four successful Go batches, no retry. An initial postprocessing assertion incorrectly
required all protocol counters to be0 and rejected the race receipt; the summary is
corrected to retain the nonzero observations, not discard them or rerun tests until0.
The admission/cleanup assertions passed; this is not a zero-protocol-error acceptance.
CPU quota50% of one core, peak83°C; start75°C/
stop85°C guards, no emulator. Only test binaries compiled; selected retained product
source hashes remain unchanged. Gateway mux/lease source equality is checked, but the
fixture compiles both peers from each client tree; this is not an exact-binary gateway,
live provider, real-site DNS, mobile performance or device acceptance test.

[Runner, tests and four logs](../../research/browser-admission-20261017/README.md) ·
[Safe inputs/results and hashes](evidence/2026-10-17-browser-admission-local-1.json).
The original raw export/journal is not republished. No new retention evidence is
invented: export11 limitations remain those in the preceding report, including missing
quota counter, trace/boundary drops and bounded server window.

## Next step and final state

Focus the next candidate on bounded admission/control capacity and diagnostic visibility,
not another blind speed increase. Preserve real active sessions; no arbitrary eviction,
unbounded queue, timeout extension or authorization bypass. At minimum both refusal
surfaces need distinct safe counters through the existing native→Java→ring/export path
before another owner attempt. Any product fix must be tested for overload, cancellation,
valid long-lived flows and control access; it is not installed or implicitly authorized
as a live operation by this local investigation.

No current device/server readback in this turn. Last observed phone state remains the
prior receipt's VPN OFF, candidate installed; last observed gateway was running5de40b9c.
Do not call those old timestamps a fresh maintenance/readiness guarantee. Actions:
local test batches4; product patches/builds/install/rollback0; SSH/ADB0; CONNECT/export0;
service transitions0; native-stat polls0; emulator0. Public artifacts and release status
unchanged; current pair still not device-accepted. Historical accepted-pair checkpoint,
handoff, supervisor, field/release and historical causal-binding scopes remain unchanged.
