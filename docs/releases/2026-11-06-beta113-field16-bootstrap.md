# beta113 / API28 — отдельный полевой отказ начального подключения

<a id="dual-direct-path-failure"></a>
## Продолжение148e212: оба прямых служебных пути недоступны

**COLD_BOOTSTRAP_GAP_REPRODUCED / PRODUCT_UNCHANGED.** В поставленной beta113 нет
реализованного пути получения проверенных стартовых материалов для уже активированного
устройства **без пригодного readiness-кеша и без уже работающего VPN**, если одновременно недоступны основной
HTTPS `185.251.89.19:8443` и прямой RNS TCP `186.246.45.246:4242`. Это отсутствие
перехода до первого MESH, а не только неточная классификация ошибки. Локальный тест
задаёт оба отказа; он **не устанавливает**, что именно оператор блокирует эти адреса
на данном телефоне. Прежние source/JSON выводы148e212 ниже сохраняются без пересмотра.

### Зависимости первого подключения

Все ссылки на исходники в этом разделе относятся к поставленному
`d2882cde4c50b15085b925007c04c48f4de61bf0`, не к текущему main. Пути Java указаны
от `clients/android/app/src/main/java/com/familyconnect/app/`.

| Этап | Фактический вход / источник | Что есть без readiness-кеша |
|---|---|---|
| Identity / активация | FriendsAccessAndroid.identity; FriendsActivity.register; `/friends/challenge` → proof → `/friends/activate`; при приглашении сначала `/friends/referral/claim` | У активированного клиента сохранён локальный ключ. Новый ключ можно создать офлайн, но это не выдаёт серверную identity/активацию/допуск |
| Trust / выбор сервера | APK ControlTrust anchor, pin/config RNS; статический выбор gateway и отдельно сохранённые обычные профили | Публичный якорь, адреса, выбор узла и возможные AWG/TCP-профили не содержат замену действующему Family/readiness bundle |
| Получение readiness | FriendsAccessAndroid:94; actual ReadinessBootstrapRoute + FriendsReadinessProtocol: HTTPS challenge/fetch, при допустимом сетевом отказе challenge — прямой RNS | Третьей release-ветки получения bundle нет. Chat fallback в post:50 разрешён только для chat/challenge и chat/register, не активации/readiness |
| Проверка / кеш | FriendsRestricted.cache:31 → NativeRestricted.validationCode; RestrictedCache/RestrictedVault | Нужны выданные issuer delegation, leaf с device/Family/node binding, действующая CRL и directory/seed join URLs, сроки и монотонные ограничения. Ключ и anchor сами их не создают |
| Начало MESH | RestrictedTunnelEngine:80 ждёт ready; только затем beginReady:84 → native DeliveryMaterial → wholedevice.OpenProvisioned | Без пригодного bundle до Telemost bootstrap не доходит; descriptor ещё не запрашивается |
| Seed / descriptor / session | wholedevice/session.go:323,340 → bootstrap.Recover → seed Family TLS → broker descriptor → dedicated room/Family TLS/mux | Уже требуются Family credentials и usable directory. `/v1/bootstrap/directory` в bootstrap/seed.go:97 также проверяет существующую Family TLS identity, а не выдаёт её с нуля |

Production native `pilot/android-restricted/native/main.go:101` вызывает
`wholedevice.DeliveryMaterial(..., time.Now())` перед созданием сеанса.
`carrier/wholedevice/provisioning.go:119,205` проверяет issuer/leaf/CRL, identity/root/node
bindings и bounds; private leaf material выводится в памяти из существующей identity.
Directory принимается в проверенном provisioning-контексте, не из произвольного
неподписанного файла. Видимый список узлов не означает наличия этих материалов.

Граница вывода: уже существующая ветвь `HTTPS_VPN` при собственном `status=on`,
`healthStatus=ok` может доставлять readiness через ранее работающий VPN. Это не
независимый холодный вход: сначала нужно получить исправный транспорт. В тесте
status/health=off, как при отсутствии такого соединения; blocking guard не равен
healthy VPN. Возможную доступность AWG/TCP отдельно в конкретной сети не отрицаем,
но в заявленных жёстких белых списках она не доказана и не заменяет требуемый cold MESH.
Само создание VPN-интерфейса или видимый сервер не удовлетворяет этому условию.

**Service-only ChatCarrier не разрывает зависимость.** Его настоящий `acquire():21`
загружает identity/anchor и `RestrictedCache`; при `cache.usable()==null` прекращает
вызов **до** native chatAcquire. Native restrictedchat также требует DeliveryMaterial
перед OpenProvisioned. Наличие классов carrier/chat не является альтернативным входом
для отсутствующего кеша. Тестовый provisioning gate обычной поставки выключен.

### Короткое воспроизведение, без телефона и реальной сети

Новый runner находится в существующем `tests/fixtures/mobile_bootstrap/`:

```sh
python3 tests/fixtures/mobile_bootstrap/check_blocked_paths.py \
  --source-root state-client-build/beta113-field16/source \
  --tools /mnt/data/PycharmProjects/family_connect/state-client-build/field65-export16/diag-source-freeze-1/resume-tools \
  --output state-client-build/beta113-field16/blocked-paths-2
```

Это уже выполненная команда; при воспроизведении требуется **новое** output-имя.
Runner не перезаписывает evidence. Компилируются неизменённые actual113
FriendsAccessAndroid, ChatCarrier, route/protocol/cache/bootstrap и release-disabled
gate; SHA выбранных source сверяются с Git d2882cd. Заменены Android/platform и I/O
границы: HTTPS write выдаёт SocketTimeoutException, RNS open — typed Unavailable.
Identity синтетическая, storage в памяти; подключения к серверу не выполняются.
Это JVM source-flow, **не Android Network/Keystore/JNI runtime и не VPN traffic PASS**.

| Случай | Фактический результат |
|---|---|
| Уже активированное устройство без кеша (существующая identity, server eligibility — предпосылка) | Один HTTPS readiness challenge и один RNS open; FETCH_FAILED, availabilityFailure=true, response=null; свежий Connect получает temporary BOOTSTRAP_UNAVAILABLE до native MESH |
| Уже валидированный, ещё действующий кеш | Те же два отказа; exact cached bytes допускаются для нового явного Connect, status=CACHED_VALID_REFRESH_UNAVAILABLE. Это **выбор материалов**, не проверенное здесь Telemost-подключение. Внутренний restoring=true при таком refresh отказе блокируется |
| Истёкший кеш | После двух отказов response=null; не превращается в допустимый кеш |
| Первая activate / register без invitation token | Создан только локальный ключ; HTTPS `/friends/challenge` не проходит, `/friends/activate` не вызван; RNS не вызывается |
| Register с синтетическим invitation token | Остановка уже на HTTPS `/friends/referral/claim`; активации/ready/RNS нет |
| Попытка service-only chat без readiness | Actual ChatCarrier.openMailbox возвращает -1; native chatAcquire не вызван, другого fetch нет |

