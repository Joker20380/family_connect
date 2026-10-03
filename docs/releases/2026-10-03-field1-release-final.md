# FIELD-1-RELEASE-FINAL / DIAG-1A — 2026-10-03

## Hosted fixture repair — 2026-10-03

Starting HEAD `fc2b3efcaabbe75195b869d5586de65c0b0dc55c`; same milestone,
Stage5N CLOSED, owner/DIAG-1A PASS retained. No product source or accepted APK changes.
Publication/signing/landing/FIELD widening remain prohibited throughout this repair.

The successful518-focused local path explicitly supplied `FC_TEST_HTTP_ARTIFACT`,
HTTP SHA, sync artifact/SHA, readiness artifact, immutable historical HTTP artifact,
Go1.26.0 and nginx. Hosted broad pytest supplied none of these; Docker's selective
COPY additionally omitted modules/manifests required during collection. This is a
test provisioning defect, not evidence of three separate networking defects.

`scripts/ci_release_fixtures.py` builds closed fixtures from committed source,
checks source commit and every inventory hash before execution, and independently
enforces historical HTTP SHA460e7520. phase0/Linux-control explicitly seed Go modules
and provision before full pytest. Docker consumes only public `git archive` exports,
restores the exact verified tree/commit without host Git configuration, then builds
fixtures in the test stage before collection. Runtime stage is unchanged. Synthetic
keys remain local test data, never production credentials or persistent secrets.

Three formerly hidden fixture assumptions are corrected without removing assertions:
historical cadence uses the pinned historical server instead of the current server;
current preflight requires the explicit current SHA (no permissive fallback);
missing-module tests explicitly import the selected dependency, including lazy ones.
No skip/xfail/conditional bypass introduced. New tests verify public-only exports,
exact source restoration, hash/commit rejection and deterministic sync ZIP metadata.

Local full provisioned pytest:1691 PASS/26 existing environment-dependent skips,
256.21s; new provisioner tests3 PASS. Logs retained in ignored
`state-client-build/field59-ci/`. Hosted rerun remains pending. The earlier client
run37115119418 is terminal: Windows/compatibility/Linux PASS; Android emulator FAIL,
so Android runtime conformance was not executed and is not accepted.

Rollback is source-only: revert the CI/test provisioner changes if necessary; no
production rollback or device data operation is involved. Public51 remains in place.

### First hosted repair run

Source `833ab39f5697d79464a603dcc40617158f84472f`, pushed without release trigger.
phase0 run37119299194 and Linux-control37119299193 now provision successfully and
collect the full suite; the missing25 fixture errors are gone. Both expose the same
remaining operator ZIP failure: Python3.13 isolated execution cannot import namespace
`control` without directory entries. Reproduced with Python3.13.15 in the existing
CI container: before `ModuleNotFoundError: control`, after explicit deterministic
ZIP directory entries `--help` PASS. No operator semantics or Android sources changed.

Docker now reaches all tests (no collection errors); its remaining environment gaps
are root nginx workers unable to read pytest's private static-fixture directories,
missing `/usr/bin/python3` for service-UID DAC probes and missing `/usr/bin/curl`.
Supply tools; execute root-DAC tests separately as root and full suite as a normal
runner, matching the accepted local/hosted execution identity. Do not chmod private
state, run nginx with extra privileges, weaken assertions or bypass root tests.

The first complete prior Android artifact confirms a distinct release blocker:
`AutoRuntimeTest` calls dual-stack `TcpRuntimeTest.traffic()` although Auto TCP only
assigns10.79.0.2 and retains the IPv6 default route fail-closed; binding fd79:fc::2
raises EADDRNOTAVAIL. Manual TCP's dual-stack test passes. Manual AWG also reports
an asynchronous-cleanup profile-edit refusal. Tests and networking are unchanged;
these are not waived or misrepresented as resolved by the Python fixture fix.
Current rerun's Windows2022 compatibility upgrade also failed its broker-restart
assertion; final repeat and terminal Android evidence still required.

## Support HTTP delivery and owner completion — 2026-10-03

