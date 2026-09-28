# DNS containment: Family hostname OPEN и wire DNS

## Аудит исходников28.09.2026

Это source audit выбранного experimental path, не packet capture всех production
клиентов. 5N.5 не является full-device VPN: выводы не распространяются на весь
Chrome/WebView/Private DNS телефона.

| Компонент | DNS dependency | Категория |
| --- | --- | --- |
| `carrier/tcpforward/client.go`, `mux_stream.go` | OpenRequest.Host сериализуется без resolve | B: user hostname внутри Family TLS |
| `policy.go`, `gateway.go`, `mux.go` | LookupNetIP("ip"), validate ALL IPs, dial literal | B: gateway-only |
| CLI `tcp.go` | HTTPS поверх Family net.Conn, original SNI/normal TLS verification | B: без direct socket/lookup |
| Telemost `auth.go`, `signaling.go`, `session.go` | API HTTP, WS, ICE/STUN `stun.rtc.yandex.net`, выданные TURN/SFU addresses | A: bootstrap, не заворачивать рекурсивно в Family |
| Android diagnostic `ProbeService.java` | shared native CLI, без WebView/proxy/VpnService | B: только Core requests |
| Android product `Transport.java` | WG/AWG/TCP(REALITY), нет registered Family transport | другой production path |
| Android `ControlProfiles.java`, `ProfileValidator.java` | InetAddress.getByName за numeric-IP validation | parsing literals, не user hostname lookup |
| Android `TcpProfile.java`, provisioning models | validated literal gateway endpoint, отдельно TLS server_name | A: provisioning/bootstrap |
| Android `TcpTunnelEngine.java`, `VpnHealth.java` | existing TUN DNS, literal health probes bound to VPN Network | другой transport; не менять ради5N.5 |
| Android `TcpRuntimeTest.java` | getAllByName для TUN DNS instrumentation | tests другого transport |
| Linux `profile_config.py`, `tcp-helper.py`, `backend.py` | literal VLESS endpoint; existing resolvectl ~./WG DNS | другой transport, нет Family SOCKS/HTTP frontend |
| Windows `Core/TcpProfile.cs`, `TcpNetwork.ps1` | literal endpoint, Xray TUN/DNS+NRPT | другой transport, Go carrier не встроен в UI |
| Windows `TcpHealth.cs` | Dns.GetHostAddressesAsync(gstatic health), VPN-bound socket | OS DNS/NRPT dependency, не Family API proof |
| TCP/XHTTP curl scripts | --socks5-hostname / socks5h:// | remote hostname resolution соответствующего proxy |
| Rust core, messenger/Reticulum/control/provisioning | old/control/discovery HTTP/TLS, не новый OpenTCP | A/control или другие paths |

## Flow и совместимость

Уже5N.4: client OpenTCP("example.com",443) → encrypted OPEN → gateway lookup →
policy(all IPs) → DialContext(validated literal). **Предварительного client resolve
в этом path не найдено; не заявляется фиктивное «перенесение».** Дополнение даёт
negative-condition proof и усиливает policy/timeout/metrics. IP OPEN не требует DNS.
Original hostname остаётся TLS SNI; end-site TLS не терминируется на gateway.

5N.5 отдельно требует QueryDNS(wire) через stream0/Family request ID для будущего
packet adapter; обычному hostname OPEN этот RPC не нужен. Resolver address задаёт
только gateway. Нет client public-DNS/DoH fallback. OPEN JSON/v1 не меняется;
mux v2 нужен concurrency, не hostname support.

ASCII DNS/A-label IDNA policy: gateway lowercases и убирает один root dot;
canonical≤253B, label≤63B. Unicode U-label явно rejected, как прежде: вызывающая
сторона должна передать ASCII IDNA representation **без DNS lookup**. Не добавлена
непроверенная Unicode normalization. URLs/userinfo/port/whitespace/zones rejected.

