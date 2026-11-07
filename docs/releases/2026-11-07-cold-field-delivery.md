# Bounded cold field delivery preparation — 7 November 2026

Current status: READY_FOR_CONTROLLED_FIELD_OPERATION. Exact Android release-CI and
downloaded prebuild55525859, corrected server package3c0487eb and finalization checks
are accepted. NOT SIGNED / DELIVERED / FIELD_PASS; no ready-to-install locator APK yet.
[Machine-readable final receipt](2026-11-07-beta120-release-qualification.json).
The following local pre-CI checkpoint and failed CI sections are retained history;
the final qualification section selects the only current delivery combination.

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
The deployment manifest names the current RU `family-connect-friends-http-candidate`
unit from canonical inventory/readback, not the historical friends-access service alias;
it remains explicitly unchanged by this operation.

Second Client builds42383259832/head18bdeee: Android128435219393 FAIL atAPI35 after
the required production x86_64 JNI build succeeds. The diagnostic probe now reaches Go,
but `runtime.cgocallback` reports an unknown caller PC. Runtime artifact13578524175
SHA256 f8670dd3850d3cf809ef93764fd5b0b6df0632f6034ce30a3a2efd301de9a3a3;
debug artifact13578848425 SHA256
e71c0cb2bf3547d5ba6d6d060d2b9ca30153a179aabc7012912fceb7a5e0f4a2 are preserved.
The process had already entered AWG Go on the instrumentation thread. The unexpected
PC ends at AWG `runtime.goexit+1` (offset0x1014dc1, inferred page-aligned base
0x792aa3213000); restricted cgocallback belongs to base0x792b280ba000. Go1.26.1
runtime/cgo/gcc_android.c assigns both runtimes TLS_SLOT_APP=2 onQ+. Both ELF files
already have SYMBOLIC/BIND_NOW/NODELETE; adding Bsymbolic would not fix that TLS collision.

Bounded correction: every restricted JNI→Go call uses a new native pthread and joins
before releasing Java-owned marshaled inputs. No JNIEnv crosses threads. Independent
calls preserve concurrent Close/Post; allocation failure does not enter Go and releases
the newly acquired global owner. C regression covers all19 exports, foreign caller TLS,
concurrent cancellation, result lifetime and allocation failure. The Android test now
explicitly enters AWG before and after restricted diagnostic/state calls on the same
Java thread. No test is skipped; API27/API35 hosted release confirmation remains required.
The new glue is a native-source delta from6eb, not a claim that F used these new bytes.
F and the old local ARM64 artifact keep their original accepted/historical scope.
Targeted host regression:26 contracts PASS and real JVM/JNI/Go diagnostic matrix PASS
after this relevant glue change; retained log SHA256
e6f93a56ee56c7a46407dd80b0053f2cc1e21d07fd34075936ad02901141c1ed.
This is not the Android confirmation of the multi-runtime fix.

## Final qualification — READY_FOR_CONTROLLED_FIELD_OPERATION

Client builds42385799106, Android job128442818128, source
55525859465ff4713196db7206129ad840f67cb3: PASS through the existing full selected
Android release pipeline: contracts, carrier/packet race, native builds, unit/lint,
API35, API27, fresh ARM64 build and exact release payload verifier. Readiness wire
42385799093 also PASS. Client builds Linux/Windows jobs are skipped by the existing
source-path policy. Separate phase0/Linux-control failures remain outside this Android
acceptance; this is not whole-repository CI green or a waiver of their failures.

438 Debug +433 Friends JVM cases PASS. Per API,82 instrumentation cases are declared:
API35 executes48 with34 existing assumption skips; API27 executes46 with36 skips.
No failures/errors. The previously crashing multi-runtime diagnostic executes and passes
on both APIs, with AWG calls before and after restricted calls on the same Java thread.
No new skips/assertion changes are used for acceptance. RU/EN large-text, failed controls
and legacy voice UI screenshots were downloaded and inspected. Existing durable-storage
conformance passes; this is not a physical113→120 update. C dispatch additionally passes
ASan/UBSan and all19 typed argument checks without warning suppressions (test-only3cd8698).
F is not rerun and no new Telemost/cold/physical-phone success is claimed for this JNI delta.

### Selected client bytes

- ARM64 artifact13580421361, ZIP SHA256
  `4a44d04badb22cb06e31d09fb2d4b5ec152232f9aad99c96fb2b8168c717f4d3`.
- Unsigned APK50385121bytes, SHA256
  `9eae8668544c9b0d968befb82dc655a2594535fe59c4b5af5d55a804fd67348c`.
