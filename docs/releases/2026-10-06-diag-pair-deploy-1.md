# DIAG-PAIR-DEPLOY-1 — PASS

2026-10-06. Owner-only deployment of the accepted sealed diagnostic pair.
This is a short no-fault baseline, not OWNER-CONTROLLED-LOSS-1 or soak.
[Accepted freeze](2026-10-06-normal-native-provenance-1.md) remains unchanged.

## Sealed manifest and installed identity

Commit `5327deb414ae8aa77ce2f9490fd99c9485eba740`, tag `diag-owner-beta66-ci2`.
Manifest SHA256 `8af6f13348c5c7d6b095eb6003f04a3ae99f100837ef685b53295cc563acbc77`.
Manifest/artifact/source-input/retained-receipt integrity checked before runtime changes.
No accepted APK/JNI/gateway was rebuilt, substituted or relabeled.

| Accepted and runtime-verified member | SHA256 |
| --- | --- |
| Signed beta66 APK, pulled back after install | e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81 |
| Existing single signer | 67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a |
| Restricted JNI inside installed APK | e433a4910d218065bd4a217b1c87aaad1698d3f4716179b7559248d41b49c792 |
| Normal libfc-awg.so inside installed APK | 44f3e72f658095a98a1b738dfcb0409a99a7be7739653c95423a023cca7f4563 |
| Loaded NL gateway | 6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec |

Package remains `com.familyconnect.app.friends`, arm64-v8a only, non-debuggable,
versionName0.1.18-beta66/versionCode66. Installed assets both identify the frozen
revision. Exact installed-byte equality covers all additional accepted Python/runtime
libraries too, not only the two Family libraries. Merged APK contains OwnerFaultReceiver
protected by android.permission.DUMP. Fault capability schema1/build tagfc_owner_diagnostic.

## Owner pre/post preservation

