# NL production gateway replacement — 30 October 2026

## Current result — Android107 public source integrated; release qualification pending

Observed 2026-10-31T12:07:52Z. Same NL-REPLACEMENT-20261030 continuation, not a product checkpoint.

**NL-REPLACEMENT-20261030 / READY_FOR_OWNER_NL_SMOKE.**
Owner-executed Sprintbox console checks at11:52UTC confirm the RU host, synchronized clock,
database integrity, unchanged API/SSH processes and real local backend/proxy challenges PASS.
The diagnostic timeout is localized to journalctl, not the challenge endpoint. A bounded
kernel-ring follow-up at11:54UTC covers the last hour: no OOM, storage, conntrack-full or
lockup match. No service restart/reload, host reboot or product configuration change.
Three consecutive samples from each of operator and new NL at11:54–11:55UTC pass SSH,
verified TLS, real challenge and signed device-status; no504. Current control-plane gates
PASS. The earlier intermittent stall's root cause remains NOT_PROVEN, not declared repaired.
Catalog4/signature/new NL endpoint and unchanged RU entry are reconciled read-only at
11:55:13UTC. No republication or sequence5. Owner subsequently reports AWG/internet working;
owner now confirms the HTTPS egress address matches185.10.158.212 and reports Disconnect.
This is owner-reported AWG egress PASS; resource cleanup is not yet verified. TCP/Auto-MESH not run.
The missing NL load percentage is localized: fresh metrics, but the replacement provider's
channel capacity is unverified. Android intentionally displays No data rather than treating
CPU alone as total load. No guessed capacity, source/configuration change or APK update.
Owner authorizes a general MESH-capable Android update: the no-build restriction is lifted,
not the release gates. Candidate107 is built from all2073 hash-verified accepted106 source
members plus three bounded changes: version, quiet notification updates and explicit microphone
permission-denial handling required by lint. All12 native libraries including MESH are unchanged.
219 JVM tests/33 suites and lint PASS;15 source/delta and4 publication tests PASS. APK unsigned,
not installed or published. Owner explicitly accepts Android12+/ARM64 as the general-release
target; Android below12 is unsupported, not a pending compatibility gate. Public-source
integration now preserves the accepted106 Android UI/MESH code with the notification fix.
All376 canonical JVM tests/63 suites and lint PASS;34 focused release/source checks PASS.
CI rebuilds Android JNI from public source with provenance and Codec2 corresponding-source
materials; no gateway rebuild/deployment or unrelated desktop job for this Android-only change.
Hosted platform CI, downloaded artifact qualification, offline signing and owner runtime remain
required before optional publication. The earlier private unsigned candidate is not the release.
Fresh HTTPS/signature readback: public Android beta60/update sequence1, optional policy unchanged.
Gateway catalog4 is separate and unchanged. No server/registry/admission change or mandatory update.
Owner says an older version is quiet; notification regression cause remains unproven without
phone evidence. Panel1000GB is traffic volume, not Mbps. Canary stays PAUSED.

New NL **185.10.158.212** has accepted AWG/TCP and now real production-bound MESH
DNS/HTTPS/egress acceptance. Reused **FLEET_MESH_PROBE_1**; no second identity/invitation,
owner identity, paid event or APK build. Probe retained non-revoked in encrypted custody.

Join cause: **PRE_CONNECT_OPERATOR_CONTROL_MISSING**. The relative operator-control
boundary was absent in the replacement service working directory. Restoring the exact
retained seven-file boundary fixed pre-Connect configuration rejection; gateway source,
binary, trust, signaling and service environment are unchanged. Direct Telemost join PASS,
then the sole full MESH retry PASS: registration, Family TLS, three DNS queries, four
verified HTTPS streams, new NL egress and bounded cleanup. Three stable samples, zero restarts.

Signed catalog **4** was published; initial authenticated NL readback returned the new endpoint,
RU entry and probe assignment remain unchanged. Actual Android catalog parser PASS without
APK update; Android106 owner AWG smoke is **IN_PROGRESS**, not completed by parser
acceptance. Owner-reported HTTPS egress now matches the new NL; cleanup is still unverified.
Prepared routing artifact and mailbox/monitoring target updates are deployed.
Fresh11:55:13UTC readback validates canonical profile/certificate/CRL, floor **27226**,
RU/NL directory equality and actual SSH snapshot. Renewal evaluates NOOP; no material refresh
is needed at that observation. Normal renewal/read-only sync timers are active/waiting,
last workers succeeded, controller COMMITTED and neither node has an active operation owner.
New NL remains active with integrated publisher rotation; no separate publisher timer.
Old NL remains **FENCED**. No rollback/catalog rewrite or RU reboot was attempted.
Paid ledger **0/0**, payments/revenue0, cohort0/10. **BETA-0-CANARY-1 PAUSED**;
paid-canary, subscription events and Android stage0 stay off. Complete the current owner
notification installed-runtime and AWG cleanup checks, then TCP and Auto/MESH once each in this
same operation. No further publication. Not NL_REPLACEMENT_LIVE until all owner gates PASS.

### Android107 canonical release-source integration

Owner explicitly accepts Android12+/ARM64; no older-device compatibility work is required.
The prior private source base is not a published Git commit and the previous client workflow
still built65. It cannot qualify the private107 APK. Accepted106 Android UI, readiness,
recovery, chat JNI and associated tests are now integrated as normal public source, not
a private source capsule. Shared carrier and messenger adaptations are preserved.
Quiet foreground-notification updates and explicit microphone denial handling are retained.
Canonical Friends version107/minSDK31 keeps the same package; provisioning faults remain
disabled. APK signing, distribution and device installation are NOT_RUN.

Local canonical JVM:376 tests/63 suites PASS; lint PASS. Focused Python source, native
provenance, release-delta and publication checks:34 PASS, unrelated Windows check deselected.
Public CI now includes pinned dynamic Codec2 build and corresponding-source export,
source-bound Android JNI verification and APK-only packaging. No gateway binary is built
by this Android release job. Platform selection keeps Android-only changes out of Windows/
Linux jobs; manual/tag release gates still select all platforms.

Next: hosted Android platform result and exact downloaded APK inspection, offline vault
signing, owner in-place/runtime acceptance, then one optional Android updater publication.
The earlier private candidate hash is historical only and will not be relabeled as a CI
artifact. Current public/invitation beta60 and owner106 remain unchanged. Rollback requires
no live action at this source-only point; gateway catalog4, paid0/0 and canary PAUSED persist.

### Android107 general update — local candidate, not published

Recorded 2026-10-31T12:54:27.563759+00:00. Owner authorizes a MESH-capable general update, lifting the earlier
no-build restriction, not signing/CI/runtime gates. No new PLAN ID or top-level operation.
The older-version-is-quiet report is retained. Historical beta60 also lacks only-alert-once;
the omission alone does not prove this runtime regression. Installed verification is pending.

Both live Android discovery routes still agree on beta60/code60. The production manifest
validator passes signature, update sequence1, minimum_supported_version1 and mandatory_after0.
These Android update manifests are separate from gateway catalog4; neither was republished.

All2073 retained106 source hashes PASS. Of152 pinned Android members, the canonical main tree
has94 identical,30 different and28 absent. Derivation therefore uses the exact accepted106
capsule, not an older main build labelled as current MESH. The
[three-file delta](../../tests/fixtures/android_notification_release/beta106-to107.patch)
changes only version, notification alert policy and explicit microphone SecurityException
propagation as IOException. This corrects the sole lint error without suppressing checks.
All12 native libraries remain byte-identical to accepted106; MESH/gateway are not rebuilt.

| Candidate | Verified result |
| --- | --- |
| Version/package/ABI |0.1.18-beta107 / com.familyconnect.app.friends / ARM64 |
| Minimum/target API |31/35; Android12+; older-device compatibility not qualified |
| Artifact |unsigned local APK;56072941 bytes |
| APK SHA256 |b7ed8d09b6c46d303396330decb94622d86f9f0a3cb121502e45a8b4bd7c2e4f |
| Full source inventory SHA256 |85d2028f3a6a5237bdc1956fb05234d0dde93b955e1b7255543c445a8a201bf7 |
| Baseline106 inventory SHA256 |8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c |
| Tests |219 JVM tests/33 suites;15 source/delta and4 publication tests PASS |
| Lint/package checks |PASS; non-debuggable;16KiB APK ZIP alignment PASS |
| Privacy scope |asset-text private-key marker scan PASS, not a complete release audit |
| Hosted CI/signing/install/publication |NOT_RUN / NOT_RUN / NOT_RUN / NOT_RUN |
| Public updater/invitation |beta60 unchanged; optional policy unchanged |
| Owner phone |last accepted106; no ADB device;107 runtime not observed |

The initial local build harness lacked the retained Git baseline context; the provenance
verifier rejected it. Corrected the harness, not the verifier. Corrected an aapt output-label
assertion as well. Neither ordinary error caused production changes or a release-gate waiver.

Remaining: public exact-source/platform CI and artifact qualification; Android8–11 compatibility
or safe delivery policy; offline signing with the existing signer; real106→107 update without
data loss; notification continuity and AWG/TCP/Auto-MESH owner acceptance. No blanket publication
from local build success. Do not widen MESH admission/paid cohort merely by distributing APKs.
Existing readiness/admission rules remain authoritative. No registry/service changes; canary
PAUSED, old NL fenced. Source rollback is a normal revert of the bounded delta; nothing new is
installed, so no live rollback is needed. Preserve all immutable APKs and existing public links.

### Repeated tunnel-on message — source fix qualified, not installed

The owner confirms the address from the requested HTTPS egress check matches the new NL,
then reports turning the tunnel off and asks to fix repeated notifications first. AWG egress
is owner-reported PASS; resource cleanup is not independently verified. TCP/Auto-MESH remain
NOT_RUN. No owner identity or server mutation is needed for this source correction.

Manual health probes update notification ID1 after every result. Successful probes schedule15s;
unsuccessful probes schedule5s after a check bounded at5s. The builder previously lacked
only-alert-once. ConnectionService now sets setOnlyAlertOnce(true), preventing repeat alerts
when the existing foreground notification is updated. It remains ongoing, with live status,
health warnings, open-app and Disconnect controls. The channel remains LOW. Health probes,
transport behavior, retries and real error state are unchanged; chat notifications are untouched.

