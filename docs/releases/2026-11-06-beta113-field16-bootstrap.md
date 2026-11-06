# beta113 / API28 — отдельный полевой отказ начального подключения

## Статус и границы входных данных

**SOURCE_AUDIT_COMPLETE / FIELD_CAUSE_UNRESOLVED.** Это отдельный клиент, не телефон
владельца, не isolated G4 и не проверка исправленного live MESH. Продуктовый код,
классификация ошибок и серверы не изменены. Нового APK, AVD, транспорта или endpoint нет.

Запрошенный `FamilyConnect-diagnostics (16).json` для beta113/API28 в доступных локальных
файлах не найден. Похожий `FamilyConnect-diagnostics(16).json` относится к **beta65/API31**;
он исключён, его идентификаторы и события не использованы. Следующие признаки — данные
из сообщения владельца, **не независимо прочитанная последовательность нужного JSON**:

- beta113, API28, CELLULAR; `cache=MISSING`;
- `CHALLENGE / CONNECT_TLS_WRITE / HTTPS_UNDERLAY / TIMEOUT`, HTTP-ответ не зафиксирован;
- `RNS / RELAY_OPEN / UNAVAILABLE`, `readiness=FETCH_FAILED`, `directory=NOT_USABLE`;
- `restricted_descriptor=NOT_ATTEMPTED`, затем AUTH и INTERNAL без раскрытой причины;
- окна по часам телефона: 2026-11-05 09:31:20–09:34:43 UTC и
  2026-11-06 11:59:26–11:59:37 UTC; Support ID отсутствует.

Часы телефона не сверены. Identity, оператор, регион, выбранный gateway и принадлежность
поздних категорий той же попытке **не устанавливались и не угадываются**. Отсутствие
Support ID не заменяется поиском похожего пользователя. Raw export/ключи в Git не попадают.

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

По предоставленным событиям первый отказ — **истёкшее ожидание readiness challenge до
записи HTTP status**. Это ещё не получение readiness, не Family TLS handshake с NL и
не отказ серверной авторизации. Причина сетевого ожидания пока неизвестна.

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

Отзыв Android VPN consent сторонним VPN — допустимая гипотеза для AUTH, но без
события onRevoke/consent и привязки к той же попытке это не установленный факт.
Точный источник поздних AUTH/INTERNAL требует правильного JSON: component/event,
policy reason, attempt ID, started/completed connection ID, connection_changed и
непосредственно предшествующие owner/cleanup события. Если их нет в113 export, нужен
узко ограниченный диагностический признак причинной ветви, а не переклассификация.

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

**Точный недостающий различитель:** для той же challenge attempt нужны выбранный
`network_type` и `network_generation` (в113 это **Network handle, не счётчик поколений**),
её NOT_VPN/INTERNET/VALIDATED и факт lost/замены к моменту ошибки, отдельно результаты
TCP-connect, TLS-handshake и получения HTTP status. Общий CELLULAR телефона и метка
HTTPS_UNDERLAY не заменяют этих данных. ReadinessFetchTrace уже содержит handle/type,
а DiagnosticRing — connection_changed; сначала следует прочитать их в правильном файле.

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

No installation/rollout/rollback is performed or needed for this documentation-only
audit. APK118/updater113, subscriptions, certificates, admission, G4 and frozen artifacts
are untouched. Earlier failed runs and unrelated local changes remain. **Next: correct
beta113/API28 export plus the single comparison above**, not another speculative APK.
