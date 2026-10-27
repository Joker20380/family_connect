# ANDROID-CONTROLLED-BETA / CONTROL-PLANE-1

Дата: 2026-10-27. Input main:
`a948d2328b5bd419b7d88be04b719c1dc6e16646`.
Статус: **DONE / LOCAL SYNTHETIC + PRODUCTION-READONLY SNAPSHOTS**.
Это подпункт существующего ANDROID-CONTROLLED-BETA, не новый продукт/PLAN ID.
Принятый [CONTROL-PLANE-0](2026-10-27-android106-control-plane-0.md) сохранён как
предыдущий checkpoint. Production deployment, реальные оплаты/enrollment —
**NOT_RUN**. Controlled paid launch по-прежнему **BLOCKED** на фактических gates.

## Реализовано

- Django5.2.18/PostgreSQL17: `LANGUAGE_CODE=ru`, `USE_I18N=True`, UTC.
  Русские Admin/login/logout, роли/permissions, model/field labels, формы,
  валидация и error pages, preview/confirm/reconcile, платежи/инциденты/audit,
  фильтры дат, легенды/подсказки, пагинация, состояния и аварийная остановка.
  Machine-readable JSON, event IDs и immutable receipts не переводятся.
- 50 synthetic identities (49 наблюдений106, одна отрицательная fixture84).
  Идемпотентное атомарное расширение прежней fixture12→50 сохраняет первые12
  identities, ключевые bindings/invites и оплаченные события. Paid cap остаётся10,
  новые демо-устройства автоматически в paid cohort не включаются.
- Раздельные `InventorySnapshot`, `InventoryDevice`, `ServerObservation`,
  `TechnicalSample`: PG хранит timestamped observations, не entitlement authority.
  Production inventory не имеет FK в payment/operation models и не принимается
  этими формами. Admin всех наблюдений — только чтение; PG immutable triggers.
- Локальный операторский SSH collector: два разрешённых шлюза, проверка host key,
  stdlib код через stdin, без установки/remote файлов. SQLite `mode=ro`,
  `query_only`, read transaction; только сведения registry/сообщённой версии,
  `/proc`/disk и фиксированный `systemctl show` перечень Family Connect служб.
  Не читаются ключи, env, raw logs, payment/subscription таблицы или клиентские
  сообщения. Нет production SQL/HTTP/service/policy writes, migrate или restart.
- HMAC-псевдонимы вместо canonical device/Support ID; приватный ключ0600 остаётся
  локально, передаётся только в памяти защищённого SSH. В Django нет SSH credentials
  и production registry mount/path/API. Снимки импортируются отдельной локальной
  CLI-командой: strict JSON, allowlist полей/источников/типов, UTC, finite ranges,
  лимит4MiB/10000 устройств, атомарность, SHA256-idempotency и system audit.
  Digest защищает от случайного изменения/повторного импорта, **не является**
  подписанной аттестацией сервера; provenance доверяет локальному оператору/SSH.
- Dashboards: раздельные контуры, источник/период/псевдоним, latest-per-source,
  версии, знаменатели, технические диаграммы, server history/drill-down,
  device history/drill-down, пагинация25. История ограничена100 наблюдениями.
  Snapshot старше5 минут явно устарел; backend synthetic projection — старше60s.
- Демо-телеметрия: 1400 измерений (50×7 дней×4 метрики), идемпотентный seed,
  активация/MESH — успех попытки, crash — сессия со сбоем, API latency — средняя,
  не p95. Метрики/denominators не выводятся из обращений поддержки.
- Аварийный stop: persistent PG flag, permission+CSRF+подтверждение+audit,
  блокирует **новые synthetic dispatch**. Отправленные RUNNING/UNKNOWN запросы
  не отменяет; исходный event readback/reconcile и APPLIED-idempotency сохраняются.
  Это не отзыв подписок/сертификатов и не production kill switch.

## Фактически наблюдалось

Read-only collection выполнен с локальной рабочей станции; код не развёрнут
на шлюзах. Последние снимки checkpoint: RU **15:00:37 UTC**, NL **15:00:39 UTC**.

| Источник | Реестр | Серверные сведения | Граница |
|---|---|---|---|
| RU gateway | 54 устройства, read-only import PASS | load/memory/disk/uptime и фиксированные службы наблюдались | Это не54 человека и не54 Android beta participants; versionCode сообщён, APK не аттестован |
| NL gateway | **UNAVAILABLE**, не «0 устройств» | load/memory/disk/uptime и фиксированные службы наблюдались | Авторитетный registry не получен; backend/data provenance не подменены |