The regression source-contract test fails on the old builder and passes after the one-line
fix.12 affected Android source-contract checks PASS; the unrelated Windows check is excluded.
These checks do not prove runtime behavior on the owner's phone. No ADB device is available;
notification-channel settings and service restart events were not observed. The reported
10s interval alone does not prove reconnection. Installed notification acceptance is pending.

At this earlier source-only step there was no build/signing/installation. The later owner
authorization and candidate107 build above supersede the no-build restriction, but do not
change the last accepted Android106 installation.
No server restart, identity change, catalog publication or paid operation. Catalog4 is retained,
old NL remains fenced and canary PAUSED. Source rollback is a normal revert of this one-line
change; there is no deployed artifact to roll back. Do not mark NL_REPLACEMENT_LIVE.

The supplied provider panel lists4.84/1000GB under bandwidth: a traffic-volume counter/quota,
not a link-speed measurement in Mbps. Its reset period and any fair-use terms are not proven
by the panel excerpt. No capacity value is inferred; the existing unknown-load display remains.

### Owner AWG report and informational load display — 31 October12:07UTC

Owner reports that AWG/internet works, but server load is missing. This is a partial owner
result, not final client acceptance: current-phone endpoint/HTTPS egress and Disconnect are
still pending; TCP and Auto/MESH have not run. A read-only check of the retained administrative
peer mapping found no handshake for that mapping. It does not attest the currently used
phone identity or prove which endpoint the current session selected. No identity was changed
or enrolled; no client address, key or raw device reference is published.

The load-display cause is proven independently of VPN health. Public HTTPS monitoring returns
fresh RU and NL samples. NL reports CPU/traffic, but capacity_mbps and load_percent are null,
reason capacity-unknown, basis replacement-provider-capacity-unverified. This was an intentional
replacement-host setting, not a stale monitor or missing gateway. The accepted monitor and
Android ServerLoad contract require a known channel capacity before calculating total load;
the UI therefore shows No data. Do not copy the old provider's estimate or substitute CPU
for overall load. Obtain the new NL tariff's channel capacity before changing this setting.
No source/configuration/restart/catalog/APK change was made. Four focused monitor tests PASS,
including unknown-capacity handling. This informational display does not block transport smoke.

Same paid0/0/canary-PAUSED restrictions. Continue with the active AWG session's HTTPS egress
readback, then cleanup and TCP/Auto-MESH once each. Catalog4 remains unchanged.

### Provider-console acceptance — 31 October11:52–11:55UTC

Continuation from main `e3151642b01a7320186c4809aadda1c7808d609f`. Provider console was
opened and commands executed by the owner; no console credentials were collected. RU host
match, NTP, API/SSH active with unchanged processes and zero restarts PASS. Available memory
about923MiB, root free7.58GB, free inodes3.32million; no failed Family Connect unit.
Three other failed units were not modified.

The first console helper hid the failing command behind TimeoutExpired. A private diagnostic-only
correction preserves partial results and safe stage names; timeout/redaction/console-gate tests PASS.
The second console run localized the8.283s timeout to bounded journalctl kernel-log reading.
Read-only database quick_check/foreign_key_check, existing probe binding and paid0/0 PASS.
Actual local backend challenge200 in0.046s and verified-TLS local proxy challenge200 in0.082s.
Monitoring GET also200 but9.565s including setup; it is not substituted for API acceptance.
No product source, gateway, Android, registry, configuration, identity or catalog change.

At11:54:30UTC a separately identified pinned-SSH follow-up read the kernel ring directly,
without journald:0.037s, retained coverage of the last hour,579 messages, no OOM/storage/
conntrack-full/lockup match. This follow-up is not represented as a console execution.
API artifact/argv and isolated proxy config/hash unchanged; proxy config test PASS, zero
restarts/OOM. Three vmstat interval samples:2/1/0% I/O-wait, zero blocked processes,
no swap-out; conntrack443/65536. This does not prove the cause of the historical stall.

Fresh consecutive operator and new-NL samples at11:54:03,11:54:53,11:55:42UTC all PASS:
SSH execution, verified TLS, real existing-probe challenge and signed device-status,
six samples, no504. Maximum SSH3.265s, challenge1.044s including relay overhead,
signed status1.090s. No MESH/gateway-join retry, enrollment or owner identity use.
Console plus external/current-state acceptance is now PASS without service recovery action;
historical failure classification remains RU_INTERMITTENT_UNRESOLVED/root cause NOT_PROVEN.

Read-only11:55:13UTC reconciliation: exact catalog4/signature, new NL185.10.158.212, RU entry
unchanged, no catalog5 or republication. Current canonical profile/certificate/CRL/directory,
CRL/floor27226, RU/NL directory equality and actual SSH snapshot exit0/empty stderr PASS.
Leaf/CRL expire13:32UTC; directory14:23:33UTC. Normal renewal NOOP: no refresh performed.
Normal renewal/read-only sync active/waiting; prior transaction COMMITTED, both owners absent,
integrated publisher active, legacy sync disabled. New NL critical units and exact gateway
unchanged, zero restarts. Old NL accepted fencing retained, probe non-revoked, paid0/0,
canary PAUSED. Temporary console helper removed after hash-guarded readback; private evidence
retained. No temporary SSH/write credential was created.

**Remaining gate:** owner Android106 AWG once, Disconnect cleanup; TCP once, cleanup;
Auto/MESH once with current readiness import/ACK, DNS/HTTPS/NL egress, cleanup. No owner
test is inferred from server acceptance. Keep catalog4 unchanged and normal monitoring active.

### Historical RU read-only reconciliation — 31 October11:20–11:27UTC

Continuation from main `26b347c2673af89c4f04704d2334485ddd947cce`. No product source,
binary, host configuration, service restart/reload, reboot, catalog, identity or invitation
change. Real challenge/device-status checks reuse FLEET_MESH_PROBE_1; only the existing
API's short-lived challenge records are exercised, not registry/device/grant mutation.

- Provider web/serial/VNC console: **UNAVAILABLE_TO_SESSION / NOT_RUN**. No provider access
  credential was found in the selected retained receipts; no provider identity is guessed.
  Host and localhost observations below use strict pinned SSH, not a claimed console session.
- At11:20UTC both external origins reached TCP22/443/8443 and SSH banner. Verified product
  HTTPS is on8443;443 belongs to the pre-existing VPN transport, not the API. Its generic
  IP-certificate TLS probe failed verification, so it is not counted as an API TLS failure.
- RU localhost at11:23UTC: static monitoring200, direct backend challenge and proxied
  challenge each exceeded the5s bound. Concurrent vmstat samples showed81/96/85% I/O-wait,
  active swap I/O and5 blocked processes. This is a real local symptom, not proof of a
  provider-only block, corrupt database, OOM, leaking process or specific resource limit.
- API artifact remains `44a6b50f1a1ce00fd74f53e0d35c5937c6b5f5c2a561fc94b7a0150f39149204`;
  same PID, NRestarts0,5 descriptors, no memory/pid-limit or OOM event. Exact isolated
  proxy configuration validates; proxy restart count0. No matching failure in inspected
  bounded proxy/API logs; absence of a log entry does not explain the earlier504.
- Database read-only quick_check and foreign_key_check PASS. Registry counts unchanged:
  57 devices,111 invites,2 restricted grants; paid subscriptions/events0/0. Root filesystem
  75% used, inodes9%; clock synchronized, no OOM/storage/kernel/conntrack-full error found
  in the bounded kernel window. Conntrack870/65536. No firewall/conntrack flush.
- Three consecutive samples per external origin at11:23:33,11:24:22,11:25:10UTC PASS:
  SSH command, trusted TLS, real challenge and signature-authenticated device-status.
  Six samples total; no504; longest SSH1.857s and challenge round trip1.072s, including
  relay overhead for the NL source. NL-origin SSH uses a local-key ProxyCommand; private
  keys remain on the operator workstation, no agent forwarding or key copy to NL.
- Subsequent bounded I/O sampling fell to1.0–3.8% I/O-wait; API rejected malformed requests
  promptly as expected. At11:27:20–11:27:24UTC both direct localhost backend and local proxy
  passed actual challenge plus signed device-status; maximum individual local HTTP time
  0.115s. These successful windows do not prove the intermittent fault cannot recur.

Read-only reconciliation at11:26:56UTC: exact catalog4 SHA256
`214cb6a3611b5c05117dd2ddfbfbb2f8add0603c680368a9299b34cd28214922`, signature PASS,
NL185.10.158.212 and RU entry unchanged. No catalog write or publication. Actual RU→new-NL
forced SSH snapshot exit0/no stderr, strict schema/profile/certificate/CRL/directory PASS,
CRL/floor27226, RU/NL directory equality. Leaf/CRL expire13:32UTC; directory14:23:33UTC;
renewal NOOP, no refresh performed. Normal renewal and read-only sync timers active/waiting,
last workers success, controller COMMITTED, no active node owners. New NL accepted binary
and critical services remain active with0 restarts; no gateway-join or MESH probe repeated.
Old NL fencing and paid/canary restrictions remain unchanged.

At this earlier observation the remaining gate was `RU_INTERMITTENT_UNRESOLVED` and
provider-console execution was pending. The subsequent console and current-state acceptance
above supersedes that access gate, not the unresolved historical root cause. Owner smoke
was NOT_RUN; no recovery or rollback action was applied.

### Diagnosis and smallest proven fix

Retained failed evidence was inspected before any new live attempt: no ROOM_RESOLVED,
SIGNALING_CONNECTED, initial-hello, SERVER_HELLO or CARRIER evidence. Exact retained starter
source revealed an earlier pre-Connect configuration check; therefore the original
Connect-only boundary was incomplete. An operator-only harness reproduced
`mux_profile_configuration` with zero network calls and zero room creations. The selector
is relative to the service working directory; the replacement lacked its seven-file
root-controlled operator boundary. Read-only export from the still-fenced old node recovered
exact bytes; modes/boundary restored, no broad old-host configuration clone or policy change.
The repaired local preflight reached the intended invalid-room sentinel, still without
network or room creation. No product source changed and no gateway rebuild occurred.

Accepted gateway remains SHA256
`f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`.
Retained source capsule inventory SHA256
`27b54a9dd167c3b6af639bb03864f4d7d121c0e8b96c90eccb45a198c936f117`.
Restored control inventory SHA256
`265498d55e01c267815de9c08d44b735fda41decfd6216f279f2f61691664679`.
Private diagnostic harness includes eight safe-reason/redaction/cause-preservation cases,
all PASS. Its binary SHA256 is
`d7721526339b70c5dca107f9796aa8610409804389cec98e8973e594fc1b0829`;
this is an operator diagnostic, not a replacement production artifact.