This supersedes the blocked Support/status observations below. Same FIELD-1/DIAG-1A;
Stage5N CLOSED. Starting HEAD40e40bb. Android source remains
`5abc2da4878d38687574776932959db284dd9797`, unchanged signed beta59/code59 APK
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`, signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
No production APK rebuild, networking change, reinstall, identity reset or enrollment.

### Authorized prerequisite deployment

- Before09:47:57UTC: existing28/28 aliases verified; owner admission maps to an
  existing non-revoked enrollment and alias. Neither Android nor delivery allocates
  an ID. Source5e0008c makes support-purpose proof completion lookup-only; a missing
  mapping returns unavailable503 without inserting anything. Regression test proves it.
- Clean committed HTTP export5e0008c:
  `ef9f2faf31ab66e119eb44f95f30aab94b9b6d3da11e36958b4689316e996291`.
  Compared with livead71cadb, exactly3 entries change: Friends access, Support IDs,
  HTTP handler. All restricted/runtime networking modules remain byte-identical.
- Successful deployment09:52:52UTC: existing
  `family-connect-friends-http-candidate.service`/loopback18086, same DB/permissions;
  nginx ordinary regex adds only `device/(status|support)`. Normal/restricted routing,
  limits, grants, admission, AWG/TCP and download routes retained.
- Initial validation command `docker exec family-connect-product-https nginx -t`
  used default `/etc/nginx/nginx.conf` and failed on read-only `/run/nginx.pid`.
  Old artifact/config hashes were verified restored before retry. Correct explicit
  `nginx -c /etc/fc/nginx.conf -t` and same-config reload PASS. No DB rollback.
- Protected rollback files/DB snapshot/receipt:
  `friends-access/support-delivery-5e0008c/` on the authorized RU host. Restore only
  previous HTTP artifact/nginx config if necessary, validate explicit config/restart
  HTTP/reload nginx. Never restore the DB or remove the existing alias backfill.

### Owner and authorization results

- Existing private owner instrumentation runs on the unchanged public candidate.
  Initial cached failure remains unavailable until explicit Refresh; MIUI rejects
  shell `input tap`. Only the separate AndroidTest helper was recompiled to invoke
  the ordinary Refresh button; production APK not rebuilt. Correct Friends test
  variant requires `-PfcTestBuildType=friends`; missing-property invocation compiled
  nothing. All initial failed harness receipts retained, not reported as product PASS.
- `supportVisibleCopiedAndStable`, `existingIdentityStillAuthenticates`, then
  force-stop/new-process Support test PASS. ID equals the **pre-deployment owner
  backfill row**, Copy equals that ID; status validates returned reference against
  the existing vault identity. No new registration/invitation consumed.
- Final09:59:02UTC after uninstalling only `.friends.test`: pulled production APK
  SHA/signer unchanged, UID10283, ceDataInode601521, firstInstallTime unchanged;
  actual normal Settings UI shows ID and enabled Copy. Encrypted identity unchanged
  and decrypts, enrollment active, Auto/off retained, no private acceptance components.
- Fresh readiness receipt on59 READY/PRESENT_VALID/ACK_RECEIVED. The prior owner
  Auto/AWG/TCP HTTPS200 evidence remains valid; no networking changes in this step.
- DIAG both typed CONNECTING/RESTORING failure snapshots plus Android MIUI chooser
  PASS. These are synthetic recorder tests, not forced live transport outages.
  Export4695 bytes SHA256
  `1493c2f0051badb6e3f1ed490be64a8329a65bd29a6ae6771d075f83319d5504`;
  ring+incident both contain the bound Support ID. Closed schemas/bounds/privacy
  checks PASS, zero secret/identity/URL/destination-history findings. No recipient
  selected/upload. Synthetic files/export URI grants and test helper removed.
- 16 paced live HTTPS negative probes PASS: missing/invalid auth400/403, malformed
  JSON400, wrong method405, unknown alias403/unknown lookup path404, unknown Support
  identity403, replay403, existing revoked device challenge403 for both purposes.
  Existing status semantics intentionally preserved: an unknown identity with its
  own valid proof receives200 with registered=false/active=false, **no access and
  no enrollment**, not a claimed403. Isolated real-handler/nginx tests also cover
  revocation after challenge and revoked invitation; no production revocation edits.
- HTTP journal13 lines: zero actual registered identity/secret-pattern matches.
  HTTP body logging disabled; conditional nginx probe log has no body/auth/query.
  Private proof/status/challenge bodies are not persisted in acceptance evidence.

### Inventory, validation and release boundary

At09:57:26UTC all six fingerprints unchanged: devices, invitations, alias mappings,
restricted grants, admission bytes and operator audit.28 total/24 non-revoked/4 revoked,
28 stable aliases; platform1 Android known/27 unknown; version1 beta59 known/27 unknown.
Owner operator lookup: active, Android59, Family ACTIVE, readiness READY, admitted.
Readiness is short-lived; this observation is not a perpetual validity claim.
No operator enable/disable executed; unchanged pinned operator keeps audit and cap3.
Current cohort/admission **1 owner**, additional selections0; never wildcard.
Update-offered/pending and legacy manual-install counts remain unknown, not zero.

55 route/access/Support tests and full518 focused Python tests PASS/0 skipped.
Whole-index false positive resolved by splitting the negative PEM test literal;
the exact assertion bytes and secret guard remain unchanged. No scanner exemption.
Tests checkpoint416d938. Existing APK JVM/native/lint results retained.
Protected evidence: `state-client-build/field59-delivery/`; no keys/DB/proofs in Git.

FIELD-1-RELEASE **BLOCKED by hosted CI**; DIAG-1A **PASS** for the defined owner/local-bundle scope.
Hosted platform CI and artifact provenance/download checks remain release gates.
Production59 signing preparation only: min-supported1, mandatory=false, same offline
root, increasing sequence/lease required. No production signature issued yet.
At10:01UTC full public51 download verified36,456,636 bytes/SHA79a2d286; signed-v2
catalog and beta59 APK routes both404. Unsigned production59 payload prepared from
the exact installed APK (draft sequence1/min1/non-mandatory), no offline key accessed;
refresh sequence/issued_at/expiry after CI. This is not install authorization.
Public beta59 APK/catalog/landing publication remains explicitly prohibited in this
continuation; do not change Windows/Linux links. Source-only push1b791c2 completed
after owner acceptance and explicit push approval. No tag/release-trigger commit,
no release assets/catalog key sent to CI. Unrelated health work remains local.
No FIELD widening. After release authorization, follow the existing tester instructions
below: in-place install, no clear/uninstall, send Support ID, await operator, CONNECT.

### Hosted CI stop: exact outstanding release gates

CI source `1b791c2848961ed485d4f1c8300e01c1ed3fb218` has identical Android/carrier/
Android-native source to accepted APK5abc2da. Hosted verification builds do not
replace/re-sign the accepted6d13720 artifact. Final CI notes are a local documentation
follow-up, not another production deployment or automatic CI retry.

| Gate / command | Observed | Expected | Release blocking |
| --- | --- | --- | --- |
| phase0/tests: `python -m pytest -q` | exit1;7 failed,1583 passed,99 skipped,25 errors. Confirmed `KeyError: 'FC_TEST_HTTP_ARTIFACT'` in readiness packaging fixture setup; additional failures need full triage | exit0 with required source-pinned fixtures available | YES |
| phase0/failover: `docker compose build` → `Dockerfile.control:33`, `python -m pytest -q && touch /tmp/tests-passed` | Docker build exit1; pytest exit2,14 collection errors, including missing public runtime/source paths (`test_sync_acceptance.py`, readiness/runtime tests) | complete public test build context, collection/build success | YES |
| Linux control preview: Protocol/crash/packaging `python -m pytest -q` | exit1;7 failed,1606 passed,76 skipped,25 errors; same confirmed missing `FC_TEST_HTTP_ARTIFACT` setup | fixture-provisioned broad suite exit0 | YES |

Relevant authoritative logs:
- [phase0 tests, job111180337783](https://github.com/Joker20380/family_connect/actions/runs/37115119420/job/111180337783): summary10:05:36UTC.
- [phase0 failover, job111180337993](https://github.com/Joker20380/family_connect/actions/runs/37115119420/job/111180337993): Dockerfile/control collection failure10:03:59UTC; bounded build-log artifact11271198754.
- [Linux control, job111180338081](https://github.com/Joker20380/family_connect/actions/runs/37115119469/job/111180338081): summary10:07:22UTC.

Whole-index guard is **PASS in hosted phase0**, not the cause of these failures.
[Windows control37115119444](https://github.com/Joker20380/family_connect/actions/runs/37115119444)
and [Android Friends wire contract37115119419](https://github.com/Joker20380/family_connect/actions/runs/37115119419)
PASS. [Client builds37115119418](https://github.com/Joker20380/family_connect/actions/runs/37115119418):
Linux job111180338239 PASS (GTK/render/interaction/packaging included); Android and
Windows jobs still in progress at inspection, not claimed accepted. No jobs cancelled
or automatically retried. Broader fixture/Docker issues were not hidden by modifying
networking, removing tests, or marking skipped tests as acceptance.

No production59 signature/catalog/APK/landing publication. Next work: triage and
repair CI fixture/context wiring, finish hosted platform acceptance and verify
downloaded artifact provenance, then offline signing **only when authorized release
gates pass**. Publication remains subject to the user's explicit hold; owner-only
admission/cap3 retained.27 other registrations still have unknown version/platform,
so neither automatic adoption nor a numeric legacy manual-upgrade count is claimed.

## Owner-device continuation — 2026-10-03

This continues the same FIELD-1/DIAG-1A checkpoint, not a new milestone. Stage5N
remains CLOSED. HEAD remains `40e40bb14fc1c020a87e09bc054307a6c79a6d22`;
release source remains `5abc2da4878d38687574776932959db284dd9797`.
The earlier sections below describe preparation before the owner reconnected;
this section supersedes their NOT INSTALLED / NO ADB DEVICE statements.

### In-place installation and preservation

Owner ADB serial31ce63ba, Redmi Note9 Pro/Android12. Before: package
`com.familyconnect.app.friends`, `0.1.18-canary58-physical`/58, UID10283,
firstInstallTime `2026-09-19 17:30:26`, ceDataInode601521. Activation true, Auto,
NL selected, private acceptance override OFF. Existing identity, configuration
and encrypted readiness were fingerprinted without exporting plaintext secrets.
The58 installed APK had SHA256
`91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`.

Exact command (09:14UTC):

```sh
adb -s 31ce63ba install -r state-client-build/field59-final/artifacts/FamilyConnect-Test-0.1.18-beta59.apk
```

Observed `Success`; no uninstall of Family Connect, pm clear, reenrollment, identity
replacement, production APK rebuild or networking code change. After: beta59/code59,
same package/UID10283/firstInstallTime/data directory/inode601521. Pulled installed
APK hash equals `6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`;
signer remains `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Installed manifest excludes private acceptance components. The public non-debuggable
build correctly denies `run-as`; same-signer private instrumentation provided the
subsequent safe preservation checks instead of weakening the app.

