# NORMAL-NATIVE-PROVENANCE-1 — PASS

The stale normal-native input STOP is resolved without changing product source,
restricted packaging logic, expected source hashes or either APK verifier.
This continues [the packaging STOP](2026-10-06-owner-diagnostic-packaging-1.md)
and [DIAG-SOURCE-FREEZE-1](2026-10-06-diag-source-freeze-1.md).
Source/artifact acceptance is not installation, deployment or physical acceptance.

## Authoritative builder and identity

The accepted path is pilot/android-awg/build.py, documented by
[Android transport acceptance](../android-transports.ru.md) and executed by
.github/workflows/clients.yml. It builds the unified libfc-awg.so containing normal
WG/AWG/TCP and generates Java, JNI and license/provenance assets. It rejects an
existing output directory. No ad-hoc native implementation or metadata patch was used.

| Contract | Accepted value |
| --- | --- |
| Builder SHA256 | 61036e9f70ac5cdb8ac654bb3c88423d0bcf3306e5b0244a4b3dbd6b22fb826d |
| Android adapter pin | 5420011143f9dd42831cc95fcdb0d6ac9bde868f |
| AWG3.1 engine pin | b5928efb6ca19f0153958460c3d141f04abc5c2e |
| Xray pin | d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 |
| WG fixture pin | ecfc5a8d54462e18e13c72173e2623d16d8e25a0 |
| Toolchain | Go1.26.1; Android NDK28.2.13676358; Android API26 compiler;16KiB maximum page alignment |
| Pair ABI | arm64-v8a only; ordinary all-ABI defaults unchanged |
| Source hashing | SHA256 of exact file bytes, not normalized text |
| Generated metadata | Existing assets/awg-build.json, no new schema or post-build editing |
| Outputs | jniLibs/arm64-v8a/libfc-awg.so; generated java; assets/awg-build.json and awg-licenses; separate host fixtures not packaged |

Exact scoped TCP source remains:
`be122bb32c4ecf59a6c3d49aaa2a8015e61562cd4123ef65b0278974dc05d988`.
TCP JNI SHA256 remains:
`6ef06b63b6d19a1160819a7fd5ac9bf19dc07db8ba32e9cc0903e1fcb4a1470b`.
Generated adapter jni_source_sha256:
`a38d3b23b2f385e7af4d5ea3a91ebbde3ab29e240a565a47a2ed10cbefa41481`.
Engine/interface patch SHA256 values are62acf2d7/ae27306d respectively; full hashes
are retained in metadata.json and downloaded awg-build.json. The generated metadata
also records actual NDK revision, builder/source revision, ABI binary digests,
go_sum_sha256, single_runtime=true, public_uapi=false and root_backend=false.

Before building, source-guard.json verifies the clean detached35-file diagnostic
candidate02f7eb9618bf1b5105cea7433a0c687dd9e452b1, exact TCP hash and input hashes.
Excluded readiness/control/docs changes are not copied. Authoritative fresh output
was built under /tmp/fc-normal-native-provenance-1; old generated outputs were moved
intact into private evidence, not reused or overwritten. Fresh Java/JNI/assets were
staged into the existing ignored awg-generated location only after metadata PASS.

## Native and package acceptance

- Metadata/source guard, dependency/toolchain pins and AArch64 ELF: PASS.
- Provenance/AWG recovery/vector/owner-checker tests:38 PASS.
- Authoritative AWG engine package set, including regression_test.go: PASS ×3.
- Authoritative Android TCP bridge host-check tests/build: PASS on clean pinned Xray.
  Initial refusal of an already patched local checkout and sandbox module-download
  denial are retained; a fresh pinned checkout and approved network execution resolve
  prerequisites without changing code or weakening the clean-source guard.
- Fresh-directory owner/Friends APK builds,258 unit tests each and lint: PASS;
  zero lint errors,36/37 warnings. No previous unsigned APK was reused.
- pilot/android-awg/verify-apk.py: PASS on rebuilt owner APK and downloaded CI APK.
- Existing normal provenance verifier: PASS, including exact builder/TCP source hashes.
- Restricted P1–P7: PASS. Accepted restricted JNI unchanged during local normal rebuild;
  final CI rebuild binds both native libraries to the final exact source revision.
