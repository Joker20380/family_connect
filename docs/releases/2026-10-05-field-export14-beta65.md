# Export14: Telemost traffic, recovery and RTP reorder correction — 2026-10-05

## Outcome and deployment boundary

The initial local-only checkpoint below is retained as history. The final
[gateway deployment checkpoint](#gateway-ci-artifact-and-deployment-pass) supersedes
its rollout state; field resolution remains unproven.

**Real restricted-channel traffic and automatic recovery confirmed; sustained VPN
operation still fails.** The unchanged main Family Connect beta65 reaches two
Telemost/Family TLS sessions during the mobile Auto attempt. Both carry DNS/TCP
traffic and both exhaust reliable retransmissions. No successful full page load
or stable Internet access is inferred from transport counters.

Investigation found and reproduced an additional local RTP receive-buffer defect.
Its correction passes native tests, but is **not deployed and not yet proven to
explain this field failure**. No new APK, version bump, signing, installation,
publication, remote configuration change or service restart in this task.

Source base is `25532b1f48ea426c4b6fb2380b8cc9f6299caf2b`, with prior uncommitted
readiness changes preserved. Native source at that base equals accepteda813dc5;
the new production Go change is confined to `carrier/telemost/rtp.go`.

## Evidence and timeline

Input `FamilyConnect-diagnostics(14).json`:147418 bytes, SHA256
`964cf8df7b332b0e16371c24002fc76982011b8ec4c7edda3000bf5ec57f56c3`.
Tester supportFC-YHQB-9VJN, beta65/code65. Current connection
`46959e0a-56b3-4d80-8df2-e7780a983c3d`; final underlying network CELLULAR.
Ring/incident each retain128 events,131 distinct combined. The preceding AWG
connection ending14:16:07 is separate; do not attribute its counters to this trial.

All times below UTC05.10; add2h for Brussels and3h for Krasnodar.

| Time | Observation |
| --- | --- |
| 14:16:32.421 | Mobile Auto starts. |
| 14:16:33.231 | Readiness FETCH_FAILED; existing validated cache remains usable. |
| 14:16:58.060 /14:17:20.379 | AWG and TCP candidates fail NETWORK. |
| 14:17:55.650 | First restricted CONNECTED; initial Auto elapsed83.230s. |
| 14:18:15.336 | Native first failure: RELIABLE_RETRY_EXHAUSTED. |
| 14:18:16.088 | Orchestrator RESTORING with policy_reason NETWORK. |
| 14:18:16.292 | Old client native handle cleanup complete. |
| 14:19:29.714 /14:19:29.744 | New restricted CONNECTED/restoration_succeeded;73.657s recovery. |
| 14:19:46.754 | Second native RELIABLE_RETRY_EXHAUSTED. |
| 14:19:50.153 /14:19:50.341 | Second loss/restoration_failed, NETWORK; one-restoration budget exhausted. |
| 14:20:07.730 | User disconnect complete. |

The second attempt stops at the existing bounded recovery guard, not the old
INTERNAL classification defect. Original Android reason_code and policy_reason
are NETWORK. The current offline correlator's narrower trace-reason vocabulary
projects these recovery reasons as UNKNOWN_INTERNAL; that projection is **not**
the application's policy classification. Preserve original evidence when reading it.
Final IO_CLOSED and closed ICE/peer states are not substituted for the pinned first
native failure. Java stage snapshots can be batched, not exact underlying onset times.

Session1 tag `98b1873d4c7ff9a8b712eff1138661f7a05f8ea199e060daeffebcb61a35520a`:
7 DNS responses/0 errors;28 TCP opens/1 error;60308 TCP bytes sent/16674 received.
Session2 tag `1d69c02d1c1bcae4f73dd242130139022eeadfde155b10b960a17ed33676f147`:
17 DNS responses/0 errors;31 TCP opens/0 errors;81761 bytes sent/48902 received.
Both CONNECTED→RESTORING intervals are approximately20.4s; native failures are
observed earlier than the Java state transition.

## Paired delivery evidence

Read-only NL journal extraction14:16–14:21UTC matches both exact session tags.
125 allowlisted server events total; both server sequences complete with no gaps,
required lifecycle stages present, bidirectional carrier activity confirmed.
The tool's historical field owner_lifecycle_complete denotes lifecycle coverage,
not proof this is the owner's device or a successful stability test.

| Client first failure | Session1 | Session2 |
| --- | --- | --- |
| send_base /send_next | 62 /70 | 117 /125 |
| Pending /head retries | 8 /8 | 8 /8 |
| Last ACK age | 551ms | 781ms |
| Time without ACK-base progress | 7877ms | 8399ms |
| ACKs received | 168 | 274 |
| Gateway receive_next /mask, retained later sample | 62 /240 | 117 /234 |

Thus the gateway reliable receiver still lacks DATA62/117, while later DATA is
buffered and ACKs reach the client. This is more specific than an ACK-only loss
hypothesis. Gateway RTP gap events rise to21/16 respectively; these count sequence
discontinuities **after local reordering**, not a packet capture proving external
network loss. They cannot distinguish provider loss from local discard.

Endpoint samples are not simultaneous. There are no matched retained fragment IDs
for the missing heads, so no exact RTP packet or loss location is identified.
Client trace retention is bounded (first session archive/delivery drops17/3), whereas
matched server sequences are complete. Do not claim RKN causality or complete client
packet history. Raw export/private receipts remain outside Git in
`state-client-build/field65-export14/`: metadata, paired-server and correlation JSON.

## Reproduced local defect and correction

`reorderBuffer.push` previously kept gapSince while queued packets remained, even
when drain advanced nextSeq to a **different** missing packet. After the first gap
expired/healed, the next arriving out-of-order packet could skip a brand-new gap
immediately. Its missing packet, arriving moments later, was then discarded as old.
A fragmented VP8 frame was lost even though every RTP packet arrived.

The correction remembers the receive position before processing a packet and
starts a fresh gap deadline when that position advances and another gap remains.
Unchanged:100ms gap allowance,256-packet bound, duplicate/late rejection, wrapping
sequence arithmetic, fragment format, reliable windows/RTO/eight retries, TLS,
authorization/revocation/expiry and recovery limits. No increased stall timeout.

`carrier/telemost/rtp_gap_test.go` covers healed/expired preceding gaps, sequence
wrap-around, actual VP8→fragment→CRC byte-exact delivery, unchanged-gap deadlines,
eventual skipping and rejection of packets arriving after a legitimate skip.

## Validation

- Baseline Go overlay, unchanged production rtp.go: four ordering cases fail and
  byte-exact carrier regression fails. Fixed source passes; RED receipt retained.
- Focused RTP/frame/fragment suite20 repetitions PASS; final RTP suite100 repetitions PASS.
- Scoped race run telemost/reliablestream/sessiondiag/wholedevice/roombroker PASS.
- Full `go test -race -json ./...`: **395 test/subtest pass records,13 skips,
  14 package passes,2 command packages without tests**. Skips include opt-in live
  provider/ProductStore/isolated Python artifact cases and the subprocess helper;
  no live field acceptance is implied. Receipt `native-race.jsonl` retained locally.
- gofmt and `git diff --check` PASS. Documentation link check480 files/2927 links,
  zero errors; this checks local links, not external download reachability.

Workspace-local TMPDIR/GOTMPDIR/GOCACHE avoid the existing `/tmp` quota; socket
tests run with approved normal host networking. An initial focused invocation used
the wrong carrier-relative temporary directory and did not run tests; corrected
absolute paths were used for RED/GREEN and all validation above.

## Current runtime, rollback and next gates

Read-only verification14:45:25UTC: actual loaded gateway SHA256
`055716447a1fe4bd8859dc2877410e756a9dc60a81b0ae5203a23f99606326a0`, sourcea813dc5,
PID464237/NRestarts0. HTTP43b99783/sync9faaa1c2 active; RU/NL directory hashes equal;
ordinary AWG/TCP PIDs unchanged. Tester fresh READY/ACK14:23:31UTC, grant1/CRL6739,
admitted/non-revoked. Actual loaded leaf/profile expiry05.10 **17:52:14UTC /
19:52:14 Brussels /20:52:14 Krasnodar**;11208s headroom at observation only.

Installed owner/tester and targeted public APK remain **0.1.18-beta65/code65**,
SHA256 `dfbdb5352b8c707fb77ff3d7392d8217f898aa8e999b6a0f52fad8172185778e`.
Default/catalog/invitation remain60. No artifact was replaced or newly distributed.
Original [beta65 release verification](2026-10-05-bootstrap-cleanup-race.md) and
[active readiness packages/material rollback](2026-10-05-readiness-clock-skew.md)
remain authoritative; this task made no production write requiring rollback.

Next: exact-source gateway CI/artifact acceptance, controlled gateway-only activation/
readback, unchanged-main-beta65 owner compatibility check, then one mobile trial.
The defect is on the receiver, so test the client→gateway correction without
an APK replacement first; the wire format is unchanged. Field effectiveness remains
unknown until that trial. Do not request another identical tester run now.

Any gateway deployment must preserve05571644 as its executable rollback, verify
actual loaded bytes, credentials and RU/NL seed propagation, and preserve ordinary
services. Never restore expired issuer4/old credentials during rollback. Recheck
material headroom and use the existing renewal path if the next gate is delayed.
Keep the tester's working VPN available for coordination; no screenshots or phone
clock adjustments are required. The separate arbitrary-clock-resilience design
remains unfinished; this RTP correction does not replace it.

## Gateway delivery continuation

User authorizes the next stage. Scoped commit `d678773` contains only rtp.go and
rtp_gap_test.go. Initial push was rejected (remote main gained documentation
`f992a7d`); normal merge `8d046321039d0bd1e18ecc1af979ff90f591e029` preserves it,
with no force push. In-progress PLAN edits were stashed by exact path, merged back
without conflict; stash retained as a recovery copy. Other dirty files untouched.

Exact-source CI started: phase0 `37329376362`, Client builds `37329375594`.
First job readback: Android native race and diagnostic contracts PASS; overall
workflow and gateway artifact acceptance still pending. The existing workflow also
builds an unsigned Android artifact; it must NOT replace/re-sign the public beta65.
Only the verified gateway executable is a deployment candidate.

Preflight15:04:36UTC: gateway05571644/PID464237/NRestarts0, loaded TLS/profile match,
10057s effective headroom, ordinary service/database/admission fingerprints captured.
Owner ADB reachable; no phone installation or server mutation. Protected continuation
receipts/operator are in `state-client-build/rtp-gap-20261005/`. Deployment is guarded
on both completed successful CI runs, source/ELF/hash verification, unchanged native
tree and a fresh live preflight. Executable rollback target is05571644 with current
valid credentials. Planned remote receipt/backup directory:
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005`.
This directory is not yet asserted to exist; no deployment success claim at this checkpoint.

## Gateway CI artifact and deployment PASS

Both exact-source workflows complete successfully on attempt1: phase0 `37329376362`
and Clients `37329375594`, source `8d046321039d0bd1e18ecc1af979ff90f591e029`.
Android job111828247709 passes native race/diagnostic contracts, ordinary emulator
lifecycles, restricted native/gateway build and exact artifact/source guard. Linux
and Windows jobs pass. No weakened checks or unrelated test changes.

Artifact11354353210,58410205bytes, ZIP SHA256
`e5d7342edf014eec8a695c7e25f26ab5165a2c667288ee1e889ad3a5088e1592` downloaded and
verified against GitHub metadata and its manifest. Gateway Linux/amd64 ELF,17373427bytes,
SHA256 **`7c6e1e11208e167309cbe83dac0f5f1f1bb306f4e41628180367aa6fa5e9aa50`**.
Embedded revision matches8d04632; vcs.modified=true retained as reported by CI
(generated build outputs), not represented as a clean-worktree build. Native source
matches the accepted commit. CI's accompanying unsigned beta65 APK remains unused:
no offline signing, installation, public replacement or catalog/version bump.

Guarded gateway-only activation05.10 **15:22:12UTC** starts PID510497; bounded
acceptance reaches fresh validated bootstrap READY15:22:18 with no restarts.
Actual `/proc/PID/exe` SHA matches7c6e1e11. TLS leaf/profile/issuer verification PASS.
Existing HTTP43b99783/sync9faaa1c2 archives, wrappers, access/security policy and
credential lifetimes are unchanged. Old executable05571644 is backed up at:
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005/bootstrap-broker.previous`.
The same directory holds durable acceptance/activation and deployment receipts.

Explicit existing RU sync succeeds. RU/NL directory is byte-equal, issued
`2026-10-05T15:22:16.364102466Z`, SHA256
`32fdb3eff72cb880f6f4fa4be3e5169ff1b53a87a342e8f144f0b210e4fb71c0`.
The directory's later19:22:12UTC expiry does **not** extend the actual loaded leaf
limit **17:52:14UTC /19:52:14 Brussels /20:52:14 Krasnodar05.10**.
Final readback15:25:08: same loaded bytes, PID510497/NRestarts0,8825s headroom.

Before/after fingerprints: RU device/invite/grant/audit/support/admission unchanged;
RU HTTP/AWG/TCP and NL AWG/TCP PIDs/start identities unchanged. Public HTTPS probes
status200, ordinary malformed challenge400, chat400, restricted malformed400 PASS.
Both signed Android catalogs retain their previous exact hashes/default60.

## Unchanged owner APK and next field trial

Owner ordinary FriendsActivity foreground15:23UTC obtains fresh fetch/native
**READY/ACK15:23:05UTC**, grant3/CRL6849 and the new directory, without forced fetch,
cache clearing, clock/radio changes or installing any product/instrumentation APK.
Before/after installed package SHA remainsdfbdb535, code65, UID10283, last update
2026-10-04 22:19:48; no instrumentation package present. Existing public beta65 bytes
and original signer are not replaced. Local receipts are in
`state-client-build/rtp-gap-20261005/` (CI/artifact, preflight, deployment,
post-deployment, owner-before/foreground, HTTP and final readback).

This proves ordinary unchanged-client import compatibility, not a new physical
owner restricted data/recovery trial. The latter was not forced through a separate
test package. Native/CI wire and lifecycle tests pass; field effectiveness of the
RTP correction is still unknown.

At15:25:11 readback, tester's last successful fetch/ACK remains14:23:30/14:23:31,
CRL6739, referencing the **retired** pre-restart directory. Generic currently_ready
is true because that receipt has not expired; it is not current-seed readiness.
Next tester action: keep working Wi-Fi/VPN, open the existing Family Connect and
allow ordinary foreground refresh. Confirm a new post-deploy fetch/native ACK before
turning Wi-Fi/other VPN off for one cellular Auto trial. Its300s refresh cooldown
was already elapsed at final observation; do not clear state or modify clocks.

After that refresh, pre-deliver the whole brief test instruction while messages work:
cellular only, other VPN off, Family Connect Auto; allow up to2min for fallback;
if connected, open several pages for3–5min rather than idle. On failure do not loop
manual retries. Save diagnostic JSON, restore the working VPN and send the export;
screenshots are not required. Report success only from real traffic and the new
paired field evidence, not the local defect reproduction.

Rollback if required: restore only the saved05571644 executable with its original
ownership/mode, rerun bounded bootstrap acceptance against current valid material,
verify loaded old SHA/chain and synchronize its new directory to RU. Preserve
issuer5, current CRL floors and grants; never restore issuer4/expired profiles or
the retired directory. Rollback was prepared, not exercised (deployment passed).
For testing after the loaded-leaf deadline, use the existing renewal path and
revalidate the actual runtime; no automatic renewal was introduced here.

## Tester availability follow-up

User reports the tester is now unavailable. The bounded seven-read observation
ended15:30:30UTC; tester still has only the old14:23:31 ACK, so current-directory
readiness and the post-fix mobile trial remain pending. No mobile trial was started
or claimed. The observer has exited; no background monitoring or schedule remains.

Gateway installation/owner import results stand, but do not prove field resolution.
Do not request further action while the tester is unavailable. On return, recheck
actual gateway health and the17:52:14UTC/20:52:14 Krasnodar05.10 leaf deadline;
if needed renew current material through the existing path, verify actual loaded
chain and RU/NL directory, then fetch/ACK on the unchanged65 over a working VPN.
No APK rebuild/reinstall is required solely for delayed testing.

Final documentation checker:480 files/2930 links, zero errors; git diff check PASS.

## Evening window renewal

On the next availability report, read-only15:33:14UTC confirmed gateway7c6e1e11/
PID510497 stable,8339s effective headroom. Tester65 had fetched15:31:33 and signed
native READY/ACK15:31:34UTC (grant1/CRL6864, admitted/non-revoked), proving import
of the post-deploy directory. No mobile trial or stability success was inferred.
User then reported unavailable again until21:00. Assumed Krasnodar timezone, equal
to20:00 Brussels/18:00UTC; no future monitor or reminder was created.

The old17:52:14UTC leaf would expire before the requested window. Therefore the
existing **four-hour credential-only** renewal was performed in advance. No new
APK, executable deployment, key, issuer, grant/revision, admission, timeout or
security-policy change. Source8d04632 and CI-accepted gateway7c6e1e11 remain loaded.
Preflight confirms issuer5 expires06.10 13:51:23UTC and existing grants cover4h.

Issuance15:38:10UTC: CRL6877, lifetime14400s, same gateway key/root/issuer5.
Atomic publication15:38:29: native positive and negative authority checks PASS;
UID/GID979:979,0600, service readability/fsync/final readback PASS. Existing sync
timer is restored in finally; no HTTP/sync code, wrapper or service configuration
replaced. Same gateway restarted as PID519555/NRestarts0. Bounded bootstrap READY,
actual loaded TLS certificate/issuer/hostname and35s stability PASS.

Actual loaded expiry **05.10 19:38:10UTC =21:38:10 Brussels =22:38:10 Krasnodar**.
Final15:39:20 readback verifies actual executable SHA7c6e1e11, profile/served leaf
match and14329s headroom. RU/NL directory is byte-equal, issued
`2026-10-05T15:38:32.443370444Z`, SHA256
`796b17bba2ac01bc7291deb12577adb9058b8497b3a06b32804d4dc84c7ed35e`.
Its19:38:29UTC expiry does not extend the earlier leaf limit. RU device/invite/
grant/audit/admission/support and ordinary-service fingerprints remain unchanged;
final gateway operator also verifies unchanged NL AWG/TCP process identities.

Receipts: `state-client-build/rtp-evening-20261005/` and the corresponding protected
remote directory on both authorized hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-evening-20261005`.
Current RU/NL sync and final loaded-byte readback receipts remain in
`state-client-build/rtp-gap-20261005/`. The operator now checks tester readiness
against the latest synchronized directory issuance, not the original binary-deploy
timestamp. This prevents accepting the15:31 ACK after the15:38 seed replacement.

No phone action is needed while the tester is unavailable. At21:00 reopen existing65
over the working VPN, confirm fresh fetch/native ACK for the post15:38 directory,
then perform the single cellular Auto trial described above. Do not clear app data,
adjust clocks or reinstall. Both devices' last receipts at final observation still
predate this renewal; no post-renewal client acceptance or mobile success claim.
If timing slips beyond the actual leaf bound, revalidate/renew through the same path.
No automatic maintenance is scheduled. Preserve current monotonic CRL floors and
valid material for any executable rollback; do not restore the saved old profile
and its earlier CRL wholesale.

## Late resumption after interruption

User reports the tester enabled VPN, then asks to continue after a connection loss.
Read-only audit19:44:21UTC finds the evening leaf expired19:38:10. Tester unchanged65
fetched19:36:47 and signed READY19:36:49, but its receipt is expired at audit too.
This is not evidence of a new post-fix mobile trial. Active gateway still loads
accepted SHA7c6e1e11, PID644769/NRestarts1; this snapshot does not establish why it
restarted. No restart cause or field success is inferred.

Preflight confirms issuer5 still expires06.10 13:51:23UTC, grants cover another4h,
and service979:979 can read the protected0600 credential. The existing credential-only
path issues at19:53:04UTC, CRL7347, same keys/issuer/grants and14400s policy. Native
positive/negative validation and atomic publication19:53:09 PASS. The sync timer
is restored; no HTTP/sync/ordinary-service code or configuration is replaced.
Gateway PID652351/NRestarts0; actual loaded certificate/chain/hostname and35s
stability PASS. Actual leaf expiry **05.10 23:53:04UTC =06.10 01:53:04 Brussels
=06.10 02:53:04 Krasnodar**. This supersedes the earlier window, not the APK.

RU/NL directory equality PASS: issued `2026-10-05T19:53:12.70859759Z`, SHA256
`4aa5ff380813b6ba798692ceea097ed5d8f022c887069113ca1b664b75e81236`.
Directory expiry23:53:09UTC does not extend the earlier leaf deadline. Private
receipts remain in `state-client-build/rtp-late-20261005/`; protected staging on
both authorized hosts is
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-late-20261005`.
Sync/readiness/final audit receipts remain in `state-client-build/rtp-gap-20261005/`.

No version/build/install/publication change: installed/targeted beta65 SHA dfbdb535
and default/catalog/invitation60 remain as previously verified, not re-published.
No security module, expiry, revocation or authorization check was disabled. Executable
rollback remains05571644 in the RTP deployment backup; retain latest valid credentials
and monotonic floors, never restore an expired profile or the retired seed.
NEXT fresh tester native READY ACK after19:53:12UTC over working VPN, then one
cellular Auto trial with3–5min traffic and diagnostic JSON after restoring working VPN.
No screenshots, clock changes, reinstall, separate test APK or manual retry loop.
Real field stability and the causal contribution of the RTP fix remain unproven.

Final runtime readback19:54:12UTC confirms loaded SHA7c6e1e11/profile/served chain,
PID652351/NRestarts0 and14330s headroom. RU before/after ordinary-service and
device/grant/admission invariants match; NL AWG/TCP identities unchanged. Explicit
timer-restored receipt is true. Seven bounded readiness reads end19:56:11UTC:
tester still has only19:36:47 fetch/19:36:49 ACK, expired, no post19:53 refresh.
Observer has exited; no ongoing monitoring or future task. User instruction is to
open existing Family Connect while keeping working VPN, not start mobile yet.
Documentation validation:480 files/2933 links, zero errors; git diff check PASS.
