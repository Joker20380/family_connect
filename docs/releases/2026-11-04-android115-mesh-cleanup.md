# Android115 and gateway MESH cleanup delivery — 4 November 2026

## Selected scope and version state

Owner selects qualification and delivery of the lifecycle correction `f66b533`,
followed by paired physical reconnect/cleanup and ordinary-UID DNS/HTTPS checks.
Preserve active-session ownership, security deadlines, retry limits, identity/P1
policy, canonical source/runtime custody and the shared fleet renewal writer.
No unrelated development successor or general public rollout is selected.

Candidate source is Android0.1.18-beta115/code115, ARM64/minSDK27/targetSDK35.
It retains the114 DNS fix and adds ordered RESET/carrier cleanup. At this source
checkpoint115 is not built, signed, installed or public. Owner remains114;
public/invitation/updater113/catalog7, Linux0.2.11 and Windows0.2.16/catalog12 remain.
The [source diagnosis](2026-11-04-mesh-startup-cleanup.md) retains both physical
failures, all local regression results and the two reproduced baseline test failures.
Full historical-suite or sustained/low-speed acceptance is not implied.

Source metadata/payload/notification/orchestrator/field checks:59 PASS, one unrelated
Windows case deselected, zero skips. Documentation links and whitespace are checked
before the source push; hosted/artifact gates remain pending.

## Required qualification and delivery

1. Exact-source hosted Android/native, JVM, API27/API35 and downloaded source/license,
   ABI/16K/provenance checks before offline existing-key signing. Retain negative CI
   attempts; no replacement of an already signed or published version.
2. Project only the reviewed server lifecycle change onto the accepted private gateway
   capsule; do not deploy generic main. Verify the full predecessor inventory, reproduce
   its binary, run fixture/negative/ownership regressions with production tags, and
   reproduce the candidate binary under the original Go/CGO/build-tag contract.
3. Inspect both current nodes and shared maintenance custody. Perform guarded runtime
   delivery with exact predecessor/rollback pins; preserve profiles, DB, grants, units,
   timers and ordinary AWG/TCP services. Stop on custody or inventory mismatch.
4. Owner115 installation is in place only (`adb install -r`), with package/signer,
   version/UID/first-install and installed-byte readback. Never clear app data, reenroll,
   bypass Android input restrictions or bypass app USB-support consent.
5. Consented bounded disconnect/reconnect must pair actual client/gateway sessions and
   check remote cleanup plus DNS/normal-TLS hostname HTTPS and selected-node egress.
   CONNECTED alone is not acceptance. Public distribution remains113 until separately
   selected and verified; do not edit invitation/download links for an owner candidate.

## Rollback and remaining gates

Until delivery, no production rollback is needed. Keep immutable113/114 APKs and the
exact previous gateway binary/source/runtime references. For a runtime failure restore
only the recorded gateway executable under the same guarded custody; never restore
product DB, keys, profiles or signed floors. Android downgrade is not a data-preserving
rollback: retain data and issue a higher versionCode if a client repair is needed.
Each build/install/runtime result and remaining acceptance gate is appended here before
claiming completion. Private evidence and signing material stay outside Git and CI.

## Canonical source projection checkpoint

Fresh17:48UTC read-only inventory finds different live predecessors: NL1 has
`f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`, NL2 has
`566cbc96621c348e188aa50ffa54d6cf7bfce6274f8a214d3b0c227e743bb219`.
Both are active/boot-disabled with NRestarts0. All ordinary AWG/TCP services and RU
HTTP are active; the single RU renewal and directory timers are active. No runtime
mutation is issued by this inspection; paths/configuration are retained privately.

The new projection pins each complete predecessor independently and applies only
bootstrap/protocol.go, familysession/session.go and telemost/session.go lifecycle
changes. It imports two test-only files from exactf66b533 and adapts only the existing
head-loss fixture constructor; existing P1 policy,
diagnostic instrumentation, framing, performance behavior and canonical readers stay
unchanged on each node. Primary is not silently upgraded to the secondary baseline.
Both real inventories and three-file patch applications validate. The first dry patch
check rejected context absent from the older capsule; its unchanged diagnostic-context
line was removed from the patch, not added to production. No candidate was deployed.

Projection/source-boundary tests34 PASS/0 skips. Exact committed materialization,
baseline/candidate reproduction and production-tag runtime checks follow; this source
checkpoint alone does not authorize claiming installation or physical acceptance.

