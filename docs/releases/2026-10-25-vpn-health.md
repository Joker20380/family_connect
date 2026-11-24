# VPN read-only snapshot —2026-10-25

Observed17:15UTC with follow-up resource samples, approximately18:15–18:17CET.
Authorized RU185.251.89.19 and NL186.246.45.246 only. No mutation, restart,
release, deployment or client traffic test. Rollback not applicable; existing
uncommitted work preserved. Initial diagnostic script syntax error prevented
execution; corrected read-only retry supplied the observations below.

## Clients

- Registry54 devices,50 non-revoked,4 revoked; +1 non-revoked versus24.10.
  Device registrations are not unique people or concurrent users.
- Friends AWG RU fcopen31:11 configured,0 recent3min/15min/24h; all11 lack
  handshakes in current runtime. Counters and5s traffic zero.
- Friends AWG NL:46 configured,5 recent3min,6 recent15min,18 recent24h;
  26 lack handshakes in current runtime.5s RX0.029Mbps/TX0.056Mbps;
  cumulative RX1.920GiB/TX54.050GiB, not daily usage.
- No established Friends TCP sockets on RU8446/NL443 at snapshot; RU8443
  had2 HTTPS sockets, not2 VPN users. MESH/legacy pilot users not counted.

## Resources

- RU2 CPUs, load0.76/0.95/0.87; RAM1062/1962MiB used,900MiB available;
  swap789/2047MiB occupied; disk74%,7.4GiB available. Initial CPU62–63%,
  follow-up42%,7%,6%; IO wait1–6%. No sustained saturation established.
- NL1 CPU, load0.30/0.27/0.32; RAM491/955MiB used,464MiB available;
  no swap; disk48%,9.7GiB available. Initial CPU2–3%, single IO-wait41%
  sample followed by0%. Five follow-up samples CPU1–14%, IO wait0% throughout.

## Services and limits

Friends AWG/TCP active on both; NL bootstrap and RU replacement HTTP candidate
active. All these report NRestarts0; not a claim of no manual restarts.
NL bootstrap activated25.10 at15:57:36UTC, RU HTTP candidate15:57:39UTC.
Binary hashes not checked: activation time is not deployment-version proof.
RU legacy Docker peer-worker remains unhealthy; host peer-worker active.
FC product API/control containers healthy, other listed FC containers up.
HTTPS status200 from both servers using curl -k; certificate validation and
authenticated end-to-end VPN not tested. Journals not re-read following the
previous timeout observations; no claim that recent errors are absent.

Current documented desktop installed candidate0.2.12~l03.2.2/build-9 and active
L04.1-LIVE-2-R1 source work are separate from this health check. No artifact or
public-version verification performed. Remaining ops: diagnose legacy worker,
add MESH/legacy runtime counts if a full online inventory is needed, monitor
resource spikes over a longer interval if symptoms recur. No auto-remediation.
