# PINNED-EVIDENCE-DEPLOY-1 — PASS / owner-only beta67 deployed

Subsequent physical-task preflight discovered a stronger evidence-contract gap:
[OWNER-PINNED-EVIDENCE-1](2026-10-06-owner-pinned-evidence-1.md) is PARTIAL/STOP before
arming. This does not invalidate installation/control availability acceptance here,
but supersedes the conclusion that full callback-level physical proof is unblocked.
No physical attempt has been consumed; receiver Reliable/ACK pinning is missing.

## Authorized continuation and final acceptance — 06.10 15:21–16:05UTC

Continued the existing deployment after AUTHORITY-RENEWAL-1 PASS and explicit
authorization for **only** FC_DIAGNOSTIC_CONTROL_DIR plus a dedicated service-owned
0700 directory. Prior attempts and their failures below remain historical evidence.
No physical selected-retry experiment, intentional DATA drop, impairment, soak,
fault arm, correlation prearm/bind, retry/RTO/pacing changes, or reverse DATA104 fix.

### Immutable pair and Android preservation

Manifest SHA256 `98dabfa38cb2cd437b5ec45700e936da3ae0b94ef47f11b8904a90faa472fc77`
and all seven members checked again before install; repeated full check15:36:14UTC.
Frozen revision `ffd27988468fba427aaba6213b862dca01020972`, CI-only tag
`diag-owner-beta67-ci1`; no product artifact rebuild/substitution.
Correlation/control schema1, prearm/descriptor pinned-correlation-v1, telemetry
public-beta66-golden-v1 remain unchanged.

- Intended ADB Redmi31ce63ba authorized. Preflight beta66/code66 exact APK
  `e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81`.
- Installed beta67/code67 with `adb install -r`; package remains
  `com.familyconnect.app.friends`. Pulled installed APK SHA256
  `8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f`.
