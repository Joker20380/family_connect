# Existing users — Android private beta delivery

## Product-fix successor —19 October2026

The later owner-authorized beta87 product-fix task builds and signs code88 from
the retained87 source. No repeated enrollment or server cutover. Current signed
candidate, hashes, measured87 download and separate IPv6 limitations are recorded
in [beta87 product fix](2026-10-19-beta87-product-fix.md). Owner87→88 in-place install
and exact readback PASS11:55:55UTC; same-identity proof/READY, production DNS/HTTPS,
one correlated automatic88 recovery and bounded before/after comparison now recorded.
No speed improvement or overnight/productionIPv6 acceptance claimed.
This does not retroactively make the earlier
delivery/recovery acceptance PASS. Original87 files/receipts below remain immutable.

## Scope and current result

PARTIAL / DELIVERY_READY=NO — beta87 is signed and installed over86; same-identity
proof/import READY and initial production Android-TUN DNS/full HTTPS pass23:48UTC.
Actual87 automatic recovery after a later loss remains unverified.
Fresh export shows automatic restoration also succeeds after ordinary rotation,
followed by another carrier failure and terminal authenticated HELLO_RECEIVE/CLOSED_PIPE.
Beta87 fixes that specific recovery classification within existing retry/backoff limits;
125 local tests do not prove physical recovery or resolve repeated retry exhaustion.
Owner-authorized private update for existing registered identities;
not a new FIELD enrollment, PERF continuation, public release or updater change.
PERF-3B remains paused, PARTIAL/INCONCLUSIVE, with operation03 CLEANED.

## Exact baseline

Read-only18 October22:16UTC (19 October local):

- Root HEAD7656f2c65ea2928b71a928c12ee65a2f47f8ac4f; unrelated dirty work preserved.
- RU installed/running API SHA256
  `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed`, PID1018662.
- Both management source manifests
  `5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145`, all source pins match.
- NL management API9faaa1…4d1 differs from RU API; do not silently substitute main.
- NL loaded gateway
  `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`, PID2478832.
