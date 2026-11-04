# VPN read-only health — 4 November 2026

## 22:54UTC refresh

Read-only snapshot22:53:54–22:54:06UTC (23:54 Brussels).

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| CPU us+sy, three one-second samples | 13–23% | 8–34% | 8–17% |
| Load1/5/15 | 1.27/1.19/1.09 | 1.20/0.72/0.59 | 0.56/0.37/0.27 |
| RAM used/total MiB | 1203/1962 | 784/1914 | 480/1919 |
| Available RAM MiB | 759 | 1130 | 1438 |
| Disk used/free | 70%/8.5G | 17%/39G | 14%/40G |
| Configured AWG peers | 19 | 47 | 5 |
| AWG handshakes180s/24h | 0/2 | 2/17 | 0/4 |
| Established TCP443/8446 | 0/0 | 145/0 | 0/0 |

AWG/TCP active on all three, both NL bootstrap services active, NRestarts0 in
sampled units. RU has no active bootstrap; no RU MESH availability is inferred.
Two recent AWG peers and145 TCP sockets are not unique users; MESH application
sessions not counted. Short CPU samples show no sustained overload; RU swap913MiB
with sampled si/so0 and IO wait0–5%. RU retains8.5GiB free after earlier cleanup.
External RU8443 TLS validates (verify0), root HTTP404 is not an application PASS.
No settings/restarts/deletion/rollout; rollback not applicable. TLS-renewal job and
legacy Docker worker not rechecked. Entry checkpoint records installed owner117,
public113 and sustained MESH stability OPEN; this inspection neither verifies release
bytes nor closes that gate. No client end-to-end test or unique-person count.

## 12:15UTC refresh

Read-only sampling12:15:35–12:15:45UTC (13:15 Brussels), all nodes2 vCPUs.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| CPU us+sy, three one-second samples | 12–31% | 10–16% | 7–11% |
| Load1/5/15 | 1.77/1.40/1.55 | 0.68/0.68/0.54 | 0.55/0.46/0.37 |
| RAM used/total MiB | 1174/1962 | 784/1914 | 447/1919 |
| RAM available MiB | 788 | 1129 | 1471 |
| Disk used/free | 77%/6.5G | 16%/39G | 13%/40G |
| AWG configured peers | 19 | 47 | 4 |
| AWG handshakes180s/900s/24h | 1/1/2 | 5/7/18 | 1/1/3 |
| Established TCP443/8446 sockets | 0 | 11 | 0 |

AMS1 follow-up confirms xray owns listener443; established sockets then9 on443,
0 on8446. Connections fluctuate and are not unique authenticated clients; do not
sum TCP sockets and AWG peers as people. Seven recent AWG peers are also not a
deduplicated user count. MESH application session count remains unmeasured.
AWG/TCP services active on all nodes. No sustained saturation demonstrated by this
brief sample. RU swap911MiB, one sampled swap-in4KiB/s, swap-out0, IO wait1–4%;
no demonstrated swap thrashing. RU disk remains a monitoring concern.

No production changes, restarts, rollout or rollback. TLS renewal not rechecked in
this refresh. Entry checkpoint now records owner112 MESH2 traffic but stability gate
NOT PASSED; public111/catalog6 unchanged in that checkpoint, not independently
revalidated by this check. Existing implementation work and queue are preserved.

## Earlier09:07UTC snapshot

Observed 09:07–09:10 UTC. AWG/TCP active on RU, AMS1 and AMS2; RU HTTP
candidate/host peer worker and both Amsterdam bootstrap services active.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| Load1 | 1.38 | 0.90 | 0.35 |
| Available RAM MiB | 833 | 1150 | 1465 |
| Root disk used/free | 77%/6.5G | 16%/39G | 13%/40G |
| Configured AWG peers | 19 | 47 | 4 |
| Handshake within180s/24h | 1/2 | 5/14 | 2/3 |
| Cumulative RX/TX GiB | 0.537/7.269 | 2.732/42.569 | 0.520/2.210 |

Eight recent peers are not eight unique users or guaranteed concurrent sessions.
Cumulative counters are not daily traffic or a speed test. No client end-to-end
VPN test or MESH application READY/ACK acceptance was performed.

RU product-cert-renew reports timeout, exited 4 November00:06:43 MSK.
External HTTPS to RU8443 currently validates TLS (curl verify0); root path returns404,
not an application-health PASS. Renewal failure needs separate diagnosis before expiry.
Legacy Docker peer-worker remains unhealthy; host worker active and product API/control
containers healthy. RU disk monitoring remains warranted. Historical failed one-shot
renewal/overlay units were observed, not treated as a new data-plane outage.

Initial sandbox SSH failed; outside-sandbox reads succeeded. AMS2 used its existing
dedicated pinned known-hosts file after default strict host verification refused it;
no host key was accepted or replaced. No settings, restarts, deployment, signing,
catalog changes or user private data output. Versions are unchanged by this check:
documented public Android111/catalog6, Windows0.2.16/catalog12, Linux0.2.11;
Android112 remains a candidate in the entry checkpoint, CI not rechecked here.
Rollout/rollback not applicable. Existing unrelated working changes preserved.
