# 25.09.2026 — изменение стратегии Home Gateway

Пользователь подтвердил: главная задача — установить защищённое соединение
телефон↔домашний компьютер, когда мобильная сеть ограничивает доступ белыми списками.
**Reticulum нужен для discovery/authentication/согласования и восстановления пути;
передавать через него все IP-пакеты необязательно.** Это заменяет первоначальное
требование обязательного IP-over-Reticulum в предыдущем checkpoint25.09.

## Новая архитектура и ближайший результат

```text
Control: Device Identity/FAMILY → Reticulum → signed transport negotiation
Data:    Android TUN → выбранный encrypted transport → Windows Home Gateway
                             direct / relay                     │
                                                     Internet / existing FC VPN
```

Сначала проверить доступность разрешённого ingress на целевой SIM при активных
ограничениях: отдельно RNS control/bootstrap и data path. Если RNS carrier
недоступен, ему также нужен достижимый путь; identity не обходит IP-фильтрацию.
Работа по Wi-Fi или в обычном LTE без ограничений этот критерий не закрывает.
Дальше — relay-assisted authenticated session: оба устройства подключаются
исходящими соединениями, relay не расшифровывает пользовательский туннель и не
подменяет домашний exit. Direct/NAT traversal — следующий этап оптимизации.

AWG/WG и существующие TCP/XHTTP/TLS рассматриваются как кандидаты по фактической
достижимости и возможностям reverse/relay path. Конкретный data transport ещё не
выбран. Наличие XHTTP-кода не является доказательством обхода белых списков.
Session binding связывает существующие Device Identity/FAMILY с выбранными
transport keys, ролями, nonce и сроком; data handshake проверяется отдельно.
Сохраняются взаимная аутентификация, fail-closed/DNS/IPv6, запрет cleartext/public
proxy, loop guards, revoke, feature OFF и неизменный default transport selection.

## Положение в глобальном плане

| Этап | Положение по текущей документации |
| --- | --- |
| 1 — identity/access/base VPN | Есть в пилоте |
| 2 — AWG/recovery | Реализация есть; длительная сетевая приёмка остаётся открытой |
| 3 — TCP transport | Реализация есть; приёмка в разных сетях остаётся открытой |
| 4 — Android/Linux/Windows clients | Пилотный выпуск принят пользователем23.09; это не production readiness |
| **5 — сейчас** | Control/fleet частично реализованы; новый приоритет Home Gateway, **начало5A: дизайн и проверка достижимости** |
| 6 — recovery при полностью недоступном gateway | Сквозная приёмка впереди |
| 7 — сервис/коммерческий запуск | Согласован план7.1 Django; админка, платежи/подписки и коммерческая готовность не завершены |

В Home Gateway:5A control/reachability →5B encrypted session →5C IP tunnel →
5D direct diagnostic gateway →5E existing VPN upstream →5F реальные сети →
5G direct paths/zero-config optimisation. Имена RNS-1–RNS-5 сохранены для continuity;
RNS-2 теперь допускает любой выбранный защищённый data transport.
Ни один из этих gates не пройден. Старые5.1–5.6 control/fleet и новые5A–5G —
связанные поднаправления этапа5, не взаимозаменяемые отметки завершения.

## Изменения и проверка

Обновлены PLAN, STATUS, ROADMAP.ru и roadmap RU/EN/index, архитектура RU/EN/index,
Home Gateway design, README RU/EN/index и docs index. В существующие документы
allowlist-connectivity и XHTTP добавлена связь с новым приоритетом; исторические
результаты не переписаны. Предыдущий отчёт25.09 сохраняет исходное решение как историю.
Лицензирование не изменилось, новый dependency/runtime код не добавлен.

Проверки: новые относительные ссылки и task-specific whitespace, согласованность
5A–5G и новых gates, `git diff --check`. Runtime tests/builds не запускались —
это изменение стратегии и документации. Android beta50/code50, Linux0.2.10,
Windows0.2.14 по release checkpoint остаются прежними; новых artifacts/rollout нет.
Runtime rollback не нужен. Unrelated migration/test debt не возобновлён.

В рабочем дереве до этой задачи были накопленные правки существующих страниц.
Они сохранены; отдельный commit стратегии включает только уже отслеживаемый чистый
Home Gateway design и этот новый отчёт. Обновлённые планы/индексы остаются локальными,
чтобы не включать прежние изменения в commit без разбора. На GitHub не опубликовано.

Проверка из корня:

```sh
git diff --check
rg -n '5A|5B|5C|5D|5E|5F|5G|белых списков' docs/PLAN.md docs/ROADMAP.ru.md
rg -n 'selected|optional|reachability|RNS-[1-5]' docs/reticulum/HOME_GATEWAY_DESIGN.md
git log -1 --oneline
```
