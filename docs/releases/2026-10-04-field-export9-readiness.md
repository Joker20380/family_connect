# FIELD export(9): fresh readiness after failed attempts — 2026-10-04

## Input and scope

`FamilyConnect-diagnostics(9).json`,84559bytes, SHA256
`7ca72d1f870824eb2d60cae741dbd499b01396f5b6be3a932c9028a93cb48752`.
Tester FC-YHQB-9VJN, reported0.1.18-beta61/code61. Export does not attest exact APK
bytes. Accepted targeted APK remains4297ea1a/signer67a90d1 per the
[verified delivery](2026-10-04-beta61-r2-direct-delivery.md); no rebuild/resign/install,
deployment, renewal, catalog, enrollment, Support-ID or FIELD change in this task.
Current source HEAD64849e828add45407625d31df61413ac98e9a2cc plus preserved existing
uncommitted work. This is local analysis and read-only RU/NL verification, not a
new release or a test remotely performed on the tester phone.

## Client timeline (UTC)

| Time | Evidence |
|---|---|
|10:00:12.968|NATIVE_VALIDATION_FAILED; precise validator branch not available|
|10:00:22.593|Wi-Fi-era AWG connection fde4773b CONNECTED|
|10:03:03.544–10:03:55.682|Connection d92a99d8 fails after52.138s; AWG/TCP NETWORK, restricted NOT_READY/BOOTSTRAP_UNAVAILABLE|
|10:04:06.272–10:04:58.429|Connection b8852d9d fails after52.158s; same reasons; saved incident explicitly CELLULAR|
|10:05:15.521|READY, after both failures|
|10:05:16.742–10:05:23.985|New connection76030d69 starts and AWG connects; latest snapshot WIFI/CONNECTED|

Saved incident is new, not identical to export(8):
connection `b8852d9d-13cb-4bdd-8d6d-4b49e80fabfd`, incident
`f025efdb-d049-434c-b479-a8dd4d471ceb`. Latest ring connection
`76030d69-9b45-4ba6-981c-6aa36d1a3a72`, incident
`b5b76a39-4567-43f2-952b-7151f8c537a2`.

Both objects have empty restricted_session/restricted_history. Recovery events say
restricted_descriptor NOT_ATTEMPTED. There is no established restricted lifecycle
or session_tag to correlate; this does not demonstrate a session-tag parser failure.
The ring's final readiness/bootstrap UNKNOWN fields are reset on connect_requested
by DiagnosticRing.event; the10:05:16 new AWG connection follows the READY event.
This reset affects diagnostic snapshot fields and does not itself delete credentials.
Latest WIFI classification must not be applied retrospectively to every ring event.

## Server corroboration,10:17:02–03UTC

- RU latest tester challenge/fetch10:05:15UTC, ACK10:05:16UTC. Receipt:
  READY, provisioning/bootstrap PRESENT_VALID, orchestrator_usable=true, NONE failure,
  beta61/code61, grant revision1/minimum CRL3680. Expiry **10:34:57UTC**, or
  **13:34:57 Moscow time**,17m55s remaining at the check. Client READY timestamp
  matches this server transaction; no later mobile attempt is present in export(9).
- Exactly two admitted devices, same owner/tester Support IDs, both non-revoked.
- RU/NL signed CRL3701 matches, lifetime3600s, expires11:16:35UTC. Active sync timer,
  last run exit0/success; actual ExecStart uses targeted archive1bfa085b with
  --crl-lifetime3600. This verifies the deployed opt-in policy, not a changed default.
- Matching directory SHA256
  `38d2ec4fc345b39551cba21b2d1c9dc4c65cc6948545530c1e1c7145cffe3fb1`,
  expires10:34:57.984222868UTC. **Directory expiry now limits this accepted readiness**;
  a one-hour CRL does not guarantee a full hour remaining at each fetch.
- NL loaded certificate matches profile, expires13:39:54UTC; same gateway binary
  b9b7d542, PID3789112/restarts0. Issuer expiry remains14:13:53UTC.
- RU beta60 discovery and invitation bytes match known6e5817dc/014ebdbd hashes;
  default Android code60/URL unchanged. No fresh public APK download or full signed
  catalog read in this task; previous verified public delivery remains the evidence
  for those artifacts. No Linux/Windows writes.

## Decision and remaining work

User asks why a four-hour renewal still leaves minutes. Four hours was the gateway
leaf lifetime only. At10:05:15 fetch the existing directory left29m42s; at10:17:02
check17m55s remained. These are remaining lifetimes, not newly imposed17-minute TTLs.
The practical request for a long uninterrupted testing window is not fully solved.
The installed native delivery validator explicitly rejects lifetimes above3600s;
merely setting a four-hour server delivery would fail validation. Directory freshness
and whole-chain lifetime must be addressed, with client rebuild/reacceptance if
extending that native contract. This clarification makes no runtime/code changes.

The longer-policy data has now been accepted on the real tester phone. The two
failed attempts preceded that acceptance and cannot test restricted transport.
The separate10:00 native-import failure is still unresolved; neither clock skew nor
a particular validator branch is proven. Do not claim RKN filtering or a transport
fix from these records.

Coordinate one mobile attempt while accepted readiness still has headroom for network
handover and ~52s Auto fallback, then immediately export diagnostics. If this window
has passed, obtain normal fresh readiness on working Wi-Fi and verify actual expiry
before trying again; simply retrying on mobile will not renew expired cached material.
Do not uninstall, clear data, reenroll or bypass signature/expiry/revocation checks.
No runtime rollback is required for this read-only task. Existing deployed policy
and gateway renewal rollback rules remain in the
[testing-window report](2026-10-04-field-test-window.md).

Private evidence: `state-client-build/field61-r2-diag9/`. Bounded privacy screen PASS:
expected export/event schema, including allowlisted recovery fields; no session
payload, URL, private-key or Bearer pattern. This is not a universal secret detector.
Server output contains selected metadata only, not credentials or raw database rows.
Local timeline/schema checks and both live verification assertions PASS. Documentation
link/whitespace checks apply; no product code changed or new product tests claimed.