Read-only package preflight06:58:06UTC: beta65/code65, UID10283, inode601521,
first install2026-09-19 17:30:26, same package, same accepted signer, non-debuggable.
Pulled beta65 SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`.
Wi-Fi0/mobile-data1; validated default cellular LTE, no network-setting change.
Preflight owner Support FC-4D8Q-REEG admitted/non-revoked, grant revision3;
stored historical READY was expired and was not reused as acceptance.

Existing signed registration-snapshot instrumentation captured encrypted-file and
enrollment fingerprints privately, including successful identity/readiness decryption.
Product upgrade used only in-place `adb install -r`; no owner uninstall, data clear,
rename, identity reset, re-enrollment, Support regeneration or forced reactivation.
Post-install, post-first ordinary startup and post-baseline/restart checks preserve
UID10283, inode601521, first-install identity, exact encrypted identity fingerprint,
enrollment fingerprint, activation and Support ID. Configuration/readiness encrypted
files were initially retained; later readiness updates are expected, not data loss.
Fresh authenticated owner fetch also proves the preserved identity remains usable.

## NL gateway and rollback preparation

Before: PID902401/NRestarts2, binary and /proc/PID/exe hash
`7c6e1e11208e167309cbe83dac0f5f1f1bb306f4e41628180367aa6fa5e9aa50`.
Listener18444 present, zero established control connections at preflight.
The pre-existing restart count is not attributed to this task.
Unit: family-connect-restricted-bootstrap.service; executable
`/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker`.
Service user family-restricted, effective group family-restricted; working directory
`/opt/apps/family_connect/friends-restricted`.

Old executable and unit snapshot saved before replacement in
`/opt/apps/family_connect/restricted-materials-stage-20261001/diag-pair-deploy-1-20261006/`.
`bootstrap-broker.previous` freshly verified as7c6e1e11 (full hash above).
Exact accepted executable staged, guarded by old/new hashes, installed atomically
with original ownership/mode, service restarted. Initial PID999491 then credential
reload PID1000816, NRestarts0, active/listening. Actual /proc/PID/exe hashes verified,
including after renewal. Accepted embedded revision5327deb4, fc_owner_diagnostic,
vcs.modified=false; loaded-byte equality ties this metadata to the live process.
Unit/settings SHA256 unchanged:
`b9012b159073ddedc2fcad12a31f4a4bc9175ff860c0ac15a9d5ec3ab9386199`.
No transport, retry/RTO/pacing, Family TLS/Mux/TUN code/config changes.

## JIT credentials and RU/NL consistency

Used the existing [credential publication runbook](../../deploy/friends/restricted/GATEWAY_RENEWAL.md)
and accepted bounded renewal operators, with current pinned clock-skew HTTP/sync
archives, issuer5 and frozen operator source. Historical artifact references were
replaced by sealed-manifest verification, not by relaxed security checks. No issuer
rotation or new grant/admission; owner3/tester1 grants, identities and ordinary RU
services unchanged. Temporary sync timer serialization restored on exit.
Native positive/negative authority validation PASS; ownership-aware atomic publication
PASS (UID/GID979,0600, actual service-readable readback). Authoritative bootstrap
reload PASS, served certificate readback and35s service stability PASS.

| Security bound | Verified UTC expiry |
| --- | --- |
| Actually served gateway leaf | 2026-10-06 11:03:25 |
| Issuer5 and existing grants | 2026-10-06 13:51:23 |
| Latest sampled CRL8593 | 2026-10-06 11:11:12 |
| Directory generation | issued07:03:34.867854224; expires11:03:32.444464641 |
| Owner READY delivery | 2026-10-06 11:03:32 |

Leaf/issuer direct signature, hostnamegateway.family-connect.test, signed CRL and
revision floors verified. The TLS listener serves one leaf matching the profile;
issuer is verified from the profile, not falsely counted as a second served cert.
Served leaf fingerprint849e0fce6f5d53c41cb55b8d41a62facf0afcca8aaa58fad6e5ca4f00b165656.
At07:11:39UTC, effective minimum bound is the leaf11:03:25UTC: **13905seconds
(3h51m45s)** headroom. The delivery's seven-second-later ceiling does not extend
the effective native/security bound. Recheck this live bound before the later test.

RU/NL exact directory SHA256, checked after renewal and again after smoke:
`32b8b5afe109b98a6daf378c9186f8993c9bd852f846ef5f2b019063fff33f23`.
Both version1, same issued_at/expires_at. Native authority validation, unchanged
admission/grants, matching directory and fresh beta66 authenticated native import
establish compatible state; no stale RU snapshot or split-brain observed. CRL floor
advances normally through sync (READY minimum8590 <= final gateway8593).

## Fresh readiness

Ordinary foreground launch, no cache clear/forced refresh/security bypass:
authenticated fetch07:04:57UTC → native READY07:04:57 → ACK07:04:57, beta66.
Later ordinary post-restart flow: fetch07:10:11 → READY07:11:11 → ACK07:11:12UTC.
ResultREADY, provisioning/bootstrapPRESENT_VALID, orchestrator_usabletrue,
failure_reasonNONE; grant revision3, delivery expires11:03:32UTC.
These are new owner receipts, not the historical beta65 ACK. No tester request,
contact or test was initiated; its existing database state was only read.

## Cellular baseline and fault status

A separate signed instrumentation helper was compiled against the clean frozen
classes; only the test APK was built, never the sealed product APK/JNI/gateway.
Initial sandbox socket/offline dependency failures were infrastructure-only; helper
build then passed with pinned Android test dependencies. Only the explicit baseline
test ran; no synthetic-loss, denial, policy override or diagnostic-export fixture ran.

Two short real RestrictedTunnelEngine/AutomaticVpnOwner sessions over cellular,
using accepted native Telemost transport and normally imported owner readiness:
DNSexample.com PASS, HTTPS200/body PASS, independent TCP80 request/response PASS,
healthy samples PASS in each session, intentional normal disconnect/cleanup PASS,
second-session reconnect PASS. No DATA was intentionally dropped. The helper
selects the existing restricted engine directly; it does not alter orchestrator
policy or impersonate successful Auto fallback. No retry exhaustion or cleanup loop
was observed during this bounded smoke; this is not a soak guarantee.
Normal app force-stop/relaunch PASS; final identity/enrollment snapshot PASS.

Each active session before and after traffic reports:
schema1, stateDISARMED, armedfalse, consumedfalse, count0, no generation/sequence.
Target field is the static capability nameoutbound_data_attempt0_after_established,
not a pending armed target. Reconnect starts equally DISARMED. After cleanup and
app restart, status returns UNAVAILABLE, empty target, armedfalse/consumedfalse/count0:
the recorder is session-scoped and absent while idle. Do not mislabel idle UNAVAILABLE
as a failed build or as a literal DISARMED response. Active operational DISARMED was
proven; no stale persisted arm state and no arm/disarm command was sent.
Temporary .friends.test instrumentation removed; owner app/data retained and
ordinary app left foreground, disconnected and unarmed.

## Rollback and next gate

Gateway rollback is prepared, not executed: stop only
family-connect-restricted-bootstrap.service; verify previous7c6e1e11 hash; copy
bootstrap-broker.previous with preserved ownership/mode to an exclusive sibling
of the live executable, atomically rename, start the unit, and verify /proc/PID/exe,
listener, current credential validity and RU/NL directory propagation before use.
Do NOT restore the expired pre-renewal gateway.json or lower CRL/revision floors.

Verified beta65 remains locally available as diag-pair-deploy-1/installed-before.apk;
public beta65 bytes were not modified. A non-debuggable code66→65 downgrade cannot
be assumed install-compatible even with the same signer: no `-d` bypass, uninstall
or data clear is authorized. Any necessary APK recovery needs a separately accepted
forward-version compatible build or an explicitly reviewed recovery plan. No rollback
was performed while the deployed pair is healthy.

DIAG-PAIR-DEPLOY-1 PASS. OWNER-CONTROLLED-LOSS-1 is allowed as a **separate** task
after fresh READY/headroom/DISARMED preflight, not armed or executed here. No fault
injection, impairment, soak, Krasnodar FIELD, WB/VK or public beta66 publication.
Default/catalog/invitation channels and sealed pair bytes remain unchanged.
Protected evidence: `state-client-build/field65-export16/diag-pair-deploy-1/`;
sealed pair manifest remains under diag-source-freeze-1/immutable-ownerDiagnostic-beta66/.
