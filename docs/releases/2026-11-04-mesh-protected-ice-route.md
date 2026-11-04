# Android117 — protected ICE route, 4 November 2026

## Scope and current boundary

Continuation of the owner-selected MESH stability incident, not another queued task.
Android source is0.1.18-beta117/code117; installed owner remains signed116
(`3ee68c6211b2e438a3250504674a3b8e676c597b6cc00863b9fb0cabe0a56aba`).
Public/invitation/updater stays113/catalog7; public links/checksums are not changed.
Linux/Windows releases are unchanged. No signing, installation or publication in this
source checkpoint. Both NL gateways retain the same running70e6c0fc executable from
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
