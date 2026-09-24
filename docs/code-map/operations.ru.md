# Эксплуатация, сборки, испытания и лаборатория

[Общая карта](README.ru.md). Скрипт рядом с исходниками может иметь реальные побочные
эффекты. Перед запуском читать код и соответствующий runbook, не выполнять каталоги целиком.

## Развёртывание и конфигурация

| Каталог/файлы | Роль | Статус/осторожность |
| --- | --- | --- |
| deploy/friends | API, gateway installers, chat sync, invitation page | Действующий пилотный контур; install изменяет сервер |
| deploy/product-https | TLS ingress и certificate renewal | Nginx/cert/systemd, не бизнес-логика авторизации |
| deploy/systemd | Peer reconciliation units | Проверять path/state и требуемые привилегии |
| deploy/server-load | Метрики нагрузки | Метрики и публикация отдельно от VPN control |
| compose.product.yaml | Product API/state | Не отождествлять с Friends DB |
| compose.pilot.yaml, compose.awg.yaml, compose.tcp.yaml | Пилотные окружения транспортов | Требуются сеть, volumes, native engines |
| compose.yaml, compose.data.yaml, compose.distributed.yaml, compose.site-*.yaml | Лабораторные топологии | Не текущая универсальная production схема |
| Dockerfile.control/product/core | Отдельные образы контуров | Сборка образа не означает deployment |

Хосты и разрешённые зоны работ — в [AGENTS](../../AGENTS.md); не использовать соседние
проекты/хосты. `state-*`, `artifacts` и локальные volume directories — runtime/build
данные, не модули исходников. Приватные данные не перечислять в публичной карте.

## Скрипты по назначению

| Семейство scripts/ | Что делает |
| --- | --- |
| sign_update.py, sign_control_config.py, sign_friends_catalog.py, sign_tcp.py | Разные подписываемые продукты/domains; ключ и доверие проверять по конкретному runbook |
| package_desktop.py, package_control.py, package_tcp*.py | Комплектует артефакты; не публикует автоматически готовый релиз |
| install_*.py, provision*.sh, register*.py, activate_windows*.py | Установка/выдача/изменение состояния: read-only тестами не являются |
| check_fleet.py, fleet_agent.py | Входы fleet validation/gateway operations |
| test_*.py/.sh, check_tcp*.py, check_linux_recovery_live.py | Проверки разных уровней; часть создаёт контейнеры/маршруты/реальный VPN |
| check_public_docs.py | Локальные Markdown links/anchors/image paths; внешние URL только перечисляет |
| generate_*icon.py | Ресурсы оформления, не transport logic |

`pilot/` содержит воспроизводимые стенды: Android/WG/AWG/TCP, Windows broker/TCP,
Amsterdam, messenger и fleet-native. Это не второй production backend.
Смотреть README конкретного стенда и dated evidence; не переносить старую команду
установки на новый сервер без проверки параметров/версий.

## Сборки, проверки и публикация

- `.github/workflows/clients.yml`: платформенные сборки/проверки клиентов.
- `control.yml`, `windows-control.yml`, `messenger.yml`: профильные контуры.
- `awg.yml`, `tcp.yml`, `windows-awg.yml`, `windows-tcp.yml`: transport/native tests.
- `distribute-*.yml`: распространение конкретных версий; наличие workflow не доказывает,
  что он запускался для текущего checkout.
- `updates/`: публичные подписанные каталоги; private signer туда не помещается.
  `VERSION`, Android Gradle version и Windows project version — разные точки версии,
  менять согласованно с процедурой выпуска, не механически одним числом.

Уровни доказательств: parser/unit → shared signed vectors → platform runtime →
native tunnel/полезный трафик → российская сеть/failure acceptance → public artifact.
Не заменять один уровень другим. Для Python использовать профильные lockfiles,
для Java — Gradle/зависимости проекта, для Windows — native Windows gates.
Точные команды: [CONTRIBUTING](../../CONTRIBUTING.md), workflows и отчёт нужного этапа.
Публичные тестовые ключи находятся только в обозначенных TEST ONLY fixtures/vectors.

## Отдельная QUIC-лаборатория

`core/` — Rust binary `family-connect-core`, вход `core/src/main.rs`, зависимости
quinn/rustls/tokio в Cargo.toml. `discovery.rs` получает/проверяет network state,
`tls.rs` обслуживает TLS-часть, `packet.rs` — пакетный путь. `control/app.py` — FastAPI
подписанного bootstrap private Phase0. `data/gateway.sh`, `data/client.sh` и
`distributed/site.sh` готовят лабораторное окружение.

Лабораторные mTLS/discovery/failover не являются реализацией Friends AWG/REALITY или
Reticulum recovery. Документы: [архитектура лаборатории](../architecture.ru.md),
[data plane](../data-plane.ru.md). Сначала определить контур, прежде чем исправлять
«главный control server» по одному названию файла.

## Что остаётся планом

Единая Django-админка/платежи, полная fleet/relay/Friends интеграция, независимый
multi-ingress recovery и новый третий transport — не готовые deployed компоненты.
Текущие границы сверять с STATUS. Обновление docs/code-map не заменяет их реализацию.

Правила [хранения критических секретов и восстановления](../secrets-and-recovery.ru.md).
