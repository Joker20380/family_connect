# XHTTP/TLS: исследование и реализация5.3в

24.09.2026. Запрос пользователя: обязательная поддержка сетей с белыми списками,
ориентир Shuka. Первый регион испытаний — Краснодар; оператор пока неизвестен.
Телефон/абонентские данные в репозитории не хранятся. Это обзор найденных первичных
источников и реализация выбранного кандидата, не исчерпывающая спецификация Shuka.

## Что известно из источников

| Источник | Подтверждённое содержание | Что из него не следует |
| --- | --- | --- |
| [Shuka, сообщения об «Атлантиде»](https://t.me/s/ShukaVPN?before=34) | Заявлен режим для ограниченной мобильной сети; исторически отмечались нестабильность, обновления подписки и применение только при отказе обычных локаций | Точный протокол, текущие адреса, доступность в Краснодаре и гарантированное восстановление не установлены |
| [Разработчик Xray: XHTTP](https://github.com/XTLS/Xray-core/discussions/4113) | HTTP-транспорт с пакетной/потоковой отправкой, TLS/REALITY, HTTP2/3 и вариантами работы через промежуточные HTTP-узлы | Наличие XHTTP не подтверждает доступность конкретного CDN у оператора |
| [Официальный пример XHTTP + Nginx](https://github.com/XTLS/Xray-examples/blob/main/VLESS-TLS-SplitHTTP-CaddyNginx/nginx.conf) | Reverse proxy к локальному HTTP origin | Пример не является нашим готовым production deployment |
| [REALITY](https://xtls.github.io/en/config/transports/reality.html) | TLS-подобная защита совместима в том числе с RAW и XHTTP | Подмена внешнего вида не меняет маршрутизацию к IP |
| [Cloudflare gRPC](https://developers.cloudflare.com/network/grpc-connections/) | Требуются включённая поддержка, TLS/HTTP2/ALPN и корректные параметры; есть ограничения продуктов | Это не рекомендация выбранного CDN и не доказательство работы в российских белых списках |
| [Tor: transports](https://support.torproject.org/tor-browser/circumvention/unblocking-tor/) | meek использует облачное/CDN направление, Snowflake — волонтёрские прокси, WebTunnel выглядит как HTTPS | Эти варианты не включаются автоматически в наш Xray runtime и требуют самостоятельной интеграции |

Первоначальная попытка открыть Telegram без параметра не удалась. Затем указанная
выше историческая страница прочитана; сообщения с обновлениями сентября2025 нельзя
выдавать за измерения сентября2026. «Белые списки» — продуктовый режим, а не название
единственного протокола. Протокол Shuka остаётся неизвестным.

## Решение для Family Connect

Первый реализуемый кандидат — VLESS/XHTTP/TLS, packet-up, HTTP2 поверх TCP.
Это наше инженерное решение: переиспользуем закреплённый Xray, существующий TCP
TUN/owner/routing и не добавляем зависимость от UDP на первом участке. Закрепление:
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` (v26.3.27); сверены
[реальный dialer](https://github.com/XTLS/Xray-core/blob/d2758a023cd7f4174a5a5fa4ff66e487d4342ba0/transport/internet/splithttp/dialer.go)
и [TLS-конфигурация](https://github.com/XTLS/Xray-core/blob/d2758a023cd7f4174a5a5fa4ff66e487d4342ba0/infra/conf/transport_internet.go),
а не только документация latest. XHTTP выполняет TCP dial через DialSystem;
Android продолжает ограничивать endpoint и привязывать соединения к своей сессии.

Схема для проверки: клиент → доступный TLS ingress (свой reverse proxy либо CDN)
→ origin Xray → интернет. При необходимости отдельного egress потребуется ещё
настроить защищённый участок ingress→egress: текущий renderer выпускает direct-egress
origin, каскад и fleet provisioning не объявляются готовыми.

Сравнение вариантов — проектные выводы:

- Достижимый IP + прежний REALITY: меньше изменений, но сначала нужен этот IP.
- XHTTP/TLS + HTTP proxy/CDN: выбран для первого стенда; необходимы совместимость
  потоковых ответов, отключение cache/buffering, допустимые лимиты и доступность ingress.
- WebSocket/gRPC — альтернативы для последующего сравнения. Не добавлять все сразу
  без измеримого преимущества; streaming ограничения посредника проверяются отдельно.
- HTTP3/QUIC — не первая реализация: UDP может быть недоступен. Возможности протокола
  и поддержка конкретного CDN не равны доступности сети.
- meek/Snowflake/WebTunnel — отдельные кандидаты, особенно для recovery; потребуется
  собственная оценка client runtime, доставки bootstrap и стоимости эксплуатации.

Если TLS завершается у CDN, CDN входит в доверенную инфраструктуру: он видит
VLESS credential, адреса назначений и данные, не защищённые внутренним TLS приложения.
Нельзя обещать end-to-end шифрование произвольного payload до origin при такой схеме.
Signed/encrypted control envelopes остаются отдельной защитой. Для недоверенного
посредника нужна дополнительная сквозная защита; она в этой итерации не реализована.

Домен может быть в .ru, .com, .net и т.д.; зона не даёт автоматического попадания в
белый список. Нужны управление DNS, проверяемый сертификат и совместимое размещение.
Пользователь предоставил существующий домен, его NS обслуживает Timeweb. DNS
не менялся. Для входа планируется отдельный поддомен; основная A-запись относится
к хосту вне разрешённого контура и не используется для развёртывания.
Новый CDN/сервер пока не выбран.

## Реализованный контракт и карта кода

JSON-профиль `vless-xhttp-tls-v1`: ровно `type, server, port, id, server_name, path, mode`.
`server` — канонический IPv4 (исключены loopback/нулевая/мультикастовая области),
`server_name` — DNS-имя для TLS и Host, `id` — ненулевой канонический UUID.
`path` — один сегмент16–128 символов из `[A-Za-z0-9_-]` с `/` по краям;
`mode` строго `packet-up`. Для реального профиля path создаётся случайно; это
не замена аутентификации UUID. Запрещены extra, downloadSettings, произвольные
headers/outbounds и ослабление проверки TLS. Ни browser dialer, ни H3 не включены.

| Код | Реализованная роль |
| --- | --- |
| `clients/desktop/profile_config.py` | Parser и Xray config; Linux helper/backend используют его при ручном импорте TCP-профиля. Mark/маршруты прежние |
| Android `TcpProfile.java`, `pilot/android-tcp/tcp-android.go` | Java/Go parser, регистрация splithttp и TLS renderer; прежние endpoint restriction, owner, protect, close barrier |
| `clients/windows/Core/TcpProfile.cs` | Подписанная активация version2 с XhttpPath; прежний TCP session host получает TLS/XHTTP config |
| `scripts/activate_windows_tcp.py` | Offline issuer version2; version1 REALITY не меняет подписанные bytes |
| `scripts/xhttp_gateway_config.py` | Генератор origin+Nginx в новом приватном каталоге; plaintext listener только127.0.0.1; private/reserved destinations блокируются routing rule |
| `scripts/check_xhttp.py` | Реальные loopback клиент/сервер, локальный сертификат, двусторонние данные и отрицательные сценарии |
| `pilot/android-tcp/host-check/` | Компиляция настоящего bridge Go-кода; host stub только для Android protect callback |
| `.github/workflows/xhttp.yml` | Автоматическое повторение сетевых проверок с pinned Xray; новый workflow сам по себе не результат CI |

Managed transport schema2 по-прежнему не принимает XHTTP под названием vless-reality.
Friends signed catalog также явно оставлен на прежних типах. Это предотвращает
выдачу нового профиля старым установленным приложениям. Python, Java и C# проверки
этой границы сохраняются. Старый Windows клиент отвергает activation version2;
старые REALITY grants остаются version1 и сериализуются без дополнительного поля.

## Воспроизведение и эксплуатационные границы

```sh
python3 -m scripts.xhttp_gateway_config --profile /private/profile.json --output /private/new-origin
python3 -m scripts.check_xhttp --xray /path/to/pinned/xray
python3 pilot/android-tcp/host-check/build.py --core /path/to/pinned/checkout --output /private/new-host-build
python3 -m scripts.check_xhttp --xray /path/to/pinned/xray --client-binary /private/new-host-build/android-host-driver
```

Renderer не создаёт TLS-сертификаты, не регистрирует клиентов в API, не развёртывает
службу и не выдаёт один credential всем абонентам. Он задаёт одного тестового клиента;
полноценная выдача/отзыв по пользователям должна идти через fleet/access.
Nginx snippet рассчитан на версию с `http2 on`; необходимо выполнить `nginx -t` на
выбранном образе и добавить supervision, firewall, limits и управление сертификатами
перед rollout. Его прохождение в этой итерации не заявляется. Внешний CDN также
должен проверять сертификат origin, сохранять Host/path и не кешировать transport.

Lab сознательно заменяет public endpoint на loopback, разрешает свой echo destination
и использует временный CA только через environment дочернего процесса. В профиль
никогда не добавляется allowInsecure. Host driver не проверяет реальный Android
VpnService.protect/JNI/TUN. Windows checks на Linux не подтверждают DPAPI/службу ОС.

Не закрыты: Friends UI/новый подписанный каталог и capability выдачи, fleet leases/
revoke/метрики ingress, публичный TLS/CDN стенд, native Android ABI build/device,
Windows native CI и TUN, полноценный Linux TUN, реальная мобильная сеть Краснодара,
блокировка входа и доставка замены без основного API. Режим нельзя объявлять готовым
«обходом белых списков» по одному локальному тесту.

## Кандидат CDN после проверки DNS

Timeweb DNS не означает наличие аккаунта или подключённого Timeweb Cloud CDN.
Изучены [настройка origin/домена](https://timeweb.cloud/docs/cdn/settings/origin-and-domains)
и [кеширование](https://timeweb.cloud/docs/cdn/settings/cache): сервис предусматривает
CNAME собственного домена и HTTPS к origin, а заголовки источника влияют на cache.
Это делает его кандидатом для стенда, но открытые страницы не подтверждают нужные
нам POST/streaming ограничения или прохождение российских белых списков. Покупка
не выполнена; CNAME target нельзя выдумать до создания/получения ресурса провайдера.
Перед выбором сравнить доступность и ограничения минимум с независимым ingress.
