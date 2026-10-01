# Architecture map / Карта архитектуры

## Latest production attempt — 1 October 2026, rolled back

Controlled owner-only NL deployment reached bootstrap READY but exposed a timestamp
compatibility defect: Go context deadline serializes with local offset; Python
delivery/sync accepts only trailing `Z`. New service stopped/disabled and directory
quarantined; RU API/routes/sync remain undeployed. No live JSON/timezone workaround
or validity change. Normal production unchanged, same sole-canary authority.
Local non-UTC producer/consumer regression coverage is required before retry.
[Exact failure, remaining inert installation and rollback](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## Production restricted delivery — 1 October 2026, local only

**Authority preparation subsequently completed, not API deployment.** Under explicit
owner authorization, one production Friends restricted Family is now represented
by its ControlTrust-signed issuer delegation and one `restricted_grants` membership.
It is not a ProductStore `/v2` entitlement; no cross-store enrollment or new root.
The existing NL control-provider Device Identity was explicitly designated as the
Family gateway (mailbox/diagnostic identities not reused). Its private key stays
NL, online CA key stays RU, offline root stays local. Four accepted additive tables
exist; issuer/CRL/gateway materials are root-only staged and validated. Owner later
installed only final NL provider.env; opaque metadata/schema validation PASS.
No API routes, new services, room creation or phone delivery enabled. Current
CRL3 expires01.10 11:35:38UTC; renew before later use if expired, without extending
TTL or resetting floors. [Current preflight](releases/2026-10-01-5n-prod-deploy-preflight.ru.md)
and [initial authority checkpoint](releases/2026-10-01-5n-prod-authority.ru.md).

Deployment authorization was subsequently granted for `ff9fb09`. The read-only
09:32–09:33UTC preflight stopped because required RU issuer/sync and NL gateway/
provider material were absent at the runbook paths. No production component or
trust material was installed/generated. The implementation checkpoint below
remains local-only; see the gate report for current prerequisites and evidence.

5N-PROV-1 is **IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED**. Friends
`/friends/*` and its device/invitation DB remain distinct from ProductStore `/v2/*`.
Two bounded POSTs (challenge + semantic restricted-readiness fetch) use existing
activated Device Identity transport-key proof and ordinary authenticated HTTPS.
Initial provisioning does **not** require already installed Family mTLS. The server
rechecks device/invitation/Family grant, exact key binding, purpose-bound nonce,
revision, admission policy, expiry and signed CRL before issuance.

The existing offline control root signs a domain-separated **issuer delegation**,
not each directory. Android accepts the online Family CA only through that
delegation; no independent root or second client private identity is introduced.
Accepted Family TLS certificate/URI/OU/ALPN format is reused. The leaf binds the
existing device Ed25519 public key; Android assembles TLS private material only in
memory from its existing secure identity. API returns no private key. Global peer
revision floor and per-device grant revision remain distinct.

BOOT-1 v1 stays unchanged: bootstrap seed `join_url` is required, exported only
after READY. Existing Family-mTLS refresh remains for already provisioned core
paths; production adds authenticated Friends HTTPS delivery. No standalone
directory signature, OAuth in Android or prewarmed dedicated descriptor.
`OpenProvisioned` consumes the validated bundle → cached seed → Family auth →
Room Broker → fresh dedicated whole-device session using the accepted Orchestrator.

`RestrictedVault` is one no-backup AES-GCM/Android Keystore AtomicFile containing
public delivery, tombstone and monotonic floors. Existing identity/normal vaults
are untouched. Native verifies root delegation/X509/CRL/device/Family/directory
before commit; malformed/stale/unavailable refresh preserves valid old state.
Authenticated rejection disables restricted usability; offline revocation remains
bounded by signed CRL/session expiry, not instantaneous.

Prewarm after activation/normal profile success and foreground resume/60s checks:
single-flight,30s deadline, persisted300s attempt cooldown,300s near-expiry window.
No background polling; CONNECT doesn't wait for refresh with valid material.
Directory≤1h/8KiB/4 seeds unchanged; seed55min, CRL15min makes effective readiness
at most15min. Single-seed rotation/death can invalidate liveness before expiry;
no hours-long offline guarantee. [Implementation and historical BLOCKED audit](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
[API/schema, controlled deployment and rollback](../deploy/friends/restricted/README.md).

## Current product decision — resilient family connectivity

Authoritative rebaseline, **30 September 2026**. [STATUS](STATUS.md) records
implementation/deployment facts; [PLAN](PLAN.md) owns execution order. Dated 5N
reports retain their exact acceptance scope, failures and STOP boundaries. This
decision changes documentation and priorities, not runtime or rollout.

Family Connect is a **resilient connectivity service**, not a protocol picker.
The initial user is a technically capable family member helping relatives/devices
stay connected without repeated VPN configuration support. Families across
countries, including relatives in Russia, are an initial context—not a permanent
geographic restriction. The mental model is **Family → people/devices → connectivity**;
identity/invitation foundations exist, but no shared family dashboard is claimed.

Target UX: install → accept family invitation → CONNECT → automatic path selection
or recovery → CONNECTED. Normal states: **CONNECTING / CONNECTED / RESTORING
CONNECTION**. AWG, TCP, VP8, ReliableStream and gateway details belong in advanced
diagnostics. The MVP cross-transport implementation is now in source; full physical
acceptance and production distribution are not yet established by that implementation.
Continuity comes before benchmark speed, country count or protocol count; normal
networks should still use fast, inexpensive transports, with a restricted carrier
as fallback/recovery rather than mandatory default.

### Network capabilities, not a VPN-only model

In one user-reported Krasnodar cellular restricted/allowlist condition, Family
AWG 3.1 and TCP did not work while Yandex Telemost communication remained available.
The initial [25 September field observation](releases/2026-09-25-telemost-cellular-evidence.ru.md)
is clarified by the user in this rebaseline. It is not a universal statement about
Russia, operators, regions or time, nor a Family VPN FIELD-1 result.

Do not assume that the Internet is reachable and only VPN packets are filtered.
Model the device as having a changing **subset of network capabilities**: direct
Internet, AWG, TCP/Reality, Family control API, Telemost/service carrier, future
carriers. Reachability of one does not establish reachability of another. A normal
Telemost call is evidence of a service path, not proof of our bootstrap or VPN.

### Three planes and implementation maturity

- **IMPLEMENTED**: current beta/product foundations and normal transport lifecycle.
- **PROVEN EXPERIMENTAL**: isolated physical acceptance, not production integration.
- **PLANNED**: future boundaries/policy; not new runtime components.

```text
                       FAMILY CORE
           Device Identity / Family admission / policy
                         [IMPLEMENTED]
                               |
          +--------------------+---------------------+
          |                    |                     |
  CONTROL / PRODUCT    BOOTSTRAP / RECOVERY      DATA PLANE
  identity/invites/     obtain trusted setup      normal AWG/TCP
  entitlement/         when API unreachable     [IMPLEMENTED]
  provisioning/        [PROVEN EXPERIMENTAL]     restricted Mux/DNS/TCP
  signed config                |                over Family TLS
  [IMPLEMENTED]                |                [PROVEN EXPERIMENTAL]
  Room Broker                  |                     |
  [PROVEN EXPERIMENTAL] <-------+                     |
          |                                          |
          +------ Connectivity / Transport Orchestrator ------+
                  [MVP implemented; acceptance not passed]     |
                        |              |                      |
                  AWG adapter     TCP adapter        service carrier adapter
                  [IMPLEMENTED]   [IMPLEMENTED]      Telemost VP8/RTP
                                                     + ReliableStream
                                                     [PROVEN EXPERIMENTAL]
                                                     future carriers [PLANNED]

  OS boundary (not a wire layer below every transport):
  Android apps <-> existing VPN lifecycle / packet adapter [IMPLEMENTED]
                 -> normal transport engines [IMPLEMENTED]
                 -> 5N Mux/DNS/TCP core binding [PROVEN EXPERIMENTAL; EU-6 physical PASS]
  Future iOS PacketTunnel adapter [PLANNED; no iOS client]
```

This is a responsibility map, not a claim that all transports share one wire
stack or already run under a new orchestrator. Room Broker belongs to the
control/product plane; bootstrap must make its authenticated setup reachable
without assuming ordinary API access. **Cached-state restricted bootstrap passed
isolated physical acceptance**; full-device integration also passed EU-6 in the
isolated primary-user route/backend/app scope, not production or modem-wide pcap.
Its opt-in implementation reuses ConnectionService/TcpVpnService and the existing
Xray/gVisor packet engine, with shared `carrier/wholedevice` and per-session
protected `carrier/underlay`. TUN routes activate only after dedicated Family
TLS/binding/Mux readiness. IPv6 and unsupported UDP are captured/rejected; session
failure retains TUN rather than enabling direct fallback. This is not a new
Orchestrator, always-on lockdown, or a public release. Exact physical maturity:
[EU-6 report](releases/2026-09-30-webrtc-eu6-android-full-device.ru.md).

### Accepted restricted path

```text
Core TCP streams + DNS wire queries -> Mux -> Family TLS 1.3
  -> ReliableStream (selective repeat/SACK) -> Telemost VP8/RTP
  -> real service SFU -> Amsterdam -> Family TLS/Mux -> TCP Internet / Family DNS
```

| Gate | Accepted evidence (PROVEN EXPERIMENTAL) |
| --- | --- |
| [5N.1](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md) / [5N.2](releases/2026-09-27-webrtc-eu2-android-binary.ru.md) | Real VP8/RTP carrier; physical Redmi Note 9 Pro Android 12 joins Amsterdam; shared Go core, separate diagnostic APK. |
| [5N.3](releases/2026-09-27-webrtc-eu3-family-session.ru.md) | Family TLS 1.3 authentication with DeviceIdentity/ProductStore-derived disposable authorization; negative admission/replay/lifecycle checks. |
| [REL-1](releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md) / [PERF-2](releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md) | Selective-repeat ordered bytes below TLS; real RTP gap recovery; demonstrated reliable goodput 1.742311 Mbit/s over 30 minutes, not a capacity ceiling. |
| [5N.4](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md) | Real outbound TCP to Internet; verified end-site HTTPS TLS, no gateway MITM. |
| [5N.5](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md) | Four simultaneous public HTTPS streams; 304.138s mixed TCP + Family DNS, exact bytes, fair scheduling and bounded buffers; destination DNS containment/hardening. |
| [5N-RB-1](releases/2026-09-28-webrtc-5n-room-broker.ru.md) | Official Telemost API, server-side OAuth only; gateway joins first/READY, physical Android obtains automatic descriptor and joins; Family TLS + four verified HTTPS200; no manually supplied room URL. |
| [5N.6](releases/2026-09-30-webrtc-eu6-android-full-device.ru.md) | Cached BOOT-1 → dedicated → existing Android VPN/TUN; ordinary Chrome2 sites,14 concurrent TCP/98 Family DNS,543.7s light smoke, protected underlay, UDP/IPv6 rejection and VPN-retained session failure. No traffic forwarding/manual room URL. |

**Room Broker itself is PASS.** Its accepted temporary control ingress used SSH
forwarding + adb reverse. The real media/data path used Telemost, not that
forwarding. It did not prove initial setup on a whitelist network with the Family
API unavailable. [DNS containment](testing/webrtc-dns-containment.ru.md) proves
tested core destination handling, not whole-device browser/OS DNS interception.

No production restricted bootstrap, product-complete cross-transport orchestration,
beta-user restricted rollout or Krasnodar FIELD-1 exists yet. Whole-device 5N
binding is isolated/opt-in; its acceptance is recorded separately below.
There is no generic UDP/QUIC/ICMP in the restricted
path; global ReliableStream HOL and lack of seamless session migration remain.
No production multi-user capacity claim follows from these single-device proofs.

### Restricted bootstrap — 5N-BOOT-1 (PASS, isolated physical)

```text
cached authenticated bootstrap directory -> bootstrap rendezvous carrier
  -> Family authentication -> REQUEST_TRANSPORT -> existing Room Broker
  -> fresh dedicated room (gateway READY) -> dedicated Family Session
```

Goal: obtain an authenticated dedicated descriptor when the ordinary control API
is unreachable but a permitted service carrier is reachable, without manual URL,
operator forwarding or an engineering harness. The bootstrap channel is
**control-only / rendezvous-oriented**, never the permanent bulk VPN.
[BOOT-1 core/runbook](../carrier/bootstrap/README.md) implements directory delivery
through existing Family mTLS, a protected atomic Android diagnostic cache, a
separate READY-only seed and one bounded authenticated exchange. The existing
Room Broker owns dedicated creation, setup binding, revocation/revision checks
and cleanup. No new signing root and no application-update key are involved.
The seed packet lease is routing only; Family TLS remains the security boundary.
Bootstrap never constructs a TCP/DNS Mux. The dedicated session uses the existing
data path after bootstrap closes. Physical acceptance30 September **PASS**:
Redmi cellular, cached directory/restart, deliberately unreachable diagnostic
control endpoint, real Telemost bootstrap, dedicated binding/DNS/four HTTPS200,
cleanup; no control forwarding or manual room URL. The endpoint-denial injection
is not a carrier-wide/production API firewall block or FIELD-1 proof; see the
[exact evidence and limitations](releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md).
Fresh installations already inside a restricted network are out of scope;
the device must have obtained its directory during earlier normal connectivity.

### Full-device boundary and MVP orchestrator

5N.6 / WEBRTC-EU-6 connects the **existing Android VPN lifecycle and packet path**
to the existing 5N mux/DNS/TCP core. ConnectionService remains the authoritative
owner; RestrictedTunnelEngine reuses TcpVpnService and the pinned Xray/gVisor
ConnectionHandler/LinkEndpoint packet boundary. The new in-process JNI adapter
uses same-process descriptors with VpnService.protect, unlike the earlier
child-process core harness. Shared carrier/wholedevice owns flow/DNS/session
behaviour, and carrier/underlay protects every network factory before connect/bind.
TUN activates after cached BOOT-1, separate dedicated Family TLS/setup binding
and Mux readiness. IPv4 TCP and Family DNS are supported; IPv6 and generic UDP
are captured/rejected. Session loss retains the VPN routes, closes app flows and
reports unavailable; explicit stop releases native state before TUN/service.
This shared boundary permits a future iOS PacketTunnel adapter; neither iOS nor
always-on process-death lockdown is implemented. The accepted5N.6 explicit diagnostic
selection remains available. Manual normal AWG/TCP factories remain unchanged.

`ConnectivityOrchestrator` now implements a bounded deterministic policy: configured
normal last-known-good/preferred → other configured normal → BOOT-1 cached recovery.
CONNECT/RESTORING have300s deadlines, normal20s and restricted200s candidate budgets,
no per-candidate retry, one automatic restoration pass per user CONNECT. Explicit
auth/config/internal failures terminate. A healthy selected path is sticky; no faster
path probes or seamless flow migration. Preferences contain normal transport IDs only.

`AutomaticConnection` runs under the existing ConnectionService operation owner and
worker. `AutomaticVpnOwner` holds full IPv4/IPv6 routes in the existing TcpVpnService
before configuration/startup and across backend cleanup/failure. `AutomaticNormalEngine`
uses existing AWG JNI/NativeTcp on that same service; it never starts a second
GoBackend VpnService. New guard establishment precedes old fd closure/backend stop.
RestrictedTunnelEngine uses this owner and shared `wholedevice.OpenCached`; no fake
loopback control probe is required in Auto. Failed sessions retain a guard until
DISCONNECT; explicit OS revocation/process death still require platform lockdown
for a stronger guarantee. Opaque restricted session loss is conservatively terminal
because the existing native API cannot distinguish revocation from network loss.

Main/Friends default to Auto; explicit manual diagnostics and managed journal policy
remain available. Local atomic diagnostics contain at most128 state/candidate/category/
elapsed-time events, no traffic/URL/destination data. Restricted activation/native
packaging is still an opt-in diagnostic integration, not a public beta rollout.
[Orchestrator implementation/acceptance ledger](releases/2026-09-30-mvp-connectivity-orchestrator.ru.md)
and [metrics/phases](PLAN.md) distinguish code, physical proof and distribution.

### Replaceable adapters and security

Telemost is the **first proven restricted service carrier**, not the product or a
permanent dependency. Provider logic remains in adapters, including
[RoomProvider](../carrier/roombroker/README.md). Provider/SFU/signaling are untrusted;
**Device Identity / Family admission / Family TLS** protect Family sessions and
authorize egress. Room secrecy is not a security boundary; provider OAuth stays
server-side. End-site HTTPS validation remains separate from Family TLS.

No second exotic carrier is on the current critical path. VK/WB/other services
stay backlog until field evidence or privacy-safe telemetry demonstrates a
meaningful coverage gap or reliability need. Home Gateway, RNS-over-WebRTC,
FEC/HOL optimisation and further performance tuning are secondary/evidence-driven,
not prerequisites for the next gate. Reticulum control/recovery/messaging and the
[Home Gateway design](reticulum/HOME_GATEWAY_DESIGN.md) remain separate retained
workstreams, not proof of a deployed restricted bootstrap. Earlier 25 September
Home/WB-first ordering is historical; [PLAN](PLAN.md) supersedes it.

## Personal Gateway / Reticulum Transport

Retained secondary/backlog design: Android ↔ Windows Home PC for LAN/NAS/RDP or
residential egress, with Reticulum control/discovery and a selected encrypted data
transport. Home Gateway is not implemented or required for the accepted Android→EU
path. [Historical design and gates](reticulum/HOME_GATEWAY_DESIGN.md) remain available;
the current product sequence is bootstrap → full-device → Orchestrator → FIELD-1.

## Product and device path

Invitation/entitlement → device identity → provisioning → client verification and
protected state → platform VPN adapter → transport/gateway.

- [Registration: EN](registration.en.md) / [RU](registration.ru.md): product admission,
  single-use challenges and entitlement. Dated module boundaries are historical.
- [Device identity ADR: EN](adr/001-identity-provisioning.en.md) / [RU](adr/001-identity-provisioning.ru.md).
- [Provisioning/cache: EN](provisioning-provider.en.md) / [RU](provisioning-provider.ru.md).
- [Stage 5 control design](stage5-architecture.ru.md) and [native binding](stage5-native-binding.ru.md):
  signed configuration delivery, verification and recovery. Initial AWG/platform limits
  in these dated documents are superseded where STATUS has newer runtime evidence.
- [Android source](../clients/android/), [Linux source](../clients/desktop/),
  [Windows source](../clients/windows/).

Android friends currently exposes AWG 3.1 and TCP REALITY options. Desktop releases
have their own capabilities and activation; see STATUS for current versions. Do not infer identical feature support
from shared architecture. Device provisioning/configuration is distinct from the
[offline-signed application update catalog](updates.en.md).

## Messenger

[Design](reticulum-messenger.ru.md) · [Core](../messenger/README.ru.md) ·
[Android voice/UI checkpoint](releases/2026-09-23-voice-scroll-beta49.ru.md) ·
[Foreground delivery/animation evidence](releases/2026-09-19-android-beta16.ru.md).

The core uses separate chat identities, encrypted storage and existing RNS/LXMF
components. Android integrates native screens and a carrier. Early core notes saying
there is no Android UI are historical, not the current pilot state. Android now has a foreground delivery service, notifications, text edits and voice.
Screen-off notification delivery was confirmed; deep Doze latency and broader
restart/offline acceptance remain open. There is no FCM integration.

## Experimental relay network

[Original QUIC architecture and threat model: EN](architecture.en.md) /
[RU](architecture.ru.md) · [Data plane: EN](data-plane.en.md) / [RU](data-plane.ru.md).

The inner/outer QUIC laboratory is separate from the current Android VPN data path.
Its mTLS, revocation timing and failover claims must not be generalized to every client.

## Trust and operations

[Security](../SECURITY.md) · [Privacy](privacy.md) ·
[Documentation map](README.md) · [Current plan](PLAN.md).
