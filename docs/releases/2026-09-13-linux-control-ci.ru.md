# CI Linux control health и повтор Android — 13.09.2026

## Результат

Source **d7c3d7943d9ab1bde214b4a37b7b421bcc38d5c5** в ветке
stage5-linux-control-preview содержит исправление control WG health и публичные
отчёты регистрации/диагностики/живого пилота. Прежний базовый commit9a23f72.
Основной dirty checkout не переключался. Только три code/test файла отличаются
от предыдущей приёмки; private state/keys/profiles в Git не включались.

| Source | Workflow / результат | Evidence |
|---|---|---|
|d7c3d79|Linux control success|[34747139792](https://github.com/Joker20380/family_connect/actions/runs/34747139792)|
|d7c3d79|phase0 success|[34747139671](https://github.com/Joker20380/family_connect/actions/runs/34747139671)|
|d7c3d79|AWG success|[34747139717](https://github.com/Joker20380/family_connect/actions/runs/34747139717)|
|d7c3d79|TCP success|[34747139660](https://github.com/Joker20380/family_connect/actions/runs/34747139660)|
|d7c3d79|Clients failure: Android failed, Windows/Linux passed|[34747139704](https://github.com/Joker20380/family_connect/actions/runs/34747139704)|
|9092594|Scoped Android diagnostic success|[34747632083](https://github.com/Joker20380/family_connect/actions/runs/34747632083)|
|9092594|Clients success: Windows/Linux/Android passed|[34747632066](https://github.com/Joker20380/family_connect/actions/runs/34747632066)|
|9092594|phase0 success|[34747632071](https://github.com/Joker20380/family_connect/actions/runs/34747632071)|

## Исходный отказ Android и доступная диагностика

Initial Android job103697028353 failed на шаге Real WG AWG TCP and Auto lifecycle
on Android emulator (08:16:32–08:21:24Z). Build/unit/lint не являются этим отказом.
Официальный job logs API вернул403; check annotation содержит только sh exit1.
Точный упавший testcase/причина первого запуска недоступны. Не объявлять его
исправленным дефектом Android или доказанным infrastructure flake.

Diagnostic source **909259406bb4721c21ad67c7cefceb66f2a6396d** добавляет только
`.github/workflows/android-diagnostic.yml` и `pilot/android-awg/report_ci.py`.
Scoped job копирует прежний Android job с теми же tests/assertions/timeouts;
добавлен always шаг публикации bounded JUnit summary в check annotation и artifact.
Профили/сырые логи/длинные encoded значения не публикуются; local extraction/redaction
smoke прошёл. Код приложений, транспорта и тестовые критерии не изменены.

Два последующих Android запуска прошли — scoped и автоматически запущенный Clients.
Это подтверждает acceptance на неизменённом app source, но не объясняет первый отказ.
Начальный failure остаётся отдельным наблюдением; повторять бесконечно для зелёного
статуса не требуется. Для следующего отказа теперь доступна публичная JUnit summary.

## Linux artifact и связь с живой приёмкой

Linux job103697028439: successful protocol/crash/arbiter/package suite, GTK
render/interaction/recovery/TCP install harness, paired и legacy six-file archives,
fresh pinned virtualenv, extracted CLI/GUI и extracted recovery.
Локально412 Python tests прошли предыдущим шагом; без новых runtime изменений
их не повторяли. Точное число CI tests не выводится из недоступных raw logs.

Check annotation Control preview SHA256 подтверждает
`FamilyConnect-Control-Linux-preview-66152538ee2a4f3e.tar.gz`, SHA256
`9c827f86f03d27705c46830758e114b3f7ef9796320d9e46f09672363de076f3`.
Он совпал с новым локальным CI checkout и комплектом успешного live config2/3 pilot.
GitHub artifact ZIP не скачивался: сверка выполнена по digest самого собранного
CI tar.gz в annotation. Manifest/digest не заменяет offline configuration signature.
Прежний bundlebc908a5f084a8bb6 не переписан; для новых live apply его не использовать.

[Живой pilot](2026-09-13-linux-control-pilot-pass.ru.md): apply/ACK, HTTPS/DNS,
crash после реального apply, recover config2, ACK/replay, GUI Disconnect/close.
MTU1280 прошёл, но контрольный возврат1420 тоже однажды прошёл: TD-1 не закрыт.

## Документация и следующий блок

Все публичные результаты сохранены в source commit, затем итоговый docs-only
checkpoint с `[skip ci]` содержит точные runs/jobs/digest receipts, текущие
STATUS/PLAN/README и [native binding plan](../stage5-native-binding.ru.md).
Docs-only checkpoint не меняет принятые runtime bytes.

Далее common interop vectors → native verifier → protected identity/journal/outbox
→ shared operation ownership → application boundary → RNS/background packaging.
Windows Wire16384 bytes и envelope65536 требуют отдельного bounded IPC контракта.
На Android Activity import/clear должен участвовать в той же ownership, что service.
Нативные транспортные CI не являются native Stage5 acceptance: этот код ещё не создан.

## Версии, возврат и оставшиеся проверки

Installed Linux0.2.8, previous0.2.7; ранее опубликованы desktop0.2.9/catalog8,
gateway0.2.1/TCP0.1.0. Нет release/catalog/main merge/install/server mutation.
Последний live journal IDLE/floor3/committed2/outbox0, pending=null, все VPN выключены,
три pilot profiles неактивны. В CI-шаге состояние сети устройства не менялось.

Следующая configuration revision≥4 с previous hash committed config2; при expiry
продлить gateway lease и подписать новый envelope. Не сбрасывать identity/journal/floor.
При pending использовать recover тем же journal; installed GUI запускать только
после успешного recovery. Gateway lease до08:43:59Z13.09, configs до08:40:14Z;
фактическое удаление peer после expiry здесь не наблюдалось.

Открыты первый Android CI failure неизвестной причины, TD-1 size-sensitive loss,
AWG3.1, native Stage5 и Stage6 independent entry. Длительные/device tests не запускались.
CI содержит предупреждения о deprecated Node20/action setup-java; они не менялись
в этом fix и остаются отдельным обслуживанием.

Scoped Android JUnit summary: {"instrumentation_cases": 3, "failures": [], "hints": []}
