# PUBLISH-SUPERVISOR-RESEARCH-STATE-1 — указатель review-публикации

Repository: **Joker20380/family_connect**, ветка **review/supervisor-state-20261015**.
Это публикация существующей работы для чтения, не diagnosis/patch/acceptance/release.
Production FAIL сохраняется; root cause не доказана. Сначала чтение, затем отдельное
решение о следующем шаге. EXACT-LOCAL-TESTABILITY и A/B/C здесь не продолжаются.

## Начать здесь

- [Restricted chat → VPN handoff — локально реализован](2026-10-15-restricted-chat-vpn-handoff-1.md):
  новый отдельно разрешённый product patch в изолированной research84 derivative,
  не правка архивных snapshots/root main. [Diff, before/after files, tests, runners](../../research/chat-vpn-handoff-20261015/README.md)
  и фиксированные normal/race/build receipts опубликованы для review. Это расширение
  первоначальной publication-only задачи; source SHA APK и frozen identities прежние.
  Native/Java compile PASS не является device acceptance; historical binding
  NOT_PROVEN и production FAIL сохраняются. Бинарники/полный retained Android build
  context остаются локальными, как явно описано в отчёте.

- [Штатный support export — EVIDENCE_RECOVERED](2026-10-15-owner-support-export-and-triage-1.md):
  получен один указанный владельцем JSON; ring/incident содержат matching C1/I1.
  Complete startup FAILED на HELLO_RECEIVE доказан до descriptor/dedicated startup,
  причина UNKNOWN. Опубликованы только обезличенные выдержки, timeline, schema limits
  и source-gated вывод; raw JSON/alias mapping приватны. Прежний WAITING checkpoint
  сохранён в истории d2ae9b7b179803101ce928692b1838fd4ac104f5. Production FAIL и
  root cause NOT_PROVEN сохраняются; старые reports/frozen snapshots не переписаны.
- [Retained owner diagnostics — ACCESS_BLOCKED](2026-10-15-owner-episode-retained-diagnostics-1.md):
  отдельная ограниченная read-only проверка после исходной публикации
  `f5d7a4b156f66f2ce38fe7976d99f6f39678bb00`. APK research84 подтверждён; app-private
  JSONL недоступен разрешёнными способами, штатный export не запускался из-за
  удаления прежних exports. Historical invocation journal не вернул записей.
  Новых owner-native records/binding/READY/counters не получено; FAIL и NOT_PROVEN
  не изменены. Публичны только безопасные выдержки и таблица пределов вывода.
- [Основной rootcause report — PARTIAL](2026-10-15-supervisor-candidate-dataplane-rootcause-1.md).
- [Production episode — FAIL, единственный rollback](2026-10-15-seed-supervisor-owner-acceptance-3-final.md):
  byte-identical копия существующего episode-90m/REPORT.md, SHA256
  `279da0be4e71f99ef0e9112d33131f76fdce1dfc028d0fc43607350e8d696ba2`.
  Его прежняя интерпретация TUN уточнена rootcause report, не переписана задним числом.
- Актуальные [STATUS](../STATUS.md) и [PLAN](../PLAN.md): текущие локальные документы
  плюс короткая запись об этой публикации; их остальные незавершённые задачи не возобновлены.
- [Supervisor acceptance](2026-10-13-gateway-seed-supervisor-1.md),
  [trigger acceptance](2026-10-13-gateway-seed-supervisor-trigger-1.md),
  [predeploy](2026-10-13-gateway-seed-supervisor-predeploy-1.md),
  [deployment entry](2026-10-13-gateway-seed-supervisor-deploy-1.md),
  [operational readiness](2026-10-13-gateway-seed-supervisor-op-readiness-1.md).
- [Original WS1011 boundary](2026-10-12-gateway-ws-1011-continuity-1.md),
  [same-room proof](2026-10-12-gateway-same-room-rejoin-proof-1.md),
  [real-provider capability](2026-10-12-telemost-real-same-room-rejoin-1.md).
