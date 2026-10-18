# TELEMOST-ADMISSION-OWNERSHIP-1 — bounded PARTIAL

10.10.2026. Историческая причина **UNKNOWN**; новая точная ownership-цепочка
получена, нарушение lifecycle не доказано. Это **не исправление и не закрытие
TELEMOST-STABILITY-1**. Отсутствие симптома после renewal/deployment не доказывает fix.

Evidence bundle `B` = `state-client-build/field65-export16/telemost-admission-ownership-1/`.
Машиночитаемый результат: `B/RESULT.json`. Исследовательский source: `B/source/`,
parent `6f3772942f3f3e45aba9a309233ebe8b8a31bf14`; новых commits/branches нет.
Основной dirty checkout не использован как замена research81 source.

## AUTHENTICATED_EXCHANGE_CORRELATION

Историческая попытка20:03:02–20:05:04UTC привязана к NL только по окну времени.
Старые `bootstrap_family_auth`/`bootstrap_exchange_rejected` не содержат exchange/
setup ID. ACTIVE с session_tag3745dceb…e3d7 не содержит requester↔holder binding.
RU provisioning challenge/fetch IDs — **не** ID последующего NL authenticated
bootstrap exchange. Ни соседняя ACTIVE, ни текущий holder не назначены владельцем
исторического ограничения. Широких/повторных journal-запросов не было.

Источники: `telemost-stability-1-current/RESULT.json`,
`telemost-stability-1-current/receipts/fresh-gateway-events.json` (все6 records),
`telemost-stability-1-current/receipts/fresh-refresh.json`, `B/preservation/inputs.sha256`;
прежний код `bootstrap.OpenServer`/`exchange`.

Новая единственная диагностическая попытка:
- client connection `e70a58e0-2228-4942-9ae5-d47c61b57ecc`, native attempt1;
- authenticated exchange `f3a07d13a765dda8da6aafd3ca57a5d8287990e701326b28df64c7d4e44cd0e7`;
- holder generation = существующий session_tag `817217f0015bb9f557fd17d24deb55697024190f76b795d5341e3958682874d0`;
- **тот же tag** в Android `restricted_session.session_tag` и server grant/lifecycle/release;
- native directory fingerprint `648fffa7fe7e376616d24ed3ed525284c39c72756ddc19ae718ba9337e632534` совпал с текущей RU/NL publication.

Это точное равенство, не соседство timestamps. Android JSON-render hash не подменяет
native fingerprint. Источники: `B/private/diagnostic/connected-ring.json` (приватный,
без публикации Support ID/полного snapshot), `B/receipts/diagnostic-result.json`,
`B/receipts/ownership-after-cleanup.json`, safe-проекция `B/RESULT.json`.

## ADMISSION_HOLDER_IDENTITY_MATCH

Исторический requester↔holder: **UNKNOWN**. Новый grant: **same_identity=true**,
реальный holder — собственный setup этого exchange. Предшествующего блокирующего
holder **в новом эпизоде не было**: authenticated→grant за2ms, ни busy, ни wait.
True при grant не подменяет отсутствующее сравнение с историческим incumbent.

Локальный тест создаёт две ACTIVE разных identities; чужая создана позднее.
Wait capture указывает на конкретный старший same-identity setup, а не ближайшую
ACTIVE. Identity/key bytes в capture отсутствуют. Источники: ownership seq1–2;
`B/source/carrier/roombroker/ownership_test.go`,
`TestOwnershipActualHolderNotNearestActive`; `B/receipts/local-final.log`.

## HOLDER_STATE_AND_OWNERSHIP

Ограничения раздельны:

1. **Seed admission**: одна routing lease `ServeCarrier.current`, FCB1 OPEN/ACCEPT,
   случайные client/server nonces; identity ещё не установлена. Client admission30s
   внутри120s exchange. Release по `finished` exchange worker, не dedicated session.
2. Family TLS authentication предшествует challenge.
3. **Broker admission**: `Broker.setups`, global outstanding32, один setup на полную
   `(Family, Device, PublicKey)`. `ChallengeAfterCleanup` ждёт `pending.done` только
   для ACTIVE или started terminal. Неактивный pending duplicate возвращает
   `device_busy` сразу; global limit — отдельный отказ. Authorization/identity
   перепроверяются; ожидание ограничено caller context, без eviction.
