# Product / Engineering Rebaseline — 30.09.2026

## Scope и starting state

Документационная переоценка после repository sync, не runtime development.
Starting HEAD/main = freshly fetched origin/main:
`5cc9d2a04149cd17a0ef3434a77fefc137b1a06a`. Исходная рабочая копия чистая.
Fetch потребовал разрешение вне read-only `.git` sandbox; выполнен без push.
История sync сохранена в [исходном отчёте](2026-09-30-repository-sync.ru.md).

Прочитаны AGENTS, STATUS/current PLAN, оба README, architecture, relevant Home
design и принятые [5N.5](2026-09-28-webrtc-eu5-mux-dns.ru.md) /
[Room Broker](2026-09-28-webrtc-5n-room-broker.ru.md) reports. Existing Android
VpnService подтверждён manifest/TcpTunnelEngine; эта работа не создаёт новый VPN.
Новый web research о сетевых ограничениях не проводился; дополнительный источник
— явное пользовательское полевое наблюдение в постановке задачи.

## Решение и authoritative документы

Family Connect — resilient connectivity service для семьи/личных устройств:
непрерывность и восстановление важнее числа протоколов/стран или benchmark speed.
Целевой пользователь — технически подготовленный член семьи, помогающий близким;
не продукт «только для России». CONNECT должен скрывать выбор доступного пути,
но полная cross-transport автоматизация пока PLANNED. Telemost — первый доказанный
заменяемый restricted carrier; третья сторона недоверенная, security boundary
остаётся Device Identity / Family admission / Family TLS.

В одном сообщённом пользователем случае сотовых ограничений/белых списков
Краснодара AWG3.1 и TCP были недоступны, Telemost работал. Никакого обобщения на
все сети/регионы/операторов/времена. Модель — доступное сейчас подмножество network
capabilities, а не предположение «Internet есть, фильтруют лишь VPN packets».

Изменены только:

- `README.md`, `README.ru.md`: согласованный product intro, usable beta,
  isolated proof и planned UX; удалены false preparation-only claims про
  Family binary/auth/TCP/DNS; RU beta50/desktop0.2.10/0.2.14 исправлены на
  документированные beta51/0.2.11/0.2.15, без изменения самих версий/артефактов.
- `docs/STATUS.md`: короткий CURRENT PRODUCT STATE, exact sync/CI evidence,
  maturity/versions/ops разделены; история сохранена.
- `docs/PLAN.md`: authoritative short critical path, phases A–I, acceptance,
  будущие privacy-safe metrics и backlog; хронологический ledger не перенумерован.
- `docs/architecture.md`: canonical philosophy, три planes, Orchestrator,
  transport adapters/OS boundary с IMPLEMENTED / PROVEN EXPERIMENTAL / PLANNED.
  Отдельный strategy/ADR не нужен; не создаём второй источник продуктового решения.
- `docs/README.md`, `docs/ROADMAP.ru.md`, `docs/reticulum/HOME_GATEWAY_DESIGN.md`:
  навигация и явный приоритет новых решений над историческим ordering.
- Этот dated report: provenance, проверки, ограничения, rollout/rollback.

## Факты и следующий gate

**Implemented:** identity/admission/provisioning, Android/Linux/Windows,
Android VPN lifecycle, normal AWG/TCP beta use.
**Proven experimental:** real Telemost VP8/RTP, physical Redmi, Family TLS1.3,
ReliableStream/selective repeat, real RTP gap recovery, long-duration goodput,
Internet TCP + verified end-site HTTPS, multi-stream mux + Family DNS/containment,
exact mixed workload/fairness/bounds. **Room Broker itself PASS**: official API,
server-only OAuth, Amsterdam gateway READY first, Android automatic descriptor/join,
Family TLS + multiple HTTPS200, no manual room URL.

**Not delivered:** production restricted bootstrap (accepted broker control
ingress was temporary SSH forwarding + adb reverse), whole-device 5N binding,
5N.6 acceptance, complete Orchestrator, beta-user restricted rollout, Krasnodar
FIELD-1, generic UDP, production capacity, iOS. Global ReliableStream HOL remains.

