# VPN read-only health — 7 November 2026

Observed19:56–19:58UTC (20:56–20:58 Brussels). Owner requested load/client counts.
SSH read-only inspection of RU185.251.89.19, NL1 185.10.158.212 and NL2
185.10.158.196. No restart, deployment, configuration or policy change.

| Metric | RU | NL1 | NL2 |
| --- | --- | --- | --- |
| CPU us+sy, live interval samples | 5–39% | 9–82% | 6–63% |
| Load1/5/15 | 1.36/1.16/1.30 | 1.43/2.03/2.22 | 0.74/0.87/0.89 |
| vCPU | 2 | 2 | 2 |
| RAM used/total MiB | 1155/1962 | 833/1914 | 427/1919 |
| Available RAM MiB | 806 | 1080 | 1491 |
| Swap occupied MiB | 904 | 261 | 31 |
| Root disk used/free | 71%/8.2G | 19%/38G | 17%/39G |
| Interface snapshot RX/TX Mbps | 0.061/0.104 | 1.577/0.060 | 0.078/0.023 |
| AWG configured peers | unavailable | 48 | 5 |
| AWG handshakes within180s/900s/24h | unavailable | 2/4/6 | 1/1/1 |
| AWG five-second RX/TX Mbps | unavailable | 0.001/0.001 | 0.015/0.005 |
| Established local TCP443/8446 sockets | 0/0 | 0/0 | 0/0 |

RU AWG is failed/masked; TCP inactive/masked. Both ActiveExitTimestamp19:04:02UTC,
AWG main process exit19:04:07UTC. AWG query fails with Protocol not supported.
This differs from6 November's snapshot; intended disablement/cause is not established.
RU HTTP candidate, peer worker and load monitor remain active. No restoration attempted.

Both NL AWG/TCP and MESH bootstrap are active; bootstrap NRestarts0, latest starts
18:29:03UTC/18:29:06UTC respectively. Active state does not prove client end-to-end
traffic or automatic-renewal acceptance. No MESH session count was obtained.

Registry read-only aggregate:63 devices,59 nonrevoked,4 revoked. Support last_seen:
5 within24h,22 within7d. These are registered/recently reporting devices, not unique
people or concurrent connections. Three recent AWG peers across NL do not establish
three unique users. Other sockets: NL1 local4243=5; RU local8443=5; not client counts.

NL1 initially shows swap-in up to14908KiB/s and swap-out2908KiB/s, IO wait19%;
follow-up CPU18–82%, swap-in up to8562KiB/s and IO wait16%. Available RAM remains
1080MiB: cannot attribute this to memory exhaustion or a particular process from
these samples. NL2 follow-up CPU10–63%, no observed swap activity. RU initial short
CPU31–39%, subsequent5–20%, IO wait briefly23%; no live sampled swap-in/out.
Network traffic is low; NL configured5Gbps capacity is an operator assumption, not
measured throughput. Short sampling cannot establish sustained overload or capacity.

Checks: read-only systemd, vmstat, free, df, uptime, ss, AWG aggregate counters and
SQLite mode=ro counts. Initial sandbox SSH permission failure resolved by approved
execution outside sandbox; RU AWG failure is retained, not reported as zero peers.
No private keys, peer IDs, IP lists or database rows printed or committed.

Versions/builds/installations/public artifacts unchanged and not reverified. Prior
entry docs record opt-in118/default113/catalog7; this is not a rollout claim.
Rollback not applicable. Remaining: establish intended RU masking; investigate NL1
CPU/swap activity if sustained; separately measure authenticated MESH concurrency
and end-to-end availability. Preserve existing engineering gates and unrelated edits.

## MESH session follow-up

Owner separately requested MESH concurrency. Snapshots20:04:25–27UTC and
20:04:51–52UTC both yield **NL1=1, NL2=0** authenticated dedicated sessions.
NL1's remaining session has Family TLS establishment and no terminal/cleanup event;
incoming HEARTBEAT/RX advances between samples, latest19.3s before final readback.
NL2 has only bootstrap_seed_ready and no dedicated admission/session events during
its current invocation. A ready bootstrap room is not a connected client.

Method: stream journalctl JSON filtered by each service's current InvocationID;
aggregate restricted_trace by session_tag on the server, never print tags. Count
GATEWAY_SESSION/ESTABLISHED with no LOCAL_CLOSE, GATEWAY_SESSION failed/closed or
CLEANUP completed event, cross-check Family TLS and recent incoming heartbeat.
Both services remain active with identical invocation/PID/start metadata before and
after each read. Journal starts18:29:06UTC/18:29:08UTC, within seconds of service
starts18:29:03UTC/18:29:06UTC. Journal reads exit0; no suppression messages observed
in the selected streams. The initial parser failed sorting missing activity samples;
fixed locally and repeated successfully, not treated as a zero-session result.

NL1 current process totals:28 setup tags,27 ACTIVE events,26 FAILED and1 EXPIRED
setup events. These are historical setup attempts/reconnections, not28 clients and
not the current online count. Repeated session-established trace events are deduped.
No CARRIER_ACTIVITY events exist in this readback; heartbeat proves recent liveness,
not a measured user payload rate. No client traffic test or memory introspection.
Journal-derived count is a point-in-time observation, not a native exported gauge;
missing/dropped logs remain a general limitation. No service/profile changes,
version changes, deployment or rollback. Existing unrelated working edits preserved.
