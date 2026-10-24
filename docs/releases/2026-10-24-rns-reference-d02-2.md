# D02.2 — public RNS/reference checks, 24.10.2026

Вход: чистая `main`, HEAD = origin/main `17256565148028da9fd660a6e31ad6be387248dd`.
Review D02.1-R и fleet-документации уже принят; повторной работы по ним нет.
D02.1-R остаётся PARTIAL, historical suite NOT_RUN из-за неподтверждённых artifact pins.
D05 QUEUED после D03/D04; контракт сохранён, реализация не начата. D01/общий CI открыт.
**D02.2 DONE в заданном scope; NEXT — отдельный review.** Code checkpoint
`da8670e4aa4e20c0fc52634666da197ed3ec9d6d` отправлен обычным push;
`git ls-remote origin refs/heads/main` подтвердил тот же SHA. Последующий docs-only
checkpoint фиксирует этот evidence, не получает автоматически результаты CI code SHA.

## Изменение и граница доказательств

Две прежние проверки больше не читают private capsule в ordinary CI. Явное соответствие
accepted → public в verifier используется обоими тестами, без fallback/skips:

| Accepted path | Публичный источник | Неизменённый SHA256 |
|---|---|---|
| `clients/android/app/src/main/assets/rns-relay.json` | тот же путь | `9305cd3486e4e7c5a7fc881a292d3824653a0d6d5c4a5559272baa98c275b7bb` |
| `clients/android/app/src/main/python/fc_rns_transport.py` | `clients/rns/fc_rns_transport.py` | `70593713d1d915904d10cf0cac0eb21ca41b11b4dedcdb7973d0da236579ada0` |

Public Android transport имеет другой полный SHA256:
`1e5637fddf8ac42471ad616550b19a871bae352eba92ee7c0adaef46e5cdcd2e`.
Поэтому repository root не подставляется вместо capsule root. В worker test hashes
проверяются **до** JSON parse; HOST/PORT/PROVIDER и provider64B assertions сохранены.
Readiness test сохраняет source_files ↔ android_ui_and_handlers, implementation files
и invariants; дополнительно проверяет APK и inventory reference согласованность.

В readiness manifest добавлена только ссылка на уже закреплённый inventory
`8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c`.
Все старые поля/accepted hashes побайтно по значениям неизменны. Default verifier
проверяет публичные RNS bytes и metadata linkage. Полный `--capsule` по-прежнему требует
настоящие inventory/source/APK/native bytes и дополнительно сверяет readiness RNS pins
с **уже проверенным по hash** inventory, аналогично существующим chat/voice checks.
Public PASS не заменяет capsule/APK/native verification и не доказывает APK signer/runtime.

## Локальная проверка до push

Чистые before/after exports без `state-client-build`, non-root Python3.13.15,
неизменённый D01.2 bootstrap/locks. Raw logs и collection lists только `/tmp/fc-d02.2/evidence/`.

- `python -m pytest -q clients/desktop/tests/test_rns_worker.py tests/test_desktop_reference.py`:
  before **2 failed, 27 passed, 1 skipped**, ровно два выбранных FileNotFoundError;
  after **49 passed, 0 failed/errors, 1 skipped**. Skip — прежний optional visual-contract
  capsule test, не добавленный обход RNS. Новых regressions20: missing/changed asset/transport,
  APK/inventory metadata mismatch, RNS pin против verified inventory, explicit `--capsule`
  CLI при missing/changed inventory/source/APK, сохранение native hash gate.
- `python -m pytest --collect-only -q`: **3031 → 3051, 0 errors**. Нет потери cases;
  +20 только в этих двух файлах. Для сравнения нормализованы четыре прежних динамических
  IDs (clock fields и `next(iter(PATHS))`), multiplicities/исходники не менялись.
- `python scripts/verify_desktop_reference.py` в clean export: **PASS**, shared_files175,
  capsule_files=null, failures=[]; никакой capsule в export не добавлялось.
- Настоящие локальные accepted source/inventory/APK доступны. Отдельный
  `python3 scripts/verify_desktop_reference.py --capsule` (host Python3.14.4): **PASS, exit0**,
  shared_files175, capsule_files2073, failures=[]; проверены pinned APK/native hashes.
  Synthetic capsule fixtures в регрессиях проверяют отказ/связность verifier и не являются
  evidence настоящей capsule. Реальный gate выполнен отдельно, приватные bytes не публиковались.

## CI и ограничения

Все результаты таблицы — фактически завершённые jobs на **`da8670e`**, не прошлые counts.
Strict imports и адресные D01 gates PASS; полный pytest сохраняет exit1 при остаточных
failures. Collection errors нет; Docker root gate — 22 passed, адресный — 59 passed.

| Окружение / evidence | Полный pytest: passed / failed / errors / skipped | Не выполнено после отказа |
|---|---|---|
| [control](https://github.com/Joker20380/family_connect/actions/runs/40084625695/job/120844903532) | 2890 / 55 / 0 / 106 | GTK render/interaction, package build, extracted artifacts/recovery, uploads |
| [phase0/tests](https://github.com/Joker20380/family_connect/actions/runs/40084625730/job/120844903468) | 2891 / 54 / 0 / 106 | cargo test |
| [Docker tests-stage / failover](https://github.com/Joker20380/family_connect/actions/runs/40084625730/job/120844903680) | 2889 / 54 / 0 / 108 | `/tmp/tests-passed`, runtime image, provision/failover/auth/offline/revocation |

У каждого полного suite также 7 passed subtests / 2 warnings. В Docker build.log
(`phase0-failover`, artifact12556841832) два изменённых файла не входят в FAILED list;
все 3051 cases учтены, полный suite выполнен от runner. Маркер и runtime COPY gate
сохранены: неуспешные тесты не выдают пригодный runtime image.

Оставшиеся 54 failures Docker: mobile_bootstrap/owner_disconnect/tunnel_restart — 19
(отсутствующие отдельные historical capsule sources); HTTP evidence/runtime/preflight/
transition — 30; native expiry — 2; private storage — 2; readiness socket — 1.
Control дополнительно падает на Auto stop/start generation assertion (D04);
причина гонки здесь не доказывалась и не исправлялась.

[Client builds/Linux](https://github.com/Joker20380/family_connect/actions/runs/40084625812/job/120844903897):
imports/адресный gate PASS; desktop **882 passed / 1 failed / 0 errors / 62 skipped**,
тот же Auto assertion, GUI/package gates skipped. [AWG](https://github.com/Joker20380/family_connect/actions/runs/40084625713/job/120844903467)
и [TCP](https://github.com/Joker20380/family_connect/actions/runs/40084625739/job/120844903405):
imports, адресные, полный desktop pytest и jobs **PASS**. Несвязанные Android/Windows
jobs не ожидались; общий Client builds workflow не объявляется PASS.

Обязательные full suites, D01 environments, release-fixture policy/export/historical pins
и следующие job gates сохранены. Локально полный исторический pytest не запускался.
Остальные capsule/nginx/expiry/privacy/socket группы, D03 ChatHTTP и D04 Auto не исправлялись.

Продукт, Android, accepted source hashes, historical runner, D05 contract, wire/IPC,
build settings и пользовательские подключения не менялись. Версии Linux0.2.11 /
Windows0.2.15 / reference Android106 прежние. Live/deploy/publication/rollback, installed
приёмка и APK signer verification NOT_RUN. NEXT — **review D02.2**; после отчёта остановиться.
