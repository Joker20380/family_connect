# 5N-PROV-1 — production restricted provisioning: pre-implementation audit

## Результат

**5N-PROV-1 = BLOCKED. Runtime integration не реализована.** Это не
`IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED`: до deploy gate не дошли.
Причина остановки — буквальное противоречие между reuse BOOT-1 v1 и запретом
live Telemost room URLs в directory. Ни новый wire protocol, ни ослабление запрета
не выбраны за пользователя. Ниже точный gap **до изменения runtime**. Отсутствие
реализованного production issuer само по себе не объявляется непреодолимым blocker.

Starting clean HEAD: `3d9fd7ca3d020618ffb7c8f95068094450483ed4`.
Local origin/main: `26447902137735ac7633f92ba6673395bae078fa`.
`9c82152` и `3d9fd7c` сохранены, история не переписана.
Read-only GitHub Actions: последний возвращённый run `36788357526`,
`Linux control preview`, head `2644790`, completed/failure30.09.2026,
updated22:56:45Z. Это не deployment receipt и не проверка этой задачи.
Production hosts/private DB/ключи не читались; deployed HEAD заново не проверен.

## Противоречие BOOT-1

Source: [directory.go](../../carrier/bootstrap/directory.go),
[seed.go](../../carrier/bootstrap/seed.go),
[accepted report](2026-09-30-webrtc-5n-boot1-bootstrap.ru.md).

- `Directory` v1: version, family, issued_at, expires_at, seeds. Каждый `Seed`
  содержит transport, **join_url**, gateway. Parser требует1–4 seeds с
  `roombroker.ValidJoinURL`; пустой URL или opaque seed ID вместо URL не принимается.
- `SeedManager.Run` **создаёт реальную bootstrap room на сервере**, подключает
  gateway, ждёт READY и публикует `room.JoinURL`. Offline client должен иметь этот
  rendezvous заранее. Создать и узнать первый seed только после потери control
  без другого rendezvous принятый протокол не позволяет.
- Dedicated room — другая комната: Room Broker создаёт её после Family admission
  при recovery; её descriptor не входит в directory. Запрет **dedicated** URLs
  при prewarm совместим с v1; запрет **всех live** room URLs — нет.
- У v1 **нет standalone signature/signing envelope**. Accepted authentication —
  existing Family TLS1.3/mTLS, gateway pin, затем protected cache.
  `SeedManager.Handler` обслуживает уже admitted mTLS-клиента. Нельзя назвать
  эти bytes отдельно подписанным directory. Требование может означать
  authenticated delivery, но это отличается от persistently verifiable signature.

Минимальное уточнение: допускается ли authenticated **bootstrap seed join URL**
в v1, если dedicated URLs исключены, а seed заранее создаёт только сервер?
Достаточна ли accepted authenticated delivery, либо необходима отдельная подпись
response через existing trust? До уточнения условия6/11 и reuse v1 одновременно
невыполнимы буквально. Нельзя молча заменить v1 или доверять downloaded CA по TOFU.

## Точный production gap

1. **Friends API — не `/v2/provisioning`.** `FriendsAccessAndroid` использует
   `/friends/challenge`, `/friends/activate`, `/friends/configuration/{ru,nl}`
   через RU HTTPS ingress. Handler — `deploy/friends/access-api.py`, backend —
   `control/friends/access.py`. В routes/purposes нет restricted-readiness.
2. `Access` связывает RNS public identity и независимый WG public key; purpose-bound
   single-use challenge живёт100s, outstanding≤8/device. `complete` проверяет proof,
   binding, purpose, expiry, used и device revoke. `status` дополнительно учитывает
   revoke invitation. Будущая выдача обязана проверять device и grant совместно
   в одной transactional authorization boundary, не только вызвать `complete`.
3. Friends grant бессрочен после activation. Таблицы invites/devices/challenges не
   содержат Family/entitlement revision/certificate serial/CRL state. Нельзя
   объявить эти проверки реализованными или подставить произвольную Family.
4. `control/product/store.py` и `provisioning.py` — отдельный ProductStore контур,
   не доказательство enrollment actual Friends device в этой DB. Миграция туда
   и создание второй identity не выполнялись.
5. Normal response: device/country/address/tcp_id и offline-signed credential-free
   catalog. Android `ControlTrust` pin — offline update/control root;
   `scripts/sign_friends_catalog.py` использует отдельный domain. Это **не online
   Family issuer**. Offline secret нельзя переносить в API для refresh. Будущая
   issuer/delegation chain должна явно связываться с existing root.
6. Accepted issuer `pilot/telemost_family_fixture.py` создаёт disposable authority,
   identities и temporary ProductStore. Он намеренно не принимает production
   DB/identity/key и не подходит для credentials владельца. Source audit не
   устанавливает отсутствие каких-либо ключей на live hosts.
7. `wholedevice.Refresh` сначала читает existing Family profile и создаёт mTLS
   client, затем получает directory. Первый provisioning обычного Friends этим
   не решён. Readiness inspection read-only, field52 cache не создаёт.

## Ключи и Android import

