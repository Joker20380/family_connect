# TRANSPORT-SPEED-CUTOVER-CANDIDATE-1 — local validation and combined candidate

Subsequent owner-authorized [signing, installation and gateway rollout](2026-10-16-transport-speed-cutover-owner-install-1.md)
are recorded separately. The original local-checkpoint outcomes/counts below are retained.

Continuation from review `ce16c96d8b049a3a42b2d452f72882127c996f76`.
The owner requests the speed and restoration changes together, followed by installation.
This checkpoint separates implementation/build validation from phone/server rollout.
No new live CONNECT, credential maintenance, observer activation or public release.

## Exact inputs and product boundary

- Last verified installed UI60-4 signed APK:
  `1bf56c381e76913d77c4dc518961020d82d2bfec33da69777a504b7569be15ef`.
- Its cumulative source inventory:
  `e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce`.
- Independent Java restoration candidate inventory:
  `ea9312d013aac02a190a06b8ad9091e1245ef63a994db6618054dde27739c0d4`.
  [Exact behavior, prior tests and limitations](2026-10-16-cutover-recovery-local-1.md).
- Independent fast-retransmit candidate inventory:
  `bb23c58fcfe27bcb817141167eb30b9ea638145dc06c19c24de8ed4831c9bcc0`.
  [Engine delta and previous model/adapter checks](2026-10-16-reliable-fast-recovery-local-1.md).
- Retained gateway executable:
  `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`;
  carrier inventory `722746429539a1307d693ce6fcc83579a842d3f1c549a626a36676a6d665c42e`.
  These are retained identities, not a fresh live readback.

The combined client adds the already tested engine change to the recovery source,
plus its two existing Go test files and a distinct private versionName. The UI60-4
layout, native/JNI source contract, async writer, queue64, ownership/handoff guards,
early bootstrap correlation, auth/revocation/floors and configured deadlines stay
unchanged. Native **bytes do change** because the Go transport engine is compiled in.
The isolated gateway derivative changes only `reliablestream/engine.go`; it is not
built from Android's carrier tree and does not inherit Android-only diagnostics.

Retry behavior is deliberately not described as entirely unchanged: one early
head retransmission consumes the existing retry budget, and Java restoration gains
the narrow bounded retry/refresh handling documented in the recovery report.
There is no new pacing/window/queue tuning or protocol negotiation change.

## Full local path and genuine mixed peers

The fixture runs separate compiled peer processes with real Pion VP8/RTP/DTLS,
production ReliableStream, mutually authenticated Family TLS1.3 and production TCP
mux. Temporary synthetic CA/leaf/CRL material is generated locally and removed with
the test temporary directory. No provider OAuth, real rooms, identities or grants.

Each case echoes two concurrent512KiB TCP streams byte-for-byte, while completing
eight small interactive echoes and eight DNS exchanges through that mux. The server
DNS upstream is a **synthetic adapter**, not Internet resolver reachability. The test
also rejects a second mux owner on the already claimed Family session. Both peers
must record real RTP writes/receives and no unexpected reliable terminal before stop.

Scenarios: clean; one first-large FRS1 DATA frame dropped in each direction; one such
frame delayed400ms in each direction. Faults are applied before VP8 encoding, not by
modifying production queues or injecting on live networks. Delay owns the fixture
lifetime, rather than extending the production per-send context.

Four genuine binary combinations are used: old/old, old/new, new/old and new/new.
The first matrix uses UI60-4-derived peers, fixed normal2/race1. A second matrix uses
the exact retained gateway source and its engine-only derivative as the server,
fixed normal1/race1. This distinction matters: gateway and client Family receive
observations and signaling diagnostics differ. No claim of exact gateway binding
is based only on the first matrix. Test-only adapters never enter product artifacts.

**Results:36/36 client-derived cases and24/24 exact gateway-source cases PASS.**
Both normal and race executables pass; no reported data race. Every successful case
verifies1MiB echoed bulk plus interactive bytes and eight DNS replies. No extra
connect/session is substituted after a failed case.

Normal exact gateway-source supplement (one sample/cell; total exchange duration):

