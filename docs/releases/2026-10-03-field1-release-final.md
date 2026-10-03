# FIELD-1-RELEASE-FINAL / DIAG-1A — 2026-10-03

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
