# CONTROL-PLANE · русская локальная панель и наблюдаемость

Substep of **ANDROID-CONTROLLED-BETA**, over the accepted
[PAID-ENTITLEMENT-MVP](../docs/paid-beta.md). Django5.2 LTS + PostgreSQL17,
custom Django Admin, dashboard/accessible SVG charts, device lookup/readbacks,
manual-payment metadata, preview/confirm/reconcile, cohort metadata, incidents,
append-only audit, aggregate analytics and fixed Android106 release metadata.
**Локальные демо-операции + production-снимки только для чтения. Не production service и не paid launch.**


## CONTROL-PLANE-1: текущие возможности и границы

- Интерфейс, Admin, роли, формы, ошибки, состояния и подтверждения — русский
  (`LANGUAGE_CODE=ru`, `USE_I18N=True`). UTC сохранён; технические JSON-ключи,
  коды событий и immutable receipts не переводятся и не переписываются.
- 50 демо-identities не означают 50 paid subscriptions: лимит существующего
  backend остаётся10. Старые12 identities и их события сохраняются при расширении.
- `/observability/`: контур, источник, период до91 дня, знаменатели, диаграммы,
  версии, свежесть; `/inventory/`: реальные устройства, поиск HMAC-псевдонима,
  пагинация25, история устройства; `/servers/gateway-ru/` и `/servers/gateway-nl/`:
  точечные нагрузка/память/диск/uptime/systemd и история снимков.
- Данные разных контуров не суммируются. Демо-телеметрия маркируется явно:
  7 дней ×50 устройств ×4 метрики =1400 измерений. Повтор команды не добавляет
  данные и не создаёт оплаты или подписки:

```sh
docker compose --project-directory control_plane -f control_plane/compose.yaml exec -T console python manage.py seed_observability
```

Production-телеметрия клиента пока **не собирается**: отсутствие данных = `null`,
не0 и не100% успешность. `TechnicalSample` сейчас допускает только синтетические
измерения (ограничение PostgreSQL); нет открытого ingestion API. Для реальных
источников потребуется отдельный согласованный адаптер/схема. Не собираются raw
логи, тексты сообщений, сетевые адреса клиентов, ключи и сведения плательщиков.
Код версии — сообщение устройства (support/readiness ACK), не аттестация APK и не
доказательство платформы, текущего запуска или пригодности к Beta-0.

### Read-only production inventory

В Django не монтируются SSH credentials, production registry или его копия.
Отдельный локальный `collect_inventory.py` передаёт проверенный collector по SSH
stdin (`BatchMode`, `StrictHostKeyChecking`, фиксированные два разрешённых адреса).
На шлюзе: только SQLite `mode=ro`/`query_only`/read transaction, `/proc`/disk stats
и `systemctl show` для фиксированного перечня Family Connect служб. Без изменений
service/policy/schema, миграций, файлов collector на сервере или чтения приватных
ключей, environment, raw logs и paid/payment таблиц. Готовый снимок импортируется
в отдельные PG таблицы; они не связаны с платёжными FK и не определяют entitlement.

```sh
python3 control_plane/collect_inventory.py gateway-ru
python3 control_plane/collect_inventory.py gateway-nl
# Вместо пути ниже — точный файл, выведенный collector (локальный, приватный).
docker compose --project-directory control_plane -f control_plane/compose.yaml exec -T console python manage.py import_inventory < control_plane/.local/ИМЯ_СНИМКА.json
```

Collector сохраняет `.local/gateway-*.json` (0600). Идентификатор устройства заменён
HMAC-SHA256: локальный случайный ключ `.local/inventory-hmac.key` (0600) передаётся
только в памяти по SSH, не хранится на шлюзе. Не меняйте ключ для «обновления»:
это разорвёт историю псевдонимов. Support ID/canonical references/public/WG keys
не входят в экспорт. Снимки, HMAC-ключ, скриншоты и `.env` остаются вне Git.
Не публикуйте снимки: псевдонимизация не делает их общедоступными данными.

Импорт ограничен4MiB/10000 устройств, строгий JSON без duplicate keys/NaN/Infinity,
точные поля/типы/источники, UTC, конечные метрики и хеш целого снимка. Повторный
импорт идемпотентен; журналирует system audit один раз. PG triggers запрещают
изменение/удаление наблюдений. Веб-формы импорта и редактирования отсутствуют даже
для superuser. CP1 сам не имеет scheduler; CP2 добавляет внешний локальный timer
ниже. Web UI не выполняет live SSH polling и не получает SSH credentials.
Старше5 минут — «устарело», недоступный реестр — «недоступно», а не0 устройств.
Период в фильтре выбирает последние снимки каждого источника в этом периоде;
история устройства/сервера ограничена100 наблюдениями и явно подписана.
Systemd active/низкая нагрузка не являются проверкой MESH Connect или SLO.
Автоматические alerts, production crash/session denominator, retention/архивация
и полноценные least-privilege SSH credentials требуют отдельного этапа.