| Client / gateway engine | Clean | One loss each direction |400ms reordering each direction |
|---|---:|---:|---:|
| old / old |2179ms |3976ms |2682ms |
| old / new |2208ms |3312ms |2601ms |
| new / old |2255ms |3353ms |2588ms |
| new / new |2085ms |2436ms |2434ms |

Under those specific two losses, new/new finishes1540ms earlier (about39% less time),
not a guarantee of39% more Internet bandwidth. The selected DATA retry moves from
1062/1091ms to256/292ms. Mixed peers accelerate only the updated sender. In the
400ms-reorder cells each updated sender spends one redundant retry; the old sender
spends none. No-loss cells have zero retransmissions. CPU-capped race durations are
retained in receipts but excluded from speed claims.

Normal wall times describe a CPU-capped local synthetic exchange, **not phone
download capacity**. Race wall times are correctness evidence only. Clean-path speed
is not materially improved; selective recovery helps only when its SACK conditions
hold. Tail loss and ACK starvation remain on ordinary recovery.400ms reordering can
produce a redundant early retry, and the receiver filters its duplicate. This cost
is retained rather than relabelled as proven packet loss.

### Validation history

The first local batch compiled both peers, then failed the baseline reordering
fixture in both scheduled normal repetitions. Four clean/loss subcases passed;
two reordering subcases failed during final fault readback. The fixture retained
the per-call SendContext after returning, although the real writer immediately
cancels that context. Traffic completed via ordinary retransmission, but delayed
delivery recorded `context canceled`. No candidate product failure or PASS is
inferred from that run. Its sources/log hashes/receipts remain retained.

Only the fixture context ownership was corrected; product files stayed unchanged.
The next fixed matrix and the exact gateway supplement are separate receipts, not
retry-until-pass. No previous transport/PKI/burst suites are recounted or rerun here.

## Build and rollout boundaries

Private versionName: `0.1.18-research84-ui60-4-speed-recovery1`, versionCode84.
Keep API31/ARM64 and the normal non-debuggable provisioning variant. No new signer,
permission, identity, storage migration or versionCode workaround. The actual new
native manifest and cumulative source guard must agree with the packaged library.
The other native libraries remain the existing accepted payloads.

Installation is a subsequent controlled step, not inferred from an APK file. Reuse
the tested unsigned bytes, verify the actual current phone package/signer/version,
retain its exact signed APK, confirm VPN OFF, then use the existing private signing
workflow and ordinary replace-install. Do not read private identity/database, clear
data or use downgrade bypass. Same code84 permits a compatible previous-key return
in principle, but is not evidence that a rollback has actually happened.

Fast retransmit acts on the **sender**. Updating only Android cannot install the new
sender behavior in the existing gateway's downlink. Mixed-peer tests demonstrate
compatibility, not both-direction optimization from a client-only update. A server
rollout requires fresh operational readiness, the accepted service coordination and
an explicitly covered outage; do not run arbitrary restarts or credential repair.
Retain the exact a5372571 gateway bytes as the product return target, never restore
old credentials/floors/current4h state as a rollback.

## Limits that remain open

- No on-device speed comparison or live recovery-after-maintenance acceptance yet.
- The specific historical call interruption preceded client exhaustion and coincided
  with a scheduled gateway stop. This does not establish a universal ten-minute timer.
- Faster frame repair cannot prevent a maintenance outage or guarantee call survival.
- The restoration change can delay recovery if the control endpoint is unavailable
  even while old cached runtime material would still work. It intentionally does not
  bypass auth, expiry, revocation or admission, or reopen unknown HELLO waits.
- Local Pion is not the provider SFU/relay/mobile network, bootstrap admission or TUN.
  No new field trial, chat handoff, supervisor acceptance, historical causal binding
  or public-release claim follows. Previous bounded owner reconnect PASS remains
  attached to its original exact APK/gateway episode.

## Final local artifacts and verification

**RESULT=LOCAL_COMBINED_CANDIDATE_READY; INSTALLATION/DEPLOYMENT=NOT_STARTED.**

