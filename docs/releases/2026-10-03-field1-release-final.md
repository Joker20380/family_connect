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

## Evidence to complete

Clean source/build inventory, final hash, test totals, production backfill counts,
owner in-place preservation/copy/Auto/DIAG acceptance and downloaded-public hash
must be recorded here. They are not inferred from a successful build or local tests.
Until owner acceptance: FIELD-1-RELEASE PARTIAL; DIAG-1A PARTIAL; publication BLOCKED.
