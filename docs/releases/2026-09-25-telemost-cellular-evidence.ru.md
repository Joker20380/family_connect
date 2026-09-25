# 25.09.2026 — Telemost: Краснодар → Бельгия

Источник: прямое сообщение пользователя в текущей сессии, не наш автоматический
тест и не утверждение reference-проекта.

**Наблюдение:** Android в ограниченной сотовой сети Краснодара успешно завершил
видеозвонок Yandex Telemost с Бельгией. Прямое подключение Family Connect VPN
при этом недоступно.

| Проверка | Результат |
| --- | --- |
| Обычный Family Connect VPN по сотовой сети | Недоступен по сообщению пользователя |
| Штатный видеозвонок Telemost: Краснодар Android → Бельгия | Успешен по сообщению пользователя |
| Telemost headless join / произвольный binary round trip | Не проверено |
| Android↔Windows carrier, RNS announces/Link | Не проверено |
| Home Gateway, FC exit IP, DNS/IPv6/no-leak/reconnect | Не проверено |

Не сообщены оператор, точное время, версии Telemost/Android, длительность,
пропускная способность, codec, ICE/STUN/TURN/SFU route и ОС бельгийского endpoint.
Не считать звонок доказательством Windows endpoint, VP8 или DataChannel. В журнале
нет packet capture или независимого подтверждения механизма мобильной фильтрации.
Не обобщать один звонок на всех операторов/времена/серверы Telemost.

## Следствие для текущего плана

Первый carrier-кандидат теперь **Telemost**, WB — резервный. Первоначальная
рекомендация WB была основана на меньшей сложности reference-кода; новое полевое
наблюдение даёт Telemost преимущество по достижимости в целевой сети.
Это выбор порядка экспериментов, не замена provider abstraction и не признание
WEBRTC-1–5 выполненными. Не снижать identity/FAMILY, TLS и fail-closed требования.

После возобновления реализации: проверить headless Telemost join/сигналинг,
binary carriage (VP8 кандидат; DC отдельная capability), desktop→Android/Windows,
затем RNS announces/Link. Воспроизвести direct-FC failure и carrier success
в одном тестовом окне. Не пересматривать сроки количественно по одному звонку:
риск полной недоступности сервиса снизился, риск интеграции carrier остаётся.

Обновлены существующие PLAN/STATUS, Home Gateway design, roadmaps, architecture
и README. Предыдущие датированные отчёты сохраняют первоначальные решения.
Scope остаётся documentation/preparation-only; carrier-код/dependencies/builds,
сессии с провайдером и работа на устройствах не запускались. Release versions
прежние по STATUS (Android beta50/code50, Linux0.2.10, Windows0.2.14), rollout нет,
runtime rollback не нужен. Все WEBRTC gates открыты.

Проверены ссылки/согласованность текста и `git diff --check`; runtime tests не
применимы к этой записи. Commit содержит только ранее чистый Home Gateway design
и новый отчёт; existing dirty plans/indices сохранены локально без присоединения
накопленных изменений. Push не выполнялся.
