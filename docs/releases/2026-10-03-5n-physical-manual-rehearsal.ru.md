# Финальная физическая репетиция Stage5N — 03.10.2026

**5N-PHYSICAL-RESTRICTED-REHEARSAL = PASS**

**STAGE 5N = CLOSED**

Продолжение существующей физической acceptance, не новый gate. Живое наблюдение
03.10.2026 01:22–01:48UTC. CONNECT выполнен вручную на Redmi после приглашения;
touch/key injection не применялся. Изменены только итоговые документы и локальные
закрытые доказательства. Код, APK и production binaries не менялись.

## Происхождение и ограничения действий

- HEAD до/после: `911fea59e08e5ee8844852ae1e2834812632fbde`.
- Новой сборки, установки, подписи, commit или push нет. Ранее незакоммиченные
  изменения private hook/tests/docs и посторонняя работа сохранены побайтово.
- Установлен ранее принятый `0.1.18-canary58-physical`, versionCode58,
  пакет `com.familyconnect.app.friends`, UID10283.
- APK SHA256: `91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Точный source inventory, прежняя in-place установка и сохранение Device Identity
  подтверждены [предыдущим отчётом](2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md)
  и [provenance58](2026-10-03-canary58-provenance.json). Они не выдаются за новую
  сборку/установку/повторный JVM или lint запуск в этой задаче.
- Никаких uninstall, pm clear, reenrollment, manual readiness injection,
  synthetic server fixture, manual room URL или SSH product forwarding.

## Живое окно и физические условия

В01:22UTC gateway certificate действовал до **01:57:34UTC**, BootstrapDirectory
до **01:52:37.529101038UTC**; оставалось около30мин. Зарезервированы20мин основной
проверки и5мин очистки. **Renewal не выполнялся**. Authority/issuer/Family/gateway
и единственный owner не менялись. Проверка и очистка закончились до expiry.

NL bootstrap READY, PID2804597, NRestarts0; unit active/disabled, как до задачи.
`gateway.json`: family-restricted:family-restricted979:979,0600;
parent root:family-restricted01770; чтение пользователем сервиса разрешено.
RU/NL одинаковые authority binding, signed CRL и directory; floor336 на входе,
384 при финальной сверке. Продвижение — обычный действующий sync timer, без
ручного сброса floor или повторного deployment acceptance. Python-проверка
подписи/сроков и согласованности PASS; native authority validation не запускалась
заново, поскольку принятую gateway credential в этой задаче не заменяли.

Физический Redmi Note9Pro, Android12/arm64, ADB device; Wi-Fi OFF, cellular ON.
ADB reverse/forward отсутствуют. Перед override обнаружена ранее включённая
обычная AWG-сессия Friends. Начальный узкий фильтр dumpsys ошибочно её пропустил;
исправлен только наблюдатель: учитывает `VPN CONNECTED`, а не только `Transports: VPN`.
Исходное доказательство не затёрто, поправка сохранена отдельно. Сессия штатно
отключена через существующий диагностический stop; перед ON VPN отсутствовал.
Другой VPN не обнаружен. Никаких изменений Android security/input permissions.

## Override и настоящий CONNECT

Существующая private Activity включила только deny_awg/deny_wg/deny_tcp.
Проверены все persisted flags=true и fsynced receipt `ACCEPTANCE_OVERRIDE=ON`.
Пакетный launcher разрешён через PackageManager:
`com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity`.
ActivityNotFoundException отсутствует. READY/Family TLS/BootstrapDirectory/usable
и ACK_RECEIVED подтверждены перед приглашением к ручному CONNECT.

В01:31:40UTC объявлено `READY FOR MANUAL CONNECT / PRESS CONNECT ON THE REDMI NOW`.
Внутри120-секундного окна появился новый структурированный `connect_requested`.
Нет автоматического нажатия, вызова прямого connect-service или fixture CONNECT.

| Событие | Время от CONNECT |
|---|---:|
| CONNECTING | 0ms |
| AWG attempt / diagnostic TRANSPORT_UNAVAILABLE | 1738 / 1745ms |
| TCP attempt / diagnostic TRANSPORT_UNAVAILABLE | 3748 / 3753ms |
| Restricted candidate attempted | 7760ms |
| Restricted candidate succeeded / CONNECTED | 30697ms |
| time_to_connected | 30704ms |

В фактически настроенном списке normal candidates были AWG и TCP; отдельного WG
attempt не заявляем. Сохранены native события `bootstrap_cache_loaded` →
`bootstrap_carrier_connected` → `bootstrap_family_auth` →
`bootstrap_descriptor_received` → `bootstrap_closed_before_dedicated` →
`dedicated_data_ready` → `vpn_packet_ready`. Это доказательство существующего
BOOT-1/Family auth/Room Broker handoff и отдельной restricted-сессии, не UI-индикатор.
Native state2, owner_transport restricted, owner_health ok.

## Whole-device трафик и пользовательские проверки

Android VPN принадлежит Friends UID10283, захватывает user0 UID0–99999, маршруты
IPv4 `0.0.0.0/0` и IPv6 `::/0`; Family DNS `10.79.0.1`, bypassable=false.
Chrome UID10195 входит в этот диапазон. Структурированный restricted session,
TUN packet counters, Family DNS/Mux и переданные байты наблюдались одновременно.
Тем самым подтверждён путь Android TUN → Family packet/Mux/DNS → dedicated
restricted Family session → Telemost carrier → gateway → Интернет.

Chrome открывался обычными ACTION_VIEW URL intents, без ADB touch/key injection.
`https://example.com` и `https://example.org` загружены по два раза с уникальными
query; все4 наблюдения подтверждают Chrome, ожидаемый host/Example Domain content,
отсутствие network error и сохранение Friends VPN. Проверки01:35:18–01:35:48UTC.
Существующий application probe дополнительно получил HTTPS200/200 с обычной
TLS-проверкой сертификатов и hostname, а также ожидаемый NXDOMAIN.

