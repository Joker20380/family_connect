# Android118 — bounded signaling diagnosis, 5 November 2026

## Scope and current boundary

Owner selected the next step after the failed117 sustained observation. This packages
the finite additive signaling-read classification from source234af08 into immutable
Android0.1.18-beta118/code118, package`com.familyconnect.app.friends`, Android8.1+/API27
ARM64. Existing beta117 signed bytes must never be replaced with changed binaries.
No transport/recovery/auth/deadline or wire change; no gateway/policy/ordinary-service
change. Both NL gateways retain common70e6c0fc. This is diagnosis, not a proven fix.

Current state:118 source candidate only. Platform build/artifact/UI qualification,
signing, installation and physical testing are pending. Owner remains signed117
SHA256`a2f637879787eec0db74efbea271f1242ee37ce9c1069618816e4a0ba4bf8802`;
public/invitation/updater stays113/catalog7, Linux/Windows unchanged. No118 public link
or checksum is invented before an artifact exists; existing download links stay intact.

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
Fresh exact-source platform qualification is still required; the failed run is retained.
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
