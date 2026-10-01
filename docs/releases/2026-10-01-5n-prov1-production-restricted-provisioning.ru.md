# 5N-PROV-1 — production restricted provisioning + bootstrap delivery

## Authorized deployment attempt — preflight STOP, 01.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** Уточнение статуса:
**prerequisite failure до начала rollout; rollback не требовался/не выполнялся**.
Это не «deployed / physical blocked». Production deployment authorization получена
для `ff9fb09af329402e538003a56eaefd0dce2b6c73`, но explicit правило пользователя
требует STOP, если обязательный secret/material отсутствует или inconsistent.
Именно это условие сработало. Ни seed, ни issuer, ни API, ни migration не deployed.

### Entry and exact missing prerequisites

- Начальный worktree clean, HEAD exact `ff9fb09af329402e538003a56eaefd0dce2b6c73`.
  Local origin/main и live `git ls-remote origin refs/heads/main` совпали:
  `26447902137735ac7633f92ba6673395bae078fa`. No fetch/push/ref rewrite.
- Прочитаны AGENTS, STATUS/current PLAN, architecture и exact accepted
  [runbook](../../deploy/friends/restricted/README.md). Runtime source не изменён.
- SSH: `BatchMode=yes`, `StrictHostKeyChecking=yes`, exact authorized IPs;
  host-key verification успешна, `SSH_CONNECTION` server destination и assigned
  interface address соответствуют каждому expected IP. RU `box-932982`,
  NL `box-966556`; соседние MicroTrader services/excluded host не затрагивались.
- RU,09:32:56UTC: `/opt/apps/family_connect/friends-restricted/` **ABSENT**.
  Required `anchor.pub`, `issuer.json`, `issuer.key`, `admission.json`,
  `revocations.pem`, `sync.key`, `known_hosts` отсутствуют по runbook paths.
- NL,09:32:54UTC: тот же protected directory **ABSENT**; required `gateway.json`
  и `provider.env` отсутствуют. Новый bootstrap service not-found; therefore
  `YANDEX_TELEMOST_OAUTH_TOKEN` **не configured на требуемом новом service path**.
  Это не утверждение, что token/gateway identity отсутствует во всех private
  stores. Другие secret locations и остатки isolated fixtures не искались,
  произвольная замена identity/CA/token не выполнялась.
- Restricted bootstrap/sync units not-found, directory snapshots absent,
  loopback18444 не занят на обоих hosts. RU deployed restricted.py absent.
  NL inspected friends-access app files отсутствуют; venv/dependencies и
  forced-command account ещё не подтверждены.

Runbook допускает создание delegated issuer во время подготовки; более позднее
user instruction явно требует STOP при отсутствующих prerequisites. Поэтому
никакая partial secret provisioning/key generation/offline signing в этом attempt
не делалась. Offline root/private device identity не читались. До retry нужны
authoritative Family/gateway material, anchored delegation/issuer, owner admission,
CRL, dedicated pinned sync credentials и server-only provider configuration;
не просить прислать OAuth/private keys в chat, не использовать diagnostic identity.

### Existing production baseline, not a new acceptance

| Проверка | RU | NL |
|---|---|---|
| Friends AWG/TCP units | active/running, NRestarts0 | active/running, NRestarts0 |
| Friends API | active/running, NRestarts0; start30.09 03:28:04UTC | not deployed here, as expected |
| Available RAM |1087.0MiB/1962.5MiB|556.0MiB/955.3MiB|
| Free filesystem space |8.63GiB|13.88GiB|
| Load1/5/15min |1.23/0.94/0.85|0.40/0.25/0.24|
| Relevant TCP listeners |443/8443/8446/18084; no18444|443; no18444|

RU product API/control containers healthy; existing peer-worker container
`family-connect-product:0.2.1` running/unhealthy, как в предыдущем health report.
Это известное pre-existing состояние, не deployment regression; не исправлялось.
Existing RU gateway images: AWG `family-connect-amneziawg:2-pilot1`, TCP
`family-connect-xray:26.3.27-pilot1`. Наличие running services не доказывает новый
end-to-end normal client smoke; activation/invitation mutation и phone traffic
не запускались после prerequisite STOP.

