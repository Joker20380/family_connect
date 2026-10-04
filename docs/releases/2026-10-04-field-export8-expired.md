# FIELD export(8): mobile attempt after readiness expiry — 2026-10-04

## Input and scope

`FamilyConnect-diagnostics(8).json`,83067bytes, SHA256
`ba27e2baf62d7d5130ab9c589878347c42edeb3fbad5a048bf2656d13e046bfb`.
Tester FC-YHQB-9VJN, reported beta61/code61; version alone does not attest exact
installed APK bytes. This task is read-only client/server investigation plus docs.
No new mobile attempt, certificate renewal, service restart, APK rebuild/sign/install,
admission/Support change or transport/security-policy modification was performed.

## Timeline (UTC04.10)

| Time | Evidence |
|---|---|
| 08:58:11.277 | Previously accepted client READY |
| 09:12:26.998–27.281 | Existing AWG cancelled; VPN released |
| 09:12:39 | Previously verified readiness expiry from authenticated server receipt |
| 09:12:43.110 | Readiness refresh FETCH_FAILED |
| 09:15:18.687 | New CELLULAR connection starts |
| 09:15:44.173 | AWG NETWORK after DNS probe failures |
| 09:16:06.498 | TCP NETWORK after DNS probe failures |
| 09:16:10.659 | Restricted candidate starts |
| 09:16:10.773 | Readiness NOT_READY |
| 09:16:10.791 | Restricted BOOTSTRAP_UNAVAILABLE |
| 09:16:10.885 | Terminal FAILED, elapsed52.198s |

Connection `3c0262d6-d823-461d-9053-e16adf18a243`; incident
`49da78f6-96cb-40e5-8a4b-640316c7c2b4`. Unlike export(7), this is a new mobile attempt.
Ring and incident are identical, each containing128 events. Both have empty
restricted_session/history; no native restricted session, session_tag or CONNECTED
transition for that transport is recorded. This is the readiness gate before native
session creation, not the original established-session disconnect or evidence of a
session-tag parsing regression. VPN capture remains open at terminal export.

Connection starts159.687s after the previously accepted readiness expiry; the
restricted gate runs211.773s after expiry. Even the Wi-Fi AWG disconnect occurs with
only about12s left in that readiness window. Auto takes approximately52s to reach
the restricted gate in this attempt. Earlier READY is not an indefinite readiness
guarantee. The export does not determine why refresh returned FETCH_FAILED or the
exact Wi-Fi-to-cellular handover instant; no packet/filter/RKN cause is inferred.

## Server readback

RU09:23:49UTC: tester latest recorded challenge08:58:10/fetch08:58:11/ACK08:58:12UTC,
revision1/CRL3556, READY receipt expired09:12:39UTC. No newer recorded challenge/fetch;
currently_ready=false. This ledger is not an exhaustive access log and does not prove
that no failed HTTP request reached the server. Both existing devices remain admitted
and non-revoked; owner readiness is also expired, not substituted for tester evidence.

NL09:23:51UTC: active PID3757156/restarts0; loaded executable
`b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217` unchanged.
Actually served certificate matches profile and verifies against the issuer;
certificate expiry09:39:30UTC, issuer14:13:53UTC. RU/NL signed CRL3604 matches,
expiry09:38:42UTC. Directory matches on both hosts, SHA256
`541fd9aeabd0ef8a53fd0c4ffed77403c0e43efd45d43c237b3aee9d44dac49a`, issued08:39:34UTC,
expires09:34:32.702517154UTC. RU sync timer active, last service exit0/success.
Gateway certificate validity does not make the expired client readiness usable.
Beta60 discovery/landing hashes unchanged; no publication or catalog write.

## Decision

Do not repeat immediately on mobile. Return to working Wi-Fi and obtain fresh ordinary
tester READY/ACK, then verify remaining gateway/issuer/CRL/directory validity before
separately coordinating another attempt. Allow time for handover and the observed
~52s Auto fallback, rather than starting next to expiry. If delayed, repeat the
read-only readiness check, not a blind mobile retry. Never extend accepted TTLs,
disable validity checks, clear app data or reenroll to overcome this gate.

Original session-loss and intermittent native-validation cause remain open. This
attempt does not establish restricted transport behavior under Russian filtering.
No runtime rollback needed: no runtime changes. Previous credential-renewal rollback
restrictions still apply; do not restore expired credentials or lower security floors.

Private analysis/live receipts: `state-client-build/field61-r2-diag8/`. Bounded privacy
screen PASS: expected schema, empty session payloads, no URL/private-key/Bearer pattern;
not a universal secret detector. Raw exports/credentials/product DB stay out of Git.
Documentation link/diff checks are applicable validation; no product code changed,
so no rebuild or product regression suite was required.

## Requested longer validity

User subsequently requested a longer certificate lifetime. Read-only source audit:
`control/friends/restricted_admin.py:publish_crl` hard-codes CRL next_update to
min(now+900, issuer expiry). `RestrictedReadiness.fetch` bounds client certificate/
delivery expiry by that CRL, plus issuer/grant/certificate/directory validity.
Increasing gateway certificate lifetime alone therefore cannot extend readiness.

`carrier/wholedevice/provisioning.go:ValidateDelivery` permits delivery/CRL lifetimes
up to3600s, and directory validators also cap lifetime at one hour. An up-to60-minute
readiness/CRL ceiling is compatible with those existing limits, but is not a promise
of60 usable minutes: remaining directory, certificate and issuer validity can shorten
it. The ordinary sync calls publish_crl regularly; a one-off longer CRL would not be
a durable fix because the next sync would return to the hard-coded900s policy.

This broadens the allowed age of revocation information, not just gateway certificate
validity. Request explicit confirmation of that tradeoff before choosing the60-minute
policy and changing/deploying the server runtime. No changes to TTL, security checks,
APK, server or admission were made in this policy-review step. Future implementation
needs regression coverage and the existing controlled server release/pin procedure.
