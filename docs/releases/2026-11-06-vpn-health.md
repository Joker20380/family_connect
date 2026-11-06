# VPN health — 6 November 2026

Read-only snapshot13:27UTC (14:27 Brussels), followed by bounded diagnosis.

| Metric | RU | AMS1 | AMS2 |
| --- | --- | --- | --- |
| CPU us+sy, three one-second samples | 70–72% | 5–22% | 0–2% |
| Load1/5/15 | 0.97/1.32/1.46 | 0.17/0.29/0.31 | 0.05/0.13/0.17 |
| RAM used/total MiB | 1161/1962 | 828/1914 | 419/1919 |
| Available RAM MiB | 801 | 1085 | 1500 |
| Root disk used/free | 71%/8.4G | 17%/39G | 15%/39G |
| AWG configured peers | 19 | 48 | 5 |
| AWG handshakes180s/24h | 0/2 | 4/18 | 0/2 |
| TCP443/8446 established sockets | 0/0 | 91/0 | 5/0 |

AWG/TCP active on all three, NRestarts0. Both NL MESH bootstrap services FAILED,
NRestarts6, Result exit-code, ExecMainStatus1. Last recorded exit5 November11:47:41UTC
on AMS1 and11:47:42 on AMS2. These timestamps do not establish continuous outage
duration. Root cause unknown: bounded journal keyword scans returned no matching
evidence, not proof of absent errors. RU bootstrap inactive as before.

RU follow-up five two-second CPU samples4–31%, IO wait0–15%, steal2–4%; initial
steal5–7%. Initial spike is not sustained saturation proof. RU swap924MiB, initial
one4KiB/s swap-in, follow-up si/so0. Cleanup gain mostly retained,8.4GiB available.
External RU8443 TLS validates (verify0); HTTP404 at root is not API-health acceptance.
Four recent AWG peers and96 TCP sockets are not unique clients. MESH sessions not
counted; no client end-to-end test. Existing connections do not prove MESH admission.

No restart/repair, deletion, configuration, publication or version change. Rollback
not applicable. Entry documentation retains opt-in118/default113/catalog7; no artifact
readback in this check. Isolated G4 qualification is separate from live service health;
do not interrupt its container or infer production acceptance from it. Next operational
follow-up: diagnose both failed NL bootstrap services before any authorized recovery.
Preserve unrelated working changes. TLS-renewal job/legacy Docker worker not rechecked.
