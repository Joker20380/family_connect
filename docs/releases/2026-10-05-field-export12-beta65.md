# Field export12 — beta65 readiness and clock dependency, 2026-10-05

## Evidence

User supplied `FamilyConnect-diagnostics(12).json`,43277bytes, SHA256
`e6cd5816a8276be86c9d353965bb347208a4e698f7b6d7c0baf64cb1dd43b9de`.
Raw export stays outside Git. Current ring is tester `FC-YHQB-9VJN`,
`0.1.18-beta65`/65, DISCONNECTED, no Family Connect VPN capture, readiness
`NATIVE_VALIDATION_FAILED`, directory NOT_USABLE, no restricted session/history.
This confirms installed65 from the export; public availability alone did not.
No Family Connect capture does not establish absence of another working VPN.

The retained incident is **older beta64**, CELLULAR, FAILED, events06:45–07:02UTC,
ending in BOOTSTRAP_UNAVAILABLE. It is not a new beta65 connection attempt and does
not demonstrate failure of the gateway deployed at10:13UTC. No new packet-loss
localization or RKN attribution follows from this export.

Current beta65 events, using the phone's recorded wall clock:

| Event UTC | Result | Nearby server challenge/fetch UTC |
| --- | --- | --- |
| 12:39:08.969 | EXPIRED_ON_IMPORT | Old-cache failure ACK received12:39:10 |
| 12:39:10.285 | NATIVE_VALIDATION_FAILED | 12:39:11, revision1, minimumCRL6596 |
| 12:45:09.515 | NATIVE_VALIDATION_FAILED | 12:45:10, revision1, minimumCRL6607 |

Read-only RU audit12:50:52UTC confirms both fresh requests and absent ACKs. Tester
grant revision1, non-revoked, matching Family; current tester certificate is signed
by the current authority, not revoked, correct device subject, valid12:13:55 through
13:28:47UTC. Issuer4/minimumRevision1 remains valid. The old-cache failure ACK itself
reports beta65 and EXPIRED_ON_IMPORT; it must not be confused with fresh native READY.
Live NL read12:49:18UTC confirms loaded05571644/PID353567/NRestarts0 and matching served
leaf. RU/NL directory equal, timer active, effective headroom2367s, expiry13:28:47UTC.
No renewal, restart, deployment, admission/grant or device-state change was performed.

## Concrete clock-sensitive conditions

`carrier/wholedevice/provisioning.go:130` rejects `delivery.IssuedAt > now.Unix()`.
`control/friends/readiness_receipts.py:76` requires
`challenge_at <= payload.observed_at <= server_now + 5`: it tolerates a small lead
but no lag before challenge issuance. Server fetch stores the same integer `now`
used for response `issued_at`; Android records the import failure after validation.
For the two temporally matched attempts, the phone event is already715ms/485ms
earlier than the server's integer issuance time. At those recorded client times,
the native issuance guard rejects the response and the ACK lower bound rejects the
failure report. The checks are unchanged from accepted APK65 source86fa1ba.

The export does not contain fetch correlation IDs or the rejected response bytes;
request pairing here is temporal, not exact-ID proof. It also exports only the broad
native failure code. Thus the clock condition is a concrete, sufficient rejection
mechanism consistent with both attempts, not proof that every other validation would
pass or an exact measurement of absolute phone clock error. A large wrong phone
clock is not demonstrated; subsecond disagreement is enough to expose this design.

An isolated synthetic reproduction was prepared without production changes.
First checker build selected an empty module-cache path and failed offline; corrected
to the existing cache, the second build failed with `disk quota exceeded`. Native
and ACK reproduction assertions did not execute; **no reproduction PASS claimed**.
Existing crypto/signature/expiry checks were not relaxed. Logs and read-only server
receipts are private under `state-client-build/field65-export12/`; earlier preflights
remain under `state-client-build/field65-krasnodar/`.

## User decision: fix clock dependency later

User explicitly says phone clocks cannot be centrally controlled and asks to address
this later. Do not ask the tester to correct the clock, install another APK, reset
data or repeatedly retry. No time-validation source patch/release in this task.

Future product requirement: readiness, session validity and ACK must not depend on
users manually setting wall clocks correctly. Design authenticated server-time
freshness with monotonic elapsed-time accounting and a safe bootstrap/restart story;
evaluate HTTPS trust when local time is grossly wrong. Merely adding a small skew
tolerance is not a complete solution to arbitrary misconfigured clocks. Keep expiry,
revocation, anti-rollback, proof binding and replay protection; do not accept expired
credentials or turn off TLS/native validation. Test slow/fast clocks, clock jumps,
restart/offline operation, expired/revoked material and stale/replayed time evidence.
This is a deferred requirement, not an implemented design or promised release date.

Tester requires a working VPN to communicate from Russia. Earlier screenshot/VPN-off
instructions were unsuitable: the app blocks screenshots, and disabling the working
VPN cuts coordination. Use the normal «Отправить диагностику» JSON export with working
VPN retained. Any later disconnected trial needs an entire pre-agreed short scenario
and a return-to-working-VPN step; never require new messages while disconnected.

Remaining gates: resolve deferred time/readiness dependency, obtain real fresh
tester READY/ACK, revalidate/renew authority and leaf for the actual later test time,
then one coordinated mobile trial. Owner/public65 and default/catalog/invitation60
unchanged. Gateway remains05571644. Existing executable-only rollback with fresh
credentials remains in the [deployment report](2026-10-05-bootstrap-cleanup-race.md).