- Owner UI84/batch1/code84, `com.familyconnect.app.friends`; APK
  `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`;
  native `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
- Schema2: two CLEANED rows, zero unfinished; isolated canary03 inactive/PID0.
- 46 ordinary device records, two legacy grants; legacy admission still enabled.
  Counts are not evidence that46 devices are active/unrevoked or tested.
- Authority17 expiry19 October09:33:41UTC; leaf/CRL27124 expiry00:59:57UTC;
  same RU/NL directorye550f2…0a999 expiry01:00:13.589601455UTC.
- Preflight evidence private: `state-client-build/existing-users-beta-20261019/`.
  First read-only helper assumed symmetric RU/NL filenames and stopped on absent
  RU gateway.json / NL issuer.json; corrected role-specific reads succeeded.
  Neither invocation wrote production state.

## Necessary delta

1. Finish shared activated entitlement and revocation-aware management; legacy grant
   expiry must not define v2 entitlement. Preserve history, explicit revocations and floors.
2. Migrate finite operational delegation coherently; leaf/CRL remain bounded and
   auto-renewed, offline-root stays offline. Do not deploy the old experimental installer blindly.
3. Preserve UI84 identity/storage and native transport while fixing required refresh
   delivery. Current Friends readiness constructor binds HTTPS to a non-VPN network;
   an active VPN alone does not prove its refresh is tunneled.
4. Verify packages/tests/migration before production writes, use exact operator review
   for new offline-root material, then physical upgrade and private signed APK handoff.

## Delivery gates

APK/server/identity/lifecycle end-to-end acceptance is not yet asserted. Existing
source-only activation-v2 tests and presentation APK are not deployed delivery proof.
No private user identity, keys, database content or room credentials belong in this report.

## Preparation checkpoint —22:42UTC

- Beta85 built from retained UI84 plus the previously tested MESH presentation and
  narrow readiness routing changes. Unsigned APK `df5aedff5b2724e6eab2c54c1343d5bd3825ec68e3099bd53acc860b81f694f1`;
  source inventory `579c2b0334236fb8d2386330c70b80e5979593e32ab2f8c64f9b27132e500138`.
  117 JVM tests PASS; all12 native libraries byte-identical to accepted UI84.
- Readiness HTTPS uses the active, healthy application VPN only when connected;
  bootstrap otherwise remains on the underlay. A failed initial challenge may select
  the existing pinned RNS channel for the complete exchange. Ambiguous proof POSTs
  are not replayed on another path; authorization/TLS failures never trigger fallback.
  RNS carries only four allowlisted readiness paths to the fixed verified HTTPS API.
  No identity/enrollment, arbitrary destination, new transport, or TLS trust bypass.
- 3 real loopback RNS integration/regression tests PASS, including two independently
  activated synthetic identities without FIELD grants, concurrent requests, replay
  rejection and one revoked device while the other still succeeds. Not physical phones.
- Exact API overlay remains `e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7`;
  only restricted.py/support_ids.py differ from deployed12ca baseline. 110 selected
  API/management tests PASS,4 native-toolchain tests initially skipped; separate accepted
  native source validation passes for two identities at day0/2/77 with controlled clocks.
  First native fixture erroneously invoked real-wall-clock TLS Configuration with a
  synthetic future clock; corrected to the existing public-input validator clock contract.
- Additional management review found scheduled read-only inspection and operator CLI
  still selecting legacy expiry semantics. These are corrected before deployment.
  Final management source `c67332cfff9aeafd90690c13518f55a75ef9687ceadb464624263657ff005ff2`;
  capsule `b2243c4deb50d796bca8f8e7a09adfe162db4972661ec476f4fd5fc1d91c9f6f`.
- New forward-only file cutover preserves DB/history, snapshots privately, rejects
  conflicting partial writes and resumes exact committed intent.10 fault/resume tests
  PASS. Initial fixture permissions were intentionally rejected; fixture modes corrected,
  production guards not weakened. Full live cutover acceptance remains pending.
- Operational model:90-day same-key delegated CA, operator renewal planned by day60,
  advisory at14 days remaining, unchanged6h hard authority gate;4h leaf/CRL renewed at
 90min remaining. No per-user trial entitlement in v2. This is not indefinite autonomy;
  unavailable network paths and neglected offline-root maintenance still fail closed.
- Exact unsigned request `existing-users-beta-authority-20261019-01`, SHA256
  `04ff22eccfff5faa23a75ef89bef36c330c7d032e962b1c25a9aa1972b8da9af`; same-key CA
  `7c57ee5913d95431f83704fe4482ff6752dfbfc0269b13fb241b231916c37449`.
  Operator approved the exact local review and existing vault workflow. Bundle
  `a8d81a1d88447fa4accf430c4f4d44ac3633feb17f2643a8ca2179e289854f3e`
  independently verified against retained root and exact request/CA;17→18, scope/minimum
  revision unchanged. NOT_APPLIED at this checkpoint. Normal apply cutoff08:33:41UTC
 19 October includes one-hour reserve before predecessor expiry; revalidate before apply.
- Live public HTTPS certificate verified NL→RU, expires23 October00:09:12UTC.
  Existing cert-renew service result success/exit0; timer active, next19 October09:13UTC.
- Latest GitHub phase0 run39110172718 remains FAILURE (pytest and failover build);
  this is not a candidate CI PASS. No push/workflow rerun/public release performed.

Production API/management/gateway and Android are still unchanged at this checkpoint;
only protected staging files and an independently verified offline candidate exist.

## Applied control plane —22:50–23:08UTC

The earlier preparation checkpoint is historical. Cutover
`existing-users-beta-cutover-20261019-01` has FILES_COMMITTED receipts on RU/NL;
authority operation `existing-users-beta-authority-20261019-01` is COMMITTED.
Do not rerun either operation or restore the private DB snapshot.

- API `e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7` is actually
  loaded on RU/PID1296994. Both management manifests are `c67332cfff9aeafd90690c13518f55a75ef9687ceadb464624263657ff005ff2`.
  Capsule `b2243c4deb50d796bca8f8e7a09adfe162db4972661ec476f4fd5fc1d91c9f6f` contains
  only the exact-base cohort, not accumulated main. Source overlay is retained at
  `deploy/friends/restricted/existing-users-api.patch` (SHA256
  `6c5b931dae99ef8fa20582da26de9012d7f7ea3d61ea70a2e70f4c6b2c267355`).
- Explicit all_activated is installed on RU and in both node configurations. A
  read-only call to the installed shared predicate finds42 eligible registrations,
  including40 without legacy grants;4 denied. This does not mint proof or claim42
  physical connections.46 device rows and2 legacy grants remain; no fake grants.
- Authority18 retains issuer key/scope/minimum revision and expires16 January2027
  22:36:48UTC. Plan root maintenance by17 December22:36:48UTC;14-day advisory begins
  2 January. Root remained offline; exact input/bundle hashes above are unchanged.
- The authority-only transaction correctly retained still-valid leaf/CRL27124,
  expiring19 October00:59:57UTC; it did **not** prematurely rotate them. NL restarted
  through the approved controller, PID2547869, same accepted executable
  `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`.
  Strict served hostname/CA/ALPN http/1.1 and exact installed leaf match PASS;
  actual service account can read the profile. NRestarts0.
- New runtime publication RU/NL hash
  `06ae2d233b8dec1a6c17310a1636746d2570e33db96e202c49c9f162ad4371d8`, issued
  22:50:20.354617688UTC, matches on both nodes. Controller committed its bounded
  readiness acceptance; independent postcheck verifies publication/TLS. An additional
  bounded journal read exceeded15s: no independent READY log count is invented.
- RU API and previous directory/renewal schedules resumed. Scheduled controller
  verification returned NOOP/no writes/no restarts with90-day authority headroom.
  `approved_leaf_crl_schedule=true`; leaf/CRL eligibility begins23:29:57UTC, not a
  guaranteed publication time. Next automatic rotation not yet observed here.
  The old legacy sync timer stays inactive. External alert delivery remains unavailable.
- Schema2, two CLEANED rows and floors unchanged (canonical private history digest
  `de80640c5e0987f433f782a1a50cae095239c8922414977e669b8fc0d285765f`); zero unfinished
  handoffs, canary03 inactive. PERF-3B remains PARTIAL/INCONCLUSIVE and paused.

## RNS service refresh extension —failure retained, corrected

The existing pinned RNS control service now forwards only the four authenticated
readiness endpoints to the fixed verified HTTPS API. Identity/state and ordinary
registration paths are unchanged. No anonymous entitlement or arbitrary proxy.

Exact installed overlay: provider `599c7f8df997ad7729c4469d7508f848a98167f172a810f2705acaca53337ec8`,
runtime `ac552317c12a9d26c2cbac662e13599eb1b50b381cb6b8ceda66931daaf128ee`,
relay `2b43eba36c9ea7fe7795e869a2c5d1f0155ff01fc93bca044327222baa316242`.
Updated preview manifest `f060ffb2b7bdfaabd8896f6be7f25328358962f21c99004f5cddaff7b8d6b6e7`,
bundle ID `21108be48a64ce5105c5205a4cfe31c907b5ddcd6e7e1af7a5cc40dca0b8747b`.

First start was not successful acceptance: the existing launcher rejected the stale
source manifest with `preview member mismatch`; a socket probe got connection refused.
Systemd had performed7 automatic retries when observed. Only the affected RNS service
was stopped. The manifest updater now preserves/verifies every unrelated file, updates
only the three allowed members and recomputes the standard bundle hash; it never
disables the launcher verifier.32 focused tests PASS (first test fixture required
permission correction; safety guard retained). Exact launcher verify under fc-relay
passes before the corrected start. RNS PID2555431 active/running/NRestarts0; MESH
PID2547869 unchanged. These temporary RNS failures are not hidden as zero-impact work.

A pinned live RNS request with only `{}` reached the existing HTTPS API and returned
expected400 in2.014s. This verifies the service path, not a physical Android fallback
or authorization for a user. Prior local real-RNS tests cover two synthetic identities,
normal proof/fetch, replay and revoked-device isolation. Protected source backups and
both transaction receipts are retained; no RNS identity or private key was exported.

## Physical upgrade beta85 —installed, rejected for delivery

Signed candidate `0.1.18-beta85-existing-users`, code85, package
`com.familyconnect.app.friends`, SHA256
`a0349c108e8f01a71c664480d538eb0a9738efb1d99ca0b08901dfc5856b614a`, signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Owner disconnected normally; `adb install -r` succeeded23:09:13UTC. UID10283 remained,
installed APK hash matched and restricted native remained dd722e…0c23. All12 native
libraries matched UI84 before signing. No uninstall/data clear/profile import occurred.
This successful package upgrade is **not** delivery acceptance.

Owner reported failed Connect. Supplied export15 SHA256
`45e839ce4cdd6276ff41b6ee50b4305539c4ec19e63860baf1b3aa5cab406abd` confirms beta85,
CELLULAR, readiness INTERNAL_ERROR, bootstrap NOT_USABLE; native session/history empty.
At23:11:12UTC Connect → INTERNAL_ERROR → BOOTSTRAP_UNAVAILABLE, followed by cancellation.
RU has no beta85 readiness challenge/fetch/ACK; latest READY was beta84 before upgrade.

Concrete packaging defect: researchProvisioning selected the experimental
ProvisioningTestGate whose installed version check is hard-coded84. Beta85 therefore
throws RESEARCH_CONTRACT before network proof and before native startup. The export
exposes INTERNAL_ERROR, not the internal exception; source proves the failing predicate.
The117 selected JVM tests did not instantiate this Android/research gate. Their prior
PASS is not evidence against the observed defect. No server recovery/reset is indicated.

Correction in progress: separate privateBeta variant using the existing production
`provisioningDisabled` implementation, with PROVISIONING_TEST_SEAM=false; do not change
the literal84 to85 and retain a source-bound experimental clock/window in the product.
Add variant tests proving production readiness has no research-window prerequisite and
ProvisioningWindow is absent. Beta86 preserves native bytes, identities and security
validators. Failed beta85 APK/source/receipts remain immutable evidence, **DO NOT DISTRIBUTE**.

Known server-side Android observations before upgrade: code60×5,65×1,84×3;
37 records have no platform observation. These do not reveal SDK/ABI. Candidate scope
is Android12/API31+ and arm64-v8a; compatibility with unobserved devices is not assumed.

## Checkpoint before beta86 installation

SERVER_CONTROL_PLANE=APPLIED_AND_READ_BACK. PRIVATE_APK85=REJECTED_AFTER_PHYSICAL_FAILURE.
IDENTITY_PACKAGE_UPGRADE=PASS_FOR_UID_AND_PACKAGE; same-key post-upgrade proof is pending.
DELIVERY_READY=NO; FINAL_RESULT=PARTIAL. Immediate correction is the concrete Android
variant/gate defect, not a new PERF investigation or a request to re-register.
No public release/updater/catalog/push or automatic recipient delivery occurred.

## Beta86 correction, signing and installed readback —23:18UTC

The correction is built and installed, not merely proposed. The dedicated
`privateBeta` variant selects the existing production `provisioningDisabled`
implementation, with `PROVISIONING_TEST_SEAM=false`. It does not compile the
research code84 predicate or `ProvisioningWindow`. APK DEX inspection confirms
absence of `RESEARCH_CONTRACT` and the research window. This removes an unintended
experimental packaging prerequisite, not proof, expiry, revocation or native floor
validation. Two added variant tests exercise the production gate and exclude the
research window.119 JVM tests in17 selected suites pass; all12 native libraries are
byte-identical to UI84. The failed beta85 artifact and export are retained unchanged.

| Artifact | Exact identity |
| --- | --- |
| Version / package | `0.1.18-beta86-existing-users` /86 / `com.familyconnect.app.friends` |
| Supported target | Android12/API31+, arm64-v8a; target SDK35;16KiB alignment checked |
| Signed APK SHA256 | `1b7d73f9494f5836640dfde820cb9119b32d9855ad56873cee772641c0672530` |
| Unsigned APK SHA256 | `403c5c66abf13c1166338f7e39b3a3c6b4c654f4f90953a360436d96d9c776bc` |
| Existing signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Retained UI84 source inventory | `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790` |
| Beta86 source inventory | `9d5a337a9cb15c7c5e6c5d89c2d93355033f576ce4beff6e3ad8f0364ca8b585` |
| Minimal Android patch SHA256 | `c993a059f120338d87ba21974bf4ffde1c0cb32ba7e8dab26eac02b777d1582b` |
| Build/test receipt SHA256 | `4cb2c8dd2a81a1040c96ffefcaceb9d44b99eb59639544fd199624bb19b47078` |
| Signing receipt SHA256 | `22e05cf0ebaceaf8255a61d588a7b56ef29311efd5a31adbe9959b22c42d20d1` |
| In-place install receipt SHA256 | `f4729689a2e6f3ec2f507e000738f5d019bb21d59c5ef6537855ed4051cdb33d` |

Private signed file:
`state-client-build/existing-users-beta-20261019/delivery/FamilyConnect-0.1.18-beta86-existing-users.apk`.
Reproducible source overlay: `pilot/android-restricted/existing-users-beta86.patch`,
against the retained immutable UI84 source, not current main. Build driver:
`pilot/android-restricted/check_existing_users.py`; offline Gradle8.11.1 and the
retained JDK/Android tools, full source inventory and invocation in private
`android86-build/`. No new native compilation, root/signing key, public catalog or
release. Existing vault signing completed; no repeat signing is required.

At23:18:21.880281UTC `adb install -r` completed over failed beta85. Independently
read installed APK hash matches the signed candidate, UID remains10283, restricted
native remains `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
VPN was disconnected before installation. No uninstall, data clear, identity/floor
reset, invitation or profile import was performed. The actual physical sequence is
UI84→beta85→beta86, not a claimed direct physical UI84→beta86 test. Known code60/65
installations and a second independent remote phone have not been physically upgraded.

