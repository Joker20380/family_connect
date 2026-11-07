# Bounded cold field delivery preparation — 7 November 2026

Status: local build/package preparation complete; unsigned/no-locator prebuild,
NOT a ready-to-install field APK, release-CI PASS or rollout.

## Accepted baseline

- F checkpoint `867ba7f7bc2869f41468c12495a2e929e4dc3f33`; application
  `9bf02724deacf1c5e4293bea1bfdc6fc4f7fcacc`, native source
  `6eb61a9faa659b6b07ac16bf9f4bac46a41cd2a7`, harness
  `252c87e367e59cdad1b29f8245d2db618125ad40`.
- F/API28/emulated CELLULAR-only cold DROP/READY/DNS/verified HTTPS/egress stays
  accepted, not repeated. E's two DNS timeouts/two ProtocolErrors remain unexplained;
  F is not a retrospective fix or physical-phone acceptance.
- Original FAILs and A–F evidence remain untouched. Production, G4, paid/cohort,
  public updater/catalogs and user phones are outside this operation.

## Native and package checkpoint

Standard `pilot/android-restricted/build.py` from a detached6eb source capsule builds
arm64-v8a with NDK28.2.13676358, pinned Xray
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, no diagnostic build tags.
The builder's required packet boundary race check passes (count3); no old JNI/JVM
matrix or emulator gate is repeated. JNI SHA256:
`773d760dc8f5a7894ed7008b5f6c30b830bd663f66a8935d470f5262ebc50d26`.
Private output: `state-client-build/cold-field-delivery-20261107/native-arm64`.

Reserve unpublished versionCode120 / `0.1.18-beta120`, not a replacement118.
The initial unsigned local119 draft is abandoned: read-only branch inventory found119
already reserved by `feature/subscription-paid-119-20261107`. That branch and its paid
work remain untouched. No119 cold bytes were signed or distributed.
Package gate now supports a pinned native-source commit and generated-artifact directory;
it still requires clean tracked sources, exact native/manifest match and verifies that
carrier runtime/native/build closure did not change. Application source is independently
recorded. Existing release-preservation pins are advanced only to already accepted9bf
classes, not to new untested application changes.

No final locator has been issued, no signature produced, no APK installed or published.
The ARM64 managed build and unit tests complete; release lint identifies `WrongConstant`
in the accepted API27 compatibility helper (numeric18 is FOREGROUND on that API).
A method-scoped source-only `SuppressLint` annotation documents that deliberate numeric
compatibility path; the expression and network-selection behavior remain unchanged.
Release lint and bytecode equivalence are rechecked before packaging, not waived globally.
Release lint now passes0 errors/57 pre-existing warnings;433 Friends JVM cases pass.
The annotation changes line-number metadata only: `javap -c -p` output is identical.
The first packaging attempt correctly rejects non-pyc Python3.14 build output; using
isolated Python3.10.19 fixes packaging without changing application or bundled Python
version. The final120 normal/restricted native/package gate passes.

## Deliverable server entry

`carrier/cmd/cold-provision-entry` wraps existing coldprovision.Run. The Linux NL entry
keeps the existing gateway key on NL and calls only the two existing RU authority RPCs
over default-verified HTTPS8443 (no proxy/redirect/arbitrary forwarding). The issuer
key and DB stay on RU; the closed one-shot pyz signs only a fresh bound locator, with
existing trust/CRL/admission validation. No second signer or policy database is added.

Disposable package checks pass11 Python cases, including packaged CLI configuration,
closed pyz invocation from outside the checkout, ready/cancel/invalid-locator lifecycle
under Go race instrumentation, real existing handlers issuing a bundle accepted by
the unchanged validator and rejecting invalid identity proof. Issuance leaves registry,
issuer key and admission bytes unchanged. Two focused Go adapter tests pass under-race:
restricted destinations/RPCs/response bound/no redirect, untrusted TLS/wrong hostname.
Existing two framing/no-forwarding checks also pass. Three finalizer tests cover
freshness/budget, payload preservation across signature and duplicate ZIP rejection.
These use disposable provider injection, not another Telemost/Android runtime or F rerun.
An additional offline finalizer test uses the actual120 APK layout, packaged Go verifier,
disposable public trust/locator and real SDK zipalign: four finalizer cases PASS, no skips.
All synthetic test output is confined to a disposable container/tmpfs and destroyed;
no fixture-signed/root-swapped bytes enter the field candidate. The server packager now
requires a fully clean committed worktree before and after packaging, including untracked
source, so source-clean evidence cannot hide dirty Go VCS metadata.