- CI verification receipt SHA256
  `48eab8c49462e3feb8c1d819db037c909ea92129eadc5915f073436275f466bb`.
- ARM64 JNI SHA256
  `9f5798fdf17c81a53fb162f110bd2ec8b945181b5e7abc0f6804c662f1a0d11f`;
  API27/API35 test JNI61f8037a…12198, both from55525859/production tags.
- Packagecom.familyconnect.app.friends/code120/min27/target35, ARM64 only,
  all19 Java JNI exports,16KiB alignment, Go1.26.1/NDK28.2.13676358.

The Go VCS stamp says modified=true in the generated CI workspace; the builder's tracked
runtime-source guard passes and the manifest pins checkout tree
9944a4afb8b1f5ba805a220531d693e8abfd3635. Generated/untracked CI output also affects that
Go stamp; do not call the entire generated workspace pristine. Rootd0ae60e6…d281 matches
113; no locator, synthetic root/identity, private key, owner diagnostic tags or qualification
transport is supplied in this release payload. Unsigned signature rejection is expected.

Compared with local269a, exactly8/143 ZIP members differ. DEX, Android manifest, trust and
all other members are byte-identical. Restricted JNI/build metadata include the bounded
callback fix/new provenance. AWG build metadata changes source/ABI hashes; its Go build-info
differences are temporary replacement paths; AWG and Codec2 .text sections are byte-identical.
Codec2 includes build/debug metadata. Chaquopy archives retain identical member sets and
equal decoded Python3.10 code objects (14 app/140 dependency), with pyc header/frozenset
serialization order and container metadata differences. Use the qualified CI combination,
not a mixture with old native/payload. Codec2 source tar/build glue/notices match the CI audio
manifest and APK. An exact55525859 public-source archive is retained alongside the CI kit.

Debug13579723637, runtime13579319399 and UI13579533973 were also downloaded and their
GitHub archive digests verified; exact hashes and all mandatory step results are in the
[final receipt](2026-11-07-beta120-release-qualification.json).

### Selected server bytes and offline finalization

Clean server source3c0487ebd0acdb79149d20dc69a4d63942f891b9, Linuxamd64/CGO0/Go1.26.0.
Two independent outputs are byte-identical. New immutable archive
`cold-provision-entry-3c0487e-linux-amd64.tar`,16916480bytes, SHA256
`5ec255f586398fbf6c17623a83056d73e0ea41c0bd7573945cf17586146d71cb`.
Manifest SHA256`ffb0c61fbd8647e1f082da3231f990e26271a1a57f0531fb77062c6f0b5c5564`;
deployment manifest SHA256`2d08912201199e7c699e0439fb12bb10ca54f2efbddf1dbec3572ce6090e4ecd`.
This package replaces, but does not overwrite, the incorrect old7398858 package.

Eleven isolated package/finalizer tests PASS,0 skips: configuration/custody and real
root-owned canonical profile read as an unprivileged user; packaged issuer/lifecycle,
existing authority handlers, bounded RPC/TLS/no-forwarding checks; actual SDK zipalign
and asset-only finalization with synthetic ephemeral authority. The test binary is built
with race support from this server source. No provider request or production issuer is used.
Fixture output dies with the disposable container. Independently, the unmodified real CI
prebuild and production root pass the now-pinned finalizer input check. Five existing
synthetic vault/apksigner tests pass without accessing the production key. No final field
signature or production locator has been created.

### Single subsequent operation, still not authorized here

Confirm recipient readiness and a reachable private document/local-transfer channel before
entry start; both remain unconfirmed. Do not assume the blocked download page or another
VPN. One authorization covers current NL1 canonical profile/leaf/route/backend/custody
preflight, installation/start of only the new bounded entry, one-shot real RU locator,
binding/expiry/liveness checks, minimal locator-only packaging, existing-key vault signature,
exact payload/113 signer verification, private handoff and the one ordinary field Connect.
Install over113 without clearing data/new identity; classify warm if a valid cache exists.
Record server readiness near Connect; at READY verify DNS, verified HTTPS and egress and
export minimal diagnostics. Historical emulator EACCES is not assigned to the phone.

Entry lifetime420s; `E=min(seed expiry, trust expiry, leaf notAfter, CRL nextUpdate)`.
Candidate200s and handoff reserve60s require260s remaining at preparation;
`connect_not_after=E-200s`. At best preparation finishes byT0+160s and Connect starts by
T0+220s; earlier trust expiry shortens both. Readiness30s is unchanged. Systemd440s/stop20s
is cleanup, not validity. All CI/tools/source work is complete beforeT0. Missed window:
stop own entry and arrange fresh issuance; do not extend TTL or reuse handed-off120 bytes.

