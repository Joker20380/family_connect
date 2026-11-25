# HA-02 — стабилизация support и CI, 25 ноября 2026

**IN_PROGRESS, не приёмка совместного handoff и не deployment.** Main содержит только навигацию.
Рабочая ветка `feature/device-technical-metadata-20261115`, опубликованный checkpoint
`f6c6171e022fbf2b671e7c950671a556a7fdeb79`; обычный push и remote SHA проверены.
[Полный исходный отчёт, evidence и ограничения](https://github.com/Joker20380/family_connect/blob/f6c6171e022fbf2b671e7c950671a556a7fdeb79/docs/releases/2026-11-25-control-ha-support-stabilization.md).

## Shutdown и terminal failure

Исходные failed receipts и JUnit с WORKERS_REMAIN сохранены локально без изменения.
Старый отказ не содержал census: **его конкретная историческая причина не доказана**.
Управляемый pipe-синхронизированный сценарий показывает исчезновение owned worker из Python
enumeration при ещё живом native TID. Исправление удерживает явное владение final-persistence
workers, join и kernel retirement; три only_main точки сохраняют ограниченную диагностику фаз,
владельцев, Python/native множеств и последнего шага, без payload/ключей/locals.
Неполный снимок помечается, native tasks не игнорируются, таймауты не увеличены ради PASS.

Необратимая ошибка теперь сохраняет исходную причину и hashes evidence в существующем
MANUAL_RECONCILIATION_REQUIRED outcome, exit78 прекращает автоматические перезапуски.
Witness/open/capture/candidate/повторный старый writer на этом пути запрещены.
65 целевых проверок,1 native terminal и3 actual-root/fc-support проверки PASS без пропусков;
новый переносимый test ptracer отдельно проходит2 user-systemd проверки без изменения host policy.

## CI на точных SHA

- `762f2d65`: panel/messenger/notifications/golden PASS; phase0 tests FAIL, control CANCELLED.
  Сохранённый native stderr доказывает Docker exit125/No such image для локального образа.
  На a39/595 первичный stderr отсутствовал: причина не приписывается им задним числом.
- `a6f7c730`: исправлены исторические overlay sources/package closure, но phase0 tests ещё FAIL.
- `1c24d595`: воспроизводимый networkless fixture, launcher context и reversible notice delta
  опубликованы; на момент нового checkpoint полный CI не был принят.
- `f6c6171e`: Windows control conformance PASS; phase0 `45709173975`, control `45709173914`,
  native support `45709174045`, golden и client builds ещё выполняются на21:59UTC.
  Native job уже прошёл bootstrap/GIL/baseline/user-manager и запустил тесты. Только завершённый
  zero-skip receipt на этом SHA может подтвердить его PASS; незапущенный/незавершённый job не PASS.

Локальные уточнения, не сумма и не замена полного CI:592 PASS/31 явный PG skip по десяти
native-maintenance семействам; networkless UID0 helper PASS; launcher/context131 PASS и финальные
context29 PASS; notice reference/authorization/publication83 PASS/40 PG skips; exact support
baseline/export10 PASS. PG skips не являются приёмкой PostgreSQL. Исходные accepted hashes не
заменены: reviewed HA notice delta обязан обращаться в точные исходные bytes.

## Что установлено и что осталось

Независимый read-only readback21:59:29–30UTC: OWNER active/running PID2022541/0 restarts,
все19 исходных файлов совпадают с baseline; NL1 active/running PID3705/0 restarts,
relay/server/codec/membership pins неизменны, daemon reload не требуется.
Рабочий candidate9d7bf840 **не установлен**. Новых версий, deployment, mailbox opening,
capture permit, удаления reservation, очистки UNKNOWN или изменения подписочной очереди нет.
RU/NL2/соседние сервисы не изменены; временный sudo-кэш аннулирован.

**Один следующий результат:** общий resumable handoff/reclosure/recovery с pause очереди,
независимым closed/drained readback, authenticated witness consumption, подтверждённым opening,
reclosure/drain/invalidation и recovery на критических crash/restart/lost-response границах;
полный применимый CI, затем уже разрешённая рабочая установка и readback. Этот исполнитель
ещё не реализован и не квалифицирован; отдельные helper PASS его не заменяют.
Возврат кода не может восстановить старые данные или обойти reservation.

Три прежних критерия HA-02 сохраняются без расширения этапов:
1. Текущие фактические inputs/authorization/trust и журналы.
2. Установленные схемы, все writers и единый coherent cross-store capture.
3. Независимый machine-loss комплект и полное актуальное восстановление после новых ACK.

Изолированная репликация остаётся PASS. FLEET-PRODUCTION-ONBOARDING-1 остаётся обязательным:
VPS → IP/доступ/роли → штатный ввод → проверенный активный узел. Миграция support не закрывает
этот контракт и весь HA-02.
