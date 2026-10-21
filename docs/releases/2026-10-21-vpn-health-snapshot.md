# VPN health snapshot —21 October2026

Read-only SSH on both authorized hosts and public HTTPS load endpoint at
08:48UTC /10:48 Brussels /11:48 Moscow. Existing uncommitted work preserved.

| Metric | RU185.251.89.19 | NL186.246.45.246 |
|---|---:|---:|
| Friends AWG registrations |11|39|
| AWG handshakes within180s |0|5|
| Friends TCP registrations |11|38|
| Friends TCP established sockets |0|0|
| Host CPU, recent monitor sample |22.8%|5.2%|
| Host RX/TX Mbit/s |0.022/0.019|1.564/0.053|
| RAM used/total MiB |1107/1962|486/955|
| RAM available MiB |855|468|
| Root disk used |74%|46%|
| Swap used/total MiB |616/2047|0/0|
| Load average1/5/15min |0.80/0.84/0.88|0.39/0.38/0.43|

Friends AWG/TCP active on both hosts; Amsterdam restricted bootstrap active.
No short-snapshot saturation observed. Monitor samples are17/23seconds old.
Registrations unchanged from20.10; recent AWG peers increased3→5.
50 AWG registrations are not50 deduplicated users; TCP must not be added.
MESH session counts and client end-to-end connectivity not measured.

No builds, installs, deploys, restarts, configuration or publication changes;
rollback not applicable. Latest documented owner96/production1011 context not
independently revalidated here. No software tests run for this read-only check.
Earlier RU worker unhealthy status and NL AWG/TCP registration difference
remain follow-ups; worker health not rechecked. No new transport acceptance.