The fresh read-only identity check after installation did not yet find a beta86
READY ACK (`POST_UPGRADE_PROOF_IMPORT_ACK_NOT_YET_READY`). This is a pending
acceptance condition, not evidence of another Connect failure. Owner was asked only
to open the application and press Connect. Successful package installation and UID
preservation do not substitute for the same-key authenticated proof/import/ACK or
production MESH DNS/HTTPS. No additional live test/restart/recovery was initiated
in response to this pending result.

## Checkpoint after installation, before owner Connect

| Check | Result / boundary |
| --- | --- |
| Supplied failed export15 | Correlated beta85 failure before proof/native startup; exact hash preserved |
| Android packaging correction | PASS_LOCAL;119 selected JVM tests, actual privateBeta APK checked |
| Signed candidate / installed file | PASS; same package/signer, exact hash read back |
| Existing identity / Support ID after Connect | PENDING authenticated beta86 READY readback; no reset performed |
| Production MESH DNS / full HTTPS after upgrade | NOT_RUN; awaiting ordinary owner Connect |
| Shared existing-user access | APPLIED;42 eligible by installed predicate,40 without FIELD grant; not42 physical tests |
| Two identities / revocation / controlled-clock lifecycle | Local fixtures PASS within reported limits; not remote or90-day physical acceptance |
| Automatic renewal after deployment | Schedule active; last observed scheduled operation NOOP, next rotation not yet observed |
| Public distribution | NOT_RUN; no updater/catalog/push/release changes |
| DELIVERY_READY / FINAL_RESULT | NO / PARTIAL |

