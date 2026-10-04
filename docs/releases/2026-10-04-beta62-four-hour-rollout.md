# Beta62 — coordinated four-hour FIELD window, 2026-10-04

## Status and scope

**Follow-up:** [export(11)](2026-10-04-field-export11-beta62.md) now contains the mobile
reproduction, matched server traces and a confirmed recovery-policy defect. The
readiness/next-attempt statements below describe the earlier rollout checkpoint;
do not repeat the mobile test now. No further runtime or APK change in that analysis.

Server long-window activation and owner native import/real session PASS. Tester
FC-YHQB-9VJN is confirmed on0.1.18-beta62/code62 with unchanged Support ID and admission.
**Long tester ACK confirmed; one coordinated mobile attempt is now the next step.**
No Russian reproduction or original transport-fix claim in this rollout.

Resumed readback14:55:19UTC after the user's connection interruption: same loaded
gateway/PID3908811, restarts0, matching RU/NL CRL4207 with14400s lifetime, unchanged
directory and successful public HTTP/catalog probes. Tester long fetch13:39:03UTC /
ACK13:39:04UTC is READY/PRESENT_VALID, orchestrator_usable=true, beta62/code62,
revision1/CRL4069, device/delivery expires17:31:33UTC. At import, conservative gateway
headroom was3h51m15s. At14:55 readback it is **2h34m59s**, not four new hours. Do not
restart/reissue a healthy session or rewrite client cache just to reset the display.
The actual earliest bound remains17:30:19UTC/20:30:19 Moscow.

No product APK rebuild, resign or replacement. Installed/published beta62 remains
source `42a5e59b4bc2c43e56e018ce7287cd7b6e901db2`, APK SHA256
`f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`, signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Default/invitation/updater remain beta60. No FIELD expansion, new enrollment/Support
ID, Linux/Windows change, transport/retry/timer tuning or validation bypass.

## Tester upgrade and initial import

Authenticated server receipt13:10:53UTC confirms tester beta62. Initial import reports
NATIVE_VALIDATION_FAILED, preceded by EXPIRED_ON_IMPORT for its old cached response.
The failed receipt's observed_at is13:10:52, while delivery issuance and the newly
issued leaf's not_before are13:10:53. Strict future/not-before native checks make
clock-boundary sensitivity a candidate; the generic reason does not prove which
branch rejected it. A similar one-second ordering appears in the earlier10:00 failure.
RU reports NTP synchronized. No clock or validation tolerance was changed by guesswork.

Normal subsequent fetch13:16:14UTC / ACK13:16:15 reports READY/PRESENT_VALID and
orchestrator_usable=true. Same tester identity/revision1, no reinstall/clear/re-enroll
or operator cache edit. That short response expired13:23:10UTC and is **not** the
acceptance receipt for the newly activated long materials.

## Exact compatible runtime

All changes are over actual deployed archives, not an assumed checkout:

| Component | Accepted new SHA256 | Scope |
| --- | --- | --- |
| RU HTTP | `098889496b9327a18c6ef08bba57ff73e81a9eae170a5d2d5030301cbaa544e1` | Only `control/friends/restricted.py` differs from live ef9f2faf |
| RU/NL sync | `9ed01927ae49cf402e126807fa3d219d8b492383afb47b485f5c14149abb2e20` | Only restricted, restricted_admin, restricted_sync differ from live1bfa085b |
| NL gateway | `6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09` | Already accepted beta62 binary, not rebuilt/replaced |

Changed Python entries come from42a5e59, whose platform CI was already accepted.
Exact overlaid archive regressions: **197 passed**, including actual Go/native
compatibility; no skipped tests in final run. Earlier private harness runs failed
because scripts/HTTP modules were absent from its import paths; corrected harness
uses actual HTTP archive modules and locked FC_TEST_GO. No product test removal or
runtime workaround. Initial read-only operator regex failure was local-only and
corrected before mutation. Private offline native checker was built from matching
unchanged Go source; positive/family/revision/CRL-negative acceptance PASS on real
renewed material before gateway publication.

Live paths are `friends-access/http-beta62-window.pyz` and
`friends-access/sync-beta62-window.pyz`. Previous archives are preserved. Existing
HTTP unit/loopback18086 is reused via62-four-hour.conf; one bounded restart, same
ordinary routes and DB. No nginx/upstream/port change. HTTP policy explicitly uses
`FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME=14400`. RU sync61-diagnostic-window.conf now
points to compatible sync with `--crl-lifetime 14400`; timer restored/active. NL forced
command retains its SSH key/admission and wrapper guards, changes only archive path.

## Actual material chain and loaded state

- Offline-root signed issuer delegation advances3→4 with the **same issuer key,
  family/gateway and minimum revision1**, expires05.10.2026 13:28:47UTC.
- Existing owner/tester grant expiries extend to that issuer expiry; revisions3/1,
  revocation state, exact two-device admission, identities and Support IDs unchanged.
- Initial long CRL4055; monotonic sequence retained, actual lifetime14400s. Regular
  sync continues to issue matching signed CRLs, with expiry/revocation checks intact.
