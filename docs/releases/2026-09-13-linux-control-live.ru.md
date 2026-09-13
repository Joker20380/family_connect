# Живой Linux control pilot и исправление health — 13.09.2026

## Результат

Пилот выявил конкретную ошибку критерия commit: standalone WG считался здоровым
при active NetworkManager без проверки трафика. Она исправлена в рабочем исходнике.
Живая приёмка целиком не пройдена: HTTPS через новый WG-профиль не работает;
причина сетевого отказа ещё не локализована. Подтверждения crash/rollback в живом
пилоте нет: сценарий остановился раньше, как и предусмотрено его проверками.

## Живые проверки

Сервер185.251.89.19: перед пилотом сверены четыре WG peers (три прежних + отдельно
зарегистрированный10.77.0.252/32). Lease ещё действовал. Пользователь разрешил
продолжить; обновлять установленное приложение для отдельного preview не требовалось.

Запущены настоящий GTK GUI и локальный pinned relay из принятого комплекта
bc908a5f084a8bb6. Runtime once получил configuration1 по реальному RNS,
импортировал/включил WG через NetworkManager, записал COMMITTED и доставил ACK.
GUI сам выбрал импортированный активный профиль: согласование поколений работает.
Независимая interface-bound HTTPS проверка не прошла; сценарий остановлен до
подготовки revision2 и имитации crash.

Отдельная короткая диагностика с тем же профилем:

- Direct IPv4 HTTPS Cloudflare: HTTP200, TCP0.103s, TLS0.170s.
- TUN default HTTPS: curl28, DNS0.110s, TCP/TLS не установлены.
- TUN forced IPv4 HTTPS: curl28, DNS0.001s, TCP/TLS не установлены.
- Interface-bound IPv4 DNS example.com: exit0.
- IPv4 route1.1.1.1 через fc-app-3caa073e/table52303/src10.77.0.252.
  IPv6 route отсутствовал; этот пилот не доказывает IPv6 connectivity.
- За подключение interface counters rx36344/tx101856 bytes. Эти счётчики не
  доказывают успешность HTTPS и не локализуют потерю пакетов.

Оба запуска отключили тестовое соединение. Основной harness проверил точное
восстановление IPv4/IPv6 policy rules, отсутствие активных VPN и сохранность прежних
профилей. Повторная диагностика также подтвердила отсутствие активных VPN.
Relay и preview GUI остановлены. Один новый профиль оставлен неактивным с
autoconnect=no — он относится к сохранённому committed journal.

## Исправление и проверки

`Linux.control_healthy(ident, expected)` для NM WG дополнительно вызывает
существующий `_probe`: bound HTTPS и совпадение egress с подписанным gateway.
AWG/TCP сохраняют существующие проверки транспорта. `BackendApplication.apply`
использует endpoint именно выбранного signed transport profile; final healthy
перед commit повторяет traffic gate. Обхода при active-only состоянии больше нет
в этом пути control apply/commit. Поведение обычного installed GUI не менялось.

Регрессии: неуспешный traffic probe при выборе кандидата и перед commit не даёт
COMMITTED, сохраняет floor и восстанавливает baseline. Отдельно проверен реальный
LinuxTCP control_healthy: active+failed bound probe=False, successful probe=True.
Целевая suite5 passed; полная **412 passed**, две прежние FastAPI/Starlette warnings.
Полная suite включает проверки распакованного комплекта и real RNS fixtures.
Это локальная автоматическая приёмка исправления; повторного live apply нового
bundle, remote CI и нового release не выполнялось.

Новый комплект:
`/tmp/fc-live-control/fixed/FamilyConnect-Control-Linux-preview-66152538ee2a4f3e.tar.gz`.
SHA256 `9c827f86f03d27705c46830758e114b3f7ef9796320d9e46f09672363de076f3`.
Launcher manifest verify exit0. Прежний принятый архив не изменялся.

## Состояние и следующий шаг

Постоянный state: `state-enroll/control-linux-pilot`. Journal IDLE, floor1,
committed=config1, outbox пуст после доставки. Этот COMMITTED получен старым
критерием и не является успешной network acceptance; не сбрасывать journal для
исправления истории. Profile остаётся неактивным. Не запускать старый preview once
для новых конфигураций. Возврат GUI0.2.8 допустим после завершённого cleanup;
installed current и previous не переключались.

Далее bounded request-to-flow диагностика WG HTTPS (SYN/ответы и маршруты),
затем следующая подписанная revision с правильным previous hash, принятие нового
bundle и crash/rollback/GUI Disconnect. Проверку восстановления через UI не считать
пройденной по принудительной cleanup harness. Existing backend rollback health
остаётся отдельной границей: этот патч усиливает кандидат/commit, а не доказывает
traffic health при восстановлении старой конфигурации.

Gateway lease до2026-09-13T08:43:59Z, envelope1 до08:40:14Z. Если истекли —
renew через штатный gateway worker и новая signed revision; прежние ключи и floor
сохраняются. Удаление peer после expiry в этом шаге не наблюдалось.

Версии: installed Linux0.2.8, previous0.2.7; desktop0.2.9/catalog8 опубликованы
ранее; gateway0.2.1/TCP0.1.0 без обновления. Нет release, merge, установки или
новых server mutations в этом шаге. AWG3.1, native Stage5 и Stage6 остаются открытыми.