4. `Challenge` создаёт setup ID, monitor и lifetime10min. `Create` принимает worker
   ownership; на ошибке вызывает finish. При успешной передаче worker `Gateway.Run`
   владеет cleanup: terminate→Gateway.Close→finish. Monitor удаляет только **не
   started** setup. Terminal state не равно завершению Close/release.
5. HELLO только после grant. Exchange до handoff отменяет только собственный setup;
   после handoff cleanup принадлежит monitor/lifetime/authorization и gateway worker.

Источники: `B/source/carrier/bootstrap/carrier.go` (`connectLease`, `ServeCarrier`),
`bootstrap/protocol.go`, `roombroker/broker.go` (`Challenge`, `ChallengeAfterCleanup`,
`monitor`, `Create`, `finish`), `roombroker/README.md`. Limits/TTL не увеличены.

**A:** ACTIVE легитимно удерживает slot; текущий контракт ждёт normal cleanup до
caller deadline. **B:** локально проверены provider error/timeout, unstarted cancel,
unused/dedicated failures, Claim/activate и передача worker ownership. **C:** local
Close barrier показывает terminal+present до настоящего Close и release после.
В новом live release подтверждён. Completed-but-unreleased owner не обнаружен;
исторический C не доказан.

В интегрированном JNI chat может заимствовать **уже готовую** matching VPN session
(`borrowed`), и chat release не закрывает borrowed carrier. Обратного заимствования
chat→VPN/согласования одновременно создаваемых owners в `begin()` нет. Это граница
контракта/потенциального конфликта, **не доказанный виновник этого live-отказа**.
В новом эпизоде ChatDeliveryService работал, route после READY — **DIRECT**;
shared Telemost chat/VPN runtime здесь не exercised. Старый stream-isolation fixture
не выдаётся за интеграционную приёмку этого случая.

Источники: `B/source/pilot/android-restricted/native/chat.go` (`fcChatAcquire`,
`fcChatRelease`), `native/main.go` (`begin`), Android `ChatCarrier.java`;
неизменные native hashes в `telemost-stability-1-refresh/research-manifest.json`;
`chat_route_observation` в `B/receipts/diagnostic-result.json`.

## WAIT_AND_RELEASE_TIMELINE

| UTC10.10 | Событие | Точный источник |
| --- | --- | --- |
| 21:43:55.790 | один UI CONNECT, Telemost/NL | diagnostic-result.events/manual_connect_intent |
| 21:43:57.790 | native attempt1 started | connected-ring.restricted_startup |
| 21:44:07.039 | authenticated | ownership seq1 |
| 21:44:07.041 | grant; AUTHORIZED/present/same_identity=true | seq2 |
| 21:44:07.042 | HELLO реально отправлен | seq3 |
| 21:44:07.767 | клиент принял HELLO, DESCRIPTOR STARTED | connected-ring.restricted_session.lifecycle.trace |
| 21:44:08.131–10.168 | CREATING→CREATED→GATEWAY_JOINING→READY→CLIENT_ISSUED, claim | seq4–9 |
| 21:44:10.169–14.125 | descriptor→handoff→exchange_end ok | seq10–12 |
| 21:44:20.522 | тот же holder ACTIVE | seq13 |
| 21:44:20.649/20.855 | native ESTABLISHED / UI connected | client trace / diagnostic events |
| 21:46:20.941–21.419 | deliberate cleanup; VPN off | before-final-cleanup/final-cleanup |
| 21:46:31.177 | Run returns→FAILED→Close begin/end→release, present=false | seq14–18 |

Ownership seq: `B/receipts/ownership-after-cleanup.json`; client:
`B/private/diagnostic/connected-ring.json`, `B/receipts/diagnostic-result.json`.
Lease deadline21:54:07.041 не наступила. Generic `gateway_session_failed` после
deliberate cleanup не приписывается старому admission failure/DATA exhaustion.

## ROOT_CAUSE — UNKNOWN

