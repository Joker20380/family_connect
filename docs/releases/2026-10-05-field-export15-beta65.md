# Export15 — expired pre-renewal attempt; fresh tester readiness confirmed

## Evidence and scope

Input `FamilyConnect-diagnostics(15).json`,50767bytes, SHA256
`ba5b0d4e3b2544a9c5268fc5db89e6a18b57b9e50b979a8f45c9ee20c08e61ff`.
Tester FC-YHQB-9VJN, installed0.1.18-beta65/code65, Android API31.
Ring79 events, incident75; current export network class CELLULAR. That top-level
class does not establish the underlying network of every earlier event.
Local allowlisted summary: `state-client-build/field65-export15/summary.json`.
Offline correlator finds zero restricted sessions; session/history/counter objects
are empty. No session tags exist to join a Telemost data-session server trace.
This report compares the client timeline with server readiness and the recorded
certificate lifetimes, not an invented paired transport trace.

## Timeline (UTC05.10)

| Time | Evidence |
| --- | --- |
|19:36:45–19:36:47|Client READY; server fetch19:36:47/ACK19:36:49 confirms old material.|
|19:37:03.419|AWG CONNECTED, followed by37 successful DNS probes.|
|19:38:10|Previous actual gateway leaf expires; old readiness receipt expires19:38:29.|
|19:40:09.387|AWG disconnect begins with CANCELLED after about186s connected, not a recorded transport failure.|
|19:40:43.245|New Auto attempt starts, already after both expiry bounds.|
|19:41:08.801|AWG NETWORK.|
|19:41:31.106|TCP NETWORK.|
|19:41:35.387|Restricted local NOT_READY, then BOOTSTRAP_UNAVAILABLE; no native session.|
|19:41:35.491|Auto FAILED after52.246s.|
|19:42:38.041|Later foreground readiness FETCH_FAILED; this does not explain the earlier AWG/TCP network errors.|
|19:53:04–19:53:12|Previously documented credential-only renewal and new directory publication.|
|19:59:59 /20:00:00|New server fetch/native READY ACK from unchanged tester65, grant1/CRL7360.|

The failed attempt is **before the19:53 renewal**, even though the file was received
later. Expired old material is a confirmed blocker; generic local NOT_READY alone
does not reveal every validation sub-check. This is not another observed
RELIABLE_RETRY_EXHAUSTED, nor a post-renewal test of the RTP correction. Earlier AWG
DNS success is not proof of Telemost traffic or of stable operation on cellular.
No phone-clock error or RKN involvement is established here.

## Current server and tester acceptance

Read-only20:03:29UTC verifies accepted gateway source8d04632, loaded SHA256
`7c6e1e11208e167309cbe83dac0f5f1f1bb306f4e41628180367aa6fa5e9aa50`,
PID652351/NRestarts0, profile/served TLS match and13774s headroom. Ordinary-service
and admission invariants remain unchanged. Readiness read20:03:32 confirms fresh
post19:53 tester fetch/ACK, READY/PRESENT_VALID/orchestrator_usable, admitted and
non-revoked. This closes the fresh-import gate, not the real-traffic gate.
Actual gateway leaf remains **05.10 23:53:04UTC /06.10 01:53:04 Brussels /
06.10 02:53:04 Krasnodar**; the receipt's23:53:09 expiry does not extend it.
Receipts: `state-client-build/rtp-gap-20261005/final-verification-*.json`.

No source/runtime/security-policy change, build, restart, renewal, installation or
publication in this task. Installed/targeted beta65 remains SHA dfbdb535;
default/catalog/invitation60 unchanged, not newly reverified as a public release.
Existing executable rollback05571644 remains at
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005/bootstrap-broker.previous`.
Retain current valid credentials/issuer5/CRL floors on rollback; never restore the
expired old profile or directory. See [deployment/renewal evidence](2026-10-05-field-export14-beta65.md#late-resumption-after-interruption).

## Next single field trial

Deliver the complete instruction while messages work: disable Wi-Fi and the other
VPN, enable mobile data, start Family Connect Auto; allow up to2min for fallback.
If connected, browse several pages for3–5min. On failure do not loop manual retries.
Save diagnostic JSON, restore the working VPN, send the export. No screenshots,
clock adjustment, reinstall or separate test APK. Identify the actual transport
from that export: an AWG success does not by itself accept Telemost stability.
No background watcher or scheduled task remains. If delayed past the actual bound,
revalidate/renew first. Field recovery/loss/RTP effectiveness remains unaccepted
until fresh post-renewal traffic evidence is available.

Operational follow-up after this trial: pre-test readiness must include sufficient
remaining gateway lifetime, not only an unexpired READY receipt. The19:36 import
had about81s before the leaf deadline; do not repeat that preparation pattern.
Do not weaken authentication/expiration or require users to manage phone clocks.

Validation: export timeline/session-count assertions PASS; public documentation
checker481 files/2937 links/zero errors; git diff check PASS. Application/native
tests were not rerun for this read-only diagnosis and documentation update.