Immediate next action is the ordinary owner Connect, then existing same-identity
READY and bounded Android-TUN DNS/HTTPS readback. Do not reinstall, enroll, alter
transport, run PERF or replay authority recovery. The precise failure in export15
was the beta85 research-only installed-version gate; its fix is installed but a
successful end-to-end connection must still be observed before delivery acceptance.

## Physical owner acceptance —23:23UTC

The owner connected normally and independently reported success. RU readback at
23:23:37UTC contains beta86 challenge→fetch→native import ACK with result READY,
PRESENT_VALID provisioning/bootstrap, orchestrator usable, failure NONE, revision9
and minimum CRL27124. The authenticated device record, public/transport-key bindings
and Support ID match the protected pre-upgrade digest. Exactly one owner device
record remains; total device46/grant2 counts are unchanged. No new enrollment or
manual entitlement was created. The support-export metadata still names beta85
because that was the last support export; the actual READY ACK explicitly names86.
These are different observations, not a claimed installation mismatch.

Bounded production probe at23:23:18UTC uses the previously verified Android system
HTTPS client through installed UI84-derived TUN, not laptop networking or a new
native Telemost CLI. UID2000 is included in the actual VPN UID range0–99999;
route readback uses tun1 and DNS10.79.0.1. One full HTTPS response from the approved
Cloudflare trace endpoint returned HTTP/1.1 200, TLS verification0,215bytes,
identity encoding, with no retry. Total request time5.160334s, DNS timing1.595128s,
TTFB5.159979s. These are request timings, **not** network RTT or throughput measurements.
Observed body SHA256 `2e41fbf3829d2b849af7b8c1a7b036c3f3f50e3d52b6de595944ef123fdb7f10`;
this is not an independent origin digest.

