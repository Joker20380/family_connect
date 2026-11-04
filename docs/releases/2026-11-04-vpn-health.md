# VPN read-only health — 4 November 2026

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
