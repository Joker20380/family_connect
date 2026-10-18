# RTP-IDENTITY-DEPLOY-1 — PASS / owner-only immutable beta69 deployment

## Final continuation — 07 October, 17:57 UTC

User authorized only the separate test-helper build/sign/use; no production build,
new freeze/commit/tag/version or CI rerun. Prior results/receipts below retained.
Historical first gateway failure remains UNKNOWN; investigation not reopened.

### Test-only correction and provenance

New helper directory: `state-client-build/field65-export16/rtp-identity-deploy-1/helper69/`.
Copied existing accepted sources without overwriting beta68 helper or receipts.
`OwnerPairBaselineTest.restrictedBaseline` and `OwnerControlSessionTest.statusOnlySession`
each changed exact `assertEquals("68", arguments.getString("expected_version"))`
to exact69; wrapper likewise launches69 after pinned manifest/installed identity checks.
Base guard still checks actual package version. No greater-than/list/automatic acceptance.
Existing HTTPS target/timeouts retained; first1024bytes check strengthened to read EOF,
HTTP200, Example Domain and closing HTML, with64KiB safety ceiling. Both live replies
were complete577byte documents. DNS/TCP targets, cycle count,180s startup deadline,
15s traffic timeouts,15s health samples and20s control session unchanged.

- Helper SHA256 `8090fa13d70c25f92ef331d4b867c6ecf9b6cad4ed971750084c5d7c21ff4d0b`.
- Source-hashes manifest SHA256
  `ab2c14636bfbf8dcae205909761cf06c7ffe730ee10d124c0676364da08e9b40`.
- Existing compatible helper signer67a90d1b used; no new key or production signing.
- Five local contract tests PASS: exact69, rejection68/70/other mandatory identity
  mismatches, required restricted/cellular assertions, unchanged timing, full HTTPS
  contract and sealed pairs. Negative fixtures did not change owner installation.
- Offline AndroidTest build PASS against cached exact-SHA classes; all production
  tasks disabled/SKIPPED. No native payload in helper; frozen source tree clean.
  `minimal.diff`, source-hashes.json, contract-tests.log and provenance.json retained.
  Initial sandbox Gradle daemon socket denial occurred before build; authorized
  outside-sandbox execution succeeded, not a product failure.

### Live acceptance and final attribution

Fresh preflight verifies package com.familyconnect.app.friends, version0.1.18-beta69/
code69, arm64-v8a, non-debuggable and pulled APK hash/signer/native payloads before
helper installation. Final pulled APK remains
`237660f3ed909b1598934beb4ed4fb3331a651fa3c3fd17473e0870235d86c51`, signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Loaded gateway remains
`edf60a6e345e1c64fdb48162ede04f3955da6f7f0b86e53c35448bce61e7182c`, revision
`986323ecef112fcc421a22263e6fbfc9d6cf1922`; manifest remains
`e039486c269b5fe1b99b51583bb155c540a32ca46dc49f8b96eb8431741189d9`.

- Wi-Fi off/mobile data on; explicit RestrictedTunnelEngine with default-route VPN,
  no Auto/WG/AWG/TCP fallback selected. Two gateway diagnostic session sockets match
  the two bounded baseline cycles. No new capability endpoint/ACK-token export used.
- DNS PASS, full HTTPS200/577bytes PASS, TCP request/response PASS in both cycles;
  ordinary teardown/reconnect and subsequent traffic PASS. No failed baseline rerun,
  retry exhaustion, recovery loop or cleanup failure observed.
- Active controls DISARMED/armed=false/consumed=false/count0; no generation or
  evidence_watch. Status-only gateway monitor PASS for both session sockets:
  service UID/GID979 mode0600, directory0700, wrong UID denied, final empty.
- Android DUMP enforcement PASS with unchanged accepted standalone permission-probe.
  First wrapper mistakenly selected OwnerPermissionRunner absent from packaged
  manifest: INSTRUMENTATION_FAILED before test-body execution, saved in permission.log
  and permission-tooling-disposition.json. Corrected launch used the existing separate
  probe, then removed it; no assertion change, baseline retry or runtime modification.
