# Журнал реализации

Журнал описывает завершённые изменения и проверки. Он не означает, что все целевые функции уже развёрнуты на платформах.

## 09.09.2026 — аудит и основа identity/provisioning

* `fc847c9`: двуязычный аудит и ограниченный контракт технических ошибок.
* `a77475b`: настоящая reference RNS identity, отдельный локальный WG-ключ, подписанная привязка/владение, строгая модель желаемого состояния и проверка зашифрованного/подписанного envelope. 75 Python tests passed.
* Нативные приложения, публичная регистрация и реальная RNS-доставка не менялись. [ADR 001](adr/001-identity-provisioning.ru.md).

## 09.09.2026 — транзакционная продуктовая регистрация

* Добавлена явная SQLite migration v1: семьи, entitlement, хеши приглашений и одноразовых challenge, устройства, независимые публичные transport keys, членство и фиксированные события аудита.
* Добавлены проверки прав приватной БД и версии схемы при запуске. Локальная SQLite выбрана для одного хоста; до распределённых control replicas нужен PostgreSQL. Базы других приложений не затрагиваются.
* Добавлены HTTP challenge/complete по приглашению в отдельной app factory. Проверяются identity proof, привязка ключей, действующие разрешения и лимиты. Challenge, расходование приглашения и создание устройства выполняются атомарно.
* Добавлена локальная операторская CLI: миграция, pilot grants/invitations, независимый отзыв устройств/разрешений/приглашений, очистка challenge. Секрет приглашения записывается в новый файл 0600, не в stdout. Публичный API не выдаёт entitlement.
* Добавлены тесты гонок, replay, expiry, revoke, лимитов, privacy, некорректных запросов, миграций, restart и CLI-output. Полный Python 3.14 suite: **102 passed**, включая desktop tests. Остались два upstream deprecation warnings TestClient; обновление зависимостей ради них в этот этап не включено.
* Локальный sandbox блокирует продвижение event loop потока TestClient; тот же suite проходит вне sandbox. Это ограничение среды выполнения, а не пропуск API-тестов.
* Исправлена Docker test stage старого control: новые тесты требуют дополнительных модулей/зависимостей. Старые runtime, v1 API и операторские scripts сохранены. Docker stage не включает desktop-файлы, поэтому число её тестов отличается от полного suite.
* Добавлены [API и инструкция оператора](registration.ru.md): backup/restore, rollback, privacy и ограничения. `state-product/` исключён из Git и Docker context.

Не развёрнуто на рабочем сервере. VPN не включался, gateway peers не менялись, сборки мобильного/Windows-клиента не изменялись, снятый с VPN сервер сайтов не использовался. Отзыв в БД пока влияет только на последующую продуктовую авторизацию; отзыв действующего WireGuard требует следующего этапа reconciliation.

## Следующие этапы (актуализировано 10.09.2026)

1. Клиентский lifecycle: построение и применение runtime из VerifiedProvisioningState, подтверждение результата (ACK), known-good recovery.
2. Подключение нового flow к Linux; нативное secure storage Android/Windows и ручная проверка Windows UI на реальном DPI перед выпуском.
3. Реальная Reticulum-доставка тех же envelopes, ограниченные retry/recovery/failover, beta telemetry, health и policy.
4. Расширение локального gateway adapter на распределённые gateway agents с отдельной аутентификацией и миграцией топологии.

Аутентифицированный fetch, кеш/version floors и локальный gateway reconciliation завершены в исходниках; ACK применения остаётся впереди.

Аутентификация аккаунта, платные подписки, интерфейс владельца семьи, распределённый PostgreSQL и публичная production-эксплуатация не заменяются механизмом операторских разрешений пилота.

Итоговая проверка этапа регистрации: Docker build прошёл, **90 Python 3.13 tests** в его test stage. В контейнере без сети прошли smoke-проверки старых `control.app.health()` и `scripts/admin.py --help`. Они не включают VPN и не заменяют физические регрессии платформ.


## 10.09.2026 — аутентифицированный provisioning provider и Linux cache