09:33:32UTC independent public check: system-CA/hostname verified TLS1.3 на
`185.251.89.19:8443`, certificate notBefore28.09 20:25:57UTC,
notAfter05.10 12:25:56UTC; `/status/server-load.json` HTTP200. Response body не
сохранялся/не выводился. Общий TLS validity PASS; product data-plane acceptance
не заменяется этим запросом.

### Rollback baseline and migration boundary

Read-only metadata/fingerprints собраны до изменений; secrets/config contents
не копировались в local artifacts/Git. Safe local receipt:
`/tmp/fc-prov1-predeploy-safe.json` (only whitelist metadata/presence/health).
Production roots не предоставляют Git HEAD (`rev-parse` unavailable), поэтому
deployed revision **UNKNOWN**, не приравнивается к `ff9fb09`/origin/main.
RU artifact fingerprints:

- `friends-access/access-api.py` SHA256
  `16e557b1ceb4099897558ade00b53b265566e34e76ab88d4a673af444ab1795a`.
- `friends-access/app/control/friends/access.py` SHA256
  `f37fe6eccdc6609159d26363b457c62e18b71c7036ca449a6d692349c3a3d48e`.
- `state-product-https/config/nginx.conf` SHA256
  `4426bfa9b589fcca124aed99daaaa9dedcf04cbd2c385a322d9fd92ead925267`.

Эти file bytes не совпадают с checkout versions; packaging/semantic differences
не исследованы после STOP. Перед retry сопоставить live layout/artifacts, не
заменять их вслепую wholesale install script. Unit FragmentPath/DropInPaths/hash,
ActiveEnterTimestamp/NRestarts и container image/state записаны безопасно.

RU DB read-only/query_only: devices27 (revoked4), invites81 (revoked5),
`restricted_*` tables **нет**. Inspected `migrate()` содержит только три intended
`CREATE TABLE IF NOT EXISTS`; CRL publisher добавляет restricted_crl_sequence.
Нет destructive DROP/rename/перезаписи old tables; additive schema совместима
с неизменёнными old API queries. **Migration не выполнялась**.

Backup/config snapshots на production **не создавались**, так как preflight STOP
наступил до любого planned write. Rollback path read/reviewed, но executable
backup/restore rehearsal не подтверждён в этом attempt; его нельзя считать PASS.
При retry private on-host backup/definitions/ingress snapshot обязателен до
изменений, без вывоза private data в task artifacts. No rollback needed/performed.
Deployment-induced API interruption **0s: no service transition/reload occurred**;
continuous availability measurement не запускалось, zero-downtime SLA не заявлен.

### Unperformed gates / unchanged product state

- RU/NL deployment, restricted API live security tests, production certificate
  issuance, CRL/directory sync, provider join/READY: **NOT RUN / NOT DEPLOYED**.
  No client fixture fabricated, no production room created, no OAuth acquired.
- Phone deliberately untouched: user permits physical work **only after healthy
  infrastructure**. Last-observed existing Device Identity PRESENT and normal
  PRESENT_VALID; restricted provisioning/BOOT-1 ABSENT (prior field52 evidence),
  not a fresh inspection. Effective production readiness expiry: **N/A**.
- READY process restart, local restricted rehearsal, Chrome2 sites, Family DNS,
  concurrency, leak/fail-closed acceptance: **NOT RUN in this attempt**.
- Final FIELD APK: **not produced**. Existing private field52/code52 readiness-only
  and public beta51/code51 untouched; Linux0.2.11/Windows0.2.15 unchanged. Public
  artifacts/catalogs не менялись и повторно не верифицировались.
- No uploads, production filesystem/config writes, migration, generated credentials,
  service restart, ingress reload, phone install/clear/uninstall, public release.
  No regression attributable to deployment; only baseline health snapshot taken.
- Runtime tests не повторялись: runtime source unchanged. Documentation guards
  PASS для этого docs-only update:409 files/2464 links/0 errors,
  source guard1552 index entries/0 blocked, working/staged diff checks PASS.
  Previous95/JVM193/native PASS
  ниже относится только к implementation checkpoint, не live deployment.

Production current state: **pre-existing services, unchanged; PROV-1 not deployed**.
Commits данного attempt — только local documentation evidence, hash в handoff.
Push: **no**. Krasnodar FIELD-1 started: **no**. STOP per missing-material rule.

---

## Historical implementation result after clarification — 01.10.2026

