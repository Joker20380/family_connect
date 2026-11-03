# Read-only service snapshot — 3 November 2026

## 15:59UTC refresh

Repeated at15:58–16:00UTC /16:58–17:00 Brussels; same read-only scope and hosts.
Registry unchanged60/56 non-revoked/4 revoked. Support seen24h/7d now6/20, not online users.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| Load1/5/15min,2 CPUs each | 1.70/1.18/1.19 | 0.39/0.63/0.83 | 0.00/0.03/0.00 |
| RAM used/total MiB | 1197/1962 | 791/1914 | 410/1919 |
| Available RAM MiB | 765 | 1123 | 1509 |
| Disk used/free | 78%/6.4GiB | 16%/39GiB | 13%/40GiB |
| Configured AWG peers | 18 | 47 | 2 |
| Recent handshake180s/900s/24h | 0/0/4 | 6/6/16 | 1/1/2 |
| Five-second RX/TX Mbps | 0/0 | 0/0.001 | 0/0 |
| Cumulative RX/TX GiB | 0.471/5.848 | 2.236/34.018 | 0.428/0.776 |

CPU us+sy samples: RU37–71%, subsequent five samples13–54%; AMS1 22–27%,
AMS2 4–14%. No sustained saturation demonstrated. RU IO wait1–2%, follow-up0–3%,
swap873MiB with sampled si/so0; IO PSI some/full avg60=2.72/1.69. AMS IO PSI0.00.
All previously listed core services active; RU legacy Docker peer-worker still
unhealthy, host worker active, product API/control healthy. Friends TCP sockets0;
RU8443 HTTPS sockets4, not VPN users. MESH sessions not separately counted.
Seven recent AWG peers are not seven unique people or guaranteed concurrent sessions.
AMS1 cumulative TX grew approximately3.071GiB since the earlier snapshot; neither
this counter difference nor the five-second idle sample measures maximum throughput.

No settings/restarts/releases/tests through user VPN tunnels; public versions remain
Android111/catalog6, Windows0.2.16/catalog12, Linux public0.2.11/owner internal.13.
MESH slow-link source work is not deployed by this check. No rollout/rollback needed.
RU disk and legacy-worker follow-ups remain; preserved all unrelated working changes.

## Earlier13:15UTC snapshot

Observed13:14–13:17UTC (14:14–14:17 Brussels). Requested operational inspection,
not a release or end-to-end acceptance. Current source catalog selects RU185.251.89.19,
AMS1 185.10.158.212 and AMS2 185.10.158.196; old NL is archive-only.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| CPUs | 2 | 2 | 2 |
| Load1/5/15min | 0.83/1.00/1.05 | 1.14/0.72/0.61 | 0.04/0.10/0.08 |
| RAM used/total MiB | 1141/1962 | 803/1914 | 396/1919 |
| RAM available MiB | 820 | 1110 | 1522 |
| Root disk used / available | 78% /6.4GiB | 16% /39GiB | 13% /41GiB |
| Configured Friends AWG peers | 18 | 47 | 2 |
| Handshake within180s/900s/24h | 0/0/4 | 5/6/17 | 1/1/2 |
| Five-second RX/TX Mbps | 0/0 | 0.491/16.008 | 0/0 |
| Cumulative RX/TX GiB | 0.471/5.848 | 2.028/30.947 | 0.424/0.723 |

Registry60 devices,56 non-revoked and4 revoked. Support last_seen within24h:4,
within7d:19; support telemetry is not a complete activity count. Peers may include
test/owner devices and overlap across hosts: no unique-person total is claimed.
Recent handshakes indicate recent tunnel activity, not guaranteed simultaneous users.
All sampled Friends TCP ports443/8446 had zero established sockets; RU8443 had3
HTTPS sockets, not VPN clients. MESH application sessions were not independently counted.

Friends AWG/TCP/load services active on all three. RU HTTP candidate and host peer
worker active; AMS1 mailbox/Reticulum/bootstrap active. RU legacy Docker peer-worker
remains unhealthy, while product API/control containers report healthy. No logs read
or root-cause diagnosis; active units do not establish end-to-end VPN health.

Short vmstat samples: RU CPU7–27%, IO wait0–1%, swap879MiB allocated without sampled
swap-in/out; AMS1 CPU21–26%, IO wait0%, steal0–1%; AMS2 near idle. RU IO PSI some
avg60=2.58/full=1.78; both AMS nodes0.00. Sampling is brief, not uptime/SLA proof or
capacity benchmarking. Cumulative counters are not daily traffic and can reset.

No production writes/restarts/client test traffic, keys or user identifiers output.
Initial sandbox SSH failed before connecting; approved outside-sandbox reads succeeded
with existing host pins. Versions unchanged: Android111/catalog6, Windows0.2.16/catalog12,
Linux public0.2.11/owner internal.13. No rollout; rollback not applicable.
Remaining: RU disk growth and legacy worker diagnosis if separately selected; no
automatic repair, fleet successor, Telegram diagnosis or field acceptance claimed.
