# FIELD-1-RELEASE-FINAL / DIAG-1A — 2026-10-03

## Diagnostic beta61 preparation — commit/push authorized

Source checkpoint `d93a01d` committed and pushed to main; unrelated VPN-health
documents left untouched. Focused packaging/field-release pytest9/9 PASS and
`git diff --check` PASS. CI `37138322487`: Linux, Windows and compatibility PASS;
Android native/JVM/lint/APK verification, emulator acceptance, full carrier race,
restricted native/gateway build and final unsigned ARM64 packaging PASS.
phase0 `37138322534`, Linux control
`37138322506`, readiness golden `37138322507` all PASS. No separate Windows control
workflow triggered (its path filters are unchanged); actual Windows job ran.
Authenticated GitHub readback is authoritative after the public API monitor hit
HTTP errors and was stopped. All Android steps including Complete job confirmed
successful through authenticated job111247328678 readback.

Artifact11279129098 downloaded after CI verification. Local archive SHA256 matches
GitHub's recorded digest:
`11adb429fd70741d86d778be9864d3505d009fdc33802dbf9257f95315a75821`.
Unsigned APK49,604,500bytes:
`7e3fb20413d7a3598ee2fffffd8e9f52b0003cf9ceba63142f733e85051beacb`.
Restricted native:
`bffb7c4db1922aa5b76c49320490911264f36f5fb26cede670a9e2539b3fbe20`.
Gateway executable:
`aca7c13af2802d07e6fcb131367705a29d118650dbbf30ca0af1c8936ad265e4`.
All originate from `d93a01d5f737a09ef46bfc1d4b7790560fdf26cd`. Verified APK package,
code61/name, Friends launcher, nondebuggable/no-backup/no-cleartext manifest,
ARM64-only, pinned Xray/patch, both native byte hashes and restricted_session DEX
contract; zipalign16KiB PASS. Privacy scan1071 entries, zero findings; only unchanged
previously reviewed stdlib upload.pyc false positive. apksigner rejects the unsigned
artifact as expected. No signing keys read, APK signed, owner/device changes, gateway
deployment or public download switch. Local receipts and immutable archive retained
under ignored `state-client-build/field61-ci/`; no private data committed.

Remaining delivery gates: offline signature, owner in-place/native acceptance,
diagnostic gateway rollout with fresh leases/ordinary READY and executable rollback,
then immutable public APK and increasing signed catalog before tester instructions
are actionable. Existing public beta60 remains intact; do not install the unsigned
CI output or uninstall the tester's current app. Root session-loss cause still open.

Source version raised to0.1.18-beta61/code61; beta60 remains public/invitation/catalog.
No signed61, device installation, gateway deployment or public rollout yet.
CI retains emulator/desktop gates, adds full carrier race tests, pinned restricted
arm64/native gateway builds, and a dedicated unsigned artifact with source SHA,
native byte/manifest/diagnostic-contract checks, normal native verification and
version/package/signature-state receipt. Increased Android job budget55→75min for
the added pinned native build. Signing remains offline after accepted CI/downloads.
Five synthetic payload tests cover parity, stale native/manifest, wrong source pin
and missing Java diagnostic contract. Existing local diagnostics test results below
still apply to the preceding unversioned implementation, not a released beta61.
Owner physical device is connected; no mutation performed in this preparation.
Required acceptance: original signer/package/UID/identity/enrollment/Support retained
through in-place update; real-device diagnostic contract; fresh readiness/leases;
controlled gateway binary with executable-only rollback. Do not restore expired
credentials, reset identities, widen admission or restart ordinary HTTP/AWG/TCP.
Tester delivery: verified signed APK link after acceptance; download over Wi-Fi,
install as Update, never uninstall/clear data, confirm beta61 and same Support ID,
then wait for operator-ready gateway before one mobile Auto test/export.
Public hashes/links remain unchanged until the signed artifact is verified/published.

## Terminal-reason diagnostic implementation — local only03.10.2026

User authorized work to identify and eliminate the repeated post-connect failure.
Starting HEAD9fde56d, prior dirty observation/VPN-health documentation preserved.
No commit/push, server/device write, registration change or release publication.
This implementation repairs lost diagnostic evidence; the network/transport cause
of the two real failures is not yet established or claimed fixed.

### Changes

- New `carrier/sessiondiag` maps typed/wrapped errors to finite categories and
  projects only selected numeric metrics and allowed reliable/ICE/signaling states.
  Unknown errors become UNKNOWN without raw text. Correlation uses a domain-separated
  SHA256/128 tag of random setup ID; no original setup capability/room/address export.
- Mux records first failure time and retains first error through cancellation,
  including control-queue overflow. Wholedevice stores plane.Wait's category and
  exposes the session projection. Existing fail-closed handling/limits unchanged.
- Gateway emits `session_terminal` plus allowlisted broker reasons instead of
  throwing away the Code. Error timestamp is separate from later cleanup/log time.
- Android exports `restricted_session` with native_state/authorization_denied and
  bounded projected report. Unknown fields/strings, fractional/negative/unsafe integers
  are rejected. First terminal snapshot survives teardown; new CONNECT resets it;
  independently retained incident persists. Poll reads health before collecting
  evidence, so native state is current at failure. Generic terminal INTERNAL policy
  is deliberately unchanged until cause classification.

No key/profile/provider token, endpoint/ICE address, DNS name, payload or arbitrary
error message added to shared diagnostics. Existing internal evidence still stays
private; no raw logs/packet capture requested. Correlation tag is ephemeral, not
a persistent device identity. No dependency/version/security-policy changes.

### Checks and artifacts

| Check | Result |
| --- | --- |
| Full carrier `go test -race ./...`, live Telemost gates disabled | PASS |
| Go added classification/privacy/correlation/first-error/overflow/cleanup tests | PASS |
| Final broker enum/race test after allowlist refinement | PASS |
| Friends JVM,36 suites /228 tests | PASS,0 failures/errors/skips |
| Android first-terminal/privacy/denied/new-connect tests | PASS |
| `lintFriends` | PASS |
| `tests/test_field_release.py` |4 PASS |
| Go1.26 gateway build | PASS, local Linux binary |
| Android arm64 native with pinned Xray/gVisor/NDK27.2 | PASS |
| Unsigned `assembleFriends` with explicit fresh native source set | PASS |
| APK native byte hash + build manifest + DEX diagnostic key | PASS |
| apksigner rejects unsigned compile-only APK | Expected rejection verified |
| `git diff --check` | PASS |

Local gateway SHA256:
`62e8de71bc1e49741739cf472ce55108c8ad8867be93822f0f7c247e8b9f9bdb`.
Local native SHA256:
`8771739a1a8968d173562d48d9a2c0f66670a8e2ca5e90c5ea19a7580b163d0b`.
Compile-only unsigned APK SHA256:
`488689f833a05f98b747f17f386961430cbc8499a6524e7974a1c4425267cfa4`.

Native output under ignored `state-client-build/session-diagnostics/native/`;
gateway `/tmp/fc-session-diagnostics-bootstrap-broker`; APK is Gradle's local
`app-friends-unsigned.apk`. APK retains source beta60/code60 only because no release
version change was made: **never install, distribute or sign this as replacement60**.
It is packaging proof only, not accepted immutable release provenance/platform CI.
Default generated native assets were not overwritten; build used a temporary Gradle
source-set override selecting the fresh .so. No signing keys accessed.

Initial Go/Gradle socket tests failed under sandbox and passed outside it. Native
build hit /tmp disk quota twice (including outside sandbox); third build with
TMPDIR/output on project disk passed. No preexisting files/cache removed. Gradle
reported Python3.14/Chaquopy bytecode warning and existing deprecation/watch warnings;
these do not constitute release-toolchain or device-runtime acceptance. Linux host
build is not a Windows validation; no desktop binary changed.

### Remaining gates / recovery

Public, installed tester, invitation and Android catalog remain accepted beta60;
Linux0.2.11/Windows0.2.15 unchanged. No new hosted CI, signature, owner installation,
gateway rollout, tester export or physical validation yet. Source commit/push needs
explicit authorization; then new immutable version/clean builds/CI, native+Java
parity, platform signing and owner identity-preserving update checks precede delivery.
Do not mistake local test success for resolution of the FIELD transport failure.

Rollout: only diagnostic gateway binary and new accepted Android build, exact2/3
cohort, no normal HTTP/AWG/TCP changes. Gateway rollback restores prior executable
under existing guarded procedure, not expired credentials or old CRL floors.
Revalidate/renew prior gateway/directory/device leases immediately before live work;
the previously recorded16:17/16:22UTC deadlines have passed during local work.
No automatic renewal or lifetime extension introduced. Runtime rollback not needed
for this task because nothing deployed. Keep previous immutable APK/catalog assets.

Next: one normal-Auto real attempt with fresh readiness; correlate both reports by
session_tag, preserve unknowns, reproduce/fix the actual cause and add its regression
test. Sustained/lifecycle acceptance still required. FIELD remains BLOCKED;
no RKN attribution or cohort expansion. [Operator/diagnostic guide](../testing/restricted-session-diagnostics.ru.md).

## Fifth export / second post-renewal attempt — 03.10.2026

User supplied `FamilyConnect-diagnostics(5).json`,83274 bytes, SHA256
`80fe63abd6491f4f147eecfe434bf26a22416e1df9d51f76ab3b0554e94b0e29`.
Same tester FC-YHQB-9VJN, Android0.1.18-beta60/code60.128 events in each bounded
snapshot, overlap deduplicated. Fresh local READY16:02:19UTC precedes normal Auto;
no server ACK readback performed for that refresh in this export analysis.

| UTC | Client evidence |
| --- | --- |
|16:02:41.309|Normal Auto start, incident network CELLULAR|
|16:03:06 /16:03:28|AWG/TCP NETWORK candidate failures|
|16:04:05.758|Restricted CONNECTED after84.449s; collected Family auth/broker/SESSION_READY|
|16:04:20.901|INTERNAL transport loss after15.143s connected|
|16:04:20.913–21.027|RESTORING→FAILED114ms, no further candidate attempt|
|16:05:06|Explicit disconnect releases VPN capture|
|16:05:15|New WIFI/AWG CONNECTED in7.432s|

Incident READY/USABLE, restricted SUCCESS from establishment, capture retained.
Counters DNS20/TCP4/active0/peak3, protect145/denied0, UDP denied15/IPv6 denied40.
These are not destination-response/download success metrics. No AUTH, STARTUP_FAILED
or NATIVE_VALIDATION_FAILED in either retained snapshot. Final ring does not contain
a post-connect DNS_PROBE_OK yet; do not infer one from the previous Wi-Fi session.

Compared programmatically with fourth export:30.227s versus15.143s until first
INTERNAL after CONNECTED. Reproduced post-connect loss, not a demonstrated constant
30s cutoff. Does not distinguish network filtering, provider/NAT, reliability or
our protocol failure. Existing missing terminal-reason diagnostics still block cause
attribution; no RKN attribution, timeout increase or retry-policy change justified.

Read-only Amsterdam correlation at16:08:37UTC: exact unit/time filter16:02–16:06
returned11 events, no omitted records/cap hit. Bootstrap auth16:03:42.115343,
CREATING16:03:43.116494, CREATED/GATEWAY_JOINING16:03:46.129273,
READY16:03:48.086468, CLIENT_ISSUED16:03:48.087938,
handoff16:03:48.486722, family_auth16:04:03.622532,
ACTIVE16:04:04.633890, dedicated_resources_closed/FAILED16:05:19.694063UTC.
Final two records share journald timestamp; reverse output order is not event
causality. ACTIVE-to-terminal record75.060s; client-to-server failure record gap
58.793s is not proof of continuous service or of which endpoint caused loss.
Events have no device/session ID; only one sequence in this interval correlates
with the supplied attempt. Same active/running PID3231001, NRestarts0, since15:22:36.
Initial bounded query timed out20s; repeat with45s allowance completed, no service
mutation. Journal-read timeout is not a transport failure. No new certificate/CRL
or server readiness validation. Do not treat this as permission for another retry.