**5N-PROV-1 = IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED.**
Это local implementation gate, **не PASS** по physical production criteria.
Продолжение начато с clean HEAD `a88b104672e53e2393e16cd45b07e9fa0c2c4e00`.
Original requested local HEAD `3d9fd7ca3d020618ffb7c8f95068094450483ed4` и
`9c82152` сохранены; `a88b104` — docs-only BLOCKED audit, сохранён ниже как история.
Public origin/main по исходному evidence — `26447902137735ac7633f92ba6673395bae078fa`;
production deployed HEAD в этом continuation не проверялся и не менялся.

Runtime implementation commit: `bb71a3f6977c719c06c77bd2d0a98686c3a70102`.
Отдельный documentation commit завершает gate; final HEAD указан в handoff после
commit (не self-referential hash внутри собственного документа). Runtime source
guard:1551 staged index entries/0 blocked files. Final documentation/source guard
receipt:409 docs/2459 links/0 errors,1552 index entries/0 blocked files,
`git diff --check`/`git diff --cached --check` PASS. Это bounded guard, не полный
security audit.

User clarification разрешило bootstrap seed `seeds[].join_url`, сохранило BOOT-1
v1, запретило prewarm dedicated descriptors и лишнюю standalone directory
signature. Initial delivery использует activated Friends identity proof/HTTPS,
а не уже существующий restricted mTLS profile. Directory TTL не расширен.

## Exact gap and implemented path

Original actual Friends `/friends/*` выдавал normal AWG/WG/TCP configuration, но
не имел trusted Family certificate/BootstrapDirectory delivery. ProductStore
`/v2/*` — другая DB/trust integration, disposable Family issuer — не production.
Existing BOOT-1 normal-control refresh требовал уже provisioned Family mTLS,
поэтому не мог bootstrap ordinary activated Friends. Physical evidence до работы:
Device Identity PRESENT, normal PRESENT_VALID, restricted/BOOT-1 ABSENT.

Теперь existing HTTPS handler имеет два POST: `/friends/restricted-readiness/challenge`
и `/friends/restricted-readiness`. Existing transport proof, stored restricted
purpose/Family/revision nonce, exact Device Identity/WG binding, live device/invite/
grant, owner admission policy, expiry/revision и signed CRL проверяются до выдачи.
Nonce одноразовый/100s, outstanding≤8, request8KiB, response64KiB, concurrency4.
Replay/expired/revision-mismatched/revoked devices не получают usable certificate.
Temporary overload/config/seed/CRL failure →503; не tombstone. Valid proof выдаёт
public-only certificate, issuer delegation, signed CRL, metadata и directory v1.
Повторный legitimate refresh повторно использует ещё достаточно свежий certificate,
но не reusable challenge. Grants additive в existing access.db; eligible existing
activation автоматически mapped без re-enrollment/operator action на телефоне.
Perpetual Friends activation остаётся perpetual grant, не выдуманный subscription;
finite grant expiry/revision/revocation поддерживаются отдельно.

### Trust and private-key decision

Online Family CA получает **domain-separated delegation от existing offline control
root**, pinned в `control-anchor.pub`. Это доказательно необходимый bridge между
normal Friends trust и ранее isolated Family issuer, не second independently
trusted root. Server-only delegated private issuer не root. Offline signer
`scripts/sign_restricted_issuer.py` отклоняет другой root. Настоящий root не читался,
подпись production manifest/генерация production secrets здесь не выполнялись.

Reuse accepted 5N.3 certificate URI/Family/role/revision и TLS1.3/ALPN
`family-connect-5n3-test-v1` без incompatible production format. Certificate public
key — **existing Device Identity Ed25519**, не новый client key. Private identity
остаётся в existing encrypted Friends identity vault. Native собирает PKCS8 и
accepted `familysession.Credentials` лишь в памяти; sensitive temporary arrays/JNI
copy wiped, private profile на диске не создаётся. Managed TLS copies подчиняются
existing runtime lifecycle, secure heap erasure всего TLS runtime не заявляется.
Existing control root и gateway private identity не переносятся на Android/API.

### BOOT-1, cache and readiness

