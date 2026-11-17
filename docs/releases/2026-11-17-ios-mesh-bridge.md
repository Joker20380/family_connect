# 17 November2026 — IOS-MESH-BRIDGE-1

## Technical acceptance — sourcefc08a50e

Exact source **fc08a50ecec45ea94e9ab27b1a9cfe28d507dc5d**:
[macOS push43991766964](https://github.com/Joker20380/family_connect/actions/runs/43991766964)
SUCCESS; separate exact-head [PR43991774552](https://github.com/Joker20380/family_connect/actions/runs/43991774552)
also SUCCESS. [PR41](https://github.com/Joker20380/family_connect/pull/41) retains author
self-review (not independent approval), final-head applicable CI and integration
receipt. This report identifies tested artifacts, not a public release or a claim
that an in-progress later documentation head has passed.

| Gate | Result on fc08a50e |
| --- | --- |
| unsigned iPhone | PASS: app + embedded Packet Tunnel extension, iphoneos/arm64, Mach-O IOS, minimum16.0/SDK18.5 |
| separate simulator | PASS: app + extension, arm64, Mach-O IOSSIMULATOR; iPhone16/iOS18.5 runtime |
| real native link/call | PASS: C exports + existing wholedevice/tcpforward/Family TLS/bootstrap/Telemost/Xray symbols in both executables; Swift/C/Go packet calls execute in simulator app |
| Go isolated boundary | PASS:9 Darwin tests ×3 with race detector; original packet regressions tagged and untagged |
| Swift isolated boundary | PASS:4 check groups, copy/family/queue/cancel/recreate, async real-gVisor DNS, late configuration callback, write failure;0 live handles |
| socket underlay adaptation | PASS: actual Darwin IP_BOUND_IF set/get and invalid-interface/fd rejection; routing through installed extension NOT_RUN |
| real TUN / VPN / Telemost / whitelist | NOT_RUN; packet-flow mock and synthetic DNS are explicitly isolated |
| production / public artifacts | NO CHANGE: public beta126/catalog9; no server, profile, identity, release-signing or deployment actions |

Runner macOS15.8.2/arm64 image20261104.0514.1, Xcode16.4/16F6,
Swift6.1.2, clang17.0.0, Python3.15.2, Go1.26.1. Laboratory app0.0.1/build1.
Retained builds are unsigned; only a temporary simulator copy receives local
ad-hoc signing, with no Apple account/certificate/provisioning. All208 per-file
hashes in the downloaded artifact match; screenshot shows actual PASS/zero handles.

[Artifact14288332488](https://github.com/Joker20380/family_connect/actions/runs/43991766964/artifacts/14288332488)
ZIP SHA256 `5164ebc2d5dcaa235ba8d82bcbf1858673036037e653da91f00ef93cc0ef746a`.
[Sanitized verification receipt](evidence/2026-11-17-ios-fc08a50e.json) preserves
toolchain, both platform/ABI targets, simulator result, exact31-module/408-package
closure and selected binary/archive hashes. Full notices, modified dependency
sources, Family sources, both patches, commands, link maps, symbols and logs are
in the30-day CI artifact. Procedural reproducibility, not bitwise determinism.

Unchanged Android JNI/desktop runtime uses the original packet engine. The only
shared-file edit is an isolated positive DNS test budget:3s, matching its TCP
fixture; rejected UDP retains100ms and all assertions remain. Successful macOS
DNS reads were258.666µs tagged and430.875µs untagged, query count1. No claim is made
that earlier timeouts' scheduler/root cause was proven. Prior failures remain below.

Remaining device gate: development enrollment/capabilities/provisioning and consented
iPhone; reviewed secure device-only configuration/keychain handoff plus disposable
authorized Family identity/admission; extension memory/lifecycle, scoped underlay
anti-recursion and path changes; IPv4 DNS/TCP, IPv6/UDP containment, trust failures;
then real Telemost/whitelist trials. No unattended follow-on task is selected.
IPv6-only/DNS64/NAT64 is unsupported. `includeAllNetworks`/`enforceRoutes` are rejected
pending a different qualified routing strategy. A scoped bind is not leak-proof
VPN evidence. [Detailed public API rationale and checklist](../../clients/ios/README.md#next-signed-iphone-prerequisites).

Rollout/rollback: no installation/distribution here; artifacts are technical-only.
Revert the source change/disable its laboratory workflow to roll it back. Existing
public/installed Android and desktop versions and all gateway policies stay intact.

## Historical source checkpoint — qualification was pending

Owner explicitly selected deferred iOS preparation. Separate worktree/branch
`feature/ios-mesh-packet-bridge-20261117` starts from remote main86663dfe; dirty
original main and other worktrees preserved. PR40 exact
3539ebe476545d700fc696bbdd4573bedd4e1a5f has no blocking threads; author's review
records accepted00:05:38 readback. Push43984661863/PR43984770165 phase0 still ran
at entry; no unrelated SHA PASS is substituted. No recovery/observer/host actions.

| Gate | Result |
| --- | --- |
| unsigned iphoneos/arm64 | PENDING macOS CI |
| separate iOS Simulator/arm64 | PENDING macOS CI |
| linked MESH / Swift-C-Go invocation | Implemented; PENDING CI |
| isolated packet lifecycle | Linux7 Go tests ×3 race PASS; existing packet regression PASS |
| Swift asynchronous lifecycle | Implemented; PENDING simulator |
| underlay | IPv4 interface bind/readback implemented; device routing NOT_RUN |
| real TUN / VPN / Telemost / whitelist | NOT_RUN |
| production / catalog / signing | NO CHANGE; public126/catalog9 retained |

Existing MESH packet adapter/wholedevice reused, no JNI copy or transport change.
Live chain preserves signed bootstrap/admission, Family TLS, ReliableStream,
mux/DNS and Telemost VP8/RTP. Fixture DNS does not claim that live chain executed.
An endpoint-only Xray build tag excludes unused platform TUN/dispatcher and its
GPL sing dependency. Actual iOS closure must pass exclusion and notices/source
packaging gates. Android/desktop behavior/source remain unchanged.

Initial saturation test expected ErrNoBufferSpace; pinned gVisor's public
WritePackets returns a short count/nil on full. Corrected test asserts exact zero
admission and full drain, without increasing limits or relaxing waits.

Toolchain: Go1.26.1, Xcode16.4/16F6, iOS18.5 SDKs, macos-15 arm64, minimum iOS16,
laboratory app0.0.1/build1. Exact SHA/host image belong in CI manifest. Procedure
is reproducible; bitwise deterministic binaries are not claimed.
[Build, ABI, underlay and device prerequisites](../../clients/ios/README.md).

Rollback: source revert/disable laboratory workflow. No deployed/installed client,
public artifact/catalog or server policy changes. Signed-device stage remains next,
not selected automatically; no user VPN readiness claim.

## Author review follow-up (not independent approval)

Checkpoint5d99f239 is pushed and remote-verified; draft PR41 is open. Clean-checkout
Linux build procedure also passes tagged bridge races and tagged/untagged original
packet regression. Review adds explicit gVisor worker join and releases late-flow/
path-monitor ownership, plus ad-hoc signing of a temporary simulator runtime copy
without signing/modifying the retained unsigned artifacts. Both patch hashes and
post-simulator artifact hashes are retained. macOS qualification remains pending.

## PR40 integrated

Exact head3539ebe476545d700fc696bbdd4573bedd4e1a5f: push43984661863 and
PR43984770165 phase0 completed SUCCESS, review-triggered panel43984863961 SKIPPED
(not an applicable execution). No blocking review threads. Ordinary merge
3468f828c793079a839e3306b5fc101f7c6155f3 is remote-main verified with the same tree
as accepted PR40. No rerun or fresh restoration/readback was performed. The
00:05:38 author-review receipt remains the supplied operational acceptance boundary.
The iOS branch incorporates this main by ordinary merge, preserving both top-level
documentation entries; no dirty original worktree, published commit or history is rewritten.

## First macOS attempts — retained failures

Source5d99f239: push43989085484 passes the new bridge race checks and both existing
packet regressions, then builds the real iphoneos/arm64 Go c-archive. Xcode project
generation fails because helper argument `name` collides with a PBX `name` field.
The helper is corrected and two local generator regression tests are added.
PR43989149491 separately passes new bridge checks but fails the original packet
test's100ms DNS read deadline. This is not diagnosed as infrastructure, hidden by
the successful push test or retried unchanged. Original tests/timeouts remain.
Neither attempt built an app/extension or ran simulator checks; no overall PASS.
Artifacts14287780072 and14286014603 retain both logs.

Further author-review checks require the tagged gVisor join (not optional), add
deterministic cancellation while a reader waits without packets, retain Swift's
terminal error after native handle release, and reject unqualified enforced-route
configurations. New Linux boundary suite8 tests ×3 race PASS. Swift lifecycle
results still require the exact candidate simulator run. Action SHAs are pinned
to the first macOS run's resolved versions; Swift/clang/Python enter the manifest.

## First complete iOS acceptance / repeated macOS fixture deadline

Sourcec125c0ea PR43990153357 SUCCESS: both unsigned app/extension targets, real
linked MESH symbols/platforms and simulator Swift/C/Go checks execute. This success
is limited to that SHA, not substituted for the newer9f242c6a candidate.
On9f242c6a push43990930518 the new bridge races and tagged original packet test
pass; the untagged original test fails the same100ms positive DNS read. Together
with the earlier PR failure this establishes a repeatable test-budget sensitivity,
not its scheduling/root-cause attribution or a network failure diagnosis.

The old fixture used the same100ms deadline for successful DNS and expected-denied
UDP. Its positive DNS wait now uses the existing TCP fixture's bounded3s budget;
negative unsupported-UDP remains100ms and all response/counter/cleanup assertions
remain. Query writes are checked, and exact elapsed time/budget/query count/error
are logged for both tagged and untagged runs. This changes only an isolated test,
not Android/desktop transport deadlines or wire/runtime behavior. Original failures
are retained (artifact14287582193); no unchanged rerun to obtain green is requested.
