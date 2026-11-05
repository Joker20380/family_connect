# VPN read-only snapshot — 5 November 2026

Observed11:28:58–11:29:10UTC (12:29 Brussels). No production mutations.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| CPU us+sy, three one-second samples | 9–25% | 19–21% | 16–18% |
| Load1/5/15 | 1.47/1.42/1.46 | 0.86/0.80/0.71 | 1.13/0.81/0.70 |
| RAM used/total MiB | 1159/1962 | 829/1914 | 489/1919 |
| Available RAM MiB | 803 | 1084 | 1429 |
| Root disk used/free | 70%/8.5G | 17%/39G | 14%/40G |
| Configured AWG peers | 19 | 47 | 5 |
| AWG handshake within180s/24h | 1/3 | 5/14 | 1/3 |
| Established TCP443/8446 sockets | 0/0 | 0/0 | 0/0 |

All AWG/TCP services and both NL bootstrap services active, sampled NRestarts0.
RU bootstrap inactive; no RU MESH availability claim. Seven recent AWG peers are
not seven unique users or guaranteed concurrent sessions. MESH sessions not counted.
Short CPU samples show no sustained saturation. RU CPU steal1/5/11% in these samples
warrants observation if latency occurs, not a proven provider incident. RU swap929MiB
with sampled si/so0, IO wait0–3%. RU disk cleanup gain remains,8.5GiB free.

External RU8443 TLS validates (verify0); root HTTP404 is not an application-health
PASS. TLS-renewal job and legacy Docker worker were not rechecked. No client
end-to-end traffic test, restart, deletion, release, configuration or policy change.
Rollout/rollback not applicable. Entry checkpoint: owner/opt-in118, default113/catalog7;
renewal integration source qualification remains in progress, no new activation.
Public artifacts not independently revalidated. Preserve unrelated uncommitted work.