`SeedManager` export callback вызывается **только после gateway READY**; bounded
atomic directory export переносится server-only sync NL→RU. Directory неизменён:
v1, family/times/seeds, required authenticated bootstrap `join_url`,≤8KiB/4 seeds/
1h. **Directory не имеет standalone signature**: transport authentication — existing
Friends HTTPS; subsequent restricted carrier — accepted Family mTLS. Signed CA
delegation и CRL — отдельные trust artifacts, не подпись directory.
Dedicated room creation остаётся lazy Room Broker после restricted recovery/Family
auth, unused descriptor60s/session default10min, без persistence/prewarm.

Android `RestrictedVault`: один AES-GCM/Keystore/AtomicFile в noBackupFilesDir,
public response + tombstone + persisted cooldown/floors, separate from unchanged
identity/normal provisioning vaults. Candidate native-validated целиком перед
atomic commit; malformed/expired/wrong-binding/stale/failed refresh не заменяет
valid старое состояние. Issued time, device revision, CRL, delegation sequence и
directory issuance floors переживают expiry/restart; conflicting equal-generation
directory rejected. Authorization rejection persistently disables usability;
old response не может resurrect denied state. Diagnostics — redacted status only.

Activation/normal profile acquisition/foreground resume и60s foreground maintenance
вызывают **local check**, не periodic network polling. Missing/invalid/≤300s material:
one worker,30s deadline, persisted300s attempt cooldown. No background alarms,
no CONNECT refresh wait with usable cache. Orchestrator actual `.friends` получает
validated production bundle через `beginReady`/`OpenProvisioned`, затем тот же
accepted bootstrap→Family→broker→dedicated full-device path. Diagnostic file path
не используется для production Friends.

### Security window is deliberately short

Directory≤1h не изменён. Deployment seed lifetime55min; CRL publisher15min, so
effective readiness≤15min, а не гарантированный час. Device certificate и response
также ограничены текущим CRL/grant/delegation/directory. Server sync every30s,
timeout15s: обычная revocation propagation около30–45s, при sync failure только до
expiry предыдущего signed CRL (≤15min), не instant offline revoke. Existing active
sessions подчиняются accepted expiry. Dead/rotating single seed может быть
недоступен раньше expiry cached directory. Prewarm непосредственно перед тестом;
hours-after-last-contact readiness **не решена**, это отдельный post-FIELD review
compromise exposure, seed rotation и revocation policy.

## Local verification and limits

- Python **95 passed**, включая opt-in real backend→Go compatibility: existing
  RNS identity proof → production response/certificate → native `DeliveryMaterial`
  → accepted Family Configuration + BOOT-1 parser. Device revision2/global peer
  floor1 проверены раздельно. Ephemeral unit-only keys в памяти, no live credentials.
- Server tests: active issuance/public binding, owner eligibility auto-mapping,
  revoked device/invite/grant/certificate, expired/wrong Family/revision/device,
  challenge replay/purpose/expiry, request/response/trust bounds, overload503,
  malformed seed, no client OAuth/private key/dedicated descriptor, idempotence,
  monotonic CRL and forced sync preserving existing gateway key, trailing PEM
  secret rejection, actual HTTP handler dispatch without network deployment.
- Go `test -race` wholedevice/bootstrap/familysession/roombroker and `go vet`
  same packages + cmd/bootstrap-broker **PASS**. Native rejects invalid trust,
  malformed/stale/expired/device/revision/CRL/directory/nonce/bounds; diagnostic
  string redacted; seed publish not before READY. Host broker build PASS.
- Friends JVM **193 passed**,0 failures/errors/skips; five new cache tests cover
  missing/import, simulated restart/expiry/cooldown, atomic storage contract/fault,
  failed refresh preservation, replay floors, denial/idempotence and redaction.
  These use storage/validator doubles; real Keystore/fs crash/process restart and
  Android-loaded JNI are **not** claimed tested by JVM. Native crypto separately
  tested above; physical combined validation remains pending authorization.
