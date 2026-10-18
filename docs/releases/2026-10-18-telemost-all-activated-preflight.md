# Telemost: общий допуск активированных устройств —18.10.2026

**RESULT=LOCAL_API_CANDIDATE; NOT_DEPLOYED; REQUEST_UNFINISHED.**

Later task boundary,18.10: the owner selected the name **MESH** and explicitly
limited that task to product integration without crypto, timeout or infrastructure
changes. The earlier access work is preserved, not deployed or accepted by the
[MESH report](2026-10-18-mesh-product-integration.md). Local experiments also exist
in `deploy/friends/restricted/maintenance/`, `offline/sign_authority.py`,
`install_bridge_access.py`, `scripts/build_bridge_access.py` and
`tests/test_activated_maintenance.py`. Their activation-v2 management and proposed
longer offline-authority validity require separate review; they are not a naming
change, not a production fix, and not authorization to publish or renew anything.
The discarded-name «Мост» source candidate was never built/signed/distributed.
No production mutation, gateway restart or offline signing was performed.

Первичная read-only проверка завершена до07:03:28UTC; затем пользователь уточнил,
что нужно переписывать схему, а не ремонтировать ручную выдачу. Ниже сохранены
наблюдения preflight и отдельно результаты последовавшей локальной реализации.
Пользователь разрешил открыть Телемост всем активированным пользователям Family
Connect, оставив выдачу APK нужным тестировщикам вручную. Это не запрос на
анонимный VPN, отключение отзыва/проверки личности или публичный релиз APK.
Повторное разрешение на расширение когорты не требуется.

## Исходное состояние и точная проблема тестера

Корневой checkout HEAD8d04632 содержит многочисленные незакоммиченные изменения;
они сохранены. Более свежая история текущего тестера обнаружена в существующем
чистом review checkout
`state-client-build/owner-cumulative-client-acceptance-1-resume/review-publication`,
HEAD947d816 от17.10. Его STATUS/PLAN и отчёты
`2026-10-17-field-1-volgograd-grant-preflight.md` /
`2026-10-17-field-1-volgograd-export17.md` прочитаны. Review checkout не изменён.

- По export17 тестер уже получил batch1/code84, Android14/API34. Это не отсутствие
  доставки APK: сервер оставил регистрацию NOT_PROVISIONED, field_admission=false.
- Установленный старый FIELD operator SHA256
  `b6fe9220590524905cd98580c083bfd985d80cd5d01391ae7c2b5c4152c995b7`
  проверяет длительность CRL максимум3600s; действующая политика —14400s.
- Его publisher также фиксирует900s. Нельзя только пропустить старую проверку:
  запись укоротила бы общую политику отзыва.
- Четыре часа — срок служебного криптографического материала, **не лимит работы
  установленного APK**. Отдельно действуют серверный допуск и обновление материала.
  Приведённая причина отказа выдачи историческая; она не заменяет свежую readiness.

## Свежие read-only наблюдения RU

Использован только разрешённый185.251.89.19:/opt/apps/family_connect. Исключённый
хост и соседние сервисы не затрагивались. Клиентские ключи/профили/строки базы
не выводились; SQL только mode=ro/query_only, вывод только агрегированных чисел.

- `family-connect-friends-access.service` inactive — не работающий API.
- Фактический `family-connect-friends-http-candidate.service` active, PID1921548,
  NRestarts0, порт18086; архив `http-publisher-research74-20261010.pyz`, SHA256
  `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed`.
- `admission.json`: mode0600,86bytes, два явных устройства, wildcard отсутствует.
  Два grants, ноль revoked и ноль expired на момент агрегированного чтения.
- Renewal/health services failed; соответствующие timers active/waiting.
- Штатный `runtime_controller.py --mode evaluate` завершился exit1 с
  `FAIL_CLOSED`, `CRL_EXPIRED_OR_FUTURE`, `automatic_retry=false`.
  Последний прочитанный renewal journal сообщает ту же причину.
- Код ошибки сам по себе не различает expired и future CRL; точные интервалы
  текущего CRL/issuer/leaf и свежая цепочка NL не прочитаны. Не утверждается,
  что offline authority уже истекла или что известна причина сбоя расписания.
- На RU7.8GiB свободно,73% used. Это не проверка нагрузки/здоровья всего VPN.

Первый SSH в sandbox не стартовал из-за permissions системного ssh_config;
повтор выполнен через разрешённую эскалацию. Два последующих соединения получили
banner timeout; ограниченный повтор source-read/evaluate успешен. Одно чтение
journal оказалось медленным и завершилось; дальнейшая оценка ограничена40s.

## Почему не применён один wildcard

Штатный HTTP допускает `devices:["*"]` и при первом authenticated challenge
автоматически создаёт grant только для существующей активной device/invite пары.
Проверки существующего revoked/expired grant не снимаются. Но `_enroll` создаёт
новую запись с `expires=NULL`.

Прочитаны только Python-модули установленного management controller, без его
конфигураций/ключей/базы. `credential_renewal.Validator.validate` требует integer
expiry; `grant_cutover.GrantDatabase.plan` отвергает NULL как
GRANT_EXPIRY_CONTRACT_REQUIRED. Expired recovery дополнительно связывает grants
с предыдущим committed checkpoint и не предназначен для добавления новых членов.
Смена одного JSON-файла создала бы несовместимое состояние после первого нового
запроса. Это не утверждение, что wildcard вообще не поддерживается HTTP API.

Прочитанные management hashes:

- credential_renewal.py:
  `fb83d851b4ac88b7ad90b97c59f516ee327bc7bbb92a642a031da08bbc50d25c`.