### Direct join and one full retry

Exactly one diagnostic room was created through the accepted provider. Exact Go REST
transport: A/AAAA both resolve, selected IPv4, verified TLS/HTTP200 and required fields PASS.
Media TCP/TLS selected IPv4 PASS; exact Origin WebSocket handshake101 PASS. Local peer/VP8
setup, initial hello, SERVER_HELLO, ICE and pub/sub connection PASS; carrier ready in1617ms.
No proxy, CA, time, IPv6 route or provider egress defect was found. No speculative UA,
capabilities, signaling, Family TLS or forwarding edits. Diagnostic session/unit closed and
private evidence archived; no retained diagnostic listener or temporary credential.

Current materials had sufficient headroom: no additional renewal operation in this
continuation. One exact gateway start produced a fresh normal publisher generation, then
accepted read-only sync copied it to RU. Probe readiness challenge/fetch, native validation,
import and durable ACK/readback PASS using the same identity and current certificate.
The sole full MESH retry completed2026-10-31T10:24:51Z with exit0/empty stderr:
bootstrap auth → dedicated room → gateway join → descriptor → registration/Family TLS →
three DNS queries, four HTTPS streams with end-site TLS verification and exact new NL egress.
No owner identity used. Local process/interface cleanup PASS. Server release completed
20.7s after client exit through bounded reliable-frame exhaustion; later close/FAILED labels
are teardown evidence, not an in-flight data-plane failure. All broker cleanup completed;
no retained dedicated session or TUN. Probe is non-revoked, invitation exhausted; encrypted
custody/readback PASS and last-success timestamp retained for fleet reuse.

Three bounded post-MESH samples: stable gateway/ordinary-service PIDs, NRestarts0, no abnormal
memory increase, OOM or kernel/storage errors. Canonical certificate/CRL expire
2026-10-31T13:32:00Z at this observation; CRL/floor27226. Directory issued
2026-10-31T10:23:35.872977678Z, expires2026-10-31T14:23:33.874307291Z, SHA256
`77c55687463798ddce5257d7adf9c6df9245524a07e61eff9a2a6902eb55acf4`.
Actual post-publication SSH snapshot exit0/empty stderr, strict schema/signatures and RU/NL
directory equality PASS; normal renewal NOOP and prior transaction COMMITTED/no active owner.
Normal renewal15min and read-only directory sync30s schedules active/waiting. Publisher
uses accepted integrated3h rotation/4h lifetime, not a separate timer. Legacy credential-only
timer was briefly included in schedule activation, but its existing condition prevented
any service execution; it is now inactive/disabled. No legacy write or old-node contact.

### Cutover and remaining owner gate

Fresh encrypted RU application/infrastructure backup:54/40 files, six SQLite checks PASS;
separate current route/artifact/unit metadata encrypted backup and authenticated readback.
Previously qualified endpoint-routing HTTP artifact is now installed:47368bytes, SHA256
`44a6b50f1a1ce00fd74f53e0d35c5937c6b5f5c2a561fc94b7a0150f39149204`.
It supersedes the47091byte active artifact only for this accepted route deployment; only
catalog-driven registration and chat-sync members differ. Original artifact/drop-ins kept
for rollback. New NL SSH pin verified; actual forced registration using the existing fleet
probe PASS. Mailbox bootstrap/ACK preserves its public identity; chat sync PASS. Monitoring
now observes the new NL, with fresh RU/NL samples; old NL remains quarantined, not zero users.

One offline signed, atomic, monotonic catalog publication **3→4**:
`214cb6a3611b5c05117dd2ddfbfbb2f8add0603c680368a9299b34cd28214922`.
Python signature/schema and actual Android Java parser PASS; no APK build/update. Real
authenticated HTTPS configuration readbacks PASS for NL and RU. NL selects185.10.158.212;
RU gateway entry/assignment unchanged, signing key/schema/AWG public-key/TCP credential
contracts unchanged. Ordinary provisioning reuses the one fleet identity/transport key;
no new device/invite or paid record. Android106 itself has not yet been exercised.

AWG/TCP prior synthetic data-plane acceptance retained; current services active. Current
Restricted/MESH server acceptance PASS; owner AWG/TCP/Auto-MESH all NOT_RUN. The late RU
availability failure below must be resolved before the owner smoke prompt.
Do not call this NL_REPLACEMENT_LIVE yet. If published NL fails before owner PASS, stop
failed NL admission via the supported catalog fallback; do not re-enable the old server
or restore the old RU database. No rollback invoked; catalog publication itself was verified.

### Historical late external availability blocker — superseded by RU readback above

After catalog4 publication/initial authenticated readback and successful actual snapshot,
the final administrative verification encountered RU SSH banner timeouts. Public monitoring
still returned fresh RU/NL samples at10:44:34/10:44:36UTC (RU CPU17.3%, NL8.8%); the next
public HTTPS check stalled in TLS, then TCP connection establishment timed out. Independent
checks from the new NL also time out to RU SSH/public HTTPS. A later monitoring GET and
SSH echo intermittently returned, but the real authenticated challenge returned HTTP504,
and a120s full SSH verification did not complete. A static monitoring response alone is not
API acceptance. This is not a Telemost join regression; the affected network/host hop is unproven. No provider blame, OOM or
application cause is inferred. No RU reboot, firewall change or neighbouring-service action.

At that observation the stop was **CONTROL_PLANE_READBACK_UNAVAILABLE**. Already published catalog4 and its
initial PASS receipts are retained, not blindly republished or claimed rolled back. Latest
RU schedules/ledger/journal cannot be freshly queried during the outage; their last accepted
values remain explicitly time-bounded. New NL services/probe custody stay intact and old NL
stays fenced. No owner smoke prompt until RU reachability, current catalog/materials and
schedules are re-read. If rollback becomes required, regain the accepted control route and
verify it; do not reactivate the old NL or invent a successful rollback.

Focused route/catalog checks53 PASS; HTTP/evidence checks40 PASS/14 optional prerequisites
skipped; exact retained HTTP candidate additionally17 PASS/14 identical optional skips.
Skipped matrix requires native nginx or a separate pinned sync artifact; nginx and that
artifact were not changed, and real public dispatch/SSH snapshot were separately verified.
Strict JSON, private-value/secret scan, Markdown links, isolated staged scope and whitespace
checks apply to this checkpoint. No Android/desktop build or historical full suite.

## Historical first fleet attempt — gateway join failed, superseded

Observed 2026-10-31T09:50:12.264119+00:00. Continuation of the same operation; no new product checkpoint.

**NL-REPLACEMENT-20261030 / BLOCKED_NL_REPLACEMENT / MESH_DATA_PLANE_FAILED.**
The owner-authorized permanent **FLEET_MESH_PROBE_1** now exists and is retained for reuse;
the prior missing-test-identity blocker is resolved. Exactly one production device and one
one-use invitation were created through the accepted enrollment path. Device/transport
binding, invitation consumption exactly1, real readiness challenge/fetch, native signature
validation/import and durable ACK/readback PASS. No owner/tester identity was used.

Expired materials were refreshed without source changes: the already accepted bounded
publisher worker supplied the prerequisite directory, followed by one normal renewal
**COMMITTED** with no first cause. Current-at-readback certificate/CRL and floor are
**27226/27226**; actual RU→new-NL SSH snapshot, synchronized directory and renewal NOOP PASS.
Historical rollback remains ABORTED and its registry additions remain preserved.

One real MESH attempt reached authenticated bootstrap and dedicated room creation, but
failed at **GATEWAY_JOIN**: broker `gateway_failed`, exchange stage `create`; the client
reported `bootstrap_protocol_rejected`. Dedicated READY/registration was not reached;
DNS/HTTPS/NL-egress were NOT_RUN, not PASS. The lower-level join cause is not yet localized.
Broker CLEANUP/COMPLETED and local process/interface cleanup PASS; no automatic retry or
second identity. Probe remains non-revoked in encrypted private custody; invite exhausted.

Safe hold: old NL FENCED; new185.10.158.212 ordinary AWG/TCP remain active with earlier
accepted data-plane evidence. Restricted gateway and integrated publisher were stopped
after the failed attempt; three pre-stop samples had stable PID/zero restarts and no
abnormal memory growth. Renewal/read-only sync timers remain paused. RU ordinary HTTP and
trusted public HTTPS dispatch remain healthy with the original artifact. Catalog3 is
byte-identical: no endpoint publication, APK change or owner smoke. Paid ledger0/0,
payments/revenue0, cohort0/10. Leaf/CRL expire2026-10-31T13:32:00Z; directory expires
2026-10-31T13:33:33.753314361Z. These are bounded observations, not scheduled freshness or
running MESH acceptance. **BETA-0-CANARY-1 stays PAUSED; paid-canary, subscription events
and Android stage0 stay off.**

### Permanent probe enrollment and custody

- Safe label: `FLEET_MESH_PROBE_1`; safe device reference: `fleet-646b53465a60`.
- Public identity fingerprint SHA256: `30b63836c67b99bff6578933db9055d17a272c4abe74a6f6ea38375e3729acad`.
- Transport public-key fingerprint SHA256: `0fcffb830108afcc970c0121d563ca97c79d1815cdcc9023668f9d0dfac29565`.
- Created `2026-10-31T09:37:22.332482+00:00` through the existing production device-identity
  implementation on the operator workstation; exactly one identity and transport key.
  Private keys never sent to RU/NL. Private parent0700/files0600, no symlinks/hardlinks;
  authenticated encrypted backup/readback PASS before enrollment and after retention.
- Existing operator invitation API, actual HTTPS challenge/proof and enrollment PASS.
  One device/one invitation added; device and transport binding PASS. Invitation use count1,
  exhausted; not revoked because the accepted contract couples invite/device revocation.
- Existing non-paid `all_activated` v2 authorization applies; no additional restricted-grant
  row is required. No new validity model or migration. The schema has neither purpose nor
  invitation-expiry fields: private purpose mapping is `internal_fleet_probe`, and enrollment
  consumed the one-use invitation within the900-second operator window. The accepted v2
  authorization has no finite expiry field; certificate lifetime remains bounded by the
  current authority/profile, rather than inventing a30-day grant.
- Registry delta: devices+1, invites+1, restricted grants+0. Paid subscriptions/events0/0,
  payments/revenue0, paid cohort0/10. No referral, owner binding or user Android identity.