JSON parsing, state/capture/outcome assertions and no-startup-AUTH/import-failure
checks PASS. No application/server code, version, binary, credential or admission
change; no build/runtime test or rollback required. Public beta60 unchanged;
preexisting exact2/3 policy preserved, no expansion. Next engineering work remains
privacy-safe native/gateway terminal-reason propagation plus tests before another
controlled attempt with fresh readiness/leases. FIELD remains BLOCKED.

## Gateway correlation for fourth export — 03.10.2026 15:54UTC

User requested server-side investigation, not another tester retry. Read-only
operations limited to authorized Amsterdam/RU Family Connect resources. No service,
configuration, admission, credential, application or catalog mutation. Starting
HEAD9fde56d and existing dirty documentation preserved; beta60/code60 unchanged.

Exact `_SYSTEMD_UNIT=family-connect-restricted-bootstrap.service` journal filter,
15:32–15:36UTC, reverse bounded500 entries, returned11 JSON events, no omitted
records, cap not reached. Earlier `--unit` query exceeded20s and was terminated;
that query timeout is not a gateway/network health result. Exact-filter query
completed twice. No broad host or neighbouring-service logs were read.

| Gateway UTC | Event |
| --- | --- |
|15:33:56.017324|bootstrap_family_auth|
|15:33:56.712509|CREATING|
|15:33:56.965373|CREATED / GATEWAY_JOINING|
|15:33:59.286103|READY / CLIENT_ISSUED|
|15:34:00.400863|bootstrap_handoff|
|15:34:12.378907|family_auth|
|15:34:13.488299|ACTIVE|
|15:34:52.100812|dedicated_resources_closed|
|15:34:52.103185|FAILED|

Gateway session active→FAILED interval38.615s. Client independently records
CONNECTED15:34:13.877→INTERNAL15:34:44.104 (30.227s). Server failure record appears
about8s later, but observation/cleanup delays and unsynchronized endpoint timestamp
accuracy prevent assigning fault origin from ordering alone. Journal events lack
session/device correlation IDs; this is the only ACTIVE/FAILED sequence in the
bounded interval, consistent with the supplied tester export, not a cryptographic
device-to-log binding. `dedicated_resources_closed` means Mux socket/stream/buffer
counters were zero at cleanup; it does not prove successful payload delivery.

15:51:57/15:54:02UTC systemd: active/running, PID3231001, NRestarts0, Result success,
start15:22:36UTC; same PID as credential reload. No service crash/restart observed.
Disk bootstrap-broker SHA256
`e17e1fe77aa0121847c276fa15db9064d29b714977a57b568183e9950149b1b8`
matches the accepted e808f50 build. `git diff e808f50 HEAD` for its entry point,
broker lifecycle and gateway code is empty.

Source correlation: `telemostGateway.Run` emits resources-closed after Mux cleanup
and returns `mux.Wait()` error; `Broker.Create` maps returned error to FAILED with
`gateway_session_failed`. The bootstrap-broker callback ignores its Code argument,
so the journal contains FAILED only. The event order is consistent with that path;
do not invent a lower-layer error or treat it as a logged gateway_session_failed.
On Android, wholedevice Attach drops plane.Wait's error, JNI sees cancelled session,
and AutomaticConnection maps unhealthy restricted to INTERNAL. Neither retained
export nor current journal contains the original terminal Mux/reliability/transport
reason. No amount of re-reading these same events can recover that missing value.

15:54:24UTC protected file metadata projection: certificate expires16:22:33UTC,
issuer04.10 14:13:53UTC, directory issued15:22:39.140368726/expires16:17:36.983028339UTC.
This did not perform another live TLS or CRL verification.15:54:27UTC readback:
owner receipt expired15:18:33; tester last ACK15:27:38 expired15:42:05, no newer
attempt. Expiration now does not explain loss at15:34:44. Both remain admitted,
non-revoked. Exact2/3 set,28 total/24 non-revoked/4 revoked and registration,
invitation, Support mapping, owner grant and audit match the15:23 checkpoint.

Validation: safe JSON receipts retained under ignored0600
`state-client-build/field60-session-loss/`; invariant comparison and bounded-journal/
same-PID assertions PASS. No runtime tests/build because runtime code unchanged.
No deployment/rollback required; never restore expired credentials or lower floors.
Next required work: enum-only privacy-safe terminal diagnostics propagated from
native/session layers and retained at both endpoints, focused privacy/regression
tests, then one controlled fresh-readiness retry. Do not blindly remap every
INTERNAL to NETWORK or alter security/TTL policy. No tester retry requested now;
FIELD completion/expansion remains blocked. Diagnostic patch not implemented or
deployed by this read-only task. Documentation whitespace check PASS.

## Fourth tester export: post-renewal session established, then lost

Analyzed supplied `FamilyConnect-diagnostics(4).json` (83272 bytes), SHA256
`27147fab9bdaafd43cef5a8cdf0fd69dc74133450048be75b683c1add6dd1cc7`.
FC-YHQB-9VJN / Android0.1.18-beta60/code60. Both bounded snapshots contain128
events; overlapping events deduplicated for the timeline. Earlier connection start
is outside this export; no all-history counts or native event timing claimed.
Native stage timestamps are collection times, not individual handshake durations.

| UTC03.10 | Observed result |
| --- | --- |
|15:27:38|READY from ordinary provisioning; server ACK same second, expiry15:42:05|
|15:32:55.942|Normal Auto connection start; incident network CELLULAR|
|15:33:21 /15:33:43|AWG then TCP candidate NETWORK failures|
|15:34:13.877|Restricted CONNECTED,77.935s from start; Family auth, broker descriptor, SESSION_READY|
|15:34:44.104|Transport loss INTERNAL,30.227s after CONNECTED|
|15:34:44.112–44.229|RESTORING→FAILED117ms, no further candidate attempt|
|15:35:16|Explicit disconnect releases retained VPN capture|
|15:35:26|New WIFI/AWG connection succeeds in7.105s; DNS OK through15:36:42|

Read-only RU observation15:36:47UTC (prior to export analysis) confirms tester
ACK_RECEIVED/currently_ready=true; owner ACK remains expired. Gateway renewal
certificate expiry16:22:33UTC and directory expiry16:17:36UTC are the prior verified
checkpoint, not a fresh host inspection here. The tester receipt was also unexpired
at loss. No evidence supports attributing this new failure to the earlier expired
gateway certificate; startup authentication now succeeds.

Incident retained `vpn_capture_open=true`, READY/USABLE, restricted SUCCESS from
candidate establishment. SUCCESS is not an ongoing health verdict. Counters:
protect_ok145/protect_denied0, DNS44, TCP9/active0/peak8, UDP denied27/IPv6 denied30.
These prove recorded activity/rejections, not successful destination responses or
downloads. Latest ring is CONNECTED/AWG, not an ongoing restricted session.

Source inspection at unchanged HEAD9fde56d: `AutomaticConnection.poll` calls
`lost(INTERNAL)` whenever `RestrictedTunnelEngine.healthy()` is false. That predicate
checks handle/native state2 and absence of FriendsRestricted.denied. Native state
becomes3 on wholedevice session failure; `Session.Failed` observes cancellation,
including after Mux.Wait returns, but its terminal error is discarded at this layer.
The shared export does not include native state, denied flag or terminal Mux reason.
`ConnectivityOrchestrator` deliberately treats INTERNAL as terminal, explaining
the117ms failed restoration without establishing the underlying failure cause.
No new AUTH, STARTUP_FAILED or NATIVE_VALIDATION_FAILED event in this export.
Do not infer a30s timeout, provider block or crash from elapsed time alone.

Validation: JSON parsed; merged event timeline/candidate order/timestamps inspected;
source paths traced. No code change, build or runtime test performed. No APK,
service, catalog, admission, grant or lease changes; no rollback needed for this
read-only analysis. Existing credential recovery must never restore expired material
or lower security floors. Exact2/3 cohort and published beta60 remain unchanged.
Next: bounded privacy-safe gateway/native terminal correlation for this interval;
then targeted reproduction/classification before any runtime fix. Fresh leases and
owner receipt required before later use. FIELD remains BLOCKED on sustained session
loss and outstanding lifecycle/network tests; no rollout/expansion authorization.

## FIELD observation and explicit tester admission — 2026-10-03

Same FIELD-1 milestone, Stage5N CLOSED, DIAG-1A PASS. Starting HEAD
`9fde56dc5eae62378ae757bdf5ea15052fd26f21`. Public beta60/code60/source5c740f2,
SHA8ee59352 and signer67a90d1 unchanged; no APK rebuild, publication, catalog or
transport change. Unrelated dirty VPN-health documentation preserved. No commit/push
for this observation operation.

### Owner readiness renewal

Read-only preflight found delegation2/owner grant2/CRL expired11:54:56UTC and gateway
certificate expired01:57:34UTC. Existing protected offline issuer/gateway procedure
renewed delegation3 and owner grant3 through2026-10-04 14:13:53UTC, preserving keys,
Family, registration and identity. CRL floor1494→1495 then ordinary sync advanced it.
Gateway credential valid through2026-10-03 15:14:31UTC; no lease extension/bypass.
Protected host backups: `restricted-materials-stage-20261001/field60-readiness-20261003`
on the two authorized gateways. Secrets and DB backups remain outside Git/output.

Initial startup precondition found retained systemd failed state, not a fresh carrier
failure. Saved state evidence; bounded journal read timed out, not interpreted as a
transport result. Reset only restricted bootstrap unit's failed state; did not reset
security floors. Fresh start14:34:22UTC, directory14:34:26UTC, exact TLS certificate
and stable process check PASS; restored ordinary RU sync timer. No runtime redeploy.
Do not restore expired credentials or regress revocation floors during rollback;
use the existing renewal procedure for currently valid material.

Private owner instrumentation (not the public APK) exercised normal foreground
provisioning: READY, PRESENT_VALID provisioning/bootstrap, usable=true, revision3,
minimum_crl1543, failure_reason NONE. Server accepted ACK14:40:34UTC; material valid
until14:55:27UTC. Support FC-4D8Q-REEG and encrypted identity unchanged. Subsequent
registrationSnapshot and existingIdentityStillAuthenticates PASS: UID10283,
enrollment/activation/Support preserved, readiness decrypts. No new registration.
This does not constitute repeated real-network FIELD acceptance.

### FC-YHQB-9VJN explicit admission

User explicitly selected this existing Support ID. Read-only lookup verified active,
non-revoked device/invitation, valid existing public-identity binding and authenticated
Support observation reporting Android0.1.18-beta60/code60. Existing operator
`support-operator-5abc2da.pyz enable-field` applied only this admission, with expiry
2026-10-04 14:13:53UTC matching the existing owner grant. Built-in audit:
timestamp1791038282 (14:38:02UTC), Support FC-YHQB-9VJN, previous0, new1, APPLIED.

Exact admitted set: FC-4D8Q-REEG + FC-YHQB-9VJN;2 devices, cap3, no wildcard.
Before/after registration, invitation, Support mapping and owner grant fingerprints
identical. Inventory28 total/24 non-revoked/4 revoked; no duplicate enrollment/alias.
No other device enabled. If admission rollback is requested, use audited
`disable-field` for FC-YHQB-9VJN only; preserve owner and all registration records.

Normal tester challenge/fetch succeeded14:39:42UTC, revision1/minimum_crl1541,
material expiry14:54:23UTC. Bounded370-second observation and final14:46:56UTC
readback found no accepted ACK. Admission is successful, but local import READY and
ACK_RECEIVED are unconfirmed. Do not force Telemost, claim ready-to-use restricted
transport, or classify the missing receipt as censorship/client failure without
device evidence. Request About/Diagnostics export; keep app online for ordinary
provisioning. No arbitrary retry/grant reset or synthetic signed device requests.

Private safe receipts: `state-client-build/field60-observation/` and
`state-client-build/field60-tester/` (ignored). No raw identities, credentials,
room URLs or browsing data in documented evidence. Real connection cycles/network
diversity and failure classification remain pending; no FIELD completion claim.
Existing service notices are public platform-filtered announcements, not targeted
Support-ID delivery. No device-specific notice has been broadcast to all users.