- Signer unchanged `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Embedded restricted JNI `4a7b6bc17c8e7cb704d3cdfdcfc9aec9333dd17d5d17ba46dbe5d435f805fa81`;
  AWG `15f1da2ea95957cdba28806b23b3ca7d698b35b2d8cb835d4ce97285270a6e6a`.
  Pulled manifest/ABI checks: non-debuggable, arm64-v8a only, DUMP-protected receiver.
- UID10283, CE data inode601521, data directory and firstInstallTime
  `2026-09-19 17:30:26` preserved. Support FC-4D8Q-REEG, exact encrypted identity
  fingerprint and successful decryption, enrollment fingerprint and activation
  unchanged at preflight, postinstall, post-first-start and final post-restart snapshot.
  Admission non-revoked/revision3; no re-enrollment or identity recreation.
- Temporary separately signed instrumentation/probe APKs were built for normal
  checks only, not product APK/JNI/gateway rebuilds. Both helper packages removed.
  Owner package was never uninstalled, data-cleared or downgraded.

### Gateway deployment and strictly scoped configuration diff

NL service `family-connect-restricted-bootstrap.service`, executable
`/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker`.
Preflight beta66 hash
`6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec`,
revision5327deb414ae8aa77ce2f9490fd99c9485eba740; no established18444 sessions.
Preflight PID/NRestarts and exact effective/static settings retained in local
`resume4-gateway-preflight.json` and server backup described below.

Final `/proc/1266691/exe` SHA256
`c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143`;
embedded revision `ffd27988468fba427aaba6213b862dca01020972`, vcs.modified=false.
PID1266691, NRestarts0, service active, listener18444 verified; not filename-based acceptance.

The complete static unit diff is the new drop-in
`/etc/systemd/system/family-connect-restricted-bootstrap.service.d/90-owner-diagnostic-control.conf`:

```ini
[Service]
Environment=FC_DIAGNOSTIC_CONTROL_DIR=diag67
```

This relative directory resolves under the **unchanged** WorkingDirectory to
`/opt/apps/family_connect/friends-restricted/diag67`, UID/GID979, mode0700.
The Unix bind pathname is76 bytes, avoiding Linux sockaddr_un length limits.
Raw `systemctl cat` equals original plus exactly this drop-in. Effective Environment
equals original plus this variable; all other compared service settings identical,
including User/Group, command argv/path, WorkingDirectory, Restart, capabilities,
ProtectSystem=strict and ReadWritePaths. Volatile ExecStart process/start-time fields
were excluded from configuration comparison; no executable command change hidden.
Original static config SHA256
`b9012b159073ddedc2fcad12a31f4a4bc9175ff860c0ac15a9d5ec3ab9386199`;
final `3249833ca83f2f38d10f5ca9e2f22c6c0e436f94de18e7db60e2d60cdd2daec7`.

Retained intermediate failures: initial absolute directory produced138-byte socket
path (too long); shorter `/opt/apps/family_connect/diag67` was outside existing
ReadWritePaths and could not create sockets under ProtectSystem=strict. Both were
corrected **only by changing the authorized variable/dedicated directory**; empty
intermediate directories removed. No sandbox permission or other service setting
was changed. Final relative-path runtime proof below supersedes failed monitors.

### Credentials, RU/NL and fresh readiness

Final served-chain verification at `2026-10-06T16:01:28.541733Z`:

- Actual served leaf DER SHA256
  `a2c4324401fbfb2374a61c1404caa0d264305533496394a17c641c4549940ff4`,
  notBefore14:47:25UTC, notAfter18:47:30UTC; matches loaded profile. Signature,
  accepted authority and hostname/service binding verified by accepted verifier.
- Issuer6 and grants owner3/tester1 valid through07.10 14:45:31UTC; minimum revision1,
  admission/revocation and identity-binding fingerprints unchanged. No weakened checks.
- RU/NL signed CRL9459 exact SHA256
  `8e42c948ddc4d62e96cf1c02616b5b86aae22577812bb451bbc49a76cb39aa13`,
  notBefore16:01:13UTC / expiry20:01:13UTC. Ordinary CRL sync continues monotonically.
- RU/NL exact directory generation `2026-10-06T15:53:17.577994843Z`, SHA256
  `0c160f8b9ada7888ae1bd7f2000b0c0deee08527a10393a5e96c2fb97bb6bff9`;
  directory expiry19:53:15.410360137UTC. No stale RU snapshot/split-brain.
- Effective bound is the earlier served leaf expiry **18:47:30UTC**, not the later
  directory/profile readiness receipt expiry. Measured headroom **9961 seconds
  (2h46m01s)**; sufficient for completed deployment/short baseline, not a perpetual
  authorization for a later experiment.
- After final gateway configuration, ordinary authenticated challenge15:59:15UTC,
  fetch/native READY15:59:16UTC, ACK15:59:17UTC. App beta67/code67, PRESENT_VALID
  provisioning/bootstrap, failureNONE, orchestrator_usable=true, admission3 non-revoked.
  Receipt expiry19:53:15UTC does **not** extend the18:47:30UTC effective parent bound.
- After final snapshot/helper removal, ordinary app restart restored valid READY
  and ACK16:02:40UTC. This was cached restoration, not a new authenticated fetch:
  the redundant fresh-fetch polling loop was stopped without changing cache/refresh
  policy. The separate15:59:16 authenticated beta67 flow is the fresh-readiness proof.

### Normal restricted baseline and safe controls

Wi-Fi OFF/mobile data ON, validated cellular path. Two short baseline invocations
each passed two normal connect/disconnect cycles through the real restricted
Telemost engine: DNS, HTTPS200/body, independent normal TCP80 response, health
samples, reconnect and complete cleanup. No immediate retry exhaustion, auth/
readiness error, cleanup loop or observed orchestrator recovery. This is a direct
restricted-engine baseline, not an automatic fallback-policy acceptance test.
An additional ordinary20-second healthy session after final directory correction
verified controls and cleanup only; no fault/selected retry traffic was targeted.

Android:
- OwnerDiagnostic OwnerFaultReceiver available; live status DISARMED, armedfalse,
  consumedfalse, count0, no generation. Native stats contained no active evidence_watch.
- Independent package UID10363 without DUMP could not reach the receiver;
  authorized shell status succeeded. Probe removed after test.
- Final idle status UNAVAILABLE/empty target/armedfalse/consumedfalse/count0 is
  expected recorder absence **after proven live control availability and cleanup**.
  Correlation status-only bridge returned rejected without a recorder/key, not disabled.

Gateway:
- During ordinary session, Unix socket created only in configured directory,
  UID/GID979, mode0600; correlated `/proc/PID/fd` inode and `/proc/net/unix` path.
- UID979 status request reached parser; UID0 (despite DAC bypass) rejected by
  SO_PEERCRED check. Only `status` sent. No prearm/bind/cleanup control operation.
- Session ended normally and directory returned empty; latest process unchanged,
  no retained socket/watch/descriptor. Final readback reconfirmed empty0700 directory.

Empty-state acceptance combines fresh process/session lifecycle, no prearm/bind
issuance, Android native watch absence and final teardown/empty directory. The
gateway protocol has no global watch enumeration; a rejected status key alone is
**not** claimed as proof of all watches empty. No unsafe dry prearm was attempted.

### Isolation and rollback

Controls present only in accepted ownerDiagnostic/native-tagged pair. Normal RU/NL
HTTP/AWG/TCP service states/PIDs unchanged against renewal baseline. No public
beta67 release, default artifact/catalog/invitation change, or unrelated service
operation. Installed owner beta67 is distinct from public/default channel versions;
download links and public checksums remain unchanged intentionally.

Beta66 APK retained in prior accepted evidence and fresh pulled
`pinned-evidence-deploy-1/resume4-installed-before.apk` with exact hash above.
Gateway backup on NL:
`/opt/apps/family_connect/restricted-materials-stage-20261001/pinned-evidence-deploy-1-20261006/bootstrap-broker.previous`.
Hash reverified against preflight beta66. `unit.before` and `effective.before.json`
retained beside it; current credentials retained independently, never roll back to
expired credentials or lower floors. Gateway rollback path: hash-check backup,
atomically restore executable preserving owner/mode, remove only this diagnostic
drop-in to restore original configuration, daemon-reload/restart, then verify actual
loaded binary/TLS/RU-NL/readiness. **Not executed**, healthy beta67 retained.
Non-debuggable Android code67→66 downgrade is not assumed supported; no `-d`,
uninstall or data-clear test. Keep identity/data intact and use separately approved
forward recovery if Android refuses downgrade.

Local restricted evidence under `state-client-build/field65-export16/pinned-evidence-deploy-1/`:
`resume4-manifest-verification.json`, `resume4-owner-{package,state}-*.json`,
`resume4-gateway-{preflight,relative-config,closeout}.json`, `verification-*.json`,
`final-owner-ready-pass.json`, `closeout-owner-readiness-*.json`,
`resume4-{baseline,second-baseline,control-session,socket-controls3}.json`,
`resume4-permission-probe.log`. Failed earlier socket-monitor logs retained, not erased.
No identity private bytes, product DB, signing keys or protected backups added to Git.

**PINNED-EVIDENCE-DEPLOY-1 = PASS.** Separate physical owner evidence/impairment is
technically unblocked but may begin only as a separately authorized task with fresh
headroom and empty/unarmed checks. This deployment task did not authorize or execute it.
**Exactly one next step:** obtain that separate owner evidence-task authorization.

## Historical STOP/PARTIAL evidence (superseded)

## Post-authority-renewal resumption — 06.10 15:11–15:15UTC

[AUTHORITY-RENEWAL-1](2026-10-06-authority-renewal-1.md) remains accepted; the old
credential STOP is resolved. This is continued preflight, not a fresh task or a
new freeze. Prior evidence and failures remain recorded below.

Fresh checks:

- ADB authorized intended Redmi31ce63ba. At15:14:11UTC beta66/code66, package
  com.familyconnect.app.friends, exact installed APK
  `e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81`, accepted signer
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`, non-debuggable.
- UID10283, inode601521, data directory and firstInstallTime preserved. Signed
  snapshot verifies Support FC-4D8Q-REEG, exact encrypted identity fingerprint and
  successful decryption, enrollment fingerprint and activation against accepted
  beta66 evidence. Repeated closeout snapshot passes; temporary test helper removed.
  Owner app was not uninstalled/cleared/upgraded; no re-enrollment or identity reset.