Immediately after update, all three ciphertexts match byte-for-byte:
`friends-identity.enc`, `friends-configuration.enc`, `restricted-readiness.enc`.
Identity and readiness decrypt with the retained Android Keystore keys; activation
true and cached normal provisioning usable. Final post-test identity fingerprint
still matches; activation and Auto remain. No raw identity/public keys were shown.
The pre-update readiness receipt was READY/ACK_RECEIVED, expiring09:16:39UTC.
Normal product activity on59 subsequently refreshed short-lived readiness:
READY, both PRESENT_VALID, orchestrator usable, ACK_RECEIVED, observed09:34:12UTC,
expiry09:47:58UTC. This is retained identity/enrollment plus an ordinary refresh,
not a reset or a promise of validity after expiry. No manual server renewal ran.

### On-device validation

| Check | Observed result |
| --- | --- |
| Normal launch/version after fresh process | PASS; beta59 visible |
| Auto, real normal CONNECT | PASS; AWG selected,7.275s, VPN present, HTTPS200 |
| Explicit AWG | PASS;1.260s, VPN present, HTTPS200 |
| Explicit TCP | PASS;1.258s, VPN present, HTTPS200 |
| Device identity/data/activation/readiness preservation | PASS as bounded above |
| Previously compiled owner-safe instrumentation |5 PASS |
| Persisted CONNECTING→FAILED incident | PASS with synthetic typed events on-device |
| Persisted RESTORING→FAILED incident | PASS with new incident ID, synthetic typed events |
| Send diagnostics | PASS; real `android/com.android.internal.app.MiuiChooserActivity` |
| Export privacy | PASS;4675 bytes, bounded closed schema, no forbidden content |
| Support ID / Copy / restart stability | BLOCKED: unavailable, Copy disabled, no ID to compare |
| Live device-status API check | FAIL:404 route, see below |