### CONTROL-PLANE-2: continuous read-only collection

`python3 control_plane/monitor_inventory.py` — один ограниченный цикл: существующий
collector RU/NL → существующий strict stdin importer → локальный PostgreSQL.
Никаких payment/entitlement commands, remote uploads/units/config edits. `flock`
не допускает параллельных циклов. Каждый subprocess ограничен60s, цикл unit260s;
ошибка одного источника не прекращает попытку другого. Старые observations не
переписываются, unavailable не превращается в0. После попытки импорта новый
промежуточный snapshot удаляется; прежние ручные снимки не затрагиваются.
`.local/monitor-latest.json` (0600) атомарно содержит последний результат/ошибку,
observed_at/hash, без stderr/credentials/device IDs. История результатов — user
journal; успешные observations — существующий PG audit. Retention PG не добавлен.

Для оператора: `monitor.service.in` подставляет абсолютные `@PYTHON@` и `@ROOT@`;
установить как `~/.config/systemd/user/family-connect-readonly-monitor.service`,
а `monitor.timer` — как `family-connect-readonly-monitor.timer`. Это **локальные**
user units, не units шлюзов. В checkpoint timer включён; интервал60s после цикла.

```sh
systemctl --user status family-connect-readonly-monitor.timer
journalctl --user -u family-connect-readonly-monitor.service -n 10
systemctl --user disable --now family-connect-readonly-monitor.timer
systemctl --user stop family-connect-readonly-monitor.service
```

Для возобновления — `systemctl --user enable --now family-connect-readonly-monitor.timer`.
Timer требует работающие Docker/SSH и бодрствующий workstation/user manager; это
не круглосуточный внешний monitoring SLA. Свежесть UI ограничена5 минутами; при
остановке timer новые данные не появляются. Автоматическая доставка alerts и
production client crash/connect telemetry NOT_COLLECTED. Административный SSH
credential **может писать**: read-only обеспечивается фиксированным кодом и SQLite
`mode=ro/query_only`, не ограниченным ключом. Ключа/production mount в Django нет.
Отдельный least-privilege SSH endpoint требует нового security gate, не выдаётся за PASS.

### Paid boundary: reviewed served baseline, not another authority

[CP2 report](../docs/releases/2026-10-27-android106-control-plane-2.md) фиксирует
reconciled baseline и **DEPLOYED_EMPTY_COHORT / REVIEW_PENDING**: paid schema
PRESENT_EMPTY, exact paid-aware HTTP обслуживает production после одного guarded
restart. Реальных subscriptions/events0; это не paid launch. Общий packaging tool:
`python3 -m scripts.package_paid_boundary build
--ref <commit> --output <new-private-tar>` из repository root экспортирует только
явный committed inventory; dirty working tree/DB/env не входят. `source-gate
--served <private-served-pyz> --candidate <candidate-pyz> --baseline
deploy/friends/restricted/served-baseline.json` требует точного SHA/size/inventory
обоих архивов из versioned reviewed contract. Без baseline действует прежний
paid-only gate; это не способ обойти reconciliation. Это необходимый, не достаточный gate;
нельзя обходить его переименованием архивов или объявлять hash-equivalence по версии.
После создания service drop-in и `daemon-reload`, **до любого restart**, выполнить
`python3 scripts/check_friends_execstart.py --python <existing-python> --archive <exact-pyz>
--sha256 <reviewed-sha256> --port 18086` на сервере. Проверяется effective systemd
ExecStart и весь argv, а не имя/presence drop-in. Проверка read-only; несовпадение
означает STOP до restart. Успешный `systemd-analyze verify` проверяет синтаксис,
но не доказывает, какой поздний drop-in победил. Не выбирать приоритет по догадке.
`scripts/observe_friends_service.py --python <existing-python> --archive <exact-pyz>`
читает только типизированный systemd D-Bus через busctl GetUnit/GetAll/ListJobs.
До restart с уже выбранным candidate используйте `--running-archive <old-pyz>`.
OBSERVED не равно PASS: отдельно требуются argv matches, idle jobs, health и DB gates.
Проверяются signatures/types, empty/nonempty jobs, двойной readback PID/start/config;
ошибки имеют stage/code без stderr/environment values/arbitrary argv. Не использовать
`systemctl list-jobs --output=json` или shell table parsing. Pending jobs допускают
только bounded read-only ожидание до gate, не повторный restart. Committed tests53+8 PASS.
Fresh backup, effective argv и post-start inventory/health PASS; consumed1 rollout/
0 emergency. Второй actual restart candidate запрещён. Предыдущие failed runner/
receipts не изменены и не повторялись. Никакого нового rebuild immutable candidate.
Нельзя удалять paid schema/события или восстанавливать старый DB для повторения
ABSENT gate; новый preflight должен принимать только проверенный PRESENT_EMPTY.
Bundle не устанавливает зависимости, не содержит чужие wheels; внешние Python/
package pins проверяются отдельно. Source/AST import/hash manifests и retained
licenses/notices включены; полный host binary/license audit этим не заявляется.