- Actual readiness challenge/fetch, native production-trust validation/import, issuance of
  one current probe certificate, ACK and durable receipt readback PASS. No owner identity.
  The retained identity is non-revoked; no successful MESH timestamp is asserted.

### Material refresh and exact artifacts

The previous leaf/CRL had expired at02:47:21Z. Fresh readback rejected them as current;
historical signature/binding validation remained intact. Normal publisher startup cannot
consume that expired predecessor, so the already accepted bounded fixed-configuration
recovery worker supplied the prerequisite directory. No new source correction, weakened
validator, edited timestamps or new trust anchor. One recovery room READY and one atomic
recovery promotion; normal integrated publisher then produced its own startup generation.

- Recovery predecessor directory SHA256: `31ce04ac75168db1119bc299bd8bd4736c79232ae1fa799d448ac18edfa0f77a`.
- Recovery fresh directory SHA256: `d9e2a1e1c1fecf5d117ea98f26cdf854d7674475748d421a19cf061fdbe5ea46`.
  Issued `2026-10-31T09:27:47.254745431Z`; expires `2026-10-31T13:27:47.254745431Z`.
  Staging/live production directory validators, contract/metadata and unchanged profile PASS.
- One normal renewal operation, safe label `FLEET_NL_NORMAL_RENEWAL_1`: **COMMITTED**,
  `commit_decided=true`, `first_cause=null`, both node owners cleaned. CRL/floor27226;
  current profile/certificate/CRL signatures PASS at readback, leaf/CRL expire13:32:00Z.
- Normal directory SHA256: `f852f050dbfd9a9553fe0d41dc5e829bfc61ec484147d989ff288b9fc851b6c2`; issued
  `2026-10-31T09:33:35.793261965Z`, expires `2026-10-31T13:33:33.753314361Z`.
  RU/NL exact directory equality PASS. Actual forced-command snapshot exit0/empty stderr,
  strict schema/current material and non-mutating renewal NOOP PASS even after safe stop.
- Existing renewal package unchanged: `2624c1ba1f49863f767ca9e9ea165a5c74c0c4f95a5ba84d2cac1d91d81d5dd1`.
  Publisher recovery package unchanged: `7904fc9e457f74c414e85ac665622a49c9cf5c353affffee1fca301cea59024c`.
  Running gateway hash verified: `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`.
  Recovery configuration archived/disabled again; no active temporary write credential.

### Actual MESH attempt and safe rollback

One production-bound probe attempt: bootstrap cache/current material loaded, Telemost
bootstrap connection and family authentication PASS on both sides. Server trace reached
AUTHORIZED → ROOM_CREATION/ESTABLISHED → GATEWAY_JOIN/STARTED → GATEWAY_JOIN/FAILED
(`RECOVERY_JOIN_FAILED`, broker `gateway_failed`). Exchange rejection: stage `create`.
Client exited1 with `bootstrap_protocol_rejected` after136seconds; it did not reach a
dedicated descriptor/READY/registration. The provider room was created, but gateway join
failed. This is a real acceptance failure, not a missing identity or a READY-only pass;
the evidence does not identify the lower-level Telemost/network/configuration cause.

Four intended HTTPS streams, DNS queries and TLS-verified egress check were not reached.
Server trace CLEANUP/COMPLETED PASS; client process exited, no TUN was created and local
interfaces were unchanged. Restricted service was stopped after evidence capture; process
cgroup empty. Integrated publisher stopped with it. Three pre-stop samples: stable PID,
zero restarts, memory20,619,264 →20,332,544 →20,262,912bytes. No further MESH attempt made.

Private operator-only harnesses were built from the exact retained282-member source capsule
with a TLS-verified egress assertion; no production or Android artifact was rebuilt.
Harness fingerprints: native import `2ba0f671043f491124c1508d150f7a5ab127e676d6d8e0c80977d0a3309dbac5`;
MESH probe `344db2c25d978473a096f70e83d23fe8a9ee618f4ac1951e330bfc9fee0b5a02`;
source inventory `9f3340d6a69af54759433e2196373270b4c5f78cc39461c8f6f374945d1a7a19`.
Local helper import/API fixture mistakes were corrected before the affected action;
they did not cause a second enrollment, renewal, gateway start or MESH attempt.

Probe private custody retained and encrypted/readback-verified after disconnect; invitation
exhausted, device non-revoked, no active session. Reuse this identity for subsequent checks.
Old NL fencing freshly verified: eight product units inactive, persistent quarantine,
product listeners/interfaces absent. New ordinary AWG/TCP and RU original HTTP stay active.
Catalog3 byte-identical, routing artifact not deployed, RU endpoint unchanged. No client
publication or owner smoke; no automatic return to old NL. Monitoring inventory cutover and
publisher/renewal/read-only sync schedule activation remain gated by real MESH acceptance.

Next action is dedicated gateway join diagnosis from retained private evidence, not another
identity or catalog publication. Revalidate clock/freshness before any later reader start.
The failure hold intentionally does not claim ongoing material freshness after the recorded
expiry; all restricted readers and refresh schedules remain stopped/paused.

### Verification scope for this continuation

Production enrollment/readiness/ACK, current snapshot/renewal, exact artifact checks,
authenticated encrypted custody and cleanup checks PASS. Actual MESH data-plane FAIL at
gateway join; DNS/HTTPS/egress and owner smoke NOT_RUN. Documentation uses strict JSON,
targeted privacy/secret scan, Markdown-link checks, isolated staging and whitespace checks;
unrelated local work remains excluded. No Android/desktop/full historical suite.

## Historical 30 October result — superseded by the current probe attempt

Observed 2026-10-30T23:10:37+00:00. Same existing operation; no new product checkpoint.

**NL-REPLACEMENT-20261030 / BLOCKED_NL_REPLACEMENT / RESTRICTED_TEST_IDENTITY_UNAVAILABLE.**
The historical rollback is terminal **ABORTED / ROLLED_BACK_READERS_STOPPED** with
`first_cause=DIRECTORY_INVALID` and separate `terminal_reason=PREVIOUS_LEAF_EXPIRED`.
Two device and two invite additions are preserved; historical expected hashes and restricted
state remain exact under the dedicated overlay contract. Both complete archives/ledgers
PASS, old active owners removed. No old database restoration or expired reader resume.

The bounded publisher recovery created one fresh room (READY PASS), staged and published
one directory through the accepted atomic store. Strict production directory/DirectoryPort
validation PASS. One fresh renewal operation is now **COMMITTED**, CRL/floor **27225/27225**,
current profile/certificate/CRL and synchronized RU/NL directory. Its initial
`NEW_DIRECTORY_NOT_READY` was resolved by the authorized normal gateway start and explicit
committed recovery of the same operation; no additional transaction or manual journal edits.
Actual RU→new-NL forced-command snapshot exits0 with empty stderr; strict schema/signatures
and non-mutating renewal NOOP PASS. Normal publisher produced its own fresh generation.

Remaining real acceptance blocker: no permitted production-bound synthetic MESH identity
was found.98 scoped disposable profiles use independent trust, and four previously recorded
custody locations remain absent. This is not an exhaustive claim about all database users.
No owner/tester identity was substituted, no new client key/identity/grant was generated.
MESH registration/DNS/HTTPS/egress therefore remain NOT_RUN; no catalog publication or
Android106/owner smoke. An existing authorized synthetic identity is required to continue;
creating one would require an explicit exception to the owner's no-new-identities rule.

Safe hold: old NL FENCED; new185.10.158.212 AWG/TCP remain active with accepted synthetic
data-plane evidence. Restricted gateway passed three stable samples/zero restarts, then
was stopped because data-plane acceptance is incomplete. Its integrated publisher is also
stopped; recovery entrypoint disabled and archived. Renewal/read-only sync definitions now
use the accepted package and pinned new-host route; actual read-only sync PASS, timers stay
paused at the acceptance gate. RU ordinary HTTP/public trusted HTTPS healthy, catalog3
unchanged, paid ledger0/0. Current leaf/CRL expire2026-10-31T02:47:21Z: revalidate freshness
before continuation and never start expired readers. **BETA-0-CANARY-1 stays PAUSED;
paid-canary, subscription events and Android stage0 stay off.**

### Source, artifacts and verification

- Registry-overlay source: `e822b391a43dd4cec5949df7a8a33ba6e44872a5`, pushed/remote verified;
  deployed renewal package SHA256 `2624c1ba1f49863f767ca9e9ea165a5c74c0c4f95a5ba84d2cac1d91d81d5dd1`,66287bytes.
 231 focused tests PASS/one optional native interoperability skip; source/member manifests,
  two identical builds,13 imports/four help commands and canonical-route construction PASS.
- Publisher recovery source: `a11eb8f2614ed7dff85522c437c54862daedaf74`, pushed/remote verified;
  package SHA256 `7904fc9e457f74c414e85ac665622a49c9cf5c353affffee1fca301cea59024c`,8700919bytes/4members.
  Helper binary SHA256 `f44ace11d7013cdf2908e888a5ed6175a936970ab9c9195ddf9846d77f587995`,16342590bytes;
  source inventory SHA256 `526a5a9884e115cd78bc7d414cd241f4b876bafdccec933d8c53f628eb47c0e6`.
  The retained282-member source capsule is exact; seven narrowly projected/added members.
  Two byte-identical builds, manifest/member metadata/hashes, help and privacy scan PASS.
  Gateway binary remains exact `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`.
- Publisher tests:113 current-tree and119 exact-capsule Go tests PASS;181 focused Python
  directory/sync/profile-store tests PASS,29 optional integration prerequisites skipped;
  two bounded source-projection tests PASS. No Android/desktop/full historical suite.
- Fresh authenticated encrypted backups/readback PASS for controller/node journals,
  SQLite/schema/integrity, profile/Locator, publisher metadata/configuration and final routes.
  Protected private records retain full provenance; no material contents enter this report.

### Publisher and fresh renewal result

Recovery directory: old SHA256 `e0c1674381f910b6133d9ce295a01784f47487a437a3ad993e1e3be57a4ba53c`;
fresh SHA256 `101524bb996a39716bde2a9fef2c6c32e94675e7a81c13ec5f3eff560b8f7a90`.
Issued `2026-10-30T22:40:46.140928387Z`, expires `2026-10-31T02:40:46.140928387Z`.
Exactly one recovery room creation and one recovery live promotion; real room READY PASS,
staging left live bytes unchanged, publisher contract/parent/ownership/mode preserved.
Profile/CRL/floor unchanged by this worker. Normal runtime then generated a separate directory:
SHA256 `31ce04ac75168db1119bc299bd8bd4736c79232ae1fa799d448ac18edfa0f77a`, issued `2026-10-30T22:52:38.661449239Z`,
expires `2026-10-31T02:52:36.127149321Z`. This is normal publisher startup, not a second
recovery publication. RU/NL copies are equal through the accepted renewal/read-only sync path.

