# Android beta64 — paired delivery diagnostics candidate, 2026-10-04

## Current gate

**Exact-source CI/signing, owner in-place64 and paired gateway acceptance PASS.**
User requested the next release/owner-validation stage after the
[source diagnostics checks](2026-10-04-paired-delivery-diagnostics.md).
Version `0.1.18-beta64`, code64, source
`ce73ddf3e0dfc25546850b083b7dae4680720397`, pushed to main from de7cacd with user approval.
No tag or GitHub Release created. Diagnostics/tests/version/release and required baseline
docs committed. The existing02.10 health report was included solely because HEAD
STATUS/PLAN already linked to the then-untracked file; clean-export checking found it.
Five other dirty historical/renewal documents remained outside the source commit.
This continuation preserves those edits; the renewal runbook additionally gains the
observed RU/NL directory-generation gate. **Owner64 installed; matching gateway deployed;
targeted64 published and verified19:14UTC.** No default/catalog/invitation promotion.
User authorized one Krasnodar trial, gated on tester in-place64 and fresh readiness.

## Initial read-only preflight (before release/owner rollout)

- GitHub main readback remains de7cacd. Latest Client builds run37214189165, attempt2,
  completed SUCCESS for beta63; it is not candidate64 acceptance.
- `git ls-remote --tags origin '*beta64*'` returns no matches. Sandbox SSH configuration
  access failed first; approved normal execution completed successfully.
- `2026-10-04T18:08:23Z`: beta64 HTTPS download HEAD returns404; no release bytes claimed.
  Existing default route/catalogs were not modified or reverified in this preflight.
- Same authorized owner Redmi31ce63ba connected over ADB. This checks connectivity,
  not current installed APK bytes, authenticated readiness or identity preservation.
- Previous material bound `2026-10-04T17:30:19Z` has elapsed. No renewal attempted here;
  renew/revalidate the complete chain immediately before physical acceptance.

## Version and artifact separation

All four exact-source workflows completed SUCCESS by18:32:38UTC:

| Workflow | Run | Accepted attempt |
|---|---|---|
| phase0 |37223645511|1|
| Linux control preview |37223645532|1|
| Client builds |37223645645|1|
| Android Friends readiness wire contract |37223645492|2|