* Migration v2 сохраняет продуктовую регистрацию и добавляет одноразовые fetch challenges и историю неизменяемых envelopes.
* Отдельный fetch proof с domain/audience, транзакционная проверка revoke/key/entitlement, запрет replay и fallback к старым версиям. Потеря ответа восстанавливается новым challenge без выпуска лишней версии.
* Операторские init-provisioning-signer, publish-provisioning (--peers-ready), provisioning-versions; signing key не нужен HTTP-процессу. Публикация вручную после подготовки peers, автоматического reconciliation пока нет.
* HTTPS reference client и атомарный Linux cache: floors, повторная проверка lease, точная повторная доставка, отказ при повреждении и обнаруженном откате часов. Нет ACK применения туннеля, нативной интеграции и аппаратной защиты от rollback backup.
* Полный suite: **130 passed**, два прежних upstream warnings; HTTP-тесты запускались вне sandbox из-за известной блокировки TestClient.
* [Протокол, команды, ограничения](provisioning-provider.ru.md). Следующий этап — gateway reconciliation/outbox и применение/отзыв peers; затем интеграция клиента с lifecycle VPN.

Docker: **118 Python 3.13 tests passed**; build succeeded. Legacy health and scripts/admin.py --help smoke checks passed in a container with networking disabled.


## 10.09.2026 — gateway reconciliation и исправление desktop UI

* Migration v3: deployment, адресные резервации и durable peer outbox. Publish/fetch требуют подтверждённого deployment; ручной --peers-ready удалён.
* Revoke атомарно ставит удаление в очередь. Worker проверяет expiry/key/revoke, восстанавливает drift, повторяет ошибки с backoff, подтверждает фактическое состояние. Docker helper перечитывает актуальную запись под lock, включая запоздалые операции после timeout.
* Pilot adapter проверяет gateway key/port/mount, сохраняет публичные peer records атомарно, защищает чужие/static peers. Systemd service/timer подготовлены, не установлены.
* Linux: адаптивные кнопки/перенос, прокрутка и доступность по Tab, постоянный footer, согласованная тёмная тема, HiDPI minimum и отмена timer при закрытии. Windows: явные auto-size строки, ограниченная ширина текста, scroll/footer, PerMonitorV2 и адаптивный диалог кода.
* Linux: 18 layout cases RU/EN, размеры 360×420/480×620/800×700, Scale 100/150/200%; снимок проверен. Windows cross-build: 0 warnings/errors. WinForms /layout-test добавлен в CI, на этой Linux-машине не запускался; ручная DPI-проверка Windows остаётся перед выпуском.
* Настоящий WG в отдельном Docker namespace без сети: install/remove/restart, delayed command после удаления, сохранение чужого peer, read-only /keys — passed.
* [Gateway protocol/operator/rollback](gateway-reconciliation.ru.md), [UI и снимок](desktop-layout.ru.md). На рабочий сервер не развёрнуто, установленные приложения не заменены.

Итог: **155 Python tests passed**, Docker control собран, **143 tests passed** в Python 3.13 stage; два прежних upstream warnings.


## 2026-09-10 — 0.2.1 rollout

Published immutable Linux/Windows release from 8cd0f2d; all client CI passed.
Linux replaced with backup; server gateway/API/worker deployed, 3 peers preserved.
Signed catalog sequence 1 added. Reticulum notifications and personal Windows install
remain pending. Current facts and next steps: [STATUS](STATUS.md), [PLAN](PLAN.md).


## 2026-09-10 — Desktop 0.2.2

Refreshed desktop appearance and temporary dodecahedron icon. CI passed, release
published, catalog sequence 2 signed. Linux upgraded using 0.2.1 updater with rollback
preserved. Windows update available; personal installation pending. See STATUS.


## 2026-09-10 — 0.2.3 quiet polling

Rounded buttons and rotated dodecahedron; polling separated from user-action busy state.
Unchanged polls do not repaint; stale replies discarded. Windows/Linux regression checks
passed; signed catalog sequence 3 published; Linux upgraded with rollback preserved.
See STATUS and release report for exact evidence.


## 2026-09-10 — Linux 0.2.5

User-reported clipping reproduced with actual font metrics (effective scale 2.06).
Font-aware window sizing, themed selector/dialogs, hidden unused scrollbar, cached
layout, separate polling queue and 3s polling timeout. Platform checks passed; signed
catalog sequence 4 published; Linux installed with 0.2.3 retained. Real warm runtime
probe max callback interval 17.9 ms; initial probe gap 850 ms remains documented.
See STATUS and release report for evidence and remaining confirmation.
