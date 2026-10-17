# TRANSPORT-WRITE-BATCHING-1 — local ready-write aggregation

17 October 2026. User requested actual transport modernization after slow mobile
browsing on `admission1`. This is a local product derivative, not another owner
CONNECT, rollout, maintenance operation or claim of measured mobile acceleration.

## Starting evidence and exact boundary

The [export12 analysis](2026-10-17-admission-overnight-export12-1.md) remains valid:
29 admission waits,9 exhausted40s admission budgets, TCP peak64, current18;
37 mux errors were not individually classified. The sampled server send window was
usually empty, so an increased reliable window is not justified by that evidence.
Successful lease extension and two separately matched gateway stop/start events
are not a universal explanation of all disconnects or a ten-minute timer fix.

Last confirmed installed/deployed parent, not newly read this task:

| Identity | SHA256 |
|---|---|
| Signed/installed `admission1` APK | `761430c0989fd2443cebad39f6cf972d21ef25123114e118ee841029c2149b1f` |
| Native | `6d41518ffbe2b10c767552dbb4c1bc732911fb8439a525215c353541ca41cfab` |
| Client source inventory | `c1eade0110278827c1681438a80c0509f352e2c9174badef0d3b228cc7161e9c` |
| Gateway executable | `079729e4de680cb416c55c2b9b592c6450e4254a306a6960b087930cc549639d` |
| Gateway source inventory | `0742212c5ebe38f9673dc53321d3af56c14b978e1080cbe104216ac21b40293f` |

Isolated copies preserve the retained parent, accepted historical APKs and dirty
root worktree. No checkout of old root main as the product source. Source inventory,
base Git revision, executable hash and this publication commit are different IDs.

## Implemented change

1. `familysession/batch.go`: at most32 existing Family messages are framed with their
   individual lengths and ordered sequences, then written under the existing TLS
   send lock. Maximum aggregate plaintext16,362B. Legacy receivers decode unchanged
   message framing; authentication, expiry, cancellation and first-failure paths stay.
2. `tcpforward/mux.go`: drain only frames already available to the existing scheduler.
   No collection timer or waiting for a batch; a lone frame is sent immediately.
   Existing priority/round-robin selection order remains. At most one selected frame
   that does not fit is carried forward. Terminal stream removal waits for the sent
   terminal frame so that carried RESET is not discarded after earlier data.
3. `tcpforward/mux_stream.go`: cap batch-capable endpoint data chunks at16,340B.
   Including10B mux +12B Family +22B TLS1.3 overhead fits the default16KiB reliable
   payload rather than generating a tiny extra frame. Initial TLS record sizing or
   smaller negotiated reliable payloads can still split; this is not a one-record
   guarantee for every write.

This uses the existing eight-frame send window more efficiently with many small
writes. It does not enlarge that window, receiveQueue64, TCP64+32 admission limits,
DNS/lease reservations, retry budgets, RTO, authentication or production deadlines.
No crypto/wire version/ownership/renewal/security policy changes. UI, Java behavior,
JNI contract, Xray boundary and all dependencies remain unchanged. Native is newly
built, not mislabeled as the old native. The private version name distinguishes it;
versionCode84 stays for ordinary same-signer compatibility, not downgrade bypass.
The real client `wholedevice/session.go` and server `roombroker/gateway.go` already
construct `NewMux` over the authenticated Family session; the new capability is on
that actual shared path, not only on a test adapter or unused standalone TCP proxy.

## Fixed local experiments

The [fixtures, patch, runners and logs](../../research/transport-write-batching-20261017/README.md)
use synthetic credentials, local sockets and no real provider, phone or destination.

**Actual Family TLS → mux → local TCP echo**, four concurrent streams,64KiB each
sent and echoed, byte-exact, synthetic40ms latency each way, no injected loss:

| Run | Parent ms | Candidate ms | Parent data frames client/server | Candidate client/server |
|---|---:|---:|---|---|
| 1 | 4487 | 983 | 435 / 430 | 91 / 82 |
| 2 | 4728 | 980 | 458 / 453 | 91 / 83 |
| 3 | 4561 | 904 | 445 / 442 | 88 / 84 |

All six runs: correct bodies, no retransmissions. Median4561→980ms, about4.65× faster
**in this fixture only**. It does not measure a mobile browser, provider capacity,
lossy real-world performance, single large download or site/server latency.
Separate gateway-source runs pass the same exact-body checks.

Family-only prequeued small-message fixture:256×384B, old256 data frames versus
new19;2607/2607/2611ms versus205/204/204ms. This deliberately grouped envelope is
not presented as the actual automatic mux or as phone throughput.