NL process2547869 was verified against the accepted executable SHA256 before the
probe.29 bounded socket samples attribute the HTTPS destination to that production
PID; NL exit IP alone was not used for attribution. Sampler exits0, response complete,
phone temporary files removed. The reused fixture's receipt retains its historical
`purpose=post-abort production control only; no bulk baseline` text; in this task it
is explicitly reused only for post-upgrade production acceptance. No abort, canary,
bulk or performance claim is implied by that inherited label.

Protected receipts:
- `identity-after.json` SHA256 `35dd2ffb23a1d07cb8c9b871bedb275c13c548e317e5a14132fe62fe3915b60f`.
- `acceptance-baseline.json` SHA256 `ae1824fa9a3074736cde3de65018af5c76cd3d02fd0a308a66d8ffb7147d5440`.
- `owner-https-acceptance/result.json` SHA256 `1d5aa80ff585c87b93c0267905107738e926d801aedabf05b65d2a69488a6266`.

IDENTITY_UPGRADE=PASS; OWNER_MESH_DNS_HTTPS=PASS. The former immediate beta85
packaging blocker is corrected and physically verified. Additional remote phones,
full operator-blocked-network fallback and months of physical uptime remain NOT_RUN.
No new grant or invitation is needed for existing eligible identities. A bounded
read-only observer now watches the normal scheduled leaf/CRL cycle; it does not
invoke controller, restart any unit, alter timers or write production state.