Historical operation safe label `HISTORICAL_NL_REPLACEMENT_ROLLBACK` remains ABORTED;
original cause and complete archives are retained. Fresh operation safe label
`FRESH_NL_RENEWAL_1` is COMMITTED, with both cleanup ledgers and no active owners.
Its first cause `NEW_DIRECTORY_NOT_READY` is preserved: the original service snapshot was
inactive, so normal resume did not start the publisher. After strict current candidate and
two-node commit reconciliation, one authorized gateway start generated a fresh directory;
explicit committed recovery finished that same transaction. No commit-decision reversal.
The historical terminalization HTTP outage was122.44s. The separate fresh-renewal maintenance
outage was387.23s; RU HTTP is restored with original exact artifact/argv.

Actual forced-account SSH snapshot: exit0, stderr empty, schema/signatures/current certificate
and CRL/floor PASS. Non-mutating renewal evaluation NOOP. The ordinary registry additions and
all pre-renewal device/invite rows remain present. Paid subscriptions/events0/0.
Schedule definitions/source pins/new-NL route aligned, but timers not resumed. A bounded
read-only directory sync service run PASS. Its initial protected-home known-hosts path issue
was corrected by copying the exact already-pinned host entry into the root-controlled runtime
boundary; StrictHostKeyChecking and systemd ProtectHome remain enabled. No trust relaxation.

### Acceptance hold and remaining work

One restricted gateway start, three stable PID/memory samples,0 restarts/OOM/storage errors,
current profile and healthy directory were observed. These are not MESH data-plane acceptance.
No allowed production-bound synthetic credential was located in scoped retained material;
independent-trust fixtures are not a substitute. No owner/tester private identity was used.
Restricted was stopped once for safe pre-publication hold; normal publisher stops with it.
The one-shot recovery permit is archived/disabled. Ordinary AWG/TCP and load monitoring stay
active. Old NL remains persistently fenced; unavailable old-node metrics are not zero users.

Catalog sequence3 and RU configuration remain unchanged; endpoint-routing source is still
NOT_DEPLOYED, normal client publication/Android106/owner smoke NOT_RUN. Full NL acceptance
and READY_FOR_OWNER_NL_SMOKE are not claimed. Continue only after resolving the synthetic
identity prerequisite and revalidating material freshness; then actual MESH data-plane,
normal schedules, monotonic client publication and owner smoke. No new checkpoint is needed.
Rollback status: PRE_PUBLICATION_SAFE_HOLD; no old-NL reactivation, no database restoration,
no identity conflict, no temporary write credential and no pending renewal operation.

## Earlier observations — superseded by the current result

## Confirmed terminal rollback and publisher continuation

The existing rollback is now terminal **ABORTED / ROLLED_BACK_READERS_STOPPED**.
Source `e822b391a43dd4cec5949df7a8a33ba6e44872a5` and its deterministic renewal package
were deployed through the recovery-only bridge. Fresh quiesced proof preserved two device
and two invite additions, all historical rows and exact restricted tables. Historical
expected hashes and `first_cause=DIRECTORY_INVALID` are unchanged; terminal reason is
`PREVIOUS_LEAF_EXPIRED`, with no commit decision or expired reader resume. Both node owners
were released only after complete archive and `CLEANED_FENCED_ROLLBACK` ledger verification.
The single RU HTTP stop/start lasted122.44s; ordinary HTTP/public trusted HTTPS are restored
with the original artifact/argv and all registrations retained. Paid ledger remains0/0.

Next within **NL-REPLACEMENT-20261030**: bounded publisher recovery, one fresh renewal,
actual restricted/snapshot/MESH acceptance, schedules and monotonic client publication.
The integrated publisher has no one-shot command and rejects the expired predecessor before
room creation. A narrowly scoped fixed-configuration recovery worker is therefore qualified
from the exact retained publisher source; no gateway binary rebuild or validator weakening.
It checks historical signatures/binding and the exact publisher contract, journals one room
attempt, verifies READY, stages privately and uses the existing locked atomic store.
It never writes profile/CRL/floor and never starts expired readers. Recovery is unavailable
once its fixed permit expires or normal current material is restored.

New NL185.10.158.212 ordinary AWG/TCP server data-plane remains accepted; old NL is FENCED.
Restricted gateway inactive, renewal paused, stale directory retained. No room generation,
directory publication, fresh renewal, client catalog change or owner smoke yet. Catalog3.
**BETA-0-CANARY-1 remains PAUSED; paid events and Android stage0 remain off.**

Renewal package SHA256 `2624c1ba1f49863f767ca9e9ea165a5c74c0c4f95a5ba84d2cac1d91d81d5dd1`,
66287bytes/17members; two byte-identical builds, exact source/member inventory,13 imports,
four help commands and canonical-route construction PASS.231 focused Python tests PASS,
one optional native interoperability skip. Fresh authenticated encrypted backups/readback
PASS before deployment, during writer quiescence and after terminalization.
Historical rollback is labeled `HISTORICAL_NL_REPLACEMENT_ROLLBACK`; its private ID and
complete controller/node journals are retained privately, not published. The controller
transaction remains available as ABORTED; no database/profile/directory writes occurred.

Publisher recovery source qualification is separate from production execution. The exact
282-member retained capsule is verified; only the atomic-store extraction and six bounded
recovery source/test members are projected. Normal publisher logic is unchanged.
Focused publisher checks:113 current-tree and119 exact-capsule Go tests PASS;
181 directory/sync/profile-store Python tests PASS,29 optional integration prerequisites
skipped; two bounded source-projection tests PASS. No Android/client/full-history suites.
Production helper deployment, fresh room/publication and fresh renewal are pending.

## Historical source qualification and blocker evidence — superseded

The following entries describe earlier states, not the current operation gate.

## Append-only registry correction — same operation

The owner authorized retaining strictly proven device/invite additions without rewriting
the historical database snapshot or any expected-state hash. The new narrow RU
`rollback-registry-overlay` RPC validates schema, integrity, foreign keys, unique identities,
application bindings, unchanged historical rows and exact restricted security tables.
Only safe hashes/counts enter its immutable private receipt. Later drift is rejected.
Normal previous-readback, rollback and grant application retain exact-state comparisons.

Explicit fenced recovery binds the historical and live database hashes and overlay receipt,
archives the complete evidence and returns `ROLLED_BACK_READERS_STOPPED` with controller
state `ABORTED`. It preserves `first_cause=DIRECTORY_INVALID`, never writes the database,
never publishes a directory and never resumes expired readers. A recovery-only source
bridge verifies both retained and replacement source inventories without changing the fixed
node configuration included in historical state. Ordinary/scheduled entrypoints cannot use
the overlay. Production deployment and recovery execution are not yet performed.

Focused qualification:231 tests PASS, one optional native interoperability probe skipped.
This includes overlay rejection/replay, cleanup fault injection, explicit CLI gates,
unchanged ordinary recovery, package inventory and canonical-route construction with
both retained/current source tamper rejection. No unrelated client/build suite was run.

The retained authenticated encrypted SQLite backup and live accepted schema match for all
five projected tables. Read-only entry audit reconfirms two device and two invite additions,
no removals, exact restricted tables, unchanged coordinator journal, NL exact rollback and
RU ordinary HTTP active. Counts are observations, not hard-coded acceptance requirements.
Next: qualify the deterministic renewal-only package, fresh backup/quiescence, terminalize
the existing operation, restore ordinary HTTP, then continue publisher/fresh renewal and
cutover. The earlier blocker evidence below remains historical, not a new operation.

## Status and authorization

**NL-REPLACEMENT-20261030 / BLOCKED_NL_REPLACEMENT / BLOCKED_RENEWAL_JOURNAL_UNRESOLVED.**
The owner-authorized fenced-rollback source correction is qualified but **NOT_DEPLOYED**.
Fresh read-only verification supersedes the earlier two-node rollback PASS: RU now returns
`ROLLBACK_READBACK_MISMATCH`; NL still returns `PREVIOUS_SNAPSHOT_RESTORED`.
Only RU `database_sha256` differs from its recorded expected state. Relative to the
rollback snapshot, the current registry contains two additional device rows and two
additional invite rows, with no removed rows. Restricted grants, certificates and CRL
sequence rows are unchanged. The recorded previous database hash is internally consistent.
The RU ordinary HTTP reader is active and belongs to the renewal barrier; therefore the
claim that both barriers are stopped is also no longer true. No records were deleted,
expected hashes rewritten or services stopped to manufacture an exact rollback proof.
The existing journal remains `RECOVERY_REQUIRED`, `first_cause=DIRECTORY_INVALID`,
`commit_decided=false`. Recovery execution and package deployment are **NOT_RUN**.
This is a genuine live-state conflict, not another leaf-validation exception.
Restricted services remain inactive/quiesced and renewal is paused. Old NL is FENCED.
New ordinary AWG/TCP synthetic data-plane and cleanup PASS, but no client publication,
Android106 endpoint verification or owner smoke. This is not full server acceptance.

## Fenced rollback correction — source only

Entry local/remote main: `c6e1f725a638c0a3f416712ffeed3b381d0067cd`.
This continues the same operation; no new PLAN ID or product checkpoint.

- The controller distinguishes verified rollback, current-valid predecessor and resumed
  readers. Only the exact `LEAF_EXPIRED_OR_FUTURE` exception, with a historically valid
  and demonstrably expired leaf, permits fenced finalization. Future material and other
  validation failures remain fail-closed. Normal valid rollback, committed recovery and
  expired-authority rollforward retain their existing paths.
- The new `finalize-fenced-rollback` RPC binds the existing operation, expected state and
  controller recovery evidence. It requires stopped barriers, exact readbacks and no start
  intent, reconciliation or directory publication. It writes only a private terminal receipt
  and node owner state `ABORTED_FENCED`; it never restores material or resumes readers.
- Cleanup archives the complete node journal, terminal receipt and owner/first-cause
  evidence, then durably records `CLEANED_FENCED_ROLLBACK` before releasing ownership.
  Replay verifies the archive and stopped barrier. Partial finalization/cleanup is resumable
  without a second rollback or reader start.