| Identity | SHA256 |
|---|---|
| Client cumulative source inventory,57 retained delta entries | `211b127d545af5c129acc93bf0ff78cac3af93707aad8def27bb6da830e2ae86` |
| Combined patch relative to UI60-4 | `89b0cdd752788e860a44d9d62c4e4c6cb961bc3f56643c0e33a2a8ada0f2c09c` |
| New normal ARM64 native | `f25124ba1c94a0c6f4258e8b67488e8febf9a1c9e88cb2073790564c3a1f4729` |
| New unsigned APK,55,992,676bytes | `2cf26421b67e536b5c178af7020cade9b499fec06822c82b713461cf534f5ac1` |
| Gateway carrier inventory | `3693f70552d27365a56eb9f625f8afe03c01f7e513acdc04cb31e107f52d837e` |
| New Linux/amd64 gateway executable,not executed | `5de40b9ce9c15aac85475df05c449bddf2ecfe61a1928fa3844b4a8446b33047` |

One native/Gradle/JNI/gateway build batch succeeds. Full assemble plus97/97 targeted
JVM tests (12 classes) pass, including14 restoration cases and normal bootstrap
projection/ring/export/UI checks. Existing Go model/race suites are not repeated:
the full-stack fixtures compile the exact same changed engine, and its hash is
checked again before native compilation. Full Gradle provenance/vital lint and
normal JNI Java-header/C-bridge checks pass. No transport test adapters are packaged.

Artifact readback verifies `com.familyconnect.app.friends`, code84, API31/target35,
ARM64, non-debuggable, unchanged permissions,16K ZIP alignment and unsigned status.
The new native/source manifests match the actual embedded library; exactly one of
12 shared libraries changes. The other11 remain byte-identical to UI60-4. Full source
boundary check/patch round-trip passes:11 changed files including3 test files and
the private versionName,2003 other compared files unchanged. Generated Android build
reports and Git metadata are excluded, not product sources. Existing native-stats
call-site count stays2 in the engine; no reader added by this task.

Gateway remains normal CGO1/Go1.26.1/Linux-amd64/v1 with no diagnostic/acceptance tags.
Dependency versions match the retained a5372571 executable. No gateway program is
executed by the build verification. Source/workflow identity warnings from the long
retained Git alternate chain are recorded; exact source guards still pass without
disabling them. Existing Gradle deprecation notes do not become a new product change.

Thermal receipts: corrected client matrix maximum71°C; exact gateway supplement67°C;
combined build79°C,412.381seconds. The initial failed fixture batch also peaks79°C.
All runs use50% of one CPU, no emulator; no85°C cutoff or unbounded waiting occurs.

Safe reproducibility material: [README/runners](../../research/transport-speed-cutover-20261016/README.md),
[full client-derived matrix](../../research/transport-speed-cutover-20261016/full-stack/results.json),
[exact gateway-source matrix](../../research/transport-speed-cutover-20261016/full-stack/gateway-results.json),
[build receipt](../../research/transport-speed-cutover-20261016/build-receipt.json),
[artifact checks](../../research/transport-speed-cutover-20261016/artifact-check.json),
[validation history](../../research/transport-speed-cutover-20261016/validation-history.json).

### Final state and action counts

- Product candidates:one combined client source,one normal native build,one unsigned
  APK/full Gradle build,one gateway build. Signed/new installed APK:NOT_CREATED.
- Completed new full-path cases:60 PASS; initial fixture batch4 PASS/2 FAIL retained
  separately. JVM:97 PASS. No multiplication of these counts into a blanket acceptance.
- SSH0; ADB0; signing0; installs0; controlled restarts0; credential changes0;
  owner CONNECT/export0; rollback0; emulator0; public binary publication0.
- Last verified phone remains UI60-4/APK1bf56c38; last verified working gateway is
  a5372571. Neither is queried or modified in this task; current VPN/PID/invocation
  are **NOT_CHECKED**, not assumed OFF or continuous from an old receipt.
- Owner readiness/VPN OFF and fresh operator readiness are the remaining rollout
  prerequisites. No further development or repeated full matrix is needed merely
  because the owner reconnects USB. Sign the already verified APK, not a rebuild.