## First automatic rotation —server PASS, client recovery NOT_ACCEPTED

The bounded observer completed; no background process is left waiting. Normal
operation `scheduled-1792366211-15073bd3bff3dcdb` is COMMITTED, commit_decided=true,
first_cause=null; renewal unit success/exit0. Readback at23:30:39UTC observes CRL
27124→27125. Fresh leaf/CRL expire19 October03:30:15UTC; authority18/scope unchanged.
Controller transaction SHA256 `113dd7ca443c70760583e4a1de54f72fa8b27e220c56cd2d128c020df3c2906e`.
Observer receipt SHA256 `0dcbdcc3a698d10b32b8dee8b84642506e7d0f84bf448d2e014d317ca10bb47e`.

Independent RU/NL readback verifies same CRL27125, authority18 and directory SHA256
`065f365eecd5c0c7fcb68225a391467855dbd61150db5000f23ef88a717a3a1f`, issued
23:30:31.604211548UTC, expires03:30:28.010279691UTC. NL PID2573049 runs the accepted
unchanged binary, NRestarts0. Served hostname/CA/ALPN and exact installed leaf match,
service-account readability and all source pins pass. Handoffs remain CLEANED.
Readback receipt SHA256 `20579780022033e95c9f799601a96979d30864bed5dfd4466172fa3c2205c12c`.
This was the normal approved schedule, not an agent-forced controller run/restart.

At23:31:03UTC a beta86 authenticated import ACK reports READY with CRL27125 and
revision9. Same identity/key bindings and Support ID persist; application PID968
remains. No additional manual Connect was requested or invoked by the agent. This
proves fresh material delivery/import, **not** native session or data-path restoration.

The first post-rotation probe fails before HTTP with curl6, `Could not resolve host`,
zero body bytes,6.002723s. The reused fixture then raises because it tries to read
the nonexistent body. That helper exception is subsequent to DNS failure, not its
cause; failed stdout/stderr and bounded socket samples are preserved. After server
readback and the fresh import were confirmed, one separately identified control
probe also fails DNS, zero bytes,5.947978s. No more requests were sent. Both helper
temporary directories were explicitly cleaned; neither failure is counted as HTTPS
or recovered-connection PASS. The first failure receipt SHA256 is
`e4733662f3d8b9ac3877c5b01d17ff9c17606974195fe757dd2a58ebec71f9fc`.

An additional journal read was restricted to the exact NL unit,23:30–23:35UTC,
maximum120 entries; it exceeded the18s bound. It was not repeated. No server
authentication/root-cause statement is inferred from unavailable journal data.

### Immediate blocker and required evidence

Initial beta85 packaging failure is fixed. The new observed blocker is that the
application data path has not passed after normal credential rotation, despite
successful fresh provisioning. Native recovery stage/selected session is missing:
READY alone cannot distinguish media recovery, Family session recovery or DNS-path
failure. No speculative transport/credential change or manual reconnect was used
to hide this result. The owner was asked for **Settings → Send diagnostics** from
the existing app, without disconnect/reconnect. This one export is the next required
input; no new diagnostic build, performance experiment or enrollment is needed.

| Final field | Result |
| --- | --- |
| SIGNED_PRIVATE_APK | Beta86 available at exact path/hash above; candidate, do not distribute yet |
| INITIAL_UPGRADE_AND_IDENTITY | PASS on owner; no duplicate device/enrollment/reset |
| INITIAL_PRODUCTION_DNS_HTTPS | PASS with actual production PID attribution |
| ALL_ACTIVATED_SERVER | APPLIED; local two-identity/revocation checks and installed predicate, not two remote phones |
| AUTOMATIC_SERVER_RENEWAL | PASS for one actual committed rotation and independent installed/served readback |
| POST_ROTATION_CLIENT_IMPORT | READY27125 with existing identity |
| POST_ROTATION_DATA_PATH | FAIL_AT_DNS twice; exact native recovery stage UNKNOWN |
| REMOTE_FIELD / LONG_PHYSICAL_SOAK | NOT_RUN |
| DELIVERY_READY / FINAL_RESULT | NO / PARTIAL |

No canary/PERF, public release/updater/catalog, commit/push, key/floor reset, extra
registration or uncontrolled retry was performed. The existing connected UI state
must not be reported as restored Internet access without a successful data-path check.

## Supplied post-rotation export —causal boundary corrected

Owner supplied the existing diagnostics export without any new diagnostic build.
Original SHA256 `66418a629bbd20ecee46cc699769aa608c4dbbfebe154f60f81d92127b57bab2`,
retained privately as `postrotation-export.json`. It identifies beta86, API31,
CELLULAR, one continuous orchestrator connection with three native session histories
and final startup attempt4. Public reporting omits Support/connection/session IDs.