- [Research84 provisioning seam](2026-10-12-whitelist-provisioning-block-seam-1.md),
  [installed research84 EN](research84.en.md) / [RU](research84.ru.md).

## Frozen identities и доступность Git commits

Значения взяты из существующих manifests, не из нового publication HEAD.
Полная безопасная проекция: [source-identities.json](../../research/supervisor-20261015/source-identities.json).

| Объект | Реальная source identity | Binary SHA256 |
|---|---|---|
| Working baseline | `a4087e000fdbe674b72ede3a6c8822445c87c654` + classifier delta `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`; preserved source snapshot `471d1d62e1385a9ffc5ff6a16a5a7e9fe043fae2` | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Accepted supervisor parent | `c9d75db6020f9f605e891036cbb9b68cebede708` | `d6875817cf33fdd85c6ad78a342fc93afd16864293e94a6e5b7136eec5125765` |
| Failed frozen candidate | `134083d87773dacc038c9593afdaff0c57ea951d` | `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f` |
| Research84 Android | base `f5240994869826c6a28f59e58e38256c688cf6eb` + delta `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7` | reused native `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2` |

Опубликованная ancestry начинается с фактического local HEAD/public main
`8d046321039d0bd1e18ecc1af979ff90f591e029`; неопубликованных ancestor commits на входе нет.
Доступен новый **publication source snapshot**
[`b896f63da15e1ae6b8eef35aadcba1090d6c8baf`](https://github.com/Joker20380/family_connect/commit/b896f63da15e1ae6b8eef35aadcba1090d6c8baf),
затем documentation commit этой ветки. Ни один из них не является source SHA бинарника.

Изолированные истории a4087e0/471d1d6/c9d75db/134083d8/f5240994 **не импортированы**
в ancestry review-ветки. Перед публикацией GitHub Git Commit API вернул404 для
a4087e0,134083d8,f5240994; ссылки на эти commits не предлагаются как доступное evidence.
Вместо недоступной истории опубликованы exact source-file snapshots и recorded diffs.
Для c9d75db сохранена цепочка baseline → supervisor behaviour/observability diffs,
не отдельный Git commit object. Бинарники и исходные Git bundles остаются локальными.

## Где читать исходники и существующий local stack

Общий [README](../../research/supervisor-20261015/README.md) и
[per-file inventory с origin/SHA256](../../research/supervisor-20261015/source-inventory.json).
Это архивные source namespaces; корневой product source остаётся checkpoint8d046321.

| Проверяемый вывод | Опубликованные файлы |
|---|---|
| Exact baseline differential | [baseline/carrier](../../research/supervisor-20261015/baseline/carrier),226 files; [frozen-candidate/carrier](../../research/supervisor-20261015/frozen-candidate/carrier),243 files |
| Startup/config/context | candidate [main.go](../../research/supervisor-20261015/frozen-candidate/carrier/cmd/bootstrap-broker/main.go), [seed_supervisor.go](../../research/supervisor-20261015/frozen-candidate/carrier/bootstrap/seed_supervisor.go), seed.go/seed_overlap.go/seed_security.go и tests в соответствующих каталогах |
| Dedicated ownership/READY/Mux | candidate [gateway.go](../../research/supervisor-20261015/frozen-candidate/carrier/roombroker/gateway.go), broker.go/lease.go, wholedevice/session.go, familysession/ и tcpforward/ |
| Acceptance policy/seed bridge | [seed_acceptance_linux.go](../../research/supervisor-20261015/frozen-candidate/carrier/bootstrap/seed_acceptance_linux.go), [acceptance_linux.go](../../research/supervisor-20261015/frozen-candidate/carrier/telemost/acceptance_linux.go), matching disabled implementations и tests |
| TUN до dedicated READY | research84 [AutomaticVpnOwner.java](../../research/supervisor-20261015/research84/clients/android/app/src/main/java/com/familyconnect/app/AutomaticVpnOwner.java), AutomaticConnection/RestrictedTunnelEngine/ConnectivityOrchestrator и существующие unit tests; [native main.go](../../research/supervisor-20261015/research84/pilot/android-restricted/native/main.go), packet/ и wholedevice/ |
| Existing local real-Pion stack | [семь overlay files](../../research/supervisor-20261015/local-stack-overlay/carrier), включая bootstrap/rejoin_capability_test.go, internal/rejoinfixture/provider.go, metadata/TLS/dial hooks; [original validation script](../../research/supervisor-20261015/provenance/trigger/validate.py) |
| Исторические source acceptance и отделение behaviour/observability | [provenance/trigger](../../research/supervisor-20261015/provenance/trigger) и [provenance/supervisor](../../research/supervisor-20261015/provenance/supervisor) |

514 существующих source/provenance files скопированы byte-identical; source snapshot
добавляет только README, identity/inventory metadata и три небольших result receipts.
Research84 — selected source slice, не полный APK build tree. Семь overlay files
накладываются на frozen carrier subtree для представления retained validation source.
Этот stack требует fixture rebuild; это **не exact-binary A/B/C adapter**. Ничего
не строилось, не запускалось и не исправлялось. Historical runner paths не адаптированы.

## Что является доступным evidence

Опубликованы существующие отчёты и [три bounded receipts](../../research/supervisor-20261015/receipts):
production result projection, rootcause result projection, historical trigger-test
differential. Их PASS/FAIL/NOT_RUN относятся к исходным задачам, не к этой публикации.
No owner READY/packet evidence добавлено или выдумано.

Supplemental retained-diagnostics task публикует только новый отчёт и обновления
STATUS/PLAN/этого указателя. Raw ADB/journal receipts, копии прежних diagnostic
receipts и provenance находятся в отдельной private capsule, не в исходном seal.
Полные exact research84 StartupDiagnostics/Diagnostics/DiagnosticsProvider прочитаны
из сохранённого source; их digests и короткие безопасные code excerpts есть в новом
отчёте, но selected source slice не расширялся. Public source/frozen identities не
менялись; новый documentation commit не является source SHA исследуемого бинарника.

**Только локально:** raw episode journal/UI/support exports, полные sealed capsules,
APK/native/gateway binaries, Git bundles, build archives и большие test logs; все
private keys/profiles/vault/credentials/runtime configs. Ссылки `/tmp` и
`state-client-build` внутри неизменённых отчётов не являются доступным GitHub evidence.
Некоторые ссылки STATUS/PLAN на несвязанные локальные задачи также не публикуются.
Не включены чужие dirty workflow/API/desktop/Android edits из основной рабочей папки.

## Publication safety и границы

Review-ветка создана отдельно; original main/index/dirty worktree сохранены.
Новые source/doc blobs проверены на secret/private-key patterns, реальные join URLs,
userinfo/PII, бинарные/runtime файлы; найденные URL/userinfo в tests — synthetic inputs.
Новые commits содержат только docs и `research/supervisor-20261015`; workflow changes,
tags/main merge/release отсутствуют. Существующие frozen source bytes не форматировались:
diff-context/third-party-license whitespace сохранён, это не новая product правка.

Изучены действующие workflow triggers и известные repository hooks: deployment/release
jobs привязаны к другим branches/tags либо manual dispatch; active local Git hooks нет.
Эта публикация может запустить обычный phase0 CI с isolated fixtures, но не deployment
или APK distribution. Workflow protection не изменялась; manual CI/acceptance не запускались.
Полный sealed audit/CI/acceptance не повторялись; проверялся только состав публикации.

Production deployment/restart, owner CONNECT/reconnect/instrumentation, APK install,
credential mutation/refresh, live provider sessions, intentional recovery triggers,
new product patches/candidates: **0**. После push требуется remote-ref/content readback;
его точный окончательный HEAD и blob-ссылки фиксируются в итоговом ответе задачи.
