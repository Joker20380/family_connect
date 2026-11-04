# Android117 — protected ICE route, 4 November 2026

## Scope and current boundary

Continuation of the owner-selected MESH stability incident, not another queued task.
Android0.1.18-beta117/code117 is built and qualified, still unsigned; installed owner remains signed116
(`3ee68c6211b2e438a3250504674a3b8e676c597b6cc00863b9fb0cabe0a56aba`).
Public/invitation/updater stays113/catalog7; public links/checksums are not changed.
Linux/Windows releases are unchanged. No signing, installation or publication in this
qualification checkpoint. Both NL gateways retain the same running70e6c0fc executable from
[the unified delivery](2026-11-04-unified-mesh-stability.md); no server mutation here.

## New system evidence and limits

Read-only Android connectivity metrics show cellular NETWORK_DISCONNECTED at local
22:05:48.860, with the phone UTC offset independently read as+0100. ConnectivityService
stops that network's keepalives with error-20 at22:05:48.852455; Wi-Fi's cellular-state
observer changes at22:05:48.878754. The VPN network advertises Wi-Fi+VPN, was connected
at22:04:34.495, and is not disconnected until22:07:47.238 during the later normal stop.
Cellular reconnects at22:07:30.581. These are separate network identities, compared
privately; no identifiers, addresses, SSIDs, credentials or raw dumps are committed.

This cellular loss coincides with the paired116 ACK stall around21:05:48UTC and
precedes client ICE/peer disconnected by about5s and reliable DATA expiry by about20s.
The original probe's unchanged VPN handle did **not** prove unchanged physical underlay.
The original session did not retain its selected local candidate address/interface:
the correlation alone does not conclusively attribute that session to cellular.
Unrelated cellular loss is a concrete regression scenario, not proof that all MESH
outages share one cause. No radio/network settings were changed to obtain this evidence.

## Reproduced defect and correction

`telemost.webRTCSettings` previously accepted every IPv4 interface while Android's
`VpnService.protect` only bypassed VPN routing. Pion could gather host and STUN candidates
from a non-default cellular interface or the VPN address instead of the protected route.
Both publisher and subscriber use this settings path. Server code with no protected
underlay retains its existing IPv4 policy; there is no wire or server compatibility change.

`underlay.Network.RouteIPv4` now opens one protected UDP socket to the existing numeric
resolver target, reads its kernel-selected local address, and closes it without writing
any payload or performing DNS resolution. Pion's host and STUN gathering use an exact
IPv4 filter for that address. A rejected/closed/cancelled protector fails initialization;
there is no fallback to all interfaces or an unprotected socket. No new endpoint, timer,
retry, auth exception, network request, radio control or active-owner eviction is added.
The route is selected per peer setup, not claimed to migrate an established session
seamlessly when its actual physical network disappears.

## Verification

- Before correction, real local Pion gathering advertises an address outside the
  protected route; denied, closed and cancelled protection initialize ICE incorrectly.
  Four leaf regressions fail. An initial test API compile error was corrected before
  recording that executable red result; it is not counted as a reproduced behavior bug.
- Ten race-enabled repetitions pass for route selection and real Pion host/STUN
  gathering, including a synthetic extra interface address without changing host network
  configuration. Negative protection cases pass; route lookup writes no UDP payload
  and does not invoke DNS.
- Full `underlay`, `telemost`, `reliablestream` with Go1.26.1, `-race` and
  `fc_perf_diagnostic`:239 PASS test/subtest events,6 optional fixture/provider/helper
  skips, zero failures. New protected bidirectional VP8 checks byte-exact1/4096/65536-byte
  messages in both directions. Three additional repetitions of that check plus real
  Pion transient/persistent packet-loss recovery:6 PASS, no skips/failures.
- Release/provenance and unified-source Python contracts:46 PASS. Diff whitespace check
  passes. No Android UI/native artifact or physical117 acceptance is inferred from these
  local checks. Server admission tests are not substituted with a new all-suite PASS.

## Delivery gates and rollback