The exact **unapplied** host/path/service/custody/rollback manifest and executable
assets-only workflow are in
[deployment.json](../../deploy/friends/restricted/cold-provision-deployment.json) and
[RU/EN handoff procedure](../../deploy/friends/restricted/COLD_FIELD_DELIVERY.md).
Server-side HTTPS access, real authority/key validity and registered-user eligibility
remain live preflight checks after authorization; no current production readiness is claimed.

## Exact deliverables and remaining boundary

Private output root: `state-client-build/cold-field-delivery-20261107/`.
No binaries/private state were added to Git. [Safe receipt](2026-11-07-cold-field-delivery.json)
retains exact checksums for outputs and verification logs, including failed preparation.

| Component | Source / identity |
| --- | --- |
| Application prebuild | `08d7e416be2bbd9067e207d92fa9900df63f4812`, accepted9bf behavior plus version120/source-only lint annotation |
| Unsigned APK | `accepted-apk-120/FamilyConnect-Test-0.1.18-beta120-unsigned.apk`,50,367,849 bytes, SHA256 `269a9219f093d7afbc487ba41a9115036842ebba22633879d79a794350fca967` |
| Native | accepted6eb, Go1.26.0/NDK28.2.13676358, ARM64/API26 build target; SHA256 `773d760dc8f5a7894ed7008b5f6c30b830bd663f66a8935d470f5262ebc50d26` |
| Server package | `7398858d2b404104e486e56411e78a9e1e15ad78`, Linux/amd64/CGO0; all9 package files byte-equal across two builds |
| Server archive | `cold-provision-entry-7398858-linux-amd64.tar`,16,906,240 bytes, SHA256 `26ccddba2e0eafc635c6138f5109debae8c5b96347de6a0c90561373c2131fdd` |
| Entry executable | SHA256 `c7ed0b15b38fc3f215ef23f8a8687076ed5e73ade1c099d6ffc2d69ca3a8a96c` |
| Closed locator issuer | SHA256 `08b0ed4a8e982f7aa54a64b0630dce68a19399c492ee30fbb8d43ff4016d97a2` |

APK package is `com.familyconnect.app.friends`, minSdk27/target35, ARM64-only,
non-debuggable; all19 JNI exports present, ELF AArch64/16K LOAD alignment and APK16K
alignment verified. Packaged native equals its manifest; diagnostic tags/schema disabled.
No locator, synthetic root, test identity/private key or qualification assets are included.
The public anchor is byte-identical to trusted beta113 and repository ControlTrust,
SHA256 `d0ae60e61af6ac5018428aaad89e362ec0f75d7468633a26c22906356228d281`.

Trusted beta113 digest6078d061…4edc094 is verified with the existing signer certificate
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
New120 is **unsigned**, so signature compatibility is a checked required pin, not a
completed signing/install claim. Identity/configuration/restricted/chat-key vaults,
settings and AndroidManifest match beta113 source d2882cd; delivery changes do not
clear storage or regenerate identity. Actual in-place physical upgrade remains untested.
Unchanged accepted AWG/audio libraries and notices are retained. Matching Codec2 LGPL
source/rebuild files accompany the private kit in `accepted-apk-120/corresponding-source`;
source archive SHA256 `6e3066c08ff87062cfd4e74ee31e5336cabb833ee20a0f97e10c6717b9d4fc1d`.
Retain that source offer with the private APK handoff over the same reachable channel.

The selected release/package batch initially gives80 PASS/1 failure/1 Windows deselection.
The failure is an obsolete exact-string contract: accepted047da1d already inserts
`startupStage="NATIVE_BEGIN_READY"` after `checkAccess()`. The assertion now requires
that exact checked order; all17 targeted orchestrator contracts pass afterward. No
authorization check, runtime assertion, timeout or product code was removed to pass.
Final package tests include the new dirty-source rejection; no production credentials
or calls occur. Full `Client builds` CI (including the independent old runtime/native
suites) was not relaunched for this bounded preparation and is **not** claimed accepted
for120. Its existing release gate still applies before real vault signing. Prior CI,
local433 JVM/lint checks and F are recorded separately, not substituted for it.
Final120 variant unit check passes433/0 failures/errors/skips at9f194fd; Android
sources remain byte-equal to APK build08d7e41 and its immutable APK digest is unchanged.
Final selected source/package/orchestrator checks pass54 with no skips. Earlier local
119 draft and failed preparation logs remain hashed evidence, not candidate artifacts.

