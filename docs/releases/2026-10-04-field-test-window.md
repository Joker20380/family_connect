# FIELD diagnostic lifetime window — 2026-10-04

## Authorization and bounded policy

After export(8) demonstrated readiness expiry before the mobile attempt, the user
explicitly authorized a practical testing window rather than repeatedly encountering
the existing short limits. This supersedes the preceding request for confirmation.
No indefinite credentials, admission expansion or disabled validation is authorized.

- Standard CRL default remains900s. Explicit RU sync CLI option `--crl-lifetime 3600`
  selects the existing client's maximum one-hour CRL policy for this testing contour.
- Publisher validates integer lifetime900–3600 before mutation, and caps at issuer
  delegation expiry. CLI accepts only900/3600. Signature, revocation, monotonic sequence,
  expiry and native one-hour delivery/directory checks remain unchanged.
- This permits older signed revocation information, a consciously accepted testing
  tradeoff. Publishing a current revocation still works; revoked devices remain rejected.
- Gateway leaf renewed for14400s, bounded by existing issuer expiry. Client readiness
  remains the minimum of CRL, device certificate, directory, grant and issuer validity.
  It is not guaranteed to last60 minutes from every fetch, nor valid indefinitely.

## Source, tests and exact artifact

Working source base `64849e828add45407625d31df61413ac98e9a2cc` plus uncommitted scoped
patch to `control/friends/restricted_admin.py` and `control/friends/restricted_sync.py`.
Tests updated in friends_restricted, native_authority_compat, restricted_runtime and
sync_acceptance. No new commit, GitHub CI run or Android version is claimed.

An initial current-checkout build1917802f was **not deployed**: comparison found an
unrelated access-module/Support-ID manifest change against the live sync. The actual
targeted package preserves deployed access.py and the existing absence of support_ids.py;
only the two lifetime modules differ. Every archive member was compared with the
accepted installed baseline, not merely the new two files. Minimal sync runtime
dependencies match their pins from existing lockfiles; no HTTP/test dependencies
were installed into that server venv. Initial overbroad dependency preflight and the
unrelated-source comparison both stopped before server mutation.

| Item | SHA256 |
|---|---|
| Existing sync baseline, preserved | `f6aa8859ab716383bf207b2ff7b302687692832b2ccb410f1aef0ada0793a9c9` |
| Tested/deployed targeted sync | `1bfa085b03edf6b1cfbfab05ac6b4ca1e8626932669d49d7ef3325bf0f0fc0d0` |
| RU lifetime drop-in | `7242a8c29a6d2f57c507a5973cfe4c3cd29881134336e29310fd8ae2e8dc67cd` |
| Unchanged gateway executable | `b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217` |

Local locked Python/Go source suite: **138 passed**, including native compatibility,
30-minute delivery acceptance, actual expiry rejection, four-hour gateway certificate,
revocation and issuer cap. Exact targeted artifact, isolated CLI/source inventory and
positive/negative sync acceptance: **66 passed**. Earlier non-targeted artifact tests
were not substituted for this exact-archive check. No skipped native coverage in the
138-test run. `git diff --check` and focused documentation links are also checked.

Private evidence, immutable build snapshot and complete member/source hashes are under
`state-client-build/field61-test-window/`; targeted bundle is `runtime-targeted/`.
Original whole-checkout candidate remains retained but is not live. No secrets enter
source, build archive, logs or Git; profile/issuer operations remain protected.

## Live operation and verification

1. Protected gateway-only renewal09:39:54UTC: same gateway/issuer/Family identities,
   same two admitted devices and grant revisions. Python/native positive and negative
   validation PASS; owner-only0600 profile retains UID/GID979 and service readability.
2. Only restricted gateway reloaded; loaded certificate matches validated profile,
   issuer/hostname verification and35s stable readback PASS. Gateway expiry
   **13:39:54UTC04.10**, issuer still **14:13:53UTC04.10**. PID3789112/restarts0.