Follow-up14:51:59UTC: exact cohort/audit/registration fingerprints unchanged; owner
still READY/ACK_RECEIVED within its lease, tester still no ACK or newer attempt.
No retained tester ACK challenge at14:48:29UTC; expired challenges are pruned, so
absence is not proof that no earlier ACK challenge request was attempted. Device
receipt is needed to distinguish import failure, interrupted app execution and ACK
delivery/rejection. Private `.friends.test` instrumentation removed successfully;
production application/data unchanged. Documentation diff whitespace check PASS.

User-requested recheck14:54:35UTC: tester still has only the14:39:42 fetch, no ACK
and no newer attempt; its material expired14:54:23UTC. This expiration follows the
missing ACK and does not explain the original non-delivery. Owner normal refresh
fetched14:53:08UTC and acknowledged READY14:53:09UTC, minimum_crl1566, expiry15:08:03UTC.
Exact2/3 admission, no wildcard, inventory28/24/4 and registration/invitation/Support/
owner-grant/audit fingerprints unchanged. No writes to production during this check.

### Tester-provided diagnostic export

Received `FamilyConnect-diagnostics.json`,41168 bytes, SHA256
`d8fb5dcf21f3d7e859c70c8a7f9c2a56e9aee9b06fe44f5a0364ff8c85a5934b`.
Support FC-YHQB-9VJN, beta60/code60, API31, WIFI, CONNECTED, capture open,
AWG SUCCESS. Ring128 events:127 DNS_PROBE_OK and one READINESS /
NATIVE_VALIDATION_FAILED at14:55:44.414UTC; bootstrap_directory NOT_USABLE.
Last exported event14:55:44.552UTC. No incident snapshot, local ACK receipt or
native failed-predicate detail in this bundle. Event fields are typed/allowlisted;
no extra free-form event data, credentials, keys, room/destination URLs or raw DNS
history observed. Export kept outside Git; documented only safe summary/digest.

Server readback14:58:23UTC now shows a newer tester challenge14:55:46UTC and fetch
14:55:47UTC, revision1/minimum_crl1570, expiry15:10:15UTC, no ACK. Exported native
failure precedes this fetch: cannot assert it explains rejection of the new payload
or the original14:39 attempt. Classification narrowed to READINESS validation, not
AWG failure or proven censorship. Exact signature/certificate/binding/time predicate
remains unknown. Code publishes negative import receipts too, so native failure
alone does not explain why no negative ACK was accepted. Need newer client receipt
and correlated ACK/native evidence before claiming root cause or changing production.
No grant reset, new enrollment, transport/code changes or further cohort expansion.

Second export `FamilyConnect-diagnostics(2).json`,41192 bytes, SHA256
`88716e6aaec35fa8f234124d9124879e3b9bf44aa8c2b54e83cf3890b7f3b80d`:
same Support/build/connection/incident, AWG SUCCESS/CONNECTED/WIFI, ring126 DNS successes
and two NATIVE_VALIDATION_FAILED events (14:55:44.414 and15:01:05.578UTC).
Last event15:01:53.232UTC; no incident or raw readiness receipt. Privacy allowlist PASS.
Server readback15:04:09UTC: tester challenge15:01:07/fetch15:01:08, revision1,
minimum_crl1580, expiry15:10:15UTC, no ACK. Owner continues normal READY/ACK refresh.

The repeated event/fetch pairs are consistent with the tester clock lagging by a
few seconds, but export correlation lacks provisioning request IDs, so this remains
a hypothesis requiring clock verification, not a proved pairing/offset. Native
ValidateDelivery rejects delivery.IssuedAt > now.Unix() without skew allowance;
server negative ACK validation also requires observed_at >= challenge_at. These
two checks would explain both symptoms under device clock lag. RU timedatectl
reports NTPSynchronized=yes; its sampled epoch lies within the local SSH request
window (not a precision phone clock measurement). Next controlled check: tester
automatic date/time synchronization and normal foreground provisioning. Do not relax
time validation, reset secure state or alter the published artifact based on this
hypothesis. No production mutations in this diagnostic step; FIELD remains blocked.

### Tester readiness resolved after clock synchronization

User confirmed automatic-time action complete. Read-only production verification
2026-10-03 15:11:19UTC finds FC-YHQB-9VJN normal challenge/fetch15:10:06UTC and
signed receipt accepted15:10:07UTC: READY / ACK_RECEIVED, provisioning/bootstrap
PRESENT_VALID, orchestrator_usable=true, failure_reason NONE, Android0.1.18-beta60/60,
revision1/minimum_crl1597, expiry15:25:02UTC. The previous missing-ACK/native-validation
blocker is resolved. Clock correction followed by successful retry supports the
clock-skew diagnosis; no exact offset measurement or extra native predicate trace
is claimed. No validation relaxation, production code change or secure-state reset.

Admission readback15:11:18UTC confirms exact owner FC-4D8Q-REEG + FC-YHQB-9VJN,
2/3, no wildcard; registration/invitation/Support mapping/owner grant/audit fingerprints
identical to the admitted checkpoint. Inventory28 total/24 non-revoked/4 revoked.
Owner also currently READY/ACK_RECEIVED. Safe receipts are the ignored
`field60-tester/after-clock-*-179104027*.json` files. No production writes or pushes.
Tester now has accepted restricted readiness; Auto remains free to prefer normal
AWG/TCP. This does not prove an actual Telemost session or broader FIELD completion.
Before restricted transport testing, recheck/renew gateway and directory leases:
last recorded gateway certificate expiry15:14:31UTC is independent of tester receipt
expiry15:25:02UTC. Existing renewal only; no expiry bypass or automatic cohort widening.

### Third export: real connection incidents and gateway-only repair

`FamilyConnect-diagnostics(3).json`,83713 bytes, SHA256
`7e5aa129cd2b0628f3b61e8b4b628dd34560005ed6062310d2949a19dbdef4f0`.
Contains bounded ring plus incident, Support FC-YHQB-9VJN, beta60/API31/WIFI.
After deduplicating shared events, four complete new connection starts and one
older partial connection are visible. Full observed outcomes:

| UTC result | Outcome | Duration |
| --- | --- | --- |
|15:11:09.264|CONNECTED / AWG|7036ms|
|15:15:35.196|FAILED / AUTH after restricted STARTUP_FAILED|62119ms|
|15:16:54.469|FAILED / AUTH after restricted STARTUP_FAILED|62099ms|
|15:17:36.104|CONNECTED / AWG|7082ms|

Failed paths include AWG/TCP NETWORK outcomes with failed DNS probes, then restricted
READY and BOOT_CACHE_READY/BOOT_CARRIER_READY before STARTUP_FAILED. Snapshot at
FAILED retains vpn_capture_open=true, readiness READY, directory USABLE, outcomes
AWG NETWORK/TCP NETWORK/restricted AUTH. This proves snapshot/correlation operation
and capture-state retention, not packet-level no-leak or successful restricted traffic.
Final ring state CONNECTED/AWG, readiness UNKNOWN after connection reset; do not
interpret that metadata alone as loss of cached provisioning. This third ring has44
successful and18 failed DNS probes, plus typed lifecycle/restricted events;
earlier second-export counts are separate. No new native validation failure observed.
Strict schema/event-field privacy checks PASS; no traffic payload/raw destination data.

Read-only NL check15:20:41UTC proves gateway certificate expired15:14:31UTC while
bootstrap PID3205461 remained active/running, no restarts. Directory still valid
until15:29:22UTC, illustrating that a valid client directory is not proof of a valid
live gateway certificate. Expiry precedes both restricted failures; classify the
confirmed blocker as GATEWAY credential expiry, with client AUTH evidence. Exact
failed-handshake predicate is not contained in export; post-renewal retry is required.
Normal AWG/TCP NETWORK causes remain unproven (no censorship claim).

Executed the already accepted credential-only renewal, not an application patch:
`/tmp/fc-field60-gateway-renew.py` adapts only operator assertions from historical
owner-only to the explicitly admitted two devices/current delegation3. Both admitted
grants checked; all26 non-admitted registrations denied. No grant/enrollment writes.
Issuer3/owner grant3/tester grant1 unchanged. Monotonic CRL1620; same gateway/issuer
keys, Family, minimum revision1 and accepted one-hour gateway certificate lifetime.
New gateway certificate15:22:33–16:22:33UTC. Native positive/negative validation PASS;
atomic publication/service-readable979:979/0600 verified before reload.

Restricted bootstrap only restarted15:22:36UTC; new PID3231001, fresh directory issued
15:22:39.140368726UTC, expires16:17:36.983028339UTC. Existing bounded acceptance PASS,
actual control TLS certificate matches renewed material, issuer/hostname/expiry PASS,
35-second stable PID/no-restart check PASS. Ordinary sync timer restored; natural sync
already delivered exactly the new directory to RU at15:23:52UTC, no extra sync trigger.
Registration/invitation/Support mapping/grants/operator audit/admission and ordinary
HTTP/AWG/TCP service PID/start fingerprints unchanged before/after. Exact owner+tester,
2/3, no wildcard; inventory28/24/4. No production APK, runtime binary, source, catalog,
landing or admission modification. No commit/push. Protected backup/receipts on both
hosts: `restricted-materials-stage-20261001/field60-cycles-gateway-20261003`; local
ignored evidence `state-client-build/field60-cycles/gateway-renewal/`. Never roll back
to expired credentials or lower revocation floors; recovery uses existing renewal.

An earlier read-only broad preflight failed with a redacted remote error before any
mutation; its exact cause remains uninvestigated and it is not a service-health verdict.
Subsequent focused certificate/unit checks and guarded renewal completed successfully.
At15:23:56UTC tester's latest ACK still belongs to15:10 material (expiry15:25:02UTC),
owner's latest15:03:48 ACK has expired15:18:33UTC. Require fresh ordinary provisioning
and device-side Auto retry after gateway reload; do not claim post-repair restricted
success or FIELD completion. No additional tester selection/expansion. Manual gateway
lease renewal is still operationally required before its next expiry; no automatic
renewal or lifetime policy change introduced. Documentation diff whitespace check PASS.

## beta60 publication — 2026-10-03

User explicitly authorized publication after evidence checkpoint
`8316f85a34e99f57702befb4d9610ac6100861a9`. Same FIELD-1 milestone; Stage5N CLOSED,
DIAG-1A PASS. Acceptance-only restrictions below are historical, superseded only
for the authorized publication, not for FIELD widening or new roadmap work.

### Immutable public identity

- Package `com.familyconnect.app.friends`, `0.1.18-beta60`, versionCode60, ARM64.
- Build source `5c740f2d05f725ee1bcbe63a41f886605d4c7ac4`.
- Public URL: https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta60.apk
- Independently downloaded outside the build workspace:49412987 bytes, SHA256
  `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
- Public APK certificate SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- No APK rebuild, APK resigning, overwritten version or private acceptance component.
  Historical beta59 remains unpublished: public route404 before and after.

### Catalog and public paths

Production `/updates/android-friends-v2.json` equals committed
`updates/android-friends-v2.json`, SHA256
`f042becae969474ed7ebc28890a635ae5812769a3203fa6d75cf18fd22060006`.
Existing offline Ed25519 root; domain `family-connect/android-update/v1`,
channel `android-field`, payload schema1, sequence1, version60. Issued2026-10-03
13:34:01UTC, expires2027-01-01 13:34:01UTC. minimum_supported_version1,
mandatory_after0: optional, no forced legacy shutdown. No new signing trust root.
Catalog signature prepared only after hosted platform acceptance and verification
of public APK bytes. Key never uploaded. HTTP cache policy no-store.

Legacy `/updates/android-friends.json` also references exact60 bytes, preserving
the existing beta51 Settings checker. Android production verifier accepts the live
signed catalog and an identical repeat; rejects a higher replay floor, same-sequence
different digest, expired lease, future issuance and signature tampering. Package,
expected signer and downloaded APK SHA verified on the owner Android runtime too.

Both `/invite/` and `/i/` return updated page SHA256
`014ebdbd78966185b1d99823ae5e7e0251369dde26059bc82957e454ea99a49f`.
Only Android display version and filename change51→60; exact text comparison proves
Windows/Linux URLs, invitation-token handling and `familyconnect://invite/` logic
unchanged. Script/style CSP hashes independently verified against the actual response.
No invitation or registration created for testing.

### Post-publication Android acceptance