The64 idle-slot fixture confirms the next opener remains waiting until a normal
stream closure; the baseline and candidate release the slot within0–3ms in sampled
local runs. Half-close/reset cleanup ends with no retained streams/sockets. This
does **not** fix legitimate64-connection keepalive occupancy, prove absence of all
browser leaks, or authorize forced eviction, larger limits or a shorter deadline.

## Regression checks and retained failure

- Targeted client and exact gateway derivative normal/race checks pass: Family
  authentication/expiry/replay/cancellation, batch limits/sequences, scheduler order,
  immediate sends, carried-terminal handling, admission FIFO/bounds/reserved lease,
  mixed batch/legacy endpoints, half-close/reset and end-site TLS closure.
- Added actual Family TLS + new mux loss/duplicate fixture: three32KiB streams,
  byte-exact, positive retransmissions; exactly two normal and two race repetitions
  per source tree. Synthetic loss only, no live fault injection.
- Initial wider candidate race run fails inherited
  `TestMuxConcurrentExactSegmentation/32` at its15s fixture wall-clock deadline under
  CPUQuota50%. An unchanged-parent comparison fails the same bound. Neither initial
  run is relabeled PASS; no race-detector report appeared.
- A predefined one-run-per-side comparison overlays only the two test fixture clocks
  to60s. Both pass within the bounded80s test limit. Product deadlines stay unchanged;
  the slow inherited fixture is not silently excluded from the result.

All tests/builds use one Go worker and50% CPU quota. Start threshold75°C, cutoff85°C;
no emulator. Test peak82°C in the inherited parent race comparison. No assertion that
the machine cannot overheat in other workloads; the guard controls this work only.

## Candidate artifacts

Build result and final artifact identities are recorded in the companion evidence.
Private version: `0.1.18-research84-ui60-4-batch1`, code84, API31+, ARM64.
Client source inventory `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790`.
Gateway source inventory `aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483`.
Base Git revision `f5240994869826c6a28f59e58e38256c688cf6eb` is not either inventory.

| Built artifact | SHA256 |
|---|---|
| Unsigned APK | `56b3c958f696d09d216e06b3128b194c5b8c7b9df21c1c2661ba1d8b18049db5` |
| New embedded native | `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23` |
| New gateway executable | `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |

RESULT=PASS_LOCAL_BOUNDED_CANDIDATE_NOT_DEPLOYED. Native C-shared build, full
`assembleResearchProvisioning`,100 tests in13 selected JVM/export/state suites,
Java/C JNI contract checks and gateway build pass. APK56,007,341B; exact embedded
native/provenance checked,16KiB alignment PASS, non-debuggable, unchanged permissions,
API31/target35/ARM64, all other native libraries unchanged. `apksigner verify`
confirms the artifact is unsigned. Gateway Go1.26.1/CGO1/dependencies retained;
gateway executable built but not run. No signed candidate or install exists.

Build ran458.571s with maximum sampled CPU73°C. Existing deep Git-alternate warnings
appeared, but exact base/tree resolution and provenance guards succeeded. Gradle
overwrote its inherited nonproduct HTML problems report in the source copy: the
post-build seal correctly rejected this extra difference. Moving only the new report
outside source initially still failed because the inherited copy was then missing.
Both receipts are retained. `postcheck.py` preserves the new report privately,
restores the byte-identical inherited report and repeats the strict inventory guard:
exactly the six intended files differ; built client/gateway inventories unchanged.
No product source, manifest guard or test result was adjusted to hide that artifact.

## Outcome and next boundary

Local batching modernization implemented and byte-exact transfer improvement
demonstrated in the stated fixture. It is not proof that every slow website, idle
slot, protocol error or disconnection is fixed. Provider/RTP and mobile throughput
acceptance are not reclassified from these local results.
Safe build/test hashes and retained failure receipts are in the
[evidence bundle](evidence/2026-10-17-transport-write-batching-1.json).

Any next step must verify fresh exact installed/deployed identities and ordinary
compatible retained backups, current security/runtime readiness and scheduling,
then coordinate a private paired rollout and a small timed owner download. Preserve
the previous APK/gateway. Do not auto-connect or restart to hide an error, loosen
security, replay application writes, or claim a lower-version rollback is safe.

Phone untouched; last known export12 had VPN CONNECTED, not a newly verified final
OFF. Existing live gateway/config/material untouched by this task, current runtime
not polled. SSH0, ADB0, CONNECT0, export0, signing0, installs0, rollbacks0,
deploy/restart0, maintenance0, emulator0, additional native-stats pollers0.
Historical causality, chat handoff, supervisor, field and public release remain open.
