# Per-app Android routing fixture

This directory is exclusively a synthetic, disposable-emulator fixture. Alpha
and Beta are separate APKs/UIDs. They issue their own default-network DNS and
certificate-verified HTTPS requests; neither shell traffic nor two requests from
the VPN owner count as independent application routing.

`fixture.py` starts a real pinned AWG userspace peer and pinned Xray REALITY peer,
plus distinct direct and VPN TLS responders. Its CA/key are generated per run.
Only the CA in `probe-assets/` belongs in probe APKs. Never pass the entire output
directory as `fcProbeAssets`. The static WG/REALITY keys and UUID in these sources
are test-only and have no production authority. No production profiles are used.

The direct emulator DNS must be reachable; the local run uses the emulator's
`-dns-server 1.1.1.1`, without changing host or production resolvers. A direct DNS
failure is fixture/network unavailability, not split-tunnel acceptance.

The synthetic DNS responder supports UDP and framed TCP on port53. Xray routes
both there, never to the HTTPS responder. Port853 is explicitly rejected: this
stand does not implement trusted DNS-over-TLS/QUIC. Android Private DNS settings
are not changed; strict Private DNS is not qualified by this fixture. Opportunistic
validation must fail normally instead of entering an unrelated HTTPS handshake.
The default-network `InetAddress` probe,8-second lookup deadline and independent
UID/address assertions are unchanged. Bounded `fixture/dns.json` records only
protocol/type/send time (no query names/material); it is retained with Xray logs.
`FC_APP_VPN_XRAY=/path/to/pinned/xray-peer python -m pytest -q tests/test_app_vpn_dns.py`
reproduces the old TCP53/853-to-HTTPS misrouting and verifies the corrected routes
with actual Xray, plus UDP/TCP framing, malformed input and joined stalled-client
cleanup. This local routing test is not Android or REALITY acceptance.
The TCP DNS listener, like Go's listeners, uses SO_REUSEADDR for closed-connection
TIME_WAIT on sequential API runs; it never uses SO_REUSEPORT or shares a live
listener. The separate TCP lifecycle fixture reserves its endpoint with the same
option plus exclusive listen, then still proves the spawned peer's PID/inode.

The MESH policy test invokes the production owned-TUN attachment and uses the
REALITY carrier behind it. This proves Android application selection and guard
replacement, **not MESH wire, cold-entry, readiness or provider qualification**.
Auto tests run its real AWG/TCP handoff and native carrier DNS health, with a
debug-only lost-carrier trigger. They do not fake routing results.

Private outputs, emulator images, generated native code, keys, probes, APKs and
screenshots stay outside Git. Run one emulator at a time under the repository's
shared qualification lock; the owner's host requires KVM/NVIDIA rendering.

The dedicated instrumentation class is `AppVpnRuntimeTest`, enabled only with
`fc_app_vpn=true`. It rejects physical devices. The ordinary historical lifecycle
suite does not silently count this opt-in class as routing acceptance.

Implementation and acceptance are still in progress; see the dated task report.