- Post-baseline app restart PASS. This run obtained a genuinely new authenticated
  fetch at1791395656 and ACK1791395657, receipt phase=import/READY/version69;
  unlike earlier restart receipt, this is not merely restored cached readiness.
- Final real served TLS at2026-10-07T17:56:20.281831Z matches profile, signature,
  hostname and revocation PASS; leaf limiting expiry20:13:53Z/headroom8252s.
  Authority expiry08Oct16:08:35Z; current CRL07Oct21:56:08Z. RU/NL directory and
  authority consistency PASS. Existing renewal remains valid; no additional renewal
  or service restart needed. PID1943512/NRestarts0 stable; unit/sandbox unchanged.
- Owner UID10283/data/first-install/Support ID/identity/enrollment/activation preserved.
  Temporary baseline helper and permission probe removed. Idle controls unarmed/count0,
  no generation, diag67 retained0700 UID/GID979 and empty; no stale18444 connections.
  Gateway rollback rehashed; keep renewed credentials/floors with any binary rollback.
  No Android downgrade/uninstall/data clear/re-enrollment performed.
- All sealed beta67/beta68/beta69 files unchanged before/after helper build and live
  use. No public/invitation-channel changes, fault/prearm/bind, selected-retry,
  impairment, soak, load test or Krasnodar operation.

Final evidence: helper69/PASS.json, baseline.json/log, control.json/log,
resume4-socket-controls.json, permission-PASS.json, restart-ready-PASS.json,
after-preflight.json, owner-after.json, cleanup.json and rollback-final.json.
RTP identity hop-local-rtp-v1 and pinned-reliable-callbacks-v1 acceptance retained
through loaded bytes→sealed manifest→accepted exact source/CI, not a new experiment.

No remaining deployment blocker. Separate owner selected-retry prerequisites are
satisfied at recorded measurement time, subject to its fresh credential/headroom/
empty-control preflight and separate authorization. Single next step: that separate
owner experiment with the accepted complete pinned-chain criterion; not started here.

## Historical continuation — PARTIAL (superseded)

## Resumed result — 07 October, 17:26 UTC

This section supersedes the original preflight STOP retained below. Freeze remains
PASS; no source, version, tag, immutable artifact, build or CI changes.

- Current startup blocker PROVEN: expired authority/CRL in the exact service
  --family-config gateway.json. Service UID979 read access, regular0600 file,
  credential format, signatures, key/leaf binding, hostname, floors and revocation
  verified. NTP synchronized. Existing beta68 source1abaa3a8 validates configuration
  via ServerTLS before net.Listen. Historical first termination cause UNKNOWN;
  generic retained error cannot distinguish it from subsequent startup failures.
- Standard renewal completed with existing root/issuer keys: issuer sequence7,
  authority/grants expiry2026-10-08T16:08:35Z; owner grant3/tester grant1 and
  admission/bindings/revocation unchanged. Existing24h authority and14400s CRL/leaf
  policies retained. Leaf expiry2026-10-07T20:13:53Z. Native publication positive/
  negative checks and atomic service-readable publication PASS; normal timer restored.
  An operator import failure before mutation was preserved and resolved using the
  already-pinned sync package; readback proved no credential mutation before correction.
- Exactly one controlled beta68 recovery PASS (reset-failed/start after evidence).
  Loaded3038888a/source1abaa3a8, listener/actual TLS and35s stability verified.
  Recovery success does not establish historical root cause.
- In-place owner com.familyconnect.app.friends0.1.18-beta69/code69 installed;
  pulled APK SHA256 `237660f3ed909b1598934beb4ed4fb3331a651fa3c3fd17473e0870235d86c51`.
  Signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  arm64-v8a, non-debuggable, exact embedded JNI/native hashes PASS. UID10283,
  inode601521/first-install time, Support ID FC-4D8Q-REEG, encrypted identity,
  enrollment and activation preserved before/after/final. No owner data reset.