- Same Friends applicationId, beta66/code66, non-debuggable, ARM64 only, owner-only
  DUMP receiver, restricted schema1/source metadata and16KiB alignment: PASS.
- Public source/index guard:1781 entries,0 blocked. No excluded source imported.

### Reproducibility limitation, not concealed

A second authoritative fresh build has identical sources, pins, Go module checksums,
Java, headers, licenses and host fixtures, but its normal .so differs. Raw byte
reproducibility is therefore **NOT PASS**; reproduce.json retains FAIL.
Read-only binary comparison proves the entire difference is four occurrences of
the random temporary directory in embedded Go module replacement metadata.
Replacing those prefixes in memory solely for comparison makes the complete byte
arrays identical; no files, verifier or expected artifact hash were modified.
Go build-info output independently identifies the two engine/Xray replacement paths.

First local native hash af7b5025af9ecb9614b9813c62e3ece1a2c28efa38da1f4377c4fa6081536bbc;
repeat ac2e5954d8edd4660cd02b7e82435c2763331b6037d4f2b8b69c0ec1a084fdad.
Each generated manifest correctly hashes its own binary. Provenance acceptance binds
the exact downloaded CI bytes, not a claim of bit-reproducibility across temporary
paths. The old f5ec5e49 source hash is absent from newly generated provenance.

## Intermediate source and CI artifact (not the final pair)

Clean scoped source commit:
`9e8640a3b5c508239ca0f05626e38fbe3d8050cd`.
Immutable CI tag: `v0.1.18-beta66-ownerDiagnostic-ci1`.
All35 accepted source inputs remain identical to02f7eb9. The only additional file is
.github/workflows/owner-diagnostic.yml: a read-only-permission, non-deploying workflow
that builds/verifies unsigned owner/Friends packages, tagged native, diagnostic race
tests and matching gateway, then uploads artifacts. No signing secrets enter CI.
Original working-tree HEAD/index and excluded work are preserved; remote main stays
8d04632. This is not a public beta66 release or any catalog/invitation update.

Owner workflow37422149024 PASS, artifact11393268238 downloaded and independently checked.
ZIP SHA256: f8d3cbf58101bed935cdffa0a998b6fc3e125d5d27b890f0e3d88b1fdddc101e.

| Downloaded unsigned pair member | SHA256 |
| --- | --- |
| Owner APK | 9499ff383557c654a60ed291dc093c9faef188f61cbbc1832458fd63e3a4ffff |
| Restricted JNI | 90e5beddfa68145c1de829a2d9d331bb08e88b638e0448da7e512d0f46930c99 |
| Normal JNI | 21d64d60581c5552b378fb1e4063d66c824d375b934f6f281c5612c46903812c |
| Matching gateway | d08d1eaf873bbacb7aa24841de6bf9a75e4cbc57accead4bcfe3c409d547485f |

Both native metadata assets report that intermediate source revision. Restricted JNI and
gateway Go build information carry fc_owner_diagnostic and vcs.modified=false.
The downloaded libraries exactly equal the APK entries. The normal metadata records
the expected be122bb3 TCP hash and builder61036e9f. No metadata is relabeled.

## Historical completion checkpoint (superseded)

At this checkpoint remaining platform CI is running. Signing has NOT started and
no signed pair manifest exists yet. DIAG-SOURCE-FREEZE-1 remains PARTIAL until all
required CI, accepted-signer signing and immutable manifest verification finish.
DIAG-PAIR-DEPLOY-1 is NOT yet allowed. No owner installation, gateway deployment,
credential renewal, READY, device fault arming, physical Telemost, soak, tester
contact or public/default/catalog/invitation mutation occurred. Disposable CI
emulator/platform acceptance is distinct from owner physical acceptance.

Private receipts are under state-client-build/field65-export16/diag-source-freeze-1/
normal-native-provenance-1/. Prior STOP reports and failed receipts remain intact.

## Final freeze — PASS

