# Windows TCP native engine acceptance

Operator/CI-only preview component. It is not included in the stable desktop installer
and does not yet add connect/import/fallback actions to the Windows broker or GUI.

Xray is built on Windows amd64 from the same revision as Linux TCP:
d2758a023cd7f4174a5a5fa4ff66e487d4342ba0, Go1.26.1. Wintun0.14.1 is obtained from
https://www.wintun.net/ with its published SHA256 and checked using Windows Authenticode.
Signed Wintun binaries are distributed under the license included in their ZIP;
the preview includes Xray and Wintun licenses. Do not replace the existing WireGuardNT DLL.

The isolated Windows CI runner executes two fresh Xray client/server pairs. Each client
creates an actual Wintun adapter; six synthetic HTTP requests use a single test route
198.18.0.1/32 through TUN, local VLESS and a loopback HTTP fixture. No public VPN profiles,
credentials or gateway access are used. This tests Windows TUN + VLESS runtime, NOT
REALITY handshake or Internet VPN routing. Default routes and DNS are preserved.
Only the uniquely named test adapter/address/route is touched. Forced client termination
is followed by exact test-route/address cleanup and adapter-removal verification.

The build manifest records source/toolchain and binary hashes. The CI artifact is a
preview, not an authenticated updater payload or release. Packaging into the broker,
encrypted profile storage, REALITY configuration, routing/DNS lifecycle and WG→AWG→TCP
recovery remain separate integration gates. User network/load tests stay deferred.

Upstream source: https://github.com/XTLS/Xray-core/blob/d2758a023cd7f4174a5a5fa4ff66e487d4342ba0/proxy/tun/tun_windows.go