- The controller remains available as `ABORTED`, with external result
  `ROLLED_BACK_READERS_STOPPED`, `rollback_verified=true`,
  `previous_material_current=false`, `readers_resumed=false`, `readers_state=STOPPED`,
  `terminal_reason=PREVIOUS_LEAF_EXPIRED`, and no commit decision. Original `first_cause`
  is retained; the terminal receipt also exposes the same value as `first_reason`.
  Only explicit recover CLI actions accept this result as successful command completion.
- These are **tested source semantics, not production terminalization results**. The
  historical rollback operation is referenced only by the safe label
  `replacement-initial-renewal`; its private operation ID and journals are not published.

Focused qualification: **168 passed,1 skipped** across fenced rollback, activated
maintenance, renewal transport, deterministic renewal packaging and canonical profile
store tests. The skip is the optional accepted-native-source/toolchain interoperability
probe; no gateway or client build was requested or performed. Fault coverage includes
terminal-receipt/owner interruption, partial archive moves, archive fsync and completed
ledger interruption, idempotent replay and fresh-operation exclusion until both cleanups.
Ordinary test-harness issues (missing Git, explicit synthetic unit argument and CLI umask
isolation) were corrected before the successful run. No production workaround was used.

Source checkpoint `dfbfbc34cc3345e281294ff429555d9b95a35f91` was pushed and remote SHA
verified before packaging. Only the credential-renewal/controller-node package was rebuilt:
two byte-identical builds,62716 bytes,17 members. Package SHA256:
`349018be0015b03743cd9164f287589b79e46f60d405da26712a7d9b71e61e0d`.
Exact13-module inventory SHA256:
`7d5012cb0ff7b811f4d33ad42cb4da5e74ae6ce1d1be00a9a38a0c34a9025cf1`.
Manifest SHA256:
`edc26e30c88edaf8fabf2d7c69d9e869374b1f0e7238374d4f8394005c9436c4`.
Six changed modules match the source commit; archive/API member hashes and privacy scan
PASS. The actual package passes13 module imports, four CLI help commands and one isolated
canonical-route construction test using its pinned API. Import/help runtime: Python3.13.15;
this is local qualification, not a production CPython3.14.4 deployment claim.
The prior accepted renewal artifact remains deployed and is **not superseded** operationally.
AWG, TCP, gateway binary, Android, snapshot and maintenance artifacts were not rebuilt.

Fresh21:18–21:21UTC read-only evidence confirms the database-only conflict and retains
authenticated encrypted evidence. At21:22UTC the old node remains fenced with eight
product units stopped/disabled and no product interfaces/listeners. New AWG/TCP remain
active; restricted remains inactive, with expired directory still correctly rejected.
Paid ledger0/0 and catalog sequence3 remain unchanged. No publisher room, directory
publication, new renewal operation, service start, client cutover or owner smoke occurred.
Final21:29UTC readback confirms the same conflict, byte-identical controller journal,
paid0/0, catalog3, paused renewal, fenced old NL and available RU public HTTPS. No new
production recovery command was sent; both node owners and all history remain retained.

**Next gate:** reconcile the live RU registry additions with the retained operation
without discarding records or weakening exact-state checks. Do not deploy or execute
recovery until both exact rollback readbacks and stopped-reader prerequisites are proven.
Only then may the authorized publisher/fresh-renewal/cutover sequence continue.

## Earlier host preparation provenance

Host/staging provenance: after the initial
blocked audit, the owner authorized installing the required OS/packages over SSH.
Supported LTS upgrades and exact-runtime compatibility checks are complete, not a
provider disk reinstallation or product deployment. Final OS: Ubuntu26.04.1 LTS,
kernel7.0.0-42-generic. Inactive file restoration is verified; product activation and
acceptance were then pending. Current fencing/ordinary results are recorded below.

The initial **BLOCKED_NEW_HOST_OS** finding was an incompatible OS/runtime: Ubuntu22.04/glibc2.35
cannot load the exact accepted CPython3.14.4 executable requiring `GLIBC_2.38`.
The snapshot launcher explicitly requires CPython3.14; system Python3.10 is not an
accepted substitute. No runtime downgrade, custom build, libc replacement or OS
upgrade was attempted during that initial read-only audit. This is an ELF ABI
incompatibility, not a missing ordinary tool. Subsequent installation is recorded below.

Initial host-key verification was paused. The owner could not locate the provider
console and then explicitly chose direct public-key installation. In a separate local
terminal the owner accepted the previously observed RSA fingerprint via SSH TOFU and
completed `ssh-copy-id` successfully. Provider-console verification remains **not done**;
TOFU is not independently verified provider identity. The operator subsequently checked
the accepted known-host fingerprint and authenticated with strict host-key checking and
the existing private key, without password prompts. No known-host entry was replaced or
checking bypassed. Password input stayed in the separate terminal, not this transcript,
shell history, command arguments, environment or reports. No private SSH key was copied.

Target: `root@185.10.158.212`, replacement production Netherlands gateway. This is
availability restoration, not a new product checkpoint. **BETA-0-CANARY-1 remains
PAUSED**. Paid-canary, subscription events and Android stage0 were not run.

## Repository and provenance

- Fetched `origin/main`; local and remote entry SHA both
  `17713e70279ed86d13c52ebddf167b6dc3d40a47`.
- Existing unrelated tracked and untracked changes are preserved and excluded from
  this source/documentation checkpoint. No branch switch, reset or history rewrite.
- Accepted coherent canonical source remains
  `c9c0a4de55f455e0788e7b519383c0cb0743fc96`; no rebuild or approximate substitution.
- Read the current incident, canonical acceptance and backup boundaries. The accepted
  old-network findings were not reinvestigated. New NL is the restoration path.
- No client/server version, installer, APK, invitation link or update catalog changed.
  Android106 is the required later client acceptance target, not newly observed here.

## Artifact audit

All five requested anchors have exact retained matches. A private inventory records
size, SHA256, owner, group, mode and source/receipt provenance;889 local files were
inventoried. Matching copies were found twice for each role. Later canonical acceptance
retains these bytes; no artifact supersession is asserted.

| Role | Bytes | SHA256 |
| --- | ---: | --- |
| Snapshot package | 167573 | `6dd51ead36a977abd4e6afee978d81df229ac767a6315bc4b2347328bde60c84` |
| Credential renewal | 60950 | `c2ce2b01ac15cbb553692579e7a03b6bc7ad97f2159906ed884c3fda490a40c0` |
| Restricted maintenance | 201792 | `c134eb6b56f01a4a54829b73c3259ba15886f603726058cc5f29afd3778b2a2d` |
| Canonical gateway | 17925498 | `f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef` |
| Exact-payload CRL helper | 138174 | `3c3736917efb1720b7086e57e4e8b2182fcb56734ec85b662b9bed71c15840a6` |

## Coordinated backup and old-host readback

At17:57:07UTC, read-only SSH using the existing accepted operator route exported the
later accepted coordinated NL backup created28.10 at20:14:20UTC:42 files, manifest
SHA256 `de7f7af32260b310a6b41f6758b95b0175d5f4f2adda42085901fd08bb45c969`.
Every retained payload matched its receipt hash both remotely and locally. The archive
was encrypted in memory with AES-256-GCM before local persistence; encrypted-file
readback and authenticated decryption reproduce the same bytes. Local private material
uses0700 directories/0600 files. No plaintext archive or key was printed or committed.

For the coordinated-backup role, this later42-file receipt supersedes the earlier
34-file staging backup as the selected recovery evidence. Neither is a complete current
machine image. Current gateway identity/TLS/authority, AWG/TCP keys and peers, supporting
identities, forced-command lines, runtime, firewall/NAT/sysctl and monitoring coverage
still require a complete private restoration matrix and fresh coordinated export.
Backup integrity PASS is **not** full identity-recovery or deployment acceptance.

Additional read-only exports are encrypted and verified: current application7 files
and infrastructure14 files, with one SQLite backup checked in each; recovery bundle
3895 files/549 directories and a separate NL renewal-state bundle1394 files/164
directories. Bulk live exports are **not coordinated across all roles**; final
quiescent/fenced export and the full private deployment matrix remain required.
The application snapshot's AWG private identity derives the running server public key;
all46 peer/address mappings match the live interface, with no duplicate addresses.
All46 TCP credential IDs and mappings are unique. No client credential was regenerated.
The canonical private identity matches both retained coordinated profile copies.
Historical canonical profile signatures/bindings PASS, CRL/floor27224 aligned. Its
authority remains valid until16 January2027; gateway certificate and CRL expired
29 October11:42:38UTC. Historical validation is not current-valid production acceptance.

Read-only current inventory at17:57:40UTC retained112 file/directory metadata records,
effective service argv and listeners privately. AWG, TCP, mailbox, Reticulum and load
monitor were active; restricted gateway was inactive/disabled. All six observed
`NRestarts` values were0 in this single sample; this is not a stability or data-plane test.
**Old NL remains unfenced**; nothing has been activated on the replacement. No identity
conflict was introduced. Old service activity is not evidence of healthy production.

## Historical inactive restoration qualification

Private deployment matrix now covers13 roles and10 source units, including ordinary
AWG/TCP, canonical gateway, snapshot/renewal/publisher/maintenance boundaries, mailbox,
Reticulum, monitoring, retained legacy AWG/native WG and the mailbox mount.5285 verified
files and689 directories are restored inactive. Full paths/configurations remain private.
Five locked service accounts preserve names/groups; two numeric UID collisions with
base OS accounts were remapped, without changing those OS accounts or creating admins.
Production service starts are guarded by an absent activation marker. Forced-command
authorized-key routes are not installed; existing new-host SSH identity/admin access is unchanged.

The external interface changes from the observed old `ens3` to new `eth0` in the two
active JSON configurations and two scoped nftables files only. No signed material or
binary was patched. The publisher directory inode/device binding and dependent locator
hashes are rebound to the new filesystem; profile/directory ownership boundaries remain
separate. A missing parent-directory traversal mode was corrected from source metadata.
Exact accepted snapshot launcher bytes match after fresh pinned-runtime qualification.
Mailbox uses a newly allocated bounded ext4 volume with the original marker, identities
and file-level snapshot; no live filesystem image was copied. Mailbox preflight, Xray
configuration, native WG configuration and both scoped firewall syntax checks PASS.
These checks neither start product listeners nor establish current-valid restricted
materials, data-plane acceptance, actual SSH snapshot or successful renewal.

