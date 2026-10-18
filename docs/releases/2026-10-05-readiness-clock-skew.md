# Readiness clock-skew correction — 05.10.2026

## Scope and decision

User requests the working Telemost path in Family Connect, not a separate diagnostic
application. The attempted diagnostic variant was cancelled before distribution;
all its tracked source changes were removed. No new APK is required by this patch.
Owner/tester and targeted public APK remain `0.1.18-beta65`/65, SHA256
`dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`.
Default/updater/invitation remain60. Gateway executable remains accepted a813dc5,
SHA256 `055716447a1fe4bd8859dc2877410e756a9dc60a81b0ae5203a23f99606326a0`.

This removes the concrete subsecond issuance/import/ACK barrier from export12.
It does not establish why export13's fetch failed on cellular, resolve original
DATA/ACK loss, or prove a Krasnodar Telemost VPN result. Arbitrarily incorrect phone
clocks still require a separate authenticated-time design; no manual clock change
is requested. Keep the tester's working VPN for coordination and preparation.

## Server correction

- Backdate new readiness issuance and leaf NotBefore by at most5 seconds, respecting
  issuer/CA start bounds. Shorten readiness expiry where necessary rather than
  increasing its configured one/four-hour interval or absolute expiry.
- Backdate CRL ThisUpdate by at most5 seconds. Preserve prior ThisUpdate and increasing
  CRL number: the gateway anti-rollback check is unchanged. CRL expiry remains bounded
  by its own configured lifetime and the delegated issuer.
- Accept signed, correlated ACK observations up to5 seconds before the challenge,
  symmetric with the existing5-second future allowance. Proof binding, device/grant
  revocation, replay protection, expiry and revision/CRL floors remain required.
- Existing freshly issued certificates, directories or issuers can still have a later
  start bound. They must mature before the test; no bypass of those signed bounds.

## Verification

Regression before patch:3 failed,8 passed,11 native checks deliberately skipped.
After patch: **131 passed**, including the unchanged native validator at phone
offsets−5s/−715ms/−485ms/0/+5s. Restoring only the old response issued_at reproduces
rejection. Early/expired/revoked/forged/future-CRL cases remain rejected; signed ACK
offset boundaries, revocation, expiry, correlation and rollback checks pass.
The tested native provisioning/checker sources have no diff from accepted APK65
source86fa1bae8b97ff34d3e8cbd5b3cfe923cb7d71a6. This is a compatibility check, not
a rebuild/re-signing of that APK.

Initial packaged suite:310 passed,14 skipped,1 failed. The failure combined old
packaged Access.initialize (no Support-ID schema creation) with a current-source HTTP
fixture. It is retained, not hidden or labelled PASS. Follow-up separates exact
package tests from HTTP tests using the normal initialized schema and the actual
candidate HTTP archive. Final exact-package suite: **295 passed**. Separately,
the actual candidate HTTP archive with the normal initialized Support-ID schema:
**2 passed** (Support-ID proof/alias and full signed readiness exchange). No production
schema or ordinary-route changes were made to accommodate the fixture difference.

Build resource failure: `/tmp` disk quota affected Go compile/link. Setting both
TMPDIR/GOTMPDIR and build cache to ignored repository storage allowed compilation;
no arbitrary user artifacts were deleted. HTTP tests require outside-sandbox sockets.

## Packages and activation plan

Candidate source: HEAD25532b1 plus the recorded uncommitted three-module patch;
not an exact-source CI release. Existing accepted archives preserved byte-for-byte
except those explicit members; no ordinary-route/admission code replaced.

| Artifact | Candidate SHA256 | Previous SHA256 |
|---|---|---|
| HTTP | `43b9978317dd39e93f369f9b691627287464cb4f942a1aa759e62262cb4b5dc0` | `098889496b9327a18c6ef08bba57ff73e81a9eae170a5d2d5030301cbaa544e1` |
| Sync | `9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1` | `9ed01927ae49cf402e126807fa3d219d8b492383afb47b485f5c14149abb2e20` |

Activated05.10 at13:55–13:56UTC: new immutable runtime names
`friends-access/http-clock-skew-20261005.pyz` and
`friends-access/sync-clock-skew-20261005.pyz` on the authorized RU/NL hosts.
Evidence/backups: `/opt/apps/family_connect/restricted-materials-stage-20261001/clock-skew-20261005/`.
Local private receipts: ignored `state-client-build/readiness-clock-skew-20261005/`.

