# Android113 MESH reconnect incident — 4 November2026

## Current result and scope

Owner reports that MESH no longer connects after113 publication. This selects a bounded
FLEET-BOOTSTRAP-2 investigation, not another release or general MESH acceptance.
**NOT_FIXED:** Wi-Fi reconnect reaches CONNECTED and an ordinary application verifies IPv4
HTTPS egress through Netherlands2, but hostname HTTPS fails and a correlated carrier
failure/recovery occurs. A green connection indicator is not working DNS/HTTPS acceptance.

Public/invitation/owner stays0.1.18-beta113/code113; optional catalog7 is byte-identical
at14:56UTC. No product installation/source change, signing, server restart, admission/
policy change, profile reset or data clearing. Temporary probes are removed after runs.
At14:56 ADB is available but the app explicitly refuses snapshots with USB support disabled.
No bypass is attempted. The last accepted snapshot is CONNECTED; current state after
permission loss is not inferred. Further controlled phone checks need renewed app consent.

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

## Next gate and evidence

Renew explicit app USB support, then correlate A/AAAA wire queries and Android results on
one underlying network/native session; reproduce resolver/network selection and the exact
NL2 frame-loss sequence. Completion needs ordinary hostname DNS/HTTPS and stable reconnect,
preserving IPv6/DNS leak containment, identity, admission and bounds. A client fix still
requires exact platform/native CI, offline signing and in-place/public acceptance. Never
replace113 with different bytes or start an unrelated queued task automatically.

This turn changes documentation only. Temporary SDK35/JDK probe compilation succeeds with
one source8/bootstrap warning and deprecated-API note; it is not product CI. Raw private
evidence stays in ignored `state-client-build/android113-mesh-incident-20261104/`; no device,
session, support identity, keys or raw journals enter Git. No product deployment needs
rollback; do not restore databases or uninstall the product to address this incident.

Scoped PLAN/release/incident links and whitespace PASS. Full documentation scan retains
only the same two historical anchor errors as before this incident (October27 STATUS and
October24 source-checkpoint links); no new broken link is introduced. Product suites are
not rerun for this documentation-only checkpoint; live negative results remain failures.
