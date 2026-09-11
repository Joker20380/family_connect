# Изолированное TUN/SOCKS/direct сравнение — 11.09.2026

Следующий пункт PLAN выполнен на первом ноутбуке. Исходно host VPN off.
Два одноразовых Docker bridge namespaces (не host network), новый Xray на серию.
Образ family-connect-xray:26.3.27-pilot1, image id
865c9e3311707e87476611c4fd65dc840ef5b4addf7bac5822e08245e59a5453.
Исполнялся mounted установленный /usr/local/lib/family-connect-tcp/xray, SHA256
4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940;
хеш внутри контейнера совпал с host. Helper/backend/profile_config также mounted
из установленного TCP-компонента. Существующий профиль fctcp75850269 read-only,
private config только в container /run tmpfs0600, удалён; ключи не выводились.

К существующему TUN inbound добавлен SOCKS только127.0.0.1:10819 внутри контейнера.
Оба используют один outbound/Xray/REALITY endpoint185.251.89.19. TUN MTU1280 неизменён.
Direct curl UID65534 и правило10500 bypass main; маршруты direct→eth0 и default→TUN
проверены явно. На ноутбуке маршруты, DNS, offload и установленный VPN не менялись.

## Метод и результат

Пять прежних pinned целей: Cloudflare1.1.1.1, три ipify IP, example.com104.20.23.154.
curl IPv4, connect budget3s/max6s; SOCKS5 с локальным pinned resolve (не socks5-hostname).
Каждый раунд — одна и та же цель одновременно через direct/TUN/SOCKS (3 workers).
Никаких фоновых приложений в namespace, только проверки и мониторинг.

| Серия | TUN | SOCKS | Direct во время VPN | Direct до/после |
|---|---:|---:|---:|---:|
| Новый процесс1 |20/20|20/20|20/20|20/20 +20/20|
| Новый процесс2 |40/40|40/40|40/40|20/20 +20/20|

Все260 HTTP-проверок прошли. На каждый VPN-путь60/60; direct всего140/140.
Основные окна13.60s и27.50s — короткая низконагруженная проверка, не длительная приёмка.

AF_PACKET SOCK_DGRAM на TUN сохранял только IPv4 TCP metadata без payload:
481/977 записей, capture drops0, лимит20000 не достигнут. По времени запроса и curl
local_port сопоставлены все20/40 TUN handshakes: SYN→SYNACK median0.221/0.230ms,
max0.419/0.482ms. Это локальный TUN handshake, не внешний REALITY/TLS handshake.
Снимки external socket count каждые~250ms: peak6 в обеих сериях, peak send queue5047/5293B.
Это дискретные снимки, возможны пропущенные пики; per-request→external-socket mapping нет.

Ранее на host были до190 sockets и TCP-connect timeouts. В текущем сравнении ошибки
не воспроизведены, поэтому нельзя объявить причиной фоновые приложения или TUN:
одновременно отличаются нагрузка, namespace/bridge/NAT и момент измерения.
Данные показывают, что текущий бинарник/профиль способен пройти оба пути при этих условиях.

## Очистка и версии

Container timeout180s с kill-after10, outer timeout205s и finally removal.
Оба запуска exit0, stderr empty. Правила IPv4/IPv6 внутри вернулись к baseline,
процессы остановлены, TUN отсутствует, private runtime config удалён, containers удалены.
Отдельные host snapshots подтверждают неизменность полных IPv4/IPv6 policy rules и
отсутствие host TUN. Существующие Docker services не затрагивались.

Stable Linux0.2.7, published desktop0.2.8, TCP0.1.0, server0.2.1 unchanged.
Сервер не менялся, root components не обновлялись, прежние5 client edits сохранены.
Новый CI/deployment/release не выполнялись; последнее release evidence — first-laptop-resume.
Product code не менялся, operator py_compile и doc diff check прошли. Unit suite не повторяли.
Установочного отката нет; одноразовые процессы/контейнеры уже удалены.

Scripts/results/headers: ignored state-client-build/session-2026-09-11-first-isolated;
рабочие /tmp/fc-first-isolated. Raw metadata локальны, private profiles туда не копировались.

## Дальше

Ограниченно увеличивать параллельность изолированного теста (например1→4→8 на путь),
с теми же pinned целями/direct control, свежим engine для каждой ступени, известным
числом запросов и общим deadline. Записать local TUN handshakes и sockets/FD/queues.
Если сбой воспроизведётся — привязать failed request к TCP flow и локализовать
TUN-only либо shared transport failure. Если останется чисто, сравнить host namespace
при контролируемой нагрузке, сохранив связь пользователя. Не называть успешную короткую
серию решением прежних timeouts; offload/MTU/timeouts остаются исходными.
Этап4 открыт; второй ноутбук пока на паузе.