The first primary candidate builds reproducibly, but its Telemost tests fail to compile:
importing the entire newer head-loss fixture references a framing constant absent from
primary. Production code is not changed to satisfy that test. The corrected source
projection preserves the predecessor fixture and applies only the constructor seam;
the failed qualification and original source output remain retained, not deployed.
Corrected projection/source-boundary checks35 PASS/0 skips; runtime qualification repeats
from a new committed source output rather than modifying the failed private capsule.

## Exact gateway build qualification

Committed projection `3a2584b2d1d2c74359404c6fd28eb8d4c1511e95` preserves the respective
predecessors. Both baseline rebuilds equal the running executable hashes above. Each
candidate is built twice with Go1.26.1/linux-amd64/CGO1/`fc_perf_diagnostic`, trimpath and
buildvcs=false; each pair is byte-identical:

| Runtime | Candidate SHA256 |
| --- | --- |
| NL1 | `8769eadfa88850c41fc0d90a9dcc4749f2e949de36dfd95bb606c32c404b3c30` |
| NL2 | `5bcb32ea138325fbe3c788e2500d5054073ffc8df589e1cd1e83ed31c0946638` |

Fresh private capsules retain their exact source inventories; only the reviewed three
production members differ. Canonical reader/startup, entitlement/P1, crypto and directory
policy are not replaced with generic main. Production-tag race checks with disposable
Family fixtures and `FC_EXPECT_SEED_OBSERVABILITY=1`:

- Each candidate's lifecycle and negative-authentication selection passes5 repetitions:
  85 test/subtest passes, zero failures/skips per node. Includes active-owner preservation,
  disconnected seed-slot reuse, RESET cancellation/deadline and seven identity cases.
- Primary seven-package selection:654 passes,28 optional skips, zero failures. It excludes
  exactly the two inherited auth/busy assertion tests already reproduced on unchanged main.
- Secondary selection:729 passes,31 optional skips and one failure in the unchanged
  `TestLeaseLostResponseReconciliation` (`TCP OPEN: stream_limit`). Exact unchanged
  secondary predecessor reproduces4 failures/26 passes over30 attempts. No room-broker
  source is changed. Focused remaining broker selection:109 passes/20 optional skips.
- Failed attempts remain evidence, not an all-green full-suite claim or weakened gate.
  Live-provider/isolated-root/helper optional skips do not count as runtime acceptance.

Android115 source `86c5f9d46eba66ba981caa83936c37d1f86b14f9`, Client builds41880315713
attempt1 fails at emulator startup with zero instrumentation cases; the build/native/JVM
steps passed but signing is prohibited. One failed-job rerun is requested for the same
source. Readiness-wire41880315810 passes. Phase041880315853 and Linux control41880315891
fail in release-fixture/isolated-stack preparation; no full release-suite PASS is claimed.
At this checkpoint no candidate runtime, APK or public catalog has been installed.

## Gateway delivery and independent readback — 18:07UTC

Both candidates are staged separately and pass service-user `-help`, current executable/
locator/config pins, canonical-reader checks and credential headroom (>9300s) before
service mutation. The primary's additional legacy publisher contract entry is preserved;
only its matching current executable entry changes. The common RU writer is paused with
an eight-minute automatic-resume watchdog after a confirmed COMMITTED checkpoint and
no owned operation. Each node's operation lock is held through guarded runtime change.

- NL2 completes18:06:21UTC with the exact qualified `5bcb32ea…` candidate.
- NL1 completes18:06:28UTC with the exact qualified `8769eadf…` candidate.
- Each node has one controlled MESH stop/start, a newly published seed, canonical
  publisher validation, NRestarts0 and unchanged boot-disabled state. Locator pins,
  referencing node/snapshot config and the effective ExecStart are updated together.
  Profiles are byte-identical; old executables and exact private backups are retained.
- RU inspection is unchanged; coordinated post-upgrade evaluation returns NOOP.
  Both renewal/directory timers resume active and the temporary watchdog is stopped.
  No renewal transaction, authority/key issuance, DB migration or profile rollback occurs.
- Independent18:07 readback confirms both running executable hashes. All six ordinary
  AWG/TCP service PIDs/states and RU HTTP PID/state remain identical to the preflight;
  RU node/controller config bytes remain unchanged. No backend restart is hidden here.
