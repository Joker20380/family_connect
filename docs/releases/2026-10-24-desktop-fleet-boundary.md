# Desktop parity106 / fleet boundary — документационный checkpoint, 24.10.2026

**Документация закреплена; реализация D05 QUEUED, проверки D05/fleet NOT_RUN.**
Вход: чистая `main`, HEAD = проверенный `origin/main`
`a0bbcfcadef10f443c5a143aa270bfca86c115d5`. D02.1-R уже сохранён отдельно:
code `85b29dabbff6fb7387c3be0aceb24ca7de4e4848`, docs `a0bbcfc…`, **PARTIAL**;
historical suite NOT_RUN из-за неподтверждённых retained artifact pins. Его изменения
не смешаны с этим checkpoint и не продолжаются. D01/D02 и общая CI-приёмка открыты.

## Закреплено сейчас

Нормативный [планируемый desktop/provider контракт](../desktop-architecture.md#desktop-fleet-boundary)
разделяет страну, локальный target ID, подтверждённый gateway_id, транспорт, requested
P0/P1 и активную generation; preference, verified assignment и applied session — отдельно.
Legacy Friends остаётся строгим RU/NL/two-gateway adapter без выдуманного gateway_id;
подписи/floors, доказательства fetch/inspect/validate и privilege boundary не ослабляются.
Refresh списка не вызывает configure/apply/reconnect. Смена — через существующего owner,
с cleanup/cancel/fencing; MESH/chat borrowing сохраняет проверенный native profile context.
Linux source/readback не объявляется Windows runtime evidence; общий Windows Go Auto — W02.

Свободный ID **D05** добавлен после D04, зависит только от D03/D04, не от live fleet,
VPS/F-01 или W01/W02. Модель/provider boundary реализуются через существующие Linux
auto_configuration/auto_platform/native normal и Windows FriendsOwner/broker boundaries.
Продуктовая Windows-интеграция — W01/W02, UI — L07/W09, упаковка/capabilities — L03/W10,
миграция identity/history/settings — L08/W12, установленная приёмка — L04/W11/R01.
L01/L02/W04 не расширены до произвольного служебного сетевого доступа.

## Критерий и проверка checkpoint

[D05 завершится](../desktop-architecture.md#desktop-fleet-acceptance) после адресного доказательства
разделения сущностей, выбора по ID на synthetic 2×NL+DE при refresh/reorder, отсутствия
apply/reconnect при refresh, отбрасывания stale callback, сохранения строгих legacy
отрицательных проверок и достоверных capabilities. Такой fixture не доверенный assignment
и не принимается legacy wire verifier; model PASS не заменит установленные gates/F-01.

Проверены согласованность формулировок, относительные ссылки/anchors, уникальность D05,
отсутствие циклов в desktop task dependencies и `git diff --check`. Только пять Markdown
документов: architecture, PLAN, STATUS, README и этот отчёт. Продукт, тесты, schemas,
IPC, build settings, accepted106 pins и исторические evidence не менялись.
Pytest, сборки, эмулятор и live/fleet проверки **NOT_RUN**, как предписано scope.
Новые D05 tests ещё не реализованы. Старые CI результаты не присваиваются этому commit.

Версии не менялись: Linux0.2.11 / Windows0.2.15, reference Android106. Deploy/publication/
rollback не выполнялись, существующие подключения не тронуты. Server leases/renewal,
production fleet, signing workflow, новые VPS, Telemost multi-gateway и Django отдельно.
Это не закрытие D01/D02/D05/fleet. **NEXT основной очереди: D02.2 после review коррекции
D02.1-R. После документационного commit/push остановиться, без автозапуска реализации.**