**7 JUnit PASS, 0.361s, compiler/run exit0.** Положительный cache-case использует
контролируемое время и seam уже успешного validator; это не подмена production-проверки
и не самостоятельное доказательство криптографической пригодности. Поэтому отдельно
на exact113 выполнены существующие native тесты:
`TestCachedBootstrapCryptoDeadlinesAndRevocation`,
`TestProductionDeliveryToExistingFamilyMaterial`,
`TestProductionDeliveryRejectsBindingTrustExpiryBounds` — **3 PASS, 0.014s, exit0**.
Они используют реальные синтетические подписи, actual ValidateDelivery/DeliveryMaterial,
Family configuration и directory parser, проверяют expiry/revocation/bindings. Это не
wall-clock пересечение срока и не полный carrier suite. Команда с offline Go caches,
GOMAXPROCS=2, `-p 1`, nice10 и timeout приведена в [fixture README](../../tests/fixtures/mobile_bootstrap/README.md#beta113-both-direct-bootstrap-paths-unavailable).
JVM ограничен двумя CPU/128MiB; ни AVD, ни APK, ни длительный soak не запускались.

Локальный корень результатов: `state-client-build/beta113-field16/` в отдельной
рабочей копии. Результаты не складываются с прежними пересекающимися suites.

| Evidence | Результат / SHA256 |
|---|---|
| `blocked-paths-2/receipt.json`, `check-1.log` | PASS7; log `1f83d0cae4a9700dfb9832737482a453032172dc74a49d1db025adb52b362ca4`; receipt содержит команды, exit и source/fixture inventory |
| `blocked-native.log`, `blocked-native.exit` | PASS3/exit0; log `f86d3ccd9911307550d9bfa78ed5e03ad10f5eacd8bee77a68b630e8ba00788a` |
| Первый `blocked-paths-1/check-1.log` | **FAIL сохранён**, `b4e290dc114de7d9058818c7199cfb8f24632b945a5ecc0041dcd387e209e1a9`: ошибочный test URL handler запрещал само создание внутреннего JCE non-HTTPS URL. Исправлен только seam: запрет на открытие сети, не создание URL; продукт/ожидания не менялись |
| Runner `check_blocked_paths.py` | `3855550e4d845948d33432d2ffbf870198dea857dc33f3db57a9e167196df6cc` |
| `blocked_paths/BlockedPathsTest.java` | `73965a090f50f57b088b15b5b489598faaa8482edd299c0c9e582472a88d7093` |

### Минимальный недостающий переход — предложение, не реализация

Не хватает перехода **существующая device identity + публичный trust → проверенный
readiness bundle через доступный carrier, до наличия Family leaf/seed directory**.
Минимальное направление — ограниченный service-only provisioning-вход поверх уже
используемого Telemost packet transport с существующими challenge/device-proof,
readiness handlers, issuer и trust boundaries. Не второй writer/signer/transport и
не выдача доступа только за знание room URL.

У этого входа должен быть **аутентифицированный provisioning rendezvous, не зависящий
от самого readiness-кеша**: его locator/server binding проверяется существующим
trust anchor/pin; locator не является grant. Пока такого входа нет, просто вызвать
ChatCarrier означало бы цикл. Разрешены только ограниченные provisioning RPC;
TCP/DNS/mux-доступ — после обычной проверки bundle, identity/node, CRL/floors и bounds.
На сервере переиспользуются текущие entitlement/admission/proof проверки без ослабления.
Если для rendezvous потребуется новый контракт, его надо явно ограничить и проверить,
а не объявить существующим на основании transport-классов.

**Один следующий шаг реализации:** такой bounded adapter для *уже активированного*
клиента без кеша и его интеграционный тест с двумя отключёнными direct путями,
настоящим signed bundle и неизменённым validator, прежде чем разрешать MESH.
Получение новой identity/первая активация остаётся отдельным неподтверждённым сценарием;
для него понадобился бы тот же service-only доступ к существующим claim/challenge/
activate handlers с прежними правилами, не автоматическое расширение этого задания.
Здесь adapter не реализован, endpoint/provider не добавлены. Доступность Telemost
в конкретных белых списках телефона не установлена и должна проверяться в поле.
Timeout/retry, истёкший кеш, неподписанный каталог и сторонний VPN не являются решением.

### Минимальная правка сохранения причины — отдельно от доступности

Сохранённое исходное FETCH_FAILED, последующий owner interruption AUTH и cleanup
INTERNAL — **разные события**. Exact113 `ConnectivityOrchestrator:143` теряет `last`
при исключении closeCandidate, вызывая finish(INTERNAL); `:164` аналогично заменяет
переданный reason. Ранее сохранённый control-flow probe воспроизводит эти ветви.

Предлагаемая минимальная правка — не переклассификация и не изменение recovery:
добавить к terminal event/DiagnosticRing ограниченные enum-поля `trigger_reason`,
`cleanup_reason`, `secondary_stage`, сохранив действующий `reason=INTERNAL` как
policy outcome. В первом catch передавать сохранённый `last` как trigger; во втором
захватить входной reason **до** попытки cleanup. Обе ветви записывают classify(cleanup)
в отдельное поле, не текст исключения/ключи/URL. Схема результата для воспроизведённого
случая: `reason=INTERNAL, trigger_reason=AUTH, secondary_stage=CLEANUP`; cleanup enum
берётся только из реально пойманного исключения, не угадывается по экспорту.

Существующие `candidate_failed`/fetch trace остаются самостоятельными, связанными с
своей попыткой; старый fetch не копируется как доказанная причина нового AUTH.
Источник owner-события сохранять UNKNOWN до наблюдения фактического callback;
onRevoke и onDestroy различать лишь там, где они действительно вызваны. Fail-closed,
терминальность и отсутствие нового retry остаются прежними. Gate такой правки:
два cleanup-catch теста плюс неизменённые orchestrator/serializer проверки; **это
описание минимального изменения, не уже установленное исправление**.

### Неопределённость телефона и границы результата

По-прежнему отсутствует признак живого выбранного physical Network в момент ошибки
и раздельный исход TCP connect / TLS handshake / HTTP write. Поэтому недоступность
служебного адреса и ошибка выбора/потери underlay на этом телефоне пока неразличимы.
Локальный dual-block test не выбирает одну из этих гипотез. Сравнительный same-cellular
тест предыдущего отчёта остаётся полевой рекомендацией, а не выполненной проверкой.
Новый диагностический APK не собирался: полезен был бы только для различения этих
конкретных этапов/liveness и фактических owner/cleanup событий, не как предполагаемый
ремонт холодного старта. Raw export, opaque IDs, ключи и приватные receipts в Git нет.
G4/frozen artifacts, production, сертификаты, подписки, admission и другие рабочие
копии не затронуты. Изменены только локальные fixtures/runner и документация.

## Статус и границы входных данных

Следующие разделы сохраняют выводы checkpoint148e212; их прежний NEXT заменён
ограниченным предложением реализации в продолжении выше, не новым глобальным этапом.

**EXPORT_READ / SOURCE_AUDIT_COMPLETE / FIELD_CAUSE_NARROWED_NOT_FIXED.** Это отдельный клиент, не телефон
владельца, не isolated G4 и не проверка исправленного live MESH. Продуктовый код,
классификация ошибок и серверы не изменены. Нового APK, AVD, транспорта или endpoint нет.

Владелец передал точный путь Telegram к `FamilyConnect-diagnostics (16).json`;
файл прочитан: **17640 bytes**, SHA256
`94e2ba954b844b70107f8984837ff8fb4cd96c1c092094bee6f3fee287174682`.
Оба раздела подтверждают beta113/code113/API28, Support ID=null. Ранее найденный
похожий файл **beta65/API31 по-прежнему исключён**. Предыдущий source-only checkpoint
`56c445df5ffcb97056deb9a16fa99e1b1135284b` сохраняет факт тогда отсутствовавшего input;
теперь следующие признаки проверены непосредственно в правильном JSON:

- beta113, API28; оба сохранённых fetch имеют CELLULAR и `cache=MISSING`;
- `CHALLENGE / CONNECT_TLS_WRITE / HTTPS_UNDERLAY / TIMEOUT`, HTTP-ответ не зафиксирован;
- `RNS / RELAY_OPEN / UNAVAILABLE`, `readiness=FETCH_FAILED`, `directory=NOT_USABLE`;
- `restricted_descriptor=NOT_ATTEMPTED`, затем AUTH и INTERNAL без раскрытой причины;
- окна по часам телефона: 2026-11-05 09:31:20–09:34:43 UTC и
  2026-11-06 11:59:26–11:59:37 UTC; Support ID отсутствует.

Часы телефона не сверены. Identity, оператор, регион и выбранный gateway
**не устанавливались и не угадываются**. Принадлежность событий соединениям сверена
локально по opaque IDs, которые в отчёт не включены. Отсутствие
Support ID не заменяется поиском похожего пользователя. Raw export/ключи в Git не попадают.

## Уточнение по фактическому экспорту

### Два snapshot, не одна непрерывная попытка

- `incident`:35 событий5 ноября, последнее состояние FAILED, последний сохранённый
  `vpn_capture_open=true`. Два явных Connect и два retry второго подключения.
- `ring`:4 readiness-события6 ноября, состояние DISCONNECTED, `vpn_capture_open=false`;
  Connect/owner/native events отсутствуют. Это readiness/prewarm-окно, не доказательство
  нового VPN Connect6 ноября. Global network_class=UNKNOWN, но fetch.network_type=CELLULAR:
  readiness logging не вызывает `Diagnostics.network()`, в отличие от orchestrator events.
- В обоих snapshot `restricted_session` и `restricted_startup` пусты, history пуст.
  Это согласуется с отказом до native beginReady; полноценного Family-сеанса не показано.
- Snapshot `vpn_capture_open=true` сам по себе не является свежей проверкой Android VPN
  owner: событие onRevoke/onDestroy в113 не записывает отдельную причину и может оставить
  прежнюю диагностическую метку. Утверждать сохранённый TUN после AUTH по этому полю нельзя.

### Хронология, UTC по телефону

| Время5 ноября | Факт и локализация |
|---|---|
| 09:31:20.807 | MISSING до первого явного Connect |
| 09:31:23.369–23.395 | Первый Connect, VPN_CAPTURE_READY |
| 09:31:31.039 | **Первый записанный отказ FETCH_FAILED**; его отдельный detailed trace уже не сохранён |
| 09:31:41.120–41.231 | BOOTSTRAP_UNAVAILABLE, переход к RESTORING и recovery_wait |
| 09:32:01.257 | AUTH, RESTORING→FAILED, **без нового restoration_attempted**, через20.026s после recovery_wait |
| 09:32:09.888–09:32:10.251 | Явный Disconnect/VPN_RELEASED, затем второй Connect/VPN_CAPTURE_READY |
| 09:32:25.658–35.813 | FETCH_FAILED, BOOTSTRAP_UNAVAILABLE, ожидание recovery |
| 09:33:10.834–09:33:32.369 | Первый retry; сохранённый detailed fetch, затем BOOTSTRAP_UNAVAILABLE и recovery_wait |
| 09:34:37.406–38.453 | Второй retry и попытка restricted candidate |
| 09:34:42.946–42.991 | Candidate AUTH → restoration_failed INTERNAL, промежуток45ms |

В incident сохранён **последний завершённый readiness trace09:33:11.942–09:33:22.194**,
а не trace исходной попытки09:31 и не trace последнего AUTH09:34. Его нельзя ретроспективно
назначить этим двум попыткам. Connection ID у этого trace совпадает с началом/концом
второго подключения; `connection_changed=false` не означает неизменную сеть.

В ring6 ноября: MISSING в11:59:26.560/.639 и FETCH_FAILED в11:59:31.874/36.867.
Сохранён только один подробный trace11:59:26.427–11:59:36.862. Два результата не позволяют
угадать, какие node scopes/prewarm их породили: gateway binding в этом export не указан.

### Сеть в двух сохранённых detailed traces

| Trace | Длительность monotonic / wall | Состояние и route |
|---|---|---|
| 5 ноября09:33 | 10252ms /10252ms | CELLULAR handle H1, HTTPS TIMEOUT → RNS UNAVAILABLE, HTTP status0 |
| 6 ноября11:59 | 10434ms /10435ms | CELLULAR handle H2, HTTPS TIMEOUT → RNS UNAVAILABLE, HTTP status0 |

H1/H2 — только локальные обозначения: **handles различны между днями**, совпадают
в HTTPS/RNS failure records внутри каждой попытки, не нулевые. У обоих trace
cache=MISSING, source=NONE, refresh=FETCH_FAILED, connection_changed=false.
Это исключает объяснение этих двух сохранённых traces одним неизменно закешированным
handle на оба дня, но не исключает потерю выбранной Network внутри попытки.

Две одинаковые записи RNS UNAVAILABLE внутри trace — предусмотренное логирование в
`relayPost` и внешнем `restrictedReadiness` catch, а не свидетельство двух relay opens.
При штатных monotonic clocks полный10.3s trace короче25s ожидания RNS path/link и нового
30s общего бюджета. Callback записывает NONE/0 при отсутствии bindable underlay, чего
здесь нет. По exact113 это существенно сужает RNS отказ до **TCP-connect ветви**; форма
около10s совместима с последовательными5s HTTPS/RNS ожиданиями. Но export не содержит
самого socket errno/индивидуального времени фаз: конкретный timeout/refusal, причина
недоступности адреса и политика оператора **не доказаны**. В частности, это не доказанное
25-секундное ожидание отсутствующего RNS peer и не отсутствие локального Python runtime.

### Происхождение двух поздних категорий

1. AUTH09:32:01 возникает до минимального30s retry backoff и без события новой попытки.
   В штатном flow113 это ветвь `retryIfDue()` при уже установленном `interrupted=AUTH`,
   а не новая HTTP challenge-авторизация. Production caller этого AUTH interruption —
   callback AutomaticVpnOwner от `TcpVpnService.onRevoke()` **или** `onDestroy()`.
   Какая из двух callback-причин сработала и кто её вызвал, JSON не различает. Это
   не доказательство запуска стороннего VPN или конкретного действия пользователя.
2. AUTH09:34:42.946 относится к candidate второго retry. Через45ms записан именно
   `policy_reason=INTERNAL`. По control flow после candidate AUTH до terminal finish
   категория меняется на INTERNAL при исключении `closeCandidate()`/cleanup. Там
   выполняются blocking guard replacement и `candidate.down()`. Exception class и
   точная операция отсутствуют; связку «owner revoke → guard establish null» нельзя
   объявить доказанной. Ранее сохранённый trace09:33 не содержит причины этого AUTH.
3. TRANSPORT_UNAVAILABLE сразу после restoration_attempted в09:33/09:34 не следует
   объявлять отдельным измерением сети: source113 пишет это исходное значение `last`
   в событии fallback, затем через1s пробует candidate. Export не сохраняет имя fallback.

Обе control-flow последовательности воспроизведены синтетически на неизменном113;
это локализует происхождение категорий, но не воспроизводит Android callback/сеть
этого телефона. HTTP401/403, AUTHORIZATION_REJECTED или native Family-auth rejection
в предоставленном JSON **не зафиксированы**. Классификация продукта не менялась.

## Точная версия и способ проверки

| Компонент | Проверенная привязка |
|---|---|
| Рабочая база аудита | `19af689c05b6cfd68c4c2929ae1337dc42ac2ff6`, отдельный managed worktree; исходная рабочая копия с чужими изменениями не изменена |
| Поставленный source113 | `d2882cde4c50b15085b925007c04c48f4de61bf0`, snapshot через `git archive`, не текущий Android source |
| Версия | `com.familyconnect.app.friends`, `0.1.18-beta113`, code113, ARM64, min27/target35 |
| Сохранённый product-signed APK | SHA256 `6078d0610272c5eb1b8008d330f9e646163b90b89df180b4bd56fd8ae4edc094`, проверен локально, не пересобран |
| Встроенный `assets/rns-relay.json` | Побайтово совпадает с d2882cd; SHA256 `9305cd3486e4e7c5a7fc881a292d3824653a0d6d5c4a5559272baa98c275b7bb` |

Источник release provenance: [принятая поставка113](2026-11-04-android113-server-picker.md).
APK непосредственно с исследуемого телефона не считывался: соответствие его установки
этим байтам пока опирается только на сообщённую версию. Среди рассмотренных Java/Python
файлов текущий HEAD отличается от113 добавлением renewal-метода в FriendsRestricted и
расширением native-диагностики DiagnosticRing; эти поздние изменения в тесты113 не включены.

Далее имена Java-файлов относятся к
`clients/android/app/src/main/java/com/familyconnect/app/`, Python — к
`clients/android/app/src/main/python/`; номера строк — **в d2882cd**, не текущем main.
Снимок и локальные receipts сохранены в `state-client-build/beta113-field16/` отдельной
рабочей копии. Никакие G4/frozen sources, контейнеры или артефакты не использовались.

## 1. Первый подтверждённый переход и HTTP/underlay

Первый recorded result — FETCH_FAILED09:31:31. Самая ранняя сохранённая подробная
сетевая цепочка09:33 подтверждает **истёкшее ожидание readiness challenge до записи
HTTP status**. Это ещё не получение readiness, не Family TLS handshake с NL и не
отказ серверной авторизации. Причина сетевого ожидания пока неизвестна.

В `FriendsAccessAndroid.java:63` запрос идёт на
`POST https://185.251.89.19:8443/friends/restricted-readiness/challenge`.
Только успешный challenge позволяет сформировать proof и выполнить
`POST /friends/restricted-readiness`; ACK имеет отдельные `/ack-challenge` и `/ack`.
Это служебный адрес bootstrap, **не свидетельство выбора данного VPN-gateway**.

Readiness создаёт direct-клиент с общим 30-секундным бюджетом
(`FriendsRestricted.java:98`). Если собственный ConnectionService не `on/ok`,
`HTTPS_UNDERLAY` выбирает `ChatNetworkAndroid.openHttps`; при собственном `on/ok`
используется отдельная ветвь default-route HTTPS_VPN. Метка HTTPS_UNDERLAY означает
ветвь кода, а не самостоятельный сетевой capture.

`ChatNetworkAndroid.java:29` заново перечисляет `ConnectivityManager.getAllNetworks()`
и берёт **первую** Network с `NOT_VPN` и `INTERNET`, затем вызывает её
`Network.openConnection`. Нет выбора по названию оператора, DNS для этого literal IP,
отключения TLS/hostname verification или обхода проверки сертификатов. Redirect запрещён.
Connect timeout ограничен 5s, read timeout — 15s и остатком общего бюджета. Это разные
ограничения; по одной длительности попытки нельзя определить конкретную фазу отказа.

**CONNECT_TLS_WRITE — укрупнённая метка.** Она выставляется перед
`getOutputStream()/write`, а следующая метка появляется лишь после
`getResponseCode()` (`FriendsAccessAndroid.java:74–78`). Поэтому сюда попадают TCP
connect, TLS, запись запроса, ожидание HTTP status и проверка остатка deadline между
операциями. TIMEOUT не доказывает именно TLS-сбой, отсутствие запроса на сервере или
HTTP401/403. Отсутствующий/нулевой записанный status — не реальный HTTP-код ответа.

`ReadinessBootstrapRoute.java:16` после IOException **challenge** выбирает имеющийся
RNS fallback. SSLException отдельно пробрасывается без такого обхода trust. TIMEOUT
подходит под IOException. Повтор proof/fetch после неопределённого результата этим
маршрутом не разрешается. Несколько `failed`-записей могут описывать один проброшенный
отказ; без attempt/connection correlation их нельзя считать отдельными relay-open.

## 2. Что означает RNS / RELAY_OPEN / UNAVAILABLE

В поставленном asset relay — **TCP `186.246.45.246:4242`** с закреплённым публичным
ключом RNS provider. Это control relay, не доказательство выбранного узла MESH.
`FriendsAccessAndroid.java:123` ставит RELAY_OPEN до `ControlRnsAndroid.openReadiness`;
RELAY_REQUEST появляется только после успешного открытия.

`ControlRnsAndroid.java:45` загружает Python/runtime и asset; Python
`fc_rns_transport.py:25` превращает **только TransportUnavailable** в tuple UNAVAILABLE,
который Java преобразует в `FriendsReadinessProtocol.Unavailable`. В этом классе
склеены разные исходы (`Channel:57`, `_check_cancelled:109`, `_wait:122`):

| Источник | Что действительно произошло в коде |
|---|---|
| Нет bindable underlay | Callback не смог привязать свежий socket к подходящей физической Network |
| Relay TCP | `socket.connect` дал OSError, включая timeout/refusal и другие ошибки сокета |
| RNS path/link wait | До общего 25s path/link deadline не появился маршрут или установленный link |
| Shared deadline | Общий readiness-бюджет уже исчерпан во время Python wait |

По данной категории нельзя выбрать одну строку. В частности, relay мог быть
недостижим, а мог принять TCP без своевременного готового RNS path/peer.
Ошибка импорта/инициализации Python, malformed asset, busy-session lock, отмена и
немедленно закрытый неактивный link **не все переводятся в typed UNAVAILABLE**:
ряд ветвей выбрасывает обычный OSError/другую ошибку. Поэтому нельзя просто расшифровать
эту запись как «RNS не установлен», «нет локального runtime» или «оператор блокирует RNS».
Она не содержит errno и точного внутреннего подэтапа открытия.

RNS сохраняет singleton runtime, но создаёт новый TCP socket и заново вызывает bind
для каждого Channel; старый path только этого pinned destination удаляется перед
запросом нового маршрута. Это не долговечный Android Network/SocketFactory cache.

## 3. AUTH и INTERNAL — не доказанная первопричина

`RestrictedBootstrap.java:30` различает authorization rejection и availability failure.
Только AuthorizationFailure/CHALLENGE_UNAUTHORIZED дают AUTHORIZATION_REJECTED;
challenge status401/403 обрабатывается отдельно. TIMEOUT → relay UNAVAILABLE при
отсутствующем кеше даёт **FETCH_FAILED + temporary BOOTSTRAP_UNAVAILABLE**, не AUTH.
Это воспроизведено на точном113 source с синтетическими transport failures.

Дальнейшие категории могут иметь иное происхождение:

| Категория | Реальные ветви113; не утверждение о данном телефоне |
|---|---|
| AUTH | `AutomaticVpnOwner.java:23,59`: требуется VPN consent либо `Builder.establish()` вернул null |
| AUTH | `AutomaticConnection.java:60`: callback revoke/destroy VPN owner; отдельно Denied при получении обычного профиля |
| AUTH | `FriendsRestricted.java:53`: сохранённый в текущем scope флаг именно authorization rejection; не timeout |
| AUTH | `ConnectivityOrchestrator.java:149`: SecurityException; это не обязательно HTTP-авторизация |
| INTERNAL | Нераспознанная Exception/LinkageError в orchestrator; отдельный INTERNAL_ERROR во внешнем prewarm/import catch |
| INTERNAL | `ConnectivityOrchestrator.java:143,164,185`: ошибка cleanup может заменить исходную категорию |

Эта таблица перечисляет общий source-контракт. После чтения правильного JSON
применимые ветви существенно сужены в разделе фактической хронологии: первый AUTH —
interruption при ожидании retry, последний INTERNAL — cleanup после candidate AUTH.
Отзыв consent именно сторонним VPN остаётся гипотезой. Export не разделяет onRevoke
и onDestroy и не содержит причинное исключение cleanup; нужна эта узкая детализация,
а не переклассификация сетевого timeout в AUTH или наоборот.

## 4. Почему список серверов виден без usable readiness

`GatewayPicker.java:8` строит список из статических RU и двух ControlFriendsCatalog
gateways. Выбор сервера хранится локально. Отображение списка не требует успешного
challenge, доступного RNS relay или расшифрованного MESH readiness.

Отдельно `ServerLoad.java:48` делает default-route
`GET https://185.251.89.19:8443/status/server-load.json`, с timeout5s/5s.
Это не Network-bound readiness POST; при стороннем VPN маршрут может отличаться.
FriendsActivity обновляет load map при успехе, при ошибке оставляет предыдущие данные
с предусмотренной проверкой свежести. Обычные AWG/TCP профили также имеют собственный
encrypted cache и `/friends/configuration/{ru|nl}` либо `/friends/gateway-configuration/...`.

MESH получает и проверяет отдельный node-bound bundle, хранит его через RestrictedVault
(AndroidKeystore/AES-GCM/AtomicFile, отдельные node scopes), проверяет сроки, подписи и
floors. Prewarm/chat может касаться другого узла либо обоих: это не доказательство
выбора узла пользователем. При cache=MISSING отказ обоих способов получения bundle
оставляет native connection без пригодного начального readiness.

`DiagnosticRing.java:67` прямо отображает non-READY result в NOT_USABLE; это **не
отдельный результат проверки отсутствующего файла каталога**. NOT_ATTEMPTED также
строится с учётом совпадения incident/restrictedSession. В рассматриваемой source-цепочке
без readiness до native beginReady не доходят, но одна экспортная метка не доказывает
отсутствие всех native попыток вне этой корреляции. Отсутствие записей каталога в
ограниченном диагностическом JSON не используется как диагноз.

## 5. Смена сети после стороннего VPN: факты и гипотезы

**Установлено по source и лёгким stub-тестам:** ChatNetworkAndroid и ControlRnsAndroid
не держат Network/SocketFactory между новыми запросами. Каждый новый HTTPS open и
RNS socket bind заново исключает VPN networks. При исчезновении физической сети нет
автоматического перехода на TUN. Это не проверка реализации ConnectivityManager на API28.

**Оставшиеся гипотезы:**

- Первая Network с INTERNET/NOT_VPN не обязательно VALIDATED или фактически рабочая;
  эти capabilities не являются доказательством reachability конкретного адреса.
  Выбор не отдаёт явный приоритет active/default Network.
- Уже открытый запрос остаётся привязанным к выбранной Network до завершения/ошибки.
  FriendsRestricted повторно использует незавершённый per-node prewarm future
  (`:70–73`); явный Connect может дождаться старой in-flight попытки. Network-change
  callback здесь её не отменяет и не запускает заново на другой сети.
- System always-on/«Блокировать соединения без VPN», переходное состояние Android
  после другого VPN, недоступность служебного IP:port или задержка HTTP/relay могут
  давать похожую внешнюю картину. Ни одна из этих причин на телефоне не воспроизведена.

**Точный недостающий различитель после чтения JSON:** network_type=CELLULAR и
`network_generation` уже известны; в113 это **Network handle, не счётчик поколений**.
Неизвестно, оставалась ли эта Network действующей в момент ошибки: нужны её
capabilities/lost/replacement и отдельные результаты TCP-connect, TLS-handshake и
HTTP status. `connection_changed=false` сравнивает IDs подключения Family Connect,
не Android Network. Совпадение handle на двух этапах не доказывает его liveness.

Для строгого отличия неверного выбора сети от недоступности служебного адреса нужен
сравнительный connect к **тому же IP:port с подтверждённой привязкой к текущей физической
Network**: старый/lost handle при успешном fresh-bound connect подтверждает проблему
выбора/старой попытки; совпавший live physical handle с одинаковым отказом оставляет
reachability/TLS/server path причиной, а не подтверждает stale Network. Даже VALIDATED
сам по себе не доказывает доступность этого адреса. Новый диагностический APK пока не
обоснован; существующий coarse trace не позволяет честно сделать более сильный вывод.

## 6. Один минимальный сравнительный тест на клиенте

Один парный **warm/cold** тест, без смены версии, identity, выбранного сервера или режима:

1. Оставить CELLULAR, выключить Wi-Fi. Штатно отключить сторонний VPN. Не менять
   always-on/«Блокировать без VPN»; если они удерживают VPN/запрещают underlay,
   записать это ограничение и не обходить его ради теста.
2. **A:** сразу после отключения стороннего VPN выполнить один Connect Family Connect,
   дождаться результата, записать UTC и сохранить диагностику. Затем обычный Disconnect.
3. **B:** в Android принудительно остановить **только Family Connect**, не «Очистить
   данные/хранилище/кеш» и не удалить приложение. Открыть его снова на той же CELLULAR
   и повторить один Connect с теми же настройками; сохранить результат/UTC/диагностику.
4. При обоих VPN OFF один раз открыть в браузере существующий read-only адрес
   `https://185.251.89.19:8443/status/server-load.json`. Отметить JSON/HTTP response,
   timeout или TLS warning; предупреждение сертификата **не обходить**. Ключей,
   профилей, активационных кодов или содержимого JSON присылать не нужно.

Успех только B поддержит гипотезу процессного/in-flight состояния, но не докажет stale
Network сам по себе. Провал A/B и browser-control совместим с недоступностью служебного
адреса/системной политикой; browser success при провале клиента сужает поиск до его
маршрута/POST/состояния. Browser — вспомогательное сравнение, не bound-socket доказательство:
его proxy/cache/network могут отличаться. Если между A/B изменились сеть или cache/READY,
это надо сохранить в результатах, а не называть чистым воспроизведением сетевой гонки.
Две небольшие диагностики передаются приватно; сами private keys экспортировать не надо.

## 7. Выполненные проверки и сохранённое evidence

Только локальные javac/JUnit/Python, nice10, JVM max128/256MiB и два active processors.
Использованы сохранённые JDK/JAR; никакого Gradle/AVD/Android сборки, SSH или запроса к
production endpoints. Тесты mock/stub, не полевой runtime и не full-CI PASS.

| Проверка на d2882cd | Результат | Локальный receipt, SHA256 |
|---|---|---|
| Existing ReadinessBootstrapRouteTest, MobileBootstrapTest, RestrictedBootstrapTest, ConnectivityOrchestratorTest, ReadinessStopTest, RestrictedGatewayTest, GatewayPickerTest | 64 PASS, JUnit 0.329s | `check-1.log`, `129d95fd3ac15769b3dc76ac5d97dc3f8e5c7fe17c8356e08538e773bcfe9383` |
| Existing network_fixture + actual113 ChatNetworkAndroid | PASS: fresh Network, handoff before/during/after ready, TUN excluded, lost-network failure | `check-3.log`, `4c01d107f8fd5f33330618713131800a1dc69b494b02ef17487407542cfa5622` |
| Existing Python bridge fixture, pinned exclusively to113; typed connect refusal, no underlay/cancel, malformed/busy/unknown, request timeout, rejected response, deadline | 6 PASS, 0.018s | `rns-checks.log`, `90c7e48f3f3d91b8d9dbc8887dbb7caaef8f89f41812439c99b66a874da71714`; exit0 |
| Synthetic exact113 TIMEOUT → UNAVAILABLE + missing cache chain | PASS: FETCH_FAILED/temporary BOOTSTRAP_UNAVAILABLE; AUTH/INTERNAL are distinct branches | `failure-chain.log`, `fff95980602d5c0128754e0a55a9c18f8ba84bfaff2f89ed9d5c818de412d392` |

`checks.json` retains exact compiler/JUnit/network-fixture commands, exit codes and log
digests. Ignored local thin drivers: `checks.py` SHA256
`f629c2d70cbf4dff1e54f21570b8a0086b58990c56eace9300069bfeb46b9032`,
`rns-checks.py` SHA256 `0acaecd42928f06de5f2cb65884aab790ae90fa1393dcb7ad2f65897f2c96658`,
`Field113FailureProbe.java` SHA256 `f38ed701e55909cb3ee29be02cb7bf675bb8a67c4338bde42771a5f4fb75a38d`.
These checks overlap in modeled behavior; they are not summed into an acceptance suite.
Documentation check: `python3 scripts/check_public_docs.py docs/STATUS.md docs/PLAN.md
docs/releases/2026-11-06-beta113-field16-bootstrap.md` — three files/295 links, no errors;
`git diff --check` passes. This is local link validation, not an HTTP availability check.

### Дополнение после получения правильного файла

В ignored `actual-export16/` сохранены input.private.json (0600), sanitized-analysis.json
(локальные aliases вместо opaque IDs), exact commands/exit codes в recovery-checks.json.
Raw JSON, его opaque IDs и локальная таблица сопоставления в Git не включены.

- Существующий `ConnectivityOrchestratorTest`: **31 PASS**, 0.043s;
  `recovery-check-2.log` SHA256 `875173a5bccfd202143e0ecb5339f9e00ac39e5f89cdba690b359477f97ccb7c`.
  Это адресный повтор части прежних64, не31 дополнительных независимых теста.
- Два синтетических control-flow сценария exact113: interruption AUTH до due retry;
  candidate AUTH + cleanup exception → INTERNAL. Оба PASS, вместе с проверкой
  fallback TRANSPORT_UNAVAILABLE при networkAvailable=true.
  `recovery-check-1.log` SHA256 `940c36fd0d7f070cb594b0e3477a60288dde1d3893493d004e9173a7a27093de`.
  Thin driver `Field113RecoveryProbe.java` SHA256
  `aeda3cbf076797954c99e2776bf4747a50c55ba44aa29d1944122742fa9ebe5b`.
- Sanitized local correlation SHA256
  `c0c6f64dd966c05ce67e8f402baf792e049ea98594e9ce4ac7dde169979948e8`.
  Это анализ двух snapshot, не новый полевой запуск и не Android runtime PASS.

No installation/rollout/rollback is performed or needed for this documentation-only
audit. APK118/updater113, subscriptions, certificates, admission, G4 and frozen artifacts
are untouched. Earlier failed runs and unrelated local changes remain. **Next: the
single comparison above with UTC/cache/Network observations**; the correct export
has been received and does not need to be requested again. No speculative APK.

## Bounded provisioning candidate

### Answer and discovery contract

**Yes in the isolated source/integration candidate, not in installed beta113.** An
already registered device with no readiness, no working VPN and both direct paths
disabled obtains a new signed bundle and opens normal MESH. It needs its existing
Friends identity, the existing public root and a **previously delivered, still-valid
public locator asset** `provisioning/nl-amsterdam-1.json` (or the node2 equivalent).
No runtime injection after Connect, missing readiness, Family client leaf, old service
IP or extra carrier is used to discover that room. This is NOT first activation.

The locator is version1/purpose `family-connect-provisioning-v1`, node-bound, sequenced,
time-bounded and contains only a room locator and public server certificate plus the
existing root-signed restricted issuer delegation. The **same existing issuer key**
signs it with a separate domain; `control/friends/bootstrap_locator.py:issue` checks
the existing `_trust`, CRL, server certificate and SeedManager directory. No root,
signer service, entitlement database or authorization writer is added. Locator sequence
is metadata in this asset-only version, not a newly implemented persistent rotation floor.
Readiness replay/revision/CRL floors remain unchanged and mandatory.

The real SeedManager creates a room, joins it, then invokes its publication callback;
only that published seed can be signed. Lifetime is bounded by seed expiry, issuer,
server leaf and current CRL, **never more than4h**, and provider room failure can shorten
it. This is a finite controlled-delivery window, not evergreen cold discovery. Rotation
requires independently delivering a new signed asset; a client missing that delivery
fails closed. There is no fallback locator download from HTTPS8443/RNS4242, hidden
service IP, per-Connect manual room entry or prerequisite third-party VPN. No actual
locator asset is committed or shipped. The original beta113 GAP evidence is preserved.

### Bounded entry and custody

- Server source entry: `coldprovision.Run(Config, RoomProvider, SeedConnector, Backend)`
  uses the existing SeedManager and single-exchange carrier. `Config.Publish` remains
  an authority-custody callback; it returns the signed locator for verification against
  the actual published seed and server certificate. The integration invokes the actual
  existing issuer in a separate Python process. Gateway code has no issuer private key
  or grant registry. No change to production bootstrap entrypoints/configuration.
- Client native entry: `coldprovision.Open` + `Telemost(underlay)` via the new JNI adapter.
  Same Telemost/packet/reliable stream code, TLS1.3, distinct ALPN and exact signed
  server certificate pin under the existing root delegation. No Family client leaf is
  needed for this **pre-admission service**, but it cannot open Family mux/data plane.
- Only challenge then readiness-fetch; at most two framed64KiB requests,30s overall
  (also bounded by existing bootstrap exchange lifetime), one server exchange per seed,
  at most two local JNI leases. No arbitrary HTTP URL, activation, ack, DNS or TCP RPC.
  Backend is a fixed numeric loopback adapter to the existing readiness handlers;
  redirects and environment proxies are disabled. No carrier-owned authorization store.
- Existing device proof is checked by the real authority against current registration,
  admission, entitlement and revocation. The adapter additionally binds node, public
  identity, WG key and returned fresh challenge to this TLS exchange. Reusing another
  session's proof, wrong-purpose challenge or recipient fails. Locator/room knowledge
  is not bearer access. No proof is retried through another route after uncertain fetch.
- Android selects this route only after an initial HTTPS challenge I/O failure and typed
  RNS Unavailable, with no usable cache. TLS/trust/auth rejection and post-proof failure
  do not select it; activation and ack remain outside it. A fresh physical Network and
  its IPv4 DNS are selected and pinned for this provisioning lifetime. Loss fails closed,
  not an implicit VPN or public-resolver fallback. No hardcoded replacement service IP.
- Unchanged readiness protocol, native validator, encrypted RestrictedVault, existing
  AutomaticVpnOwner and RestrictedTunnelEngine finish the normal path. Cancellation
  does not revive the owner: a late valid response may populate the identity/node-bound
  cache but cannot start native in the closed attempt. A separate new Connect is distinct.

### Executed scope and provenance

Local evidence: `state-client-build/cold-provisioning-20261106/` in the separate worktree.
Base41b4e6e034efc3e51446f383f2fbaedee3ad5a67 plus candidate source inventory
`03f3db74a76e8b60655544e081f6d7a44b7958db29f7ad366e318dd635616d85`.
`full-4/receipt.json` records exact commands, image/binary hashes and exits; its inventory
is verified unchanged at the end. Source checkpoint is the commit introducing this section;
this is not a claim that unmodified41b4e6e implements provisioning.

| Check | Result and exact scope |
|---|---|
| `full-4/runtime.log` | PASS13.91s; actual SeedManager publication → preplaced locator → dual-block Android source selection → server TLS → registered device proof → real access-api/issuer → unchanged validator/encrypted vault/owner/engine → real native Family TLS/mux, TCP echo, DNS and verified TLS HTTPS; normal cleanup |
| Same runtime, negatives | PASS other issuer-valid but unpinned server, unactivated/revoked/expired-subscription devices (403), other-session replay, wrong-purpose challenge, other recipient, link drop, stale/tampered/wrong-device bundle. Certificate-row count unchanged by negatives. Malformed signature retains existing backend503, not relabelled AUTH; no issuance/fallback |
| Same runtime, late owner | PASS actual fetch held until Disconnect, then validator/cache completion without native begin or owner resurrection; a separate fresh client Connect subsequently succeeds |
| Locator | Missing/structurally invalid/forged/wrong-node/expired rejected; expiry boundary uses supplied verification time, not a wall-clock certificate-crossing claim |
| `jvm-4` |94 PASS (includes earlier65, not additional); route selection/no proof retry/no auth bypass, cache floors, protocol, trigger/cleanup; actual ChatNetworkAndroid methods with OS stubs separately verify physical resolver/pinned-network loss |
| `python-1.log` |97 PASS,4 skipped in1.09s: new locator9 cases plus existing readiness/paid-authority regression. The skipped artifact-enabled native delivery cases are NOT claimed PASS |
| `race-1.log` |coldprovision/bootstrap/familysession/roombroker packages PASS with `-race -count=1 -p1 -timeout=90s`; not whole-native/full-CI acceptance |

Runtime log SHA256 `40f424a86a73c6c2d0058b59b53e2fa58bef238841ba8432e9e08e22a4924259`.
Python log `6925026ea2d9ef724c9e0043d7106da7f27b259beca948ea536ebd782167e1e3`;
JVM log `feccd4362baaa260755b46d437fbd22f8c58cf9351a5ad2bf826ec975fba5098`;
network log `bd8f60f24582ed7acaac4b3ca8220ee5ebc8c21f1e6dcc03de86a7f961feb3a7`;
race log `7d08dbcbfd467667eaa10f28159c7ccd93cf7eb518c6773e05465d99fe50ca5b`.

Reproduce with the existing pinned local tools and already present offline image;
`OUTPUT` must be a fresh directory beneath this worktree's ignored `state-client-build`:

```sh
python3 tests/fixtures/mobile_bootstrap/run_provisioning.py --tools "$TOOLS" --output "$OUTPUT"
python3 tests/fixtures/mobile_bootstrap/check_provisioning.py --tools "$TOOLS" --output "$OTHER_FRESH_OUTPUT"
python -m pytest -q tests/test_bootstrap_locator.py tests/test_friends_restricted.py tests/test_paid_beta_readiness.py
```

The Python command needs the existing control/identity locked dependencies. Runtime
runner inspects/reuses the local image; it does not build/pull an image or contact a
production endpoint. Original FAIL outputs must not be reused as OUTPUT.

The short runtime reuses the existing local packet provider and existing offline test
image, `--network none`,1CPU/640MiB, no AVD. The service authority is a separate Python
process; JVM source uses a test-only local RPC shim to the real Go native operations.
Android framework/TUN, JNI invocation and hardware-keystore provider are fixtures;
AES-GCM, identity proof, issuer, validators, owner/engine code and native MESH/traffic
are real. Thus this proves source/core integration, NOT kernel VPN routing, Android
JNI runtime, actual Telemost signaling/media or accessibility in this phone's network.
JNI binary compilation is pending at this checkpoint, not silently substituted by the shim.

### Preserved failures and diagnostic change

Earlier field JSON/source analysis and41b4e6e GAP reproduction remain unchanged.
Local candidate failures are retained: missing system RNS dependency; first closed pipe;
integer-seconds seed-publication check corrected to existing nanosecond clock; initial
DNS fixture incorrectly assumed default resolver and then used a prohibited non53 port
(now isolated real port53, no relaxed mux rule); shell PATH variable failure; source
compile errors/resource omission. `full-1` fails on reused test request IDs;
`full-2` fails because its alleged wrong purpose was the valid enrollment audience,
and because it assumed403 for malformed signature where the existing handler returns503.
The corrected test uses an actual status-purpose challenge, fresh IDs, exact existing
503 and asserts zero new certificates. No production expectation was changed for green.
`full-3` PASS15.58s is preliminary; `full-4` rechecks the final CRL-bounded signer and guards.

Diagnostic changes retain `trigger_reason` independently of `cleanup_reason` and
`secondary_stage=CLEANUP`, keeping the existing event/attempt correlation and terminal
`policy_reason`. AUTH is still AUTH; cleanup can still make policy INTERNAL. Existing
fetch failure is a separate event; no inference of onRevoke or timeout cause is added.
No key, proof, personal identifier or rendezvous content is logged by the new adapter.

### Remaining boundary / one next

Qualify this exact candidate on **real Android and actual Telemost provisioning** with
fresh independently delivered locator, then separately authorize controlled delivery
and a cold dual-block attempt in the target mobile network. Test OS keystore/JNI/TUN,
Network handoff/cancellation and finite-locator distribution/rotation there. This does
not claim provider reachability, first activation, permanent discovery, or a delivered fix.
No new speculative diagnostic APK is proposed. No release, install, live policy change
or rollback was performed; source rollback is omission of this independent branch.
Main worktree/foreign edits, G4/frozen artifacts, APK118/updater113, existing schedules,
paid/cohort/admission and all production credentials remain untouched.

### Final continuation: recipient guard, deferred ACK, actual bounded stalls

The earlier6840193 candidate and `full-4` result above are retained, not relabelled.
The final source delta fixes two directly relevant integration failures:

1. After Disconnect and replacement of the synthetic local identity while the real
   provisioning response was delayed, the previous recipient's response could enter
   the shared node cache. Native did not start, but that cache write was inappropriate.
   `identity-3-before` is a corrected, specific FAIL11.89s: it checks the **response**
   field, not the existence of cache-attempt metadata. Earlier `identity-1`/`identity-2`
   used the overbroad whole-file assertion and remain FAIL evidence, not proof by
   themselves. The adapter now reloads the local identity, compares public identity
   AND WG binding before returning provisioning material, and wipes a rejected result.
   `identity-4-after` PASS17.43s includes changed identity, unchanged closed owner,
   then a separate successful fresh Connect. This is not a diagnosis of the field AUTH.
2. `final-3` retains FAIL at50s: a wall-clock model of15s HTTPS TLS/write timeout plus5s
   RNS socket timeout obtained the bundle, but synchronous best-effort ACK via the same
   unavailable API held completion beyond the owner's30s deadline. No timeout/TTL was
   increased. Provisioning results now persist the existing **ACK_PENDING** receipt and
   immediately finish normal owner delivery; existing later refresh/restart publication
   remains the retry path. Cold locator-enabled restart also defers its old receipt.
   No ACK is transported by the pre-admission service, no new timer/writer, and server
   ACK_RECEIVED is not claimed. Ordinary/no-locator and usable-cache paths retain their
   existing acknowledgement behavior. The unit test covers durable defer then normal ACK.

**Final acceptance: `final-4/receipt.json`, all exits0, runtime38.52s.** It includes
the full source/native traffic path, identity/owner negatives, and a real in-flight
link loss after the authority has handled the challenge but before the reply arrives
(not merely closing a handle before making a request). Invalid/stale bundle cases now
explicitly require a valid public-identity baseline before the negative assertion.
The normal Connect waits the actual modeled15s+5s before entering provisioning, obtains
the bundle and starts native in the remainder of the unchanged30s budget. These are
wall-clock **I/O fixture delays**, not measured phone/provider latency or cryptographic
deadline crossings. Longer stalls or an unavailable Telemost carrier can still fail closed.

Final runtime log SHA256 `85f89f620d73ef3b56c442a0a1ae7584c98e477e03fb7bc1790d7c712b5841b9`;
receipt `4e1fc81f4035db3b69ac54eecc12843d458b5dd9765effa8f12967d9e379d16d`;
source inventory `c5a2920ff29a67e73149e387e8464fb03c3e4c3cc051367c7fb4afafcfcc6488`;
integration binary `6ef021fa58d96d68ae9ce3d099068f7e568987f91c34c38912fddbf9a984340a`.
The inventory covers6840193 plus the source/test delta in the commit introducing this
continuation; docs are not runtime inputs. Final JVM `jvm-5`: **95 PASS**, including
earlier94 (not summed), plus the same actual Java network-selection probe. JVM log
`44c4d88ce59b25a5754d705fd354c07c197cd59ea6ab201d58c306792a9c0a9c`.
`race-2` repeats only coldprovision after strengthening its forbidden-path test with
a valid request ID; PASS1.012s, not an additional package/full suite.

The official `pilot/android-restricted/build.py` also passes its packet `-race -count=3`
gate and arm64-v8a release-mode JNI compilation,1CPU/nice15, no AVD/Gradle/APK.
Exact native source `6840193e766f33c2974dad639b8d7e6dad7d6bcb`; library SHA256
`1e478adf1b2bf5c8ce78498f0ad9554f0b121190a18bceaf1dad0eabe4d58a4b`, Telemost provider,
no qualification tags. All three new JNI exports are present. The final delta changes
Android Java/tests, not production Go/C sources, so this unchanged library is not rebuilt.
This is compilation/link acceptance, NOT execution of that library on Android.

[Sanitized final component/evidence manifest](2026-11-06-cold-provisioning-evidence.json).
Source is on the independent `feature/android-cold-provisioning-20261106` branch;
6840193 was pushed and verified before the final logical fix. The final fix/report
commit and remote verification are reported with this task, not an inferred main SHA.
Original main remains19af689 with unchanged status/diff/staged hashes; all own short
containers have exited/removed, no AVD started. Private fixture keys and raw evidence
remain ignored/local. All field/Android/Telemost and controlled-delivery limitations
above remain; positive traffic scope is the synthetic primary-node configuration,
not a separate positive node2/production acceptance.

### Android/Telemost runtime eligibility, 6 November17:55UTC

**NOT_RUN**, not a failure of the accepted core candidate and not a runtime PASS.
The requested source remains `cf419a150f261bc7d49d7211d9cebda980a8d593` on
`feature/android-cold-provisioning-20261106`, clean at preflight; remote SHA matched.
This continuation changes documentation/evidence only. No previous suites were rerun.

Read-only Docker inspection at17:55:51UTC finds these existing containers running:

| Resource | Started UTC | CPU quota |
| --- | --- | --- |
| `fc-mesh-full-core-bfff97d-c8eb8b9` | 2026-11-06T10:42:51.672330173Z | 1 CPU |
| `fc-mesh-full-core-c8eb8b9-gateway` | 2026-11-06T10:42:56.345212932Z | 0.2 CPU |
| `fc-mesh-full-core-c8eb8b9-origin` | 2026-11-06T10:42:56.213258024Z | 0.2 CPU |

A preceding `docker stats --no-stream` sample reports9.97%/0.58%/0.22% CPU,
respectively. This establishes occupied resources, **not a G4 test outcome**: no G4
logs, receipts or frozen files were read/modified, and no container was stopped.
The user's no-competing-heavy-build/AVD constraint therefore prevents this run.
KVM is readable/writable; NVIDIA GTX1650Ti/driver580.178.04 is present. GPU availability
alone is not permission to compete with G4. No AVD is launched and no software
rendering fallback is used. No physical test phone has been authorized for this task;
owner/field devices were not queried or used.

`roombroker.NewTelemostRoomProvider` requires `YANDEX_TELEMOST_OAUTH_TOKEN`.
Only its **presence in the current execution environment** was checked: absent.
No separately authorized test-account credential path was supplied. This is not a
claim that credentials do not exist elsewhere; no private files, other process
environments or production hosts were inspected for them. The older
`pilot/android-telemost/bootstrap_acceptance.py` hardcodes a live gateway/SSH writes
and is **not executed** as an isolated substitute. No provider call or room creation
is made. The existing offline JNI/RPC fixture is not rerun as Android evidence.

#### Artifact and result boundary

The prior arm64-v8a JNI library is unchanged: native source
`6840193e766f33c2974dad639b8d7e6dad7d6bcb`, SHA256
`1e478adf1b2bf5c8ce78498f0ad9554f0b121190a18bceaf1dad0eabe4d58a4b`.
It is compiled evidence only, not an APK or a library executed on Android. A future
KVM AVD must use a matching ABI and the actual JNI/framework/Keystore, never an
ARM emulation/software-provider substitution or the prior invocation shim.

| Requested measurement/result | This continuation |
| --- | --- |
| Real Android + Telemost provisioning + validator/vault + MESH | NOT_RUN |
| Qualification APK manifest/native/assets/source/digest | No APK built; no digest invented |
| Locator origin/issued-at/expiry/node/server binding | No locator issued or injected; fields absent |
| Connect, direct-path completion, carrier ready, server/device authentication, bundle validation, native ready, first DNS/HTTPS monotonic timestamps | No Connect attempted; all absent, not zero or the38.52s core-suite time |
| Tested node, DNS, verified HTTPS and gateway egress | NOT_RUN; neither NL claimed |
| Disconnect/late result/old owner, expired locator, foreign/revoked identity | NOT_RUN on real runtime |
| Durable ACK_PENDING and separately delivered ACK_RECEIVED | NOT_RUN on real runtime; prior source evidence retained |
| Cleanup | No own runtime resources created; none to stop |

Local read-only receipt:
`state-client-build/cold-provisioning-runtime-20261106/preflight.json`, SHA256
`3dcfd10d70db27605a04f12341d28d3e6f879f736985879f65fe42ba9aad15be`.
Its monotonic elapsed field measures **preflight only**, not Connect latency.
[Sanitized NOT_RUN manifest](2026-11-06-cold-provisioning-runtime-evidence.json).
The earlier core receipt, original failures, source inventory and artifact remain
unchanged. Main-worktree status/diff/staged hashes match the preceding checkpoint;
no installed version, public catalog, G4, production, admission/paid/cohort or schedule
change occurred. There is no new deployment or deployment rollback.

#### Locator rotation remains an open product scenario

Current `ProvisioningCarrier` reads only `assets/provisioning/<node>.json`. For the
future bounded runtime check, the same issuer must sign the real SeedManager
publication and include that locator in the qualification APK **before Connect**;
record issuance/expiry, node/server binding and APK/source digest locally without
publishing the rendezvous. No readiness bundle is preloaded. The maximum4h and all
shorter seed/certificate/CRL bounds remain unchanged. A stale asset is rejected.

The scenario **registered client starts after its last locator expires while both
direct service paths are unavailable** is still unsupported. A qualification APK
carrying a short-lived asset is not a final field fix or evergreen discovery.

One minimal **proposed, unimplemented** independent-refresh contract is explicit
signed-locator-file import through Android's document picker. The existing authority
issues the same public locator envelope with the same issuer/root trust; an operator
delivers that file through an independently available channel chosen for that user,
not through the blocked API or a required third-party VPN. No specific channel is
assumed reachable in the field phone's network. Before atomic replacement in a
separate local locator store, validate root delegation, signature, version/purpose,
node/server binding, all time bounds and a persisted per-node locator sequence floor;
equal-sequence identical content may be idempotent, conflicting/older content must
not replace it. Keep the current locator on failed import; do not reset floors or
touch readiness/identity. The new file remains a locator, never a grant or user
secret; device proof and current authority admission are still required. This small
manual refresh contract does not promise unattended discovery, needs its own review
and tests, and is **not implemented or started in this continuation**.

**One execution next:** when G4 resources are released and an authorized test OAuth
source is identified, run the single bounded Android/real-Telemost vertical and
small runtime regression on the separate synthetic backend, with matching-ABI JNI,
KVM/NVIDIA if using an AVD, fresh pre-Connect asset and scoped direct-path isolation.
Stop on the first exhausted unchanged Connect budget; retain its stage/reason.
Record latency from the actual Connect, not suite time. Field-network accessibility,
controlled delivery and any permanent discovery decision remain subsequent,
separately scoped work; no delivery is performed here.

### Authorized vault access follow-up, 6 November

**NOT_RUN / LOCAL_VAULT_AUTHENTICATION_REQUIRED**, not a provider rejection or an
Android failure. Product source remains `cf419a150f261bc7d49d7211d9cebda980a8d593`;
the existing branch starts this documentation-only continuation at `f860098`.
The owner authorizes exactly one named local vault entry for this bounded test and
new test rooms; its private entry path is not copied into Git. This authorization
does not cover other entries, account OAuth changes, existing rooms, production,
admission, subscriptions, catalogs or live services. No further permission to use
that entry is required within this test; authentication and authorization differ.

The one allowed G4 snapshot at **18:23:17.516730UTC** establishes:

- `fc-mesh-full-core-bfff97d-c8eb8b9`: exited, Running=false, Pid0, ExitCode0,
  FinishedAt `2026-11-06T18:14:35.056146808Z`; existing `.exit` file contains0.
- Both existing route helpers are stopped: gateway exit1, origin exit0. The gateway
  nonzero exit is retained, not described as successful cleanup.
- No terminal receipt is found at the inspected local relative path
  `state-client-build/mesh-core-runtime-20261105/full-core-bfff97d-c8eb8b9/full-core/progress.json`.
  It is not searched for elsewhere or reread. Exit0/resource release alone is not a
  final G4 acceptance receipt. Interpretation and cleanup stay with the main session.
- No container restart/stop/removal, G4 source/profile/network/artifact change,
  repeated poll, AVD or heavy build occurs in this continuation.

A separate local process/session-metadata check finds KeePassXC **not running**, no
KeePassXC DBus owner, and an available desktop session bus. A registered generic
Secret Service is not evidence of an unlocked KeePassXC database: it is not queried
for entries or used as a substitute. Local KeePassXC settings/cache presence is
checked, but no KDBX contents, vault entry, password or token is read. CLI and Zenity
are installed; the existing [protected local-input pattern](../vault-signing.ru.md)
requires ordinary owner authentication. No password dialog is left waiting, no lock
is bypassed, and no other credential location/process environment is searched.
The observation does not establish that the database or selected entry is missing.

Consequently there is no provider request, test room, APK, newly issued locator,
Connect, Android measurement or runtime regression result. No temporary secret copy
or owned runtime resource is created, so none needs removal. The original vault
entry is unchanged. Previous source/core checks are not rerun or counted as runtime
acceptance. Installed/public/invitation versions and catalogs are unchanged; there
is no deployment or rollback action. Only sanitized documentation is checkpointed
on the existing feature branch, preserving the unrelated dirty main checkout.

**One next:** complete normal local vault authentication without sending credentials
to chat, then run the previously agreed single isolated vertical with the existing
finite pre-Connect locator, matching-ABI JNI, one NVIDIA/KVM AVD under the shared
qualification lock and the same bounded runtime negatives/ACK checks. Protect the
token from command arguments, logs, reports, APK/locator/client artifacts and Git;
retire only this test's newly created resources and any temporary secret copies.
Locator import, new discovery and additional product functions are explicitly out
of scope. This is a blocked runtime checkpoint, not a release or acceptance PASS.

Documentation validation: `check_public_docs.py` on STATUS, PLAN and this report
passes3 files/305 links, no errors; sanitized JSON invariants and `git diff --check`
pass. These checks do not exercise Android, Telemost or any external URL.

### Actual Android/Telemost attempt, 6 November

**FAIL_RUNTIME, incomplete acceptance.** The previous authentication-only blocker
is superseded by successful protected local input and an actual bounded Connect.
No product source changes: candidate `cf419a1`, execution checkout `41923a2` (later
commits in that interval are documentation only). No locator import/new discovery,
OAuth/account, production, admission, subscription, catalog or live-service change.

#### Secret input and preserved setup failures

The existing Zenity→stdin-pipe→KeePassXC CLI pattern is used, not GUI-unlock reuse,
clipboard, chat, argv or a recorded terminal password prompt. The selected database
is opened read-only with the existing owner/mode/symlink guards. Only the authorized
entry's Password attribute is requested; no listing, full export or other entry.
CLI output goes to the dedicated local test supervisor, then the server's stdin;
the server creates its provider and immediately removes the temporary environment
binding. Build/Android processes do not receive this value. Core dumps are disabled.
No password/token file, report value, hash, fragment or client-asset copy is created.
All processes that held the secret have exited. The original entry is unchanged.

The first two CLI attempts fail with the displayed root group incorrectly included
in the CLI path. Their raw diagnostics were suppressed, so no password-error claim
is made. A disposable synthetic database reproduces this path discrepancy; removing
the display root addresses the same authorized entry, not a search for alternatives.
The next successful read is followed by a fail-closed executable-permission guard
before provider access. Its memory is released; the guard is moved before input and
the own executable is restricted to0700. Further local input successfully starts
the server. These operator/runner failures are retained, not credential exposure or
product failures. No automatic recovery of a password from another source occurs.

The first runtime fixture uses loopback DNS127.0.0.53 for a protected-route server
connector. `underlay.RouteIPv4` therefore selects loopback and the ICE filter cannot
advertise the physical route. The ordinary gateway publishes a real seed, while the
provisioning worker fails before its locator. Both workers join, the authority stops,
and the first NVIDIA/KVM AVD closes before installing/running the test. The initial
worker error was not retained beyond its stage; attribution to the fixture's route
selection is source-supported, not a captured provider error. The corrected fixture
uses existing `bootstrap.TelemostSeed` on the non-VPN server; Android's real protected
network code is unchanged. A new local input starts this separate corrected attempt.

#### Actual runtime result

Before heavy work, no running G4-matching container is found. No G4 final receipt is
reread, and none of its resources is stopped/removed. The shared qualification lock
and absence of another QEMU process are checked. AVDs run sequentially, API27/x86_64,
`-gpu host`, PRIME offload, `-accel on`; actual guest renderer is NVIDIA GTX1650Ti /
driver580.178.04. Strict guest wall-clock checks pass without adjusting clocks or
relaxing certificate checks. No physical owner/field device is queried or used.

The fresh local Friends authority has generated disposable identities, root/issuer,
DB and profile. Provider access creates test rooms only. The corrected server publishes
an issuer-signed finite locator before Connect; the build embeds only that locator
and synthetic trust. Test identity is imported into real Android Keystore-wrapped
storage; readiness is initially absent. Guest-only OUTPUT rules reject the RU address
and TCP8443/4242 before app installation, preventing accidental production fallback.
There are no host firewall or server-policy changes. This is a synthetic gateway
using the primary-node identifier, **not production NL1/NL2 or cellular acceptance**.

| Actual instrumentation event | Guest monotonic ms | Since Connect |
| --- | --- | --- |
| CONNECT_START | 38706 | 0 |
| OWNER_OPEN | 38725 | 19ms |
| FAIL_Rejected | 68825 | 30.119s |
| OWN_CLIENT_CLOSED | 68893 | 30.187s |

JUnit:1 test/1 failure,30.203s; host instrumentation command30.567534s. These durations
are not successful provisioning latency. The unchanged30s Connect bound is not
extended and the actual Connect is not retried. The corrected authority DB has one
restricted challenge and one issued certificate; the earlier fixture has zero of
each. This proves progress through authenticated issuance, **not** response delivery,
client validation, encrypted readiness-cache completion or native READY. The test
retains the exception class `Rejected`, but not its category/native substage; no AUTH,
provider-denial or carrier-timeout diagnosis is invented. DNS, verified HTTPS, egress,
late/closed-owner, expired/foreign/revoked identity and ACK_PENDING/ACK_RECEIVED runtime
assertions are NOT_RUN after this first failure. Earlier mocked/core PASS is separate.

Qualification APK manifest remains118/`0.1.18-beta118`, package
`com.familyconnect.app.friends`, debug signing for this disposable AVD only. Native
metadata: `telemost`, x86_64, no local-core/owner-diagnostic build tags. Its bytes and
packaged locator/root match the actual inputs. APK and test APK are built and installed
only in the disposable AVD; no public install/update/catalog/invitation version changes.
There is no production rollout/rollback action. Exact hashes and retained local
evidence are in [the sanitized runtime receipt](2026-11-06-cold-provisioning-live-attempt.json).

#### Cleanup and remaining boundary

On failure the engine is closed and the owner ends; both owned emulator processes
are subsequently confirmed stopped. All own Telemost workers join, the isolated
authority container is stopped/removed, and the credential supervisors exit. Final
checks find no own stand, Zenity or QEMU process and no own authority container.
No secret file was created, so there is no temporary secret file to delete. Private
synthetic fixture/AVD/artifact evidence remains ignored/local, not Git. Provider-side
room-object deletion/retention is not independently verified: this receipt proves
closure of own participants/connections, not deletion of the provider's room metadata.
Working rooms are not inspected, modified or closed. No additional OAuth read is
performed just to repeat this failed Connect.

**One next:** improve stage attribution around issuance→delivery→cache→native READY
within this same bounded diagnostic task before considering another runtime attempt.
Keep the original result,30s budget and current scope. Do not start locator import,
discovery, public delivery or any unrelated feature. This is an incomplete runtime
checkpoint, not an authentication-only documentation update or acceptance PASS.

Documentation/receipt validation passes: three Markdown files/308 local links,
eight retained evidence/source hashes, exact monotonic delta, manifest118/version
readback, JSON parsing and whitespace. No full-CI or remaining runtime PASS is claimed.

### Same-incident harness correction, 6 November

The original `FAIL_RUNTIME` receipt and private evidence are unchanged. SHA256 of the
executed instrumentation source is reverified as
`952790bb4137c3d5f55c19474b84a8072d4b69fa0c563ed6fbc5911ad13fc590`.
It directly creates RestrictedTunnelEngine with `elapsedRealtime()+30000`, bypassing
ConnectionService/AutomaticConnection. Earlier wording calling this the unchanged
product Connect budget is incorrect. In cf419a1 the orchestrator gives MESH a200000ms
candidate deadline under300000ms Connect; FriendsRestricted separately gives fetch30s.
The exact original absolute deadline was not emitted: assignment lies between recorded
38706/38725ms, so its deadline lies within68706–68725ms on that guest clock. `Rejected`
at68825ms lacks its enum/stack and cannot prove which check rejected. No clocks from
different processes are subtracted. Original authority issuance proves authenticated
issuance only; server write, client receipt, validator/vault and native begin are unknown.
No saved logcat/server stage log exists. An offline read-only conversion of the retained
AVD disk does not expose an ext filesystem (encrypted userdata); the original AVD is
not booted or modified to invent retrospective evidence.

The replacement harness calls existing AutomaticConnection with the MESH-only selection
used by ConnectionService, not a bespoke engine deadline. It does not exercise the service
foreground/UI lifecycle and does not call recovery polling. Existing diagnostics gain
bounded stage elapsed/remaining fields and a live readiness trace; server logs contain
only stage, validated random request ID, status and size. Before `candidate_failed`
cleanup the harness captures enum category, trigger/cleanup fields and native state.
Its finally always closes the owned connection even if snapshotting fails.
36 JVM tests (deadline/category and trace bounds included), Go coldprovision tests and
test-only118/x86_64 prebuild pass. The already pinned real-provider JNI is reused; the
server adds observational logging only. Runtime remains pending one diagnostic attempt.
No runtime negatives, product timeout/TTL/trust/admission change, user APK or deployment.

### Single corrected diagnostic attempt, 6 November

1. **Origin of30s / conformity.** Original hash-verified harness bypassed AutomaticConnection
   and supplied `now+30000` to the whole engine. That test defect is fixed, not a product
   timeout. The new harness invokes the same AutomaticConnection MESH-only selection as
   ConnectionService, without its UI/foreground-service lifecycle. Recorded absolute
   candidate deadline339645ms is139645+200000ms on this guest; Connect begins139617ms.
   The separate readiness fetch remains30000ms. Original exact deadline/category were
   not recorded, so original30.119s is not retrospective proof of a particular check.
2. **Bundle delivery/acceptance.** Original attempt: issuance1, delivery/acceptance unknown.
   New attempt: fresh authority restricted challenges0/certificates0; no challenge reply
   and no bundle received/accepted. Cache diagnostics remain MISSING/selected_source NONE.
   A readiness storage file exists after the attempt because cache bookkeeping is durable;
   that file's existence is not an accepted readiness bundle. Initial vault read was null.
3. **Last success / first unexpected failure.** Both direct paths are deliberately rejected.
   HTTPS CHALLENGE fails at CONNECT_TLS_WRITE/SOCKET (trace20ms); RNS at RELAY_OPEN/
   UNAVAILABLE (1729ms). Provisioning locator passes native begin validation and a lease
   is allocated (CARRIER_OPEN1734ms → CARRIER_HANDLE1736ms). CARRIER_REQUEST starts1736ms,
   then fails by1739ms without RESPONSE_RECEIVED. Source control flow and the wrapper
   code identify the native Post null/no-reply boundary, not its underlying Go reason.
   There is no server TLS-ready/request/backend/write event; absence does not distinguish
   failed carrier establishment from earlier native underlay/lease failures. No request-ID
   match can be made because no server request event exists. No cross-process monotonic
   subtraction is used. FriendsRestricted.ready returns null; engine stage READINESS_RETURNED
   precedes its BOOTSTRAP_UNAVAILABLE rejection. NativeRestricted.beginReady is NOT_RUN.
4. **Fixed causes / remaining uncertainty.** Harness-wide30s was wrong and is corrected.
   The new failure occurs at orchestrator elapsed1792ms, leaving198230ms at the pre-cleanup
   snapshot; readiness has about28277ms left at CARRIER_REQUEST. Neither deadline expired.
   The recorded trace's PROTOCOL is misleading: generic provisioning IOException becomes
   CHALLENGE_TEMPORARY_SERVER_FAILURE with availabilityFailure=false, an IllegalArgumentException
   subtype classified as PROTOCOL by the old diagnostic mapper. After this run, source now
   retains the original provisioning exception before wrapping and maps wrapped IO to IO,
   retaining challenge enum/availability. This changes diagnostics only, not retry policy.
   37 focused JVM tests pass, including deadline/category and wrapped-IO regression tests;
   Go coldprovision tests pass. No second runtime tests that final diagnostic correction.
   The original issuance→client boundary and the new native no-reply subcause remain unknown;
   neither AUTH nor slow Telemost nor generic network failure is established as root cause.
5. **Single run / cleanup.** API27, real Keystore/JNI/TUN owner, NVIDIA host GPU/KVM;
   guest-only direct-path rejects. Registered synthetic identity is explicitly verified
   against the fresh read-only authority DB, with zero previous challenge/certificate;
   matching identity assets, valid prepositioned locator, null readiness and no prior VPN
   are checked before Connect. This is the only new Connect, with no restoration polling.
   It is FAIL_RUNTIME, not MESH PASS. DNS/verified HTTPS/egress and other runtime negatives
   are NOT_RUN. Client disconnected, owned AVD exited, carrier workers joined, authority
   stopped/removed, credential supervisors exited and shared emulator lock was reacquired.
   Two new owned room objects have distinct privately retained IDs; participant closure
   is not object deletion. The official Telemost conference reference lists create/read/
   update, not an object-delete operation; no guessed DELETE or working-room access was
   attempted. Room-object deletion and lifetime remain NOT_VERIFIED. No token file was
   created; secret-bearing processes exited. Original KeePass record is unchanged.

The first Wayland dialog returned without a value; protected Zenity via the verified
X11 display succeeded. No password/token entered agent stdin, logs, client assets or Git.
The original AVD/evidence are untouched; the follow-up uses a separate ignored directory
`state-client-build/cold-provisioning-followup-20261106`. Its source is047da1d; pinned
JNI remains4e27ff23…57f99 from41923a2 (same product code as cf419a1). The follow-up server
adds safe stage logging and preserves provider ownership records. Test-only APK118/
`0.1.18-beta118` is built and installed only in its disposable AVD, never distributed.
No production rollout or rollback, installed owner/field client, admission/catalog,
OAuth account settings, paid pilot, G4 or other branch is changed. The one-run allowance
is exhausted; further native-boundary work is not an automatic authorization for runtime.

Exact artifact/source/log hashes and typed pre-cleanup evidence:
[sanitized follow-up receipt](2026-11-06-cold-provisioning-followup.json).
Public provider-reference check: <https://yandex.ru/dev/telemost/doc/ru/conferences/>.

### Native diagnostic continuation, 6 November

Owner-requested continuation from9765c5c; previous runtime047da1d and JNI4e27ff23…57f99
remain FAIL_RUNTIME evidence, not tests of this new instrumentation. Both original
receipts and local artifacts are preserved; no authority/readiness material is reused
as a hidden cache. Current scope is source diagnostics and one separately gated runtime.

Implementation: one mutex-protected snapshot in each existing provisioning lease,
returned through a separate JNI output argument, not a synthetic server response.
It records Go entry, handle, last completed/first failed stage, allowlisted cause,
provider step/status, numeric errno, elapsed/remaining budget, protection counts and
close/release observations. Pre-Go failures explicitly mark unknown Post budget;
the JNI allocation snapshot is set before acquiring references. No raw error text,
room URL, proof, token, certificate or bundle enters this diagnostic result.
Existing `startupdiag.Preserve` keeps carrier/TLS causes with legacy classifications.
The first failure is recorded before cleanup. Post observes Open completion before
its cancellation check; ready→cancel cannot erase that completed failure. Closing a
handle removes only that map entry, while an in-flight Post keeps its lease reference.
Underlay callback locking drains before releasing the JNI global owner. Java serializes
Posts, records each call's result in finally before cleanup, and keeps separate close
observations instead of overwriting the failed request. CARRIER_HANDLE still means
allocation only; CARRIER_REQUEST is invocation only; REQUEST_WRITE success means the
framed TLS write returned, not server receipt. Trust errors still fail closed.

Provisioning Network evidence comes from the actual pinned `ChatNetworkAndroid`, with
its own handle/type, availability at bind and snapshot, bind outcome/time and resolver
class. RNS's previous Network label is removed at provisioning-route entry. No network,
DNS, protocol, retry, admission or timeout setting is changed. Request encoding is
checked before write while preserving the original fail-and-close behavior.

Source gate (local `state-client-build/cold-native-diagnostic-20261106/`):

- `host-jni-final`: actual host JVM `-Xcheck:jni` → production C Begin/Post/Close → Go,
  with only a local connector seam and a Post-entry latch. Pre-carrier rejection,
  protect refusal, JNI callback missing/exception, carrier Open EOF, real TLS trust
  refusal, real TLS response EOF and concurrent Close/Open are distinguishable after
  JNI. No provider request. Host JVM reports expected Go/JVM signal-handler coexistence
  warnings; this host test is not an Android execution claim. Earlier fixture build/
  premature-server-close failures remain in host-jni-1…4; host-jni-5/6 also pass.
- `go-race-final.log`: changed coldprovision and selected Telemost owned-lifetime
  tests PASS, `-race -count=3`; real local TLS, write/EOF and concurrent snapshots.
- `lease-race-final.log`: production portable lease/map state PASS, `-race -count=3`,
  each exercising100 simultaneous Open failure/Post/Close cases; no stale-handle read.
- `jvm-final`:100 JVM tests PASS plus actual ChatNetworkAndroid/stubbed-platform
  selection/bind/lost-Network assertions. `pipeline-2`: source pipeline compiles.

Remaining gate: new real-Telemost x86_64 JNI/APK and short API27 provider-free check,
then exactly one fresh cold Connect. Android result, bundle/READY/DNS/HTTPS/egress are
NOT_RUN for this source checkpoint. Test-only version stays118/0.1.18-beta118; no
installation on owner/field devices, distribution or catalog update. Rollback is to
stop/remove only the disposable test execution; no production deployment to undo.

#### Built artifact and stopped Android preflight

Source070b8087ed494876c550f50befc64ffc7f197193 is committed, pushed and remote-SHA
verified on the requested branch. Its newly built x86_64 Telemost JNI has SHA256
`af52aeb8af7c5c782a8c1a659f271e0505e4a49a84a9a774b3f97404a86d1e04`;
no `fc_local_core` or diagnostic transport substitution. JNI Begin/Post/Close and
Go Begin/Post/Close/protect exports are checked. The library bytes exactly match the
packaged disposable118 APK, SHA256
`19a9b85f2a69d801dbd3d5c808725b5d1541c1966d2bf28a90fa3f1601cbc7a7`.
Instrumentation APK SHA256
`3f4965c8195bc23b7a7795992e4f775f706307e61c455fd6934b0cb387f0eed5`.
These are provider-free prebuilds with placeholder locator/identity assets, NOT a
ready-to-run cold provisioning package and not a user APK/public release.

Three own preflights fail before guest boot because the emulator normalizes its
userdata requirement to6GiB and the worktree filesystem has insufficient free space.
Those failed directories/logs are retained. Only the new test AVD storage is moved
to the writable data filesystem; no existing state, other branch or process is changed.
API27 then boots with actual GLES reporting NVIDIA GTX1650Ti, host GPU and KVM.
The CPU thermal guard stops that own AVD at85°C before instrumentation. After cooling,
an offline-only retry on the same own userdata with CPUQuota100% (previously150%)
again hits the guard, first observed at88°C, during preflight/install. No further AVD
is started. The original GPU80°C/CPU85°C and180s host safety limits are not relaxed.
Guest wall-clock eventually satisfies the observation guard; no clock/DNS/Network
switch is made. No JNI Android assertion has run: NVIDIA/KVM boot is NOT its PASS.

Consequently the **single new Telemost Connect is NOT_RUN and remains unused**.
No OAuth read, new provider room, authority, registered runtime identity or fresh locator
was created. No new cold transport cause can be claimed. Go/carrier/TLS/challenge
boundaries are demonstrated only by the local deterministic JNI fixture, not a field
attempt. Bundle/READY/DNS/verified HTTPS/egress and runtime negatives remain NOT_RUN.
Do not use source PASS, an allocated handle or prebuild APK as runtime acceptance.
The first concrete *test blocker* is resource availability, not a provisioning diagnosis.

Final review additionally finds RouteIPv4 and resolver wrappers discarding typed
underlay causes. The narrow follow-up preserves their original cause behind the same
safe `ErrDenied` string/identity; context/DNS/errno remain inspectable without logging
their private values. Cancellation after completed TLS is recorded at request validation,
not as a TLS handshake failure. This follow-up is source/race-qualified only and is NOT
inside the070b808 library/APK above. Rebuild latest source before any future runtime;
do not reuse either4e27ff23 or this intermediate070b808 binary as the final candidate.

Own AVDs/processes are stopped, shared emulator lock reacquired/released. Guest-only
rules vanish with those guests; host network, production, G4 and other processes are
untouched. The live fixture/credential workers were never started. All19 exact original
FAIL artifacts are rehashed unchanged. The previous provider room objects remain
deletion NOT_VERIFIED; this turn creates none. Source transport cause remains unknown.
Resume only when a safe thermal/resource window is available, through provider-free
Android JNI first, then fresh cold materials and the one authorized Connect.

[Sanitized checksums, preserved FAILs and all preflight outcomes](2026-11-06-cold-native-diagnostic.json).

#### Actual Android JNI PASS; live preflight stopped

6 November21:12UTC, continuation from
`6eb61a9faa659b6b07ac16bf9f4bac46a41cd2a7`, with no subsequent product-source delta.
The previously built070b808/af52aeb8 artifact is not reused. Latest source, including
underlay cause preservation and post-TLS cancellation classification, is rebuilt with
Go1.26/NDK28.2 for x86_64/API27, real Telemost, no transport-substitution tags.
ELF Android identification is27; seven JNI/Go provisioning exports are defined/global,
not undefined references. Both APK generations contain byte-identical current JNI and
the matching restricted-build manifest. Heavy builds finish before emulation begins.
Existing host-JNI,100 JVM and targeted race evidence is retained rather than rerun.

| Artifact | SHA256 |
| --- | --- |
| Latest JNI, source6eb61a9 | `17119f000407ec1d7ccdf8d33acabe423f3cf20e32b6f8af839d209aa3360c59` |
| Provider-free APK, installed on own API27 | `405f739958676a887bd2e74d4af522cab2fa9de14188bed731c1b0db0b310cbb` |
| Provider-free instrumentation APK | `3f4965c8195bc23b7a7795992e4f775f706307e61c455fd6934b0cb387f0eed5` |
| Final real-input cold APK, built but NOT installed | `79c4ea7bda4e8c7dbcab6abe13dc076fce5be4623910e1bc55606d99242cbbfc` |
| Final real-input instrumentation APK, NOT run | `bd230fc53ed70ce84e2dd353cb511b930af22811c1a0cd0594cad3ec5a0b4257` |

**Actual Android JNI: PASS.** Initial preflight samples CPU70/58/57°C and GPU53°C;
available memory16363692KiB and AVD data-filesystem space22907133952bytes. Shared lock
is held and no other emulator exists. Reuse only the task's provider-free userdata on
the corrected data filesystem, not the space-constrained worktree filesystem.
Actual API27/x86_64 GLES reports NVIDIA GTX1650Ti; host rendering/KVM, two guest cores,
own CPUQuota100%, existing CPU85°C/GPU80°C/180s guards remain. Observed peak83°C/59°C;
no guard abort. `ProvisioningDiagnosticRuntimeTest` completes one test successfully
(JUnit0.015s; instrumentation wall0.467s). It asserts JNI_ARGUMENTS with Go not entered,
Go-entered LOCATOR security rejection, CLOSED for handle−1, idempotent Close and the
saved diagnostic remaining unchanged after Close. This directly exercises Android/JNI,
not the host invocation shim. It does not open a provider socket, establish a carrier,
test a live asynchronous lease race, or imply TLS/readiness. The earlier host matrix
remains the evidence for those injected failures and concurrent lifecycle cases.

Only after that PASS, the existing protected local password dialog reads the same
authorized OAuth entry and pipes its value through process memory; no secret is written
to files/APKs/logs. A new test authority registers a synthetic identity and creates two
provider rooms. Native build has already finished. A new signed locator is verified by
the production `coldprovision.Verify` implementation, with400s remaining at initial
verification and316s before the runtime preflight. Final APK assets match the new
anchor/locator and synthetic identity exactly. No prior readiness or issuance material
is imported. The separate host verified-HTTPS egress expectation is a digest only;
it is NOT an Android/VPN HTTPS or egress result.

**Single cold Connect: NOT_RUN, authorization remains unused.** Before launching the
fresh runtime AVD, CPU samples68/80/86°C violate the unchanged85°C threshold. GPU is
56/56/57°C; available memory15740940KiB and data space22189363200bytes pass. The runner
records `FAIL_PREFLIGHT / THERMAL_PREFLIGHT`, does not start this emulator or install
the final APK, and stops its authority/workers. There is no retry/restart cycle.
The proven blocker is host CPU temperature at this preflight; it is not a diagnosis
of the original provisioning failure or proof of a Network race. The source setup
would reject only guest TCP185.251.89.19:8443 and186.246.45.246:4242, leaving other
carrier/control destinations intact; these new rules are NOT applied because the
guest never starts. AutomaticConnection200000ms candidate and separate30000ms readiness
remain unchanged. No new client provisioning Network/bind snapshot, carrier exchange,
TLS handshake, challenge transmission, bundle/READY, DNS, verified HTTPS or egress
exists. No runtime-negative tests are started. Authority counters remain0 challenges
and0 certificates. Provider API room creation is not client cold-path traffic evidence.

**Cleanup and retained evidence.** First own AVD is stopped; no emulator or own stand
process remains, the exact own authority container is absent, workers join, protected
input/supervisor exits0, shared lock is reacquired/released. The two new provider room
objects are retained privately; deletion is NOT_VERIFIED. The unbooted new AVD directory
and both APK generations remain local evidence. Both old FAIL_RUNTIME receipts and all
19 original artifacts are rehashed unchanged. No foreign processes, production/G4,
host network/cooling/power settings, public artifacts, subscriptions or admission are
changed. Both APK generations are disposable118, not a release/version rollout; no
production rollback is needed. No additional source fix is inferred from this blocked
runtime. Future execution needs a stable thermal window with the stand active and
new finite locator/assets, not a blind reuse of this locator or another restart now.

[Sanitized Android PASS, current artifact identities and stopped-live preflight](2026-11-06-cold-native-android-check.json).

#### Ordered runtime resource attribution

Continuation of documentation checkpointfce81ed with unchanged product6eb61a9 and
JNI SHA256 `17119f000407ec1d7ccdf8d33acabe423f3cf20e32b6f8af839d209aa3360c59`.
The accepted provider-free Android JNI gate is NOT repeated. No Go/native build or
host/JVM/race suite runs. Existing stand/verifier binaries and APK bases are verified
and reused. A local assets-only ZIP/zipalign/test-signing packager is prepared to avoid
Gradle compilation with the AVD; only syntax is checked, not runtime qualification of
that packager. No new final APK is produced, and earlier APKs are not overwritten.

The local runner adds bounded resource snapshots at preparation boundaries and guard
abort: named temperature sensors, memory, PID/process name and interval CPU. No command
lines, environments, secret values or browser content are collected. Prior pre-AVD86°C
evidence has no process CPU samples, so it cannot establish that event's load source.
This attempt starts exactly one existing own API27 AVD on the corrected data filesystem,
with NVIDIA/KVM, CPUQuota100%, unchanged85°C/80°C/180s guard and shared lock. Android
boots, actual NVIDIA renderer is verified, own test packages are removed, and no test
VPN/readiness remains. Before OAuth/rooms/workers, during wall-clock readiness observation
(as-run runner phase `ANDROID_BOOT`), the guard stops the AVD after34.035s.

| Guard-aligned observation | Value |
| --- | --- |
| First guard violation | coretemp `Package id 0` and `Core 5`:87°C, limit85°C |
| GPU / memory available | NVIDIA60°C;13860068KiB; neither guard fails |
| CPU sample interval | 3.072s;100% means one CPU core |
| Own emulator | PID3031862 `qemu-system-x86`:82.35% |
| Other processes, total | 226.62% |
| Largest other process | PID2937122 `Isolated Web Co`:79.09% |
| Next other process | PID19485 `firefox-bin`:68.35% |
| Other desktop processes | PID13381 `gnome-shell`:12.69%; PID16284 `ptyxis`:11.72% |
| Own builds / authority / Telemost-workers | No such running processes; not started |

This is a measured thermal conflict under concurrent AVD and desktop load, not proof
that one process alone causes a temperature or that the old pre-AVD abort had the same
cause. The next observation after stop reaches93°C; cleanup observation91°C, with no
QEMU remaining. Do not reinterpret the resulting `adb device not found`/CalledProcessError
as the primary cause: the earlier guard record retains87°C, stage, processes and elapsed.
Clock convergence was not completed (observed guest offset about10s); no clock change
is attempted. Server-worker co-load is NOT tested because that stage is never entered.

Connect is NOT_RUN/0 consumed, no OAuth read or new rooms/identity/locator, no assets-only
packaging/install, no new guest blocking rules or client carrier/TLS/challenge traffic.
Bundle/READY/DNS/verified HTTPS/egress remain unknown; no runtime negatives or new
product fix. Own runner and QEMU PIDs are gone, no emulator or own authority remains,
shared lock is free. Foreign processes, host network/cooling/power, production/G4 and
user/public APKs are untouched. Prior room deletion remains NOT_VERIFIED; this attempt
creates zero rooms. Both original FAIL receipts/19 artifacts and all checksummed accepted
Android PASS evidence remain unchanged. No automatic restart, host or phone migration.

[Sanitized process/stage evidence and local artifact hashes](2026-11-06-cold-ordered-runtime.json).