| Device UTC | Observation |
| --- | --- |
| 23:23:15–16 | Initial Family authentication, broker descriptor, SESSION_READY and CONNECTED |
| 23:26:12.370 | First established-session failure: CARRIER/RELIABLE_RETRY_EXHAUSTED, before the scheduled rotation |
| 23:26:17–38 | Automatic restoration; fresh READY, Family/broker/session success and CONNECTED again |
| 23:30:27.930 | Second established-session retry exhaustion; near the scheduled publication cycle |
| 23:31:03 | Fresh READY27125 |
| 23:31:33.499–646 | Family authentication, descriptor and SESSION_READY; restoration reaches CONNECTED |
| 23:32:31.085 | Third established-session retry exhaustion |
| 23:33:07–22 | Fourth native startup; fresh READY and Family authentication, then HELLO_RECEIVE/CLOSED_PIPE |
| 23:33:22.245 | Orchestrator becomes FAILED/BOOTSTRAP_UNAVAILABLE |
| 23:34:24–25 | Later cancellation/disconnect; not the cause of preceding startup failure |

This corrects the pending assumption that ordinary renewal alone prevented recovery:
the client **did restore a session after renewal**, and one earlier failure preceded
renewal. The two external DNS controls did not prove a standalone resolver defect;
they occurred during this unstable/recovering interval. No exact cross-node latency
or causality is derived from independently timestamped server/device observations.

Final startup observation: point FAMILY_RECEIVE, CLOSED_PIPE, context LIVE,
stop_at_observation NONE, elapsed14939ms; cleanup begins14944ms. The matching existing
bootstrap exchange records `family_authenticated=true`. HELLO was never received,
so no descriptor or application session was established in attempt4. No credential,
floor, identity or explicit authorization rejection is reported. The three earlier
session traces preserve first cause RELIABLE_RETRY_EXHAUSTED; later Family close
events must not replace it. Trace/archive drops are nonzero for some sessions, so
complete packet histories and an external carrier cause are not claimed.

Read-only current gateway inspection confirms PID2573049/accepted binary with peer
and ownership diagnostics **disabled**. No collector was enabled and no restart was
performed. Seed invocation duration4h and seed-rotate-after3h are existing settings;
neither proves the reason for a few-minute established-session loss. Exact accepted
gateway source is the sealed `transport-write-batching-1/gateway-source/carrier`
inventory aeeb6755…d9483, not current main. Its bootstrap server authorizes and may
wait for preceding lease cleanup before sending HELLO. Without its exchange result,
the reason the peer closed before HELLO remains UNKNOWN; device_busy is not asserted.

Concrete client recovery limitation: beta86 `RestrictedRecovery.bootstrapRetryable`
accepts only STARTUP_CALLER/SEED_ADMISSION deadline evidence. The authenticated
FAMILY_RECEIVE/HELLO_RECEIVE closed pipe is therefore terminal BOOTSTRAP_UNAVAILABLE,
even during requested restoration. A narrow beta87 candidate is being tested: permit
only this correlated, authenticated, pre-cancellation HELLO closed pipe to use the
**existing** two-recovery limit and30/60s backoff. It does not accept invalid material,
change any retry constant, increase rights, bypass authorization, or fix/prove the
cause of ReliableStream exhaustion. Fresh proof/import still precedes each attempt.
Exact matching exchange, complete startup, unchanged attempt, no dropped evidence,
LIVE context and no earlier stop are required. Explicit auth/protocol/certificate
failure, cancellation and uncorrelated evidence stay terminal. No beta87 signing,
installation or production change has occurred at this checkpoint.

### Beta87 tested, signed and installed — 18 October23:46UTC / 19 October local

The exact86 behavior fails the new synthetic authenticated-closure reproducer
(three expected failures retained);87 passes all125 JVM tests in18 suites. Tests
cover the positive evidence predicate, missing/conflicting/dropped authentication,
wrong stage/attempt, explicit security/protocol failures, cancellation/local stop,
successful bounded restoration and exhaustion of the unchanged two-recovery budget.
The sealed source/build receipts and rejected86 test output remain private evidence.
No native, transport window/RTO/pacing, server binary or credentials were changed.