Отсутствующая на конкретном узле служба показывается как «не установлена»,
а не как установленная, но упавшая. Systemd active и низкая нагрузка не доказывают
MESH Connect/здоровье полного сервиса. Первые снимки с более узким перечнем служб
сохранены как история; последующий collector читает согласованный фиксированный
перечень Family Connect, без перезапусков или ремонта служб.

Это точечная инвентаризация, не непрерывный мониторинг. Не подключены production
client telemetry, crash/session denominator, client heartbeat, alert delivery,
централизованный ingestion, retention/архивация или scheduler. UI/JSON возвращают
«не собирается»/`null`, а не ложные0/100%. Production telemetry ingestion блокируется
текущим DB constraint: пока допускаются только synthetic samples.
В PG нет второй subscription state machine, копии paid subscription rows или
самостоятельного ALLOW/DENY. Friends `paid_beta` остаётся единственной authority.

## Проверки

| Gate | Результат |
|---|---|
| Console на настоящем PostgreSQL | **95 PASS**, без skips; не full repository suite |
| Existing paid backend storage/readiness | **76 PASS**, без skips; backend source неизменён |
| CP0→CP1 fixture migration | Старые identities/bindings/paid events сохранены; повтор не добавляет devices/events |
| Empty/non-cohort и cap10 | Проверены в real-backend integration tests; 50 fixtures не расширяют cap |
| Production snapshots | Strict schema/тип/UTC/NaN/duplicate/privacy negatives; import atomic/idempotent; workflow isolation |
| Safety | Auth/RBAC/CSRF, read-only Admin/PG triggers, expiry/version/cap enforcement, emergency stop и uncertain reconciliation |
| Chromium desktop1440×1100/mobile390×844 | **PASS**, русские страницы/фильтры, inventory pagination/drill-down, stop/resume, charts; нет JS errors/page overflow |
| Русский payment/preview/confirm workflow | Демо03: одна новая synthetic payment record, activate→revoke; production funds/enrollment0 |
| Django system/migration checks | No issues; migrations current; no ungenerated model changes |
| Android/backend/public catalog scope | Не изменены; exact APK size/SHA256 повторно сверены |
| Scope/privacy/JSON/links/whitespace | Проверены перед commit; private files/build outputs исключены |

Первый source syntax pass выявил ошибку механической подстановки label для
OneToOneField; исправлено до запуска нового образа. Первая генерация migration
не могла записать checkout от container UID10001; повторена от владельца checkout,
без chmod/reset. Начальные94 tests прошли с read-only pytest cache warning;
финальный invocation использует `/tmp` cache. Эти промежуточные наблюдения не
заменяют финальные gates и не скрывают product/CI failures.

Предыдущие243/10 skips/8 deselections PAID-ENTITLEMENT-MVP и57+76 CP0 остаются
историческими результатами, не повторно объявленным full-suite PASS.
Linux L04.2/Windows/desktop messenger, Android build/install, production writes,
реальные оплаты/cohort и full repository suite **NOT_RUN**.

## Exact Android106 / отсутствие rollout

- versionName: `0.1.18-beta106-recovery`; versionCode:106.
- package: `com.familyconnect.app.friends`; size:56093664.
- APK SHA256: `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- signer SHA256 (принятый вход): `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Private APK: `state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk`.
- Никакого rebuild/re-signing/download/public catalog/update-channel изменения.
  Никакой новой установки или публикации этим checkpoint не выполнено.

## Локальный запуск, recovery и STOP

Адрес: `http://127.0.0.1:8765/`; прежний операторский аккаунт сохранён.
Новых паролей не публикуем; credentials/.env/HMAC/snapshots/screenshots/DB остаются
в ignored private local state. [Runbook](../../control_plane/README.md) описывает
build/up, collection/import, permissions, stop и безопасные границы восстановления.
Существующий Compose project/volumes сохранены; сборка использует allowlisted
source context, не весь checkout. Lockfiles/base-image digests неизменны.

При проблеме остановить **локальную console**, сохранив volumes. CP0 не принимает
fixture50; запуск старого образа с новой registry и частичный PG-only restore
недопустимы. Согласованный paired backup/restore drill — отдельный будущий gate,
не PASS этого checkpoint. Никакой production rollback не выполнялся.
Evidence retained privately: `state-client-build/control-plane-1-20261027/`;
production sanitized snapshots/HMAC: `control_plane/.local/`. Эти файлы не в Git.

**STOP. NEXT — review CONTROL-PLANE-1 и только фактические Android controlled-beta
launch blockers**, без автоматического подключения paid backend к production,
реальных платежей/cohort, client telemetry или новых платформенных задач.
Production console security (TLS/MFA/throttling/least privilege, dedicated SSH RO
identity), continuous collection/alerts и live paid enforcement/recovery требуют
отдельного согласованного этапа. Сам по себе dashboard не закрывает launch gates.
