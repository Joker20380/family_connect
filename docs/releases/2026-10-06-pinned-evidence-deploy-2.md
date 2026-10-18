# PINNED-EVIDENCE-DEPLOY-2 — PASS / owner-only beta68 deployed

## Final continuation — 2026-10-06

Continued the existing task; earlier credential and reporting STOP receipts remain
below. User explicitly accepted exact loaded-binary-to-sealed-manifest attribution
for callback schema readiness instead of a runtime capability-string endpoint.
No product source change, capability endpoint, beta68 rebuild or artifact substitution.

### Exact eight-link callback-schema attribution

1. In-place installed/pulled APK SHA256 `4c9c3b993cd62c86aa7eb083b6e4684945d7c507ff0a8c787c3dc62a42a9e9fb` equals sealed beta68.
2. Pulled APK signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` equals accepted compatible signer.
3. Embedded restricted JNI `c37392ac38252447ec297f2c6d0cf25d83262d13f030f24a0d16c6ef5c15e1b3` equals seal.
4. Embedded normal native `af441b102e6b340a498f77bd8822686191df225868f44ffd707ea4844387c8d7` equals seal.
5. Actual loaded `/proc/PID/exe` gateway SHA256 `3038888ae8abc585d159f9c0bec629ce59b0b2ac40b0a3d22e9bb73a92d9f717` equals seal.
6. Loaded bytes embed revision `1abaa3a8a9ba8ad9fa2a71c126620175b713c321`, clean VCS.
7. Immutable manifest SHA256 `53889bcf5c326d3285c21adbe78fd3db124646295a19936ef98deeaf21dc5345`
   binds those artifacts to `pinned-reliable-callbacks-v1`, tag `diag-owner-beta68-ci2`.
8. Exact frozen source Reliable→ACK pinned-chain/actual-write regression and17/17 CI
   acceptance remain accepted; their freeze closeout/manifest references verified.

Manifest: `state-client-build/field65-export16/pinned-evidence-freeze-2/immutable-ownerDiagnostic-beta68/pair-manifest.json`.
Correlation/control schema1, prearm/descriptor pinned-correlation-v1, public telemetry
public-beta66-golden-v1 unchanged. This is provenance-based runtime schema proof,
NOT a new physical selected-retry trace or a claimed runtime capability response.

### Owner in-place installation and preservation

Intended Redmi Note9 Pro, package `com.familyconnect.app.friends`, beta68/code68,
non-debuggable, arm64-v8a only. Fresh beta67 preflight verified original APK/signer,
Support ID, decryptable encrypted identity, enrollment fingerprint and activation.
Installed only sealed beta68 with `adb install -r`; pulled back exact APK afterward.
Before/after/final UID10283, CE data inode601521, first install2026-09-19 17:30:26,
Support FC-4D8Q-REEG, encrypted identity hash, enrollment fingerprint and activation
all preserved. Server admission/revocation and owner3/tester1 revisions unchanged.
No owner uninstall, data clear, identity reset or re-enrollment. Separate signed test
helper only was rebuilt for beta68 assertions, installed temporarily and removed.
Its first Gradle invocation hit sandbox socket restrictions; outside-sandbox build
passed. No sealed product artifact was rebuilt or modified.

### Gateway and credential chain

Before swap, beta67 loaded hash c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143,
PID1398351/NRestarts1 were recorded as pre-existing observations (not this task's
restart). Preserved old binary/config before replacing only the executable.
Final beta68 PID1401423, NRestarts0, listener healthy and stable
through baseline/control checks. Unit/config unchanged byte-for-byte, including
`FC_DIAGNOSTIC_CONTROL_DIR=diag67`; no unrelated systemd changes.

Actual served leaf/profile match, signature/hostname/issuer/CRL checks PASS after
swap and again at closeout. Issuer6/minimum revision1 and both grants valid through
07.10 14:45:31UTC. Final CRL9946 valid until2026-10-07T00:26:08+00:00;
RU/NL exact CRL/authority/directory equality and grant compatibility PASS.
Directory generation `2026-10-06T20:13:55.407645965Z`, expiry `2026-10-07T00:13:51.527596537Z`;
SHA256 `2159d02f9d5cabe150ed206ba395b788cd346c9fba0037b8428aafa54655baa4` on both hosts. Sync naturally advances CRLs.
Actual leaf expiry **2026-10-06T23:48:47+00:00**, effective minimum
**2026-10-06T23:48:47+00:00** across leaf/issuer/CRL/grants/directory/receipt; **12133seconds**
headroom at **2026-10-06T20:26:33.437015+00:00**. Directory/READY expiry never extends served-leaf validity.
No renewal was performed in this continuation.

### Fresh READY, ordinary cellular baseline and restart

New beta68 authenticated fetch/native READY 2026-10-06T20:14:42+00:00, ACK
2026-10-06T20:14:43+00:00; PRESENT_VALID/PRESENT_VALID, usable, failure NONE, owner revision3.
Not reused beta67 READY. Wi-Fi OFF, cellular ON verified both via settings and native
network capabilities. Two real restricted/Telemost engine connections each passed DNS,
HTTPS200 with bytes, TCP response,15s healthy observation and cleanup; second connection
proves reconnect. No retry exhaustion/auth failure/cleanup loop observed in this short
baseline; no intentional DATA loss or extended soak. Baseline directly exercises the
restricted engine, not a sustained automatic-orchestrator recovery-loop experiment.
App force-stop/relaunch after helper removal obtained fresh beta68 READY/ACK again:
fetch 2026-10-06T20:26:15+00:00, ACK 2026-10-06T20:26:16+00:00.

### Diagnostic controls and safe final state

Android active-session status DISARMED, armed=false, consumed=false,count0, no
generation; full native stats check found no evidence_watch. Dedicated unprivileged
probe confirms DUMP enforcement; temporary probe removed. Cleanup status UNAVAILABLE
with armed=false/count0 means no active native session, not an active-session failure.

Gateway sockets from both baseline sessions: service UID/GID979,0600, exclusively
inside service-owned0700 diag67. Same-UID status reached parser; wrong UID(root)
was rejected despite root's DAC privileges. Only status requests were sent; no
prearm/bind/cleanup/fault command. Requests without matching prearm rejected as expected.
Sockets disappeared after session cleanup, final directory empty. No stale descriptor,
watch or generation remains after clean session teardown. No live Reliable DATA
attempt was targeted to prove schema support.

### Rollback and operating limits

Beta67 APK and gateway retained and all sealed files/manifest rehashed unchanged;
beta68 sealed pair likewise unchanged. Remote beta67 backup:
`/opt/apps/family_connect/restricted-materials-stage-20261001/pinned-evidence-deploy-2-20261006/bootstrap-broker.previous`,
hash `c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143`. Gateway rollback, if authorized/needed: verify that
hash, stop only restricted bootstrap, atomically restore binary preserving permissions,
start and reverify loaded hash/revision, served current credentials and fresh directory
propagation. Retain current issuer/CRL/floors; never restore expired authority material.
No rollback performed. Non-debuggable Android code68→67 downgrade is not guaranteed
in-place; do not uninstall/clear data to force it. Prefer a separately accepted forward
recovery build for client rollback needs while preserving owner identity.

Public/default/catalog/invitation distribution unchanged; beta68 is owner-only installed,
not publicly released. No physical selected-retry, fault/prearm, intentional DATA drop,
impairment, soak, Krasnodar, reverse DATA104 or transport tuning.

Evidence: `state-client-build/field65-export16/pinned-evidence-deploy-2/resume2/`.
Prior failed/partial receipts retained. Source dirty work untouched; STATUS/PLAN/report
updated. Checks establish bounded readiness at recorded time, not future headroom.

**Separate beta68 owner physical selected-retry task is technically allowed to begin**
after its fresh preflight and separate authorization; it was not executed in this task.

**Exactly one recommended next step:** separately authorize that owner beta68 physical
selected-retry task with fresh credential/headroom and empty-control preflight.

---

## Previous attempts and evidence

# PINNED-EVIDENCE-DEPLOY-2 — PARTIAL / resumed after credential renewal

## 06.10 fresh preflight and capability-reporting blocker

Continued the existing deployment, not a new task. GATEWAY-CREDENTIAL-RENEWAL-2
remains PASS. This attempt made no install/deploy/renewal/prearm/fault changes.

Sealed beta68 source1abaa3a8a9ba8ad9fa2a71c126620175b713c321 and all beta67/beta68
manifest members reverified unchanged. Intended owner Redmi Note9 Pro remains
beta67/code67, non-debuggable, UID10283, data inode601521. Installed beta67 SHA256
8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f matches its seal.
Wi-Fi0/mobile_data1; Android status UNAVAILABLE, armed=false, count0. This is idle
beta67 status, not an operational beta68 control test. Full fresh encrypted identity/
enrollment snapshot was deferred with installation; no preservation-after-update claim.

Fresh live TLS at 2026-10-06T19:59:54.606516+00:00: beta67 loaded hash
c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143, PID1387868, NRestarts0; actual served leaf matches
profile, signatures/hostname/validity/non-revocation PASS. Limiting expiry23:48:47UTC,
headroom 13732seconds. RU/NL exact directory/authority/CRL equality
PASS, grants owner3/tester1 and admission/identity-revocation fingerprints unchanged.
CRL snapshot 9897; ordinary service states unchanged.
Directory generation 2026-10-06T19:49:15.595849272Z, hash
`005662ad02a22d0133acd38a6bd61a716bf137222a92c8ab291849309ea1cbca`.

### Exact unmet gate

The original deployment acceptance requires runtime reports of support for
`pinned-reliable-callbacks-v1`, without prearming/targeting a live Reliable DATA attempt.
Clean exact frozen source was inspected, not the unrelated dirty checkout:

- `carrier/sessiontrace/fault_receipt.go`: status has control schema/state/arm/count,
  no callback capability version field.
- `carrier/sessiontrace/correlation_command.go`: only prearm/status/cleanup/bind;
  no read-only capability operation.
- `carrier/sessiontrace/correlation.go:165`: status rejects absent/mismatched watch;
  idle status cannot expose callback evidence through this path.
- Android receiver/native bridge route these same commands. No capability reporter.
- Runtime source under carrier/Android/native has no pinned-reliable-callbacks-v1
  label; that name exists in sealed diagnostic-contract/pair-manifest metadata.

The callback implementation and source acceptance remain accepted. This is a
runtime reporting/evidence-contract gap, NOT a callback failure and NOT proof that
the implementation would be inactive after installation. Exact loaded hash/revision
could provide provenance-based capability evidence, but it was not silently
substituted for the explicitly required runtime report. Installing both binaries
would not add the absent reporting surface, so stopped before runtime changes.
No watch was prearmed merely to elicit callback fields; no sealed source/binary changed.

### Remaining gates and preservation

Pending: beta68 in-place install/identity preservation, gateway replacement and
loaded proof, fresh beta68 READY/ACK, cellular baseline/reconnect/cleanup, full
operational control tests, runtime schema evidence and final rollback acceptance.
Beta67 APK/gateway retained locally and running; no rollback needed. Existing Android
downgrade constraints and prior rollback notes below still apply. No public release,
default/catalog/invitation changes, physical experiment, DATA drop, impairment or soak.
Separate owner physical selected-retry task **may NOT start**.

Evidence: `state-client-build/field65-export16/pinned-evidence-deploy-2/resume1/`,
including exact source file hashes, seal/owner snapshot and fresh authority log.
Prior credential STOP and renewal receipts preserved. Documentation only plus local
evidence scripts changed; unrelated work untouched.

**Exactly one recommended next step:** explicitly accept exact loaded-binary-to-manifest
attribution as callback-schema evidence in place of the unavailable runtime capability
report, so deployment can resume without modifying sealed beta68 artifacts.

---

## Previous deployment evidence

# PINNED-EVIDENCE-DEPLOY-2 — PARTIAL

## Fresh preflight and mandatory STOP — 2026-10-06 19:10 UTC

Freeze acceptance remains PASS. Deployment is not accepted. The explicit
credentials-invalid stop condition was reached before installation or gateway swap.
The insufficient-headroom renewal path was not used to bypass this invalid-credential
STOP: the actual served certificate was already expired, not merely near expiry.

## Immutable verification

Frozen source `1abaa3a8a9ba8ad9fa2a71c126620175b713c321`, tag
`diag-owner-beta68-ci2`, version0.1.18-beta68/code68, package
`com.familyconnect.app.friends`. All manifest members rehashed successfully; manifest
SHA256 `53889bcf5c326d3285c21adbe78fd3db124646295a19936ef98deeaf21dc5345`.
Accepted signer, non-debuggable, arm64-v8a-only, embedded native/metadata equality,
clean VCS revision and diagnostic gateway tag checked. No rebuild or substitution.

| Artifact | SHA256 |
| --- | --- |
| Signed beta68 APK | `4c9c3b993cd62c86aa7eb083b6e4684945d7c507ff0a8c787c3dc62a42a9e9fb` |
| Signer | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Restricted JNI | `c37392ac38252447ec297f2c6d0cf25d83262d13f030f24a0d16c6ef5c15e1b3` |
| Normal native | `af441b102e6b340a498f77bd8822686191df225868f44ffd707ea4844387c8d7` |
| Beta68 gateway, NOT deployed | `3038888ae8abc585d159f9c0bec629ce59b0b2ac40b0a3d22e9bb73a92d9f717` |

Manifest: `state-client-build/field65-export16/pinned-evidence-freeze-2/immutable-ownerDiagnostic-beta68/pair-manifest.json`.
Schemas remain correlation/control1, pinned-correlation-v1, pinned-reliable-callbacks-v1,
public-beta66-golden-v1. These are sealed-source contracts, not fresh beta68 runtime proof.

## Owner and gateway observations

Intended Redmi Note9 Pro reachable. Package beta67/code67, UID10283, data inode601521,
first install2026-09-19 17:30:26, non-debuggable. Installed APK hash
`8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f`
equals sealed beta67. Wi-Fi0/mobile_data1. No app update, uninstall/data clear or
identity reset. Fresh encrypted identity/enrollment snapshot and installed-signer
pull inspection were not completed before STOP; preservation across an update is
therefore NOT claimed. RU owner admission true/non-revoked, grant revision3.

Android status returned schema1, UNAVAILABLE, armed=false, consumed=false, count0.
This does not prove operational beta68 controls, no stale generation, or callback
schema readiness. No arm/prearm/bind command was sent.

Gateway remains beta67: loaded SHA256
`c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143`,
revision `ffd27988468fba427aaba6213b862dca01020972`, PID1266691, NRestarts0,
active and listener present. Config SHA256
`3249833ca83f2f38d10f5ca9e2f22c6c0e436f94de18e7db60e2d60cdd2daec7`.
Accepted `FC_DIAGNOSTIC_CONTROL_DIR=diag67` unchanged; directory empty,0700, UID/GID979.
No new socket/same-UID/wrong-UID checks or beta68 callback runtime checks performed.

## Credential failure and RU/NL comparison

At19:10:52.396185UTC actual TLS leaf matched gateway profile and expired18:47:30UTC.
Effective observed chain headroom **-1402 seconds**. Issuer expiry07.10 14:45:31UTC;
CRL9807 signature valid, nextUpdate06.10 23:10:38UTC; grant rows unrevoked/future-dated.
Hostname and issuer signature checks pass, but expiry makes credentials INVALID.

RU/NL directory exact hash matches:
`0c160f8b9ada7888ae1bd7f2000b0c0deee08527a10393a5e96c2fb97bb6bff9`;
issued15:53:17.577994843UTC, expires19:53:15.410360137UTC. Full authority/grant/CRL
compatibility after renewal/swap remains pending; directory equality alone is not
complete readiness. Existing beta67 authenticated fetch/ACK was observed at epoch
1791313798/1791313799, receipt READY, revision3/minimumCRL9805. It is NOT a beta68
receipt and does not override the expired actually served TLS certificate.

## Remaining gates / rollback

NOT RUN: beta68 in-place install/preservation, gateway replacement, fresh beta68
READY/ACK, restricted DNS/HTTPS/TCP/reconnect/cleanup/restart baseline, full runtime
control/schema checks. No selected retry, intentional loss, impairment, soak,
Krasnodar, reverse DATA104, public publication/catalog/invitation changes.

All beta67 sealed members and manifest remain hash-verified locally. Beta67 APK and
gateway retained in `pinned-evidence-freeze-1/immutable-ownerDiagnostic-beta67`.
No rollback needed because runtime was unchanged. Future gateway rollback must use
the hash-verified beta67 binary, preserve service config and current monotonic
authority/CRL state; expired credentials are not a healthy rollback. Release APK
downgrade from code68 to67 is not a guaranteed in-place path on non-debuggable Android;
do not uninstall/clear data to force it. No device downgrade performed.

Evidence: `state-client-build/field65-export16/pinned-evidence-deploy-2/` contains
manifest-verification, beta67-preservation, owner-package-before, per-host credential
preflights, gateway-preflight and stop receipts. No private keys/profile contents
or encrypted identity bytes exported. Unrelated source work preserved.

**Exactly one recommended next step:** perform a separate authority-runbook gateway
credential renewal and verify the actually served valid chain before resuming deployment.
The separate owner physical selected-retry task may NOT start.
