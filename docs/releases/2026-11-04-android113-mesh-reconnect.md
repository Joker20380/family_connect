# Android113 MESH reconnect incident — 4 November2026

## Current result and scope

Owner reports that MESH no longer connects after113 publication. This selects a bounded
FLEET-BOOTSTRAP-2 investigation, not another release or general MESH acceptance.
**SOURCE_FIX_ONLY, live incident still OPEN:** Wi-Fi reconnect reaches CONNECTED and an
ordinary application verifies IPv4 HTTPS egress through Netherlands2, but DNS failures and
a correlated carrier failure/recovery occur. Renewed USB consent enables a bounded wire
comparison and a deterministic packet-level DNS fix below. No corrected APK is installed.
A green connection indicator is not working DNS/HTTPS or sustained stability acceptance.

Public/invitation/owner stays0.1.18-beta113/code113; optional catalog7 is byte-identical
at14:56UTC. No product installation, signing, server restart, admission/
policy change, profile reset or data clearing. Temporary probes are removed after runs.
At14:56 the app refuses snapshots with USB support disabled; no bypass is attempted.
The owner subsequently renews consent: snapshots work again and confirm CONNECTED on Wi-Fi,
unchanged113/P1. The source fix does not change the currently running app.

## Services and renewal

Read-only inspection confirms RU HTTP and both NL MESH units active. NL2 uses its existing
separately pinned known-hosts file after the default lookup refuses; no TOFU or changed
SSH verification. Renewal/directory timers are active. Scheduled renewal COMMITTED at
14:10:48UTC;14:24 is NOOP, not the earlier unprepared STALE_NODE_STATE incident.

At renewal, RU HTTP stops14:10:03–14:10:44; primary MESH stops14:10:05–14:10:37, seed ready
14:10:39. Secondary is active since14:10:39. Phone history includes a terminal session at
14:10:26 and a separate carrier/signaling read-error termination14:24:00. Planned service
interruption and later transport failures are distinct, not one proven universal cause.

Read-only receipt inspection binds the known device to valid READY acknowledgments for113
on both gateways. Primary foreground prewarm is distinct from secondary VPN readiness:
the latest general refresh alone does not identify the selected node. Exact native session
correlation below identifies Netherlands2. No synthetic request substitutes for its ACK.

## Phone and underlying networks

- At14:32 the snapshot reports Wi-Fi, but failing readiness is explicitly CELLULAR-bound:
  HTTPS connect/TLS/write TIMEOUT, then RNS UNAVAILABLE and cache fallback. Connectivity
  inventory contains validated Wi-Fi and cellular Internet networks.
- At14:34 controlled normal support Connect obtains fresh READY but fails SEED_CONNECT
  after15,003ms, cause UNKNOWN, caller context LIVE. Its failed VPN capture is subsequently
  disconnected through the ordinary support API. No timeout/authentication limit is changed.
- `ChatNetworkAndroid` and `AutomaticVpnOwner.resolver()` use the first eligible
  `getAllNetworks()` entry, not a consistently selected default physical network. Native
  VPN sockets use `VpnService.protect` without binding to that resolver network. This is
  a concrete consistency risk, **not proven packet-level causation of this15s failure**.
- By the independent underlay probe only validated Wi-Fi is eligible; no agent command
  changes Wi-Fi/mobile settings. Default and first-eligible network/resolver now match;
  bounded raw DNS receives valid replies and provider HTTPS returns200. The earlier
  simultaneous cellular/Wi-Fi condition is not reproduced by that later observation.
- At14:42:56 controlled Connect uses fresh Wi-Fi readiness and succeeds on unchanged113/P1.

## Correlated second-node failure and recovery

The14:42 session's exact private native tag matches37 records on **nl-amsterdam-2**,
not unrelated primary-node sessions:

| UTC | Observation |
| --- | --- |
|14:45:04.426 |Gateway CARRIER/FAILED, RELIABLE_FRAME_TIMEOUT, RELIABLE_EXHAUSTION; age20,061ms, retries5, pending8 |
|14:45:04.927 onward |Gateway closes carrier; Family TLS/session close follows |
|14:45:05.339 |Client IO_CLOSED/recovery_exhausted; subscriber-disconnected observation retained |
|14:45:09.858 |New client startup begins |
|14:45:34.825 |Automatic restoration reaches CONNECTED; same connection lifecycle, new native session |

Gateway frame timeout precedes the client terminal state. Media loss, framing/retransmit,
scheduling and provider behavior still need separation. Blind timeout increases or server
restarts are not a root fix. Successful restoration does not erase the negative result.

## Ordinary application traffic

A disposable package uses a normal application UID/default VPN network, normal certificate
verification and bounded public requests. Egress has no Family credentials/native shortcut,
socket protection or explicit underlay binding. All attempts are retained:

1. First egress fails DNS with UnknownHostException around carrier recovery.
2. After restoration DNS succeeds, but hostname HTTPS fails with ConnectException.
3. In one unchanged native session, `www.cloudflare.com` resolves to0 IPv4/2 IPv6 addresses;
   hostname HTTPS fails in11ms. Verified HTTPS to `1.1.1.1/cdn-cgi/trace` returns200 in2,747ms
   with **Netherlands2** egress. VPN/default network/native session remain unchanged.

Whole-device transport deliberately denies IPv6 connections, so an IPv6-only DNS result
cannot work here while IPv4 HTTPS can. Why the A answer is missing is **not established**:
loss/timeout, Android resolver caching, network selection and response handling need
separation. Do not claim general Internet acceptance from an IP-literal request or change
DNS semantics without a reviewed contract and positive/negative regression tests.

## Renewed consent: wire comparison and source fix

