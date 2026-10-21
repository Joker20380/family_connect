# VPN read-only health snapshot —20 October2026

## Refresh20 October16:09UTC /18:09 Brussels

Read-only SSH and fresh public HTTPS metrics: RU/NL AWG registrations11/39,
recent180s peers0/3; TCP registrations11/38, established sockets0/0.
CPU24.8%/4.5%; host RX0.028/2.167Mbit/s, TX0.032/0.675Mbit/s.
RAM used1060/1962 and526/955MiB, available901/429MiB. Disk73%/44%;
RU swap630/2047MiB. Friends AWG/TCP services active on both hosts; NL
restricted bootstrap active. No saturation observed in this short snapshot.
No MESH session count, unique-user deduplication, end-to-end tests or repeat
peer-worker diagnosis. Registration mismatch and earlier follow-ups remain.
No runtime/version/publication changes; no rollback required. Latest documented
owner build96 install is context only, not independently verified by this check.

## Original snapshot

Observed19 October22:10–22:12UTC /20 October00:10–00:12 Europe/Brussels.
Only185.251.89.19 and186.246.45.246 inspected; no service/configuration changes,
builds, installs or publication. Existing dirty work preserved. No rollback needed.

| Metric | RU | Amsterdam |
|---|---:|---:|
| vCPU |2|1|
| Load average1/5/15min |0.98/0.82/0.89|0.60/0.57/0.49|
| RAM used/total MiB |1021/1962|495/955|
| RAM available MiB |941|460|
| Swap used/total MiB |623/2047|0/0|
| Root disk used |73%,7.7GiB available|42%,11GiB available|
| Friends AWG registrations |11|39|
| Friends AWG recent180s handshakes |0|2|
| Friends TCP registrations |11|38|
| Friends TCP established sockets |0|0|

Public HTTPS load endpoint responds with fresh samples: RU CPU21.0%,
RX0.025/TX0.029Mbit/s; NL CPU17.6%, RX2.701/TX2.735Mbit/s. These are
whole-host short-window metrics, not VPN-only throughput. Configured200Mbit/s
capacity is provider-default-estimate, not measured capacity. vmstat short
samples show no current swap-in/out and no CPU saturation.

Friends AWG cumulative counters: RU RX150099883/TX884881508bytes;
NL RX12804594297/TX224400764271bytes. These are lifetime/reset-dependent
counters, not daily usage. Legacy RU WG3/AWG1 peers and NL WG4 peers have
zero recent180s handshakes. Counts across transports/hosts must not be summed
as unique people. No exact MESH user/session count obtained.

Main VPN services are active. RU product/control API containers healthy, but
family-connect-peer-worker container unhealthy with failing streak58638;
its systemd unit remains active. Root cause not investigated in this snapshot.
RU renewal22:02:51UTC, credential health22:07:21UTC and directory sync22:11:28UTC
report success; scheduling timers active. Amsterdam retains failed historical
family-connect-mesh-perf-3b-20261018-01.service, not its active production broker.

Actual Amsterdam broker PID3387107 started22:03:03UTC, NRestarts0,
memory32808960bytes; executable SHA256
`79d9c8c58676d5af7ebff78fd780009d98e468e6dcafbdc47e48de755bd16f86`.
This matches temporary observation A from the ongoing queue/retry comparison,
not accepted normal baseline b9ae8807 or normal candidate fb3f416d. No cleanup
or restart attempted. Existing installed-owner beta90 is documentation evidence
only; no phone/install/public artifact verification was performed here.

Remaining checks: diagnose peer-worker health separately; explain NL AWG/TCP
registration difference; finish ongoing comparison in its owning session.
No end-to-end client VPN, sustained throughput or new software tests performed.
Read-only operational probes are not a transport stability acceptance.