`scripts/backup_paid_registry.py --database <operator-known-db> --destination
<new-private-directory>` создаёт consistent backup и проверяет **изолированную**
SQLite restore-copy (integrity/FK/logical fingerprints). Source открывается только
`mode=ro`; live registry не заменяется. Отказывается при paid rows/events>0,
симлинках и существующем destination. Private files0600/directory0700. Ошибка —
STOP с сохранением evidence; не удалять backup и не повторять с live restore.
Это не application disaster-recovery: issuer state, service restart, live acceptance
и безопасный application rollback требуют отдельной проверки согласованного baseline.

### Аварийная остановка и восстановление

`/stop/` блокирует новые dispatch в **демо** backend (RBAC+CSRF+подтверждение,
сохранённый PG singleton и audit). Уже отправленные RUNNING/UNKNOWN операции
не отменяются: только read-only reconcile исходного события. Чтение APPLIED
идемпотентно даже при stop. Подписки, сертификаты и production не меняются.

Обновление локального образа: подготовить context, `up --build -d --wait`.
Сохраняйте `.env`, HMAC-ключ и оба volumes. Безопасное немедленное действие при
регрессии — `docker compose ... stop console`, не `down -v` и не откат одного store.
CP0 не принимает fixture50: нельзя запускать прежний образ с новой registry или
переименовывать marker. Возврат к старому состоянию возможен только после review
согласованной пары PG+synthetic registry backup; это не проверенный disaster-recovery
PASS. Частичный PG backup этого checkpoint не считается такой парой.
Никакого production rollout/rollback этим runbook не разрешено.

## Quick start

Requirements: Docker Engine + Compose, Python3.13+ for the preparation script.
From the repository root:

```sh
python3 control_plane/prepare_local.py
docker compose --project-directory control_plane -f control_plane/compose.yaml up --build -d --wait
docker compose --project-directory control_plane -f control_plane/compose.yaml exec console python manage.py createsuperuser
```

Open **http://127.0.0.1:8765/**. There is no default password. Preparation creates
random local application/database secrets in ignored `control_plane/.env` (0600)
only when absent. `.env.example` contains placeholders, not usable credentials.
The checkpoint's browser QA may leave a local-only operator login in ignored
`control_plane/.local/operator-login.json` (0600); inspect it locally, never paste
it into tickets, commits, public receipts or release notes. Fresh checkouts use
`createsuperuser` above. Do not regenerate `.env` against an existing PG volume.

Startup applies PostgreSQL migrations, initializes50 synthetic Friends identities
(49 report exact106; one intentionally reports84), refreshes projections and
collects local static assets. It **does not enroll any device in paid beta**.
Re-running `seed_demo` validates/reuses the same fixture without creating new
identities or payment events after the one-time guarded12→50 fixture expansion.
Expansion retains the original12 identities, invite bindings and paid events. Synthetic private identity keys are discarded after
fixture generation; they are not stored in PostgreSQL or served by UI.

`prepare_local.py` stages an explicit source-only build context at
`.local/build-context`. Docker never traverses the parent repository's state,
APKs, profiles, `.env`, credentials or backups. Re-run preparation before rebuilding
after source changes. Docker image bases are digest-pinned; Python dependencies
are transitively pinned with hashes. Runtime does not mount the checkout or any
production directory. Local named volumes retain PG workflow and synthetic
registry independently. Django does not contact authorized gateway hosts; the
separate operator-only read-only collector described below does.

Only the console's HTTP port is published, on **127.0.0.1**. PostgreSQL has no
published port and uses an internal Docker network. The console additionally uses
a UI bridge so loopback publishing works; this is **not an outbound-network
sandbox**. No remote registry URL/path, gateway address, payment provider API or
generic outbound request facility exists in this app. Django only accepts local
hosts and local PostgreSQL addresses. No public hosting/tunnel/reverse proxy.

