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
