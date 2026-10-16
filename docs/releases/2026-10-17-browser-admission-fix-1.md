# BROWSER-ADMISSION-FIX-1 — bounded connection capacity and control reservation

Date:17 October2026 local (build/check events span16 OctoberUTC).
Parent review publication:`85f033752c4f79f258a9383e1249f40a5a88aa9c`.
User authorized a fix after the [local browser-shaped reproduction](2026-10-17-browser-admission-local-1.md).
This task changes retained product sources locally. It is not an owner trial or rollout.

**RESULT=PASS_LOCAL_BOUNDED_CANDIDATE_NOT_DEPLOYED.** Targeted normal/race and12
direct JVM checks pass, as do full native/JNI/Gradle/gateway builds and100 selected
Gradle JVM tests. This is local verification, not device/browser acceptance.
**PHONE_AND_SERVER_UNTOUCHED; OWNER_BROWSING_FIX=NOT_YET_VERIFIED.**

## Exact source and artifact boundary

| Identity | SHA256 / value |
|---|---|
| Parent client cumulative source | `211b127d545af5c129acc93bf0ff78cac3af93707aad8def27bb6da830e2ae86` |
| Parent gateway cumulative source | `3693f70552d27365a56eb9f625f8afe03c01f7e513acdc04cb31e107f52d837e` |
| New client cumulative source | `c1eade0110278827c1681438a80c0509f352e2c9174badef0d3b228cc7161e9c` |
| New gateway source | `0742212c5ebe38f9673dc53321d3af56c14b978e1080cbe104216ac21b40293f` |
| New unsigned APK | `ff4a844f8de2df2aac4df5f7e5ec35ae10746033730177e3a9f19e8c0c35edda` |
| New native | `6d41518ffbe2b10c767552dbb4c1bc732911fb8439a525215c353541ca41cfab` |
| New gateway executable | `079729e4de680cb416c55c2b9b592c6450e4254a306a6960b087930cc549639d` |
| Version | `0.1.18-research84-ui60-4-admission1`, code84 |
| Package / applicability | `com.familyconnect.app.friends`, API31+, ARM64 |

Retained source basef5240994869826c6a28f59e58e38256c688cf6eb is not the cumulative
source identity. Publication SHA, source inventories and artifact hashes are separate.
The root dirty worktree, original source snapshots and accepted artifacts are preserved.
New candidate source is derived from the actual installed speed/recovery source,
not old main, beta60 or a reconstruction from a release title.

Last verified installed APK remains
`28543d4690327e29a6eb6a60e52fa50232a407663ed7e610f1434cd56f86193d`, native
`f25124ba1c94a0c6f4258e8b67488e8febf9a1c9e88cb2073790564c3a1f4729`; last verified
gateway executable remains
`5de40b9ce9c15aac85475df05c449bddf2ecfe61a1928fa3844b4a8446b33047`.
These are prior readbacks, not new phone/server observations. Signed candidate hash
does not exist. VersionCode is not raised; no downgrade bypass, signer or permission
change is planned. Actual replacement compatibility and same-key payload verification
remain future rollout gates, not a claim of performed rollback.

## What changed

1. Ordinary mux capacity32→64, with a bounded FIFO of32 pending opens. The original
   40-second open budget includes waiting. Overflow, timeout and cancellation are
   explicit counters; queued callers do not allocate mux windows. No arbitrary idle
   eviction, forced holder release or infinite retry is introduced.
2. A single reserved lease-control stream cannot be consumed by ordinary traffic.
   Server reservation requires the existing exact control destination and existing
   callback. Real Family authentication, authorization/floors/revocation, sequence,
   security expiry and renewal protocol remain intact. One waiting lease is allowed
   only during terminal predecessor removal; duplicate live control is rejected.
3. Wholedevice bounds are96 ordinary handlers (64 active+32 waiting),16 DNS handlers,
   4 service handlers. TCP DNS uses the separate DNS pool instead of competing for
   ordinary TCP slots. Chat still shares ordinary mux capacity; it is not bypassed.
4. In the pinned Xray/gVisor adapter, `ForwarderRequest.Complete(false)` now follows
   successful endpoint creation rather than the full connection lifetime. Established
   sockets no longer consume the64 in-flight handshake budget. Endpoint, TCP buffer,
   wholedevice and mux bounds remain; no kernel or handshake-cap increase.
5. Existing packet `limit_denied` and six admission counters now survive native stats
   → Java projection → ring/incident snapshot → ordinary export. Missing legacy data
   stays missing, invalid numeric values are rejected and late cleanup does not replace
   first failure. No extra stats reader, private destination or identity export.

Only16 client files and6 shared gateway files change. UI60-4, async writer/queue64,
ReliableStream/media, JNI interface, broker ownership/authentication, security policy,
startup120s, Java retry/recovery and storage stay unchanged. The native library and
gateway must be rebuilt because their mux/admission code changes; this is not a
UI-only or diagnostic-only candidate. Existing fast-retransmit remains present.

## Local verification and honest failed attempts

Fixed test batches, not retry-until-pass; serial/GOMAXPROCS1, offline caches, CPU50%,
start below75°C and thermal stop85°C. No emulator or heavy concurrent workloads.
Observed peak82°C in the initial tests,79°C in the follow-up,71°C in the final direct
JVM check and83°C during the372.405-second full build; no thermal cutoff was reached.

