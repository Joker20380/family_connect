# 5N-ANDROID-CANARY-BUILD — 02.10.2026

**Subsequent installation, attempt14:** the unchanged accepted APK was installed
in place on the owner Redmi02.10 16:43:11UTC; exact installed hash/signature/code54
verified16:47:47UTC. No uninstall/data clear/public distribution. Server restricted
deployment rolled back after owner UI observation failed; cache/import readiness
unverified. This does not rewrite the build-only evidence below.
[Attempt14 result](2026-10-02-5n-prov1-attempt14.ru.md).

**5N-ANDROID-CANARY-BUILD = PASS. LOCAL BUILD / PROVENANCE ONLY.**

Starting/final HEAD: `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`.
Preceding accepted [owner-proof handoff](2026-10-02-5n-owner-proof-handoff.ru.md)
is packaged, not redesigned. No production access/deployment, authority refresh,
product services, live Telemost, Redmi/ADB, installation, key extraction or push.
No new FIELD APK. No automatic deployment attempt13, DIAG-1 or regional beta.

## Artifact and provenance

| Field | Accepted value |
| --- | --- |
| Private canary APK | `state-client-build/android-canary54-4bb53b0/artifacts/FamilyConnect-canary54-prov1-4bb53b0-arm64.apk` |
| APK SHA256 | `f81920412089bd87950d8055daf883b754fea3323b412ccb28b0c092b9a909c6` |
| Size | 49,593,211 bytes |
| Source | `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`, all1608 exported tracked blobs verified |
| applicationId | `com.familyconnect.app.friends` |
| Version | `0.1.18-canary54-prov1`, code54 |
| ABI / SDK | arm64-v8a only; min26, target/compile35; non-debuggable Friends variant |
| Certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Go / NDK | Go1.26.1 linux/amd64; NDK27.2.12479018 |
| Xray, both builders | `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` |
| Amnezia Android / engine | `5420011143f9dd42831cc95fcdb0d6ac9bde868f` / `b5928efb6ca19f0153958460c3d141f04abc5c2e` |
| Restricted gVisor | `v0.0.0-20260122175437-89a5d21be8f0` |
| Fresh packaged `libfc-awg.so` | `1527c5b68c767dcae0609c873b505613c2d0eb84118735e054f5d444b3b39db0` |
| Fresh packaged `libfc_restricted.so` | `7316f8254d3a8b333a30431c62363956e7793b27c41cd12da51a08189dc2a97a` |

Both product JNI libraries were built anew from the clean export using the committed
builders, not copied from canary53. Exact output/embedded-manifest/APK hash equality
verified. APK also includes pinned Chaquopy runtime libraries; these are cached
third-party dependencies, not claimed as locally rebuilt. The complete native hash
inventory is in `artifacts/manifest.json` beneath the task directory above. That
manifest also records source-inventory/packaging-override digests and test classes.
Go/cgo builds are not claimed byte-for-byte reproducible across arbitrary build paths.

Existing protected local beta PKCS12/password were read with ownership/mode/type
checks and certificate pinning; signing used the accepted `scripts.sign_android_vault.sign`
memfd primitive. No secret argv/env/output or additional plaintext key export.
APK signature verification, v2 signature and ZIP alignment PASS. Output is0600.
No release tag, update catalog, invitation page or public download changed.

## Broken symlink: stale generated state, not repository defect

Exact failed path:
`clients/android/app/build/python/env/friends/bin/python3.10`.
Old target: `/tmp/fc-chat-tools/python310/python/bin/python3.10`, now absent.
Sibling `python`/`python3` point to `python3.10`; old `pyvenv.cfg` records that
temporary Python3.10.21 installation. The links, venv and target installation are
untracked generated toolchain/build state; `app/build` is ignored.

Generator: Chaquopy16.1.0 `TaskBuilder.createBuildPackagesTask`,
`:app:extractFriendsPythonBuildPackages`. Inspection of the cached plugin bytecode
confirms it calls configured host Python `-m venv --without-pip`. Gradle encountered
the dangling generated output while inspecting the old venv, before Java compilation.
This is not a missing tracked Python source or Android protocol defect.

Repair: preserve the stale venv as `stale-python-env-friends` in the ignored task
directory; regenerate with the existing `clients/android/chat-python.gradle`
`fcBuildPython` property. The selected complete Python3.10.21 toolchain in this
environment is `/tmp/fc-eu6-python310/python/bin/python3.10`. Chaquopy itself creates
the new symlink; no manual link rewrite, arbitrary checkout or file copying to fool
Gradle. Root-worktree `extractFriendsPythonBuildPackages` actually succeeds after
regeneration (8s). The accepted APK was independently built in the clean export,
not from the repaired root-worktree build outputs.

Repository/source fix required: **no**. No Android/build source changed; no commit
required or made. Toolchain location is a build-time input, never a committed
absolute path. A Python toolchain must outlive any generated venv that references it.

## Rebuild contract

Use a new private output directory and `git archive` of the accepted full HEAD;
verify exported blobs against `git ls-tree`, without overlaying dirty files. Set
JDK17, SDK35, NDK27.2, Go1.26.1, Python3.10 and pinned dependency caches. Native
builders remain `pilot/android-awg/build.py --abi arm64-v8a` and
`pilot/android-restricted/build.py --xray PINNED_XRAY --go GO --ndk NDK --out OUTPUT`.
Use the export's ignored `clients/android/awg-generated` and `restricted-generated`
outputs. Do not reuse previous JNI. Preserve public beta51 version defaults.

