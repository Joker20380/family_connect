# DIAG-PAIR-PREP-1 — PARTIAL, artifact gate STOP

2026-10-06, read-only baseline approximately03:56–04:05 UTC. No matching
diagnostic pair installed/deployed; no fresh readiness claim. DATA-hole root cause
remains **STILL UNKNOWN**. OWNER-CONTROLLED-LOSS-1 cannot start.

## Source and artifact verification

HEAD `8d046321039d0bd1e18ecc1af979ff90f591e029`;52 dirty/untracked paths at entry,
including pre-existing DATA-HOLE instrumentation, control/readiness, tests and docs.
Preserved all work; no commit/reset. HEAD alone is not the diagnostic source.
Gateway and diagnostic JNI embed that revision with `vcs.modified=true`; JNI
also records local carrier replacement. No immutable dirty-source manifest tied
to exact platform CI acceptance was established in this prep. This is missing
provenance evidence, NOT a demonstrated binary hash mismatch.

| Artifact | SHA256 | State |
|---|---|---|
| Installed owner APK | `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e` | Pulled from owner, signature verified |
| Installed JNI | `4fdc14f751e9ada09a0306970caca6d5bc134e2728dc5c073842ea7f20499fb2` | Extracted/hash only, not diagnostic |
| Diagnostic unsigned APK | `f686988d8da15b4ffced81efc6d8e9e9041286b65543bb5e884f7af0419f1d6e` | Matches DATA-HOLE-1 receipt; apksigner DOES NOT VERIFY |
| Diagnostic ARM64 JNI | `49406ddb8a6672804bf97b75a13131d1c830219791650e1247973d629ab5f6bc` | Local and APK entry hashes identical |
| Diagnostic Linux/amd64 gateway | `ce017d8fd5b3fa9c7c11597d7002dd6904eccc9b0431445fae07c6af941fc426` | Matches DATA-HOLE-1 receipt; NOT loaded |
| Actual loaded NL gateway | `7c6e1e11208e167309cbe83dac0f5f1f1bb306f4e41628180367aa6fa5e9aa50` | Hash read through /proc/PID/exe |

Diagnostic build receipts/local regressions remain those in
[DATA-HOLE-1](2026-10-06-field65-data-hole-1.md), not newly run tests or CI acceptance.
Installed package `com.familyconnect.app.friends`,0.1.18-beta65/code65, UID10283,
lastUpdateTime2026-10-04 22:19:48. Installed signer SHA256
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Diagnostic APK still uses internal beta65 metadata and is unsigned. No signing,
test-key substitution, installation/downgrade, data clear, re-enrollment or reset.
The accepted [signing procedure](../android-vault-signing.ru.md) requires release
gates and checked CI artifacts before signing; local dirty builds alone do not
satisfy it. A separate accepted diagnostic identity/build remains required.

## Owner and readiness

Wi-Fi setting0/mobile_data1; LTE was established by the preceding preflight,
not independently reproven here. Support ID FC-4D8Q-REEG is admitted/non-revoked.
Stored readiness revision3/minimum CRL6858; fetch1791214084, ACK1791214085,
expiry1791228132. Stored READY is now expired; currently_ready=false.
Two existing admissions remain admitted/non-revoked. Grants revisions3/1 both
expire1791294683 (06.10 13:51:23UTC). No fresh fetch/import/READY/ACK initiated.
No phone private data exported. UID and package verified; Device Identity,
activation and enrollment continuity inside app storage were NOT independently
verified. No mutation does not substitute for a post-install preservation test.

## Served TLS and effective bound

NL03:56:53UTC: active PID902401/NRestarts2; control TLS listener18444 answered
with ALPN http/1.1 and hostname gateway.family-connect.test. PID/restarts changed
since preceding preflight; cause UNKNOWN, not caused by this task.
Actual served leaf SHA256
`7a262c7960640586d9ac3ce9bdd44b2a8c5713fcecf7b26b5d9edd97a4e54c6a`;
expiry05.10 23:53:04UTC. Exactly one certificate was served; it equals profile
leaf, hostname matches, direct issuer signature verifies. Issuer was read from
profile, NOT misrepresented as an additional served certificate; expires
06.10 13:51:23UTC. Signed profile CRL8235 expires07:56:43UTC and verifies.
Profile minimum_crl8235. No credential material printed/exported.

Observed min(leaf, issuer, CRL) headroom **-14629s** at observation. The full
min(issuer, leaf, CRL, directory, grant/policy constraints) was NOT cryptographically
validated; it cannot be positive because the served leaf already expired.
No renewal attempted while artifact gates remain unresolved; do not call a fresh
directory a new four-hour credential window. Issuer/grant expiry is a hard cap.

## RU/NL consistency and baseline checks

Exact directory issued_at `2026-10-06T03:54:12.732057624Z`, version1,
expires_at `2026-10-06T07:54:09.967587414Z`, hash on both hosts:
`7440cbca2966a279836fa3dfd42ec64ff1b538e59a70d360a804944c2d3d2216`.
Byte equality PASS at observation; full issuer/CRL/grant compatibility and fresh
loaded diagnostic state NOT established. No stale snapshot observed at this sample;
no claim of comprehensive split-brain absence across subsequent timer updates.

RU AWG active/PID1515959/NRestarts0; TCP active/PID1908885/NRestarts0.
This is service status only. Traffic baselines, AUTH denial, cancellation,
privacy/export, app restart and post-install identity tests NOT RUN after artifact
STOP. Prior local test PASS receipts are historical, not baseline security PASS.

## Fault-control and rollback

fault-control armed state by this task = **false**; no arm request or fault occurred.
An actual runtime one-shot mechanism was NOT found/accepted: head-loss fixtures
are in Go _test.go, not proof of a physical arm endpoint. Therefore first-head/
attempt0 targeting, auto-disarm and restart non-persistence remain UNVERIFIED.
Do not label this as a verified operational DISARMED mechanism.

No runtime mutation to roll back. Current unit settings digest:
`b9012b159073ddedc2fcad12a31f4a4bc9175ff860c0ac15a9d5ec3ab9386199`.
Historical backup exists at
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005/bootstrap-broker.previous`,
SHA256 `055716447a1fe4bd8859dc2877410e756a9dc60a81b0ae5203a23f99606326a0`.
This is older than the current7c6e1e11; existence/hash is NOT a verified rollback
for a new deployment. Preserve current binary/settings before any future change.
Never restore expired credentials or lower security floors. Owner APK was pulled
for verification, not claimed as a safe downgrade rollback after a future bump.

## Publication, receipts and next gate

No default/catalog/invitation/public artifact write. Local signed Android catalog
remains beta60/code60/sequence1, artifact SHA256
`8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
RU download directory contains beta60 and beta65. Public HTTP bytes and live
invitation/default versions were NOT freshly verified; historical default60
must not be treated as fresh evidence. No rollout claimed.

Protected local receipts and pulled APK: `state-client-build/field65-export16/diag-pair-prep-1/`;
read-only probe: `state-client-build/field65-export16/diag-pair-baseline.py`.
Sandbox failed with quota during startup; escalated read-only commands used.
Heredoc also failed quota; apply_patch direct argument succeeded. No claim that
storage is fully unavailable. No background task left by this prep.

Single next step: establish exact-source accepted, install-compatible diagnostic
artifacts, including any missing disabled test-only one-shot control, before
runtime deployment/JIT renewal. Then verify full bound, RU/NL consistency, fresh
ordinary owner READY/ACK and baseline security/preservation. No controlled loss,
soak, impairment, Krasnodar FIELD, WB/VK or transport-policy changes in this task.