Для20:03 отсутствует связь failed exchange→generation/identity/state→release.
Новый наблюдаемый процесс не восстанавливает прошлое. Контенция не воспроизвелась
в единственном эпизоде; leak, stale callback, двойное создание или неверный cleanup
**не доказаны**. Независимое поведенческое исправление тоже не заявлено. Ещё один
сбор общих логов и новый неизменённый CONNECT не запланированы.

## LOCAL_BEFORE_AFTER

- Before на неизменённом6f377294: existing active-wait test PASS, включая deadline,
  authorization change/cancellation; прежний trace не даёт holder attribution.
- After: поведение то же, но exact holder/generation/transitions/wait_end/release
  наблюдаемы. Чужая поздняя ACTIVE не подставляется. Cancel waiter не удаляет owner;
  late/double Cancel старого ID не удаляет новую generation; ошибка до acquisition
  не освобождает чужой ресурс. No unconditional finally release.
- Race×3:52 top-level PASS×3;7 fixture tests SKIP×3 в nonfixture прогоне.
- Затем disposable ProductStore fixtures: roombroker/wholedevice/command PASS;
  authenticated busy/binding/silent-handshake cleanup PASS. **Общий bootstrap suite
  FAIL**: `TestProductIdentityOverBootstrapCarrier`, diagnostic assertion
  `auth_test.go:86`,6 negative subcases. Тот же FAIL воспроизведён на неизменённом
  baseline теми же fixtures; не исправлялся и не объявлен новым дефектом.
- Pinned control/identity Python environment; publication native positive/negative
  validation PASS. Initial `/tmp` quota failures и отсутствие RNS в system Python
  сохранены; принят запуск с project-SSD temp и pinned venv.

Источники: `B/receipts/local-final.log`, `local-authenticated.log`,
`baseline-authenticated.log`, `credential-publication.json`,
`python-dependencies-escalated.log`. Полный suite PASS не заявляется.

## CORRECTION — observability only

Server-only patch: ephemeral seed nonce→hashed exchange ID, setup→существующий
session tag. Exact map-holder snapshot под broker mutex; **никаких disk/SSH/network
ожиданий под ним**. Только metadata, без keys/user IDs/room URLs/SDP/credentials.
Никакой догадочной role. До512 events/15min, без HTTP debug endpoint. Snapshot
копируется до записи. Existing/unavailable capture не обрушает gateway; повторный
process не перезаписывает spent evidence. Сбор заканчивается автоматически.

Patch SHA256 `7b78c8591222d7cd8402976013f0cebe244b369529fc569aefb9870d8414a948`.
Built **и loaded/next verified** server SHA256
`c101065a92e3a10e5c018b09c982e56c0a0d954965bd914b15a00fa091cc54c7`;
invocation `d1e195e90b1744768e3768d9ccddc4c5`, PID57722. Capture header подтверждает
schema/тот же PID/invocation/limit/expiry. APK не пересобирался/переустанавливался:
research81-refresh/code81, SHA256
`06513be88ac924e6412cf65865361b6c4369da7f7e4c80e90c3d91eab1fe543f`.

До deployment сохранены старые invocation7ca1ffc5…, binary5be7b309…, unit/directory
и incident evidence. Authority9 истекла к **новому** preflight, но была валидной
при историческом20:03 отказе. Разрешённый AKI-correct **same-key renewal9→10**:
прежние issuer/grants24h и gateway/CRL4h, offline root остался локально. Admissions,
revocations, bindings/revision floors сохранены, CRL монотонна. Один необходимый
issuer API reload и один NL observation deployment, AWG/TCP без restart. Новая
directory после invocation синхронизирована. Strict served chain/hostname/expected
leaf и RU/NL agreement PASS; текущий headroom14220s, **не старые225s**.
Старое in-memory ownership при deployment утрачено; это не retrospective proof/fix.

Источники: `B/observation-manifest.json`, `ownership-observation.patch`,
`receipts/runtime-before.json`, `authority-before.json`, `credential-publication.json`,
`issuer-loaded.json`, `observation-loaded.json`, `directory-current.json`,
`preflight-nl.json`, `preflight-ru.json`, `timer-restored.json`.

## HELLO / DEDICATED_READY / TRAFFIC