Accepted `familysession.Credentials`: certificate, private_key, authority,
revocations, family, gateway, minimum_revision, minimum_crl; максимум48KiB.
TLS использует **existing Ed25519 signing key Device Identity**, не WG key.
URI SAN связывает full public identity; OU — protocol/Family/role/revision.
Runtime проверяет TLS1.3/chain/CRL/floors/expiry/gateway pin. Fixture сохраняет
plaintext PKCS8 в profile0600 — это не accepted encrypted production key delivery.

Предпочтительная модель для реализации: signing seed остаётся в existing
`FriendsIdentityVault` (Keystore AES-GCM/AtomicFile/noBackup); сервер получает
только authenticated public identity, возвращает certificate/public trust material.
TLS key representation строится локально из existing identity, без новой identity
или private-key download. Эта интеграция **ещё не реализована**.

Normal `FriendsConfigurationVault` уже encrypted/AtomicFile, но ограничен16KiB,
не48KiB profile+8KiB directory. Две независимые записи не являются atomic pair.
Нужны validated encrypted generation/bundle, одна commit point, persisted replay
floors и native import boundary. Не писать signing seed в SharedPreferences или
новый plaintext file. Readiness/Orchestrator должны читать одну committed generation.
Malformed/stale/failed refresh сохраняет valid generation; definitive authenticated
revocation запрещает usability. Timeout/503 не равен revoke; мгновенная offline
revocation не обещается. Runtime/storage changes в этом checkpoint отсутствуют.

## TTL и prewarm

Ничего не продлено: directory≤1h/8KiB/4 seeds. Реальная usability дополнительно
ограничена живым seed/gateway и certificate/CRL expiry. Broker defaults:
unused descriptor60s, session lifetime10min; это разные сроки.
Persistence не гарантирует recovery спустя часы после последнего control contact.
Будущий FIELD prewarm непосредственно перед тестом допустим, но не закрывает
product offline-window limitation. Продление требует анализа compromise/revocation,
seed rotation/lifetime, signing, stale directory и refresh cadence.

Будущая bounded policy: existing normal-control lifecycle, single-flight,
near-expiry threshold/cooldown, отсутствие CONNECT wait при valid cache и
aggressive polling. Числа политики/tests пока не реализованы и не заявлены как PASS.

## Проверки и физическое evidence

Новые server/Android tests требований11–12 **не добавлены и не выполнены**:
operation/import отсутствуют. Existing directory/cache/issuer tests прочитаны
для проверки контракта, не представлены как новый PASS.
`python3 scripts/check_public_docs.py --all`:408 files/2449 links/0 errors;
`git diff --check` и `git diff --cached --check`: PASS.
`python3 scripts/check_public_sources.py`:1534 index entries/0 blocked files,
staged docs-only changes; это не runtime/security acceptance.

[Предыдущий physical BLOCKED](2026-10-01-field1-device-readiness.ru.md) сохранён:
Identity PRESENT, normal PRESENT_VALID, restricted/BOOT-1 ABSENT, после restart
то же. Здесь телефон не трогали; prewarm/restart/rehearsal/browser/DNS/fail-closed
не запускались. Новых APK/JNI/build/install/signing/publication нет.
По последнему accepted report: public Android beta51/code51, private installed
readiness-only field52/code52, Linux0.2.11, Windows0.2.15. Public artifacts и
invitation pages заново не проверялись. Field52 не final FIELD artifact.

## Deployment boundary

Live deployment впоследствии нужен: **да**, но deployable implementation и точного
deployment plan сейчас нет. Сначала clarification, isolated implementation/tests,
затем отдельный `IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED` с проверенными
artifacts/units/migration/rollback. Текущий BLOCKED не запрашивает deploy approval.

Минимальная ожидаемая зона, **планирование, не команды к исполнению**:

- RU `185.251.89.19:/opt/apps/family_connect`: Friends handler/backend,
  `family-connect-friends-access.service`, ingress `family-connect-product-https`.
  Новая capability сначала только owner device, normal semantics без изменений.
- NL `186.246.45.246:/opt/apps/family_connect`: отдельный ещё не выбранный production
  seed/broker unit, Family admission/CRL synchronization. Не diagnostic listener.
- Secrets/config: accepted anchored issuer/delegation, gateway identity, current
  signed CRL и grant revisions; server-only Telemost OAuth. Offline root остаётся
  локально. Имена env/mounts пока не определены, новые секреты не создавались.
- Migration: определить durable Family/grant/revision/certificate mapping existing
  Friends, backup/backward compatibility. Нельзя обещать «migration не нужна».
- Downtime не измерен, zero downtime не обещается; API restart может кратко
  затронуть control, существующие AWG/TCP units перезапускать не требуется по цели.
- Future rollback: disable новую выдачу, restore сохранённые API/config artifacts
  без отката revocation/replay floors; сохранить DB/keys; stop только новый unit.
  Android только same-signature corrective update, без uninstall/pm clear/downgrade.
  Текущий docs-only checkpoint runtime rollback не требует.

Production deployment: **no**. Diagnostic credentials для продукта: **no**.
Push: **no**. Krasnodar FIELD-1 started: **no**. STOP до уточнения контракта.
