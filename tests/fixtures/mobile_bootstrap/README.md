# Volgograd mobile bootstrap — exact beta95 derivative

The capsule is `state-client-build/mobile-bootstrap-20261020/`. Source baseline is
the verified installed95/A0 source inventory, not checkout main. Relevant94 and95
readiness Java/Python files are byte-identical; all twelve native libraries in96
equal95. Gateway/1011 and LEGACY64 remain unchanged. No production fault injection.

`prepare.py` verifies the two supplied exports, deduplicates events and creates an
isolated source copy once. Do not rerun it over an existing capsule. Product delta
is `beta95-to-beta96.patch`; apply only to that exact accepted95 source tree.
`build.py` seals the delta, reuses native95 and runs the affected/recovery JVM suites.
It binds the existing immutable Git metadata to the isolated work tree for the
existing provenance verifier; it neither creates a branch nor alters the accepted
source. Retained failed build logs must not be deleted or counted as passing.

Tests:
- `python3 -m unittest discover -s tests/fixtures/mobile_bootstrap -p 'test_*.py' -v`.
- `build.py`:175 JVM cases including valid/expired/denied cache, recovery and JSON
  export through the actual DiagnosticRing serializer.
- `network_fixture`: compile these stubs plus actual candidate ChatNetworkAndroid
  with the existing JDK, then run `com.familyconnect.app.NetworkProbe`. This checks
  per-call underlay selection/handoff/TUN exclusion without connecting any sockets;
  it is not Android kernel/Volgograd cellular acceptance.

`api_readback.py` runs read-only on authorized RU. It looks up only the specified
Support ID, never uses that ID for authorization and never copies device keys,
nonces or proof. Server receipt retention and journal gaps limit historical attribution.

`sign.py --check-only` verifies unsigned96, exact native reuse, package/alignment
and previous signer pin. `sign.py` uses the existing offline GUI vault workflow;
the owner must enter the vault password in the protected dialog, never chat/shell.
Do not start it unattended or leave a prompt waiting in the background. No signing
secret is persisted/exported. Signed destination is
`delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk`; successful signing receipt and
SHA25607a90f03… are retained. Do not sign again to reproduce an existing artifact.
Do not send or install the unsigned APK, and do not present beta95 as a bootstrap fix.

`upgrade.py check/install/identity-after` reuses the pinned existing guarded updater
with fresh pre/post identity comparison, never a stale identity snapshot. Owner update
95→96 completed14:48:37UTC while VPN/service were already absent; do not rerun install.
For any future update, a fresh version/signer/identity readback and ordinary manual
disconnect are prerequisites. Never replay a saved install intent, clear data,
downgrade or reactivate. Candidate must keep LEGACY64/128 OFF. Owner's manual Connect
and new96 READY/device proof are pending; server-row equality is not that proof.
One targeted tester cellular Connect+diagnostic export is useful only after that
ordinary same-key update; FIELD_PASS stays NOT_RUN until actual evidence arrives.
No new API, invitation, root enrollment, gateway restart, speed test or public push.

## beta113: both direct bootstrap paths unavailable

`check_blocked_paths.py` is a short, offline source-flow check of shipped113
(`d2882cde4c50b15085b925007c04c48f4de61bf0`), not a candidate APK or Android runtime.
Use the existing immutable113 source snapshot and cached JDK/dependencies:

```sh
python3 tests/fixtures/mobile_bootstrap/check_blocked_paths.py \
  --source-root state-client-build/beta113-field16/source \
  --tools /path/to/existing/resume-tools \
  --output state-client-build/beta113-field16/blocked-paths-new
```

The output directory must not exist; previous logs/receipts are never overwritten.
The runner pins the actual FriendsAccessAndroid, ChatCarrier, readiness route/protocol,
cache/bootstrap and release-disabled provisioning gate to113. Other Java dependencies
come from that snapshot, not current application source. Cached tools must contain
`jdk/bin/{java,javac}` and Gson2.13.2/JUnit4.13.2/Hamcrest1.3/BouncyCastle1.85.2 jars
under `gradle-home/caches/modules-2/files-2.1`; nothing is downloaded.

`blocked_paths/` replaces only Android/platform, storage/native and I/O seams:
HTTPS output throws a synthetic timeout; the RNS opener throws typed Unavailable.
Actual entrypoint code selects the fallback and subsequent failure. No real network,
device, keys, server registration, VPN or Telemost room is used. Generated identity
keys are test-only memory. The release provisioning gate remains disabled.
The modeled ConnectionService is off: the existing HTTPS_VPN branch requires an
already healthy VPN and is not an independent cold-start route under test here.

Seven cases distinguish uncached bootstrap, validated-cache fresh Connect versus
recovery, expired cache, activation, registration with/without invitation, and the
cache dependency of the actual service-only ChatCarrier entrypoint. The positive
cache case models an already validated bundle with controlled time: it does **not**
claim signature verification, encrypted Android storage or end-to-end connectivity.
The separate existing native113 checks cover real synthetic signatures/bindings:

```sh
cd state-client-build/beta113-field16/source/carrier
GOMAXPROCS=2 GOMEMLIMIT=384MiB GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off \
  GOCACHE="$TOOLS/go-cache" GOMODCACHE="$TOOLS/go-mod" \
  timeout 90s nice -n 10 "$TOOLS/go/bin/go" test -p 1 ./wholedevice \
  -run '^(TestCachedBootstrapCryptoDeadlinesAndRevocation|TestProductionDeliveryToExistingFamilyMaterial|TestProductionDeliveryRejectsBindingTrustExpiryBounds)$' \
  -count=1 -timeout=30s
```

Set `TOOLS` to the same existing absolute tools directory. These tests do not prove
Android networking, a real cryptographic-deadline crossing, or Telemost reachability.
See the [incident continuation](../../../docs/releases/2026-11-06-beta113-field16-bootstrap.md#dual-direct-path-failure)
for retained PASS/FAIL evidence and the exact missing product transition.
