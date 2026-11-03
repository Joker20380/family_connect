# Krasnodar supplied diagnostics — 3 November 2026

## Export26 primary journal

Read-only AMS1 journal inspection,3 November. Existing source routing/public111 still
uses primary MESH; secondary activation is a separate workstream. Journal archive
19:39:30–20:18:42UTC covers the attempt; adjacent archive/current file checked too.
Initial SSH timed out; retry succeeded. Default journal JSON omitted large MESSAGEs;
final --all read19:59–20:15 includes long messages with remote allowlist filtering,
no raw logs/provider URLs/user identifiers exported. Final query returned0.

-20:00:40.996 systemd Stopping;20:00:41.189 Stopped;20:01:30.354 Started;
20:01:32.586 bootstrap_seed_ready. Release record separately documents the common
fleet transaction's primary/HTTP stop/start. This inspection caused no restart.
-Client starts20:07:20, uses valid cached material after refresh failure, then fails
SEED_ADMISSION/DEADLINE at20:08:12. Latest20:15 fetch retains cache age1946s, selected
CACHE, directory expiry22:35:43UTC. Export25 already had this directory expiry before
the restart. Age/expiry validity does not prove an old media-room endpoint is live.
-No unit records in20:05–20:08 window; no successful bootstrap_family_open/auth for
this attempt observed. Next bootstrap_family_open20:14:04/auth20:14:09, descriptor
issued20:14:14, then gateway_session_failed20:14:44. Do not attribute that uncorrelated
exchange to this phone; its client history does not report that success.

Strong hypothesis: client cached the pre-restart directory and could not refresh it,
then joined an obsolete bootstrap room without the gateway. Source SeedManager creates
a room on startup, and admission precedes Family authentication. However historical
room bytes were not recovered/compared, and pre-auth OPEN/ACCEPT packet receipts are
not logged per client. Therefore cannot prove whether its OPEN arrived or ACCEPT left,
exclude seed contention/media loss, or call the hypothesis a completed root cause.
No evidence here establishes a HyperOS-specific failure or expired client credentials.

No production writes/restarts, phone changes, builds/publication or acceptance claim.
Public111/catalog6 unchanged; rollback not applicable. Remaining: exact cached-versus-
restart directory correlation and fresh-directory field comparison; resilient recovery
when cryptographically valid cached bootstrap addresses stop serving. Do not reset
identity or weaken signature/expiry/revocation checks. Earlier retry-exhaustion
incidents remain distinct and are not explained by this later restart.

## Export24 server correlation

Separate second API36 phone, beta111, cellular. Read-only RU lookup matched the supplied
Support ID without printing or committing identifiers. Device revoked=0, invitation
revoked=0, no field-support audit rows. No stored online diagnostics snapshot for this
Support ID; this does not distinguish disabled consent, failed delivery or retention.
Support metadata last_seen18:26:27UTC/version60 is not installed-version proof: the
client export explicitly reports111. Two certificate records have expiry20:05:02UTC
and22:35:24UTC; issuance times and receipt on this phone are not established. No explicit
restricted_grants row; eligibility can be derived in all_activated mode, so absence
alone is not an access-denial diagnosis. Effective deployed policy was not read back.

Client18:29:49UTC AUTHORIZATION_REJECTED is followed by four pre-session failures
18:30–18:34UTC. Latest fetch shows cache MISSING, HTTPS CHALLENGE/CONNECT_TLS_WRITE
TIMEOUT without HTTP status, and RNS RELAY_OPEN UNAVAILABLE. No MESH session started.
Current HTTP candidate is active, activation timestamp18:35:46UTC (21:35:46MSK),
after these attempts. That timestamp alone proves neither an overlapping outage nor
the reason for activation. Unit stdout/stderr are null; historical systemd/proxy
evidence must be checked before claiming receipt/nonreceipt of the failing requests.

Initial SSH/database read succeeded. Subsequent banner/command timeouts prevented
historical journal, readiness receipt and effective policy readback. Correlation is
PARTIAL; original authorization rejection and network timeout causes remain open.
No server changes/restarts/permission changes, release or phone actions by this task.
Versions unchanged; rollback not applicable. Retry bounded historical evidence reads
once SSH is available; do not reset device identity or weaken authentication.

## Original export22 analysis

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