- Unchanged historical beta51 `AppUpdate.check()` source executed on the owner's
  Android runtime via a temporary shell DEX probe: real production HTTPS discovery
  returns code60, which is newer than51. This is legacy-checker execution, **not**
  an installed51 UI test or a claim that another user updated. Owner not downgraded.
- Owner60 real Settings → Check for updates reports **You have the latest version**.
  Live download/hash/package/signer verification and same-version reinstall rejection
  pass. Two private instrumentation tests pass; accepted release APK unchanged.
- Initial historical UI helper failed its button lookup: system/application context
  ru-RU differs from activity's selected English. A private test-only locator uses
  the displayed activity locale; same product action/result assertion passes. No
  production fix, bypass or release APK change. Direct shell touch injection was
  rejected by MIUI; in-app instrumentation click verifies the real control instead.
- Existing device-status authentication PASS, activated/enrollment/UID10283 and
  encrypted Device Identity fingerprint unchanged. Support retrieval returns the
  existing inventory alias FC-4D8Q-REEG; visible/Copy/restart PASS. No reenrollment.
- Temporary instrumentation package and shell probe removed after verification;
  no credentials, private keys or user traffic exported. Release-test private APK
  was never uploaded/published. Local publication receipts are ignored state only.

### Inventory, admission and readiness

Read-only production before/after fingerprints match for registrations, invitations,
Support ID mapping, restricted grants, admission bytes, operator audit and deployed
HTTP artifact. Inventory28 records,24 non-revoked,4 revoked,28 assigned aliases.
Platform/version known1 (Android beta60/code60), unknown27; no inferred platform or
version. Only one known device is on60. Update-offered/pending/manual-required counts
are unknown: this infrastructure does not provide fleet delivery/install receipts.
No all-users-updated or DAU claim. Legacy clients without a checker must download once
from their normal invitation link, install over the app, never uninstall/clear data.

Admission remains exactly existing owner1, no wildcard, cap3. Deployed operator
artifact SHA `b6fe9220590524905cd98580c083bfd985d80cd5d01391ae7c2b5c4152c995b7`
unchanged; cap and audited enable/disable logic verified. No operator action,
additional tester selection, grant change or automatic24-device admission.

Readiness is **last-observed EXPIRED_ON_IMPORT / ACK_PENDING**, not fresh READY.
Encrypted state/decryption preservation is not readiness renewal. No restricted
transport test was attempted during publication. Before future restricted FIELD
use, restore valid material through existing provisioning and obtain fresh accepted
readiness; do not bypass expiry or reopen Stage5N.

### Deployment scope and rollback

Changes are restricted to one immutable APK, exact nginx download allowlist entry,
two Android catalogs, Android landing text and its CSP hashes. Existing HTTP/support,
activation, networking, enrollment, inventory and admission implementations unchanged.
The first public GET after file upload returned404 because nginx uses exact allowlist
routes. An initial route-patch preflight caught a nested-block match and restored
the original configuration **before reload**. Corrected exact block insertion passed
`nginx -t`; successful public download preceded catalog signing. No invalid config
was activated. Both final publication/landing config tests and reloads passed.

On-host backups under `state-product-https/config`: nginx files
`.before-beta60-download`, `.before-android-update-60` where changed, and
`.before-beta60-landing`; legacy catalog `.before-android-update-60` and
`invite.html.before-beta60-landing`. Public release inputs kept at `release-beta60/`.
Rollback must never replace published60 bytes or distribute59. To withdraw discovery,
coordinate a higher-sequence signed policy/catalog with the existing offline root;
do not replay sequence1 with different bytes or restore an older signed sequence.
For emergency route/landing withdrawal, restore only the targeted release changes,
validate nginx, reload, retain APK evidence and preserve all identity/admission data.
Renew the signed catalog before expiry. No release tag or unrelated desktop release.

Hosted acceptance remains the already-green runs documented below; this publication
changes no Android/Windows/Linux implementation. Public signed catalog, landing and
documentation form the task-owned release checkpoint; unrelated VPN-health edits
are excluded. Stop after publication verification, before FIELD widening.

Final local checks: `tests/test_field_release.py` and `tests/test_sign_update.py`
9 PASS; documentation checker11 files/600 links/0 errors; whole-index guard1702
entries/0 blocked files; `git diff --check` PASS. Final independent public re-download
and installed owner APK SHA match8ee59352; public signer matches67a90d1, private test
package absent. No normal app uninstall, clear, reenrollment or transport change.

Publication checkpoint `741aac3d18c9398c0b8c01dfc0327954ff160500` pushed to
`origin/main` from evidence HEAD8316f85. Thirteen task-owned paths only: public
signed catalog, Android landing and release/user documentation. No tag, GitHub
binary release, production-code change or unrelated VPN-health content included.
This follow-up records that push; the immutable APK build source remains5c740f2.

## beta60 final acceptance — publication gate READY

Same FIELD-1 milestone; Stage5N CLOSED. All requested platform acceptance gates are
green. DIAG-1A PASS. **Stop before catalog signing/publication/landing/FIELD widening.**

### Immutable candidate

- Android `0.1.18-beta60` / versionCode60, `com.familyconnect.app.friends`, ARM64.
- Clean committed build source `5c740f2d05f725ee1bcbe63a41f886605d4c7ac4`.
- APK SHA256 `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`;
  49,412,987 bytes; signer SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Local immutable candidate: `state-client-build/field60-r2/artifacts/FamilyConnect-Test-0.1.18-beta60.apk`.
  Source inventory SHA256 `2b30498d8c015bb8853e3cefd1a17ad0fd792a39c6a5747e87fa5906ea908654`.
- Final hosted source `4963c7c3f46d2d55e87ea680c56982d5d7af73b7`; differences from
  build source are test harness/regressions/docs only, no main Android/Gradle/native
  changes. Candidate was not silently replaced after owner acceptance.
- Historical59 remains SHA6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148,
  untouched and unpublished. No59 filename/path reused for60.

### Three blockers resolved

1. **Auto TCP production defect:** builder omitted fd79:fc::2/128 while routing::/0.
   Added exactly that address beside10.79.0.2/32; DNS1.1.1.1,MTU1280,routes/native
   socket protection unchanged. Source contract strengthened and separate runtime
   builder assertion checks both sources/default routes/DNS/MTU. Existing Auto traffic
   test unchanged: IPv4 AND IPv6 bind/connect/HTTP acceptance now passes through real
   emulator TUN/native TCP/synthetic peer, not an IPv4 fallback or relaxed assertion.
2. **Manual AWG harness defect:** asynchronous connect could encounter failed=true
   retained from the previous off/revoked session. Shared wait helper mistook that
   stale flag for the new attempt failing, entering cleanup prematurely. Cleanup
   used stopService then immediate profile clearing, masking the primary exception
   with the legitimate active-VPN mutation refusal. With full Auto now passing,
   5c740f2 additionally exposed premature foreground-service teardown in the next
   AWG test. Helper now rejects active failures, not stale off-state failure, while
   retaining exact requested-state success and30s failure deadline. Manual harness
   logs primary outcome, VPN/health/requested/active/profile-present state, waits for
   normal disconnect and idle ownership, and preserves cleanup failure as suppressed
   when primary fails. Production AWG/service/profile authorization unchanged.
   Final runtime12:53:06UTC: scenario PASS; screen-off5s, UDP outage20s, recovery6ms,
   explicit disconnect during outage terminal. Before cleanup: primary=PASS, off/off,
   requested=awg,active=awg,vpn=false,profile_present=true. Cleanup PASS12:53:07UTC.
3. **Windows2022 readiness race:** installer Native.Install returns after `sc start`
   accepts the request; old test required Running in a single immediate observation.
   Final lifecycle proves installer exit0 can coincide with **Start Pending**, not a
   broken installation or failed preserved state. Old broker PID5304; SCM stopped
   12:48:12.060UTC, deleted/recreated with unchanged Auto/LocalSystem/image path;
   installer return snapshot12:48:17.885 reports Start Pending/new PID7016. Bounded
   readiness sees Running and authenticated status/request/invalid-activation rejection
   PASS at728ms. Requires PID different from pre-upgrade, start time after upgrade,
   and the same PID still Running after probe. Maximum60s with200ms polling; no fixed
   startup sleep. Sentinel/runtime/broker checks retained. Production Windows code
   unchanged. Both normal Windows and2022 compatibility pass, twice after this change.

### Owner in-place evidence

Owner Redmi31ce63ba updated at12:42:51UTC with `adb install -r`, never uninstalled,
cleared or re-enrolled. UID10283, ceDataInode601521, firstInstallTime2026-09-19 unchanged.
Pre/post instrumentation snapshots match all three encrypted files byte-for-byte
(identity, normal configuration, restricted readiness) and enrollment fingerprint.
Identity/readiness decryption, activation and existing signed device-status PASS.
Existing production-bound Support ID `FC-4D8Q-REEG` visible, Copy matches, survives
process restart; no device-generated alias or replacement registration.

Normal product UI: Auto selectsAWG in7.265s, manualAWG1.509s, manualTCP1.259s;
VPN present and test HTTPS200 for each. No normal-candidate exhaustion used on owner.
Owner Auto TCP fallback was NOT forced; dual-stack TCP traffic evidence comes from
the emulator's existing synthetic dual-stack contract, not a claim that the owner's
live network exposed fd79:fc::1 or naturally forced TCP fallback.

Both typed CONNECTING→FAILED and RESTORING→FAILED DIAG snapshots and Android share
flow PASS.4719-byte bundle SHAe7e09b80b292e2adba783b8c4ada799d561e0ee3fbb0ad56f4755f7f22efa4aa;
closed schema/event bound128, no credentials/keys/tokens/room URLs/traffic or raw DNS
history,0 findings; no recipient selected/upload. Five existing safe instrumentation
methods PASS. Only synthetic diagnostic artifacts and separate test package removed.
Pulled installed60 matches candidate SHA/signer; private acceptance components absent.
Final ordinary About UI confirms60/Support ID/Copy after restart, VPN off/Auto retained.
A delayed final UI capture initially found a different app screen; immediate targeted
About readback passed. This was not substituted for the actual successful Copy test.

**Readiness limitation, not hidden:** initial encrypted state was preserved exactly
and decrypts. Later normal prewarm reports EXPIRED_ON_IMPORT/NOT_READY/ACK_PENDING;
no fresh restricted readiness or restricted connection is claimed. No server renewal,
expiry bypass, new enrollment or admission change was made. Existing material must
be valid before any later restricted field use. This does not invalidate the verified
in-place data-preservation gate or the normal transport/DIAG acceptance.

### Required hosted gates