Transport checks used the existing visible transport picker and CONNECT dial through
instrumentation; no normal-candidate exhaustion, private acceptance Activity,
second stack, radio change, gateway change or transport override. The HTTPS request
was a test to example.com; no traffic body was logged. Each successful test used the
ordinary disconnect action and restored Auto. Original emulator-only suites that
clear profiles/managed stores or require10.0.2.2 were deliberately NOT run on the owner.

Five existing tests: `DiagnosticsProviderTest`, both `ControlProtocolRuntimeTest`
methods, `AppUpdateRuntimeTest#verifiesInstalledSignerAndRejectsDowngradeAndInvalidArchive`
and `AppUpdateRuntimeTest#providerOnlyAllowsExactReadOnlyCacheApk`.
Additional private owner probes exercised preservation, normal product controls,
diagnostic persistence/export and final cleanup. Only the separate test APK was
packaged/signed; the beta59 artifact was never rebuilt or replaced. Initial owner
probe launch-idle/selector mistakes were corrected in that private harness; original
logs are retained as `*-initial-harness-*` / `*-v2-harness-*`, not mislabeled as
network regressions. Final transport checks above all pass.

Incident validation injected typed events into the existing DIAG recorder only;
it did NOT force a real transport outage, repeat Stage5N physical acceptance or
claim a spontaneous production incident. The Android confirmation opened the actual
share chooser; no recipient was chosen and nothing was uploaded. Exact exported
bundle SHA256 `e0f31b384a8b4c04230a01de00be23a8980eaccf6b37e3a417ffd29e038dd0e2`.
Both ring and incident use the fixed field schema, enum-like codes, UUID correlations,
coarse CELLULAR network class and no destinations, DNS history, credentials, keys,
identity, messages, room URLs or tokens. `device_support_id` is null: DIAG support
correlation remains incomplete until authentic server delivery works.

