# Android118 — bounded signaling diagnosis, 5 November 2026

## Scope and current boundary

Owner selected the next step after the failed117 sustained observation. This packages
the finite additive signaling-read classification from source234af08 into immutable
Android0.1.18-beta118/code118, package`com.familyconnect.app.friends`, Android8.1+/API27
ARM64. Existing beta117 signed bytes must never be replaced with changed binaries.
No transport/recovery/auth/deadline or wire change; no gateway/policy/ordinary-service
change. Both NL gateways retain common70e6c0fc. This is diagnosis, not a proven fix.

Current state at5 November00:06UTC:118 qualified, signed and installed over117 only on
the owner phone. Exact installed bytes, UID/first-install and consented Support ID are
verified. Controlled118/NL2 traffic fails one of8 wire DNS cases, while2/2 Android HTTPS
pass and the same tunnel remains connected. Temporary probe is removed; no sustained
acceptance. Public/invitation/updater stays113/catalog7, Linux/Windows
unchanged. Existing public download links/checksums stay intact;118 has no public URL.

## Evidence and completion gates

The previous[117 receipt](2026-11-04-mesh-protected-ice-route.md#failed-sustained-observation-and-additive-signaling-diagnosis)
records a20-minute observation interrupted after91.621s, first client WebSocket
READ_ERROR/SIGNAL_READ, no preceding ICE failure, and normal automatic recovery35.694s.
Nearby network transitions do not establish the socket's underlay or exact read cause.
The added fields preserve legacy recovery behavior and redact raw remote/error text.
Prior source checks:57 default-production trace/report race passes,140 selected media/
signaling race passes (including repeated subtests),39 Android JVM tests. These are not
substitutes for the exact118 platform/artifact/runtime gates below.

1. Push a versioned source checkpoint and verify the remote SHA; select the Client builds
   run bound to that exact SHA. Do not sign artifacts from234af08's same-version117 build.
2. Require accepted platform CI including API27/API35; download ARM64/debug/runtime/UI
   artifacts and verify run/source, archive digests, native provenance, package/version/
   ABI/API/16K alignment, corresponding source/licenses and UI images. Retain any failure
   or retry. Separate inherited phase0/Linux-control failures are not whole-CI green.
3. Verify synthetic117→118 Java-storage retention without product keys/data. Sign only
   accepted ARM64 bytes using the unchanged offline signer. Do not publish a catalog/tag.
4. Guarded owner in-place117→118 installation must preserve signer, UID, first-install
   and existing identity; read back exact installed bytes. No uninstall, data reset,
   reenrollment, active-owner eviction or blind failed-install retry.
5. Read diagnostic/traffic state only with current app consent. An expired grant is not
   permission to bypass it. A new controlled same-session observation must distinguish
   the read-error class and separate actual recovery from uninterrupted operation.

The production/default-tag source gate is distinct from optional`fc_owner_diagnostic`:
the latter has an existing missing Snapshot.FirstClose build failure, reproduced with
the original trace source. It is retained, not silently repaired or used for delivery.
The prior dirty-tree Friends provenance rejection is also retained; the clean exact
source build must satisfy that guard normally.

## First qualification and correction

Sourcea03bdeca639153b2a8bcea93db67dbcd3f0b9849 is pushed and remote-SHA verified.
Client builds41931735646 attempt1 fails at Restricted diagnostic and readiness contracts,
before native ARM64 packaging or signing. Its preceding carrier race and204 diagnostic/
readiness tests pass. Local reproduction of the subsequent release selection gives
57 passes, one Windows deselection and two failures: the candidate contract still expects
117 and the strict reviewed-handler pins still expect the pre-classification diagnostics.
These expectations are updated explicitly to118 and the two reviewed diagnostic hashes;
the immutable historical reference and every unrelated handler pin remain intact.
A contract verifies identical native/Java finite classes and the unchanged recovery hash.
Contract-only edits now trigger/select Android CI; no release test is removed or disabled.
Fresh exact-source platform qualification is required after that failure; its completed
result is recorded below and the failed run is retained.
The corrected local CI selections pass204 diagnostic/readiness tests and60 release
tests, with the same one Windows deselection as the workflow. No diagnostic test is
deselected in the final first selection. Whitespace and new local document links pass.

Separately, disposable API27 x86_64 Java-storage117→118 retention passes: same UID,
distinct processes, identity/journal/outbox and atomic-interruption recovery. Candidate
fixture SHA256`29ac3ac4b4442c5472e50fbfbdb19509cac8ef10407949bdfa7fa12c143c1b76`.
The fixture uses sourcea03bdec, the unchanged storage-test source, existing local generated
inputs and fresh disposable signing keys; it is not the release ARM64 payload. No product
key, private phone data or physical phone mutation is involved. The owned emulator is
stopped in cleanup. Evidence remains under`state-client-build/android118-signaling-20261105/`.

The full documentation checker reports746 files/4638 links and two existing missing
anchors: the dirty STATUS historical27 October health link and the23 October desktop
phase22 link from the24 October source report. New118 links and whitespace are checked
separately; no all-docs PASS is claimed and unrelated historical content is not changed.
Final targeted documentation validation checks6 changed files/359 links and retains only
the existing dirty STATUS27 October anchor failure; new118 links and whitespace pass.

## Exact-source qualification and owner delivery

Source13e0b37eb3feba53fae7e281f4e12d49a840e85c is pushed and remote-SHA verified.
Client builds41933207129 attempt1 and readiness wire41933207233 pass. Separate
phase0 41933207131 and Linux-control41933207100 fail; this is not whole-CI green.
Four downloaded artifact archives match GitHub digests, source and run metadata:

| Artifact | ID | SHA256 |
| --- | --- | --- |
| ARM64 | 13375205947 | `60077e3761ea18feb9b46cb98a1f953949e4e32ad0abe53bc60deee76ef8e86b` |
| Debug/JVM | 13374806902 | `093c10f659c81319b81dc97db0257821c025f4c95acb5ca41bd01ef4c9421012` |
| Runtime | 13374976425 | `8dad28d9264585a3f43b3e010c2be01727223fbd0b65f58aa7cfe516094df2ea` |
| UI | 13374986440 | `b09f87bd241d022a6645b7c8e29d3002b57bf869ad8e70857a7859f13dd3aa44` |

Unsigned118 APK is50,263,893 bytes, SHA256
`9526990b34c7fbdd9129be90baf1aa446fd1b121bb28173d4e25cfa8236e72f4`.
Package/version/minSDK27/target35/ARM64 identity, production/default native provenance,
12 ELF libraries, ZIP/ELF16K alignment and corresponding source/licenses pass. No owner
diagnostic tag or ProvisioningWindow payload. JVM422 debug+417 Friends=839 pass, no skips.
Runtime API35 debug28 pass/25 skip and Friends19/4; API27 debug27/26 and Friends18/5.
Required lifecycle, picker/language/radio/legacy-voice cases pass; skips remain explicit.
Eight selected new-run UI images are visually reviewed, including RU/EN large text,
three nodes, green/orange load, failed-state controls and Codec2 compatibility. The CPU
row's fixed280x56 fixture crops its bottom identically to117; identical bytes are verified,
not represented as a new118 fix or an unqualified all-layout PASS.

The disposable storage fixture remains sourceda03bdec; a separate qualification mapping
verifies zero differences through13e0b37 in clients/android, carrier, messenger and
tests/vectors. It does not relabel the original fixture receipt or substitute for ARM64 CI.
Offline signing uses the existing certificate
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`, without key export.
Signed118 is50,285,984 bytes, SHA256
`b7b0be92456f522f81d87c71c401c2622d2f823178510b28510a6fb8d5c69fca`;
the unsigned payload is unchanged and signature/alignment checks pass.
Local delivery file:`state-client-build/android118-signaling-20261105/android118-delivery/FamilyConnect-Test-0.1.18-beta118.apk`.
Guarded117→118 install verifies prior117 hash and reads back exact118 installed bytes,
same UID and first-install. Current authorized USB support independently confirms118
and the unchanged Support ID. No uninstall, product-data clear, reenrollment, gateway
mutation, public tag/catalog or public installer change. Private evidence remains ignored.

## Controlled118 field result: paired-DNS timeout, no tunnel loss observed

Current app USB grant is accepted; no consent bypass. One ordinary Connect reaches
CONNECTED/native2/NONE at00:03:10UTC. Fresh118 readiness validates both current gateway
bindings; exact authenticated session appears only on NL2 with authorization/family-TLS/
gateway establishment. Read-only running-process hashes on both NL nodes remain
70e6c0fc with PIDs1293513/1184264 and NRestarts0. No gateway, policy or network mutation.

The20-minute ordinary-UID observation stops after26.081s during its first DNS round.
Seven of8 wire cases receive answers; the fourth UDP_PAIRED case reports
SocketTimeoutException after8011ms. Both Android hostname HTTPS checks return200;
network binding is unchanged. Egress round is NOT_RUN; zero complete traffic rounds,
no20-minute or30–60-minute acceptance. The test helper raises KeyError because an error
record has no result field: this is not an application crash and does not erase the
underlying timeout. Only future local failure classification changes to a guarded field
lookup; no timeout, product code or acceptance criterion changes, and this run is not retried.

Readbacks00:04:45 and00:06:49UTC are still118 CONNECTED/native2/NONE on the same session,
same Support ID and no temporary probe. Signaling/ICE failure remains NONE; no new read-error
class to explain117's WebSocket close. Protocol errors13 (unknown_stream9/dns_unmatched4),
retransmissions/recovery_timeouts9 and zero actual mux violations are retained; counters
alone do not prove the paired-DNS root cause. After-probe gateway readback remains on
the exact NL2 session, same process/hash, no observed close. No manual recovery/reconnect
or injected network loss. Raw evidence stays under the ignored field118 directory.

Next evidence gate is exact paired-DNS client/gateway correlation and a deterministic
reproduction before correction. Do not claim DNS timeouts and117's WebSocket close share
a cause without evidence. No new public build, arbitrary retry/deadline increase or
unrelated queued task is authorized by this checkpoint.

## Remaining stability work and rollback

There is no promised number of versions: identifying/reproducing/correcting the actual
failure, controlled slow/lossy checks on both NL nodes and sustained30–60-minute checks
are separate acceptance gates. A diagnostic build or an automatic reconnect does not
complete them. Do not start an unrelated queued task or public rollout from this checkpoint.

Source can be reverted normally without changing installed runtime. Preserve117's signed
artifact and both gateway rollback custodians documented in the unified116 report. After
installation, an owner rollback requires an accepted higher-version compatible package
with the same signer, never uninstall/data clearing or replacement of a published binary.
Keep all keys, profiles, support/session IDs and raw device/server evidence local/ignored.