The disposable ordinary-UID probe uses only the active VPN and its advertised10.79.0.1
resolver: no protected socket, physical-network binding or product credentials. Before/after
snapshots retain the same native session and CONNECTED state. Probe removed after execution.

| Request | Result |
| --- | --- |
| UDP A, www.cloudflare.com | Timeout8,005ms |
| UDP AAAA, same name | Two AAAA records,272ms |
| TCP A, same name | Two A records,127ms |
| Paired UDP AAAA+A on one port | Both replies,513ms |
| UDP A/AAAA, TCP A, paired UDP for example.com | All replies,234–436ms |
| Android resolver/HTTPS, www.cloudflare.com | Two A/two AAAA; HTTPS200,978ms |
| Android resolver/HTTPS, example.com | UnknownHostException despite preceding wire replies |

This rules out universal A suppression or a consistently IPv6-only upstream. Intermittent
UDP loss is established; Android resolver caching remains a possible additional factor.
The exact missing live packet was not traced through every internal boundary.

The unchanged pinned Xray/gVisor fixture establishes a concrete local defect:16 completed
UDP DNS requests on different source ports leave16 idle flows until the10s flow deadline.
The17th request is silently dropped at the packet boundary before wholedevice/Mux admission;
wholedevice shows active16/dns16/limit_denied0. This red test uses no external resolver,
provider or phone. The normal Android resolver's short-lived UDP sockets can hit this cap.

The fix opens an optional datagram callback in the existing pinned packet boundary and
routes Android DNS packets directly to bounded wholedevice queries, instead of retaining
idle UDP pseudo-connections. Query bytes are owned before asynchronous dispatch; replies
retain their original source/destination and DNS contents. The same16-slot budget now
counts in-flight queries, not completed requests waiting for nonexistent UDP close events.
No higher flow limit, timeout increase, AAAA filtering, IPv6 enablement or fallback resolver.
TCP DNS, ordinary TCP, other packet consumers and generic Mux DNS semantics stay unchanged.
The existing MPL patch/notice delivery remains required; no dependency pin changes.

Qualification:

- Pre-fix pinned packet regression: query17 fails, retained as red evidence.
- Patched packet tests: `go test -race -count=10` PASS, including64 sequential source ports,
  paired same-port replies and existing TCP/UDP-denial/session-failure coverage.
- Wholedevice, restrictedchat, restrictedowner and desktopmesh: race/count5 PASS. New tests
  cover copied packet ownership,16 pending queries, cancellation/close, output errors,
  rejected sizes/IPv6/non-DNS destinations and no direct-network fallback.
- Python release-payload/MESH/correlation contracts:44 PASS.
- The initial broad count5 TCP-forward run reaches its180s harness deadline in existing
  speed-profile tests; retained as a failed run, not a complete-suite PASS. Subsequent focused
  DNS/hostname HTTPS race/count5 PASS; full TCP-forward race/count1 PASS in35.8s.
- Native build now runs pinned packet race/count3 tests before cross-compiling, so future
  hosted Android builds must exercise this path rather than only shared carrier tests.

Source **cf9d576c11e2bf1e12d16030d4bbbfb15e6f9fcb** is committed, pushed and remote-SHA
verified. Local exact-source normal ARM64 build (Go1.26.0/NDK28.2.13676358) passes its new
host packet/race gate. ELF AArch64 shared library, all four LOAD alignments16,384 and
embedded MPL patch identity PASS. This is a native library only, not an APK or installation:

- Native SHA256: `7d15a2738c28b58bde99a382134c2940ec1b2f36ed8d9f2c3b4a163b445c1c8d`.
- Patch SHA256: `770f8f359faf0630a271f103bcd31033eb46d30aeb531b5933c15058c624b420`.
- Source tree: `6566bc43e301da76145671bf21c92ca20887bed9`.

[Client builds41857785568](https://github.com/Joker20380/family_connect/actions/runs/41857785568)
and phase041857785734 start for this exact source. Client qualification is IN_PROGRESS;
Android is building its unified VPN library, not yet at API27/API35/native delivery gates.
The earlier113 CI receipt does not qualify this fix. No signing or distribution until the
new immutable version's exact gates and artifact checks pass.

15:28UTC final readback: unchanged113/P1 CONNECTED on Wi-Fi, native state2/NONE and the same
private native tag as the wire probe. Disposable package absence verified. No product
installation, support connect/disconnect, phone network-setting change or server mutation
in this renewed-consent follow-up. This readback is not corrected-binary acceptance.

## Next gate and evidence

Exact hosted source CI and a new immutable version are required before offline signing,
in-place installation and ordinary-app DNS/HTTPS acceptance. Do not re-sign/re-publish113.
Separately reproduce underlying-network/resolver selection and the exact NL2 frame-loss
sequence; the DNS fix alone does not explain those failures. Completion needs stable reconnect,
preserving IPv6/DNS leak containment, identity, admission and bounds. A client fix still
requires exact platform/native CI, offline signing and in-place/public acceptance. Never
replace113 with different bytes or start an unrelated queued task automatically.

This follow-up changes DNS source/tests/build gating and documentation. Temporary SDK35/JDK probe compilation succeeds with
one source8/bootstrap warning and deprecated-API note; it is not product CI. Raw private
evidence stays in ignored `state-client-build/android113-mesh-incident-20261104/`; no device,
session, support identity, keys or raw journals enter Git. No product deployment needs
rollback; source can be reverted normally before any delivery. Do not restore databases
or uninstall the product to address this incident.

Scoped PLAN/release/incident links and whitespace PASS. Full documentation scan retains
only the same two historical anchor errors as before this incident (October27 STATUS and
October24 source-checkpoint links); live negative results remain failures. Exact hosted
CI, corrected installed/public version and physical post-fix acceptance are still pending.