- Wi-Fi0/mobile-data1. Only read-only diagnostic `status` broadcast sent:
  schema1, stateUNAVAILABLE, empty target, armedfalse, consumedfalse, count0.
  This is expected idle recorder absence, not proof of active beta67 control readiness.
- Sealed beta67 manifest/all7 members/signature/native provenance reverified
  at15:14:27.352759UTC, PASS; no rebuild/substitution.
- Fresh authority/TLS check15:11:54.435714UTC: issuer6/grants valid, owner/tester
  revisions3/1 and admission fingerprint preserved; signed CRL9368 on RU/NL,
  expires19:11:14UTC. Actually served leaf remains the accepted renewed leaf,
  expires18:47:30UTC, **headroom12935s =3h35m35s** at that check.
- RU/NL generation14:47:36.916634343UTC and exact directory SHA256
  `303ac42212e6c1c0bc61bb1a7f9f73f05ae239de6be1b2ba782eef531e7d3aa1` match.
- Gateway /proc/PID/exe remains beta66
  `6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec`, tied to sealed
  revision5327deb414ae8aa77ce2f9490fd99c9485eba740. PID1231405/NRestarts0;
  service config hash unchanged. Read-only query observed zero established18444
  control connections; this alone does not prove absence of all data sessions.

### Configuration conflict found before installation