Все IP проверяются до первого dial: private/loopback/link-local/unspecified/
multicast/CGNAT/ULA/metadata/reserved и gateway interface addresses denied. Mixed
public/private set отвергается целиком. Gateway snapshots interface addresses при
создании session; NAT public alias вне interfaces требует отдельной deployment
policy. Explicit test-only127.0.0.1:exact-port override сохранён. Повторного lookup
при connect нет. До32 candidates, resolver order preserved, per-address dial≤3s
в общем default10s/max30s budget; недоступный IPv6 допускает следующую IPv4 попытку.
Lookup≤3s с context cancellation. Compatible errors: DNS/NXDOMAIN/empty →
dns_failure; DNS/connect timeout → timeout; denied → policy_rejected; cancelled →
cancelled; refused → connection_refused. Внутренние resolver/IP errors не выдаются.

Metrics без hostname labels: hostname_open_requests, dns_lookup_success/failure/
timeout, ipv4_selected/ipv6_selected, destination_denied, connect_failure.
Application cache **не добавлен**: LookupNetIP не возвращает TTL, выдуманный TTL
был бы некорректен. System resolver может иметь собственный TTL-aware cache;
Family не заявляет его hit/miss. Cache expiry test N/A, не PASS. Wire DNS сохраняет
полученные RR/TTL, bounded message4096B/outstanding16/timeout5s.

## Negative-DNS integration

TestHostnameHTTPSWithBrokenClientDNS: admitted Family TLS+ReliableStream,
poisoned Go DefaultResolver (Dial всегда отказывает), gateway fixture lookup,
HTTPS fixture. Negative lookup обязан вызвать poison resolver; затем hostname
OPEN/verified TLS/HTTP200 при **нуле** client lookup и одном gateway lookup.
Fixture CA доверяется только тесту; это не public Internet proof.

Diagnostic CLI opt-in `--deny-client-dns-after-admission`, только mux probe/native
CGO. Linker wrapper getaddrinfo прозрачно вызывает оригинальный libc до admission;
после carrier+Family admission atomic guard возвращает EAI_AGAIN **до сети** и
считает вызовы. Negative lookup проверяет guard; счётчик затем обнуляется.
GODEBUG=netdns=cgo выбирается только в test process до bootstrap; Android обычно
и так использует libc. OS/Private DNS settings пользователя не меняются.
Это process-scoped unavailable DNS, не whole-device interception.

## Physical Android procedure

С проверенными native/APK artifacts, новой private room environment и disposable
ProductStore profiles (не production credentials):

```
python3 pilot/android-telemost/mux_acceptance.py --adb /path/to/adb \
  --binary /private/telemost-binary --family-dir /private/family \
  --case public --out /private/new-public-attempt
python3 pilot/android-telemost/mux_acceptance.py --adb /path/to/adb \
  --binary /private/telemost-binary --family-dir /private/family \
  --case mixed --out /private/new-mixed-attempt
```

Diagnostic mux mode включает guard. Cellular, Wi-Fi off, no active VPN/TUN;
сохранить и восстановить radios. Evidence: одна family_auth на endpoint,
negative_probe_blocked, четыре simultaneous OPEN, verified HTTPS200 example/
Cloudflare, gateway hostname lookup counters, guard final post_probe_calls=0.
Runner rejects missing/nonzero guard evidence; одного HTTP200 недостаточно.

Независимая pcap-проверка — rooted test device/emulator: capture до admission,
отделить bootstrap interval, проверить DNS53/853 IPv4/IPv6 после guard. На non-root
Redmi tcpdump может быть недоступен; отсутствие pcap нельзя объявлять capture PASS.
Guard доказывает выбранный native resolver path, не Java/browser/app-owned DoH
или будущий SOCKS/TUN adapter. Не публиковать raw pcap/DNS history/room/credentials.
После acceptance удалить diagnostic APK, owned processes и private credentials;
сохранить allowlisted evidence, восстановить radios. Текущий verdict/ограничения:
[5N.5 report](../releases/2026-09-28-webrtc-eu5-mux-dns.ru.md).
