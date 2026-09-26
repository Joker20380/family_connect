# Упрощение активации Family Connect — design/result report

Дата: 2026-09-26. Статус: audit + design; реализация серверной части, landing page и
клиентского контракта. Real-device Android E2E acceptance ещё не пройден.

Корректировка 2026-09-26 (на базе commit `308ec08`): устранено противоречие с реальным
Android sideload flow. Fresh-install sideload активация **не** является fully automatic:
после установки APK требуется ровно один явный шаг пользователя — вернуться на уже
открытую landing page и нажать единственную кнопку «Открыть Family Connect».

## 1. Как работает существующий invitation flow

Backend (развёрнут через `deploy/friends/access-api.py`, данные в
`control/friends/access.py`, `control/friends/referrals.py`):

- Владелец: `POST /friends/referral/issue` → `Referrals.issue()` возвращает
  `url = https://185.251.89.19:8443/i/#<64-hex>`. `<64-hex>` — HMAC
  (`referral.key`, `referral-v1:<device>`), хранится только `sha256(token)` в
  `referral_links`. Это referral capability спонсора (bounded campaign), не
  WG/RNS/FAMILY credential.
- Landing `deploy/friends/invite/index.html` читает `location.hash` (fragment не
  уходит на сервер), показывает платформу, ссылку скачивания APK и **один** primary CTA
  без checkbox.
- «Открыть» формирует deep link `familyconnect://invite/<64-hex>`.
- Android (`FriendsActivity.handleInvitation` → `FriendsAccessAndroid.register`):
  `POST /friends/referral/claim {token, request_id=device.reference}` →
  `Referrals.claim()` реконструирует `FC-…` code (идемпотентно по `request_id`),
  затем `POST /friends/challenge` (single-use challenge, TTL 100с) →
  `POST /friends/activate` (`Access.complete`: atomically создаёт device, связывает
  invite, гасит challenge).
- Provisioning: `POST /friends/configuration/<country>` с proof возвращает
  AWG/TCP profile.
- Device Identity: локально (RNS Ed25519 + X25519 WG); `device` = `sha256(rns_public)[:32]`,
  детерминирован от локальных ключей.

## 2. Почему после свежей установки всё же нужен один ручной шаг

Токен попадает в приложение только через deep link. При sideload Android не передаёт
контекст установки (см.
[android-sideload-deferred-bootstrap.ru.md](android-sideload-deferred-bootstrap.ru.md)),
поэтому после установки APK единственный надёжный путь передачи invitation context —
вернуться на уже открытую landing page и нажать «Открыть». Это **не** automatic
deferred activation: fresh install не может восстановить контекст из установщика.

## 3. Ограничения Android sideload

Deferred bootstrap (browser → APK → install → первый запуск с контекстом) для
sideload APK невозможен: install referrer есть только у Play Store. App Links
(`autoVerify` + `assetlinks.json`) работают и для sideload, но только для
установленного приложения. Custom scheme — только для установленного приложения.
Подробно в [android-sideload-deferred-bootstrap.ru.md](android-sideload-deferred-bootstrap.ru.md).

## 4. Два acceptance flow (без fully automatic fresh-install)

Канонический smart URL: `https://<host>/i/#<opaque-id>` (opaque invitation reference
только во fragment; backward-compat redirect со старого `/invite/#…`). App Link
(`https`, `autoVerify`) как primary для установленного приложения; custom scheme
`familyconnect://invite/<opaque-id>` как fallback. Landing page `/i/` с одним primary
CTA и без checkbox/инструкций. Bootstrap claim = существующий single-use challenge
(TTL 100с), привязанный к invitation+device+keys; новый постоянный credential в URL
не вводится.

### Flow A — приложение уже установлено (target: near zero-friction)

```
invitation URL / QR
  → familyconnect://invite/<opaque-id>
  → Family Connect
  → enrollment → provisioning
  → ready
```

Пользовательских действий: **1** (открыть ссылку или отсканировать QR). Возможное
подтверждение браузера для custom scheme не считается шагом активации.

### Flow B — приложение не установлено, sideload APK (target: один очевидный шаг)

```
invitation landing (/i/#<opaque-id>)
  → «Скачать Family Connect»
  → Android installer
  → возврат на уже открытую landing page
  → единственная кнопка «Открыть Family Connect»
  → deep link
  → enrollment → ready
```

Пользовательских действий: **3–4** (открыть invitation → скачать → установить →
нажать «Открыть»). Количество шагов установщика зависит от устройства и системных
диалогов; активация сама по себе добавляет ровно один шаг «Открыть».

**Не заявляется:** fresh-install sideload активация **не** fully automatic;
`device/status` recovery **не** является механизмом передачи invitation при fresh
install (см. п.7).

## 5. Security implications

- GET `/i/` не расходует приглашение (fragment не уходит на сервер; страница static);
  messenger-preview/crawler не может активировать устройство.
- State-changing claim только через `POST /friends/referral/claim` + proof.
- Replay fail-closed: single-use challenge (hash, used-flag), атомарная транзакция
  `complete()` исключает конкурентное создание двух устройств для одного `invites` code.