Readback of the actual gateway process environment finds **no
`FC_DIAGNOSTIC_CONTROL_DIR`**. No other environment variables or secrets were printed.
The exact frozen commit `ffd27988468fba427aaba6213b862dca01020972`, inspected via
`git show`, implements `carrier/sessiontrace/correlation_linux.go` as:
`directory := os.Getenv("FC_DIAGNOSTIC_CONTROL_DIR")`; empty value returns immediately.
Thus a byte-exact beta67 replacement with unchanged environment cannot expose the
required diagnostic Unix socket, even once an ordinary restricted session starts.
The [accepted contract](2026-10-06-pinned-evidence-correlation-1.md) requires an
operator-created mode0700 directory owned by the service effective UID; sockets are
per-session/mode0600 and enforce same UID via SO_PEERCRED. It is not an always-on
idle socket, and a missing socket cannot be used as a successful runtime UID test.

The current request simultaneously requires this control surface and unchanged
service configuration. No environment/drop-in/wrapper/launch override was applied
to evade that constraint. Installation and gateway replacement were held before
creating a mixed pair that could not satisfy the remaining control gate.

Result **PARTIAL**, awaiting a narrow configuration exception, not an artifact,
identity or renewed-credential failure. Beta67 is NOT installed/deployed; fresh
beta67 READY/ACK, DNS/HTTPS/TCP/reconnect baseline, runtime DUMP/UID enforcement and
complete empty watch/prearm/nonce/descriptor proof remain NOT RUN/NOT VERIFIED.
No stale state was found, but its complete absence is not claimed. No arm/prearm,
bind/cleanup/purge, DATA drop, physical experiment, soak or impairment was sent.

Local beta66 APK/gateway retention is hash-verified; the live loaded gateway matches
the retained beta66 image. Authority-renewal server backups remain retained, but no
new beta67 replacement backup/rollback operation was performed. Android downgrade
limitations below remain in force. Public/default/catalog/invitation channels unchanged.

Fresh evidence: `pinned-evidence-deploy-1/resume3-*` under the existing protected
session evidence directory; fresh server/TLS receipt retained as a new
`authority-renewal-1/verification-*.json`. Existing evidence was not overwritten.

**Separate owner physical evidence/impairment task: NOT ALLOWED.**
Exactly one recommended next step: authorize the narrow ownerDiagnostic service
configuration exception for `FC_DIAGNOSTIC_CONTROL_DIR` and its service-owned0700
directory, preserving every other setting, then resume remaining deployment gates.

## Resumption — owner connected, new security stop

This continues the original PARTIAL attempt; its historical evidence remains below.
Owner ADB absence is resolved. No sealed artifact was rebuilt or substituted.
Fresh immutable recheck at2026-10-06T14:31:36.764890Z passes all original checks.

### Mandatory owner preflight — PASS