- runtime_controller.py:
  `73c3784855f8fb53140d3ddfdcc7f693cad080c84b3fbec1481f91b2dc076c59`.

## Что осталось сделать

1. Завершить management-часть all-activated workflow. Локальная API-часть теперь
   реализована, но установленный current4h planner требует legacy grant для каждого
   сертификата. Нужно разделение entitlement/credential lifetime в контроллере,
   общий предикат допуска, привязка режима к двум узлам и durable checkpoint/recovery.
   Не использовать renewal как неявную выдачу нового entitlement.
2. Локальная проверка exact current4h contract: положительная выдача, неверная
   подпись/привязка, revoked device/invite/grant, истечение, гонки регистрации и
   renewal, сбои публикации/восстановления и rollback без отката security floors.
3. Свежая диагностика сроков и восстановление текущей цепочки штатным coordinated
   controller; offline подпись только существующим ключом на локальном хосте,
   если требуется authority renewal. Никакой перенос root key на сервер.
4. Контролируемое применение совместимого допуска и live readback обеих сторон;
   затем refresh/ACK выбранного тестера через работающую сеть. E2E Телемост
   проверять отдельно, не объявлять его PASS по одному серверному допуску.

## Версии, проверки, rollout/rollback

Production install/sign/deploy/restart/renewal/grant/admission/CRL writes0,
APK публикация0, ADB/CONNECT0. После уточнения выполнен локальный API source patch
и сборки временных HTTP/sync архивов внутри тестов. Релизные артефакты не создавались.
Built/installed/public/invitation версии клиентов этой задачей не изменены;
batch1/code84 у тестера — сохранённое свидетельство17.10, не свежая аттестация APK.
Публичные downloads/catalogs не перепроверены и rollout complete не заявляется.

Ничего не раскатывалось, rollback не применялся. Будущий rollback должен
сохранять новые revocation/floor/checkpoint; возврат старых expired материалов
или одной admission.json не является безопасной процедурой восстановления.

## Продолжение: entitlement v2 переписан локально

Новая явная operator policy `{"version":2,"eligibility":"all_activated"}`
отличается от старого wildcard. `control/friends/restricted.py` выводит право
доступа из действующей ordinary activation без создания restricted_grants.
Это не бессрочный сертификат: proof, identity/WG binding, nonce/replay, issuer/CRL/
directory validity, криптографические лимиты14400s и floors не изменены.

Старый конечный FIELD expiry больше не ограничивает entitlement в **явном v2**,
но исходная строка сохраняется. Revoked device/invite/grant, wrong Family и revision
ниже signed minimum остаются deny; повышенная существующая revision сохраняется.
Legacy policy по умолчанию продолжает прежнее поведение. Новая политика не
принимается из HTTP-запроса. Unknown/mixed/duplicate schema fails closed.

`support_ids.py` / read-only `support_admin lookup` различают ELIGIBLE и фактическую
readiness. Старый FIELD writer не может перезаписать v2 policy. Обычная активация,
identity, Android/native и transport код не изменены этой дельтой.

Добавлены31 целевая проверка в двух новых файлах:
`tests/test_restricted_activation_policy.py` и
`tests/test_restricted_activation_http.py`. Проверены existing/new recipients без
grant writes, сохранение отзывов и binding/revision, challenge/fetch revoke, replay,
возобновление выдачи после обновления материала более чем через4h, CRL inclusion,
support semantics и настоящие proof/fetch HTTP-запросы к закрытому архиву на loopback.
Успешная выдача с синтетическим14400s CRL проверена отдельно от default1h fixture.

Итоговый выбранный набор pytest: **217 passed,25 skipped,4 deselected,11.89s**.
Команда использует `-k 'not backend_delivery_consumed_by_native_material'` для
девяти модулей: двух новых, test_support_ids, test_friends_restricted,
test_restricted_clock_skew, test_restricted_test_window, test_readiness_receipts,
test_friends_http_runtime, test_restricted_runtime. Skip reasons:11 Go/native
validator fixtures без FC_TEST_GO,13 nginx fixtures без FC_TEST_NGINX,1 pinned-sync
interop без FC_TEST_SYNC_ARTIFACT. Четыре native delivery cases исключены явно.
Это не полный suite, hosted CI, Android/native acceptance или клиентский E2E.

Окружение найдено в
`state-client-build/field65-export16/telemost-admission-ownership-1/build/venv`:
pytest9.1.1/cryptography46.0.7; проверены все26 pinned packages control/identity
lockfiles, несовпадений0. Системный Python из preflight для тестов не использован.

Сохранённые ограничения/первичные ошибки:
- Первая новая CRL-проверка ожидала now+14400, не учитывая inherited issuance skew;
  тест исправлен на точную длительность14400s и допустимый верхний предел. Runtime
  или skew-политика ради теста не менялись.
- Sandbox отверг loopback sockets; разрешённый вне-sandbox повтор выбранных HTTP/
  runtime модулей прошёл. Production/провайдерские подключения тесты не создают.
- Отдельно запрошенный test_readiness_adapter_packaging не имел обязательных
  FC_TEST_HTTP_ARTIFACT/FC_TEST_GO; он не входит в итоговый выбранный PASS и не
  объявляется проверенным. Это frozen-fixture/operator suite, не новый API пакет.

Проверка whitespace diff без замечаний. Локальные проверки не разрешают подключить
новую API policy к старому live controller. Следующий конкретный шаг — management
rewrite из [контракта v2](../../deploy/friends/restricted/ACTIVATED_ACCESS_V2.md),
затем совместная миграция/recovery и ограниченная проверка тестера. Общее live-право
доступа этой задачей пока не включено; APK раздаётся по решению владельца, не нами.