Remaining sequence: complete release acceptance before ephemeral issuance; obtain one
authorization for only the new bounded NL1 entry + existing RU issuer operation + private
handoff. Confirm live server credentials/handlers, selected-node/user eligibility and
reachable private delivery channel. Then issue the real locator, package only that
asset, sign via the existing protected vault workflow and verify exact signed bytes.
No manual key extraction is needed; production vault access was not attempted early.
The generated receipt supplies absolute Connect cutoff=locator expiry−200s; missed
window means no attempt with expired material, fresh coordinated issuance, and a new
free version if previous bytes were already handed off. No blocked-page promise or VPN.

Original19 FAIL artifacts and all A/B/C/D/E/F receipts14/11/9/12/18/19 rehash unchanged.
No AVD, real provider room, OAuth access, production write or phone operation occurred.
Disposable test containers exit/remove; test HTTP threads join; synthetic material in
tmpfs is destroyed. No own persistent runtime remains. Provider object deletion is
not claimed. This is neither G4 PASS nor proof of the original physical user's network.

Rollback is to stop only the prospective new entry; existing services and public
beta113/catalog7 remain unchanged. No new public download link/checksum is advertised.
# Release qualification continuation

The prepared node/host mapping is corrected toNL1/185.10.158.212. Signed retained
catalog4/6 verify offline; the old host186.246.45.246 is retired, not a management alias.
[Binding evidence](2026-11-07-cold-field-node-binding.json). Fresh deployment preflight
must verify the current canonical profile/leaf; documentation is not live verification.
The original server7398858 archive is preserved and superseded only by a newly hashed
package. Exact-source Client builds Android qualification and CI byte selection are
in progress; the old local269a9219 APK is not retroactively CI accepted.
Client builds42381579767/head59849b0 selects Android; Windows/Linux jobs are skipped
by the existing path policy, not waived after failure. Saved NL1 binding readback also
establishes canonical `/etc/fc-canonical-pinned-venv/profile.json` and existing provider
environment/service user; the template is corrected, live verification still mandatory.
Finalizer now pins the CI prebuild/receipt/source/native/anchor and independently checks
that the prepared APK differs by only the locator before accepting a signature. Pins
remain PENDING until downloaded acceptance. Five synthetic KeePassXC→memfd→apksigner
tests pass on the host; fixture packaging passes with real zipalign in isolation.
The corrected unit uses ProtectSystem=strict without binding the canonical directory:
the existing custody reader rejects mounts at/below that path. A package configuration
test exercises a real root-owned0640 canonical profile in an isolated container.

First Client builds42381579767/head59849b0: Android job128430153601 FAIL atAPI35,
`ProvisioningDiagnosticRuntimeTest` → UnsatisfiedLinkError/libfc_restricted.so absent.
Contracts/race/native AWG+audio/managed unit+lint/APK checks passed; API27, restricted
ARM64 and release upload were not reached. Runtime artifact13578990044 ZIP SHA256
e37868205ac0bd94556947a90c9c76588d19d573fa8f4e1e97c63be9684e48ed is retained.
The unchanged diagnostic test had been added to androidTest, but CI built restricted
JNI only after both emulator runs. The build dependency is corrected: standard builder
supports explicit production-tag x86_64 (no local-core/owner tags), built before runtime;
its output is preserved separately before the existing fresh ARM64 build. Four targeted
builder/order regressions cover this; no assertion/skip or application/native runtime
code is changed. A new exact-source Android run, not a retry of missing-library bytes,
must pass. Separate phase0/control preview fixture failures are not a full-matrix PASS.
Corrected client source18bdeeeef44d9f153273b87be26a251d2f3e7d74 is running as
Client builds42383259832/android128435219393;42 targeted package/build contracts PASS.
The canonical profile test additionally runs the real packaged executable as UID/GID65534
with no supplementary groups against a synthetic root-owned0640 profile. Initial
container noexec refusal is retained; explicit exec on its own disposable `/run` tmpfs
permits that probe (2 PASS), with no host mount/power/user-account change.