## Authority and data boundary

| Layer | Owns | Never owns |
|---|---|---|
| Existing Friends SQLite registry | Canonical identity/activation, `paid_beta_subscriptions`, immutable `paid_beta_events` | Django login/workflow metadata |
| `control.friends.paid_beta` | The sole subscription state machine and effective entitlement decision | Admin UI, charts, payment-provider integration |
| PostgreSQL | Operator accounts, immutable operation intents/workflow, payment metadata, cohort opt-in/handoff metadata, incidents, audit, release metadata | A second subscription table or MESH ALLOW/DENY policy |
| DeviceProjection | Explicit read-only backend JSON and `observed_at` | Current/live authorization, expiry recomputation, subscription writes |

The adapter opens **only** `.local/synthetic/registry.sqlite3` under this subtree
(a separate container volume when using Compose). There is no environment variable
or form field for another registry. Symlinks, absent/wrong fixture markers and
unexpected device sets fail closed. The fixture marker is an operational guard,
not a security boundary against a host administrator rewriting files. Do not
replace this volume with a production registry or modify the guard for convenience.

Support ID is accepted only by a private POST lookup and resolved by the existing
backend. It is not persisted in PG projections, intents, payment records, receipts,
audit, URLs or client/protocol fields. Backend canonical references remain private
administrative data. Amounts/currency/opaque-reference hashes are synthetic payment
metadata; no payer/bank/transaction-secret/crypto-address fields or raw payment blobs.
There are no free-form diagnostic uploads or payment-provider webhooks.

## Operator workflow

1. Sign in. Use **Devices & readbacks** to view fixtures or POST a synthetic Support
   ID/canonical reference. Refresh explicitly; readbacks are timestamped and marked
   stale after60 seconds. Even a recent projection is not a current MESH decision.
2. In **Cohort metadata**, explicitly record synthetic opt-in and verified exact106
   handoff for the chosen fixture. This does not grant any entitlement.
3. Record synthetic operational metadata with explicit purpose: `customer_payment`
   (positive minor units, EUR/USD) or `internal_canary` (strictly zero minor units,
   not a customer payment or revenue). Existing records/default calls remain
   `customer_payment`. Purpose is immutable from creation, even before confirmation;
   PostgreSQL constraints enforce the purpose/amount pairing. Only SHA256 of an
   opaque unique reference is stored. Explicitly confirm the record. Duplicate
   reference hashes are rejected; confirmed metadata remains immutable.
4. Create an **activate** intent with the matching confirmed record, UTC start/end
   and exact APK attestation. One record backs at most one intent. Grace requires
   only a grace boundary; expire/revoke have no payment/date fields. No automatic
   trial/grace and no trial issuance UI. The existing backend supplies all state,
   version, activation, limit10 and terminal-revocation validation.

5. **Preview** runs the real `paid_beta.apply_event` on an in-memory SQLite snapshot,
   then reads before/after via the same backend. Nothing is committed to the real
   synthetic registry. An invalid operation has a safe rejection code, not a fake
   successful projection. Preview is bound to the immutable intent, operator and
   backend fingerprint and expires after5 minutes.
6. Review the exact action/device/periods/before/after. Explicitly confirm the POST
   operation using its signed token. Execution rechecks metadata, fingerprint and
   TTL under locks, then calls the existing backend, not Django state logic. The
   event ID is fixed as `cp0-<request UUID hex>` and never regenerated on retry.
   A state change between preview/execute requires a new preview of that same intent.
7. Read the durable backend event receipt; refresh the projection separately.
   APPLIED describes the operation, not ongoing MESH health or live paid access.
   For support, add categorized/severity/owner/status incidents in Admin; no raw
   logs/messages or personal payment details. Charts aggregate recorded operations,
   observed backend states and version observations, not invented live telemetry.

The BETA-0-CANARY-1 source extension separates `confirmed_payments` (customer only)
from `confirmed_internal_canary_records` in analytics (records, not distinct devices
or occupied cohort slots). Operational activity charts still count all operations,
not revenue. Purpose is shown on record/operation screens, admin filters, new metadata
audit rows and the administrative receipt wrapper; the authoritative backend
receipt/event stays unchanged (`event_type=payment`). Do not infer revenue from that
technical event type or the generic payment audit action. No additional subscription
state machine or production adapter is added. Migration0006 is tested on an isolated
PostgreSQL test database; this checkpoint does not upgrade the running local console/
schema or connect a production canary. Do not reverse to the old positive-only schema
with zero-value canary records or delete retained records to make a downgrade fit.