### Exact failing gates — publication blocked

**Support ID delivery/UI (release-blocking):**

```sh
adb -s 31ce63ba shell am instrument -w -r \
  -e owner_serial 31ce63ba \
  -e class com.familyconnect.app.OwnerFieldAcceptanceTest#supportVisibleCopiedAndStable \
  com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner
```

Expected: registered `FC-XXXX-XXXX` visible, Copy enabled/matching, stable after restart.
Observed: `Support ID unavailable: server delivery has not been deployed` assertion;
unavailable message visible and Copy disabled again after a real process restart.
Copy correctness and ID stability are NOT VERIFIED, not silently passed for null.
Host route probe `POST /friends/device/support` with empty JSON returns404.
Logs: `state-client-build/field59-owner/support-instrumentation.log`,
`support-result.json`, `final-device.json`.

**Existing device-status API (release-blocking failed live check):**

```sh
adb -s 31ce63ba shell am instrument -w -r \
  -e owner_serial 31ce63ba \
  -e class com.familyconnect.app.OwnerFieldAcceptanceTest#existingIdentityStillAuthenticates \
  com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner
```

Expected: the existing signed identity proof yields active device status.
Observed: `java.io.IOException: Test access unavailable`,
`FriendsAccessAndroid.post:54`, `deviceStatus:106`. An independent empty-JSON
`POST /friends/device/status` route probe returns404 (not an authorization rejection).
Logs: `state-client-build/field59-owner/enrollment-instrumentation.log` and
`enrollment-result.json`. This missing route is NOT evidence of lost enrollment:
unchanged identity/configuration, activation, working transports and subsequent
authenticated READY/ACK evidence remain intact. Nevertheless the API test did fail.

