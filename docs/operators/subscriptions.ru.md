# Подписки Family Connect: ежедневная эксплуатация

Каноническая инструкция SUBSCRIPTION-OPERATIONS / SUBSCRIPTION-PAID-119, 7 ноября 2026.
Закрытая интеграция PR1 слита в main `9d05c0f936b076b0536f7c7d23833436677e0191`.
Это инструкция по существующей модели, **не разрешение на конкретную оплату**.
Получатель, основание оплаты, абсолютный период и допустимая версия должны быть
согласованы до операции. PR2 закрыт merge `5197563916442d953746cb5aa3d03756ab85e51f`.
Владелец отдельно разрешил политику108/119: установка119 или merge сами по себе
не являются таким разрешением. [Политика A и отдельное решение Б](#политика-a-и-отдельное-решение-б).
Фактические install/CI/merge receipts — в [отчёте PAID-119](../releases/2026-11-07-subscription-paid-119.md).

## Где смотреть и чему доверять

Откройте локально **http://127.0.0.1:8765/subscriptions/**, войдите существующей
учётной записью панели. Право чтения — `console.view_inventorysnapshot`, штатные
группы «Наблюдатели панели» / «Операторы панели». Порт доступен только loopback;
не публикуйте его наружу. Раздел **«Реальные подписки · чтение»** всегда PRODUCTION.
«Демо-устройства», «Записи оплат» и их действия остаются SYNTHETIC, не оплатами
реальных пользователей. Форма демо не принимает HMAC реального устройства.

Проверьте результат и локальное время **последней попытки** collection/import,
отдельно `observed_at` (UTC) **последнего успешного серверного снимка**, время
импорта, SHA256 проверенного серверного runtime и отметку свежести. Ошибка попытки
не скрывается более поздними часами сервера. До 5 минут — свежее *наблюдение*, не live-запрос.
Старше 5 минут — устаревшее; время в будущем более15 секунд — ошибка часов.
Перезагрузка страницы не опрашивает сервер. Сохранённый `state` и `effective_state`
относятся к одному серверному now/SQLite read transaction, а не к времени открытия
страницы. Панель не вычисляет новый допуск из старых данных.
Если сам локальный importer/PostgreSQL недоступен или его60s бюджет исчерпан,
сохранить ошибку в панели невозможно: смотрите private monitor receipt/user journal
и старение последнего успешного снимка. Не считайте отсутствие новой строки успехом.

Различайте: нет наблюдений; ошибка/непроверенный runtime; отсутствующая paid-схема;
устаревшее успешное наблюдение; успешный снимок с нулём устройств; устройство вне
cohort. Ни ошибка, ни отсутствие схемы не означают «0 подписок» или «не оплачено».
При ошибке показано время последнего успешного чтения, но оно не подменяет ошибку.

Цепочка: внешний операторский SSH collector → проверенный archive SHA256 →
`control.friends.subscription.snapshot` и `paid_beta` в каноническом реестре
(`mode=ro`, `query_only`, одна транзакция) → ограниченный JSON → строгий importer →
append-only наблюдение PostgreSQL → страница. В веб-контейнере **нет** SSH-ключа,
production DB или приватного конфигурационного файла источника. PostgreSQL не
подписочная state machine. HMAC связывает наблюдения с существующей инвентаризацией;
Support ID, ключи, reference/payload hashes и банковские реквизиты не импортируются.
Последнее событие связано с текущей ревизией/периодом; отсутствие подходящего
события не мешает показать снимок. Event ID в панели также псевдонимизирован.

## Найти существующее устройство и прочитать status

Попросите владельца передать **Support ID** через закрытый канал из приложения.
Не используйте номер телефона, HMAC из панели или event ID как получателя.
Закрытый операторский receipt содержит канонический registry, проверенный Python,
runtime/operator paths и соответствие Support ID ↔ HMAC. Не помещайте receipt,
сырые status, ключи, БД или персональные пути в Git/PR/общий чат.

Работайте в принятом control/identity Python-окружении с lockfiles. Используйте
административный путь из **актуального закрытого install receipt**, не исторический
оператор106 или ранее подготовленный локальный108. Перед новой записью выполните
read-only `policy`: он не открывает registry даже при указанном `--db`.

```sh
"$OPERATOR_PYTHON" -I "$PAID_OPERATOR_ARCHIVE" policy
```

Должны совпасть `policy=android-paid-108-119-v1`, два release descriptors ниже,
`cohort_limit=10`, archive SHA256 и хеш paid_beta с установленным HTTP runtime.
Пути, interpreter, исходный commit, inventory и checksums берутся из закрытого
receipt. Несовпадение — остановить новую запись, а не подменять APK hash.

В примерах `OPERATOR_PYTHON` — проверенный locked interpreter; команды выполняются
**там, где доступен канонический registry**, не в веб-контейнере. `REGISTRY_DB`,
`SUPPORT_ID` и остальные переменные берутся из закрытого задания.
Отключите shell tracing/history, направляйте результат в новый private0600 receipt.
Блоки используют отдельный subshell с `set -C` (noclobber): существующий receipt
не перезаписывается, команда при таком отказе перенаправления не запускается.
Не используйте `>|`; при точном replay сохраняйте новый receipt, старый оставьте.

```sh
( umask 077; set -C
"$OPERATOR_PYTHON" -I "$PAID_OPERATOR_ARCHIVE" --db "$REGISTRY_DB" status \
  --support-id "$SUPPORT_ID" > "$PRIVATE_STATUS_RECEIPT"
)
```

Нормализация Support ID и уникальность получателя проверяются оператором.
Сверьте `device` с закрытым receipt, `activation_active`, `cohort`, сохранённую
`subscription.state`, `effective_state`, `paid_allow`, период и `version`.
`status` не мигрирует БД. Команда `migrate` существует, но **не является ежедневным
чтением**: здесь её не выполняем. Отсутствующая/повреждённая схема требует разбора,
а не фиктивного enroll. Не запускайте `backfill` для поиска существующего клиента.

## Значения и пределы допуска

- **Activation** — зарегистрированная identity/приглашение; не платёж.
- **Cohort** — постоянное участие устройства в paid_beta. Лимит10, это устройства,
  не люди; expired/revoked сохраняют занятый slot. Удаления/unenroll нет.
- **paid_allow** — разрешение paid-слоя на момент наблюдения, не итоговый VPN-допуск.
  Identity, grants, revocation и другие проверки остаются обязательными.
- **Effective state** — каноническая оценка сохранённой записи и времени.
  `active`/`trial` действуют строго до `paid_until`; `grace` — до `grace_until`.
  На самой границе доступ уже истёк, хотя сохранённое состояние может быть active.
  За пределами cohort остаётся прежний legacy admission; это не unpaid.
- Платный enforcement сейчас покрывает **MESH** (grant/readiness/выдача и срок
  entitlement). **Обычные AWG/TCP не проверяют paid_beta.** Не обещайте их отключение
  после expire/revoke. Отзыв paid-записи — не отзыв самой identity.
- Уже выданные MESH материалы/сессии ограничены прежними сроками/CRL/кешем. Оператор
  не рассылает CRL и не гарантирует мгновенное завершение всех старых сессий.

## Записать оплату или продление

Общая штатная операция — `activate` → **payment/APPLIED**. Это ручная операторская
фиксация согласованной оплаты, не запрос к банку. Отдельной `renew` нет. Общего
режима бесплатной выдачи/платёжного sandbox нет; bound internal_canary из старой
квалификации нельзя переносить на произвольного пользователя или считать выручкой.

Все даты: точное `YYYY-MM-DDTHH:MM:SSZ`, абсолютное UTC, без дробей/offset.
`PERIOD_START_UTC <= server now < PAID_UNTIL_UTC`. Дни автоматически не прибавляются.
Продление — ещё один `activate` с новым event ID и явно согласованным новым концом;
начало не раньше прежнего, конец **строго больше** прежнего paid/grace конца.
Backend допускает равную границу, но такая операция не продлевает доступ и не
должна называться настоящим renewal. Не округляйте период
по локальному часовому поясу. Последние authenticated support/readiness observations
должны согласованно определить **одну** точную пару версии. Equally-latest108 и119
отклоняются как конфликт. Выберите `ACCEPTED_APK_SHA256` именно для этой пары:

| versionName | versionCode | APK SHA256 |
| --- | --- | --- |
| `0.1.18-beta108` |108| `144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf` |
| `0.1.18-beta119` |119| `52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d` |

Это не диапазон версий. Будущие релизы не разрешены автоматически; хеш другой
разрешённой версии также отклоняется. APK119 сохраняет source
`b2a37fe989294018ab08060bdebfa46d741d11d5`, Friends/ARM64 и прежнюю подпись.

```sh
( umask 077; set -C
"$OPERATOR_PYTHON" -I "$PAID_OPERATOR_ARCHIVE" --db "$REGISTRY_DB" activate \
  --support-id "$SUPPORT_ID" --event-id "$PAYMENT_EVENT_ID" \
  --reference "$OPAQUE_REFERENCE" --period-start "$PERIOD_START_UTC" \
  --paid-until "$PAID_UNTIL_UTC" \
  --apk-sha256 "$ACCEPTED_APK_SHA256" \
  > "$PRIVATE_PAYMENT_RECEIPT"
)
```

Постоянный `event_id` создаётся и сохраняется **до запроса**, 8–128 ASCII
букв/цифр/`_`/`-`, без Support ID/персональных данных. Reference — непрозрачная
ссылка на закрытое основание сверки, не банковские реквизиты. При потерянном ответе
сначала сохраните исходный argv, проверьте receipt и свежий status; при повторе
используйте **точно тот же event ID, получателя, действие, reference, период и APK hash**.
Ответ `duplicate=true` означает прежнее применение, а не новую оплату.
Изменённый payload с тем же ID отклоняется `EVENT_ID_CONFLICT`. Не создавайте новый
ID для «повтора» неизвестного результата. Старый duplicate receipt не возвращает
подписку к прежнему состоянию: итог проверяйте отдельным свежим status.
Точный108 replay после upgrade119, expiry или revoke возвращает прежнюю квитанцию
до проверки текущей версии. Не меняйте исходный108 hash на119 для такого replay.

## Grace, досрочное окончание, terminal revoke

**Выберите ровно одно нужное действие**, не выполняйте три блока подряд.
Для каждого согласуйте свой event ID, основание и новый путь receipt.

### Grace — временная льготная граница

```sh
( umask 077; set -C
"$OPERATOR_PYTHON" -I "$PAID_OPERATOR_ARCHIVE" --db "$REGISTRY_DB" grace \
  --support-id "$SUPPORT_ID" --event-id "$GRACE_EVENT_ID" \
  --reference "$OPAQUE_REFERENCE" --grace-until "$GRACE_UNTIL_UTC" \
  > "$PRIVATE_GRACE_RECEIPT"
)
```

### Expire — досрочное окончание

```sh
( umask 077; set -C
"$OPERATOR_PYTHON" -I "$PAID_OPERATOR_ARCHIVE" --db "$REGISTRY_DB" expire \
  --support-id "$SUPPORT_ID" --event-id "$EXPIRY_EVENT_ID" \
  --reference "$OPAQUE_REFERENCE" > "$PRIVATE_EXPIRY_RECEIPT"
)
```

### Revoke — терминальный отзыв

```sh
( umask 077; set -C
"$OPERATOR_PYTHON" -I "$PAID_OPERATOR_ARCHIVE" --db "$REGISTRY_DB" revoke \
  --support-id "$SUPPORT_ID" --event-id "$REVOCATION_EVENT_ID" \
  --reference "$OPAQUE_REFERENCE" > "$PRIVATE_REVOCATION_RECEIPT"
)
```

Каждой операции — **отдельный** новый путь receipt (не затирать предыдущий).
Grace не создаёт новую cohort-запись; граница в будущем и не короче paid/старой grace.
`expire` досрочно делает запись expired. Естественное истечение по часам не обязано
создавать событие. **Revoke терминален**: последующая новая payment/grace запрещена;
старый точный replay лишь возвращает старую квитанцию. Ни expire, ни revoke не
освобождают slot. Возврат к noncohort, удаление event или «отмена теста» восстановлением
старой БД моделью не предусмотрены. После любой операции заново выполните status.

## Что увидит клиент

Попросите открыть **«Подписка и доступ → Обновить»**. Проверяйте время наблюдения,
срок, состояние и правильную identity, не только исчезновение spinner.
Первое подходящее payment-событие сообщает подтверждение **доступа**; продление —
продление доступа. Grace/expire/revoke не означают «деньги получены». Один active
snapshot без события не создаёт оплату или уведомление.

Получается только **последнее соответствующее событие**, не вся история оплат.
Новые события обнаруживаются при открытии экрана/Refresh. Затем durable-сохранение
запускает обычную доставку; обычный старт приложения может доставить ранее сохранённое.
**Независимого фонового получения нет**: при закрытом приложении новая операция
ожидает следующего обращения. Повторный refresh не должен дублировать событие.
Ошибка сети оставляет последнюю подтверждённую проекцию с честной отметкой кеша.
APPLIED в панели не доказывает банковское поступление, прочтение или доставку клиенту.

## Мониторинг и обновление источника

Штатные user timers: `family-connect-readonly-monitor.timer` и
`family-connect-network-probe.timer`. Они зависят от включённого/не спящего компьютера,
его user manager, Docker, SSH/сети. Внешних alerts, SLA и гарантии непрерывности нет.
Read-only monitor: по завершении цикла ещё60s до следующего, три пары collect/import
с лимитами60s, **unit budget380s**, не260s. Network probe: TCP connect только к
разрешённым control-портам, unit95s; это не доказательство VPN/клиентского маршрута.

```sh
systemctl --user status family-connect-readonly-monitor.timer family-connect-network-probe.timer
systemctl --user show family-connect-readonly-monitor.service family-connect-network-probe.service \
  -p ActiveState -p Result -p ExecMainStatus -p TimeoutStartUSec
curl --fail http://127.0.0.1:8765/health/
```

Вне web-процесса `.local/subscriptions-source.json` (0600) содержит ровно
`python`, `archive`, `archive_sha256` из закрытой сверки действующего RU runtime.
Существующий HMAC-ключ переиспользуется, не генерируется заново при переносе панели.
После обычной замены HTTP archive его новый hash/path должен быть **отдельно проверен**
и обновлён оператором; mismatch → unavailable, не автоматическое доверие новому коду.
При SSH failure importer записывает неизвестность, если локальная панель доступна;
при отказе importer старый снимок стареет. Детали без секретов — private monitor receipt.
SSH credential административный: readonly обеспечивается кодом/SQLite, а не
ограниченным SSH account. Не выдавайте этот ключ веб-процессу.

## Резервная копия и проверка восстановления

Старый empty-cohort backup без флага **не годится** для непустого реестра и должен
отказаться. Теперь существующий скрипт имеет явный `--include-paid`; он открывает
source только для чтения, использует SQLite backup API (включая WAL), проверяет
integrity, все строки/хеши таблиц, FK и канонические paid-снимки на одном now после
восстановления в **отдельную** временную SQLite. Live registry не заменяется.

```sh
umask 077
python -m scripts.backup_paid_registry --database "$REGISTRY_DB" \
  --destination "$NEW_PRIVATE_BACKUP_DIRECTORY" --include-paid
```

Destination должен быть новым, не symlink, на закрытом носителе с достаточным местом;
каталог0700, файлы0600. Сохраните `registry.sqlite3`, `receipt.json`, точный source/
runtime inventory и принятый способ восстановления секретов сервиса в закрытом
операторском хранилище. Backup registry содержит приватные данные, не Git/CI artifact.
Отдельно сделайте зашифрованную offline-копию, сверив SHA256 после переноса; ключ
шифрования храните отдельно. Для панели отдельно сохраняются PG dump, synthetic
volume и `.env`/HMAC key; это **не** backup канонического registry.

Успех: `BACKUP_AND_ISOLATED_SQLITE_RESTORE_PASS`, `paid_projection_recovery=PASS`,
live_database_writes=0. Скрипт удаляет только собственный успешный rehearsal-файл;
при ошибке сохраняйте evidence, не используйте копию. Для периодической проверки
уже сохранённой копии запустите ту же команду с её `registry.sqlite3` как source и
новой destination: сравните inventory/checksum и canonical status нужного устройства
на копии. Не запускайте копию с production listener, signer, timers или transport.
`application_recovery=NOT_RUN`: холодный запуск всего сервиса/секретов — отдельный
план аварийного восстановления с остановкой writers и согласованным RPO/RTO.
Не копируйте live SQLite обычным `cp`, не откатывайте оплаты старой БД, не придумывайте
CLI `restore`/`dry-run`: их нет. Для настоящего disaster restore сначала сверяются
все операции после backup; эта инструкция не даёт разрешения терять их.

## Политика A и отдельное решение Б

### A. Новые платные операции для beta119, без потери108

Решение выбрано владельцем. `confirmed_android_release` разрешает только точные
descriptors108/119. Grace использует ту же eligibility без APK-аргумента и без
превращения в payment. Сохранены active identity/invite, MESH revoke, лимит10,
периоды и terminal revoke. `confirm_android_baseline` оставлен108-only для старых
canary/permits; live canary не повторяется. Synthetic backend/seed_demo/immutable
ReleaseMetadata остаются108; старые identities, наблюдения и payment records
не преобразуются в119. Старый entitlement не требует нового activate или upgrade.
Это изменение серверной политики новых операций, не новая Android-квалификация.

### Установка и кодовый rollback политики A

Перед обновлением: согласованный `--include-paid` backup/rehearsal по предыдущему
разделу, private fingerprints paid/identity и сохранённые HTTP/CLI archives, effective
unit и source config collector. `scripts/package_paid_policy_overlay.py` требует
точные SHA256 serving archive и его paid_beta; заменяет **только paid_beta.py**,
сравнивает полный inventory. Bootstrap/renewal и прочие serving bytes не заменяются
снимком HEAD. Оператор собирается `scripts/package_support_operator.py --operator
paid-beta --output "$NEW_OPERATOR_ARCHIVE"` и проверяется реальным `policy`/status.
Пути и точные команды установки находятся в закрытом комплекте, не в веб-процессе.

Restart разрешён только независимому HTTP API после проверки его effective unit;
сразу подтвердите новый PID/archive/module hashes и read-only status. Согласованно
смените archive path/SHA256 в private `subscriptions-source.json` внешнего collector,
**сохраните HMAC key**. Дождитесь успешного импорта и authenticated HTTP200 страницы
`/subscriptions/` с новым runtime SHA и свежим observed_at; ошибка/старый кеш не PASS.

При кодовом rollback: вернуть сохранённый HTTP ExecStart/drop-in и соответствующий
проверенный108 CLI (не legacy106), reload systemd и restart **только этого HTTP API**;
вернуть сохранённый collector source config, не HMAC key; проверить старые hashes,
status и свежий импорт. БД/платежи/cohort/identity/периоды **не восстанавливать из backup**.
Уже выданные119 entitlement сохраняются, новые119 activate/grace после отката
недопустимы. Зафиксировать rollback receipt, приостановить новые119 операции.

### B. Одна подписка AWG/TCP/MESH

Объём предложения: единый canonical paid predicate поверх существующей identity,
не новая billing DB. MESH сохранить в `RestrictedReadiness._grant`, readiness и
выдаче материалов. Для AWG/TCP добавить серверные проверки в
`deploy/friends/access-api.py` на configuration/gateway-configuration после proof,
в gateway registration (`deploy/friends/awg-gateway.py::register`, `tcp_user`) и
в синхронизацию активных peer/user sets **на каждом реально обслуживающем узле**.
Read-only subscription/status и recovery control-путь не должны требовать paid VPN.

Одного запрета скачать профиль мало: уже выданный AWG peer и TCP UUID продолжат
работать. Нужны проверенная доставка paid revision/expiry к узлам, отказ от stale
allow, удаление/блокировка peer и TCP user в runtime **и** persisted config, определённое
поведение существующей TCP-сессии, restart/reconciliation и recovery после продления.
Сохранить legacy noncohort (или отдельно согласовать изменение этой политики),
identity revoke и MESH CRL/renewal; не менять их неявно ради общего переключателя.

Gate: явно согласованная максимальная задержка отключения/правила offline; active,
grace, natural expiry, explicit expire/revoke, renew на AWG/TCP/MESH; ранее выданные
профили и уже открытые сессии; все узлы и restart без возврата revoked доступа;
неучастники и control HTTPS без VPN не ломаются. Зафиксировать rollback правил без
отката ledger и риска повторного допуска. Это отдельное решение, **не реализовано**
и не включено в production операторской передачей.

## Границы доказательств

[Отчёт этапа](../releases/2026-11-07-subscription-operations.md) отделяет фактические
read-only наблюдения от синтетических проверок. Физический ARM119 подтверждал лишь
собственный noncohort через штатный ingress; событие на этом телефоне не проверено.
API35/тестовый backend — отдельные прежние доказательства. White-list/COLD_BOOTSTRAP_GAP,
естественное истечение на Android, смена identity через UI и mixed-network остаются
в прежних статусах. Операторская панель не закрывает эти Android gates.
