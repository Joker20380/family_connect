# requested tester seamless upgrade —2026-10-26

Later explicit P1 scope completed: gateway limit expanded to4, canonical target
added while preserving original3; single approved restart and readback/TLS PASS.
[Separate deployment receipt](2026-10-26-p1-four-members.md). This supersedes
pending P1 notes below, not the original full in-place-upgrade evidence blockers.

## Follow-up: requested MESH access and existing106

### Explicit P1 request and counting clarification

Owner requests target as third additional tester, four identities including owner.
Fresh NL executable SHA256 remainsa515539af72844cb5af4f918a229c85e23cff874f0f6ac369649df3839273c85.
Source parser admits at most3 TOTAL hashes/99 bytes; current group has3 hashes,
98 bytes, SHA2561cb942471c3d1349a4551b7acb922adc75e788549201a0cbabb764b72b858103.
P1 enabled, pacingOFF. Initial read incorrectly resolved relative diag67 against
SSH cwd; corrected /proc/PID/cwd-relative read confirms policy exists unchanged.
No missing-policy incident. Adding fourth without changing parser would fail
closed, not enable the target. No policy/binary change yet; shared gateway update
and coordinated restart needed before extending group while preserving members.

Fresh authoritative lookup confirms unique target, device/invite revoked0,
no revoked grant, running v2 all_activated admission. MESH eligibility already
exists; server operation is a no-op, writes0. No P1 cohort expansion implied.
Existing shared private106 APK verified locally with apksigner and aapt2:
com.familyconnect.app.friends /0.1.18-beta106-recovery/code106,56093664 bytes;
SHA256242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020;
signer67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
File:state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk.
No new build/publication/remote install or message to tester. This verifies the
available106 artifact, not the target's installed signer or completed84→106 upgrade;
previous full seamless-upgrade BLOCKED result remains distinct.

RESULT: BLOCKED. Production stopped at user-defined evidence gates; no changes
to client, server records, signing, release catalogs or public artifacts.

## Authoritative read-only findings

RU Friends access.db opened mode=ro. Exactly one support join and one matching
canonical device/public identity row. Canonical identifier retained privately.
Platform android; last support_request observation2026-10-17T12:42:49Z:
0.1.18-research84-ui60-4-batch1, versionCode84. This is last reported version,
not fresh proof of installed bytes on26 October.

The public Device Identity key fingerprint is retained only in private evidence.
Device revoked0; exactly one invite association revoked0. Existing activation
valid by Friends registry semantics. One chat binding. No restricted grant row,
no readiness ACK, no target handoff row, no diagnostic snapshot in standard DB.
No duplicate identity found in queried registry; local stale state not inspected.

Running RU HTTP process restricted root admission.json:version2,
eligibility all_activated. Absence of an explicit per-device grant is therefore
not by itself an entitlement defect or reason to create one. No account/person
association inferred from device records. No personal data or credentials exported.

## Missing evidence / stop rule

Authoritative device_support schema stores device/support_id/platform/app_version/
version_code/last_seen/observation_source only. Installed package ID, APK signing
certificate, updater channel, UID, local store/schema and provisioning generation
are not recorded there. No target diagnostic snapshot supplied those facts.
Last successful VPN connection, assignment, protocol schema and update error cause
remain unknown. Historical owner code84 reports identify com.familyconnect.app.friends
and a signed artifact, but do not attest this target installation. A matching
version string cannot substitute for installed signature evidence.

User requires immediate production stop for unknown installed signing certificate
or inability to prove identity preservation. Both gates remain unsatisfied.
Root cause of any upgrade incompatibility is NOT ESTABLISHED; no speculative
migration or entitlement correction justified. No claim that in-place upgrade is
impossible, only that requested safety/acceptance cannot currently be established.

## Execution and remaining work

No production writes; backup/rollback/audit mutation receipt not applicable.
No package built, signed, installed or published. No upgrade fixture or tests run;
passed/failed/skipped counts not applicable. Existing unrelated work preserved.
Target version deliberately not selected before identifying installed update path.
Resume requires trusted target-linked package/signer/channel and old-state evidence
sufficient for genuine in-place preservation testing, without exporting production
secrets or asking for uninstall/reset/re-enrollment. No end-user procedure beyond
the requested two actions has been issued. Published artifacts unmodified/unverified.