| Измерение к концу healthy traffic | Результат |
|---|---|
| Family DNS requests/responses | 44/44; errors0, timeouts0 |
| TCP / OpenOK | 31 / 31 |
| Пик параллельных TCP / Mux streams | 14 / 14 |
| Mux bytes sent / received | 67803 / 248824 |
| Native packet failed | false |
| Underlay protection | protect_ok148, protect_denied0 |

Не заявляем отсутствие всех transport ошибок: зафиксированы OpenErrors1,
Resets5, ProtocolErrors8, FlowStalls16. Контролируемые страницы и TLS-пробы
прошли, сессия оставалась healthy. Эти счётчики не скрыты и не названы нулевыми.
Ограниченный дополнительный NL journal запрос завершился timeout; журнал по
принятому runbook негейтящий. Повторного расследования/изменения сервера не было.

## Fail-closed: точная область доказательства

Область — текущий Android user0, Friends/Chrome и существующие application probes,
не privileged traffic, другие Android users/work profiles или глобальный OS pcap.

- **Прямой DNS: измеренный дополнительный underlay DNS =0.** За controlled healthy
  traffic счётчик остался16→16, Family DNS вырос5→44 с44ответами. Сохранены
  маршруты всех UID user0 и Family DNS. Это instrumented measurement, не независимый
  packet capture всего cellular-интерфейса; глобальную «нулевую утечку ОС» не заявляем.
- **Protected TCP bypass: 0 успешных соединений из1 корректной failure-пробы**
  к `1.1.1.1:443` во время RESTORING. VPN был активен до/после, owner_health checking.
  Это ограниченное измерение, не универсальная оценка всех потоков во всё время.
- **UDP/QUIC fail-closed:** UDP443 probe отправлен в захваченный путь;
  packet udp_denied0→93. Это блокировка unsupported UDP, не успешная QUIC-сессия.
- **IPv6 fail-closed:** literal IPv6 TCP connect завершился ожидаемой ошибкой;
  ipv6_denied2→18 при сохранённом IPv6 default capture route.
- **Underlay protection:**148 успешных protect,0 отказов; соединение и трафик
  прошли без наблюдаемой VPN recursion. Новых transport/route исключений не добавляли.

