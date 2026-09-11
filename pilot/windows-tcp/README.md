# Windows TCP native engine acceptance

Operator/CI-only preview component. It is not included in the stable desktop installer.
The broker now implements connect-tcp and session cleanup; the regular installer still
lacks the engine payload and GUI controls. Signed profile import is described in
docs/windows-tcp-profile.ru.md; the session in docs/windows-tcp-session.ru.md.

Xray is built on Windows amd64 from the same revision as Linux TCP:
d2758a023cd7f4174a5a5fa4ff66e487d4342ba0, Go1.26.1. Wintun0.14.1 is obtained from
https://www.wintun.net/ with its published SHA256 and checked using Windows Authenticode.
Signed Wintun binaries are distributed under the license included in their ZIP;
the preview includes Xray and Wintun licenses. Do not replace the existing WireGuardNT DLL.

The isolated Windows CI runner executes three fresh Xray client/server pairs through the production TcpEngine.cs
process owner primitive. Each client
creates an actual Wintun adapter; six synthetic HTTP requests use a single test route
198.18.0.1/32 through TUN, local VLESS and a loopback HTTP fixture. No public VPN profiles,
credentials or gateway access are used. This tests Windows TUN + VLESS runtime, NOT
REALITY handshake or Internet VPN routing. Default routes and DNS are preserved.
Only the uniquely named test adapter/address/route is touched. Explicit shutdown,
owner termination and engine termination each verify no orphan child or adapter.
The owner uses a kill-on-close Windows Job Object and sends config through stdin only
after assignment. Both pinned binary hashes are checked before launch; tamper is refused.
Driver installation requires the allowlisted standard Windows environment. Synthetic
engine diagnostics are compiled only into the CI harness (TCP_ENGINE_TEST).

The build manifest records source/toolchain and binary hashes. The CI artifact is a
preview, not an authenticated updater payload or release. Protected profile import
and broker/SCM network session are implemented and locally exercised. Packaging/UI,
full external REALITY routing acceptance and WG→AWG→TCP recovery remain gates. User network/load tests stay deferred.

Upstream source: https://github.com/XTLS/Xray-core/blob/d2758a023cd7f4174a5a5fa4ff66e487d4342ba0/proxy/tun/tun_windows.go

The additional SessionHost compiles the actual broker under TCP_SESSION_TEST with
scoped IPv4/IPv6 routes and DNS namespace, plus local VLESS instead of REALITY.
It runs as LocalSystem through SCM and the normal pipe. Four connected scenarios each
verify3 IPv4 +3 IPv6 HTTP requests, OS resolver through NRPT/UDP and foreign-SID refusals;
a fifth cancels startup. All verify no child/TUN/routes/journal and unchanged host network
settings. The test account is created/deleted by Windows APIs without a shell password.
The compile-time test mode is absent from the normal client and cannot be selected by IPC.