Public signed catalog remains113/sequence7/hash2283a89f…1b30; public120 URL returns404.
Read-only main advanced to1cbe8fbf (still119), paid branch remainse7759534; neither was
modified by this task. This does not prove absence of every private distribution: recheck
reservation before handoff. Public118/default113/updater remain unchanged.

Original FAIL manifest still hashes8b4501cf…6961c; old server26ccddba…131fdd and local269a
are retained. E/F retain their exact scopes and E's unexplained2/2 counters. No local AVD,
OAuth, rooms, Connect, production change, phone installation or public release occurred.
Own test processes/containers ended; provider room deletion is not claimed. Native/runtime
and field-signer/source compatibility are not a performed physical update or FIELD_PASS.

### Owner API31 operation preflight

The owner authorized the field operation and then explicitly selected their USB-connected
Redmi Note9 Pro, Android12/API31/ARM64, installed119, instead of the original API28/113
target. This changes only the addressed test scope; no original API28 or cold PASS follows.
The accepted b3af8cd kit remains unchanged. Installed119 APK SHA256 is
`52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d`;
its verified sole signer and ControlTrust root match the accepted120 requirements.
The actual119→120 installation has not occurred.

Private evidence directory (excluded from Git):
`state-client-build/cold-field-delivery-20261107/owner-api31-20261107T193739Z`.
Exact phone Support ID from explicitly enabled USB support resolves to one existing
device. Read-only RU registry/grant checks pass; no enrollment/admission/subscription
change. Current NL1 canonical profile and RU trust agree on family/gateway, issuer,
revision floor1, CRL/floor27285. Leaf/CRL expire22:28:35UTC. Existing `public-gateway`
RPC validates the current key/public-certificate pair without exporting a private key.
The initial operator RPC serialization was rejected `NON_CANONICAL_INPUT`; canonical
JSON succeeds. Both responses are retained; no server change or bypass was required.
NL1→RU8443 verifies normal HTTPS/IP trust and reaches the challenge route (GET405,
SSL verification0); this is not a successful authorized provisioning RPC.

CI prebuild9eae8668…7348c, JNI9f5798fd…0d11f, rootd0ae60e6…d281 and server archive
5ec255f5…d71cb hashes match. Protected local vault check-only verifies the required
certificate; no APK is signed and no key/password is persisted. One incomplete earlier
vault preflight is retained as unsuccessful, not a signed result.

Only new manifest paths are staged: NL1 entry binary/public anchor/template unit/run
parent and RU one-shot issuer tool/run parent. Every transferred file hash matches the
accepted kit. Unprivileged `--check` returns `CONFIGURATION_VALID_NO_PROVIDER_CALL`.
Provider environment stays root0600: systemd reads EnvironmentFile before dropping to
the existing service user; permissions are not broadened. Template verification and
daemon-reload complete without restarting existing services. New instance
`cold-provision-entry@cold-owner-api31-20261107t193739z.service` is inactive/dead,
MainPID0, template static/not enabled; its invocation directory does not exist.
Existing NL bootstrap PID1072432 and RU authority PID3636765 remain active/unchanged.
No new entry process, provider room, locator or connection needs stopping at this point;
staged files remain inactive for the authorized continuation, not an active deployment.

Phone snapshots show DISCONNECTED, app TUN closed, WIFI and a validated bundle expiring
22:28:35UTC (23:28:35Europe/Brussels). Do not remove it to manufacture a cold result.
An attempt using it is WARM. Owner was asked to select NL1, disable Wi-Fi and other VPNs,
leave mobile Internet available, and signal readiness before the short entry window.
Final selected-node/other-VPN checks remain pending. Public120 file still returns404;
this does not prove absence of every private distribution. Updater/catalogs unchanged.

States: LIVE_PREFLIGHT=server/device checks pass, final phone setup pending;
ENTRY_READY=NOT_STARTED; SIGNED=NOT_RUN; HANDED_OFF=NOT_RUN; INSTALLED=119;
COLD_OR_WARM=valid cache present, WARM if used; FIELD_PASS_OR_FAIL=NOT_RUN;
CLEANUP=no started entry/connections, own check processes completed. The entry lifetime
and locator countdown have not begun. Next action is the coordinated operation, not
another build, release gate or documentation-only acceptance.