ADB serial31ce63ba, Redmi Note9Pro/joyeuse, authorized. At14:30:44.851716UTC:

| Property | Fresh observation |
| --- | --- |
| Package/version | com.familyconnect.app.friends /0.1.18-beta66 /code66 |
| Pulled installed APK SHA256 | `e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81` |
| Verified signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| UID / CE data inode | 10283 /601521 |
| Data directory | /data/user/0/com.familyconnect.app.friends |
| First installation marker | 2026-09-19 17:30:26, unchanged |
| Debuggable | false |
| Support ID | FC-4D8Q-REEG, preserved |
| Encrypted identity | retained exact fingerprint; decrypts successfully |
| Enrollment / activation | fingerprint unchanged /true |
| Network settings | Wi-Fi0, mobile data1; no network setting changed |

The existing signed `registrationSnapshot` helper performs the identity/enrollment
checks without launching FriendsActivity or initiating readiness. Its signature was
verified before installing only the test APK. Snapshot matches the accepted beta66
final identity/enrollment/Support/activation state. A final repeated snapshot matches
this fresh baseline. The temporary `.friends.test` helper was then removed; the
owner application was never uninstalled, cleared, reset, re-enrolled or upgraded.
Final package metadata still matches beta66, UID, inode and first-install marker.
No post-beta67 first-start/restart preservation claim is made: installation did not occur.

Read-only RU preflight at14:31:26UTC confirms owner admitted/non-revoked, grant
revision3 (tester revision1 also non-revoked). Both grants expired13:51:23UTC.
Owner's last stored beta66 READY/ACK is now expired, `currently_ready=false`;
it is not used as fresh readiness. No fresh authenticated fetch was requested.

### Credential STOP and gateway observation

The original combined server probe saved RU evidence but failed its NL TLS-chain
assertion. A separate bounded read-only inspection at14:34:40.474472UTC confirms:

| NL observation | Result |
| --- | --- |
| Unit | family-connect-restricted-bootstrap.service, active/running |
| PID / NRestarts | 1124728 /1; pre-existing, no restart by this task |
| Actual /proc/PID/exe SHA256 | `6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec` |
| Revision binding | retained sealed beta66 `5327deb414ae8aa77ce2f9490fd99c9485eba740`, by exact binary hash |
| Listener | 127.0.0.1:18444 listening |
| Service configuration SHA256 | `b9012b159073ddedc2fcad12a31f4a4bc9175ff860c0ac15a9d5ec3ab9386199` |
| Profile gateway leaf expiry | 2026-10-06T11:03:25Z, expired |
| Issuer expiry | 2026-10-06T13:51:23Z, expired |
| Profile CRL expiry | 2026-10-06T13:51:23Z, expired; signature verifies |
| Profile minimum-bound headroom | −12675seconds; not a served-chain validity proof |
| Actually served TLS chain | no certificate returned by bounded TLS1.3/http1.1 ALPN probe; NOT VERIFIED |

This triggers the explicit invalid-credentials STOP before product installation or
gateway replacement. No production settings were weakened. Existing accepted
credential-only renewal (`diag-pair-deploy-1/renew.py` and its bounded operator)
requires a currently valid delegated issuer, unchanged grants and >1800seconds
headroom; current authority/grants violate those prerequisites. Merely issuing a new
leaf cannot fix this. That operator was inspected, not executed or modified to bypass
validation. No issuer rotation, grant extension, CRL publication or credential renewal
was performed after this STOP. Authority restoration must use the accepted authority
renewal procedure before deployment can safely resume.

RU and NL directory bytes match SHA256
`e5a04bfbeffaef4c5a0062b5d00949b8b43b55bf007cab8329e55fa6ba4d627e`, version1,
issued2026-10-06T11:04:06.167518871Z, expires2026-10-06T15:04:02.723498131Z.
No directory-generation divergence observed; **overall RU/NL credential readiness
is not PASS** because authority/grants/CRL are expired. A later directory expiry
cannot extend the credential bound or establish that a usable seed exists.

### Closeout and remaining gates

