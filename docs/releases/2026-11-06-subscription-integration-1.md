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

Before merge, close/revise the integration PR; after merge use an ordinary reviewed
revert, never reset published main. This does not uninstall the existing APK or roll
back the already accepted live overlay. Any later server rollout requires its own
current runtime/source-drift check and code-only rollback to the retained archive/
drop-ins/ingress; no DB/payment/identity rollback. G4/frozen worktree/services,
renewal/MESH/bootstrap operations, production, signing keys and public artifacts were
not changed by this task.
