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

`scripts/check_public_sources.py` — stdlib guard Git index перед публикацией;
`tests/test_public_sources.py` — проверка секретов в staged bytes и отсутствия
значений в выводе. `.github/workflows/test.yml` повторяет guard в CI (после push).
Это не хранилище секретов и не полный secret scanner.

Source guard также блокирует `.kdbx`/`.keyx`; личное KeePassXC-хранилище не является
частью проекта. Порядок доступа и backup описан в политике секретов.

Локальный vault содержит проверенные encrypted recovery copies; signing/службы пока
читают прежние рабочие источники. [Границы импорта](../releases/2026-09-24-vault-import.ru.md).

`scripts/signing_key.py` — общий loader `--key`/`--vault` для update/control/Friends
issuers. KeePassXC→memfd→private inventory→pinned public anchor; plaintext key-файл
не экспортируется. `tests/test_signing_key.py` содержит synthetic KDBX integration.
[Команды и ограничения](../vault-signing.ru.md).

Дополнительные потребители `signing_key.py`: `sign_tcp.py`, `tcp_setup_signature.py sign`.
Standalone setup verifier не зависит от vault. `deploy/friends/70-private-files.conf`
задаёт UMask0077 для будущих запусков AWG/TCP; установщики содержат то же правило.
[Проверка configured/runtime и приёмка](../releases/2026-09-24-secret-consumers.ru.md).

[Приёмка runtime UMask0077 после TCP restart RU/NL](../releases/2026-09-24-tcp-private-umask-restart.ru.md):
настройка уже действует, source changes/версий в этом шаге нет.

`scripts/server_secret_snapshot.py` — allowlisted FC state→private binary stream,
gateway registration lock/SQLite online backup; `verify` проверяет inventory/hash
и SQLite в памяти. `tests/test_server_secret_snapshot.py` — WAL/lock/path/tamper.
[Runbook](../server-secret-backup.ru.md). Orchestration SSH→KeePassXC пока операторский,
автоматического расписания backup/full-service restore нет.

Infrastructure scope того же snapshot модуля: SSH host identity/authorized_keys,
RU Certbot regular files + private link mapping, NL mailbox identity/bootstrap/spool.
Тесты проверяют границы ссылок и обязательную identity; SQLite остаётся online backup.
[Checkpoint и обнаруженный chat-sync сбой](../releases/2026-09-24-infrastructure-secret-backup.ru.md).

Внешняя зависимость membership — синхронное время RU/NL.
`deploy/time/family-connect.sources` содержит дополнительный NTS-источник;
[приёмка новых серверов и диагностика](../server-time-and-chat-sync.ru.md).
Приёмник сохраняет fail-closed TTL, runtime код не изменён.

`scripts/vault_restore_probe.py` — in-container восстановление четырёх закрытых
snapshots в tmpfs, проверка Access/referral и mailbox identity/start/stop.
`tests/test_vault_restore_probe.py` — private modes, TLS links, overwrite/symlink refusal.
`pilot/recovery/Dockerfile` — добавление pinned LXMF к локальному control test image.
[Границы и запуск](../vault-restore-rehearsal.ru.md); production secrets не идут в CI.

[Реестр категорий секретов и потребителей](../secret-consumer-register.ru.md):
закрытый фактический инвентарь хранится в KeePassXC; operator audit helper локальный,
не production runtime и не CI job. Android signing migration ещё не реализована.

`scripts/sign_android_vault.py` — PKCS12/password members из общего vault_archive,
certificate pin, APK input hash, memfd signing/verify и новый output.
`tests/test_android_vault_signing.py` — отказы и opt-in реальный KDBX/apksigner.
Общий reader `scripts/signing_key.py` обслуживает Ed25519 и Android; проверки
формата ключа/anchor остаются у соответствующего потребителя.
[Runbook](../android-vault-signing.ru.md). Production signing ещё не выполнялась.

`scripts/sqlite_backup_compare.py` — bounded online snapshot, проверка integrity,
логическое сравнение schema/typed rows/rowid; private data/digests не печатаются.
`tests/test_sqlite_backup_compare.py` — WAL, row/schema changes и unsafe inputs.
[Методика и фактическая local DB проверка](../local-sqlite-backup-review.ru.md).
