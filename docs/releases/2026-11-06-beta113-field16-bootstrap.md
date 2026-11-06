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