## Fencing and ordinary data plane

Old NL: eight product units stopped/disabled, with persistent missing-marker restart
guards and a separate scoped ingress quarantine. Product interfaces and listeners are
absent; external TCP443/4242/4243 no longer accept connections. RU mutating SSH ingress
to old NL is blocked while direct operator SSH and read-only local monitoring remain.
No old file or identity was deleted. An initial verification fixture treated systemd's
unprintable `Conditions` property as text; corrected readback checks loaded guard files,
unit states, network interfaces and actual firewall rules instead. Fencing is proven.

Final coordinated export19:59:43UTC runs with product services inactive, mutating ingress
isolated and profile/registration/membership locks held:5289 files,709 directories,
75623230bytes, SHA256 `a7e8b7ed5eec29ec0ccec166d295c02995dc2608bce179d2a2165d46daae9b8f`.
Authenticated encrypted readback PASS; two changed files reconciled before activation.
The new host retains its own verified SSH host identity and owner administrative key.
Four accepted forced-command public-key lines and one bounded sudoers route are restored;
no private SSH key was transferred. Actual RU→new-NL canonical RPC inspection PASS.
Snapshot rejects the expired profile; this is not current-valid snapshot acceptance.
A canonical JSON newline fixture error was corrected without rebuilding any artifact.

New scoped ingress is default-deny with loopback, established/related, ICMP/IPv6 ICMP,
SSH and only required product ports allowed. SSH/fail2ban remain usable; no global flush.
Accepted IPv4 forwarding/rp-filter and IPv6 policy verified; scoped AWG NAT uses `eth0`.
AWG/TCP plus retained legacy interfaces, mailbox, Reticulum and monitoring started.
Restricted gateway remains inactive pending current-valid materials.

- AWG20:03UTC: synthetic handshake, DNS, HTTPS, new-IP egress, IPv6 fail-closed and cleanup PASS.
- TCP20:04UTC: synthetic REALITY authentication, remote DNS, HTTPS, new-IP egress and cleanup PASS.
- No owner/paid-canary identity or persistent peer/credential was used. A non-root Docker
  fixture write-permission error was corrected inside the bounded synthetic container.
- Three samples over30seconds: stable ordinary/supporting PIDs,0 restarts,46 authoritative
  AWG peers/46 TCP credentials, no duplicate allowed addresses, no OOM/kernel storage error.
- New monitoring samples are fresh. Old provider capacity200Mbps is not asserted for the
  replacement: capacity remains unknown until independently established.
- Fresh RU application backup:54 files/six SQLite databases; infrastructure backup:40 files;
  encrypted/hash-verified. Paid subscriptions/events0/0; signed catalog sequence3 unchanged.

These are server-side ordinary results, not full supporting-role/MESH or owner acceptance.
No normal-client endpoint or RU production route has been switched.

## Restricted renewal blocker and safe rollback

At20:14UTC, non-mutating evaluation of the retained exact renewal package reported
`RENEWAL_REQUIRED`: no file changes, remote writes or restarts. Actual forced-command
RPC inspection already passed through the new host's pinned SSH route. The owner-paid
identity was not used. The renewal timer was paused to exclude overlapping runs.

One manual accepted renewal transaction started20:21UTC, using a private controller
configuration pointing to new NL, without changing the production controller route.
Fresh candidate profile validation reached the canonical promotion boundary, where
`DirectoryPort.read(candidate, now)` rejected the still-expired publisher directory.
The exact maintenance gate reports `DIRECTORY_INVALID`; no binary, validator or
accepted package was patched. Independent20:29UTC readback confirms directory expiry
at29.10 13:04:25UTC; its historical signature/binding validates, its current validity does
not. Original certificate/CRL are also expired; CRL/floor remain aligned at27224.

The accepted recovery logic rolled profile state back on both nodes. Actual RU and NL
readbacks return `PREVIOUS_SNAPSHOT_RESTORED`. Reader resumption is blocked by the expired
previous materials, so the coordinator retains `RECOVERY_REQUIRED`, first cause
`DIRECTORY_INVALID`, `commit_decided=false`. Preserve this journal and staged evidence;
do not rerun renewal, erase the transaction, relax validation or create a new trust anchor.
The legacy credential-only publication helper is not an accepted canonical-directory
recovery path; the expired-apply route reaches the same promotion gate.

After both rollback readbacks, only the pre-existing RU ordinary HTTP service was
restarted with its unchanged accepted artifact.20:26UTC loopback dispatch and20:34UTC
external trusted HTTPS return the expected JSON400 for malformed requests. This verifies
API availability, not an authenticated client/VPN smoke. Automatic renewal remains paused;
restricted sync timers remain quiesced. New restricted gateway was never started and
has0 restarts. The manual controller is no longer running. Renewal failure records and
state from both nodes were encrypted, hash-verified and read back privately.

Final20:34UTC safety checks: eight old product units remain inactive with persistent
guards; old interfaces/listeners absent and external TCP checks negative. New ordinary
AWG/TCP remain active, no catalog cutover; paid subscriptions/events freshly0/0 and catalog
sequence3 unchanged. No paid-canary, subscription event or Android stage0 activity.

### Read-only continuation: publisher and journal recovery gate

Fetched local/remote main both match `edadd7fe050147d05dc976af9530234a2b6896ff`.
Fresh actual RU/NL rollback readbacks confirm the accepted previous snapshots; coordinator
is still normal-mode `RECOVERY_REQUIRED`, `commit_decided=false`, first cause unchanged.
Journal files are hash-identical before/after the audit. The candidate is current-valid;
the predecessor passes historical validation only, not current validation.

Exact publisher audit PASS: effective executable is the retained canonical gateway
`f8ff517804c8cc425b172c821630274ce39ccfa9a3e79328db3e8a626f45ebef`, covered by Locator's
unchanged publisher contract. All282 retained source-member hashes validate against
manifest `27b54a9dd167c3b6af639bb03864f4d7d121c0e8b96c90eccb45a198c936f117`.
Provider configuration matches the exact fenced backup; no credential/API call was made.
The sole declared publisher is integrated into the stopped restricted gateway: duration4h,
seed rotation3h, systemd restart delay30s, not a separate publisher timer. No accepted
publisher process is running. The exact executable has no one-shot recovery command.
Publication uses the retained `Cache.Store` lock, exclusive sibling temporary file,
file fsync, rename and parent fsync. The source validates the current profile before
starting the seed publisher. Normal startup is not an expired-predecessor recovery path.

Current directory remains unchanged:
SHA256 `e0c1674381f910b6133d9ce295a01784f47487a437a3ad993e1e3be57a4ba53c`,
issued29.10 09:04:28.459218429UTC, expires29.10 13:04:25.250203756UTC.
Historical family/gateway binding PASS; current-time validation rejects expiry.
No new directory hash/generation exists. Room creation, room validation, directory
publication and restricted start are **NOT_RUN**, not failed attempts or acceptance PASS.

The deployed renewal controller source matches the repository exactly, SHA256
`d0ab545cc71d54d95600b10a03d3e501226c018a01d60a5ea4039f9003627bce`.
Its normal `recover()` path verifies rollback, then requires current-valid predecessor
credentials before restoring readers and reaching cleanup. Exact production validation
returns `LEAF_EXPIRED_OR_FUTURE`. An in-memory replay of the deployed method with all
writes and node RPCs replaced by simulation reaches `ROLLED_BACK` then `RECOVERY_REQUIRED`;
it never reaches directory reconciliation or terminal cleanup. These are simulated
states only: no production journal write, service fence/restart or recovery RPC occurred.
Normal `run()` always dispatches this unfinished operation back to recovery; it does not
resume the fresh candidate. The exact expired-recovery checkpoint check independently
rejects `OTHER_OPERATION_RECOVERY_REQUIRED`, because it requires a committed checkpoint.

This is **BLOCKED_RENEWAL_JOURNAL_UNRESOLVED**, not a publisher permission/package fixture
error. The allowed publisher-only source correction cannot change that controller gate.
Stop before creating a room or publishing a directory that cannot unblock promotion.
Required next authorization within the same operation: a bounded controller recovery
transition that makes verified rollback terminal while expired readers stay fenced,
preserving first cause, prior receipts and authority; no manual journal edit or validator
relaxation. No source was changed or production artifact rebuilt in this continuation.

Focused directory/profile-store/snapshot/restricted-sync checks:127 PASS,72 deselected
in an isolated root container with network disabled and read-only source/artifacts.
Two initial missing retained-fixture inputs were supplied and hash-verified, then the
entire same selection passed; no test was skipped to hide those fixture errors.
Final21:00UTC readback confirms old NL FENCED, RU ordinary HTTP available with trusted
public HTTPS dispatch, renewal paused, ledger0/0 and catalog sequence3. New ordinary
services remain active with0 restarts; restricted inactive, CRL/floor27224 unchanged.
No owner/canary identity, subscription/event, APK or client endpoint change.

## Source-only cutover preparation

Endpoint routing preparation is committed as a **NOT_DEPLOYED source checkpoint**:
ordinary NL registration uses the same operator-owned catalog envelope returned to the
client, chat synchronization uses its configured node, mailbox acknowledgement uses the
identity-bound bootstrap, and monitoring accepts a configured remote host. Strict SSH
pinning is preserved; RU registration remains local. No endpoint/private configuration,
monitoring inventory, signing key, APK or production HTTP artifact was switched.

Focused routing, monitoring, HTTP-runtime and chat tests:43 PASS,14 optional skips.
Skipped tests require the configured native Nginx matrix or pinned synchronization
artifact; this is not a complete HTTP deployment gate. Two local HTTP builds are
byte-identical:47368bytes, SHA256
`44a6b50f1a1ce00fd74f53e0d35c5937c6b5f5c2a561fc94b7a0150f39149204`.
This candidate does not supersede any retained accepted artifact. The unchanged active
RU HTTP package is47091bytes, SHA256
`dcd769986a1da7cb1662c0f73d18a88e9f73485a977db937ca5b1428c1fd1029`.

## Acceptance and publication gates

### Authorized host preparation continuation

- Owner authorized required installation; continuation entry main
  `6ed27282b582d0600208cdb31d32e245e0ee99f8` was fetched and remote-verified.
- New-host SSH/access, package-source, network and boot configuration were backed up
  encrypted before management writes; authenticated decryption readback PASS.
- Official Jammy security updates and base diagnostic/upgrade packages installed.
  Root/password access was not disabled. No public product listener was introduced.