## Один контролируемый сбой

Ровно один раз вызван существующий `mode=failure`; новой failure/recovery схемы нет.
`transport_lost NETWORK` появился через336550ms первоначальной сессии.
RESTORING → normal candidates rejected → restricted retry → FAILED через14482ms;
категория `BOOTSTRAP_UNAVAILABLE`. На попытке восстановления native дошёл до
bootstrap carrier/Family auth, затем startup_failed до получения descriptor.
Точная причина этой неудачной restoration не установлена; автоматическое успешное
восстановление не заявляем. Терминальный FAILED разрешён существующей acceptance.

Во всех17 bounded наблюдениях VPN ownership и IPv4/IPv6 capture routes сохранены;
одна валидная TCP-проба заблокирована, прямой cellular fallback не наблюдался.
Управляемый сбой тем самым прошёл проверку существующего fail-closed поведения.

Позднее зарегистрирован **новый** connect_requested и restricted CONNECTED за31368ms.
Его инициатор из доступных данных не установлен; ассистент не отправлял CONNECT
и не повторял failure. Дополнительная probe, задуманная как проверка terminal FAILED,
попала уже в здоровую новую restricted-сессию и успешно соединилась. Сохранён
отдельный разбор: эта probe **исключена** из failure-state denominator; её нельзя
называть ни обходом VPN, ни второй успешно заблокированной пробой. Исходные записи
контролируемого FAILED и последующего CONNECT сохранены без исправления задним числом.

## Очистка и финальное состояние

В01:45:22UTC новая сессия штатно отключена. Existing prepare deny_normal=false:
fsynced receipt OFF, все deny flags false, fail_active отсутствует. Затем
force-stop/start через разрешённый launcher, PID7119→13021; свежий процесс
подтвердил OFF и Auto. Новый encrypted restart receipt: READY, Family TLS и
BootstrapDirectory PRESENT_VALID, orchestrator_usable=true, ACK_RECEIVED,
revision2/minimumCRL368. Activation=true, UID и данные сохранены; identity bytes
не читались/не заменялись. VPN после штатного disconnect отсутствует.

Auto policy восстановлен конфигурационно; отдельный normal CONNECT после очистки
не запускали. Wi-Fi0/cellular1, adb reverse пуст. Временный UI dump удалён.
Никакой remote test policy не создавался, удалять серверное тестовое состояние не нужно.

Финальная production проверка01:46–01:48UTC: NL тот же PID2804597/restarts0;
RU sync timer active, последний oneshot success; одинаковый RU/NL floor384,
authority/CRL/directory hashes. Один owner, без новых admissions.
HTTP PID3917121/generation `attempt17-0615953`, nginx и артефакты неизменны.
RU AWG1515959/TCP1908885 и NL AWG2729703/TCP2420425 неизменны.
Сериализованные external probes не чаще1/sec:200/400/400/400, без429/502.
Gateway ownership/mode/readability сохранены. HTTP/AWG/TCP не перезапускали;
server binaries, schema и staging не трогали. Production rollback не требовался.

Доказательства с fsync и SHA256 inventory находятся в закрытом ignored каталоге
`state-client-build/physical-manual-20261003-0120/`: window/consistency, correction,
override-on, connect-result, chrome0–3, application-probes, traffic-before/after,
measurement-scope, controlled-failure и17samples, supplemental-probe-reconciliation,
cleanup, final health/consistency, ordinary-final, acceptance-summary/evidence-inventory.
Credential secrets/частные ключи не включены в отчёт или Git.

**Stage5N закрыт. Дополнительных Stage5N gates нет.** Следующая проектная фаза:
2–3 доверенных реальных field-canary и DIAG-1A параллельно, без автоматического
старта в этой задаче. FIELD-1/DIAG-1/OPS-1/beta не начаты; push нет.58 остаётся
частной установленной сборкой; публичные downloads/invitation artifacts не менялись.
Истечение зафиксированных short-lived credentials после проверки не продлевается
этим отчётом: перед будущим использованием нужна обычная проверка/renewal по runbook.
