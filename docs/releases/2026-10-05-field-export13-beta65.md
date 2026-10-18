# Field export13 — mobile Auto attempt, 2026-10-05

## Result

The requested current-system mobile attempt did **not** connect. Unlike export12's
older beta64 incident, both ring and incident in this export identify tester
`FC-YHQB-9VJN`, installed `0.1.18-beta65`/65. Final network snapshot is CELLULAR.
No code, APK, server configuration, material, admission or grant was changed during
this analysis. Development remains stopped after the user's explicit request to
test the already installed system instead of continuing implementation.

User supplied `FamilyConnect-diagnostics(13).json`,83088bytes, SHA256
`ee33e0d4f9ed1526796443700ca9de3799b12974d73022a56caa912935ea8738`.
Raw export remains outside Git. Each snapshot has128 events; deduplication across
ring/incident yields131 distinct events and two connection IDs. Do not count the
same attempt twice or mistake old successful DNS probes for this attempt's success.

## Earlier working connection

Connection `71bc1088-aa02-4178-bbe8-cdcfcf268627`: retained events12:54:56.946 through
13:03:22.027UTC,98 DNS_PROBE_OK and no DNS_PROBE_FAILED. Before explicit CANCELLED
disconnect the orchestrator is CONNECTED on AWG. Its start is outside the bounded
ring, so full startup evidence is unavailable. The final CELLULAR snapshot does not
prove the earlier connection's physical network type. This establishes earlier AWG
operation/DNS health, not arbitrary site access or successful restricted transport.

## New mobile attempt

Connection `5fce2231-1922-4af1-8726-8ef2e8a573f9`, phone event timestamps:

| UTC | Event |
| --- | --- |
| 13:03:41.755 | DISCONNECTED → CONNECTING, Auto begins |
| 13:03:42.842 | READINESS/FETCH_FAILED |
| 13:03:47.141 | AWG candidate begins |
| 13:04:07.278 | AWG NETWORK, about20.1s after candidate begins |
| 13:04:09.414 | TCP candidate begins after transition/backoff |
| 13:04:29.585 | TCP NETWORK, about20.2s after candidate begins |
| 13:04:33.721 | Restricted candidate begins after transition/backoff |
| 13:04:33.897 | READINESS/NOT_READY |
| 13:04:33.904 | Restricted BOOTSTRAP_UNAVAILABLE |
| 13:04:33.999 | CONNECTING → FAILED, duration52244ms |
| 13:04:41.279 | Explicit disconnect completes; VPN capture released |

This connection has29 unique retained events,8 DNS_PROBE_FAILED and no successful
DNS probe. Ring ends DISCONNECTED/capture=false; saved failure incident retains
FAILED/capture=true. These are snapshots before/after user cleanup, not contradictory
status. Outcome maps agree: AWG NETWORK, TCP NETWORK, restricted BOOTSTRAP_UNAVAILABLE.
Neither snapshot contains a restricted session or history.

`RestrictedTunnelEngine.up` records NOT_READY when `cache.usable()` returns null,
then throws BOOTSTRAP_UNAVAILABLE **before** `NativeRestricted.beginReady`. Therefore
this attempt did not reach a new native restricted session/descriptor. It is not
a repeat of the ReliableStream DATA/ACK exhaustion from export11 and does not test
the newly deployed gateway cleanup fix over the tester's mobile carrier.

## Server comparison and limits

Read-only RU observation13:07:18UTC: tester admitted/non-revoked; latest successful
challenge/fetch still12:45:10UTC, revision1/minimumCRL6607, no ACK/native READY.
No new successful fetch for the13:03 attempt appears in this bounded readback.
Receipt saved under ignored `state-client-build/bootstrap-cleanup-owner/` as a
timestamped readiness JSON. Owner65's separate READY is not tester readiness.

Export13 records FETCH_FAILED during the attempt, **not another observed
NATIVE_VALIDATION_FAILED at that point**. It does not expose the HTTP phase/status or
underlying exception. Export12's clock-sensitive native/ACK guards remain a prior
blocker, but do not alone prove why this later mobile fetch failed. NETWORK is also
too broad to locate AWG/TCP loss or attribute it specifically to RKN. The last verified
server material expiry13:28:47UTC was later than this attempt; this does not make an
older rejected/expired client cache usable.

## Decision / next work

The mobile attempt is complete and negative; another identical trial with the same
unready cache would not add useful evidence. Keep/restore the working VPN for
communication. No manual clock changes, data clearing, reinstall or immediate repeat
requested. Local/export/server analysis completed; no production fix claimed.

Before asking for another field attempt, resume explicitly scoped implementation
and acceptance on the engineering side: a compatible clock-sensitive issuance/ACK
fix if confirmed by tests, preserve expiry/revocation/proof/anti-rollback checks,
then verify tester-ready material over a working connection. Grossly incorrect phone
clocks remain a separate authenticated-time design requirement, not solved by a small
tolerance. Renew/revalidate actual authority/leaf headroom for the later test rather
than racing the05.10 13:28:47UTC limit. Preserve native/API failure evidence without
exposing keys/profiles. Subsequent trial needs one pre-agreed scenario and a route
back to the working VPN, not live instructions while disconnected.

Owner/tester/targeted public APK65 and default/catalog/invitation60 unchanged. Gateway
remains the last deployed05571644; no fresh NL process audit in this read-only RU
comparison. Existing rollback paths remain in the
[gateway deployment report](2026-10-05-bootstrap-cleanup-race.md).
