# FIELD export(10): real restricted sessions correlated — 2026-10-04

## Evidence and scope

`FamilyConnect-diagnostics(10).json`,122832bytes, SHA256
`e497ba1d62a8e077611fca11a91891823bed03ca3f5a3bd73a2956b65cb5c71d`.
FC-YHQB-9VJN, reported0.1.18-beta61/code61, not an attestation of installed APK bytes.
Saved incident CELLULAR; latest snapshot WIFI/AWG CONNECTED. No additional tester
attempt was requested or performed by the operator. Server analysis is read-only.

NL journal restricted-bootstrap unit read for10:21–10:28UTC, bounded below10000 lines
and8MiB; selected structured traces pass exact allowlist equality. Unstructured text
is withheld, with input digest/count retained. Four-ID joins use client metadata and
are not server authorization claims. Private receipts and full safe correlation:
`state-client-build/field61-r2-diag10/`.

## Session bindings

| Field | First session | Second session |
|---|---|---|
|connection_id|dea9496d-b3dd-4e56-b3bf-20d514709ac9|8e5774bf-d228-4bef-be8d-0bb5ff81bc5d|
|incident_id|148ffd22-0574-4b37-9627-0afc659fe4c5|9ac25ac6-0c45-4084-b391-07cf78630e39|
|session_tag|5d092fb4add0750e1f5970854e302865d1fc8401c0e573e945f546e267383408|a008c0680264105a881d148dc4c185e6003a7f1db5b917cd45e61a9855809052|
|Client native terminal UTC|10:23:53.513|10:25:48.944|
|Client reliable_terminal|recovery_exhausted|recovery_exhausted|
|Client retransmissions / recovery_timeouts|23 /24|74 /75|
|Client DNS responses / errors|2 /0|30 /0|
|Client TCP open success / errors|8 /1|16 /0|
|Exported client / server trace events|32 /54|57 /69|

Both bindings resolve through Support ID, connection ID, initial incident ID and
session tag. Server sequences are complete, starting at1, with no gaps; all required
normal lifecycle stages including heartbeat TX/RX and cleanup are present. The
correlator's owner_lifecycle_complete=true is a stage-checklist result, **not**
physical owner acceptance or proof that the initiating failure is fully traced.
First client's exported sequence begins12; its initial client events are absent.

## What worked and where it stopped

- Both client READY gates pass (10:23:12.239 and10:24:56.679UTC). Sessions precede
  accepted readiness expiry10:34:57UTC. This is not the expired-readiness failure
  of exports(8)/(9), and four-hour code was not installed or deployed for these runs.
- Server Family TLS establishes10:23:41.388/10:25:14.090UTC; gateway sessions establish
 10:23:42.789/10:25:15.146UTC. Client agrees on established TLS/gateway stages and
  records real DNS/TCP results. Both endpoints report bidirectional carrier activity.
- Client terminal snapshots: IO_CLOSED, reliable_terminal=recovery_exhausted,
  authorization_denied=false, protocol_errors=0, signaling_failure=NONE, ice_failure=NONE.
  These are stronger evidence than the outer UNKNOWN_INTERNAL display.
- Source `reliablestream/stream.go` sets recovery_exhausted only for ErrExhausted.
  `engine.tick` can return it for open-handshake timeout, outstanding frame age or
  per-frame retry budget. These sessions already exchanged data, so the relevant
  failed stage is established-stream recovery; the exact age/retry branch and why
  acknowledgments/progress stopped are not identified by the exported counters.
- Client LOCAL_CLOSE starts10:23:53.496/10:25:48.661UTC. Later FAMILY_TLS_ERROR is after
  close/cleanup. On the server LOCAL_CLOSE similarly precedes TLS_ERROR and terminal
  GATEWAY_CLOSE/gateway_session_failed. These cleanup effects are not independently
  proven causal failures. Cross-host wall-clock ordering is not causal proof.
- Recovery creates new incident IDs and completes cleanup, but new descriptor is
  NOT_ATTEMPTED and restoration ends UNKNOWN_INTERNAL. No successful fresh-session
  recovery is shown. Structured first_failure is absent on both endpoints: this is
  a remaining diagnostic gap despite successful correlation and lifecycle coverage.

## Decision

Real restricted disconnect is now reproduced and exactly correlated. The observed
failure boundary is ReliableStream recovery exhaustion, not expired certificates,
denied enrollment or a recorded ICE/signaling close. No RKN attribution, network
root-cause claim or transport fix is justified. Do not raise retransmission/timeouts
blindly or confuse these packet-recovery bounds with certificate lifetimes.

Next: preserve this evidence, identify exact exhaustion branch/ACK progress and
surface the causal reliable failure before cleanup; separately complete the
[four-hour candidate](2026-10-04-four-hour-readiness.md) owner/build/material gates.
No additional blind mobile retry is required to establish these already captured facts.
Runtime rollback unnecessary: journal analysis made no server/client changes.
No APK/version/catalog/admission/Support-ID/publication changes.

## Checks

Two exact correlated tags, four lookup paths each PASS; structured server trace
allowlist/privacy screen PASS. Client export keyword screen excludes raw URLs,
private keys, bearer/OAuth material and known credential fields; not a universal
secret detector. No raw journal text or credentials copied into Git. Existing local
diagnostic correlation regressions are included in the168-test Python PASS run;
documentation links and whitespace checked separately.
