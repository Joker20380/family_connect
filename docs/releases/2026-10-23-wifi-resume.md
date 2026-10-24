# Owner Wi-Fi continuation after workstation reboot —23 October2026

## Preserved baseline before changes

Owner statement22.10 remains the network correction: «22 октября 2026 года владелец
сообщил: пакет мобильного трафика закончился, оператор ограничил скорость;
на Wi-Fi приложение работает нормально». Owner report, not a fresh phone test.
Rate/onset/version during that success and Wi-Fi upstream independence UNKNOWN.
Historical mobile failures and Volgograd/Krasnodar incidents are not rewritten.

04:23–04:29UTC readback: Redmi31ce63ba, `com.familyconnect.app.friends`, installed
`0.1.18-beta105-recovery`/105, UID10283. Pulled APK SHA256
`91ba2d6e4cb6d3c789e4921df96b79ea196d42bc602bc72ea727fa1489aef2a3`
equals the verified artifact/signer/all12 native libraries.2071 source files and
static88/94/104 upgrade metadata reverified; physical tester upgrades remain unproved.
Wi-Fi398 is the default network, no owner VPN/ConnectionService; protected status
`off`, upload `STORED`. USB consent **active**, not the current blocker. Full normal
snapshot again fails `FileNotFoundException: Snapshot unavailable`. Prior identity
FC-4D8Q-REEG is retained evidence, not a newly read live full JSON/settings/cache.
APK, app/system logcat, exit info, network/services/power and clock saved first.
No clear logcat/data/cache/incident, force-stop, profile switch or Connect/Disconnect.

Gateway186.246.45.246 binary
`3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae`, PID2170469,
NRestarts0, start03:49:10UTC before this task. Config SHA256
`f8188a9763c091984166788f1dd0456cadeeb730fa43b9557f59fe3bb63ed5f7`.
P1 policy has one owner target; pacing/counters OFF, baseline mux operator LEGACY64.
Without an owner session this is not negotiated RS32/CREDIT128 proof.
Cert/CRL valid03:48:57–07:48:57UTC. Actual RU185.251.89.19 credential renewal timer
active,04:18:56→04:18:59 success; directory sync04:28:11→04:28:13 success.
Initial guessed Amsterdam renewal-unit read is non-authoritative; exact RU unit
read supersedes it. Phone cache validity cannot be inferred from server validity.
No timers/floors/expiry, config, binary or server services changed by this task.

## Minimal diagnostic successor106

Recovered unfinished106 work, absent from the prior summary. The retained217-test
`build-initial-regression` predates two source changes; it is not current build proof.
Final offline build: **219 JVM checks PASS**, including six diagnostic-budget checks.
Exact105→106 delta: app version, `DiagnosticRing.snapshot()` call, new
`DiagnosticRecordBudget` and its tests. All12 native libraries unchanged, restricted
SHA256 `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`.
Keep102 health,103 deadline/cancel/cache,104 bounded750ms reorder and105 pressure
drain. No retry/window/buffer growth, Q1/packing/FEC/QUIC or security change.
Retained targeted native/race/bridge tests still apply to identical native bytes;
no new platform CI or field validation claim.

The correction budgets the serialized deep copy at the existing256KiB limit;
retained in-memory history is not mutated. Session summaries, first causes, raw
counters, first/latest detail entries survive; omitted middle details are counted.
Recorded replay with two synthetic valid contexts:262837→262098 bytes, export PASS;
current session and app events unchanged, four oldest-session middle trace details
omitted and accounted for. Original JSON unchanged. This is local proof, not direct
inspection of the live heap or exclusion of every possible IO failure. Tests cover
UTF-8 accounting, boundary events, omission counts, small-record byte identity,
fresh state and snapshot/history non-mutation.

Signed through the existing protected vault; no key/password output or public write:

- Path: `state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk`.
- Version `0.1.18-beta106-recovery`, code106; package `com.familyconnect.app.friends`.
- Signed SHA256 `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Android12+/API31, arm64-v8a,16KiB aligned. Unsigned SHA256
  `551c4e02d19aa04901e73200a344f35becc3cee412f85a580f1165ed7c8db272` is separate.

Guarded105→106 `adb install -r` succeeded04:38:17UTC, same UID10283, exact signed
APK/native hashes. No uninstall/data clear/force-stop. Fresh normal JSON succeeds,
code106/FC-4D8Q-REEG/WIFI/READY/USABLE; USB support active, no further consent needed.
One ordinary support Connect returned CONNECT_REQUESTED. Fresh snapshot04:44:16UTC
has CONNECTED/TUN/P1/RS32/CREDIT128, errors0, session
`815157cc5333ec06cf3217b36142d15da88406d2144e4aef9b2f8a2c82d37ca8`.
Same invocation's gateway session_profile04:44:04.982UTC matches both contracts;
this is ordinary Connect, not auto recovery. The unavailable105 full Wi-Fi baseline
is **not** recorded as PASS. No new enrollment or profile command was sent.

First control harness's SSH/stdin diagnostic read timed out before any application
request/reservation. This is not a transport/body failure. A separate bounded gateway
acquisition succeeded (361 reassembled records, no parser errors); exact raw manifest
and runtime freshness are checked by the retry before using that same-session proof.
Its10min maximum evidence age is a readback guard, not a transport retry/timeout change.

## Fresh Wi-Fi transfer and ordinary intent checks

`baseline106-r1` completes **19/19** HTTP200/TLS-verified/full-size responses:
single4MiB28.210s/**1.189452Mbit/s**, parallel2×2MiB14.740s/**2.276420Mbit/s**.
Sixteen1KiB requests cover before/during/after load and four10s idle intervals.
Small response median/max seconds: before2.529/3.132; during1.870/2.405;
after3.629/4.064; idle3.199/4.549. Latency varies; no new improvement/guarantee claim.
Same real owner TUN/session/Wi-Fi398/P1 throughout, no observed fallback or reconnect.
Explicit curl binding to the TUN prevents direct bypass on interface loss. Network/
session/topology monitor stops on change; none detected. DNS responses32/errors0 at
the final sample; normal DNS_PROBE_OK events retained. Body hashes are observed,
not independent origin-digest/byte-exact proof for the random Cloudflare endpoint.

Android raw protocol_errors0→1 is retained: stream33 had local abort/removal at
1792731052387ms; crossed RESET arrived147ms later, classified `expected/crossed_reset`.
No actual violations, unclassified incidents or dropped contexts. This was an old
stream, not assigned to a benchmark request without evidence. tcp_open_errors1→1
already existed before the series; no new attribution of that historical counter.
The separate post-control gateway journal contains normal restricted_trace events,
not an independently matched Mux incident snapshot; do not invent server error0.
Gateway binary/config/PID/invocation remain unchanged. No unexplained critical body
failure is observed in this bounded control; this does not close historical cases.

Ordinary Disconnect: seven observations during a45s bounded check all DISCONNECTED/
no TUN. Ordinary Connect: new session
`34dfb9269cbdc6d44db36fdf419030a1656c93ce3702770ab190245b885dcf18`, both-end
RS32/CREDIT128, same Wi-Fi/TUN and identity. One further full1KiB HTTPS200 completes
in1.393372s. This proves persistent profile and ordinary intent handling, **not**
automatic recovery following actual network loss. All temporary monitoring threads
ended; no continuous download/collector remains. Normal export continues to work.
Final pre-manual readback retains the same new session/Wi-Fi/TUN/P1/READY and no
terminal error. Its raw protocol_errors6 are all classified expected crossings,
actual violations/unclassified0. This is a later background observation of the
new session, not a rewritten0→1 baseline or a reason for another speed/audit cycle.
Exact timestamp/hash is in `latest_pre_manual_readback` of the delivery receipt;
no extra application request was sent for this snapshot.

## Automatic Wi-Fi return —05:10–05:17UTC

The owner answered «готово» after the explained mobile-data-OFF, Wi-Fi-OFF/ON
action with no Connect/Disconnect. This is the owner's action report; exact10s
switch-off duration and every instant of the off interval were not instrumented.
Normal JSON/history were acquired first, without a connect/profile/install command.
The initial fresh read was RESTORING, not CONNECTED; the next read proves a new
automatic session. Old-session IO_CLOSED is retained as the induced network-loss
termination, not erased or attributed to an APK regression.

| Event | UTC |
|---|---|
|NETWORK detected / entered RESTORING|05:10:18.471 /05:10:18.496|
|Unavailable attempts, retries1 and2|05:10:18.740 /05:10:53.790|
|New Wi-Fi422 created, subsequently validated|05:10:54.786|
|Retry3 / network-available attempt|05:11:58.851 /05:11:59.888|
|New session CONNECTED / restoration_succeeded|05:12:41.364 /05:12:41.393|
|DNS_PROBE_OK|05:12:47.132|
|First measured post-return HTTPS body complete|05:17:04.311|

NETWORK→CONNECTED142.893s; Wi-Fi creation→CONNECTED106.578s. Native startup reports
39.892s. Recovery succeeds but is slow, not instant; the later one-shot HTTP timing
does not establish the earliest possible application availability. No retry/timer/
window changes, sweep or repeated bulk series were performed to improve this result.

New session `4dca57cfaac40e9270181617b7532620ae0762b23b001be5203b498277c7da09`
matches Android and the gateway's authenticated session_profile: P1, RS32/32,
CREDIT128/131072. The gated probe binds curl to owner TUN `tun1`, with Wi-Fi422
underneath, and completes full1024-byte HTTPS200/TLS verification in3.733008s.
The endpoint reports Amsterdam gateway egress186.246.45.246. The earlier restoring
snapshot had only an IMS cellular network, not an Internet cellular fallback;
matched session/probe snapshots remain Wi-Fi, with no AWG/TCP switch. This does not
prove the Wi-Fi upstream is independent/unthrottled or continuous off-interval
cellular monitoring. Body SHA is observed, not an independent origin digest.

Before/after the probe: raw protocol_errors8→8, expected crossings8→8, actual
violations/unclassified/incident_dropped0, dns_errors0, dns_responses32→34,
tcp_open_errors1→1. These new-session background counters are retained separately
from the earlier sessions; no counter reset or new failure attribution. No old
callback closes the replacement session in the bounded observation. Normal JSON
works, identity/version remain106/FC-4D8Q-REEG, terminal NONE. Existing-stream
survival, automatic replay of interrupted operations, overnight stability and
arbitrarily poor-channel performance are not claimed.

Gateway binary/config/PID2170469/invocation/NRestarts0 remain unchanged in the fresh
read. The one-shot collector and finite meter monitor exited; no matching local
temporary collector remains. No remote gateway restart or production policy write.

## Remaining acceptance and safety boundary

| Gate | Result |
|---|---|
|OWNER_WIFI_ACCEPTANCE|PASS_BOUNDED106; Wi-Fi upstream independence still UNKNOWN|
|RECOVERY_ACCEPTANCE|PASS_BOUNDED106; explicit cancellation and automatic Wi-Fi return/full small HTTPS|
|SIGNED_APK_READY|YES106, same signer; not field acceptance|
|TESTER_P1_POLICY_READY|YES; confirmed exact-three policy deployed in later23.10 follow-up|
|FIELD_WHITELIST_VALIDATION|POSITIVE_REPORTED_VOLGOGRAD96_WITH_CELLULAR_MESH_DIAGNOSTICS|
|FIELD_106_P1_VALIDATION|NOT_RUN; Krasnodar separate|
|PRIVATE_FIELD_READY|YES; limited manual handoff after later post-deploy control|

Later23 October: owner confirmed all three IDs; gatewaya515 group policy deployed
and verified, owner106 automatically regained P1 and passed another full1KiB HTTPS
in3.422s after normal USB consent renewal. Latest same-budget total8,408,064 bytes.
Export21 separately corroborates reported Volgograd96 whitelist success. See the
[final cohort report](2026-10-23-tester-p1-cohort.md) for exact rollout/rollback,
field limitations and current delivery scope. The preparation paragraphs and
8,407,040-byte checkpoint below are retained as the preceding phase, not pending work.

**Historical external boundary, subsequently resolved23.10:** current closed P1 membership. Historical explicit
handoffs/admission identify FC-ZMVK-MM7C (Volgograd, recorded94) and FC-YHQB-9VJN
(earlier tester admission). Neither old admission nor the service's all_activated
entitlement establishes the exact current P1 cohort or installed tester versions.
Ask the owner whether these two, plus owner FC-4D8Q-REEG, are the complete P1 group;
do not silently expand all eligible registrations or request another owner outage.

Prepared server follow-up, not applied: extend the existing authenticated
speedPolicy from one identity target to the confirmed finite group; keep owner P1,
legacy/nonselected P0, negotiation compatibility and the separate diagnostic filter.
Test selected/unselected/malformed/legacy policy paths locally, freeze exact source/
binary/config and plan an ordinary bounded deployment before declaring group-ready.
A second target cannot simply overwrite the current owner target. No new API,
grant/enrollment, temporary activation, USB prerequisite or global transport switch.
The ordinary persistent Android profile selector already needs no USB permission;
the APK is unchanged by this pending server policy work. Owner distribution remains
manual; actual tester updates and mobile whitelist attempts have not occurred here.

Continue the **same22.10**32MiB allowance:8,407,040 bytes reserved/requested
(8MiB+18KiB),25,147,392 remain; do not allocate a second32MiB. Prior25,204,736-byte
reservations untouched. Carrier/background/support traffic is separate, not the
application total. No mobile bulk probes, server restart, public
release/catalog/invitation update, push or messages. No active old local collectors
observed after reboot; no continuous collectors started. Public artifact availability
not revalidated in this private task.

Rollback:106 is installed and left connected on checked P1; no uninstall/downgrade/data
reset. Preserve failure evidence and use a higher-code same-signer correction based
on retained105 if necessary. Do not switch to P0 automatically because of throttling.
Static88/94/104/105→106 package/signer/increasing-code checks PASS; only105→106 has
a physical direct-to106 receipt. Actual tester versions/direct physical upgrades
and group P1 remain separate gates; do not infer support for every old version.

## Evidence paths

- Phone: `state-client-build/owner-disconnections-20261022/raw-entry-20261023T042347Z/`,
  manifest `f30c154f570b95759860ca8d2be35d5004a07f0a965f955d43cc0beb7f513276`.
- Gateway: `state-client-build/owner-disconnections-20261022/raw-gateway-reboot-readback-20261023/`,
  manifest `cd3d2c5b1d61614dde9948223dcd500eb59c839ac67c8eb901ab306f122cdd7a`.
- Consent/process readback, actual renewal,105 revalidation and106 source/replay
  receipts: `state-client-build/owner-wifi-resume-20261023/`.
-106 final inventories/build/signing/install receipts:
  `state-client-build/owner-diagnostic106-20261022/`; retain initial build separately.
- Full control and small reconnect probe: `state-client-build/owner-wifi-resume-20261023/baseline106-r1/`
  and `reconnect106/`; nonrefundable reservations in the same parent directory.
- Ordinary intent: `state-client-build/owner-disconnections-20261022/explicit-intent-check-106/`.
- Automatic-return initial phone capture: `state-client-build/owner-disconnections-20261022/raw-entry-20261023T051103Z/`,
  manifest `49a230f7d75e67676bb1b219567eaa4f3f9016d2ec79ac77e1d62b64e60c1a88`.
- Recovered gateway session: `state-client-build/owner-disconnections-20261022/raw-gateway-wifi106-recovered-session/`,
  manifest `009de915c1b6b5cad24480fcb0e381a20d2d513d59a03a51d31ddf52edd5b8f0`.
- Automatic-return gate, one-shot probe, before/after JSON and exact derived receipt:
  `state-client-build/owner-wifi-resume-20261023/automatic-return106/`.
- [Delivery receipt with exact hashes and retained22.10 checkpoint](2026-10-22-private-field-delivery-receipt.json).