All local evidence is protected under `state-client-build/field59-owner/`.
Private test sources, APKs, exported test bundle and logs are not published or added
to Git. The two probe commands require reinstalling that private test APK: it was
removed after validation, not left as an acceptance surface on the phone.

### Cleanup and release boundary

Three test-generated diagnostic files removed by matching the synthetic connection
ID / exact export hash; export URI permissions revoked. The separate
`com.familyconnect.app.friends.test` package was uninstalled; the actual Friends app
was NOT uninstalled or cleared. Final09:38:25UTC: exact signed59 installed, fresh
normal app process, Auto/disconnected, VPN count0, Support unavailable/Copy disabled,
UID/data inode unchanged, no private acceptance component. No downgrade attempted.

Public Android catalog re-read: still beta51/code51. No catalog signing, landing
change, publication, hosted CI advancement, server deployment, new admission,
commit or push. Existing selected owner is the only cohort member; no widening.
One physical beta59 installation is now evidenced; no claim that all users updated.

The user's continuation permits Support HTTP deployment only after **all** owner
checks pass, while the missing Support ID depends on that deployment. This
prerequisite conflict is reported, not bypassed by seeding a local alias or deploying
early. Required next decision is to permit the already-defined server delivery/route
prerequisite before rerunning these blocked owner checks. Hosted CI/source-guard
resolution and production publication evidence remain later gates.

**FIELD-1-RELEASE = BLOCKED. DIAG-1A = PARTIAL** — on-device ring/snapshot/share/privacy
pass, but registration Support ID delivery/copy/stability remain incomplete.

## Boundary and version policy

Starting HEAD `1790793d2d2412896a6c5e23482c15c0def6b0c0`; Stage5N CLOSED.
Previous clean source `b952c3b8a69c845913e01508ca1d722168698a07`, local candidate
SHA256 `8229a36e8b176aa49346f3bf106f4f1229cb492a47c1c50e86593ddcb4c85a3b`
is retained in its original private artifact directory, never published or overwritten.
Live legacy catalog still advertises beta51/code51 at task entry. Repository release
rules forbid replacing **published** artifacts; user explicitly permits rebuilding
unpublished59. Revised candidate retains `0.1.18-beta59`/59,
`com.familyconnect.app.friends`, existing beta signing certificate
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.

No ADB devices at entry. The owner is last evidenced on private58, not freshly
observed. No install/uninstall/clear/enrollment operation ran. Acceptance and
publication cannot be claimed; no signed production59 catalog, landing switch,
APK publication, push, tag, or FIELD expansion is authorized by this checkpoint.

## Support ID foundation

Random eight-character human-safe alias `FC-XXXX-XXXX`, database UNIQUE constraint
with collision retry, one immutable mapping per existing device registration.
No deterministic derivation from identity; not an authentication or invitation token.
Additive `device_support` and `field_support_audit` tables only. Backfill includes
revoked records and does not change devices/invites/grants or resurrect registration.
New registrations receive aliases; migrated legacy records retain their original keys.

`POST /friends/device/support` requires existing single-use signed device proof,
separate `support` purpose, active registration/invitation and bounded app metadata.
Response contains only schema and alias. Existing activation/status wire contracts
are unchanged. No new public operator endpoint. Android caches the alias against
its existing private registration reference; offline UI never displays raw identity.
Settings → About / Diagnostics provides version, alias, copy and refresh.
DIAG uses this alias or null, replacing the previous unrelated local UUID; event
recording does not decrypt identity on every event. No automatic diagnostic upload.

`python -m control.friends.support_admin --db <existing-db> backfill|inventory|audit`
and `--admission <authoritative-admission.json> --support-id FC-XXXX-XXXX lookup`
are local operator commands. `scripts/package_support_operator.py` produces an
isolated deterministic source-only `.pyz` for the existing locked runtime.
Safe lookup: alias, optional label/platform/version/last_seen and its source,
registration/revocation, Family grant/readiness and admission states. No key, raw
identity, credential, Family ID, destination or room URL is returned.