Final clean source commit: `5327deb414ae8aa77ce2f9490fd99c9485eba740`.
Immutable CI-only tag: `diag-owner-beta66-ci2`. All17 required hosted workflows
completed successfully, observed2026-10-06T06:48:39Z. Owner pair run37424038212;
Client builds37424038238. Final artifact11394575744, archive SHA256
8876f6164aecd28b55c98e1df001fb4baa608f19f600ebbed8e46ec4b9f2b210.
All35 diagnostic inputs remain exact; two additional CI workflow inputs are mapped
in the manifest. The cloned source is clean; original HEAD/index/main and excluded
readiness/control work are preserved. No production source/semantics were changed.

The intermediate v-prefixed CI1 tag unintentionally selected the legacy public
release job. Its version guard failed before `gh release create`; no release was
published. That CI failure was not waived. The corrected CI-only tag namespace is
accepted by Client builds, but cannot select its public release job; the owner-only
workflow uses the same namespace. Final CI was rerun successfully on the new commit.
Existing public release guard/condition were not weakened; both historical tags remain.

Final normal metadata reports TCPbe122bb32c4ecf59a6c3d49aaa2a8015e61562cd4123ef65b0278974dc05d988,
source revision5327deb414ae8aa77ce2f9490fd99c9485eba740, Go1.26.1,
NDK28.2.13676358 and the unchanged pinned builder61036e9f. Both native metadata
assets and clean restricted/gateway Go build information match this revision.
Downloaded verify-apk.py PASS; P1–P7 PASS; exact APK JNI/assets equality PASS;
arm64-v8a-only, non-debuggable, packagecom.familyconnect.app.friends,
version0.1.18-beta66/code66 and owner-only DUMP control PASS. Scoped source index
privacy1781 entries/0blocked; bounded APK privacy136entries/0blocked.

| Final immutable pair member | SHA256 |
| --- | --- |
| Signed ownerDiagnostic APK | e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81 |
| Downloaded unsigned APK | 2cc7f592c854189b8a4edbeb4de8f68396cb388999f3ac2238da68f090b8cf90 |
| Restricted JNI, inside APK and sidecar | e433a4910d218065bd4a217b1c87aaad1698d3f4716179b7559248d41b49c792 |
| Normal libfc-awg.so, inside APK and sidecar | 44f3e72f658095a98a1b738dfcb0409a99a7be7739653c95423a023cca7f4563 |
| Matching diagnostic gateway | 6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec |
| Pair manifest | 8af6f13348c5c7d6b095eb6003f04a3ae99f100837ef685b53295cc563acbc77 |

Existing accepted single-signer certificate SHA256:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Offline apksigner verification, v2 signature, alignment and unchanged original ZIP
entries PASS. Initial local signing wrapper failed loading the signer because it
requested the same one-line password file twice; no APK was created. The wrapper
was aligned with the accepted PKCS12 command (one password read), without modifying
the key/password or requesting credentials; signing and verification then passed.

Pair location: `state-client-build/field65-export16/diag-source-freeze-1/immutable-ownerDiagnostic-beta66/`.
Manifest: `pair-manifest.json`; APK: `FamilyConnect-OwnerDiagnostic-0.1.18-beta66.apk`.
The manifest binds commit,37input hashes, APK/JNI/normal/gateway hashes, certificate,
fault schema1/fc_owner_diagnostic/DUMP/one-shot DISARMED contract, CI artifact/runs,
and hashed current plus retained test receipts. No byte is substituted after sealing.

NORMAL-NATIVE-PROVENANCE-1 PASS; OWNER-DIAGNOSTIC-PACKAGING-1 PASS;
DIAG-SOURCE-FREEZE-1 PASS. DIAG-PAIR-DEPLOY-1 may now START separately. Recommended
next step: inspect this sealed manifest before any separate deployment procedure.
Built/signed does not mean installed/distributed/READY. Owner UID/data preservation
capability follows unchanged package and signer; actual install preservation remains
unexecuted. No owner install, gateway deploy, credential renewal, READY, fault arming,
physical Telemost, soak, tester contact or public beta65/default/catalog/invitation
change. No rollback is needed because no runtime rollout occurred; retain existing
owner/gateway pair and beta65 bytes. Raw cross-temp-path bit reproducibility remains
the explicitly documented limitation, not a claimed PASS or source mismatch.