**NEXT = 5N-BOOT-1**, затем **5N.6 → MVP Orchestrator → FIELD-1 → 50–100-user beta**.
Bootstrap target: signed/cached directory → rendezvous carrier → Family auth →
REQUEST_TRANSPORT → existing Room Broker → dedicated room/Family Session.
Только control/rendezvous, не bulk VPN. Второй carrier/Home Gateway — backlog;
FEC/HOL/performance — evidence-driven позже. В этой задаче BOOT-1 не начинался.

## CI / operational evidence на starting HEAD

Read-only GitHub API verification после fetch:

| Run | Результат |
| --- | --- |
| [36718292459 — Linux control preview](https://github.com/Joker20380/family_connect/actions/runs/36718292459) | completed/success |
| [36718292492 — phase0](https://github.com/Joker20380/family_connect/actions/runs/36718292492) | tests PASS; failover FAIL на Build isolated failover stack |
| [36718292488 — Client builds](https://github.com/Joker20380/family_connect/actions/runs/36718292488) | Linux/Windows/Windows compatibility PASS; Android build/unit/lint PASS, emulator WG/AWG/TCP/Auto lifecycle FAIL; release SKIPPED |

Нет green-full-CI заявления. Causes не диагностировались/не исправлялись в docs
task. Latest documented deployment — disk mitigation29.09, не sync commit;
остаточные NL disk latency, RU API restart cause, worker healthcheck/outbox,
TLS monitoring и client E2E остаются отдельными ops follow-ups, см. STATUS.

## Docs validation

- `python3 scripts/check_public_docs.py --all`: **PASS**, 398 Markdown files,
  2396 local/external link references, errors0. Первый проход нашёл два legacy
  anchor references из architecture EN/RU; сохранён совместимый Home Gateway
  heading/ссылка, повторный полный проход PASS. Проверяется существование
  local paths/anchors, не доступность каждого external URL.
- `python3 scripts/check_public_docs.py`: **PASS**, public subset17 files,
  372 link references, errors0.
- `git diff --check`: **PASS**.
- Semantic EN/RU review: одинаковые версии, maturity boundaries, NEXT и limits;
  сохранённые license sections совпадают byte-for-byte с starting HEAD.
  STATUS/PLAN historical ledger tails также byte-for-byte сохранены.
- Новых Mermaid diagrams нет: новые responsibility/flow diagrams — fenced text,
  rendering Mermaid не требуется. Новых изображений или download URLs нет;
  новые внешние ссылки — проверенные read-only GitHub CI run records.
- `python3 scripts/check_public_sources.py` после staging: **PASS**, 1467 index
  entries, 0 blocked files; `git diff --cached --check` PASS. Повторяется на
  финальном index непосредственно перед commit.

Physical Android/PERF/full Python/Go suites/build/deployment не запускались;
их старые PASS — ссылки на принятые отчёты, не повторные результаты этой задачи.

## Versions / rollout / rollback / remaining

Версии не менялись: Android **0.1.18-beta51/code51**, Linux **0.2.11**, Windows
**0.2.15** (0.2.14 compatibility fallback). Latest documented public/invitation
versions те же; новое чтение public artifacts/checksums/установок не выполнялось.
Diagnostic code4/name5N.5-test-only previously built/test-installed/uninstalled,
не public release. Catalog sequences Linux9/Windows11 не менялись. См.
[release evidence](2026-09-26-server-list-crossplatform.ru.md) и
[Linux distribution](../linux-appimage-deb.ru.md).

Никаких builds, новых downloads/hashes, install, publication, tag, catalog signing,
push, server commands или production changes. Rollout: только локальный docs
commit. Rollback документации: `git revert <rebaseline-commit>` после проверки
рабочей копии, не reset истории; production rollback не нужен. Операционный
rollback предыдущего deployment остаётся в [disk report](2026-09-29-disk-io-recovery.ru.md).
Commit ID возвращается в итоговом ответе, без самоссылочного SHA в этом файле.

Remaining: CI/ops issues выше и будущие gates D–I по PLAN; никаких unfinished
runtime changes этой задачи нет. После documentation commit **STOP**, не начинать
5N-BOOT-1. Push performed: **no**. Runtime changed: **no**. Production changed: **no**.
