# VPN read-only health —2026-10-24

Initial host snapshot21:26UTC (23:26CEST), followed by sequential bounded samples.
Only authorized RU185.251.89.19 and NL186.246.45.246 accessed. No service,
configuration, policy, version or deployment changes; rollback not applicable.
Current desktop D01.3-R source/review checkpoint unchanged; deployed binaries and
public artifacts not reverified by this operational task.

## Clients and traffic

- Friends SQLite read-only aggregate:53 devices,49 non-revoked,4 revoked; yesterday
  52/48/4. Devices are not unique people or simultaneous users.
- RU Friends AWG fcopen31:11 configured peers,0 handshakes within3min/15min/24h;
  all11 have no handshake in current runtime. RX/TX counters0,5s traffic0.
  This is not proof that the peers have never connected historically.
- NL Friends AWG fcopen31:45 configured peers,8 handshakes within3min,9 within15min,
  18 within24h;27 have no handshake in current runtime. Five-second traffic:
  RX0.873Mbps,TX34.606Mbps; cumulative RX1.001GiB/TX25.921GiB.
- NL AWG unit activation24.10 at03:20:15UTC differs from yesterday. Current
  counters must not be subtracted from yesterday's higher counters as daily usage.
- No established Friends TCP sockets on RU8446/NL443 at observation; RU8443 had4
  HTTPS connections, not4 VPN users. MESH sessions and legacy pilot interfaces
  not counted. No global unique/concurrent-user total established.

## Resources and health

- RU2 CPUs: load2.38/1.56/1.22; short current CPU samples4–10% user+system;
  IO wait2%, no sampled swapping. RAM1073/1962MiB used,888MiB available;
  swap783/2047MiB occupied, disk74%,7.3GiB available.
- NL1 CPU: load0.64/0.59/0.51; short CPU samples1–9%, IO wait0%;
  RAM458/955MiB used,497MiB available; no swap; disk48%,9.6GiB available.
- Both Friends AWG/TCP active; NL restricted bootstrap active, RU replacement
  HTTP candidate active. These units report NRestarts0, not proof of no manual
  restarts. Current NL bootstrap activated24.10 at19:54:19UTC; RU HTTP candidate
  at19:54:23UTC. No restart performed by this diagnostic.
- RU host peer-worker active; legacy Docker peer-worker unhealthy,72735 failing
  probes. Latest two probe classifications include connection-refused/timeout
  and timeout, exit1/-1. Underlying cause/endpoint not independently verified.
- RU product API and control containers healthy; other listed FC containers up.
- RU HTTPS status endpoint returned200 with curl -k (certificate validation not
  performed). No authenticated end-to-end client VPN test or traffic stress test.
- Bounded journal queries timed out; do not report zero recent errors from these
  attempts. SSH basic reads succeeded on both servers, unlike yesterday's RU issue.

Follow-up: inspect worker health target and journal latency separately, without
automatic restarts; add authorized MESH/legacy runtime counts if a complete
concurrent-device inventory is needed. Preserve current clients and identities.