- Normal-TLS HTTPS200 returns byte-identical public113/catalog7, SHA256
  `2283a89ffa05e6ad439858f111f7272993b4e46e652c9efa11b44158b9f01b30`.

Rollback was not used. For either node, retain its own predecessor binary and guarded
backups under `/var/lib/fc-profile-control/mesh-cleanup-3a2584b2-20261104/`; restore only
that node's recorded locator/config/ExecStart/executable under the common writer window
and node operation lock, then validate a fresh seed and resume the common writer. Do not
restore profile/DB state or replace primary with the secondary baseline.

This is gateway runtime delivery, not client/physical acceptance. Owner remains114;
Android115 is not yet qualified/signed/installed, and public/invitation/updater stay113.
Client CI attempt2 and then consented paired reconnect/DNS/HTTPS remain the selected gates.

## Android115 hosted and local artifact qualification

Exact source `86c5f9d46eba66ba981caa83936c37d1f86b14f9`, Client builds41880315713
attempt2/job126759635946 completes successfully. The first attempt's zero-case failure
is retained; successful retry is not evidence for its precise startup cause. Native
race/contracts, lint, JVM and both API35/API27 emulator gates pass. Download selection
pins the successful attempt's artifact IDs/timestamps; similarly named failed-attempt
artifacts are retained and are not substituted:

| Artifact | ID | Downloaded ZIP SHA256 |
| --- | --- | --- |
| ARM64 release/source | 13351263470 | `b86b98ff4efb9714c55e09fc3ee296b6c7c14d4fdf1ccacec5509fa695b03cf8` |
| Debug/JVM/runtime | 13351033714 | `5678c8012a15ad7778983b1efb0642aff75e4caed683d553e522bf67e087f2aa` |
| Runtime matrix | 13352002067 | `2c31d12ae0a92aaa4d321d7552c56a1145078e0a8cadb232e5625935d0e929d2` |
| UI screenshots | 13352611893 | `754f720b1d7648d43fc7efd6db2b4400099e5af4f560c8ff27a7a44546d8daf8` |

Unsigned ARM64 APK:50,260,905bytes, SHA256
`dce9c4c556ddcb5de7c616f1fe1b819e5133f8826b2f31d2748a088d7a21549c`.
Local verification confirms friends/code115/minSDK27/target35, nondebuggable/unsigned,
12 ARM64 native libraries, ZIP/ELF16K alignment, pinned corresponding source/licenses,
normal restricted build tags and exact source/tree/builder/native hashes.

JVM:418 debug +413 Friends passes, zero failures/skips. Runtime test cases:

| Android | Debug pass/skip | Friends pass/skip |
| --- | --- | --- |
| API35 | 28/25 | 19/4 |
| API27 | 27/26 | 18/5 |

No runtime failures. Required picker/language/native-radio/recording-capability cases
execute; conditional skips do not count as exercised features. Eight downloaded
screenshots are inspected: RU/EN names, enlarged lists, selected-row checkmark/tint,
green squares/orange87%, CPU-only fallback, failure controls and API27 Codec2 notice.
These are CI fixtures, not live load or physical Huawei evidence.

Separate disposable API27 storage114→115 upgrade passes with the same UID, distinct
processes, retained identity/journal/outbox and interrupted atomic-write recovery. It
uses a local x86_64 Java-storage fixture whose tracked Android/messenger/vector sources
equal the candidate, and a disposable signer; it is not a product-signed ARM64 runtime
or physical identity readback. The CI debug archive contains only the final ARM64
Friends APK, so it is not misrepresented as the x86_64 storage fixture. Initial local
fixture setup errors (reusing a one-line password file for two signer prompts, then
expecting an all-ABI Friends artifact) are retained and corrected without altering the
release APK or product source. The temporary emulator is stopped after acceptance.

Independent18:37UTC fleet readback matches18:07 runtime hashes/PIDs/config; common RU
timers remain active, ordinary services unchanged. No further deployment/restart occurs.
Phone ADB is authorized, but the provider rejects support access as disabled. At this
checkpoint signing waits for the protected local vault password dialog:115 is not signed,
installed or public. Owner114 and public113/catalog7 remain. Next: existing-key offline
signing, in-place owner readback, renewed app consent, then paired cleanup/reconnect and
ordinary-UID DNS/HTTPS. Sustained/low-speed stability and physical Huawei remain open.
