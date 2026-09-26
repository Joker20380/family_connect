# Упрощение активации Family Connect — design/result report

Дата: 2026-09-26. Статус: audit + design; реализация серверной части, landing page и
клиентского контракта. Real-device Android E2E acceptance ещё не пройден.

## 1. Как работает существующий invitation flow

Backend (развёрнут через `deploy/friends/access-api.py`, данные в
`control/friends/access.py`, `control/friends/referrals.py`):

- Владелец: `POST /friends/referral/issue` → `Referrals.issue()` возвращает
  `url = https://185.251.89.19:8443/invite/#<64-hex>`. `<64-hex>` — HMAC
  (`referral.key`, `referral-v1:<device>`), хранится только `sha256(token)` в
  `referral_links`. Это долгоживущая opaque invitation reference (capability), не
  WG/RNS/FAMILY credential.
- Landing `deploy/friends/invite/index.html` читает `location.hash` (fragment не
  уходит на сервер), показывает платформу, ссылку скачивания APK и требует:
  отметить checkbox «Приложение установлено», затем нажать «Открыть».
- «Открыть» формирует deep link `familyconnect://invite/<64-hex>`.
- Android (`FriendsActivity.handleInvitation` → `FriendsAccessAndroid.register`):
  `POST /friends/referral/claim {token, request_id=device.reference}` →
  `Referrals.claim()` реконструирует `FC-…` code (идемпотентно по `request_id`),
  затем `POST /friends/challenge` (single-use challenge, TTL 100с) →
  `POST /friends/activate` (`Access.complete`: atomically создаёт device, тратит
  invite, гасит challenge).
- Provisioning: `POST /friends/configuration/<country>` с proof возвращает
  AWG/TCP profile.
- Device Identity: локально (RNS Ed25519 + X25519 WG); `device` = `sha256(rns_public)[:32]`,
  детерминирован от локальных ключей.

## 2. Почему сейчас нужен возврат в браузер

Токен попадает в приложение только через deep link с landing page. При sideload
Android не передаёт контекст установки (см.
[android-sideload-deferred-bootstrap.ru.md](android-sideload-deferred-bootstrap.ru.md)),
поэтому единственный надёжный путь передачи invitation context после установки —
вернуться на страницу и нажать «Открыть». Текущая страница ещё и разделяет это на
два шага (checkbox + кнопка), что теряет пользователей.

## 3. Ограничения Android sideload

Deferred bootstrap (browser → APK → install → первый запуск с контекстом) для
sideload APK невозможен: install referrer есть только у Play Store. App Links
(`autoVerify` + `assetlinks.json`) работают и для sideload, но только для
установленного приложения. Custom scheme — только для установленного приложения.
Подробно в [android-sideload-deferred-bootstrap.ru.md](android-sideload-deferred-bootstrap.ru.md).

## 4. Выбранный механизм automatic/deferred bootstrap

Вариант B (практически надёжный):

- Canonical smart URL `https://<host>/i/#<opaque-id>` (opaque invitation reference в
  fragment, не в access log; backward-compat redirect со старого `/invite/#…`).
- App Link (`https`, `autoVerify`) как primary для установленного приложения; custom
  scheme `familyconnect://invite/<opaque-id>` как fallback.
- Landing page `/i/` с одним primary CTA и без checkbox/инструкций.
- Bootstrap claim = существующий single-use challenge (TTL 100с), привязанный к
  invitation+device+keys; новый постоянный credential в URL не вводится.
- Authenticated recovery через `POST /friends/device/status` (см. п.5).

## 5. Security implications

- GET `/i/` не расходует приглашение (fragment не уходит на сервер; страница static);
  messenger-preview/crawler не может активировать устройство.
- State-changing claim только через `POST /friends/referral/claim` + proof.
- Replay fail-closed: single-use challenge (hash, used-flag), атомарная транзакция
  `complete()` исключает конкурентное создание двух устройств.
- Invitation/entitlement revoke продолжает блокировать unused claims и новые устройства.
- `device/status` — read-only authenticated запрос, доказывает владение identity,
  не расходует invitation и не создаёт устройство; закрывает
  `enroll → commit → timeout → restart` без второго устройства.
- В URL/QR/claim нет private keys, WG private key, FAMILY identity, bearer token.

## 6. Migration / backward compatibility

- Старые действующие `/invite/#<64-hex>` продолжают работать: redirect/parser на
  canonical `/i/#…`; значение opaque-id не меняется.
- Активированные устройства после update не переактивируются: локальная identity
  остаётся, `register()`/`device/status` возвращают active без нового приглашения.
- Никакой смены WG key, сброса provisioning, потери messenger-истории.

## 7. Файлы, которые будут изменены

- `control/friends/access.py` — `status` purpose + read-only `status()` (recovery).
- `deploy/friends/access-api.py` — route `POST /friends/device/status`.
- `deploy/friends/install-access.py` / nginx — canonical `/i/` + redirect `/invite/`.
- `deploy/friends/invite/index.html` — smart landing, один CTA, QR canonical, без
  raw token/checkbox.
- `scripts/check_invitation_page.py` — проверки нового landing.
- `provisioning/friends.py` — метод `device_status()`.
- Android: `EnrollmentCoordinator` (startup state machine), App Link + custom scheme,
  recovery; интеграция в `FriendsActivity`.
- `docs/`: STATUS, PLAN (WIP), `docs/design/*` (этот отчёт + Android note).
- `docs/getting-started.*` и README обновляются **только после** прохождения
  real-device E2E acceptance.
