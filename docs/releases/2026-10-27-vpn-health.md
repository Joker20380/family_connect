# VPN read-only snapshot —2026-10-27,08:34UTC /09:34CET

## Evening readback —17:36UTC

Fresh check18:36CET; no changes/restarts/client traffic or publication.
Registry unchanged54/50 non-revoked/4 revoked. RU AWG12 configured,0 recent
3min/15min/24h; NL46 configured,6 recent3min,7 recent15min,19 recent24h.
NL5s RX0.257Mbps/TX7.711Mbps, cumulative RX5.179GiB/TX108.385GiB.
No established Friends TCP sockets RU8446/NL443; MESH/legacy counts not collected.

RU2 CPUs load1.11/0.95/0.83, CPU1–31%, IO wait0–6%; RAM1080/1962MiB used,
881MiB available, swap803MiB, disk74%/7.3GiB available. NL1 CPU load0.64/0.48/0.49,
CPU4–33%, RAM580/955MiB used,375MiB available, disk49%/9.4GiB available.
NL IO-wait0/0/44/84/28%; PSI some avg10/60/300=14.17/6.27/5.13,
full10.20/4.87/4.15. Recurrent stalls, not a zero-issue health claim; underlying
process/storage cause not established. RU PSI some avg60=2.95,full1.99.

Both Friends AWG/TCP active, NL bootstrap active since15:35:05UTC, RU HTTP
candidate active since17:22:17UTC (matches current separate control-plane work;
active does not prove candidate rollout acceptance). HTTPS status200 with curl-k;
no certificate/end-to-end test. Legacy RU Docker worker remains unhealthy,
host worker active. Actual NL binary96754942…fe367 and policydd3718ef…a9e81f
match full hashes recorded26.10; P1 enabled for4, target included. Last target
support observation still code84/17.10; actual106 installation/use unknown.
No artifact/version change, rollback not applicable. Preserve CONTROL-PLANE-2
MIGRATED_EMPTY/ROLLOUT BLOCKED_EFFECTIVE_EXECSTART status; this check does not
accept or repair that deployment. Remaining ops: IO latency/legacy worker diagnosis.

Only authorized RU185.251.89.19 and NL186.246.45.246 inspected. No changes,
restarts, releases or test client traffic. Rollback not applicable. Existing dirty
and staged work preserved; deployment baseline is26.10 four-member P1 release.

- Registry54 devices/50 non-revoked/4 revoked, unchanged from25.10.
- RU Friends AWG:12 configured,0 recent3min/15min,1 recent24h;5s traffic zero.
- NL Friends AWG:46 configured,8 recent3min,9 recent15min,20 recent24h;
  5s RX0.019Mbps/TX0.025Mbps. Cumulative RX4.507GiB/TX98.423GiB, not daily totals.
- No established Friends TCP sockets on RU8446/NL443 at snapshot. RU8443 had5
  HTTPS sockets, not VPN clients. MESH/legacy runtime users not separately counted.
- RU2 CPUs: load1.55/1.36/1.37, short CPU3–19%, IO wait2–3%; RAM1047/1962MiB
  used,914MiB available; swap816/2047MiB occupied without sampled swap activity;
  disk74%,7.4GiB available.
- NL1 CPU: load0.35/0.45/0.43, RAM544/955MiB used,411MiB available; no swap;
  disk49%,9.4GiB available, inode7%. Initial CPU2–13%, IO wait0/26/87%.
  Follow-up seven samples CPU2–45%, IO wait0% throughout, steal up to5%.
  IO PSI some avg10/60/300=3.77/6.55/5.76, full=3.38/5.31/4.67.
  Intermittent IO pressure observed, root cause not established; no sustained CPU
  saturation shown. Follow-up required if latency symptoms recur.
- Friends AWG/TCP both active; NL restricted bootstrap active since08:04:26UTC,
  RU replacement HTTP active since08:04:29UTC, NRestarts0. Activation timestamps
  do not by themselves prove cause of restart. No restarts by this diagnostic.
- NL loaded gateway SHA25696754942e7518233bc702277d860b0c9b740fb7553c9742b2ae642a0746fe367;
  group4 SHA256dd3718efdd99c11582306ecf435e9e393377acf6c5e9c5cbc73f0bb72aa9e81f,
  matches accepted26.10 policy, target included, P1 enabled, pacingOFF.
- requested tester last server support observation remains code84/version
  0.1.18-research84-ui60-4-batch1 at17.10 12:42:49UTC. This neither proves a
  successful106 update nor proves it has not occurred. Actual P1 use unobserved.
- RU legacy Docker peer-worker unhealthy, host peer-worker active; FC product
  API/control containers healthy. No worker repair attempted.
- HTTPS status200 from both hosts with curl -k; not certificate validation or
  authenticated end-to-end VPN acceptance. Journals not read, no zero-error claim.

No artifact publication or installed-client version change. Remaining: intermittent
NL storage latency, legacy worker diagnosis and actual target106/P1 field receipt.