- Friends lint **0 errors / 37 existing warnings**. No unrelated lint fixes.
- Fresh arm64 restricted JNI compile/link **PASS**, Go1.26.0, NDK27.2.12479018,
  Xray `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, gVisor
  `v0.0.0-20260122175437-89a5d21be8f0`, patch SHA
  `2d0a556f73cdd7fb9f0d152edf564b126ba00cfdd526bb7c3325f5051b02339b`.
  Binary SHA `403a4625d3a1f8c57c5ba860400f060a256ef0ff10655681eb6bf02e98f4dd15`,
  ignored output `state-client-build/prov1-native-checked/`. Builder still labels
  this smoke manifest `diagnostic_only:true`; **not a signed/installed FIELD APK**.
  Host broker SHA `c2839cd21f2dd2f7171ea8c8d6596f415a16fe5b7fb84b22bb5715b609c47396`.

Reproducible targeted checks (use locked venv/toolchain; local paths are evidence):

```sh
FC_TEST_GO=/tmp/fc-boot1-tools/go/bin/go /tmp/fc-boot1-venv/bin/python -m pytest -q \
  tests/test_friends_restricted.py tests/test_friends_access.py \
  tests/test_restricted_android_contract.py tests/test_bootstrap_acceptance.py \
  tests/test_orchestrator_android_contract.py tests/test_orchestrator_native_provenance.py \
  tests/test_orchestrator_restricted_acceptance.py tests/test_restricted_acceptance.py
```

Cross-language test requires `FC_TEST_GO` explicitly; otherwise one skip, not the
95-pass acceptance above. Use `TMPDIR=state-client-build/prov1-tmp` as an **absolute**
path with this host's constrained /tmp; GOCACHE/GOPATH under existing locked tools.
Initial JNI attempts failed from /tmp user quota; moving scratch inside repo exposed
enclosing `.git` discovery causing extracted Xray patch not to apply. Builder now
sets `GIT_CEILING_DIRECTORIES` for extracted workspace. Fresh scratch build passed;
initial failures are not erased or presented as accepted artifacts.
Final logs: `/tmp/fc-prov1-python-final.log`, `/tmp/fc-prov1-jvm-accepted.log`,
`/tmp/fc-prov1-native-checked.log`. Go race/vet results recorded in task tool receipt.

## Deployment boundary and remaining physical gate

Deployment required: **yes**. Production deployment performed: **no**.
Exact files/units/hosts/migration/secrets/rollout/rollback in
[controlled deployment runbook](../../deploy/friends/restricted/README.md):

- RU `185.251.89.19:/opt/apps/family_connect`: existing Friends access API/venv,
  `family-connect-friends-access.service` drop-in, existing product HTTPS ingress
  new locations, private delegated issuer/config, new restricted-sync service/timer.
- NL `186.246.45.246:/opt/apps/family_connect`: new dedicated account and
  `family-connect-restricted-bootstrap.service`, fresh broker, private gateway
  profile, forced-command signed-CRL/READY-directory sync, loopback18444 only.
- Same access.db additive tables/online backup; preserve existing activation and
  revocations. `FC_FRIENDS_RESTRICTED_DIR`, offline-signed public issuer delegation,
  delegated server issuer key, existing gateway identity/certificate, owner-only
  admission, pinned dedicated sync key/known_hosts, server-only
  `YANDEX_TELEMOST_OAUTH_TOKEN`. No actual values supplied/generated here.
- Expected short API restart (seconds, not measured), ingress reload, no planned
  AWG/TCP downtime/restart. Verify actual service layout/dependencies before rollout.
- Rollback disable new API/drop-in/sync/seed, restore saved API/ingress artifacts;
  preserve DB tables/revocation/replay floors and private identities. Never roll an
  old full DB over new revocations; Android forward corrective update only.

No physical READY/restart or local restricted rehearsal run in this continuation.
Browser/DNS/fail-closed prior accepted isolated report is **not** new production
cache acceptance. Physical last-observed Friends state still BLOCKED, field52
readiness-only/code52 installed previously; public beta51/code51, Linux0.2.11,
Windows0.2.15 unchanged. No new APK, version bump, signing or public artifact.
After separate authorization: controlled owner canary → private same-signature
update in place → normal prewarm READY → process restart READY → local restricted
rehearsal with actual identity/cache/browser/DNS/fail-closed → only then final
shareable FIELD APK. No uninstall/pm clear/diagnostic identity/traffic forwarding.

Push: **no**. Krasnodar FIELD-1 started: **no**. Stop at deployment boundary.

---

## Historical pre-implementation audit — preserved from a88b104

Следующие разделы описывают состояние **до clarification/runtime implementation**;
их BLOCKED/no-tests/no-build утверждения не являются текущим статусом.

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