Result **FAIL / STOP_CREDENTIALS_INVALID**, not a beta67 artifact failure. Fresh
manifest and owner preservation PASS; beta67 installation, gateway replacement,
fresh READY/ACK, cellular DNS/HTTPS/TCP/reconnect baseline and runtime diagnostic
control/stale-state checks remain NOT RUN/NOT VERIFIED. No prearm/watch/arm/purge
command or physical fault/evidence/impairment experiment was sent. Public/default/
catalog/invitation channels remain unchanged. Current beta66 remains installed;
the accepted beta67 remains only a retained signed candidate.

Local beta66 APK/gateway retention is verified; the observed loaded NL hash now
matches the retained beta66 rollback binary. No new server-side backup was created
and full replacement/rollback preflight remains open. No rollback is necessary;
Android downgrade limitations in the original attempt remain applicable.

Added protected evidence under the same `pinned-evidence-deploy-1/` directory:
`owner-package-before.json`, `installed-before.apk`, `owner-state-before.json`,
`owner-state-closeout.json`, `owner-package-closeout.json`,
`manifest-verification-resumed.json`, `185.251.89.19.json`, `nl-preflight.json`,
`resumed-result.json`. No identity secrets or product DB were printed or committed.

**Separate owner physical evidence/impairment task: NOT ALLOWED.**
Exactly one recommended next step: restore valid authority/grants/CRL/gateway
credentials through the accepted renewal procedure, then resume this deployment
with fresh preflight and all outstanding gates; do not bypass expired authority.

## Historical first attempt — PARTIAL, ADB unavailable

2026-10-06. Owner-only immutable deployment preparation. No runtime mutation.
Accepted input: [PINNED-EVIDENCE-FREEZE-1](2026-10-06-pinned-evidence-freeze-1.md).

## Manifest verification — PASS

Fresh local checks completed at **2026-10-06T14:12:04.495185Z**.
Frozen revision `ffd27988468fba427aaba6213b862dca01020972`, CI-only tag
`diag-owner-beta67-ci1`; retained source bundle HEAD matches. The working tree
HEAD remains `8d046321039d0bd1e18ecc1af979ff90f591e029`, not the sealed source;
existing dirty work was preserved. No rebuild, signing, CI rerun or substitution.
The accepted manifest records all17 hosted workflows successful; these are retained
freeze results, not new deployment tests or a fresh remote CI poll.

| Verified local item | SHA256 |
| --- | --- |
| Pair manifest | `98dabfa38cb2cd437b5ec45700e936da3ae0b94ef47f11b8904a90faa472fc77` |
| Signed beta67 APK | `8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f` |
| APK signer | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Restricted JNI | `4a7b6bc17c8e7cb704d3cdfdcfc9aec9333dd17d5d17ba46dbe5d435f805fa81` |
| Normal libfc-awg.so | `15f1da2ea95957cdba28806b23b3ca7d698b35b2d8cb835d4ce97285270a6e6a` |
| Matching gateway | `c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143` |

All7 manifest members match, including provenance and diagnostic contract JSON.
Fresh apksigner verification passes with exactly the accepted signer. AAPT verifies
`com.familyconnect.app.friends`, `0.1.18-beta67`/code67, non-debuggable; all embedded
native libraries are arm64-v8a. Both embedded Family native hashes and byte-exact
provenance assets match. Gateway Go build metadata embeds the frozen revision,
`vcs.modified=false` and `fc_owner_diagnostic`; this is static, not loaded-process proof.
Schemas: correlation1, prearm/descriptor `pinned-correlation-v1`, control1,
telemetry golden `public-beta66-golden-v1`. No mismatch found.

## Owner preflight blocker

The initial sandbox ADB probe failed to bind its local listener (EPERM).
An approved outside-sandbox probe then completed successfully but listed no devices;
a final approved repeat at **2026-10-06T14:12:18Z** again returned zero devices.
Expected owner serial `31ce63ba` is unavailable. This is an access/prerequisite
blocker, not evidence of signer, identity or transport failure.

No APK was installed, no instrumentation or app launch was performed, and no
network setting was changed. Prior accepted beta66/code66, UID10283 and Support ID
are historical expectations only. Current installed APK hash/signer/package/UID,
data inode, Support ID, encrypted identity, enrollment, activation, admission,
revocation/revision, readiness and cellular/Wi-Fi state are **NOT VERIFIED**.
There is no post-install or post-restart preservation result; do not claim that
no mutation alone proves current identity preservation. No re-enrollment occurred
through this task, but automatic activity on an unavailable device is unobserved.