Source commit`5a0f6e0375e8a27c009956378e72c96a37385ad6` is pushed to the existing
`main` upstream with equal remote SHA. Exact Client builds`41917441995` attempt1 and
Android job`126880803015` pass. Readiness41917442025 passes. Separate phase041917442194
fails at failover stack construction and release-fixture provisioning; Linux control
41917441984 fails at release-fixture provisioning. These steps also failed for116;
their underlying errors are not reanalyzed here. No whole-repository CI-green claim.

Downloaded archives are bound to5a0f6e0/run41917441995 and their GitHub digests:

| Artifact | ID | ZIP SHA256 |
| --- | --- | --- |
| ARM64 |13367556375|`707e1a296e63e712d1fce4b3596a9c00b6f3f8b7fd122bef419435963c2bca1d`|
| Debug/JVM |13367661185|`f0f120516a2ca3d2337f0605d5daf4d911efd72e7142fc347845fae969c6704c`|
| Runtime |13366663348|`9742a285fd37c66e5fde708f5798ae4a0cd3e864d4779f8b273591845d57dd63`|
| UI |13366862803|`80a6c31751180ffe5c8b898c00dbb90899379fe86faa91c05b30d77dcbc75097`|

Unsigned ARM64 APK:50,262,297 bytes, SHA256
`07d88bef1f5aafbc9da0664d0c77454f56f84061206bb3e21ffec8beebb50eea`.
Package/version/minSDK27/target35/nondebuggable,12 native libraries, exact source/tree,
JNI/ABI/ELF16K/ZIP16K, source/licenses and disabled-provisioning checks pass.
JVM:419 debug+414 Friends pass without skips. API35:28 debug pass/25 skips and19 Friends
pass/4 skips; API27:27/26 and18/5 respectively. These runtime tests are not physical
restricted-MESH acceptance. Eight downloaded UI images actually reviewed: RU/EN three
nodes, large text, green/orange87% squares, CPU distinction, failure controls and legacy
Codec2 compatibility text fit. Two extra117↔116 real-Pion mixed runs:8 PASS, no skips.

Later read-only server checks confirm both running executable hashes still70e6c0fc,
active/NRestarts0, with PIDs1293513 and1184264. Those PIDs differ from the earlier
delivery; this readback is not proof of uninterrupted uptime since20:28UTC. This task
does not restart services or change the common writer, profiles, identities or policy.

Independent synthetic API27 storage upgrade116→117 passes with the same disposable
UID and distinct processes: identity, journal/outbox and atomic-interruption recovery.
The Java storage test source is unchanged betweena597d2a and5a0f6e0. This is a local
x86_64 Java-storage fixture retaining prior generated native inputs, **not** the
release ARM64 native artifact or a physical phone check. Fixture SHA256:
`c16d09adf1df5e15fda16535fe3924661569e7d0284eed6c1b86a4261bd89137`.
Fresh disposable signing key only; no product-key access. The owned emulator is stopped.
Receipt/build logs remain private in`state-client-build/mesh-ice-route-20261104/`.

1. Finish targeted native/race, protected bidirectional VP8 and existing transient-loss
   coverage; retain failures/skips. Check release provenance/contracts and diff hygiene.
2. Push source117, then inspect exact platform CI and downloaded ARM64 artifacts,
   source/ABI/16K/licenses/API27/API35/UI and in-place retained-data gates. No replacing
   already published113 or already signed116 with different bytes.
3. Sign only accepted assets with the existing offline product key via the protected
   local vault workflow. Install over116 without uninstall/data clearing/reenrollment;
   confirm exact package and retained identity with renewed app consent when necessary.
4. Run bounded paired same-session ordinary-UID DNS/HTTPS/egress and cleanup/reconnect
   on both NL nodes, including a controlled unrelated-underlay-loss scenario only when
   its network-control authorization and restoration are explicit. No failure-loop probes.
5. Public distribution and sustained stability remain OPEN until their separate gates
   pass. Server binaries stay equal; do not redeploy gateways merely for this client fix.

Source can be reverted without changing installed runtime. Preserve signed116 and both
node-specific rollback custodians from the unified report. Any owner rollback must use
an accepted higher-version compatible package with the same signer, not uninstall or
data reset. Private evidence lives under
`state-client-build/mesh-unified-20261104/physical116/network-readback/` and adjacent
`ice-route-*` logs; raw phone/system data is ignored and remains local.