- Gateway leaf actually published with service UID/GID979:979, mode0600, service-user
  read proof and final readback PASS; expires04.10 **17:30:19UTC**.
- Existing bootstrap unit now uses `--duration 4h`. Fresh actual seed directory issued
  13:31:39.07204735UTC, expires17:31:33.403444286UTC; no invented expiry edits.
- Bounded bootstrap acceptance PASS, PID3908811/restarts0.13:34:31 TLS readback verifies
  actual loaded leaf against profile/authority, gateway hash unchanged, CRL14400s.

**Conservative session-window end is17:30:19UTC (20:30:19 Moscow), the earlier gateway
leaf expiry**, not the slightly later directory/device expiry. This is a fixed material
window, not four new hours after every app open, and not a four-hour stability test.
Do not send a stale handoff if meaningful time has elapsed; recheck all bounds.

## Owner acceptance

Owner Redmi UID10283/Support FC-4D8Q-REEG, encrypted identity and enrollment fingerprints
match the accepted beta62 baseline. No production app reinstall or data/cache clear.
An already-valid short cache would suppress ordinary background fetch until its
five-minute refresh threshold. For bounded owner acceptance, a separate private test
explicitly invokes the existing authenticated challenge/fetch, native validation,
atomic cache import and signed ACK path. It skips only the background scheduling
decision, **not authentication, signatures, native validation, expiry or monotonic
cache checks**. No production behavior or installed APK changes.

Owner long fetch13:37:22UTC / ACK13:37:23UTC: READY/PRESENT_VALID,
orchestrator_usable=true, revision3, CRL4066, expires17:31:33UTC. On-device remaining
time14050s; actual gateway bound13976s (3h52m56s), exceeding3h45m acceptance target.
New device certificate replaces the short cached one under the existing long-mode
policy, same identity/revision. Separate test APK only was compiled/signed privately;
it is not another distributed release artifact.

Controlled owner restricted session: established=true, healthy_at_capture=true,
failure_category NONE, duration59509ms including about35s healthy observation.
Product-share export succeeds. This is controlled owner validation, not automatic
fallback or a Russian mobile reproduction. Final correlation/preservation receipts
are kept under `state-client-build/field62-long-window/owner/`.

Final correlation PASS:48 client/88 server events, all four lookup directions,
bidirectional carrier/heartbeat, complete lifecycle, no server sequence gaps and
client/server trace privacy checks PASS. Session tag
`d5fee5229155c8b8ebb26c7c61e3d4c9147123d9829c4e839cf40baf2b885c3f`, connection
`d0d1d62f-4b6e-4042-84b9-b76ed108d07e`, incident
`59d240bf-37ea-4966-b6d9-fbb66fcf2d77`. First client failure absent. Server
RELIABLE_RETRY_EXHAUSTED at13:38:47.837UTC is **25.962s after intentional owner cleanup
13:38:21.875UTC**, not the cause of an unplanned owner disconnect. Age9506ms/retries8/
pending1/ACK count102 retained; no claim that it reproduces or fixes the Russian failure.

Broad journalctl queries timed out while traversing archived journals. Bounded
readback of the observed current `system.journal` file and exact13:37–13:42UTC interval
completed and yielded the complete session. No journald restart, log deletion, gateway
restart or source change was required. For the tester export, select the actual files
covering its timestamps (including a rotated file if needed), keep byte/time bounds
and require complete lifecycle/no gaps before accepting the evidence.

Post-rollout AWG15771ms, HTTPS200/VPN present PASS. Final UID10283/data inode601521,
Device Identity/enrollment/activation/Support preserved. Only the separate test package
was removed. Exact static/download inventory, beta62 bytes, other platform assets,
admission/Support/devices/invites and AWG/TCP process identities verified unchanged.

## Preservation, rollback and next gate

Public TLS probes: status200, ordinary challenge400, chat challenge400, malformed
restricted challenge400. Signed Android catalog and discovery hashes match the
accepted beta60 bytes. Existing AWG/TCP process identities unchanged. Grant expiry
changes are intentional; devices/invites/Support/admission remain unchanged.

Protected preparation/backup/receipts on **both authorized hosts**:
`/opt/apps/family_connect/restricted-materials-stage-20261001/field62-four-hour-20261004`.
Includes previous material, previous wrapper/unit/drop-in, RU DB backup and immutable
archive copies. The DB backup is evidence/recovery input, **not a rollback instruction**.
No rollback occurred. If needed, retain compatible validators, return issuance/CRL
policy to a bounded shorter window, republish a newer CRL and create a corresponding
fresh shorter seed. Never restore expired issuer/certificates, lower trust/CRL floors,
restore the DB, downgrade/uninstall clients or clear their secure state. For ordinary
HTTP startup failure, the operator removes only its new HTTP drop-in and restarts the
previous known unit; restricted health must then be re-established separately.

Tester long READY/ACK and its actual usable headroom are now checked. Keep the test
within the stated window; if delayed past it, refresh the full chain/readiness first.
Next exactly one restricted mobile attempt and immediate
diagnostic export after failure/disconnect; preserve first causal failure separately
from cleanup/recovery. The original ReliableStream disconnect remains unresolved.
