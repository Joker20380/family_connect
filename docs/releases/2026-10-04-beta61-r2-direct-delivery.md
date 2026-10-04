# Beta61 r2 direct diagnostic delivery — 2026-10-04

## Result: BETA61 R2 DIRECT DELIVERY PASS

Published03:32:45UTC; independent public download/readback completed03:34:46UTC.
Targeted diagnostic FIELD download for existing FC-YHQB-9VJN, not the primary
Android release, automatic update, mandatory update or expanded admission.
The URL is publicly downloadable; the intended tester designation is not access control.

**Public URL:**
[Android beta61 r2 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta61-r2.apk)

| Item | Verified value |
|---|---|
| Existing accepted artifact | `state-client-build/field61-r2-delivery/FamilyConnect-Test-0.1.18-beta61-r2.apk` |
| VersionName / versionCode | `0.1.18-beta61` / `61` |
| Source commit | `64849e828add45407625d31df61413ac98e9a2cc` |
| Local, server and downloaded APK SHA256 | `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb` |
| Signer SHA256, local and downloaded | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Retained beta60 signer comparison | Exact match, independently verified |
| Downloaded size | `49654651` bytes |
| Public HTTP / TLS | `200`, TLS certificate/hostname verification enabled |
| Content type | `application/octet-stream` |
| Content disposition | `attachment; filename="FamilyConnect-Test-0.1.18-beta61-r2.apk"` |
| Build / signing / GitHub operation | None / none / none |

## Narrow publication

Uploaded only the existing signed APK. Final server path:
`/opt/apps/family_connect/state-product-https/config/downloads/FamilyConnect-Test-0.1.18-beta61-r2.apk`.
No existing artifact replaced. Guarded hashes before promotion; no-overwrite link
publication, permissions inherited from the beta60 public APK. Added only an exact
download location in `nginx.conf` and `nginx-final.conf`, copied from the existing
beta60 route with only the diagnostic filename changed. Removing that new block
reproduces the exact previous config bytes. `nginx -t` PASS; reloaded only nginx in
`family-connect-product-https`, without restarting the ordinary app/AWG/TCP services.
No extra checksum/test/unsigned artifact uploaded to the public downloads directory.

Landing was deliberately not edited: no diagnostic link added to the main page,
no primary-download switch, no mandatory update. The direct URL is provided to the
operator for the single existing tester.

## Production preservation — independently checked

Public beta60 APK was downloaded again after publication:
SHA256 `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104` unchanged.
Both `/invite/` and `/i/` remain byte-identical and still link to beta60; page SHA256
`014ebdbd78966185b1d99823ae5e7e0251369dde26059bc82957e454ea99a49f`.

- `/updates/android-friends.json` discovery remains beta60/code60;
  SHA256 `6e5817dc109b579384985b7f966bcf56c22ec59b4759eb477ef031cdc59a6a3b` unchanged.
- `/updates/android-friends-v2.json` signed catalog signature verified; remains
  beta60/code60, `mandatory_after=0`;
  SHA256 `f042becae969474ed7ebc28890a635ae5812769a3203fa6d75cf18fd22060006` unchanged.
- All pre-existing downloads, including Linux and Windows, have identical hashes
  and sizes before/after. No Linux/Windows link, catalog or release changes.
- Static HTML/JSON, FIELD admission, Support ID mapping, device/invitation/grant
  rows and ordinary HTTP/AWG/TCP service process identities match before/after.
  Sensitive database contents were never exported; checks retain hashes only.

Private operation/readback receipts and downloaded APK:
`state-client-build/field61-r2-direct-delivery/` (`local.json`, `server-before.json`,
`public-before.json`, `publication.json`, `server-after.json`, `verification.json`).
Documentation validation: `git diff --check` PASS; `check_public_docs.py --all`
PASS (458 documents,2765 links,0 local link/anchor errors). External HTTP checks are
the separate actual public readbacks above, not inferred from the Markdown check.

## Tester instructions and remaining boundary

Install **over beta60** using **Update**. **Do not uninstall, clear app data or
activate a new invitation.** Keep Support ID FC-YHQB-9VJN and enrollment unchanged.
If installation is rejected, stop and retain the exact error; uninstall is not the fix.
No tester installation, remote app action or Russian mobile reproduction occurred
in this delivery task. The original restricted-session disconnect is **not claimed
fixed**. Owner real-correlation acceptance remains in the
[03.10 report](2026-10-03-beta61-targeted-acceptance.md).

Before a later coordinated single mobile Auto attempt, verify/renew current gateway,
issuer, CRL, directory leases and obtain fresh tester READY/ACK. Historical owner
acceptance is not evidence that today's leases are valid. Export diagnostics
immediately after failure/disconnect, before another connection, and correlate all
four identifiers against bounded server evidence. Do not expand FIELD admission.

## Rollback

Protected pre-change nginx backups and publication receipt are under
`/opt/apps/family_connect/release-beta61-r2-diagnostic-20261004/`.
Post-publication nginx hashes:
`nginx.conf`: `0ebfe188809d6892d87edfc009b8afc300ee8b701b23c8151eb0f4936246ca15`;
`nginx-final.conf`: `fc16ffd4a052321004c6a7cf0b19c4aa2e9ff0b44880597dc721a5c27740702c`.
If withdrawal is authorized, remove only the diagnostic exact-match route; use whole
backup restoration only while these current hashes still match. Validate nginx and
reload the same container. Retain immutable APK/evidence; never overwrite its bytes,
roll back production catalogs, or clear device data. Immutable HTTP caches may retain
already downloaded bytes; withdrawing the server route cannot revoke those copies.