| Gate | Commit | Run / job | Result |
| --- | --- | --- | --- |
| phase0 pytest/cargo + whole-index guard |4963c7c|[37123699367](https://github.com/Joker20380/family_connect/actions/runs/37123699367),111204679104|PASS|
| Docker build/failover/auth/offline/revocation |4963c7c|same run,111204679027|PASS|
| Linux-control pytest/GTK/extracted packages |4963c7c|[37123699363](https://github.com/Joker20380/family_connect/actions/runs/37123699363),111204679055|PASS|
| Android wire contract |4963c7c|[37123699362](https://github.com/Joker20380/family_connect/actions/runs/37123699362),111204678800|PASS|
| Linux client |4963c7c|[37123699385](https://github.com/Joker20380/family_connect/actions/runs/37123699385),111204679040|PASS|
| Android emulator + runtime control conformance |4963c7c|same run,111204679073|PASS, including steps15 AND17|
| Windows client, running-service upgrade + UI |4963c7c|same run,111204679067|PASS|
| Windows2022 compatibility, identical installer upgrade |4963c7c|same run,111205584991|PASS|
| Windows control, explicit rerun after fixes |ef554e7|[37120091189](https://github.com/Joker20380/family_connect/actions/runs/37120091189),111206327208|PASS|

Windows-control reruns its prior commit because its workflow path filter is unrelated
to these changes. `git diff ef554e7..4963c7c -- clients/windows/Core clients/windows/Tests
tests/vectors scripts/ci_release_fixtures.py .github/workflows/windows-control.yml`
is empty: exact scoped control inputs identical, not an assumed cross-platform PASS.

Final Android artifact11274129354 ZIP SHA740c8ef1b635d5df490fefa75ed13ecfa2c3710da506823e079cd96715c6b51c;
Windows compatibility11273854400 SHA5832f627dc547db05350f12f03a995d2fc5235beced0ea7fc4e41079c58898d2.
Both downloaded/hash-verified. Android summary60 variant cases/0 failures;32 distinct
methods actually execute successfully. Existing variant/live-production opt-in skips
are not newly added/waived release failures and are not counted as passes. Auto/TCP/
AWG, builder and required control-runtime methods executed; Keystore/AtomicFile/
outbox restart uses distinct processes and passes. No required gate skipped or xfailed.
Earlier failing runs371224* and37122729324 remain historical evidence, not final PASS.

Local clean export: Friends JVM226, Debug JVM231, standalone control JVM163 PASS,
lintFriends/instrumentation compile PASS; focused Python15 PASS. Package/JNI symbol/
source/secret checks PASS;1074 signed archive entries scanned with0 findings and the
previously reviewed stdlib non-secret false positive retained. No acceptance hook
packaged. No production change beyond Auto TCP address and Android version metadata.

### Boundary and rollback

No update catalog signed, no APK uploaded to production, no landing edit, no release
tag, no grant/admission/operator mutation. Existing owner-only/no-wildcard/cap3 state
not changed; no new production inventory count inferred. Public Android remains51.
beta59/60 and signed-v2 download routes remain unpublished; full public51 bytes are
checked separately in local public-readonly evidence. All source pushes use non-release
commit messages, never `Release ` or a release tag. Unrelated VPN-health work preserved.
Owner stays on accepted60; do not uninstall, clear data or attempt downgrade to59.
If a new production fix is needed, create another explicitly identified candidate and
repeat affected acceptance; never silently replace this accepted SHA.

## beta60 authorized continuation

Starting HEAD9351e07; beta60/code60 production source now assigns the missing Auto
TCP IPv6 TUN address. DNS1.1.1.1,MTU1280,both routes and socket protection retained.
Source contract now requires both address families; separate runtime builder test
checks addresses/routes/DNS/MTU. Existing Auto dual-stack traffic test unchanged.
Manual AWG primary/cleanup outcomes are separately logged, with safe state fields;
cleanup waits for disconnect and idle operation ownership before profile deletion.
Hosted reproduction is pending; no claim of resolved primary AWG cause yet.
Windows compatibility remains pending. No beta60 signed artifact or owner result
yet. beta59 SHA6d13720 remains preserved/unpublished; public Android51 unchanged.
No signing of update catalog, publication, landing, admission or FIELD expansion.
Candidate rollback means keep historical installed59 while blocked, never clear
data or install a lower version. Final source/artifact/hosted evidence follows here.

Initial candidate source f3a5d43 pushed without release trigger. Local regression13
PASS; local build caught a hidden Android SDK LinkAddress constructor in the new
test only; corrected to compare public address/prefix accessors. No APK signed yet.
Windows source trace: Native.Install returns after `sc start` (SCM request accepted),
not a Running/API-ready barrier. Upgrade test previously sampled service once.
Test now records pre/post SCM state/PID/configuration, background transitions and SCM
events, and requires a different newly started PID plus authenticated broker API
status/request/activation within60s. Polling is bounded, not a fixed startup sleep.
Sentinel/runtime/broker postchecks remain. Production Windows code unchanged;
hosted lifecycle evidence is still needed to confirm the observed race.

Hosted5c740f2 client37122729324: Auto's unchanged dual-stack/fallback/exhaustion/
cancel/revoke scenario PASS; new address/route builder check PASS. Windows main and
Windows2022 compatibility both fully PASS, including stronger new-PID/API checks.
Android next AWG test crashes during premature cleanup: the shared wait helper reads
the previous revoked session's failed=true/off before the asynchronously queued
connect is delivered; its finally stops a foreground service before promotion.
The helper now fast-fails only a non-off failure, retaining the exact expected-state
assertion and30s deadline. An actual start failure ending off still fails that deadline,
not silently passes. Manual AWG scenario awaits a complete hosted reproduction.
Only test code changed after the signed candidate source5c740f2. beta60 candidate
SHA8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104,
signer67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a,
package com.familyconnect.app.friends. Clean ARM64 export/JVM/lint/package/secret
checks PASS; no private acceptance classes in APK. Owner installation pending.

## Android Auto runtime diagnosis — artifact stop boundary

**FIELD-1 publication remains BLOCKED; DIAG-1A remains PASS.** Sequential work
stops at the user's explicit boundary: a required production Android correction
would invalidate the accepted APK as the final release artifact. Stage5N remains
CLOSED; no new milestone or physical-acceptance gate is introduced.

Starting and ending HEAD: `9351e07f1c9f1e6c5b813df62b6d3404a3c60d90`.
This continuation changes documentation only; no commit/push or hosted rerun.

### Android Auto: confirmed production defect, not emulator assumption

Evidence is from the requested [client run37120091287](https://github.com/Joker20380/family_connect/actions/runs/37120091287),
Android job111194358923, source `ef554e75e54d1193ada96086480eac1087d6ca3b`.
Fetched `android-awg-app.log` from artifact11273242837 with ZIP member CRC verified;
local ignored evidence `state-client-build/field59-ci/android-37120091287-app.log`,
10,874,469 bytes, SHA256
`12d540a5e9246157dbe8df2fc38ab6b164ab5e19da865af2c0721a4a0259e893`.
These are existing hosted runtime observations, not a newly executed acceptance.

- Command: `python3 -u pilot/android-awg/run.py`, invoking
  `:app:connectedDebugAndroidTest`. `AutoRuntimeTest` line47 waits for Auto TCP
  selection/connected state, then calls `TcpRuntimeTest.traffic`.
- Requested source is `fd79:fc::2`, destination `fd79:fc::1:18080` (IPv6 address
  fd79:fc::1, port18080). The IPv4 half uses10.79.0.2 and198.19.1.1:18080 first.
  Line23 binds before connecting; the stack explicitly fails in `Socket.bind` /
  `IoBridge.bind`, not TLS, peer connection, DNS or a remote route.
- Emulator underlay inventory in ConnectivityService: wlan0 has10.0.2.16/24 and
  an fe80::/64 link-local address; eth0 has10.0.2.15/24. Underlay default route is
  via10.0.2.2 and DNS10.0.2.3. The requested fd79 source belongs on the VPN, not on
  these underlays; a public IPv6 underlay is not required by the synthetic TCP peer.
- 11:43:33.992UTC (log64632–64633): retained tun0 gets10.79.0.2/32 **and**
  fd79:fc::2/128. Earlier WG/AWG candidates likewise have their configured v4/v6
  source pairs; Auto has not globally disabled IPv6.
- 11:43:38.053UTC (log64772): TCP replacement tun1 gets **only10.79.0.2/32**.
  netd adds tun1 to network102, removes tun0, adds0.0.0.0/0 and::/0 routes on
  tun1, and removes the old fd79:fc::2/128 route (log64775–64794). Routing ::/0
  does not assign an IPv6 source address. The sole assigned fd79 source disappears
  when the old TUN is replaced; no IPv6 address is added to the TCP TUN.
- 11:43:44.978UTC (log65577–65583): EADDRNOTAVAIL in TcpRuntimeTest23/AutoRuntimeTest47.
  The finally cleanup has already restored a dual-stack blocking tun0 at11:43:44.233;
  that later restoration must not be mistaken for the failing TCP interface state.
- Control evidence from the **same emulator/run**: manual TCP establishes both
  addresses at11:44:22.992UTC and subsequent TCP sessions;11:45:09.962UTC logs
  `TCP PASS: 18 REALITY HTTP, 3 OS DNS, 12 WG/AWG UDP, 5 stops, cancel and revoke`.
  Its shared traffic helper exercises both address families. Therefore an emulator
  lacking IPv6 support or a universally invalid test source is not the explanation.

Source trace: `ConnectivityOrchestrator.run` tries normal candidates and calls
`AutomaticConnection.open`; that invokes `AutomaticNormalEngine.up` then IPv4-bound
`VpnHealth.check(normal.source)` before emitting CONNECTED. In
`AutomaticNormalEngine.java:25–30`, TCP sets10.79.0.2, installs both default routes,
but omits `.addAddress("fd79:fc::2",128)`. `AutomaticVpnOwner.replace` establishes
the replacement and closes the previous TUN; prior addresses do not carry over.
`TcpTunnelEngine.java:17–18` and the retained-owner builder explicitly add both
addresses. Both TCP engines pass the established TUN descriptor to `NativeTcp.start`;
`pilot/android-tcp/tcp-android.go` duplicates that descriptor and protects the outer
TCP socket to the configured peer. It does not assign missing Android interface
addresses. The failed inner IPv6 bind occurs before its connect reaches this backend.

**Exact required fix, identified but NOT applied:** add fd79:fc::2/128 to the Auto
TCP VpnService.Builder, matching the manual TCP address contract, while retaining
both routes, socket protection, profile restrictions and existing dual-stack traffic
assertions. This is shared production source compiled into Friends, not test-only
or an emulator provisioning setting. The Android/native source diff between accepted
APK source5abc2da and current HEAD is empty; the defect is in the accepted source too.

**Regression status:** no test altered/added or failure waived at this stop boundary.
The existing Auto dual-stack runtime test already exposes the defect. On authorized
resumption, add a focused Auto TCP LinkProperties address/route assertion before
the existing dual-stack traffic check, then require the entire emulator and runtime
control gates to PASS. A test-only IPv4 fallback would hide this production defect
and is explicitly rejected. No claim of corrected dual-stack PASS is made.

### Remaining sequential blockers (not advanced past the stop boundary)

| Gate | Root cause / fix / regression status | Latest hosted evidence | Production changes |
| --- | --- | --- | --- |
| Manual AWG stability | Primary result still obscured by cleanup; actual scenario cause unproven. No harness fix yet. Required follow-up: preserve both results and pre-cleanup VPN/profile/transport state, then reproduce; do not relax active-VPN profile guard. | Same run/job: ManualAwgStabilityTest82, `Disconnect VPN before changing profiles` | None |
| Windows2022 compatibility upgrade | Restart failure observed; SCM/process/readiness cause unproven. No arbitrary sleep or other fix/test change. Compare passing normal Windows path and instrument lifecycle before choosing bounded authoritative readiness polling. | Same run: compatibility111195231706 FAIL; normal Windows111194359044 PASS, including running-service upgrade | None |

All previous terminal hosted results in the following fixture-repair section remain
the latest evidence: Linux client/control, Windows main/control, Android wire,
phase0, Docker failover/auth/offline/revocation and whole-index guard PASS. Android
emulator and Windows compatibility FAIL; Android runtime-control conformance was
not executed after the failed emulator step. No full-green or accepted completion claim.

### Artifact and safety boundary

Rechecked with SHA256, `apksigner verify --print-certs`, and `aapt dump badging`:
`com.familyconnect.app.friends`, `0.1.18-beta59`/59; APK
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`, signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Bytes and signature remain intact, but **that artifact cannot represent the required
production fix and is not eligible for publication under the dual-stack gate**.
No rebuild, APK replacement, device install/reset, production deployment, admission
mutation, catalog signing, public publication, landing change, tag or push occurred.
No new production inventory query: last authoritative owner1/no-wildcard/cap3 and
Support/enrollment/backfill evidence remain unchanged, not newly measured here.
Previously accepted DIAG-1A and owner results remain historical PASS evidence.
Unrelated VPN-health edits are preserved. No runtime rollback is needed because no
runtime change was applied; documentation-only additions can be reverted separately.

Next action requires authorization to change the Android candidate/release identity,
then a clean committed build, renewed owner acceptance and the remaining sequential
hosted gates. Existing publication prohibition remains in force even after a rebuild.

## Hosted fixture repair — 2026-10-03

### Final observed result

**Fixture/provisioning repair PASS; FIELD-1-RELEASE BLOCKED; DIAG-1A PASS.**
Final pushed CI source `2b3c997e1df158c538525122554d0e15c2959fd5`. Platform runs use
`ef554e75e54d1193ada96086480eac1087d6ca3b`; the subsequent commit changes only Docker
test Go-cache provisioning and this report, not platform application/test sources.
Final evidence documentation is retained locally without another CI-triggering push.

| Hosted gate | Source | Run / job | Terminal result |
| --- | --- | --- | --- |
| phase0 full pytest + cargo |2b3c997|[37120492530](https://github.com/Joker20380/family_connect/actions/runs/37120492530),111195481064|PASS|
| Docker build + failover/auth/offline/revocation |2b3c997|same run,111195481345|PASS|
| Whole-index guard |2b3c997|same run,111195481064 step4|PASS; local1700 entries/0 findings|
| Linux-control pytest/GTK/extracted bundles |ef554e7|[37120091177](https://github.com/Joker20380/family_connect/actions/runs/37120091177),111194358632|PASS|
| Windows control |ef554e7|[37120091189](https://github.com/Joker20380/family_connect/actions/runs/37120091189),111194358497|PASS|
| Android wire contract |ef554e7|[37120091156](https://github.com/Joker20380/family_connect/actions/runs/37120091156),111194358466|PASS|
| Linux client |ef554e7|[37120091287](https://github.com/Joker20380/family_connect/actions/runs/37120091287),111194359023|PASS, all packaging/UI steps|
| Windows main client |ef554e7|same run,111194359044|PASS, all installer/UI steps|
| Windows2022 compatibility |ef554e7|same run,111195231706|FAIL, upgrade broker restart|
| Android client |ef554e7|same run,111194358923|FAIL, emulator; runtime-conformance step not executed|

The release job is skipped by the existing no-release-trigger policy, intentionally;
this is not a skipped acceptance test. No acceptance skip/xfail/bypass was added.
The original three failure classes are repaired, but **all hosted release gates are
not green**, so the final publication gate is NOT READY.

Remaining release-blocking commands and evidence:

- `python3 -u pilot/android-awg/run.py` → `:app:connectedDebugAndroidTest`:
  `AutoRuntimeTest.automaticFallbackHealthLossExhaustionCancelAndRevoke` fails at
  `TcpRuntimeTest.java:23` / `AutoRuntimeTest.java:47` with
  `java.net.BindException: bind failed: EADDRNOTAVAIL`. The test requires dual-stack
  TCP echo; existing Auto TCP does not assign fd79:fc::2. This is separate from the
  Python fixture defect. Neither networking nor this assertion was changed.
- Same command: `ManualAwgStabilityTest.screenOffOutageRecoveryAndExplicitDisconnect`
  fails at line82 during cleanup with `Disconnect VPN before changing profiles`
  (`ControlOperations.java:43`, `ProfileStore.java:60`). Expected full manual-AWG
  scenario and safe teardown. Cleanup may mask the original scenario failure;
  current evidence does not establish a production AWG defect or a complete PASS.
- `./clients/windows/test-install.ps1 -Stage Upgrade`, Windows2022: line49,
  `Broker did not restart after upgrade`; expected broker Running followed by data,
  runtime and broker checks. Installer log reports success but job exits1. Seen in
  both833ab39 and ef554e7 runs. Root cause beyond this observed native failure remains
  unresolved; not waived based on the passing main Windows job or older run.

Latest Android bounded summary: artifact11273242837,40 instrumentation cases,
2 failures; retained as `state-client-build/field59-ci/android-37120091287-summary.json`.
Windows compatibility artifact11273202392 SHA256
`a17daffe8d94862c9191489aad20fd4e350377af51b9a2907adf12381f660ac3` retains install/upgrade
logs. Private/local evidence paths are ignored; no diagnostic credentials committed.

Release identity reverified, not rebuilt: package `com.familyconnect.app.friends`,
`0.1.18-beta59`/59, APK SHA256
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`, certificate SHA256
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
No Android/carrier/pilot source diff from accepted APK source5abc2da. CI test builds
are not replacements for that signed candidate. No beta key or offline update root used.
Read-only production comparison preserves all registration/invitation/Support mapping,
grants/admission/audit, deployed HTTP and nginx fingerprints.28 records/24 non-revoked/
4 revoked/28 aliases;1 known Android59,27 unknown; admitted owner1/no wildcard/cap3.
No deployment, catalog signature/publication, landing edit or FIELD widening. Unrelated
VPN-health edits remain uncommitted and intact. Rollback is source-only as below.

Starting HEAD `fc2b3efcaabbe75195b869d5586de65c0b0dc55c`; same milestone,
Stage5N CLOSED, owner/DIAG-1A PASS retained. No product source or accepted APK changes.
Publication/signing/landing/FIELD widening remain prohibited throughout this repair.

The successful518-focused local path explicitly supplied `FC_TEST_HTTP_ARTIFACT`,
HTTP SHA, sync artifact/SHA, readiness artifact, immutable historical HTTP artifact,
Go1.26.0 and nginx. Hosted broad pytest supplied none of these; Docker's selective
COPY additionally omitted modules/manifests required during collection. This is a
test provisioning defect, not evidence of three separate networking defects.

`scripts/ci_release_fixtures.py` builds closed fixtures from committed source,
checks source commit and every inventory hash before execution, and independently
enforces historical HTTP SHA460e7520. phase0/Linux-control explicitly seed Go modules
and provision before full pytest. Docker consumes only public `git archive` exports,
restores the exact verified tree/commit without host Git configuration, then builds
fixtures in the test stage before collection. Runtime stage is unchanged. Synthetic
keys remain local test data, never production credentials or persistent secrets.

Three formerly hidden fixture assumptions are corrected without removing assertions:
historical cadence uses the pinned historical server instead of the current server;
current preflight requires the explicit current SHA (no permissive fallback);
missing-module tests explicitly import the selected dependency, including lazy ones.
No skip/xfail/conditional bypass introduced. New tests verify public-only exports,
exact source restoration, hash/commit rejection and deterministic sync ZIP metadata.

Local full provisioned pytest:1691 PASS/26 existing environment-dependent skips,
256.21s; new provisioner tests3 PASS. Logs retained in ignored
`state-client-build/field59-ci/`. Hosted rerun remains pending. The earlier client
run37115119418 is terminal: Windows/compatibility/Linux PASS; Android emulator FAIL,
so Android runtime conformance was not executed and is not accepted.

Rollback is source-only: revert the CI/test provisioner changes if necessary; no
production rollback or device data operation is involved. Public51 remains in place.

### First hosted repair run

Source `833ab39f5697d79464a603dcc40617158f84472f`, pushed without release trigger.
phase0 run37119299194 and Linux-control37119299193 now provision successfully and
collect the full suite; the missing25 fixture errors are gone. Both expose the same
remaining operator ZIP failure: Python3.13 isolated execution cannot import namespace
`control` without directory entries. Reproduced with Python3.13.15 in the existing
CI container: before `ModuleNotFoundError: control`, after explicit deterministic
ZIP directory entries `--help` PASS. No operator semantics or Android sources changed.

Docker now reaches all tests (no collection errors); its remaining environment gaps
are root nginx workers unable to read pytest's private static-fixture directories,
missing `/usr/bin/python3` for service-UID DAC probes and missing `/usr/bin/curl`.
Supply tools; execute root-DAC tests separately as root and full suite as a normal
runner, matching the accepted local/hosted execution identity. Do not chmod private
state, run nginx with extra privileges, weaken assertions or bypass root tests.

The first complete prior Android artifact confirms a distinct release blocker:
`AutoRuntimeTest` calls dual-stack `TcpRuntimeTest.traffic()` although Auto TCP only
assigns10.79.0.2 and retains the IPv6 default route fail-closed; binding fd79:fc::2
raises EADDRNOTAVAIL. Manual TCP's dual-stack test passes. Manual AWG also reports
an asynchronous-cleanup profile-edit refusal. Tests and networking are unchanged;
these are not waived or misrepresented as resolved by the Python fixture fix.
Current rerun's Windows2022 compatibility upgrade also failed its broker-restart
assertion; final repeat and terminal Android evidence still required.

Follow-up source `ef554e75e54d1193ada96086480eac1087d6ca3b`: hosted phase0 full
pytest+cargo PASS and Linux-control full pytest/render interaction PASS (remaining
packaging steps pending at observation). Docker's seeded Go modules must also be
shared explicitly across its root-to-runner boundary; use `/opt/fc-go`, owned by the
test runner, and disable network module fallback after the seed step. Isolated
Python3.13 root-DAC tests22 PASS locally; operator/provisioner regressions21 PASS.

## Support HTTP delivery and owner completion — 2026-10-03

This supersedes the blocked Support/status observations below. Same FIELD-1/DIAG-1A;
Stage5N CLOSED. Starting HEAD40e40bb. Android source remains
`5abc2da4878d38687574776932959db284dd9797`, unchanged signed beta59/code59 APK
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`, signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
No production APK rebuild, networking change, reinstall, identity reset or enrollment.

### Authorized prerequisite deployment

- Before09:47:57UTC: existing28/28 aliases verified; owner admission maps to an
  existing non-revoked enrollment and alias. Neither Android nor delivery allocates
  an ID. Source5e0008c makes support-purpose proof completion lookup-only; a missing
  mapping returns unavailable503 without inserting anything. Regression test proves it.
- Clean committed HTTP export5e0008c:
  `ef9f2faf31ab66e119eb44f95f30aab94b9b6d3da11e36958b4689316e996291`.
  Compared with livead71cadb, exactly3 entries change: Friends access, Support IDs,
  HTTP handler. All restricted/runtime networking modules remain byte-identical.
- Successful deployment09:52:52UTC: existing
  `family-connect-friends-http-candidate.service`/loopback18086, same DB/permissions;
  nginx ordinary regex adds only `device/(status|support)`. Normal/restricted routing,
  limits, grants, admission, AWG/TCP and download routes retained.
- Initial validation command `docker exec family-connect-product-https nginx -t`
  used default `/etc/nginx/nginx.conf` and failed on read-only `/run/nginx.pid`.
  Old artifact/config hashes were verified restored before retry. Correct explicit
  `nginx -c /etc/fc/nginx.conf -t` and same-config reload PASS. No DB rollback.
- Protected rollback files/DB snapshot/receipt:
  `friends-access/support-delivery-5e0008c/` on the authorized RU host. Restore only
  previous HTTP artifact/nginx config if necessary, validate explicit config/restart
  HTTP/reload nginx. Never restore the DB or remove the existing alias backfill.

### Owner and authorization results

- Existing private owner instrumentation runs on the unchanged public candidate.
  Initial cached failure remains unavailable until explicit Refresh; MIUI rejects
  shell `input tap`. Only the separate AndroidTest helper was recompiled to invoke
  the ordinary Refresh button; production APK not rebuilt. Correct Friends test
  variant requires `-PfcTestBuildType=friends`; missing-property invocation compiled
  nothing. All initial failed harness receipts retained, not reported as product PASS.
- `supportVisibleCopiedAndStable`, `existingIdentityStillAuthenticates`, then
  force-stop/new-process Support test PASS. ID equals the **pre-deployment owner
  backfill row**, Copy equals that ID; status validates returned reference against
  the existing vault identity. No new registration/invitation consumed.
- Final09:59:02UTC after uninstalling only `.friends.test`: pulled production APK
  SHA/signer unchanged, UID10283, ceDataInode601521, firstInstallTime unchanged;
  actual normal Settings UI shows ID and enabled Copy. Encrypted identity unchanged
  and decrypts, enrollment active, Auto/off retained, no private acceptance components.
- Fresh readiness receipt on59 READY/PRESENT_VALID/ACK_RECEIVED. The prior owner
  Auto/AWG/TCP HTTPS200 evidence remains valid; no networking changes in this step.
- DIAG both typed CONNECTING/RESTORING failure snapshots plus Android MIUI chooser
  PASS. These are synthetic recorder tests, not forced live transport outages.
  Export4695 bytes SHA256
  `1493c2f0051badb6e3f1ed490be64a8329a65bd29a6ae6771d075f83319d5504`;
  ring+incident both contain the bound Support ID. Closed schemas/bounds/privacy
  checks PASS, zero secret/identity/URL/destination-history findings. No recipient
  selected/upload. Synthetic files/export URI grants and test helper removed.
- 16 paced live HTTPS negative probes PASS: missing/invalid auth400/403, malformed
  JSON400, wrong method405, unknown alias403/unknown lookup path404, unknown Support
  identity403, replay403, existing revoked device challenge403 for both purposes.
  Existing status semantics intentionally preserved: an unknown identity with its
  own valid proof receives200 with registered=false/active=false, **no access and
  no enrollment**, not a claimed403. Isolated real-handler/nginx tests also cover
  revocation after challenge and revoked invitation; no production revocation edits.
- HTTP journal13 lines: zero actual registered identity/secret-pattern matches.
  HTTP body logging disabled; conditional nginx probe log has no body/auth/query.
  Private proof/status/challenge bodies are not persisted in acceptance evidence.

### Inventory, validation and release boundary

At09:57:26UTC all six fingerprints unchanged: devices, invitations, alias mappings,
restricted grants, admission bytes and operator audit.28 total/24 non-revoked/4 revoked,
28 stable aliases; platform1 Android known/27 unknown; version1 beta59 known/27 unknown.
Owner operator lookup: active, Android59, Family ACTIVE, readiness READY, admitted.
Readiness is short-lived; this observation is not a perpetual validity claim.
No operator enable/disable executed; unchanged pinned operator keeps audit and cap3.
Current cohort/admission **1 owner**, additional selections0; never wildcard.
Update-offered/pending and legacy manual-install counts remain unknown, not zero.

55 route/access/Support tests and full518 focused Python tests PASS/0 skipped.
Whole-index false positive resolved by splitting the negative PEM test literal;
the exact assertion bytes and secret guard remain unchanged. No scanner exemption.
Tests checkpoint416d938. Existing APK JVM/native/lint results retained.
Protected evidence: `state-client-build/field59-delivery/`; no keys/DB/proofs in Git.

FIELD-1-RELEASE **BLOCKED by hosted CI**; DIAG-1A **PASS** for the defined owner/local-bundle scope.
Hosted platform CI and artifact provenance/download checks remain release gates.
Production59 signing preparation only: min-supported1, mandatory=false, same offline
root, increasing sequence/lease required. No production signature issued yet.
At10:01UTC full public51 download verified36,456,636 bytes/SHA79a2d286; signed-v2
catalog and beta59 APK routes both404. Unsigned production59 payload prepared from
the exact installed APK (draft sequence1/min1/non-mandatory), no offline key accessed;
refresh sequence/issued_at/expiry after CI. This is not install authorization.
Public beta59 APK/catalog/landing publication remains explicitly prohibited in this
continuation; do not change Windows/Linux links. Source-only push1b791c2 completed
after owner acceptance and explicit push approval. No tag/release-trigger commit,
no release assets/catalog key sent to CI. Unrelated health work remains local.
No FIELD widening. After release authorization, follow the existing tester instructions
below: in-place install, no clear/uninstall, send Support ID, await operator, CONNECT.

### Hosted CI stop: exact outstanding release gates

CI source `1b791c2848961ed485d4f1c8300e01c1ed3fb218` has identical Android/carrier/
Android-native source to accepted APK5abc2da. Hosted verification builds do not
replace/re-sign the accepted6d13720 artifact. Final CI notes are a local documentation
follow-up, not another production deployment or automatic CI retry.

| Gate / command | Observed | Expected | Release blocking |
| --- | --- | --- | --- |
| phase0/tests: `python -m pytest -q` | exit1;7 failed,1583 passed,99 skipped,25 errors. Confirmed `KeyError: 'FC_TEST_HTTP_ARTIFACT'` in readiness packaging fixture setup; additional failures need full triage | exit0 with required source-pinned fixtures available | YES |
| phase0/failover: `docker compose build` → `Dockerfile.control:33`, `python -m pytest -q && touch /tmp/tests-passed` | Docker build exit1; pytest exit2,14 collection errors, including missing public runtime/source paths (`test_sync_acceptance.py`, readiness/runtime tests) | complete public test build context, collection/build success | YES |
| Linux control preview: Protocol/crash/packaging `python -m pytest -q` | exit1;7 failed,1606 passed,76 skipped,25 errors; same confirmed missing `FC_TEST_HTTP_ARTIFACT` setup | fixture-provisioned broad suite exit0 | YES |

Relevant authoritative logs:
- [phase0 tests, job111180337783](https://github.com/Joker20380/family_connect/actions/runs/37115119420/job/111180337783): summary10:05:36UTC.
- [phase0 failover, job111180337993](https://github.com/Joker20380/family_connect/actions/runs/37115119420/job/111180337993): Dockerfile/control collection failure10:03:59UTC; bounded build-log artifact11271198754.
- [Linux control, job111180338081](https://github.com/Joker20380/family_connect/actions/runs/37115119469/job/111180338081): summary10:07:22UTC.

Whole-index guard is **PASS in hosted phase0**, not the cause of these failures.
[Windows control37115119444](https://github.com/Joker20380/family_connect/actions/runs/37115119444)
and [Android Friends wire contract37115119419](https://github.com/Joker20380/family_connect/actions/runs/37115119419)
PASS. [Client builds37115119418](https://github.com/Joker20380/family_connect/actions/runs/37115119418):
Linux job111180338239 PASS (GTK/render/interaction/packaging included); Android and
Windows jobs still in progress at inspection, not claimed accepted. No jobs cancelled
or automatically retried. Broader fixture/Docker issues were not hidden by modifying
networking, removing tests, or marking skipped tests as acceptance.

No production59 signature/catalog/APK/landing publication. Next work: triage and
repair CI fixture/context wiring, finish hosted platform acceptance and verify
downloaded artifact provenance, then offline signing **only when authorized release
gates pass**. Publication remains subject to the user's explicit hold; owner-only
admission/cap3 retained.27 other registrations still have unknown version/platform,
so neither automatic adoption nor a numeric legacy manual-upgrade count is claimed.

## Owner-device continuation — 2026-10-03

This continues the same FIELD-1/DIAG-1A checkpoint, not a new milestone. Stage5N
remains CLOSED. HEAD remains `40e40bb14fc1c020a87e09bc054307a6c79a6d22`;
release source remains `5abc2da4878d38687574776932959db284dd9797`.
The earlier sections below describe preparation before the owner reconnected;
this section supersedes their NOT INSTALLED / NO ADB DEVICE statements.

### In-place installation and preservation

Owner ADB serial31ce63ba, Redmi Note9 Pro/Android12. Before: package
`com.familyconnect.app.friends`, `0.1.18-canary58-physical`/58, UID10283,
firstInstallTime `2026-09-19 17:30:26`, ceDataInode601521. Activation true, Auto,
NL selected, private acceptance override OFF. Existing identity, configuration
and encrypted readiness were fingerprinted without exporting plaintext secrets.
The58 installed APK had SHA256
`91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`.

Exact command (09:14UTC):

```sh
adb -s 31ce63ba install -r state-client-build/field59-final/artifacts/FamilyConnect-Test-0.1.18-beta59.apk
```

Observed `Success`; no uninstall of Family Connect, pm clear, reenrollment, identity
replacement, production APK rebuild or networking code change. After: beta59/code59,
same package/UID10283/firstInstallTime/data directory/inode601521. Pulled installed
APK hash equals `6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`;
signer remains `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Installed manifest excludes private acceptance components. The public non-debuggable
build correctly denies `run-as`; same-signer private instrumentation provided the
subsequent safe preservation checks instead of weakening the app.

Immediately after update, all three ciphertexts match byte-for-byte:
`friends-identity.enc`, `friends-configuration.enc`, `restricted-readiness.enc`.
Identity and readiness decrypt with the retained Android Keystore keys; activation
true and cached normal provisioning usable. Final post-test identity fingerprint
still matches; activation and Auto remain. No raw identity/public keys were shown.
The pre-update readiness receipt was READY/ACK_RECEIVED, expiring09:16:39UTC.
Normal product activity on59 subsequently refreshed short-lived readiness:
READY, both PRESENT_VALID, orchestrator usable, ACK_RECEIVED, observed09:34:12UTC,
expiry09:47:58UTC. This is retained identity/enrollment plus an ordinary refresh,
not a reset or a promise of validity after expiry. No manual server renewal ran.

### On-device validation

| Check | Observed result |
| --- | --- |
| Normal launch/version after fresh process | PASS; beta59 visible |
| Auto, real normal CONNECT | PASS; AWG selected,7.275s, VPN present, HTTPS200 |
| Explicit AWG | PASS;1.260s, VPN present, HTTPS200 |
| Explicit TCP | PASS;1.258s, VPN present, HTTPS200 |
| Device identity/data/activation/readiness preservation | PASS as bounded above |
| Previously compiled owner-safe instrumentation |5 PASS |
| Persisted CONNECTING→FAILED incident | PASS with synthetic typed events on-device |
| Persisted RESTORING→FAILED incident | PASS with new incident ID, synthetic typed events |
| Send diagnostics | PASS; real `android/com.android.internal.app.MiuiChooserActivity` |
| Export privacy | PASS;4675 bytes, bounded closed schema, no forbidden content |
| Support ID / Copy / restart stability | BLOCKED: unavailable, Copy disabled, no ID to compare |
| Live device-status API check | FAIL:404 route, see below |

Transport checks used the existing visible transport picker and CONNECT dial through
instrumentation; no normal-candidate exhaustion, private acceptance Activity,
second stack, radio change, gateway change or transport override. The HTTPS request
was a test to example.com; no traffic body was logged. Each successful test used the
ordinary disconnect action and restored Auto. Original emulator-only suites that
clear profiles/managed stores or require10.0.2.2 were deliberately NOT run on the owner.

Five existing tests: `DiagnosticsProviderTest`, both `ControlProtocolRuntimeTest`
methods, `AppUpdateRuntimeTest#verifiesInstalledSignerAndRejectsDowngradeAndInvalidArchive`
and `AppUpdateRuntimeTest#providerOnlyAllowsExactReadOnlyCacheApk`.
Additional private owner probes exercised preservation, normal product controls,
diagnostic persistence/export and final cleanup. Only the separate test APK was
packaged/signed; the beta59 artifact was never rebuilt or replaced. Initial owner
probe launch-idle/selector mistakes were corrected in that private harness; original
logs are retained as `*-initial-harness-*` / `*-v2-harness-*`, not mislabeled as
network regressions. Final transport checks above all pass.

Incident validation injected typed events into the existing DIAG recorder only;
it did NOT force a real transport outage, repeat Stage5N physical acceptance or
claim a spontaneous production incident. The Android confirmation opened the actual
share chooser; no recipient was chosen and nothing was uploaded. Exact exported
bundle SHA256 `e0f31b384a8b4c04230a01de00be23a8980eaccf6b37e3a417ffd29e038dd0e2`.
Both ring and incident use the fixed field schema, enum-like codes, UUID correlations,
coarse CELLULAR network class and no destinations, DNS history, credentials, keys,
identity, messages, room URLs or tokens. `device_support_id` is null: DIAG support
correlation remains incomplete until authentic server delivery works.

### Exact failing gates — publication blocked

**Support ID delivery/UI (release-blocking):**

```sh
adb -s 31ce63ba shell am instrument -w -r \
  -e owner_serial 31ce63ba \
  -e class com.familyconnect.app.OwnerFieldAcceptanceTest#supportVisibleCopiedAndStable \
  com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner
```

Expected: registered `FC-XXXX-XXXX` visible, Copy enabled/matching, stable after restart.
Observed: `Support ID unavailable: server delivery has not been deployed` assertion;
unavailable message visible and Copy disabled again after a real process restart.
Copy correctness and ID stability are NOT VERIFIED, not silently passed for null.
Host route probe `POST /friends/device/support` with empty JSON returns404.
Logs: `state-client-build/field59-owner/support-instrumentation.log`,
`support-result.json`, `final-device.json`.

**Existing device-status API (release-blocking failed live check):**

```sh
adb -s 31ce63ba shell am instrument -w -r \
  -e owner_serial 31ce63ba \
  -e class com.familyconnect.app.OwnerFieldAcceptanceTest#existingIdentityStillAuthenticates \
  com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner
```

Expected: the existing signed identity proof yields active device status.
Observed: `java.io.IOException: Test access unavailable`,
`FriendsAccessAndroid.post:54`, `deviceStatus:106`. An independent empty-JSON
`POST /friends/device/status` route probe returns404 (not an authorization rejection).
Logs: `state-client-build/field59-owner/enrollment-instrumentation.log` and
`enrollment-result.json`. This missing route is NOT evidence of lost enrollment:
unchanged identity/configuration, activation, working transports and subsequent
authenticated READY/ACK evidence remain intact. Nevertheless the API test did fail.

All local evidence is protected under `state-client-build/field59-owner/`.
Private test sources, APKs, exported test bundle and logs are not published or added
to Git. The two probe commands require reinstalling that private test APK: it was
removed after validation, not left as an acceptance surface on the phone.

### Cleanup and release boundary

Three test-generated diagnostic files removed by matching the synthetic connection
ID / exact export hash; export URI permissions revoked. The separate
`com.familyconnect.app.friends.test` package was uninstalled; the actual Friends app
was NOT uninstalled or cleared. Final09:38:25UTC: exact signed59 installed, fresh
normal app process, Auto/disconnected, VPN count0, Support unavailable/Copy disabled,
UID/data inode unchanged, no private acceptance component. No downgrade attempted.

Public Android catalog re-read: still beta51/code51. No catalog signing, landing
change, publication, hosted CI advancement, server deployment, new admission,
commit or push. Existing selected owner is the only cohort member; no widening.
One physical beta59 installation is now evidenced; no claim that all users updated.

The user's continuation permits Support HTTP deployment only after **all** owner
checks pass, while the missing Support ID depends on that deployment. This
prerequisite conflict is reported, not bypassed by seeding a local alias or deploying
early. Required next decision is to permit the already-defined server delivery/route
prerequisite before rerunning these blocked owner checks. Hosted CI/source-guard
resolution and production publication evidence remain later gates.

**FIELD-1-RELEASE = BLOCKED. DIAG-1A = PARTIAL** — on-device ring/snapshot/share/privacy
pass, but registration Support ID delivery/copy/stability remain incomplete.

## Boundary and version policy

Starting HEAD `1790793d2d2412896a6c5e23482c15c0def6b0c0`; Stage5N CLOSED.
Previous clean source `b952c3b8a69c845913e01508ca1d722168698a07`, local candidate
SHA256 `8229a36e8b176aa49346f3bf106f4f1229cb492a47c1c50e86593ddcb4c85a3b`
is retained in its original private artifact directory, never published or overwritten.
Live legacy catalog still advertises beta51/code51 at task entry. Repository release
rules forbid replacing **published** artifacts; user explicitly permits rebuilding
unpublished59. Revised candidate retains `0.1.18-beta59`/59,
`com.familyconnect.app.friends`, existing beta signing certificate
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.

No ADB devices at entry. The owner is last evidenced on private58, not freshly
observed. No install/uninstall/clear/enrollment operation ran. Acceptance and
publication cannot be claimed; no signed production59 catalog, landing switch,
APK publication, push, tag, or FIELD expansion is authorized by this checkpoint.

## Support ID foundation

Random eight-character human-safe alias `FC-XXXX-XXXX`, database UNIQUE constraint
with collision retry, one immutable mapping per existing device registration.
No deterministic derivation from identity; not an authentication or invitation token.
Additive `device_support` and `field_support_audit` tables only. Backfill includes
revoked records and does not change devices/invites/grants or resurrect registration.
New registrations receive aliases; migrated legacy records retain their original keys.

`POST /friends/device/support` requires existing single-use signed device proof,
separate `support` purpose, active registration/invitation and bounded app metadata.
Response contains only schema and alias. Existing activation/status wire contracts
are unchanged. No new public operator endpoint. Android caches the alias against
its existing private registration reference; offline UI never displays raw identity.
Settings → About / Diagnostics provides version, alias, copy and refresh.
DIAG uses this alias or null, replacing the previous unrelated local UUID; event
recording does not decrypt identity on every event. No automatic diagnostic upload.

`python -m control.friends.support_admin --db <existing-db> backfill|inventory|audit`
and `--admission <authoritative-admission.json> --support-id FC-XXXX-XXXX lookup`
are local operator commands. `scripts/package_support_operator.py` produces an
isolated deterministic source-only `.pyz` for the existing locked runtime.
Safe lookup: alias, optional label/platform/version/last_seen and its source,
registration/revocation, Family grant/readiness and admission states. No key, raw
identity, credential, Family ID, destination or room URL is returned.

Explicit `enable-field --expires <unix-seconds>` / `disable-field` use existing
grant and signed CRL machinery, the configured admission authority and an operator
file lock. Max3 unique explicit devices; wildcard rejected, sole owner retained.
Revoked registration cannot be enabled. Existing admitted expired grants require
the existing explicit grant-renewal operator, not implicit renewal by this command.
Disable revokes the grant before CRL/policy publication. Failed enable revokes its
new grant; incomplete multi-resource operations remain visible in audit for repair.
Audit records timestamp, Support ID, previous/desired state and PENDING/APPLIED/
INCOMPLETE outcome; no secrets. Never treat INCOMPLETE as successful admission.

## Deployment / rollback

Backfill can run independently of Android publication after a protected on-host
SQLite backup. Compare all preexisting table rows before/after; preserve admission
file bytes. Do not recreate/initialize the registration database. Source-only
operator can be removed on rollback; retain additive mappings so aliases stay stable.
Do not restore a stale whole DB over newer enrollment or delete Support IDs.

Authenticated delivery requires the new closed HTTP artifact and the ordinary
ingress route extension `device/(status|support)`. Do not rerun the full historical
installer or change gateway configuration to add this route. Verify isolated HTTP
contracts before a narrowly scoped existing-runtime transition. Until deployed,
Android shows unavailable and permits explicit refresh, rather than inventing an ID.

Initial release policy remains latest59, minimum_supported_version1,
mandatory=false (`mandatory_after=0`). Use the accepted offline update root only
after platform/release acceptance. Publish both legacy and signed discovery catalogs.
Public51 has a manual Settings checker; old builds lacking it require one invitation
page update. Exact per-version populations are unknown, not inferred from total
registrations. Windows/Linux links and catalogs are out of scope and unchanged.

## First tester instructions (after publication)

1. Open your normal Family Connect invitation/link.
2. Install the offered update **over the existing app**; approve Android installation.
3. Do **not** uninstall, clear app data or reenroll.
4. Open Family Connect.
5. Settings → About / Diagnostics → Copy Support ID; send it to the operator.
6. Wait for operator confirmation for this exact registration.
7. Press CONNECT normally in Auto on your real network; no diagnostic exhaustion.

Keep the owner; select only1–2 additional trusted physical devices, ideally one on
a naturally restricted cellular network. Application version is independent of
restricted admission. No wildcard or expansion beyond the initial2–3 cohort.

## Revised candidate evidence

Clean committed source `5abc2da4878d38687574776932959db284dd9797`, exported using
`git archive`, no source overlays:1697 source files plus38 verified generated/native
inputs. Inventory SHA256 `5143e0b09558d7a83679a998972e0568b5d332916e5911f2f0c342dc0329085b`;
local evidence under `state-client-build/field59-final/`.
APK `artifacts/FamilyConnect-Test-0.1.18-beta59.apk`,49,609,595 bytes:

`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`

Existing beta certificate above verified with APK v2 signing and16KiB alignment.
Only the protected beta APK key was used in memory; offline update-root key unused.
No private acceptance components in manifest or DEX; required production/Support ID
classes present; non-debuggable, backup disabled, no cleartext. Native source remains
`061595376fa65ae38725ed75baac769d71623d92`; verified native bytes reused, not rebuilt:

- AWG `1910ccac238884dd55120917c509571117f2aa2e95d10e9255ea00a069738517`.
- Restricted `0307df7e41bd2a002ee9cde37002862d5c6a445e319c9ea297829975b7e6da21`.

Orchestrator/transport/fail-closed code unchanged. Existing native JNI symbols match;
JNI on-device runtime is NOT RUN. No new physical acceptance surface was packaged.

226 app JVM tests and163 overlapping control JVM tests PASS; lint0 errors/36 existing
warnings; assemble and Android instrumentation compilation PASS. Five native package
race tests and vet PASS (bootstrap, Family session, whole-device, underlay, TCP).
Initial expanded Python run504 PASS/6 missing-nginx skips; final run with the verified
nginx1.30.4 executable **510 PASS,0 skipped in85.70s**. Unlike the previous partial
task, all historical/closed HTTP,
sync/readiness, Java golden, Go and synthetic APK-signing fixtures are supplied.
Source-only operator reproducibility/isolation and actual packaged Support endpoint
authentication/replay tests PASS. Instrumented UI/copy/share tests have NOT run.

Whole-index guard still reports the unchanged negative assertion in
`tests/test_readiness_adapter_packaging.py:283` containing a PEM-header literal.
This is not private-key material; no broad scanner exception or weakening was made.
It remains a recorded release check failure, not a claimed all-green result.
All27 changed-task source files:0 guard findings. Signed APK/nested Python scan:
1074 entries,0 findings after one previously reviewed byte-pinned stdlib false positive.
Docs links and `git diff --check` PASS. Hosted platform CI and actual owner runtime
acceptance remain outstanding. Both unrelated VPN-health files match their original
byte hashes; the41-line unrelated STATUS additions remain unstaged, not committed.

## Production backfill — executed08:50:29UTC

Authorized RU host only. Source-only operator artifact SHA256
`b6fe9220590524905cd98580c083bfd985d80cd5d01391ae7c2b5c4152c995b7`
installed at `/opt/apps/family_connect/support-operator-5abc2da.pyz`.
Protected backup and result receipt:
`friends-access/support-backfill-5abc2da/{before.db,result.json}` on that host;
no database/keys copied locally or committed. Backfill under a SQLite write lock
preserved all rows in13 preexisting tables and the exact admission file bytes.

| Authoritative record inventory | Count |
| --- | ---: |
| Total records / assigned Support IDs |28 /28|
| Non-revoked / revoked device records |24 /4|
| Platform known / unknown |0 /28|
| App version known / unknown |1 /27|
| Latest known version |1 private canary58/code58|
| Records evidenced on beta59 |0|
| Restricted admission / wildcard |1 /no|

Version knowledge comes from an existing signed-device readiness receipt; platform
is NOT inferred from the version string. No per-device update-offered/pending
telemetry exists; exact legacy/manual population is unknown. Zero evidenced59
does not prove every unknown installation is on another version. No DAU claim.

No enable/disable action was run against production. Existing owner admission stays
unchanged; no additional testers selected. Only preparation for1–2 more devices.
Operator lookup/actions are implemented and tested; the source-only operator is
available on-host. **The new HTTP runtime/ingress has not been deployed**, so Support
ID delivery to Android and automatic assignment for new registrations on the old
runtime remain pending. Do not mistake completed backfill for completed delivery.
No gateway, transport, CRL, issuer, enrollment or invitation change occurred.

## Owner, publication and remaining work

ADB still returned no devices at the final check. Neither the previous8229a36
candidate nor this revised6d13720 candidate was installed in this task. Same package
and signer are verified statically, but owner UID/data/Device Identity/enrollment/
readiness continuity, Support ID visibility/copy, normal Auto/AWG/TCP, incident
snapshot and Android share/export privacy inspection remain **NOT RUN**.
Server-side identity-preserving backfill is not evidence of Android update acceptance.

Production catalog remains beta51/code51; advertised SHA256
`79a2d28667332ea442eae1b895b4fc632b52734cbed1e75bd95f32b7175ad366`.
No actual public59 download exists to verify. The previous task independently
verified public51 bytes; this task re-read its unchanged catalog, not a new APK
download. Landing and invitation flow untouched; Windows/Linux untouched.
No production59 manifest signed/published; min1/optional is planned, not active59
policy. No update discovery of59, mandatory shutdown, push, tag or release.

Next: connect/unlock/authorize the intended Redmi; deploy the tested authenticated
Support delivery with the existing narrow HTTP transition and ingress checks;
perform both requested in-place preservation/functional checks without data clear.
Resolve the recorded source-guard false positive and hosted release validation
without reopening Stage5N. Only after owner acceptance publish immutable59, both
catalogs, Android landing metadata, verify downloaded bytes and commit/push the
accepted publication checkpoint. Never widen FIELD beyond2–3 explicit devices.

**FIELD-1-RELEASE = BLOCKED (owner acceptance/publication). DIAG-1A = PARTIAL
(local implementation/tests pass; device acceptance outstanding).**