## Remaining runtime gates

| Gate | Current result |
| --- | --- |
| In-place beta67 installation and pulled-back APK/JNI hashes | NOT RUN |
| UID/data/Support ID/identity/enrollment preservation after start/restart | NOT VERIFIED |
| Gateway preflight: loaded hash/revision/PID/NRestarts/config/TLS/directory/sessions | NOT RUN |
| Exact beta67 loaded gateway, listeners and service health | NOT RUN |
| Credential validation, actually served TLS chain, effective bound/headroom | UNKNOWN; no renewal |
| RU/NL generation/hash and issuer/CRL/grant consistency | NOT VERIFIED |
| Fresh authenticated fetch → native import → READY → ACK | NOT RUN |
| Cellular DNS/HTTPS/TCP/reconnect/cleanup/app-restart baseline | NOT RUN |
| Android receiver and DUMP protection | STATIC APK declaration verified; runtime enforcement untested |
| Gateway diagnostic Unix socket and expected UID enforcement | NOT VERIFIED |
| Empty watch/prearm/descriptor/nonce/generation state | NOT VERIFIED |
| Safe control dry-run | NOT RUN; no prearm/watch/purge or fault command sent |
| Runtime default/public isolation | NOT VERIFIED; no default/public changes made |

No gateway was contacted or changed: preserve pair sequencing until owner preflight
is possible. Do not reuse historical credential headroom or cached READY as proof.
When resuming, use the existing [authoritative renewal runbook](../../deploy/friends/restricted/GATEWAY_RENEWAL.md)
if JIT renewal is needed; preserve all issuer/CRL/floor/hostname/identity checks and
verify the served chain and RU/NL current generation before ordinary client refresh.
Any actual stop-condition failure must halt the deployment rather than be bypassed.

## Rollback readiness — local retention only

Freshly hash-verified retained sealed beta66 APK:
`e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81`.
Freshly hash-verified retained sealed beta66 gateway:
`6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec`.
Both remain in `state-client-build/field65-export16/diag-source-freeze-1/immutable-ownerDiagnostic-beta66/`.
The present live gateway was not inspected; the beta66 retained binary must not be
called the current rollback image until its equality to the current loaded binary
is freshly established. No new server-side backup or rollback test was performed.

Known gateway path: NL `186.246.45.246`, unit
`family-connect-restricted-bootstrap.service`, executable
`/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker`.
Before replacement, capture live `/proc/PID/exe` hash, revision, service settings and
retain/hash-check that exact previous executable. Rollback uses only this unit:
stop, atomically restore the verified prior binary with observed owner/mode, start,
verify loaded hash/listener/credentials and RU/NL propagation. Never restore expired
credentials or lower CRL/revision floors. No rollback is needed for this attempt.
Non-debuggable Android code67→66 downgrade is not presumed supported; no `-d`,
uninstall or data-clear test. Recovery needs a separately reviewed data-preserving
plan or accepted forward-version build, not silent identity recreation.

## Isolation, evidence and next step

No public beta67 artifact published; no catalog/default/invitation/channel updates.
Candidate bytes remain sealed; built/signed does not mean installed or deployed.
No intentional DATA drop, impairment, selected-retry capture, Telemost baseline,
soak, Krasnodar, WB/VK, transport tuning or reverse DATA104 fix occurred.
Documentation-only repository changes; no product/runtime sources changed.

Local evidence under `state-client-build/field65-export16/pinned-evidence-deploy-1/`:
`verify.py`, `manifest-verification.json`, `gateway-build-info.txt`,
`owner-preflight-blocker.json`. The verification script ran successfully; no
product unit/build suite was rerun because no product code changed.

**A separate owner evidence/impairment task may NOT start.** Deployment PASS remains
unproven. Exactly one recommended next step: reconnect and authorize the owner
Android device in ADB, then resume this deployment from full owner preflight with
fresh immutable verification. Do not substitute another device or skip preservation.
