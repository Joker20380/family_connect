# 24 November 2026 — current-content audit handoff and stage2 endpoint

Source `174f525a632ebbb7aa0cc6798090030a69d93420` ordinarily pushed and independently
remote-SHA verified on `feature/device-technical-metadata-20261115`.
Authoritative code/full report: `/home/joker/.codex/worktrees/dad9/family_connect`.
This older divergent main remains navigation only; do not deploy it or overwrite
the original four dirty files/six untracked paths to reconcile its history.

The selected actual-installed-current gate is **IN_PROGRESS**, not complete. New
read-only audit authenticates full legacy custody, preserves unequal ledgers and all
opaque bytes, and checks native scheduled COMMITTED state, service snapshots/start
intents, signed material, both NL publications and the five-table current DB projection.
Native controller/SystemdBarrier fixtures use generated local data and simulated
service calls; source trees are deleted before readback. No production journal export,
SSH, service restart, import/replay/host resume or installed acceptance occurs.

Every matching content audit still returns recovery BLOCKED. The native transaction
records a schedule decision, not original approval/configuration custody. Caller unit
order is unproven; start intent does not establish service liveness; separate state
inputs are not an atomic capture. No override flag was added. Continue this same task
with original provenance and actual installed capture evidence, not another variant.

Qualification:56 new tests /0 skips;111 stopped regressions /15 explicit PostgreSQL
skips;45 custody regressions /0 skips. Total212 PASS in151.52s. PostgreSQL was not
started or requalified. Six source docs/1007 local links and whitespace PASS.
Private JUnit: `/tmp/fc-control-ha-20261124/current-audit-regressions.xml`.

## Когда закончится этап 2

Не после ещё одной буквы или нескольких тестов. В authoritative `docs/control-ha.md`
закреплены четыре приёмочных результата:

1. Журналы: фактическая текущая операция и происхождение разрешения проверены;
   старая история сохранена без выдуманных approvals. **Частично.**
2. Установленные схемы и writers: согласованный снимок всех stores с барьером,
   без смешанных писателей. **Не квалифицировано.**
3. Полное восстановление: off-host данные/ключи/checkpoints и изолированное актуальное
   recovery после новых подтверждённых записей. **Не квалифицировано.**
4. Репликация: loss/return primary, отказ записей без кворума, отсутствие потерь
   подтверждённых событий (RPO0). **Не квалифицировано.**

Этап2 закрывается только совместным PASS этих четырёх результатов. Календарный срок
пока не подтверждён измерениями; обещать «ещё один шаг» нельзя. После него остаются
HA-03 fencing, HA-04 API/client failover и HA-05 shadow/cutover. RU dependency remains.

Latest known console5ce82415, NL GeoIP22 November20:53:48UTC, installed renewal e9fd3175,
Android126/catalog9 and public/invitation versions unchanged; no new health claim.
8/12/120s and all-three-node ACK unchanged. Rollback: stop using/revert only the source
audit, preserve custody receipts/native evidence; no host rollback or old DB restore.