Explicit `enable-field --expires <unix-seconds>` / `disable-field` use existing
grant and signed CRL machinery, the configured admission authority and an operator
file lock. Max3 unique explicit devices; wildcard rejected, sole owner retained.
Revoked registration cannot be enabled. Existing admitted expired grants require
the existing explicit grant-renewal operator, not implicit renewal by this command.
Disable revokes the grant before CRL/policy publication. Failed enable revokes its
new grant; incomplete multi-resource operations remain visible in audit for repair.
Audit records timestamp, Support ID, previous/desired state and PENDING/APPLIED/
INCOMPLETE outcome; no secrets. Never treat INCOMPLETE as successful admission.

## Deployment / rollback

Backfill can run independently of Android publication after a protected on-host
SQLite backup. Compare all preexisting table rows before/after; preserve admission
file bytes. Do not recreate/initialize the registration database. Source-only
operator can be removed on rollback; retain additive mappings so aliases stay stable.
Do not restore a stale whole DB over newer enrollment or delete Support IDs.

Authenticated delivery requires the new closed HTTP artifact and the ordinary
ingress route extension `device/(status|support)`. Do not rerun the full historical
installer or change gateway configuration to add this route. Verify isolated HTTP
contracts before a narrowly scoped existing-runtime transition. Until deployed,
Android shows unavailable and permits explicit refresh, rather than inventing an ID.

Initial release policy remains latest59, minimum_supported_version1,
mandatory=false (`mandatory_after=0`). Use the accepted offline update root only
after platform/release acceptance. Publish both legacy and signed discovery catalogs.
Public51 has a manual Settings checker; old builds lacking it require one invitation
page update. Exact per-version populations are unknown, not inferred from total
registrations. Windows/Linux links and catalogs are out of scope and unchanged.

## First tester instructions (after publication)

1. Open your normal Family Connect invitation/link.
2. Install the offered update **over the existing app**; approve Android installation.
3. Do **not** uninstall, clear app data or reenroll.
4. Open Family Connect.
5. Settings → About / Diagnostics → Copy Support ID; send it to the operator.
6. Wait for operator confirmation for this exact registration.
7. Press CONNECT normally in Auto on your real network; no diagnostic exhaustion.

Keep the owner; select only1–2 additional trusted physical devices, ideally one on
a naturally restricted cellular network. Application version is independent of
restricted admission. No wildcard or expansion beyond the initial2–3 cohort.

## Revised candidate evidence

Clean committed source `5abc2da4878d38687574776932959db284dd9797`, exported using
`git archive`, no source overlays:1697 source files plus38 verified generated/native
inputs. Inventory SHA256 `5143e0b09558d7a83679a998972e0568b5d332916e5911f2f0c342dc0329085b`;
local evidence under `state-client-build/field59-final/`.
APK `artifacts/FamilyConnect-Test-0.1.18-beta59.apk`,49,609,595 bytes:

`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`

Existing beta certificate above verified with APK v2 signing and16KiB alignment.
Only the protected beta APK key was used in memory; offline update-root key unused.
No private acceptance components in manifest or DEX; required production/Support ID
classes present; non-debuggable, backup disabled, no cleartext. Native source remains
`061595376fa65ae38725ed75baac769d71623d92`; verified native bytes reused, not rebuilt:

- AWG `1910ccac238884dd55120917c509571117f2aa2e95d10e9255ea00a069738517`.
- Restricted `0307df7e41bd2a002ee9cde37002862d5c6a445e319c9ea297829975b7e6da21`.

Orchestrator/transport/fail-closed code unchanged. Existing native JNI symbols match;
JNI on-device runtime is NOT RUN. No new physical acceptance surface was packaged.

226 app JVM tests and163 overlapping control JVM tests PASS; lint0 errors/36 existing
warnings; assemble and Android instrumentation compilation PASS. Five native package
race tests and vet PASS (bootstrap, Family session, whole-device, underlay, TCP).
Initial expanded Python run504 PASS/6 missing-nginx skips; final run with the verified
nginx1.30.4 executable **510 PASS,0 skipped in85.70s**. Unlike the previous partial
task, all historical/closed HTTP,
sync/readiness, Java golden, Go and synthetic APK-signing fixtures are supplied.
Source-only operator reproducibility/isolation and actual packaged Support endpoint
authentication/replay tests PASS. Instrumented UI/copy/share tests have NOT run.