- Invitation/entitlement revoke продолжает блокировать unused claims и новые устройства.
- `device/status` — read-only authenticated запрос, доказывает владение identity,
  не расходует invitation и не создаёт устройство; это **post-enrollment recovery**,
  а не способ передать приглашение при fresh install.
- В URL/QR/claim нет private keys, WG private key, FAMILY identity, bearer token.

## 6. Migration / backward compatibility

- Старые действующие `/invite/#<64-hex>` продолжают работать: redirect/parser на
  canonical `/i/#…`; значение opaque-id не меняется.
- Активированные устройства после update не переактивируются: локальная identity
  остаётся, `register()`/`device/status` возвращают active без нового приглашения.
- Никакой смены WG key, сброса provisioning, потери messenger-истории.

## 7. Поведение при повторном открытии invitation

| Ситуация | Наблюдаемое поведение |
|---|---|
| Приложение установлено | Flow A: deep link открывает Family Connect, enrollment (near zero-friction). |
| Приложение не установлено | Flow B: landing page, скачивание APK, один шаг «Открыть». |
| Invitation уже использован этим же device | `referral/claim` по `request_id` идемпотентно возвращает `activated`; `activate` не создаёт второй device и не тратит новый invite. |
| Invitation использован другим device | referral link — bounded capability спонсора: другое device получает собственный single-use `FC-…` code и может enroll, пока спонсор active и лимиты кампании позволяют. Сам `invites` code строго одноразовый и device-bound. |
| Enrollment committed, но response потерян | Локальная identity уже создана; повторный запуск идёт через `POST /friends/device/status` (post-enrollment recovery), без нового claim и без второго устройства. |

Примечание: подпись landing приведена к фактической семантике — «Отправьте эту
ссылку человеку, которого хотите подключить» (см. п.9). Сам `invites` code
остаётся строго одноразовым и device-bound; referral link — bounded capability.

## 8. Приёмка на реальном Android (manual checklist)

**FRESH INSTALL (Flow B):**
1. Получить invitation (ссылка/QR) на чистом устройстве без приложения.
2. Открыть landing `/i/#…` → «Скачать Family Connect».
3. Установить APK через Android installer.
4. Вернуться на уже открытую landing page.
5. Нажать единственную кнопку «Открыть Family Connect».
6. Family Connect открывается по deep link → identity → enrollment → provisioning.
7. Подключить VPN и убедиться в рабочем трафике.
Ожидаемые действия пользователя: **3–4**.

**INSTALLED APP (Flow A):**
1. На устройстве с установленным приложением отсканировать QR / открыть ссылку.
2. Family Connect открывается по deep link.
3. identity → enrollment → provisioning → VPN.
Ожидаемые действия пользователя: **1**.

**Recovery (уже activated, без invitation):**
1. Перезапустить приложение.
2. `device/status` возвращает active; повторная регистрация не выполняется.

## 9. Future product split: Personal Invitation vs Referral Link

Текущий backend `referrals` — **bounded sponsor capability**: одна referral URL может
выдать несколько конечных single-use activation codes. Поэтому текущий UI описывает
ссылку нейтрально («Отправьте эту ссылку человеку, которого хотите подключить»), а не
как строго одноразовое приглашение. Сплит на две сущности зафиксирован как backlog и
**не реализуется сейчас**: он потребует изменения Friends DB/API/schema.

### Personal Invitation

Назначение: `Настройки → Пригласить друга`.

Семантика:

- issue personal invite → один получатель → одно новое Device Identity →
  successful activation → invitation consumed.

Требования:

- single-device;
- короткий/контролируемый TTL;
- revoke;
- consumed атомарно с успешным enrollment;
- repeat/recovery с той же Device Identity не считается вторым использованием;
- другая Device Identity после consumption получает отказ.

### Referral Link

Назначение: массовое/реферальное распространение Family Connect.

Семантика:

- sponsor referral capability → N получателей → каждый получает собственную
  single-use device activation.

Требования:

- quota;
- TTL;
- sponsor attribution;
- revoke;
- abuse/rate limits;
- каждый конечный device enrollment остаётся отдельным и одноразовым.

Обе сущности остаются вне runtime scope до прохождения real-device Android acceptance.

## 10. Файлы, которые будут изменены

- `control/friends/access.py` — `status` purpose + read-only `status()` (recovery).
- `deploy/friends/access-api.py` — route `POST /friends/device/status`.
- `deploy/friends/install-access.py` / nginx — canonical `/i/` + redirect `/invite/`.
- `deploy/friends/invite/index.html` — smart landing, один CTA, fragment-only token,
  без raw token/checkbox; переход CTA «Скачать» → «Открыть».
- `scripts/check_invitation_page.py` — проверки нового landing.
- `provisioning/friends.py` — метод `device_status()`.
- Android: `EnrollmentCoordinator` (startup state machine), App Link + custom scheme,
  recovery; интеграция в `FriendsActivity`.
- `docs/`: STATUS, PLAN (WIP), `docs/design/*` (этот отчёт + Android note).
- `docs/getting-started.*` и README обновляются **только после** прохождения
  real-device E2E acceptance.
