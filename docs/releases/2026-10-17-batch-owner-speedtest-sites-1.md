# BATCH-OWNER-SPEEDTEST-SITES-1 — owner clarification

**RESULT=PARTIAL_REACHABILITY_OWNER_REPORTED; SITE_CAUSE_NOT_PROVEN.**
Date:17 October2026. Follow-up to the
[export13 analysis](2026-10-17-batch-owner-export13-1.md), input review
`bef08a040f066daf0c955665bffb92a9d502b02d`. This records a later owner statement,
not a new export, request receipt or measurement. Earlier evidence is unchanged.

## What the owner observed

- The unavailable sites were connection-speed testing sites. Their pages did not
  open at all; this is not merely a speed-test operation or static-asset failure.
- YouTube opened and Telegram worked, but loading was reported as slow.
- Exact speed-test domains, failure messages and corresponding VPN-OFF results
  have not been supplied. No throughput measurement was completed or reported.

This narrows the symptom to partial reachability. It does not establish a general
HTTPS outage, DNS failure, operator filtering, or a UDP/WebSocket restriction.
Do not attribute page-load failure to a speed test's traffic pattern when the
page itself did not load. Working YouTube/Telegram does not prove every site or
DNS resolution works, nor establish which protocol those successful requests used.

## Evidence and next step

Export13 still demonstrates five expired TCP admission budgets and reliable
recovery/window pressure in N1. Neither observation is yet mapped to the failed
sites. The50 aggregate mux errors remain unclassified; no new causal attribution
or batching regression is proved by this clarification.

The next local comparison remains bounded mixed browser-shaped stream pressure
plus directional loss/ACK delay on the retained admission1 and batch1 sources.
It has not run in this follow-up. Exact site names and any already observed
VPN-OFF behavior would help attribution, but do not gate that local comparison.
No additional phone CONNECT or export is requested just to supply site names.

## Unchanged state and scope

Last verified pair remains `0.1.18-research84-ui60-4-batch1`, code84,
APK697f9c24…49233f/native dd722ead…20c23/gateway4b722d2d…fab7, with full identities
in the [rollout receipt](2026-10-17-transport-batch-maintenance-and-rollout-1.md).
These are existing receipts, not fresh installed/loaded byte checks. Last phone
observation remains export13 CONNECTED; current VPN state is not newly observed.

Actions: documentation only. Product patches, tests/builds, emulator, signing,
install/rollback, SSH/ADB, restart, maintenance, CONNECT and new export requests:0.
No automatic rollback or deployment; no site-specific workaround, cap/RTO/queue
change, acceptance promotion or release. **SPEED_IMPROVEMENT=NOT_MEASURED.**