| Surface | Recorded coverage |
|---|---|
| Client mux/wholedevice/sessiondiag | Normal×2, race×1; FIFO, cancellation, overflow, shared open deadline, reserved control, unconfigured peer, ordinary flow/DNS/service/cleanup and first-cause projection |
| Browser-shaped Family TLS/HTTPS | Normal×2, race×1;33rd HTTPS succeeds with32 held;64 data+control plus queued HTTPS released by closing one data flow; search remains usable; DNS;40 exact-body sequential requests per three close modes |
| Actual broker lease/auth protocol | Follow-up normal×2, race×1; real disposable Family credentials; renewal with its32 configured data slots full, no displaced data; replay/security/revocation/legacy checks |
| Independently retained gateway derivative | Normal×1, race×1 of selected mux/admission/sessiondiag cases; no executable run against production |
| Patched packet/gVisor engine | Normal×1, race×1;72 simultaneous established echo sockets plus DNS while open, UDP fail-closed and cleanup; fake DataPlane, not72 real mux data streams |
| Java pure projection/export |12 targeted tests; full Gradle suite/build recorded below |

The HTTPS fixture uses actual local TLS/HTTP1.1 and byte-exact bodies, not browser
automation, real sites, mobile data or provider media. DNS responses are synthetic,
not public-resolver availability. Retained-memory assertions cover mux buffers, not
total Android RSS. The full server dependency versions remain a separate artifact gate.

The first batch is retained intact. Its real lease tests were **SKIPPED** because the
disposable profile environment was absent; exit0 was not real renewal coverage.
The follow-up generated fresh local-only ProductStore fixtures and explicitly rejects
skips. No production credential, identity or provider was used.

The first packet test failed DNS immediately after mass-closing72 flows through its
64-entry fixture channel with a100ms read deadline. The test now checks DNS while the
72 sockets remain established, then closes them. Normal and race pass in that order.
No production timeout changed. Post-mass-close packet loss was not instrumented or
proven; the failed receipt is not relabeled as a product DNS fix.

The first direct JVM compile caught a missing `throws` declaration for checked export
I/O exceptions in the new test. Only that test declaration was corrected; the focused
compile and12 tests then passed. Both failed logs/hashes remain in the research bundle.

Origin-close HTTPS tests still record server protocol-errors0/1 in the two normal
runs and28 in race, with exact bodies and cleanup passing; client protocol-errors0.
These are not the owner's10 client errors and are not silently declared harmless or
fixed. Other historical failing suites were not rerun or promoted to green.

## Build, rollout and limitations

Full unsigned assemble,100 selected JVM checks in13 suites (no failures/errors/skips),
ARM64 native build, JNI Java header/C compile and independent Linux gateway build PASS.
APK56,002,273bytes. Embedded native/provenance, unsigned signature state,16KiB ZIP
alignment, API31/ARM64/non-debuggable manifest and unchanged permissions are checked.
Only `libfc_restricted.so` changes among packaged native libraries. The native Xray
patch asset hash matches the new manifest. Gateway Go1.26.1/CGO1/dependencies/build
flags remain as recorded; no research/fault/supervisor tag added. No binary is run
against production. The existing deep Git-alternates lookup printed warnings but
returned the retained base tree; source/artifact inventory checks passed independently.
The post-build exact-delta check also detected Gradle rewriting its generated HTML
problem report in the copied source tree. The new report was retained in private build
output and the prior generated copy restored; the unchanged16-file product delta and
sealed cumulative inventory were then verified again. No source guard was disabled.

The32-slot browser failure mechanism has a tested local fix. It is not yet proved
that every owner failed site was refused at that cap. The10-minute cutoff→lease
starvation causal binding remains **NOT_PROVEN**. Reserved control removes the
locally reproduced saturation path, not every possible session/renewal failure.
Capacity is finite:64 long-held data sockets may still leave queued opens to exhaust
their40s budget. This is not a claim of higher measured phone download bandwidth.

Old peers still enforce their old lower limit; no mixed-pair64-stream acceptance or
capacity negotiation is claimed. A later coordinated private pair rollout requires
fresh material/runtime readiness and preserved exact backups; do not install only
one half and claim the new resource boundary. No credential maintenance, process
restart or reconnect is automatically authorized by this local checkpoint.

No signing/install/deploy/SSH/ADB/CONNECT/export/restart/rollback/maintenance or extra
native poller occurred: each count0. Phone state is not freshly queried; last saved
observation was VPN OFF. Gateway was not contacted or altered by this task.
Public download/catalog/invitation versions and release remain unchanged.
Owner browsing/call continuity, field, historical causality, chat handoff and
supervisor acceptance remain open. Prior exact-pair PASS_BOUNDED records are unchanged.

Sources/tests/runners and safe logs:
[research bundle](../../research/browser-admission-fix-20261017/README.md).
Machine-readable [safe receipt](evidence/2026-10-17-browser-admission-fix-1.json)
contains final identities, individual exits and thermal bounds; raw APK/native/server
binaries, disposable profiles and owner exports remain private.