- Hostname identifies replacement NL. Bounded SSH fail2ban configured; journald limits
  200MiB persistent/32MiB runtime/14days. Existing approximately1GiB swap partition is
  retained; an additional1GiB mode0600 file is enabled persistently, total about2GiB.
  Swappiness10; no gateway service memory cap was guessed before exact restoration.
- Package `needrestart` restarted the preparation runner once during its first pass.
  Readback reconciled the running job rather than starting a duplicate. Base installation
  subsequently completed; upgrade runners are now excluded from automatic needrestart.
- A local boot-test fixture initially expected ext4 as a module; the installed kernel
  builds ext4 in. The corrected gate accepts the exact kernel configuration or initrd
  module, not an absent filesystem driver. GRUB, initrd/virtio/root-filesystem, dpkg and
  SSH checks passed before reboot. No product service was involved in either recovery.
- One controlled security-update reboot returned successfully with unchanged trusted
  SSH host key and key login: Ubuntu22.04.5 LTS, kernel5.15.0-202-generic.
- The supported22.04→24.04.5 operation completed, followed by a guarded reboot to
  kernel6.8.0-147-generic. The upgrade left the resolver disabled; enabling the already
  installed system resolver restored DNS and the official26.04.1 upgrade offer. This
  ordinary configuration error was corrected without changing provider networking.
- Read-only inspection of53 retained runtime ELF files also identifiesGLIBC2.42 and
  OpenSSL3.3/3.4 version requirements in the accepted extension set. Ubuntu24.04 alone
  is therefore not the final runtime baseline. The official24.04→26.04.1 upgrade also
  completed successfully, then rebooted to7.0.0-42-generic. No CPython rebuild or libc
  transplant. Temporary SSH restart windows recovered; no host-key bypass or reset.
- Ubuntu26.04 automatically reserved320MiB for crash capture despite the existing
  disabled crash-dump policy. A guarded boot-configuration override removed that
  reservation; the fourth reboot restored1960380KiB usable RAM. Kernel reservation
  readback is0; persistent swap remains about2GiB, unused in the sample.
- Exact accepted interpreter SHA256
  `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`
  matches the installed CPython3.14.4. Isolated retained-runtime qualification1795
  files PASS: cryptography46.0.7, rns1.5.1, pyserial3.5, snapshot package import,
  exact gateway help and Xray version execution. No identity/configuration was installed
  with this runtime probe; it is not actual snapshot-account or data-plane acceptance.
- Old NL deployment contract was additionally collected read-only:88 metadata records,
  six units and11 network/runtime sections; source/configuration bodies encrypted and
  verified locally. This remains a partial private matrix, not a consistent full backup.

Historical pre-activation host readback19:11:14UTC: NTP synchronized, cloud-init done, TUN accessible,
no failed units, no pending reboot or reported package upgrades, strict pinned root SSH
PASS. Fail2ban/resolver/time synchronization active with0 restarts in this sample.
Only public SSH22 and loopback DNS listeners remain. Root/password login was not disabled;
provider-console recovery remains unverified. No broad firewall flush was performed.

Diagnostic ingress19:06:45UTC PASS from both workstation and RU: TCP443/4242/4243 and
UDP443/51820/51823. Paired bounded capture confirms a RU-origin SYN at the new interface.
All12 nonce echo checks passed; temporary diagnostic listeners closed. No product
identity was used. Provider-path reachability is demonstrated, not VPN/TLS/mesh operation.

### Historical new-host entry preflight

Observed18:08:03UTC, successful root public-key login. Ubuntu22.04.1 LTS, kernel
`5.15.0-46-generic`, x86_64, KVM,2 CPUs;1973984KiB total RAM (about1.88GiB).
50GiB virtual disk; root ext4 about9% used. Existing swap partition1048551424bytes,
unused in the sample; no additional swap was created or persistent policy changed.
TUN character device exists and is readable/writable. NTP synchronized, cloud-init done,
no failed units, no reboot-required marker. Only TCP22 is listening on IPv4/IPv6.
iptables uses the nftables backend. Numerous package updates are pending; no package
installation, security update, reboot or firewall change was made before the OS gate.
Provider firewall/console recovery is not independently confirmed.

Compatibility readback18:09:50UTC: old NL uses Ubuntu26.04, CPython3.14.4 and glibc2.43.
Its accepted interpreter ELF version-needs entries explicitly require `GLIBC_2.38`.
New NL has Python3.10.4 and glibc2.35; no CPython3.14 package candidate was identified
in its configured Jammy package metadata. `postgresql-plpython3-14` is a PostgreSQL
extension, **not** CPython3.14. The source guards in
[`build_profile_snapshot_launcher.py`](../../scripts/build_profile_snapshot_launcher.py)
require CPython3.14 for both executable qualification and the isolated pinned venv.
The retained gateway itself requires at most GLIBC2.34, so this finding must not be
misreported as gateway-binary corruption or a failure of all five accepted packages.

| Gate | Current result |
| --- | --- |
| New-host SSH identity/login | Owner-interactive TOFU, pin matched, key login PASS; no provider verification |
| New-host OS/runtime | Ubuntu26.04.1/kernel7.0.0-42; exact interpreter and retained runtime import/execution PASS |
| Architecture/TUN/NTP | x86_64/TUN/NTP PASS; ordinary data-plane acceptance separately recorded |
| Provider constraints/recovery console | Required diagnostic ports reachable from RU/workstation; console NOT_VERIFIED |
| Base preparation, updates/reboot, swap and SSH recovery | Four guarded reboots, final OS/swap/strict SSH PASS; console still unavailable |
| Private deployment matrix/identity staging |13 roles derived; inactive staging and final coordinated mutable export complete |
| Old-NL fencing | FENCED; eight product units disabled, interfaces/listeners absent, persistent guards |
| New AWG handshake, DNS, HTTPS and cleanup | PASS synthetic; egress185.10.158.212, IPv6 fail-closed |
| New TCP authentication, tunneled HTTPS and cleanup | PASS synthetic; egress185.10.158.212 |
| Canonical profile, fresh certificate/CRL/floor/directory | BLOCKED_DIRECTORY_INVALID; previous snapshot restored, expired material not accepted |
| Actual snapshot SSH, renewal preflight/timer and restricted data plane | RPC inspect PASS; snapshot rejects expiry; renewal RECOVERY_REQUIRED/timer paused; restricted inactive |
| Supporting roles and accepted firewall/NAT/sysctl restoration | Services started; scoped networking verified; supporting data plane pending |
| RU-origin packet arrival | Diagnostic ports/SYN PASS; product data plane NOT_RUN |
| Multi-sample stability and monitoring cutover | Three ordinary/supporting samples PASS; inventory cutover pending |
| Fresh RU backup, ledger and configuration prepublication checks | Backups PASS, ledger0/0; recheck before publication |
| New signed catalog sequence and restricted publication | NOT_PUBLISHED; no sequence allocated |
| Android106 endpoint fetch and owner AWG/TCP/Auto-MESH smoke | NOT_RUN |

RU renewal attempted canonical mutation and rolled back; ordinary HTTP availability was
restored afterwards. The signed catalog and production endpoint configuration were not
switched. Paid ledger0/0 is freshly queried at final readback. Monitoring inventory remains
unchanged; unavailable old registry data must not be reported as zero.
No new NL readiness, rollout or full-success claim is made.

## Resume and rollback

Host preparation, private matrix, final coordinated export, fencing and ordinary synthetic
acceptance are complete. STOP on the proven journal recovery gate, not an ordinary
installation error. First qualify an explicitly authorized bounded controller path to
terminal verified rollback without resuming expired readers or losing journal history.
Publisher recovery is already authorized, but is insufficient without that transition.
Then refresh the expired publisher directory before canonical profile promotion,
preserving authority and the shared lock; complete restricted/supporting gates before publication.
No disk reinstallation was performed; SSH host keys and root access remain intact.
The preferred24.04 baseline does not meet the full retained extension ABI requirements,
so26.04 is the verified final baseline.
Do not bypass the3.14 guard, replace system libc independently or silently rebuild
accepted runtime bytes. Reverify host identity without replacing the known-host entry.
Continue only after that localized blocker is resolved, with fresh restoration guards.
Reverify old-node fencing before any further identity activation.
Do not regenerate a recoverable identity, trust anchor or client credentials.

Prepare and restore the exact accepted contract, renew expired restricted materials via
the existing authority/renewal/publisher routes, and pass synthetic data-plane, RU-origin
connectivity, actual snapshot/renewal and stability gates before publication. Then take a
fresh RU backup and verify ledger0/0, paused canary and fencing; publish one monotonic
signed NL control-plane update. Verify Android106 without an APK change before asking
for the owner's AWG smoke, then TCP, then Auto/MESH. Canary stays paused throughout.

Rollback now: **PREVIOUS_SNAPSHOTS_RESTORED_RU_ORDINARY_AVAILABLE_RECOVERY_REQUIRED**.
No catalog rollback is required; new NL remains unpublished and old NL remains fenced.
Do not mistake profile rollback for successful restricted-service recovery. Ordinary/supporting services
and forced SSH routes are active on new NL; old NL must remain inactive. Stop the affected
new service if an identity conflict appears. Do not return traffic to old NL. Encrypted pre-upgrade configuration is
retained, but it is not a full disk image or a promise of automatic OS downgrade.
Old NL must remain fenced. New ordinary/supporting identities are active only on the new host.
Before publication, a failed replacement stays unpublished and RU ordinary service is preserved. After a
failed publication, use the supported catalog mechanism to stop NL admission/return to
RU; do not reactivate old NL without independent full acceptance. Never serve one copied
identity on both hosts. Preserve all old files as recovery evidence.

## Verification scope

Current read-only continuation updates five existing documents only: strict JSON,
targeted privacy/secret scan, changed local Markdown links, staged scope and whitespace
checks PASS. No extra report or sanitized receipt file is created.
Unrelated changes remain outside the index; original document suffixes are preserved.
Current127 focused tests and the earlier two deterministic HTTP package builds are recorded above. No platform
build or historical full test suite was run; none substitutes for unperformed production
and client gates. This is an incomplete restoration checkpoint, not a release.

[Sanitized JSON receipt](2026-10-30-nl-gateway-replacement.json) ·
[Accepted canonical receipt](2026-10-28-android106-beta-0-canary-canonical-profile.json) ·
[Retained incident](2026-10-27-android106-beta-0-canary-1.md) ·
[Backup contract](../server-secret-backup.ru.md).
