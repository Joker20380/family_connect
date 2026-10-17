# FIELD-1-VOLGOGRAD-BATCH1 — private update preparation

**RESULT=TESTER_NOT_AUTHORIZED; COMPATIBILITY_NOT_CONFIRMED; FIELD_NOT_STARTED.**
The owner selected one recipient, alias **T1**, reported readiness in Volgograd,
and requested the current build, preferably as an update. Performance engineering
is deferred in favor of this preparation; this does not accept batch1's speed or
erase the [intermittent page failures/low-rate report](2026-10-17-batch-owner-speedtest-sites-1.md).
Reported local whitelist restrictions are not independently observed. Input review:
`c9ddb53385d4d7caf898c1a32bb366f84e645834`. Date:17 October2026 UTC.

## Existing artifact, no rebuild or signing

Rechecked the already signed owner batch1 APK using the retained artifact inspection
workflow: SHA256, package/version, signature, alignment, DEX/native payload identities
all match its original signing receipt. A byte-identical copy and checksum/instructions
are staged in a private local tester kit, **not sent, uploaded or installed**.

| Identity | Value |
|---|---|
| Version / code | `0.1.18-research84-ui60-4-batch1` /84 |
| Package | `com.familyconnect.app.friends` |
| Signed APK SHA256 | `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f` |
| Native SHA256 | `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23` |
| Client inventory | `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| APK bytes / alignment |56,028,128 /16KiB PASS |
| Requirements | Android12/API31 or newer; ARM64; non-debuggable |

The last verified deployed gateway is4b722d2d…fab7 from the linked rollout/analysis,
not the older UI60 baseline gateway. Loaded gateway/security/runtime readiness was
not polled in this preparation and is not asserted current. The APK is not bound to
the owner's UID on its ordinary path; research provisioning blocking is not armed by
normal installation. No profile, key or cache is included in the tester kit.

## Exact recipient lookup and actual blocker

One read-only RU lookup at10:03:16–10:03:18 uses the currently configured API archive's
existing `support_ids.lookup`, with SQLite `mode=ro` and `query_only=ON`; no Access
constructor/schema migration, inventory enumeration, grant changes or credentials read.
The supplied recipient identifier stays private; no other person is selected.

- Registration active, not revoked; platform Android.
- Last reported app beta60/code60, support observation16Oct20:15:09UTC. This is not a
  fresh on-device installed APK/signer inspection and may lag subsequent changes.
- `family_state=NOT_PROVISIONED`, `field_admission=false`, readiness UNKNOWN.
- Model/API/ABI/current package/signer and mobile operator are not established by
  that lookup. Do not substitute the owner's API31/UID/device observations.

Registration does not confer restricted access. A simple APK update cannot grant it.
No new entitlement is created under the prior no-new-grants scope. Continuing access
provisioning needs explicit owner authorization and the accepted operator procedure;
no manual SQL/profile change, copied owner credentials or new identity workaround.

## Update route, not a public rollout

The retained updater uses one shared signed catalog, not recipient-targeted delivery;
its manifest parser accepts beta-style version names, not this research version.
Do not change the common catalog, rename/rebuild the APK or promise that T1 can obtain
this private build through the app's ordinary “Check for updates” button.

After compatibility/access checks, the simple supported route is owner-private APK
transfer, then Android's **Update** over the existing app with VPN OFF. Preserve app
data/registration. Package and signer must match and code must not decrease. If an
unexpected separate-install/signature/downgrade error appears, stop; no uninstall,
clear data or bypass. Code60→84 does not offer ordinary rollback to code60.

## Next boundary and bounded field scope

Collect model/Android and operator plus any changed installed version in one short
owner response; no further site-name request. Confirm ARM64 and package/signer from
available device/app evidence before handing over the kit. Separately authorize any
new restricted grant before using the existing workflow. Until then, no field CONNECT.

After those gates: warm preparation on working network using the tester's own delivery
and ACK; fresh gateway/material/scheduling readiness immediately before the episode.
No server maintenance/restart or capture activation is authorized by this preparation.
One mobile restricted CONNECT, Wi-Fi OFF, no other VPN; first establish base-network
observations. VPN-bound HTTPS/IP, repeat after240s READY, normal OFF and one support
export; CONNECT→final OFF at most18min. First failure stops the episode. No reconnect,
open-ended soak or repeated speed tests. A working unrestricted base network means
MOBILE_SMOKE rather than proof of whitelist bypass; no base data means no transport test.

**Action counts:** existing APK verification1, local private kit copy1, read-only SSH1;
build/sign/install/transfer/upload/catalog change/grant change/ADB/CONNECT/export/
gateway restart/maintenance0. Phone state not freshly observed; owner export13's
CONNECTED is historical, T1 VPN state UNKNOWN. Performance, full field acceptance,
historical causality, handoff, supervisor and public release remain unpromoted.