**PASS для нового диагностического участка**, не post-fix control acceptance:
grant→реальный HELLO send/receive→dedicated READY, DNS,4 последовательных полных
HTTPS206 Range responses по65536bytes с hostname/TLS/body SHA256, всего262144bytes.
Первый ответ29495ms после CONNECT. Не загрузка полного APK, не speedtest/FIELD.
ChatDeliveryService не отключали для воспроизведения: instrumentation меняет target
process, обычный service запущен до CONNECT и running на ключевых checkpoints.
`background_setting` был false ещё до CONNECT; пользовательскую настройку не меняли.
Parallel series не выполнялась: доказанного behavioral fix и post-fix control нет;
полная post-fix матрица не засчитана. Диагностический эпизод1, контрольных0,
повторных CONNECT0. Источники: `B/receipts/diagnostic-result.json`, `client-capture.log`,
неизменный `telemost-stability-1-current/testsrc/com/familyconnect/app/LateOwnerEpisode.java`.

## LATER_SESSION_STABILITY

120s после READY: client loss0, failed requests0, recovery0. Затем deliberate cleanup;
server FAILED/gateway_session_failed после него, затем точный release. Это не
доказательство причины старых carrier closures/DATA exhaustion/долгосрочной
стабильности. Восьмиминутная/post-fix приёмка не заявлена. First-failure capture
не сработал, поскольку неожиданного отказа в эпизоде не было. Источники: final event
в `diagnostic-result.json`, server seq14–18, `RESULT.json`.

## PRESERVATION_AND_CLEANUP

Owner: прежние package/code81/APK/UID, без main uninstall/data clear/re-enrollment/
Store edits/history deletion. Signed helper удалён; один ordinary launcher restore,
не новый CONNECT. **VPN OFF; приложение ON; ChatDeliveryService ON.** AWG не
переключался; настройки/службы не менялись. Новый AWG traffic smoke не выполнялся:
E2E не выводится из active service. Побайтовая неизменность всех данных/настроек
не заявляется. Последний device readback21:56:50.774UTC подтверждает конечное
состояние. Источники: `B/receipts/owner-before.json`, `owner-closeout.json`,
`helper-removed.json`, `background-final.json`, final server security receipts.

UI rollback draft не применён: `telemost-stability-1-current/preservation/ui-rollback-draft.patch`,
SHA256 `9733ec090f66d6af1553676c009f3d0a34f23d88b8e1c93d01db48603ccb61d1`.
Startup77/recovery79/diagnostics80/refresh81, UI, Codec2, Reliable/RTO/pacing,
предыдущие artifacts/evidence сохранены. Публикации/рассылки APK/Краснодарского FIELD нет.

Final collector/server closeout: `B/receipts/ownership-final.json`, `security-final.json`.
**PASS21:57:14UTC**: stopped footer после15min,18 events,limited=false; неизменный
invocation, одинаковые loaded/next arguments+binary, ordinary services/security;
issuer10, CRL19827, sync timer active/waiting, cleanup restarts0. Spent protected
capture сохраняется как evidence/single-use marker против нового сбора при restart.
Удалены только созданные executable helpers/test canary, не identities/publisher
records/rollback/history. Локальные synthetic fixtures и собственный temporary
Go cache удалены: `B/receipts/local-cleanup.json`. Source/patch/evidence сохранены.

Rollback: прежний binary5be7b309…c63ae и unit сохранены в защищённом
`/opt/apps/family_connect/restricted-materials-stage-20261001/admission-ownership-20261010/`.
Новый binary: `friends-restricted/bin/bootstrap-broker-ownership-20261010`; override
`99-z-admission-ownership.conf`. При отдельно требуемом rollback убрать только этот
override/вернуть прежний binary, **сохранив renewed authority/leaf/CRL/floors**.
Не восстанавливать expired profiles/старую DB. Restart требует fresh directory/sync/
served-chain acceptance. Сейчас rollback/cleanup restart не выполняется.

Remaining: историческая exchange→holder/state/release граница не сохранена;
shared chat-first/VPN conflict не испытан в DIRECT-сценарии; полный authenticated
suite имеет отдельный baseline FAIL. Bounded pass не назначает виновника и не
планирует blind replay. Public client/download/invitation versions не менялись;
их новый rollout/перепроверка не заявляются.