Issuer4 expired05.10 at13:28:47UTC. Replaced with same-key/root-authorized issuer5,
fresh gateway leaf/CRL/directory, unchanged owner/tester admission and grant revisions.
Offline root key stays local. Old expired credentials must never be restored.
Runtime rollback restores the backed-up HTTP/sync drop-ins and gateway sync wrapper
to the preserved beta62-window archives; keep newer valid issuer/CRL security floors.
On credential publication failure, stop restricted service and diagnose; do not expose
an unauthenticated gateway or affect ordinary AWG/TCP services.

## Actual deployment and phone readback

- Offline-signed issuer5 expires06.10 at13:51:23UTC; minimum revision stays1.
  Only the existing owner3/tester1 grant expiries renewed; admission unchanged.
- Amsterdam native positive/negative credential check and owner/group/mode publication
  PASS13:53:31UTC. Gateway PID464237, NRestarts0, executable05571644 unchanged.
- Actual served TLS certificate matches the file and verifies under the new authority;
  CRL signature valid. Its expiry is **05.10 17:52:14UTC =19:52:14 Brussels
  =20:52:14 Krasnodar**. This is the current effective test ceiling, not the later
  directory/client-cache display or tomorrow's issuer expiry. Recheck before later tests.
- RU HTTP PID2676506, NRestarts0, `/proc` command references the new archive. Both
  archive hashes verified on hosts; gateway sync wrapper points to the new sync
  archive, timer active and last sync successful. RU/NL directory bytes equal.
- Ordinary AWG/TCP service state and PIDs unchanged on both hosts. Malformed ordinary
  HTTP/chat/restricted requests remain rejected with400. No unauthenticated gateway.
- Owner Redmi's **installed beta65 bytes** verified against the unchanged public hash.
  Launched the normal FriendsActivity13:56:04UTC, with no install/instrumentation APK,
  no clock change, no data reset and no radio/VPN mutation. Actual fetch13:56:07,
  signed native READY/ACK13:56:08UTC, grant revision3 / CRL6689. Its cached expiry is
  later than the actual gateway certificate; use the earlier ceiling above.
- Tester beta65 last successful fetch remains12:45:10UTC with no ACK. No fresh tester
  attempt is visible at the final13:56:27UTC readback. Owner success is not tester success.

## Remaining field action

### Tester readiness confirmed14:11UTC

After the user reported the tester switched on, read-only verification14:11:35UTC
confirms **tester FC-YHQB-9VJN / beta65**, fresh challenge+fetch14:09:43UTC,
signed READY/ACK14:09:44UTC, revision1/CRL6714, admitted and non-revoked. The signed
client observed_at14:09:42 is one second earlier than the server challenge, which
the previous ACK guard would reject. Native import and the corrected ACK path both
succeed on the actual tester; not merely on the owner's Redmi. No APK/clock change.

Gateway binary/profile/TLS, archive hashes, RU/NL directory equality and sync timer
rechecked14:11UTC; headroom13239 seconds, expiry unchanged17:52:14UTC. Ordinary
AWG/TCP PIDs unchanged. Read of the restricted unit's bounded journal14:08–14:13UTC
returns zero lines, no session traces/exchange failures in that window. This does
not establish success/failure of Auto's ordinary AWG/TCP candidates or prove a
Telemost tunnel. Exact client diagnostics are still needed to attribute any attempt.
Receipts: `live-verification-*` and `tester-window-*` in the existing private folder.

NEXT mobile Auto/real traffic check; preparation is now complete. If Auto is already
running, preserve that attempt rather than asking for another disconnect/reconnect.

### Prior handoff13:56UTC (superseded readiness state)

The server blocker is corrected and owner65 normal import succeeds. A new APK is not
needed for this correction. Fresh tester READY/ACK followed by an actual Krasnodar
mobile Telemost tunnel is **not yet confirmed**; the remote phone is not attached to
the operator's ADB. Do not claim the original transport problem solved.

Tester keeps the working VPN for receiving the complete instructions and opening
Family Connect to prepare materials. Only after current readiness is confirmed:
one brief mobile Auto test, then return to the working VPN and send the normal
diagnostic JSON. If preparation fails, export while the working VPN is still on;
do not repeat the failed disconnected trial or request manual clock changes.
