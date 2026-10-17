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

## Subsequent owner comparison — regression priority

The owner explicitly reports that before the latest change all sites they tried
opened, although slowly; after the change some of those sites no longer open.
Treat this as **OWNER_REPORTED_REACHABILITY_REGRESSION_AFTER_BATCH1**, not merely
an unidentified site-compatibility complaint. This is a qualitative before/after
observation, not a controlled throughput benchmark or a proven code-level cause.
The earlier statement that exact domains were not supplied remains factual, but
they are neither required evidence from the owner nor a gate for engineering work.
Do not ask again for domains, a new CONNECT or another export to accept the report.

Priority is to restore the preceding version's observed reachability before pursuing
more speed tuning. Compare retained admission1 against batch1, not root main or an
older accepted APK. The narrow local source review confirms the recorded delta:
three runtime carrier files (Family batch send, mux writer selection/terminal removal,
and mux stream chunk sizing), two test files and the private version name. No new
root-cause claim follows from this inspection; mixed-load/loss reproduction remains
pending. Existing admission waits/recovery observations must not be used to dismiss
the owner's before/after regression or assert that batching is harmless.

No product changes or tests were executed in this clarification follow-up. No build,
phone/server action, install/rollback or automatic deployment was performed. The
first goal of a proposed correction is no lost reachability under the bounded local
comparison, not a better clean-link benchmark alone. Real-device improvement still
requires its own agreed verification; the current candidate is not accepted as a
browsing or speed solution.

## Later correction — pages open again; low rate and high latency

The owner subsequently reports that the sites have started opening again. Speed
measurements on several services reportedly show approximately **0.5Mbit/s in one
direction**, with very high ping. This supersedes a claim of continuing page
unavailability, but does not erase the earlier page-load failures or establish a fix.
Track intermittent reachability together with low reported throughput/high latency;
do not present persistent site blocking or a proved batching defect as established.

The rate is now an **owner-reported service measurement**, not merely a subjective
speed impression. Direction (download/upload), opposite-direction rate, numeric
latency, idle-versus-loaded latency and test timing are not recorded. There is no
saved response/result receipt or controlled before/after comparison. It is not valid
to claim0.5Mbit/s in both directions, a quantified regression or measured improvement.

No new export or exact session binding accompanies this correction. Export13's
admission timeouts, recovery and window pressure remain earlier observations, not
counters measured during these speed tests. They motivate local queue/recovery
analysis but do not distinguish latency from the underlay, carrier, destination or
queued traffic in these particular measurements. Do not infer a configured rate cap
or increase production queues/windows/RTO blindly.

Continue the bounded retained-parent/batch1 comparison, recording interactive delay
alongside bulk transfer and stream release under load/loss. Neither clean-link speed
alone nor pages reopening is acceptance. Site names remain unnecessary; any latency
or direction clarification should use already obtained results, not another requested
CONNECT or load test. Phone/server state has not been freshly observed. Documentation
only in this correction; product/test/build/live actions:0.