Only a staff account with the relevant permission can act. `Наблюдатели панели`
have read access; `Операторы панели` may record/confirm synthetic payments,
preview/execute/reconcile, and edit cohort/incident metadata. Superusers manage
accounts/groups. Readback/operation/payment/audit/release Admin screens are read-only;
generic Admin edits cannot bypass workflow. Metadata changes also append audit;
Django's own Admin log records account/group and Admin changes.

## Failure, concurrency and reconciliation

PostgreSQL and SQLite are **not a distributed atomic transaction**. PG row locks
serialize dispatch. RUNNING is durably recorded before calling SQLite; the existing
backend atomically commits event + subscription. PG then records the receipt.
Two clicks/workers share one event ID; another dispatch cannot create another
payment event. PG triggers protect immutable intents, append-only audit, retained
payment rows, confirmed payment metadata and release metadata.

If backend commit succeeds but PG/readback delivery fails, the request stays
RUNNING/UNKNOWN. **Reconcile** performs a read-only lookup of that event ID and checks
the expected payload hash. A matching durable event completes the workflow exactly
once. No event or conflicting event keeps the outcome uncertain; it does not mean
failure and does not authorize another event/payment. There is deliberately no
automatic retry/reset for an absent uncertain receipt in CONTROL-PLANE-0; stop and
review the original operation. Incorrect immutable intent/payment metadata also
needs review, not silent editing, deletion or reference reuse.

The wrapper does not modify keys, identities, invites, activation, Android wire
schema, RNS or MESH certificate format. It does not publish CRLs or instantly kill
old sessions. Existing paid-beta challenge/fetch rechecks, time/CRL/cache bounds and
non-cohort behavior are unchanged. Exact Android106 APK/signature unchanged; release
metadata has no upload, download, signing or public updater/catalog action.

## Checks and local recovery

```sh
docker compose --project-directory control_plane -f control_plane/compose.yaml exec -T console python manage.py check
docker compose --project-directory control_plane -f control_plane/compose.yaml exec -T console python manage.py makemigrations --check --dry-run
docker compose --project-directory control_plane -f control_plane/compose.yaml exec -T console python -m pytest -q -p no:cacheprovider
docker compose --project-directory control_plane -f control_plane/compose.yaml ps
curl --fail http://127.0.0.1:8765/health/
docker compose --project-directory control_plane -f control_plane/compose.yaml stop
```

Tests use a separate real PostgreSQL test database and per-test synthetic registry
copies, not the console's demo data or any production identity. The Compose PG role
is a local bootstrap/test owner; it is not a least-privilege production DB role.
The `health` response reveals only synthetic scope/ready status. Keep logs and
screenshots local; do not print Compose's resolved configuration containing secrets.
Stop preserves volumes. Do not use `down -v`, delete paid rows, reset audit, roll
back to a pre-paid backend or restore an old registry over active identities.
Any future backup/restore must preserve both stores and reconcile pending requests.

Local HTTP is intentional: CSRF, staff/RBAC, same-origin referrer policy, HttpOnly
session cookies, short sessions, no-store responses and restrictive CSP are enabled.
Secure-cookie/HTTPS/HSTS, MFA/SSO, login throttling, production RBAC/network isolation,
backup/restore drills, worker reconciliation automation and real monitoring require
a separate review before any nonlocal use. This is not production security approval.
Live crash/MESH rates remain `null`/NOT OBSERVED without real telemetry denominators.

## Dependencies and stop boundary

New server-side dependencies: Django5.2.18 and asgiref (BSD-3-Clause), sqlparse (BSD),
Gunicorn23 (MIT), WhiteNoise6 (MIT), psycopg/psycopg-binary3.3.6 (LGPL-3.0-only),
pytest-django (BSD-3-Clause). PostgreSQL uses the PostgreSQL License; base images
also carry their own component notices. Existing identity/RNS/cryptography pins
are reused without changing product dependencies. Installed distribution notices
remain in the image; any future redistribution requires preserving notices and
the applicable LGPL source/replacement obligations. No dependency is added to APK.
This local checkpoint is not clearance for public distribution of a server image.

STOP on unexpected non-cohort effects, wrong identity, duplicate payment,
missing/conflicting receipts, unknown outcomes, stale previews, or exposure of
private inputs. No real field identity, payment, enrollment or deployment is
authorized. NEXT remains only actual Android controlled-beta launch blockers;
Linux/Windows/desktop/full repository suite are not prerequisites.
