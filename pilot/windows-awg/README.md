# Windows AWG native worker

Pinned amneziawg-go `1cc94272ca8e9e223a5fe76382f5880f09d3c12d`, Go1.26.1,
Windows amd64, official signed Wintun0.14.1. The upstream Windows main is a debug
program exposing UAPI; this worker accepts one bounded JSON document on stdin after
EOF, creates a fresh `fcawgXXXXXXXX` TUN and binds UDP sockets to the selected uplink
before engine goroutines can send. It exposes no UAPI/named-pipe listener. Native
logs and configuration stay out of output. IPv4 outer transport only; IPv6 outer
is blackholed, while inner IPv4/IPv6 use AWG.

Build: `./pilot/windows-awg/build.ps1 -Output <fresh-directory>`. Output manifest
records upstream revision, wrapper source hash and binary hashes. `peer-fixture.exe`
is CI-only (memory TUN + UDP echo), never a production server or installer payload.
The CI owner uses the same ProcessJob kill-on-close primitive as the Windows broker;
it does not itself provide broker SID/DPAPI policy. No worker is installed on devices.

CI uses ephemeral X25519 keys and loopback UDP, actual Windows Wintun IPv4/IPv6,
AWG2 S1-S4/header ranges/I1, wrong-header/key rejection and engine/owner crash cleanup.
Only /32 and /128 routes are added, default routes and DNS must match the baseline.
The workflow also runs the actual LocalSystem broker with signed activation, DPAPI,
SID ownership, IPv4/IPv6 data, crash/recovery and cancellation. The synthetic peer
keeps RIO reception alive after WSAECONNRESET from the killed client port and reports
only counters (no key/config logs). It is excluded from the installer.
Profile, broker, installer and manual transport UI passed CI; automatic switching,
external AWG, full routing and production health probes remain unaccepted.
See [integration evidence](../../docs/releases/2026-09-11-windows-awg-integration.ru.md)
and [operator runbook](../../docs/windows-awg.ru.md).