For a private packaging override, an external init script only sets Friends
`android.defaultConfig.versionCode=54` and `versionName='0.1.18-canary54-prov1'`.
No signing/debug/diagnostic/source substitutions. From an environment with explicit
`JAVA_HOME`, `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `GRADLE_USER_HOME`:

```sh
gradle -p "$CLEAN_SOURCE/clients/android" --offline --no-daemon \
  --project-cache-dir "$PRIVATE_BUILD_CACHE" -I "$PRIVATE_PACKAGING_INIT" \
  -PfcTargetAbi=arm64-v8a -PfcBuildPython="$PYTHON310" \
  :app:assembleFriends :app:testFriendsUnitTest :app:lintFriends
gradle -p "$CLEAN_SOURCE/clients/android/control-tests" --offline --no-daemon test
```

Actual Gradle8.11.1 build: **BUILD SUCCESSFUL,1m1s,65 executed tasks**. All requested
assembly/unit/lint tasks ran. `--offline` refers to Gradle dependency resolution;
Chaquopy pip uses its pinned requirements/cache and configured package indexes.
The initial command used a relative init path that Gradle resolved under the project;
correcting the invocation to the actual external init script needed no source fix.
Sandbox-only Gradle socket/native clone failures were rerun with authorized local
tool/network access. No remote deployment command was run.

For signing and verification follow [Android signing protections](../android-vault-signing.ru.md).
Do not replace already accepted APK bytes; use a new version/output for later changes.
Current evidence scripts, logs, manifests and XML results remain in the ignored task
directory; generated/native/APK/private artifacts are not committed.

## Validation and security boundary

- Full app Gradle JVM suite: **204 passed,0 failures/errors/skips**. Includes
  product challenge/proof/fetch, safe receipts, identity, restricted cache storage,
  monotonicity, readiness summary and orchestrator/lifecycle state tests.
- Separate control JVM suite: **149 passed,0 failures/errors/skips**; overlaps app
  tests and is not149 additional unique tests.
- Python Android/proof/native-provenance/signing/handoff contracts: **56 passed**,
  including real local signing fixture and controlled native delivery validation.
- Backend restricted delivery/authorization and acceptance guards: **71 passed**,
  including invalid/revoked/non-canary, replay, expiry and native timestamp fixtures.
- Go `test -race` and `vet`: `wholedevice`, `familysession`, `bootstrap` PASS.
- Lint: **0 errors,37 warnings**, not warning-free. No unrelated warning cleanup.
- JNI: ELF64/AArch64, `NativeRestricted_validateDelivery` and `beginReady` exported;
  exact native bytes in APK match fresh outputs. Current prewarm/receipt/cache/vault/
  orchestrator classes verified present in packaged DEX.
- Bounded APK/nested-Python secret scan: **1074 entries,0 findings** after one
  hash-pinned previously reviewed stdlib `distutils` false positive. No OAuth token,
  real room URL, private-key/profile/credential artifact found. This is not an
  exhaustive proof over arbitrary encodings; no production OAuth value was read.
- Signature/package/alignment, local docs/source inventory and `git diff --check`
  PASS. Real Android Keystore/instrumentation/process-restart/VPN behavior is **not**
  established by JVM/static checks and remains a physical acceptance obligation.

Actual product path remains:
`FriendsAccessAndroid` normal control → `FriendsRestricted.prewarm` →
`FriendsReadinessProtocol` restricted challenge → `ControlIdentity.proveTransportKey`
inside Friends → readiness fetch → `NativeRestricted.validateDelivery` →
`RestrictedCache.accept` → Keystore AES-GCM `RestrictedVault` AtomicFile/import →
restricted recovery READY. Cache/cooldown/single-flight policy unchanged.
Safe `OwnerPrewarmReceipt.imported` follows successful validated storage; no raw
proof/bundle/key/join URL in diagnostics. Operator proof callback/key access: **no**.
No exported signing component or diagnostic signing API. Auto Orchestrator present;
normal-path forced failure default **off**, diagnostic activities absent from Friends
manifest and Friends is non-debuggable. OAuth embedded: **no**.

## Compatibility, final state and remaining gates

Update-compatible: **yes against retained installed-package evidence**, not a new
ADB observation. Prior attempt2 inventory records Redmi Note9Pro/Android12/arm64,
`0.1.18-field52-readiness`/52 and accepted beta signer. Same applicationId/certificate
plus54>52 (also54>public51/previous canary53) permits in-place update. Uninstall,
`pm clear`, reenrollment and cache injection: **not required / not performed**.
If the device has changed since that inventory, reverify during an authorized
physical step; this local gate did not access it.

Built and signed: canary54. Installed: last documented field52, **not rechecked**.
Distributed/invitation-page: last documented beta51, unchanged/unqueried here.
No public artifact verification or rollout is claimed. Production: last documented
attempt12 restricted rollback, ordinary Friends/AWG/TCP preserved; not contacted.

Future separately authorized deployment must follow the accepted
[owner-proof handoff](../../deploy/friends/restricted/OWNER_PROOF_HANDOFF.md):
old18084 retained → direct server fixtures → ingress switch → external server A–E
→ actual Friends prewarm real F/G → restricted READY → commit/retire old.
Owner failure: safe evidence, restore old ingress/prove normal routes, only then
stop candidate/rollback restricted stack. Keep monotonic security history.
This gate executes none of those operations and supplies no real-owner proof.

All pre-existing dirty/untracked work preserved. Index remains empty; only task-owned
documentation added on top of original doc deltas. No source/build fix commit;
starting and final HEAD unchanged. Push:no. Production changed:no. Redmi touched:no.
**STOP. Attempt13 and FIELD-1 not started.**