| Artifact | SHA256 / result |
|---|---|
| Source inventory87 | `5e78b4612ae5a648a19337d6b89292c37023ce1b720f8c2da6e1fdde3b1ebaf0` |
| UI84→87 overlay | `30dfb2895452c1f2b04a60587568cf4af09a3041ded4c872c092d29b3896c765` |
| Build receipt87 | `999fa9a145a1cf59759a486b01ce27bed0fa9a82c016768b5c8ada771d2053d9` |
| Unsigned APK87 | `d0e5ca6abb281730b3ddd17ff7bd3259420c27b2dfb6cfffb33babead3a0c7a1` |
| Signed APK87 | `2a45f9672bdf76de8358859be58ad4bbf37c92ffd0a551693690b9f19e604c11` |
| Existing signer certificate | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Signing receipt87 | `fb051ed26f09e3bef18b11155f298c31f4d72cdf087170efa7b5fb123b0a0f04` |
| In-place install receipt87 | `faacd02c750b906bb3ef0b1c406d8ebd2c954018b594f2427e1f4d2e60932d51` |

Existing vault signing was used with protected local operator input, no key export,
no new signer and no publication. Independent apksigner verification,16KiB zip
alignment, absence of research gate in DEX and byte equality of all12 native
libraries with UI84 passed. Same package, code87, Android12+/arm64-v8a only.

Read-only preinstall23:46:31 found exact86/native, no active VPN/service. One
`adb install -r` completed23:46:43.098600UTC; installed hash is exact87, UID10283 and
restricted native hash unchanged. No uninstall/data clearing or identity migration.
This is package preservation, not yet an87 authenticated identity/network acceptance.
Owner was asked to open Family Connect and press the ordinary Connect button.
No screen automation, forced renewal/reconnect, canary or throughput tests.

Current gate: beta87 proof/import READY and a bounded production Android-TUN
DNS/HTTPS check, followed by evidence of actual automatic recovery when applicable.
Do not substitute initial Connect or125 local tests for that recovery evidence.
Preserve failed86 probes and originals; do not downgrade/reset the phone or restore
security state to seek a PASS. Any correction continues forward with the same signer,
existing identity and monotonic state. Server cutover/authority is already committed
and must not be repeated. DELIVERY_READY=NO / PARTIAL at this checkpoint.

### Beta87 owner initial connection — 23:48UTC

Owner confirms ordinary Connect. Read-only RU query23:48:29 verifies beta87 proof,
fetch and native import ACK READY/PRESENT_VALID, revision9/CRL27125; same existing
device row, identity/transport-key bindings and Support ID.46 devices/two legacy
grants/two CLEANED operations remain. The support metadata version still says85;
it is not installed-version evidence. The authenticated ACK explicitly reports87,
and independent ADB package/hash readback proves87 is installed.

One short Android-TUN probe23:48:55.524600UTC, no bulk/retry: DNS success, full
HTTP/1.1 response200, TLS verification0,216body bytes, identity encoding,3.102376s
full request. This is HTTPS response time, not RTT/goodput acceptance. UID2000 is
covered by VPN UID0–99999, tun1 and MESH DNS10.79.0.1;17 matching origin sockets
belong to NL production PID2573049. Loaded accepted binary matches, active and
NRestarts0. Probe temp files removed;35s read-only socket sampler exits0.

| Evidence | SHA256 |
|---|---|
| Beta87 identity/READY readback | `e36ede51bcac5d3bfc06f32c3e21a2caf42ed82a9ba0fc04a368b17d05746dab` |
| Beta87 process baseline | `da43159e3ad1499eab9342a071e8e7bd60baf9be172e3cee54a33313b8618736` |
| Beta87 TUN DNS/HTTPS result | `fe85bb833e4f8468edfc62f6c3533e5ca0e79852d6673e3ebccf96c134ee1804` |
| Observed response body, not independent origin digest | `9f400accc101f7fca29020c67c1a09e08fc6998ea473d7be11120cd95bde2f06` |

Only the local measurement helper was adapted to87/unique receipt paths and made
to preserve a missing response body as a failed probe rather than raising while
reading it. Previous failed86 receipts were not overwritten. No gateway/RNS/API
restart, credentials, transport changes, canary or forced interruption in this step.

INITIAL_OWNER_ACCEPTANCE=PASS; IDENTITY_PRESERVATION=PASS;
AUTOMATIC_RECOVERY_BETA87=NOT_OBSERVED; DELIVERY_READY=NO; FINAL_RESULT=PARTIAL.
Immediate remaining gate is evidence of87 restoring an ordinary session after a
natural failure without another user Connect; no artificial failure or background
test is armed. A successful initial Connect does not prove this. Use the existing
diagnostic export if that event occurs, rather than a new diagnostic build. Second
remote phone and months-long physical operation remain NOT_RUN. Underlying repeated
retry-exhaustion cause stays UNKNOWN, not a claimed speed/security/provider defect.