Whole-index guard still reports the unchanged negative assertion in
`tests/test_readiness_adapter_packaging.py:283` containing a PEM-header literal.
This is not private-key material; no broad scanner exception or weakening was made.
It remains a recorded release check failure, not a claimed all-green result.
All27 changed-task source files:0 guard findings. Signed APK/nested Python scan:
1074 entries,0 findings after one previously reviewed byte-pinned stdlib false positive.
Docs links and `git diff --check` PASS. Hosted platform CI and actual owner runtime
acceptance remain outstanding. Both unrelated VPN-health files match their original
byte hashes; the41-line unrelated STATUS additions remain unstaged, not committed.

## Production backfill — executed08:50:29UTC

Authorized RU host only. Source-only operator artifact SHA256
`b6fe9220590524905cd98580c083bfd985d80cd5d01391ae7c2b5c4152c995b7`
installed at `/opt/apps/family_connect/support-operator-5abc2da.pyz`.
Protected backup and result receipt:
`friends-access/support-backfill-5abc2da/{before.db,result.json}` on that host;
no database/keys copied locally or committed. Backfill under a SQLite write lock
preserved all rows in13 preexisting tables and the exact admission file bytes.

| Authoritative record inventory | Count |
| --- | ---: |
| Total records / assigned Support IDs |28 /28|
| Non-revoked / revoked device records |24 /4|
| Platform known / unknown |0 /28|
| App version known / unknown |1 /27|
| Latest known version |1 private canary58/code58|
| Records evidenced on beta59 |0|
| Restricted admission / wildcard |1 /no|

Version knowledge comes from an existing signed-device readiness receipt; platform
is NOT inferred from the version string. No per-device update-offered/pending
telemetry exists; exact legacy/manual population is unknown. Zero evidenced59
does not prove every unknown installation is on another version. No DAU claim.

No enable/disable action was run against production. Existing owner admission stays
unchanged; no additional testers selected. Only preparation for1–2 more devices.
Operator lookup/actions are implemented and tested; the source-only operator is
available on-host. **The new HTTP runtime/ingress has not been deployed**, so Support
ID delivery to Android and automatic assignment for new registrations on the old
runtime remain pending. Do not mistake completed backfill for completed delivery.
No gateway, transport, CRL, issuer, enrollment or invitation change occurred.

## Owner, publication and remaining work

ADB still returned no devices at the final check. Neither the previous8229a36
candidate nor this revised6d13720 candidate was installed in this task. Same package
and signer are verified statically, but owner UID/data/Device Identity/enrollment/
readiness continuity, Support ID visibility/copy, normal Auto/AWG/TCP, incident
snapshot and Android share/export privacy inspection remain **NOT RUN**.
Server-side identity-preserving backfill is not evidence of Android update acceptance.

Production catalog remains beta51/code51; advertised SHA256
`79a2d28667332ea442eae1b895b4fc632b52734cbed1e75bd95f32b7175ad366`.
No actual public59 download exists to verify. The previous task independently
verified public51 bytes; this task re-read its unchanged catalog, not a new APK
download. Landing and invitation flow untouched; Windows/Linux untouched.
No production59 manifest signed/published; min1/optional is planned, not active59
policy. No update discovery of59, mandatory shutdown, push, tag or release.

Next: connect/unlock/authorize the intended Redmi; deploy the tested authenticated
Support delivery with the existing narrow HTTP transition and ingress checks;
perform both requested in-place preservation/functional checks without data clear.
Resolve the recorded source-guard false positive and hosted release validation
without reopening Stage5N. Only after owner acceptance publish immutable59, both
catalogs, Android landing metadata, verify downloaded bytes and commit/push the
accepted publication checkpoint. Never widen FIELD beyond2–3 explicit devices.

**FIELD-1-RELEASE = BLOCKED (owner acceptance/publication). DIAG-1A = PARTIAL
(local implementation/tests pass; device acceptance outstanding).**