Readiness attempt1/job111498774820 failed in the Python HTTP/Android contract step
after Java success. Local golden-classpath rerun passed113 tests;4 optional locked-Go
compatibility cases skipped (FC_TEST_GO absent, matching that workflow's optional path).
One unchanged-source failed-job rerun passed; no tests/assertions/source relaxed.
The initial failure is retained and its cause is not established as fixed. Public log
download403 and coarse annotations did not provide a narrower reliable diagnosis.
Client Android race/contracts, unit/lint, emulator runtime, restricted native/gateway
packaging and exact release payload passed; Linux/Windows/Windows compatibility passed.

Artifact11311153048, `FamilyConnect-Android-restricted-arm64`,58404609bytes:
ZIP SHA256 `48edede84048c8816eb4df35f897e0292ee637cfe7004dc42dc663d1b263ba7a`.
Initial transfer403 was followed by a fresh-link CDN1010 response; a standard HTTP
User-Agent resolved the transfer. No artifact bytes were accepted before digest match.

- Unsigned APK SHA256 `4dde08a241e992c3225f4cd380751ae98571fcfdbcb26efb11b8264047c84878`.
- Signed `FamilyConnect-Test-0.1.18-beta64.apk`,49671035bytes, SHA256
  `b1a9f62116265b13a8482292175d3a685dca23ad3a5be0e4af5ef995a4d32d69`.
- Signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`,
  existing local protected beta key; no rebuild, key upload or key output.
- Restricted native SHA256 `d9c709917279a5e721a74f0e7a26d9c9346d3b162393021779e1fa19800ecf8c`.
- Matching CI gateway SHA256 `f71b7e7bb92d7f312d210d41ebf200cf4416ed73ca7fe3a33ae2e13d4d3f2ebf`,
  subsequently deployed18:59UTC with loaded-executable hash verification.

Source/provenance pins, ARM64-only,16KiB alignment, non-debuggable, allowBackup=false,
cleartext=false, no private diagnostic components and privacy scan PASS before/after
signing.1074 signed entries scanned; known immutable stdlib Basic-scheme false positive
remains explicitly reviewed, no credential findings. Local receipts/artifacts are under
ignored `state-client-build/field64-ci/`; the signed APK is under its `signed/` directory.

Preserved pre-update owner63 APK SHA256:
`ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`,
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Tester last receipt62; default/updater/invitation60. Last verified gateway binary:
`6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09`.
These are the old baseline bytes; the later owner/live readbacks are below.

## Owner and gateway execution, 04.10 evening UTC

Owner Redmi31ce63ba updated in place63→64 using the accepted signed CI APK, not a
local product rebuild. Before/after UID10283, data inode/first installation, encrypted
identity, enrollment fingerprint, activation and Support FC-4D8Q-REEG matched. All
encrypted files matched immediately after installation; readiness subsequently changed
only through authenticated import. Final pulled installed APK matches full b1a9f621
SHA/signature above. Private same-signer instrumentation was built separately, then
removed; no production signing key or identity material copied to server/CI/Git.

Preflight18:48UTC found bootstrap active/restarted once but still serving the leaf
expired17:30:19UTC. A fresh directory alone had not renewed that certificate.
Existing issuer4/authority remains valid until05.10 13:28:47UTC; existing two grants
remain non-revoked, revisions3/1 and admission unchanged. Renewal reused this authority,
generated a new gateway leaf and CRL4651 under the already accepted14400s policy,
serialized RU sync, published with discovered UID/GID979/mode0600, and restored timer.
Native positive/negative authority validation and actual service-user readback PASS.
TLS1.3/http1.1 control-listener signature/hostname/exact-loaded-leaf validation and
stable35s PID/NRestarts0 PASS. New gateway leaf expires **04.10 22:57:31UTC**.

At18:59UTC the matching ce73ddf gateway f71b7e7b replaced6773423c; authoritative
bootstrap acceptance PASS with PID4077612/NRestarts0 and `/proc/PID/exe` hash match.
The unit, HTTP/API runtime and ordinary AWG/TCP services were not replaced. Current
directory expires22:59:29.319481947UTC; owner fresh native READY/ACK receipt expires
epoch1791154769 with14240s remaining at import. **Operational minimum is the earlier
gateway leaf22:57:31UTC**, not a new four-hour window measured from test completion.

First owner attempt imported an older, still-valid RU directory (expiry1791154662)
just after NL seed replacement. READY/ACK passed, but startup ended after33s with
BOOTSTRAP_UNAVAILABLE, no session tag and no injected RTP loss. The fixture still
removed its library/filter in finally. The stale-generation evidence and failed attempt
are retained; no product failure is erased or declared fixed. After verifying RU's new
directory, a fresh authenticated import (without clearing identity/cache floors) and
the unchanged native test passed. The operator runbook now explicitly gates on matching
RU/NL generation before refreshing the client. Gateway-leaf auto-renewal remains absent.

## Physical acceptance and paired evidence

- AWG/TCP HTTPS200 and enrollment preservation PASS on installed64.
- Genuine restricted session/HTTPS200 established; a private process-local RTP receive
  filter induced native RELIABLE_RETRY_EXHAUSTED after8 retries. No policy cause or
  native failure snapshot was injected. Filter removal followed by explicit production
  `AutomaticConnection.poll()` classified NETWORK, cleaned old native handle, obtained
  fresh BOOT-1/session and returned HTTPS200. Exactly one restoration success observed.
  Restricted-only candidate selection is test-only; this is not unattended UI scheduler
  coverage or proof of Russian mobile-network stability.
- Native pinned failure: send_base21/send_next29, pending8/head_retries8, receive_next22.
  Server pinned failure: send_base22/send_next29, pending7/head_retries8, receive_next29;
  ACK age757ms versus progress age9299ms. The known injected gateway→phone RTP loss
  explains this controlled case, not the original field failure.
- Actual saved production ring/incident captured before synthetic UI diagnostics:
  combined JSON45480bytes. Original32 client/55 server events; restored28/58.
  Both lifecycle joins and all four Support/Connection/Incident/session-tag lookups
  PASS, server sequences gap-free and cleanup complete. Client delivery samples8/6,
  server11/13; client last8 bound and pinned first-failure delivery retained.
  Strict endpoint allowlist/privacy and record budgets PASS.
- Both comparisons expose cumulative flow and fragment boundaries. Sender-head
  observations are client→server consumed and server→client not buffered at the
  sampled receiver, **not simultaneous**. No matching queued/written fragment ID was
  found in these retained asynchronous snapshots; do not infer a specific drop boundary
  or RKN involvement. Original field DATA loss remains unlocalized.
- Initial journal read was too early for restored server cleanup (34 events); it was
  retained separately. Later read of the same two tags reached58 events/cleanup PASS;
  no test connection was repeated for this journal completion.
- AUTH startup denial and connected-denial cleanup/no new descriptor, cancellation
  before startup, diagnostics sharing/provider/privacy, compiled security checks,
  Support/restart and final cleanup PASS. AUTH denial is a local fixture override,
  **not a real server revoke**; actual authority-negative contracts remain CI coverage.
- Final preservation helper first compared numeric fixture UID10283 to shell string
  `"10283"` and stopped before test-package removal. Normalized comparison, unchanged
  exact UID/inode/data path/first-install assertions and pulled APK verification passed;
  this was a harness type mismatch, not application data loss. Test package absent,
  process-local filters removed with zero cleanup errors and probe library deleted.

Private evidence stays under ignored `state-client-build/field64-owner/` and
`state-client-build/field64-server/`; initial stale-directory and early journal receipts
are retained separately. No client private material is part of this report.

Final live readback19:05:41UTC: same PID4077612/NRestarts0, loaded f71b7e7b and exact
renewed leaf; CRL4666 expires23:05:27UTC. Server owner receipt64 READY/ACK and tester
last receipt62, both admitted/non-revoked. Device/invite/grant/support/admission/HTTP
invariant hashes and ordinary service PIDs/start times match the pre-renewal baseline.
Default update JSON and invitation HTML hashes unchanged. Public64 HEAD returns404;
this availability probe did not verify the public endpoint's certificate and is not
artifact/signature validation. No public64 artifact or update-catalog change occurred.

## Checks and next actions

Diagnostics source previously passed full Go, six-package race, Android246/lint and
Python52 focused checks. These are local tests, not exact-source hosted release CI.
Candidate64 rerun: `:app:testFriendsUnitTest :app:lintFriends` PASS, **246 tests**,
zero failures/errors/skips; Python focused suite **52 passed**. Earlier documentation checker
**473 files/2869 links**, zero errors; `git diff --check` PASS. Existing Gradle
deprecation/cache-watcher warnings remain. The product artifact subsequently came from
accepted hosted CI; only private instrumentation was assembled during physical acceptance.

1. DONE scoped source commit/push, clean-export docs473/2862 links checked without
   unrelated working-tree changes; existing broken dependency resolved explicitly.
2. DONE all four exact-source workflows, download/digest/provenance checks and offline
   signing; failed readiness attempt retained separately from accepted retry.
3. DONE saved old gateway binary/settings and owner baseline; in-place64 preservation
   and final installed bytes/signer verified, private test package removed.
4. DONE renewal/full-chain validation, authenticated native READY/ACK and matching
   gateway deployment; exact effective bound and failed initial import attempt above.
5. DONE paired saved diagnostics/journal, cleanup/new session, real exhaustion recovery,
   AUTH/cancel and ordinary transport/privacy checks, with stated fixture limitations.
6. DONE targeted64 publication/downloaded SHA/signer/HTTPS200 verification below.
   DONE tester64 ACK confirmation below. NEXT fresh current-directory fetch/native
   READY/ACK, then one authorized Krasnodar trial. Tester64/default/catalog/invitation60;
   no mobile result or original field-loss/RKN conclusion. Revalidate full chain.

Owner-stage documentation check:473 files/2870 links, zero errors; `git diff --check` PASS.
No product code changed in this execution stage; prior platform CI remains the accepted
release evidence, and private instrumentation/server receipts are the new physical checks.

## Targeted publication, 04.10 19:13–19:14UTC

User explicitly requested the link and a Krasnodar attempt. Published the already
accepted signed APK, without rebuilding/resigning:
[FamilyConnect-Test-0.1.18-beta64.apk](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta64.apk).
Public download19:14:24UTC: verified HTTPS certificate/HTTP200,49671035bytes,
SHA256 `b1a9f62116265b13a8482292175d3a685dca23ad3a5be0e4af5ef995a4d32d69`,
original signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Server upload/digest and nginx syntax passed; only the Family Connect HTTPS container
was reloaded after adding exact version-specific routes. All older downloads, ordinary
service processes, admission/grants/enrollment/Support, invitation HTML and both update
catalogs unchanged. Default APK60 independently downloaded and hash checked; signed
catalog signature/version60 validated. No GitHub Release/tag or default promotion.
Private receipts: ignored `state-client-build/field64-direct-delivery/`.

Publication documentation check:473 files/2879 links, zero errors; `git diff --check`
PASS. RU/EN client/getting-started guides and README pointers updated locally; no
documentation commit/push performed in this delivery turn.

Fresh readback19:11UTC confirmed gateway f71b7e7b active/NRestarts0, actual loaded
renewed leaf22:57:31UTC and issuer4/CRL/directory valid, both admitted devices non-revoked.
No server renewal/reload was needed for this publication; effective window ends
**05.10 01:57:31 Moscow/Krasnodar time**. Recheck if the test is delayed.

**Outstanding tester gate:** last server receipt is still62, with older directory
expiry04.10 21:32:03UTC (epoch1791149523), not the current22:59:29UTC generation.
In-place installation alone does not force a new fetch: `RestrictedCache.attempt`
skips valid cached material while expiry is more than300s away. Reopening64 can ACK
the old cache with version64; that is not evidence of current seed reachability.
The ordinary refresh threshold for that observed cache is21:27:03UTC, subject to
foreground scheduling/backoff/network/native validation. Do not promise immediate
freshness, clear app data/security floors, alter the device clock or revoke/recreate
the identity. Ask the tester to install over Wi-Fi, keep VPN off and report completion;
then verify a **new authenticated fetch/native READY/ACK for the current directory**
before the one mobile attempt. A safe early-refresh mechanism remains an engineering
follow-up if the unchanged cache prevents that gate. No tester install/fresh fetch or
new Krasnodar result is claimed by this publication.

After the gate, use one Auto attempt over mobile data; record time and export JSON
after a disconnect before manual reconnect. Join it to the gateway by the retained
Support/Connection/Incident/session-tag bindings. This tests diagnostics and recovery,
not an already-established fix for the original delivery stall.

## Tester update readback, 04.10 19:23UTC

After the user reported updating, read-only RU evidence confirms authenticated ACK
at19:21:49UTC from beta64/code64 with the same FC-YHQB-9VJN identity/Support binding,
admitted and non-revoked. This is runtime version evidence, not a remotely pulled APK
digest. **Fetch remains17:39:16UTC**, revision1/minimum CRL4505 and expiry21:32:03UTC;
the receipt is READY but is a new ACK of the previous cache, not fresh readiness for
the replacement seed. No mobile attempt was requested after this readback.

NL19:23:35UTC: same PID4077612/NRestarts0 and loaded f71b7e7b, matching gateway leaf
valid22:57:31UTC. CRL4699 expires23:23:30UTC; issuer4 and current RU directory remain
valid. No credentials, admissions, server runtime or APK changed during this check.
Evidence is private under ignored `state-client-build/field64-tester-readback/`.

Confirmed limitation: `RestrictedCache.attempt` skips still-valid cached material
with more than300s remaining; `FriendsRestricted.prewarm` may first re-ACK that cache
using the new app version. Ordinary eligibility starts21:27:03UTC (05.10 00:27:03
Moscow/Krasnodar), not a promised refresh/connection time. Earlier owner acceptance
used an explicit authenticated fetch, so it did not establish automatic replacement
of the tester's still-valid old directory. Next engineering step is safe early refresh
with bounded retries and unchanged authority/anti-rollback checks if testing sooner;
otherwise wait for verified ordinary fresh fetch/native READY/ACK within revalidated
gateway lifetime. Do not clear identity/cache floors, alter clocks or revoke/re-enroll
to force it. Original field delivery failure remains unlocalized.

## Rollback

Targeted-route backup/receipt:
`185.251.89.19:/opt/apps/family_connect/release-beta64-paired-20261004`.
To withdraw this download, remove only its added exact routes from current nginx
configs, preserving later edits; syntax-check and reload only Family Connect HTTPS.
Retain immutable APK bytes; never overwrite64 or modify default60/catalogs for rollback.

NL binary backup: `/opt/apps/family_connect/restricted-materials-stage-20261001/field64-binary-ce73ddf/bootstrap-broker.previous`
(SHA6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09).
Credential backup/receipts on authorized hosts are under
`/opt/apps/family_connect/restricted-materials-stage-20261001/field64-renewal-20261004`.
If rollback is needed, stop bootstrap, atomically restore the previous executable with
observed ownership/mode, retire its directory, run authoritative bootstrap acceptance,
verify loaded hash/TLS and RU/NL directory propagation. Keep **current valid materials**,
never restore the expired credential backup or lower security floors. No rollback ran.
Android rollback must use an accepted forward-fix/revert release with a higher code,
not data clear or assumption that version downgrade is allowed. Keep all prior APK
bytes and routes immutable; do not alter default60 distribution for owner testing.
See [beta63 accepted baseline](2026-10-04-beta63-recovery-candidate.md) and
[material renewal runbook](../../deploy/friends/restricted/GATEWAY_RENEWAL.md).
