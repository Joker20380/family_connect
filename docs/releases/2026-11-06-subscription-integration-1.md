# SUBSCRIPTION-INTEGRATION-1 — source integration and canonical packaging

## Candidate and gate

Separate worktree `/tmp/fc-subscription-integration-20261106`, branch
`integration/subscription-20261106`, based on remote main
`41b4e6e034efc3e51446f383f2fbaedee3ad5a67`. Merges feature
`e47726c86535e2fa78378558b5ac077921067c04`, not a checkout replacement.
Only STATUS/PLAN conflicted; both subscription evidence and main's independent
bootstrap/renewal entries are retained. Main's dirty worktree is untouched.
Gate OPEN until ordinary PR checks pass and the remote merge is verified.
No `[skip ci]`, branch-protection bypass, deployment or installation is authorized
by this checkpoint. GitHub-hosted existing CI is independent of the occupied host.

Prepared [PR1](https://github.com/Joker20380/family_connect/pull/1).
First integration merge checkpoint `a71de948dd479f993e4b5f3d9b44ce11e7d22517`
was pushed and read back from the remote. Six committed-source paid-bundle and
source-drift tests pass; the canonical bundle builds reproducibly from this commit.
Initial push hit a transient DNS failure; ordinary retry succeeded without changing
network settings, history or authentication.

Integrated scope: one-use authenticated subscription purpose/HTTP schema1,
transactional canonical paid_beta snapshot/event, Android decoder/screen/encrypted
projection, revision/event fences/durable dedupe, real-focus read acknowledgement,
post-save and normal-start delivery on the existing worker. No independent incoming
payment channel, billing authority or background subscription polling is introduced.

## Canonical delivery versus live overlay

The [ANDROID-3 receipt](2026-11-06-subscription-android-3.md) records the serving
endpoint `https://185.251.89.19:8443/friends/device/subscription`, source overlay tool
`4053da47bb9d484bd87bb60884cf74ded17b6634`, HTTP archive
`0fa13b0a92406c9d58043287e880b6533768d031f31e1de10059b9072eb6473e`.
Service `family-connect-friends-http-candidate.service` runs the retained
`friends-access/subscription-0fa13b0a9240/friends-http.pyz` on loopback18086.
This task compares the saved verified archive locally, not a new live deployment or
fresh health assertion. No production connection, restart, reload or DB write needed.

The overlay preserves33 other archive members from accepted MESH2 base
`e2ed4ca6b41e134516a7fa33210cc71e80bc62c09efc370d56ecd4c6d4e6bfd9`.
The canonical merged handler, `subscription.py` and `paid_beta.py` match the saved
live archive byte-for-byte. Canonical access.py adds the already committed
`revoke_device` helper; its subscription purpose is present in both. Other differences
are **main's existing**, deliberately retained `restricted.py` online-generation support
and `scripts/read_readiness_ack.py` targeted readback. They are not copied over the live
runtime here. Main/bootstrap/renewal source is not rolled back to the old overlay.

`scripts/package_friends_http.py` uses the explicit HTTP manifest (including
`control/friends/subscription.py`), includes the actual handler and access/auth modules,
and ships `subscription-location.conf`. First-install allowlist includes the exact
operation. Existing installations must retain their current ingress and upstream:
template18084 is not permission to replace the live18086 location. The current nginx
config hash recorded by ANDROID-3 is
`6eb5d694dfe5f6b8b604484c790dc6457bdcd866f566e6a90ab51d1ac098602f`.
The [deployment runbook](../../deploy/friends/restricted/README.md) now explicitly
requires retaining this location when replacing code. Never rerun first-install on
an existing deployment. Existing source-drift/deployment gates remain enforced.

**Packaging defect fixed:** `package_paid_boundary.py` stages committed source into a
temporary closed tree before invoking the HTTP builder. It omitted the already-required
gateway-selection template and newly-required subscription template. Both are now
passed to that builder. They remain deployment configuration, not private runtime state
or permission to apply templates automatically. No dependency/DB/schema migration.
The nginx test extractor was updated for the expanded ordinary allowlist and exact
subscription location; otherwise existing ingress regression tests would fail before
exercising any route.

## Checks and evidence boundaries

- PASS:71 targeted Python checks,4 skipped (local nginx executable not supplied),
  11 deselected existing ingress cases;8.32s in the isolated locked subscription venv.
  Files: subscription package, HTTP contract, overlay, Android delivery source guards,
  Friends HTTP runtime (excluding explicitly nginx-only cases).
- New package test executes **the built zipapp via `python -I` in a clean subprocess**,
  not imports from the checkout. Synthetic canonical operator event → real HTTP
  challenge/proof → handler → real decoder → encrypted Store → displayed event
  projection/reopen/dedupe. Outside cohort, active and expired all pass; replay,
  wrong-purpose and another-device selector rejected; existing status returns the exact
  `{device, registered, revoked, active}` contract even when paid state is expired.
  Protected non-challenge tables remain unchanged after reads.
- The initial new test expected projection label `expired`; the existing notification
  enum is correctly `expire`. Only that test expectation was corrected; no product
  semantics changed. Final rerun passes.
- Existing43 HTTP contract tests cover coherent transactional reads/concurrent writes,
  schema failures, auth, no-event semantics, natural expiry, revision conflicts and
  response validation. Rerun here because the handler/auth/manifest were integrated.
- New actual-nginx/package ingress test is in the existing hosted full-test CI, which
  supplies `FC_TEST_NGINX`; local result is NOT_RUN, not a synthetic TLS PASS.
- Committed paid-boundary reproducibility, public docs/index guards and PR CI results
  are recorded in the closing checkpoint. No heavy local build/AVD/full historical run.
- Changed-document links and whitespace PASS. `check_public_docs.py --all` finds one
  pre-existing broken phase22 anchor in `2026-10-24-source-checkpoint.md`, reproduced
  from the unchanged main documents (the actual heading uses `—24.10`). It is not
  caused by this integration; the global documentation check is not labelled PASS.

### Hosted integration checks and reference boundary

Integration-specific follow-up `551ec12e295da053935c9bc4ceb3df5cdebc281e`
was pushed and remote-verified; no force push or skipped CI.

Initial PR CI exposed a missing **explicit source adaptation record** for the two
shared messenger files changed by subscription. Fixed using the existing
`local_adaptations` mechanism, not by replacing original accepted106 hashes:
`android106-messenger.json` and `android106-notifications.json` retain their immutable
accepted sources and separately pin the119 changes plus new projection module.
`subscription119-messenger.patch` is checked by actually reverse-applying it and
verifying both restored files against their original accepted106 hashes. No desktop
subscription UI, delivery transport or runtime acceptance is claimed.38 focused
reference/projection/delivery tests PASS after this metadata/test fix.

The independent Linux internal candidate run
[42270131107](https://github.com/Joker20380/family_connect/actions/runs/42270131107)
fails in `build_desktop_mesh.py` with `shared106 source verification failed`.
The verifier names44 carrier source/test files; **all44 are byte-identical to base
main41b4e6e**, and neither their source nor the reference manifest is changed by this
subscription PR. Updating these accepted desktop/shared-native assertions requires
separate provenance/qualification review; silently accepting current hashes or
skipping this workflow would bypass the gate. That existing main mismatch, plus any
remaining repository checks, prevents an unqualified merge. The old broken global
documentation anchor is also retained as a known base failure, not hidden by narrowing
the reported result. No G4 readback, restart or heavy local rebuild was used to diagnose
either failure. The original failed CI runs remain visible.

The initial phase0/control/failover fixture preparation also attempted to feed an
immutable historical HTTP source into the **current** packager, which requires newer
ingress templates. Corrected `ci_release_fixtures.historical_http` to execute the
builder from the pinned historical source in an isolated subprocess and still enforce
the unchanged historical archive SHA
`460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
Current HTTP fixtures continue to use the current strict builder; missing current
subscription sources/configuration are not silently tolerated. Regression checks
build the actual old archive with neither newer template present.8 targeted checks
PASS/1 local-nginx skip (fixture guards, packaged subscription path, committed bundle).
No historical source, accepted hash, workflow exclusion or runtime dependency changed.

Other initial CI outcomes, retained rather than silently waived:

| Check | Result / concrete gate |
| --- | --- |
| Android Friends readiness wire contract, PR42270131114 | PASS on first integration source |
| Linux voice, PR42270131035 | Initial FAIL: two messenger reference assertions; explicit adaptation fix and38 scoped tests recorded above, hosted rerun required |
| phase0/control fixture preparation | Initial FAIL: missing gateway-selection template in historical source; pinned-builder fix above, hosted rerun required |
| Messenger prototype, PR42270130971 | FAIL:22 existing bridge/carrier tests still call the4-argument Session constructor, while main already requires platform/version;200 tests pass |
| Linux internal candidate, PR42270131107 | FAIL:44 unchanged-main carrier source/reference mismatches; not subscription code |
| All-documents link check | FAIL: unchanged main phase22 anchor; changed documents PASS |

Both failing messenger test files and the required6-argument constructor are verified
against main41b4e6e; subscription adds methods, not these constructor arguments. This
task does not repair unrelated main tests or declare a desktop baseline accepted.
**Merge remains NOT_DONE.** Prepared PR1 must receive a green applicable CI result
after the existing main source-reference/test gates are resolved through the normal
review process. Any latest running checks are not recorded as PASS. No auto-merge,
main update or protection/check bypass has been attempted.

## Android provenance and retained acceptance

Merged Android production inputs (`clients/android`, `messenger`, `carrier`) have
**no diff** against installed source `b2a37fe989294018ab08060bdebfa46d741d11d5`.
No new Android source/resources/dependencies/version change in this integration.
Main's separate bootstrap regression harness is preserved, not packaged into the APK.
The accepted APK is still
`/mnt/data/fc-subscription-android-2-build/release/FamilyConnect-Test-0.1.18-beta119.apk`,
SHA256 `52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d`,
Friends ARM64 beta119/code119, `com.familyconnect.app.friends`, production signature.
Its provenance is **not** relabelled with the integration/merge SHA.

- Physical PASS previously: Redmi Note9 Pro/API31,118→119 retained-data update;
  same public identity/activation/settings, real ARM/Chaquopy and Keystore reopen,
  fresh own **outside-pilot** response over normal trusted ingress without VPN.
- API35 isolated synthetic backend PASS previously: paid snapshots/event types,
  actual UI refresh/save/automatic delivery/notification/tap/dedupe; permissions and
  offline/restart checks as bounded by ANDROID-1/2 reports. This is not physical paid
  event acceptance. Latest APPLIED event is not necessarily a payment or full history.
- NOT_RUN remains: legitimate physical paid event/notification, hard whitelist,
  natural clock expiry on installed Android, real UI identity switch and prior mixed
  network scenario. COLD_BOOTSTRAP_GAP remains separate and unchanged.

New events are discovered on subscription-screen open or Refresh. Durable save starts
the existing delivery path automatically; ordinary app start can drain a previously
saved event. A payment made while the app is closed is discovered only on a subsequent
subscription request, not by push or independent background acquisition.

## One prepared next operation — not executed

The general existing operator operation is **real manual paid activation**, not a
free grant or invented test mode: `control.friends.paid_beta_admin activate` (the
same entry point shipped in `paid-beta.pyz`). Prepare with private operator variables:

```sh
<locked-python> -I <accepted-paid-beta.pyz> \
  --db /opt/apps/family_connect/friends-access/access.db activate \
  --support-id "$TEST_DEVICE_SUPPORT_ID" --event-id "$UNIQUE_PAYMENT_EVENT_ID" \
  --reference "$PRIVATE_PAYMENT_RECONCILIATION_REF" \
  --period-start "$AGREED_START_UTC" --paid-until "$AGREED_END_UTC" \
  --apk-sha256 144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf
```

This is a **conditional template, not a command ready to run on beta119**. Missing:
legitimate payment/reconciliation and agreed UTC-Z period, separately authorized
recipient/action, a currently verified operator artifact and **compatible paid
baseline authority**. Canonical policy still requires authenticated Android
`0.1.18-beta108`/code108 and exact private handoff hash above. Current119 cannot be
honestly attested as108: it would fail `ANDROID_BASELINE_REQUIRED` (or the APK hash
guard if119's hash is passed). Do not downgrade, forge support observations or pass
the108 attestation for the119 APK. A separate explicit paid-baseline qualification/
policy decision is required before this operation can serve the current physical119
scenario; this integration does not change baseline108 or the cohort limit10.

When legitimately authorized/eligible, `start <= server now < end` creates canonical
`payment`/`APPLIED`, first revision1 and `last_event_id`, enrollment within limit10.
The first event maps to `activated`: “Сервис подтвердил активацию доступа.” /
“Access activation confirmed by the service.” Existing periods cannot be shortened;
a longer period with a retained prior snapshot maps to `renewed` (otherwise `confirmed`),
not “money received”. Only the latest corresponding
event is fetched; snapshot alone creates no payment notice.

Enrollment changes this device from legacy non-cohort admission to paid entitlement
gating. Active paid state does not grant rights beyond existing identity/admission;
MESH issuance is bounded by the period. At `paid_until` (or existing grace boundary)
effective state denies paid access without requiring a new event; identity remains
registered and can read its own status. Natural expiry may show expired state without
an expiry-event notification. `expire` is the existing explicit early stop operation;
`grace`/another valid paid activation can extend eligible non-revoked state. `revoke`
is terminal. There is **no supported remove-from-cohort/reset/ledger-delete undo**;
ending a check by expiry is not a return to the prior unrestricted non-cohort state.
Never restore a DB backup or delete payment rows as a test teardown.

The repository also has a real `paid_beta_canary` **bound internal_canary** mechanism
(zero-revenue access, not customer payment). It is not generic free enrollment: one
HMAC-bound OWNER_CANARY_1, short permit window, staged version/certificate checks,
no other cohort member and event cap4. The previous report records its separate
completed ledger1/4; no reusable permit for this119 identity is established. Rebinding,
resetting that ledger or disguising a free grant as a real payment is not a supported
next action here. No financial, subscription, cohort, admission or identity row was
changed while preparing this scenario.

## Rollback and scope

### Authorized PR1 base CI repairs

Starting refs rechecked: PR head `f119d3061edd193106b53be832cea7d9982c363f`,
main `41b4e6e034efc3e51446f383f2fbaedee3ad5a67`. Work stays in the existing
isolated integration worktree; no foreign work is reset or overwritten.

- Nine obsolete Session fixtures now pass `platform="android", version=119`,
  including reopen. Production constructor/validation/PackageManager are unchanged.
  Removing TypeError exposed three outdated relay-empty expectations: durable Android
  reception queues a **storage receipt**, not a subscription/payment notification.
  Tests now verify reply purge, automatic receipt relay, peer receipt consumption,
  `recipient_stored`, then an empty relay. No assertion removed or production default added.
- PASS:22 targeted bridge/carrier tests (16.73s), then222 messenger tests (119.33s).
- Only the phase22 fragment in the24 October report is corrected (`2410`, not `24-10`).
  Target heading unchanged. Single-document and `check_public_docs.py --all` completed
  with no errors; this is an actual global run, not an inferred result.
- Actual accepted builder `sources()` on archived commit
  `efc13f1c7f2750cb7640dd2b8b90aed15c92c6e3` reproduces all313 native entries and digest
  `f0e48d7cd3bd68a02759a5ff29967492ab170e171942d502864f0e03a07c23fe`.
  Its desktop verifier passes all175 shared sources. Full staging closure has337 files,
  digest `2d4e1380efa25109e1f0ea2e17f8971d1e8a8f127c56b313742ee8819696e933`:
  complete carrier/mesh trees plus the pinned builder, verifier and their reference inputs.
  A fresh `git archive` stage excludes later additions, not just44 known differences.
- The **current** CI checkout still supplies frontend, messenger, support files, RNS,
  normal transports and packaging. Native build and system packager independently
  verify the **same** pinned stage; modified/missing/extra inputs, builder tampering,
  symlinks and stage reuse fail closed. Historical builder,106 hashes and
  `system-reference.native_source_digest` are unchanged.13 bounded tests PASS;
  the real staging CLI also reproduced the pin. No local native build or Docker action.
- CI keeps race tests, native binary/metadata checks and real package smokes intact.
  Artifact receipts now separate `package-source.txt`, `native-source.json`, full
  `native-inventory.json`, `native-build.json` and `system-delivery.json`. The latter
  records native source commit and built binary digest. A mixed-provenance package
  is not attributed wholesale to the old native commit. Binary digest awaits hosted build.

### Hosted receipts for the repaired source

Source head `24de0b2c3e4042f903395dacc72d367ff0df0f98`, base still
`41b4e6e034efc3e51446f383f2fbaedee3ad5a67`, remote read back after push.
GitHub PR test merge `7166d2fc67dbedc942392f1d1f6153e2ac6d63fd` has precisely
these two parents and the **same tree** `a73440a6985646fb844c059c9a1fa27907fd1be9`
as source head. This is a synthetic PR test ref, **not** a completed merge to main.

| Gate | Result on repaired source | Receipt |
| --- | --- | --- |
| Linux internal candidate | PASS, complete race/build, metadata and package smoke | [42279283893](https://github.com/Joker20380/family_connect/actions/runs/42279283893) |
| Messenger prototype | PASS | [42279283973](https://github.com/Joker20380/family_connect/actions/runs/42279283973) |
| Android Friends readiness wire | PASS | [42279284000](https://github.com/Joker20380/family_connect/actions/runs/42279284000) |
| Windows control conformance | PASS | [42279283993](https://github.com/Joker20380/family_connect/actions/runs/42279283993) |
| Client builds | FAIL: Android source-review guard; Linux, Windows and compatibility jobs PASS | [42279283953](https://github.com/Joker20380/family_connect/actions/runs/42279283953) |
| phase0 | Still running at this receipt; not PASS | [42279284001](https://github.com/Joker20380/family_connect/actions/runs/42279284001) |
| Linux control preview | Still running at this receipt; not PASS | [42279283941](https://github.com/Joker20380/family_connect/actions/runs/42279283941) |
| Linux voice/encrypted messaging | Infrastructure timeout downloading Ubuntu packages, one targeted job retry requested | [42279284021](https://github.com/Joker20380/family_connect/actions/runs/42279284021) |

Linux artifact13535302062 was downloaded and its receipts inspected. `package-source.txt`
records PR test ref7166, while `native-source.json` records the pinned efc13 closure.
The artifact's full313-entry inventory recomputes exactly to `f0e48d7c…` above.
Go1.26.1 linux/amd64 binary `fc-mesh` is29,031,243 bytes, SHA256
`b038b78f1260bf37d3c48df722a3571553a0207a3be40acb2dd4bcfd44463feb`.
`system-delivery.json` independently records this binary hash and native source commit;
system archive SHA256 `c0427307858f4b3807fcd7b49651b289111f6362567fb10121a016b8ada2d3ba`.
Actual system, DEB and AppImage smoke logs are PASS; AWG/TCP prestart and integrity
checks also completed. These are isolated CI artifacts, not installation/publication.

Local additional bounded packaging selection: first attempt had9 environment failures
(inherited shell umask002 caused writable fixtures; isolated venv lacked GI). Retained
that failure, then ran the same selection with child-only umask022 and the installed
system GI import path:82 PASS,2 existing conditional skips,1.28s. No dependency install,
shared-cache modification or assertion weakening. Hosted configured environment passes.

**Concrete remaining code gate:** Client builds/android job128103761031,
`Restricted diagnostic and readiness contracts`, fails
`tests/test_android_public_release.py::test_accepted_android_ui_and_mesh_are_not_replaced_with_old_main`.
`ChatActivity.java` expected old reviewed hash
`34aec6a30af77ece7753ee65ac592fd97a2fb3af8d19721de3edfb14e623e488`,
actual `4a1e7a28cc374aef5d72664237a2c4dff8cd8d078aff760a1e996646bfb75a0d`.
The actual value also matches the installed119 **source**, not a newly changed Android
file. Local exact diagnostic selection reproduces1 FAIL/63 PASS/1 deselected. Required
next action is an explicit source-provenance review of the subscription UI delta and
its guard, retaining historical hashes, followed by this actual gate. Merely replacing
hashes or asserting the old APK qualifies a new source is not a fix applied here.

Earlier f119 phase0 failover additionally completed with110 failures/214 errors:
root-only profile/maintenance fixtures ran as UID1000 and accepted historical Git
objects (`edca544…`, historical HTTP) were absent from the restored shallow source.
Its direct desktop verifier also still targets evolving current carrier, outside the
now-fixed Linux package's pinned stage. These are reproducible fixture/selection
failures, not attributed to a transient network or claimed fixed. A proper subsequent
CI fixture repair must supply accepted inputs and execute root/unprivileged groups in
their required isolated contexts without skip/xfail or weakening source checks.

This receipt update is documentation-only. Any new commit from it retains24de0b2's
production/build/test inputs; its own automatically requested checks must still be
observed before any merge. Latest run observations belong to [PR1](https://github.com/Joker20380/family_connect/pull/1),
not a claim that the still-running rows here later passed. No deterministic failed job
was manually rerun without a fix; only the identified voice mirror timeout was retried.

Android production inputs (`clients/android`, `carrier`, messenger excluding tests)
remain byte-identical to beta119 source `b2a37fe989294018ab08060bdebfa46d741d11d5`.
Its APK provenance and all prior physical/synthetic/NOT_RUN boundaries are unchanged.
No merge is allowed while an applicable gate remains red or running.

### Scope and rollback

Before merge, close/revise the integration PR; after merge use an ordinary reviewed
revert, never reset published main. This does not uninstall the existing APK or roll
back the already accepted live overlay. Any later server rollout requires its own
current runtime/source-drift check and code-only rollback to the retained archive/
drop-ins/ingress; no DB/payment/identity rollback. G4/frozen worktree/services,
renewal/MESH/bootstrap operations, production, signing keys and public artifacts were
not changed by this task.
