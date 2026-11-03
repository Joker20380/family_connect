# Krasnodar supplied diagnostics — 3 November 2026

Read-only analysis of owner-supplied diagnostic export22. Original stays outside Git;
no user/connection identifiers, keys, raw traces or profiles committed. Location is
owner-provided, not established by the file. No server access or mutations in this task.

Two distinct records must not be mixed: incident is beta60 from31 October18:00–18:03UTC
(TCP DNS failures/recovery ending FAILED); ring is beta111, Android API36, Wi-Fi,
3 November17:14–17:22UTC. Current state ends DISCONNECTED, vpn_capture_open=false.
This is not a cellular-only Krasnodar acceptance test or proof of a specific handset model.

## Current sequence

- 17:15:04UTC connect; readiness fetch initially fails then succeeds. SESSION_READY
  at17:15:59 after55.023s. DNS succeeds and actual DNS/TCP traffic is recorded.
- First native failure17:16:44.204UTC: RELIABLE_RETRY_EXHAUSTED, close source
  RELIABLE_EXHAUSTION. Eight retries, DATA age9477ms,8 pending blocks, head not SACKed;
  last ACK255ms ago, cumulative-progress age5155ms. FAMILY_TLS_ERROR follows20ms later.
  Android enters RESTORING17:16:47; later cancellation/release17:17:01.
- New connect17:18:27; SESSION_READY17:19:14 after46.588s, DNS succeeds.
  Second native failure17:19:34.367: same retry-exhaustion first failure,8 retries,
  DATA age9387ms,8 pending blocks, head not SACKed, last ACK290ms ago,
  cumulative-progress age8440ms. FAMILY_TLS_ERROR follows16ms later.
- Recovery fails with FETCH_FAILED/BOOTSTRAP_UNAVAILABLE around17:19:58,17:20:54,
  17:22:21. Cancellation/release follows. Final connect17:22:34 gets fresh READY
  documents in1521ms; bootstrap carrier ready17:22:41, but CANCELLED and final
  VPN_RELEASED/DISCONNECTED17:22:47. Cancellation events do not identify who initiated them.

Both correlated historical sessions have authorization_denied=false, signaling/ICE
failure NONE, P0/LEGACY64, effective send window8. First/second:89/61 retransmissions,
86/62 recovery timeouts,37/16 DNS responses,0 DNS errors,35/22 successful TCP opens,
5/1 TCP open errors. Each unknown_stream counter1 is classified as expected crossing1,
actual mux violations0; it is not evidence of the first failure. Closed peer states and
TLS errors must not be substituted for the earlier recorded reliable-layer close.

## Diagnosis and limits

Confirmed immediate mechanism: missing acknowledgement of the head DATA block exhausts
the bounded retry budget and closes the entire MESH channel, although recent ACKs and
selective acknowledgement of later blocks show the reverse path is not wholly silent.
This matches the approximately9s fixed-retry defect described in
[the slow-link candidate](2026-11-03-mesh-slow-link.md); current source is not the installed
public111 runtime. The original loss/delay location (Wi-Fi, ISP, provider relay, gateway
or implementation) cannot be determined from this client-only evidence. Fresh ACKs
do not prove application delivery; no measured bandwidth or server-load attribution.
Readiness failures are a second recovery obstruction, not a proven cause of the initial
two closes; final READY and successful authorization argue against a persistent ban
or uniformly expired credentials. No assertion that a future candidate fixes this phone.

No build/install/publication or repair: public Android111/catalog6, Windows0.2.16/catalog12,
Linux public0.2.11/owner internal.13 unchanged. Rollback not applicable. Existing MESH2
then client-delivery order preserved. Remaining: qualify/release the candidate under
existing gates and compare a new affected-device trace; correlate server/provider
evidence if packet-loss origin or readiness endpoint failure must be established.
