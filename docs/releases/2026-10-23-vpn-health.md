# Read-only VPN health —2026-10-23

Observation window approximately16:22–16:30UTC. Authorized RU185.251.89.19 and
NL186.246.45.246 only. No configuration, deployment, policy or version changes;
no rollback needed. Existing uncommitted implementation work preserved.

- RU:2 CPUs, load1.18/0.95/0.84; RAM1036/1962MiB used,925MiB available;
  swap734/2047MiB occupied; disk21/28GiB,74%. Short CPU samples38–60% busy.
- NL:1 CPU, load0.47/0.45/0.39; RAM592/955MiB used,363MiB available;
  no swap; disk9/19GiB,49%. Short CPU samples approximately11–18% busy.
- Registry read-only aggregate:52 devices,48 non-revoked,4 revoked. Not unique
  humans or online count. No identities, credentials or profiles printed.
- NL Friends AWG fcopen31:44 configured peers;6 handshakes under180s,
  8 under900s,22 under24h. RX15.068GiB/TX263.066GiB cumulative interface counters,
  not daily totals. Five-second sample RX0.030Mbps/TX1.608Mbps.
- NL native WG pilot fcams:4 peers,0 recent handshakes. Separate from Friends.
- No established Friends TCP connections observed on RU8446 or NL443 at snapshot.
  Socket counts do not establish unique user counts or MESH sessions.
- Friends AWG/TCP active on both hosts; NL restricted bootstrap active. RU host
  peer-worker active but legacy Docker peer-worker unhealthy. Cause not verified.
- Legacy RU friends-access inactive; replacement http-candidate active. HTTPS
  status endpoint returned200 from NL; this is not an authenticated API/VPN test.
- NL historical mesh-perf-3b unit failed. Main restricted bootstrap running;
  no conclusion that the historical failure affects production.
- NL AWG/TCP/bootstrap journal priority-error query returned no lines over1h.
  This does not exclude warnings or application-level failures.
- Initial RU SSH reads succeeded; two later SSH banner exchanges timed out.
  RU AWG counters unavailable; no complete both-host concurrent-client total.

Latest previously documented release state remains Linux0.2.11/Windows0.2.15,
private Android106 and gatewaya515 deployment earlier today. No artifact verification
or version rollout performed in this operational check. Live service activation
times had advanced since the earlier deployment record; binaries not rehashed,
so this snapshot does not independently attest the current gateway binary.

Remaining: investigate SSH availability and Docker worker health read-only;
measure RU AWG and MESH sessions with bounded diagnostics, then longer traffic
samples if needed. No throughput/load tests or client traffic generated.