- Matching gateway loaded SHA256
  `edf60a6e345e1c64fdb48162ede04f3955da6f7f0b86e53c35448bce61e7182c`,
  revision `986323ecef112fcc421a22263e6fbfc9d6cf1922`.
  Service unit/sandbox/FC_DIAGNOSTIC_CONTROL_DIR=diag67 unchanged; PID1943512,
  active/running/NRestarts0 and prior35s stability PASS, no new restart loop.
- Actual served chain at2026-10-07T17:26:27.396966Z matches new profile;
  signature/hostname/revocation PASS. Limiting leaf expiry20:13:53Z, headroom10045s;
  authority expires08Oct16:08:35Z, current CRL07Oct21:25:53Z. RU/NL directory SHA
  `4351561dd350f37f82f4dd4d8ec50d68132752df5f4900bbc56926881315c5b1` matches,
  expires20:53:05.603575967Z; authority consistency and admission preservation PASS.
  Client/directory validity does not extend the earlier gateway leaf bound.
- Fresh beta69 authenticated fetch→READY→ACK PASS (initial-ready-PASS.json).
  App restart restored READY/ACK PASS (restart-ready-PASS.json); not claimed as
  another fresh authenticated fetch. Wi-Fi0/mobile_data1 observed.
- Restricted cellular DNS/full HTTPS/TCP, reconnect and active-session controls
  NOT RUN: existing restricted-only baseline/control helper asserts code68 and its
  base guard checks actual installed version. No honest argument works on69.
  No assertion weakening, version spoofing, new build/signing or normal-transport
  fallback substituted for the required Telemost evidence. Compatibility proof saved.
- Idle controls armed=false/count0/no generation; no stale gateway watch/socket
  state. Idle UNAVAILABLE is not a defect. Temporary test-helper package removed;
  owner app retained. Active-session cleanup acceptance remains pending with baseline.
- All sealed beta67/beta68/beta69 files rehashed unchanged. Verified rollback binary:
  `/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-identity-deploy-1-20261007/bootstrap-broker.previous`,
  SHA256 `3038888ae8abc585d159f9c0bec629ce59b0b2ac40b0a3d22e9bb73a92d9f717`.
  Preserve renewed credentials/floors during any binary rollback; never restore the
  expired profile merely to match old bytes. Android downgrade is not assumed safe.

Evidence: `state-client-build/field65-export16/rtp-identity-deploy-1/resume/`, notably
PARTIAL.json, historical-causality.json, audit-nl.json, publication.json,
beta68-recovery-verification.json, installed-attribution.json, gateway-beta69.json,
final-served-chain.json, final-ru-consistency.json, owner-state-final.json,
baseline-helper-compatibility.json, rollback.json and seals-after.json.

Private owner installation/NL deployment only; public channels/invitations unchanged.
No prearm/bind/fault injection, selected-retry, soak, impairment or tester operation.
Deployment remains PARTIAL, not ready for selected-retry. Single next step:
provide/authorize a beta69-compatible test-only restricted baseline helper, then
finish the already-defined baseline/reconnect/active-control gates.

## Historical preflight STOP (superseded)

## Scope and accepted pair

Owner-only deployment plus ordinary credential renewal authorized; no selected-retry,
prearm/bind/fault/impairment/soak/tester/publication authorization.
Frozen SHA `986323ecef112fcc421a22263e6fbfc9d6cf1922`, beta69/code69,
tag diag-owner-beta69-ci2. Manifest
`rtp-identity-freeze-1/immutable-ownerDiagnostic-beta69/pair-manifest.json`,
SHA256 `e039486c269b5fe1b99b51583bb155c540a32ca46dc49f8b96eb8431741189d9`.
Manifest and every listed artifact verified; sealed67/68/69 unchanged before/after.
No source, version, tag, artifact change, rebuild or CI rerun.

## Fresh owner observation

At2026-10-07T15:45:37Z, owner serial31ce63ba reports Redmi Note9Pro.
Installed com.familyconnect.app.friends remains0.1.18-beta68/code68:

- APK SHA256 `4c9c3b993cd62c86aa7eb083b6e4684945d7c507ff0a8c787c3dc62a42a9e9fb`,
  freshly pulled and signer verified; rehashed on device after preflight cleanup.
- Signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- UID10283, data inode601521, first install2026-09-19 17:30:26, non-debuggable.
- Accepted signed helper registrationSnapshot before/after: Support ID
  FC-4D8Q-REEG, encrypted identity hash/enrollment fingerprint unchanged,
  identity decrypts, activation true. Contents/keys not exported.
- Wi-Fi0/mobile_data1 observed. No baseline session started. Temporary test package
  removed; owner application not uninstalled, cleared, reset or re-enrolled.

## Existing gateway failure and STOP

Initial read-only observation before deployment: failed, MainPID0, NRestarts11,
ExecMainStatus1, Result exit-code. Fresh detailed receipt15:48:46UTC confirms
state transition2026-10-07 07:08:09MSK (04:08:09UTC).
Current on-disk gateway SHA256
`3038888ae8abc585d159f9c0bec629ce59b0b2ac40b0a3d22e9bb73a92d9f717`,
revision `1abaa3a8a9ba8ad9fa2a71c126620175b713c321` (beta68).
No loaded executable exists with MainPID0; beta69 gateway not deployed.

Bounded journal evidence includes bootstrap_seed_ready followed by repeated
`bootstrap broker stopped`, then systemd rate-limit failure. First retained stop
timestamp_us1791344992577359; this is the earliest stop in the retrieved window,
not a claim that the underlying primary cause has been recovered. Existing source
prints this generic message for multiple run errors; the journal cannot establish
credential expiry as its cause. No runtime diagnostics endpoint was added.
Initial read-only journal query timed out; a narrower bounded query recovered the
evidence. These were reads, not retries of deployment or service startup.

Under the requested failure policy, preserve evidence and stop changes. No blind
restart, reset-failed, credential publication or deployment. Credential renewal
permission is already present; the blocker is an unclassified pre-existing gateway
failure, not ordinary expiry or a request for renewed authorization.

## Credential and control observations

At2026-10-07T15:52:44.882309Z RU /15:52:46.288272Z NL:

- Directory SHA256 equal:
  `b003f25f01d71e980a62fc19fe8197e59bde28ec470023024d294841cf1e9855`;
  expires2026-10-07T07:55:02.63495438Z, already expired.
- Issuer sequence6/minimum_revision1, grants owner revision3/tester revision1,
  revoked0, expiry2026-10-07T14:45:31Z. CRL sequence11922/expiry same on RU/NL.
- Admission hash and identity/binding/revision/revocation fingerprint equal
  previously accepted receipt. No database/security state modified.
- RU sync service failed exit1; its timer remains active. NL no18444 listener.
- Gateway profile leaf expiry2026-10-06T23:48:47Z. These are profile/envelope
  metadata, not fresh cryptographic or served-chain acceptance. Actual served
  limiting expiry/headroom unavailable; no invented measurement or TLS PASS.
- FC_DIAGNOSTIC_CONTROL_DIR=diag67 preserved; directory0700 UID/GID979, zero
  entries. Android idle status disarmed/count0; idle UNAVAILABLE is not a defect.
  No active-session watches/control acceptance attempted, no prearm/bind/fault.

## Completion status and evidence

Evidence directory: `state-client-build/field65-export16/rtp-identity-deploy-1/`.
Receipts: PARTIAL.json, owner-package-before.json, owner-state-before.json,
owner-state-after-preflight.json, gateway-preflight.json,
gateway-primary-evidence.json, chain-metadata-185.251.89.19.json,
chain-metadata-186.246.45.246.json, seals-before.json, owner-idle-control.txt.

Beta69 READY/ACK, cellular DNS/HTTPS/TCP, reconnect/cleanup/restart not run.
No new gateway rollback binary staged, because deployment stopped in preflight;
existing binaries/sealed rollback pairs untouched. Never assume Android downgrade
safe or delete data to roll back. No renewal, beta69 install, gateway deploy,
fault injection, selected-retry, publication or Krasnodar operation.
Installed/public/invitation-page versions remain unchanged. Freeze remains PASS;
this deployment is PARTIAL and not ready for selected-retry.

Next: causally resolve the preserved pre-existing NL startup failure, then resume
the already-authorized renewal/deployment without changing accepted artifacts.