3. RU preflight verified old archive, exact two-module delta, required dependency pins,
   current unit and absent new paths. Candidate copied as a separate immutable archive;
   isolated pre-network `--check` passed before activation.
4.09:43:33UTC: stopped only existing sync timer, waited for the current job, added
   `/etc/systemd/system/family-connect-restricted-sync.service.d/61-diagnostic-window.conf`,
   daemon-reload, one synchronous sync succeeded, timer restored. ExecStart selects
   `/opt/apps/family_connect/friends-access/restricted-sync-field61-window.pyz`
   with `--crl-lifetime 3600`. No NL sync-runtime or HTTP deployment.
5. Independent09:44 readback: correct archive hash/command, RU and NL CRL3643 both
   signed and lifetime3600s, expiry10:44:36UTC. Background sync retains the new policy,
   rather than overwriting a one-off long CRL with the old15-minute default.
6. RU/NL directory hash matches
   `38d2ec4fc345b39551cba21b2d1c9dc4c65cc6948545530c1e1c7145cffe3fb1`,
   issued09:40:00.254846896UTC, expires**10:34:57.984222868UTC**. Active sync timer,
   last service exit0/success. No test connection performed by the operator.

Before/after devices/invites/grants/support-audit/mapping/admission fingerprints and
ordinary HTTP/AWG/TCP executable/process fingerprints match. Public HTTPS09:44:50UTC
returns200/TLS verified, with unchanged beta60 signed catalogf042beca, discovery6e5817dc
and invitation014ebdbd hashes. No APK rebuild/resign, FIELD admission, Support ID,
enrollment, Linux/Windows download or production distribution change.
Accepted beta61 r2 APK remains4297ea1a/signer67a90d1; no new Android artifact.

Final readback10:00:11–12UTC: RU/NL signed CRL3671 both retain3600s lifetime,
expires10:59:56UTC; directory still expires10:34:57UTC. Same runtime, loaded gateway
certificate/PID/restarts0 and active sync timer; ordinary default discovery/invite
hashes unchanged. Tester still has no fresh post-policy READY/ACK. Final source suite
rerun138/138 PASS; exact artifact66/66 PASS; focused docs5 files/391 links and diff
whitespace check PASS. The two patched baseline module bytes also independently match
HEAD before this scoped lifetime patch; no unrelated changes are hidden inside them.

## Remaining acceptance

At09:44 the tester still has the old expired08:58 READY/ACK. Server deployment does
not rewrite phone storage. Tester must open the main app screen on working Wi-Fi for
ordinary refresh (normal backoff retained); verify fresh READY/ACK and actual cached
expiry before a separately coordinated mobile attempt. No new invitation/uninstall/
data clear. Existing short cached certificates can also bound early refreshes until
normal issuance selects a new one; never falsify ACK or manually edit the device cache.
No claim that intermittent native-validation failure or original restricted disconnect
was fixed. A longer lease is operational preparation, not transport-defect repair.

## Rollback and protected receipts

RU operation stage:
`/opt/apps/family_connect/restricted-materials-stage-20261001/field61-test-window-20261004`.
Gateway protected renewal stage on authorized hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/field61-window-gateway-20261004`.

To revert only the lifetime policy: serialize the RU sync timer/job, remove only the
recorded `61-diagnostic-window.conf` after checking its hash, daemon-reload, verify
ExecStart returns to the unchanged baseline archive without the new flag, then run
the existing sync and restore the prior timer state. Retain receipts/new archive for
audit. Default next publication returns to900s; never decrement CRL sequences or
restore an old CRL/database snapshot. Already issued long-lived signed information
does not become retroactively expired merely by removing the flag.

Gateway certificate rollback is separate: do not reinstall the expired pre-renewal
certificate or lower security floors. Preserve current valid credentials and use the
protected renewal procedure if another valid leaf is required. Ordinary production
services/catalogs and enrollment require no rollback because they were unchanged.
