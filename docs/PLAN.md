# Working plan / Рабочий план

## Утверждённый порядок выпуска — 2026-09-14

Пользователь: сначала выполнить весь план VPN-сервиса на Linux, Windows и Android.
Мессенджер и iPhone отложены до завершения этого плана; текущий код мессенджера
сохраняем, новых задач по нему и iOS сейчас не начинаем. Все результаты, ограничения,
версии и оставшиеся проверки документируем. Этот порядок имеет приоритет над
историческими разделами ниже, где следующим шагом названы chat/Store bridge или iOS.

[Единый список условий выпуска](PLAN.md#release-gates-three-platforms).

## Android live acceptance и beta05 — 2026-09-14

На Redmi Note9 Pro/Android12 установлен **0.1.4-beta05/code5**, source8b6d51b,
com.familyconnect.app.pilot; исходный com.familyconnect.app0.1.0/code1 сохранён.
APK SHA256 e83c0841dfa3719e50bef3509fdb436ce7f2fb17c8479c556fa13d80d974d951,
постоянная offline beta signature,132 app unit/8 instrumentation и отдельный
storage restart5836→5870 passed. Clients34843986160, Android diagnostic34843986164,
phase034843986155 success. Публичного release/tag/catalog update не было.

На beta04 принята цепочка HTTPS IP enrollment → signed encrypted Reticulum → native
WG/AWG2/TCP → bound DNS/HTTPS → device-signed ACK, health rollback, crash после
APPLIED_PENDING с durable outbox/recovery и expiry stop/refusal. В beta05 добавлен
bound health retry в прежнем15s budget, устранены лишние UI text updates. После
обновления прежняя identity приняла revision8/COMMITTED;3/3 повторных TCP подключений
(два disconnect, один force-stop) подтвердили HTTPS IP185.251.89.19. Standard UI XML
получен, бесконечного idle wait нет. Revision8 истекла12:58:55UTC, VPN/services off.
Краткие прогоны не доказывают длительную устойчивость или все причины ранних отказов.

Телефон находится в Европе. Пользователь сообщает полную блокировку WG в России;
приёмка РФ требует AWG/TCP в российских сетях. Европейский WG остаётся baseline.
Открыты managed Auto/blocked-WG failover, AWG3.1 signed schema, relay/whole-gateway
outage, Doze/handover, полный routing/IPv6/DNS и длительная эксплуатация.

Временные Android WG/AWG peers удалены (исходные3/1 peers сверены), TCP8444 container
удалён, три expiry timers остановлены. Исходные API/AWG/TCP не перезапускались.
UI helper/XML и JDWP forwarding убраны; adb usb выполнен, Wi-Fi5555 connection refused.
Native identity/journal и private receipts сохранены. Для продолжения: новая revision>8,
previous hash fdc106fed72d7ce6a3199fe3c2cfd96436abff1544122829142c74ab21348bd9;
истёкшие тестовые конфигурации/удалённые endpoints не использовать как рабочий сервис.
Далее оставшиеся Android gates, Windows native Stage5 и остальные условия трёх
платформ. Django/платежи после VPN; messenger/iPhone отложены.
[Отчёт](releases/2026-09-14-android-storage-runtime.ru.md) ·
[Runbook](testing/android-stage5-live.ru.md) · [Sanitized receipt](android-stage5-live-result.json).

## HTTPS для Android регистрации — 2026-09-14

https://185.251.89.19:8443 развёрнут перед прежним localhost product API.
nginx1.30.4/Certbot5.4.0 pinned digests; публичный IP TLS expiry21.09.2026 02:18:22GMT.
Staging/production issuance, external TLS/routes/body/rate limits и renewal dry-run
passed; отдельный twice-daily timer active, ручной renew/reload success. Новые UFW
IPv4 TCP80/8443; прежний API и VPN не перезапускались. Созданы отдельные single-use
invitation/entitlement с предварительной private DB backup; Android enrollment выполнен
в beta04; дальнейшие live WG/AWG2/TCP/recovery описаны выше. Осталось
наблюдать scheduled certificate renewal. [Rollout/rollback и тесты](releases/2026-09-14-product-https.ru.md).

## Исторический checkpoint a342d4b и подготовка restart test — 2026-09-14

Для a342d4b Client builds34833797626: Linux/Windows/Android success;
Android diagnostic34833797792 success; phase034833797631: tests/failover success.
Release job skipped. Последний desktop release по API — v0.2.9; новый APK не
публиковался. Для новой установки подготовлена версия0.1.3-beta04/code4, debug package
com.familyconnect.app.pilot (Family Connect Pilot); beta03 не заменяется.
Добавлена обязательная проверка Android Keystore/AtomicFile/journal/outbox:
отдельные prepare → force-stop → recover процессы, отказ clock regression,
corrupt storage и повторной генерации identity. Java compilation и локальные
положительные/отрицательные проверки CI gate прошли. CI34836392940: все8 instrumentation
cases passed; дополнительный restart runner не нашёл удалённый Gradle test APK.
Добавлена установка уже собранной пары перед обеими фазами; повторный CI ожидается.
Телефон Redmi Note9 Pro/Android12 доступен, установлен0.1.0/code1. USB нестабилен;
подготовлен переход на локальный Wi-Fi ADB. Новая сборка пока не установлена.
Полная регистрация→RNS→native apply→Internet→ACK и crash rollback ещё не приняты.
Далее: новый runtime CI, подключение ADB и подписанная тестовая сборка, затем
полная Android-приёмка и остальные [условия трёх платформ](PLAN.md#release-gates-three-platforms).
[Отчёт и границы проверки](releases/2026-09-14-android-storage-runtime.ru.md).

## Git checkpoint и Android runtime acceptance — 2026-09-14

Накопленные исходники357 файлов сохранены коммитом af46e87 и отправлены в origin/main.
Client builds34828757268: Windows/Linux success, Android APK/unit/lint прошли;
эмулятор выявил устаревший Auto-тест, пытавшийся менять профиль при активном VPN.
Тест исправлен: проверяет запрет изменения и восстанавливает профиль после disconnect;
cleanup ждёт освобождения service owner. Добавлены APK gates для Python/RNS/bootstrap/
лицензий и обязательный результат ControlRnsRuntimeTest в обоих Android workflows.
Docker test stage теперь копирует Python carrier: локальная сборка passed,353 tests/27s.
Проверка runtime report принимает успешный RNS test, отвергает missing/skipped.
Повторный CI для исправлений ещё предстоит; полное live Android enrollment→relay→VPN→ACK
не проверено. Версия0.1.2-beta03/code3 сохранена, релиз и установка не выполнялись.
[Отчёт](releases/2026-09-14-git-android-acceptance.ru.md).

## Android Stage 5: автоматический RNS carrier и ACK — 2026-09-14

Добавлен явный запуск «Подключить через Reticulum»: встроенный RNS получает
challenge, Java подписывает proof ключом зарегистрированного устройства, получает
encrypted signed envelope и передаёт его существующему service owner/verifier/journal.
ACK отправляется из durable outbox; повтор обмена через60 секунд, недоступность relay
не выключает работающий VPN. TCP socket привязывается к underlying Android network.
Chaquopy16.1.0 / Python3.10 / RNS1.5.1 / pyserial3.5; добавлены лицензии и CI Python.
98 Java tests, два реальных loopback RNS сценария (включая internal crypto), aapt2/
Java compilation и Gradle Python assets packaging passed. Это ещё не полная APK-сборка
и не Android runtime acceptance. Версия остаётся0.1.2-beta03/code3, серверы не менялись.
Следующее: APK/native ABI и instrumentation на Android, публикация конфигурации именно
для зарегистрированного Android в ControlRelay, проверка minimum-version и живого
receive/apply/health/ACK/reconnect. Product enrollment сам не публикует envelope в relay.
[Отчёт, воспроизведение и оставшиеся проверки](releases/2026-09-14-android-control-rns.ru.md).

## Android Stage 5: explicit signed-file intake — 2026-09-14

MainActivity принимает encrypted signed envelope через отдельный системный picker,
проверяет лимит65536 bytes и запрашивает VPN permission. Non-exported service получает
снимок bytes, не URI/path; принимает файл только при остановленной сессии. Завершённая
регистрация/device binding проверяются перед существующим receive/apply/health/journal.
Cold duplicate committed проходит safe resume без перезаписи профилей; reject/rollback/
failed показываются отдельно. Pending bytes не сохраняются в instance state.
91 Java tests passed; aapt2 resources и app Java compilation passed с cached engines.
Это локальный ручной bootstrap, не автоматическая RNS/HTTP доставка. ACK остаются
в outbox. Android OS/UI/process-death/full Gradle/lint/ABI acceptance ещё не выполнена.
APK/версии/серверы не менялись. Далее runtime acceptance и RNS carrier/ACK delivery,
minimum-version policy и полный release plan.
[Проверки, применение и ограничения](releases/2026-09-14-android-control-intake.ru.md).

## Android Stage 5: explicit Reticulum enrollment — 2026-09-14

Добавлены UI регистрации, coordinator, отдельный encrypted enrollment state и HTTPS
adapter. Identity и пустой journal сохраняются до регистрации; RNS signature связывает
challenge и WG key. Повтор использует прежние identity/origin/proof; lost reply
проверяется через существующий provisioning challenge. Private keys/token не
сохраняются в enrollment metadata и не логируются; private keys остаются в device vault.
81 Java и57 Python tests passed; aapt2 resources и app Java compilation passed.
Это не Android Keystore/AtomicFile/UI/TLS/runtime/full Gradle/ABI acceptance. APK и
live enrollment не выполнялись. Не выдаётся и не применяется VPN config.
Далее native runtime acceptance, получение signed Stage5 config/RNS carrier,
ACK delivery и minimum-version policy; manual admission/managed Auto/AWG3.1 открыты.
[Порядок использования, ограничения и rollback](releases/2026-09-14-android-control-enrollment.ru.md).

## Android Stage 5: explicit committed resume — 2026-09-14

Явный connect после IDLE recovery теперь проверяет committed envelope на текущий
момент и поднимает только сохранённый профиль, точно совпадающий с signed config
и собственным WG key. Нет profile writes, новой revision или ACK при reconnect.
Проверяются traffic health, expiry/clock; ошибка останавливает engine. Pending сначала
восстанавливается, rollback не переходит к повторному resume/legacy/Auto.
63 Java tests passed; app Java compilation passed с Android35/cached engine/R.
Это не runtime/full Gradle/lint/APK acceptance. Далее explicit enrollment с RNS
identity/WG binding/init journal, Android runtime и carrier; текущий минимум версии
проверяется честно. VersionCode3/0.1.2-beta03, установка и серверы не менялись.
[Проверки и ограничения](releases/2026-09-14-android-control-resume.ru.md).

Пользователь запросил привязку клиента к криптографической identity Reticulum;
существующий proof/key binding сохраняется. Предложена схема Django/PostgreSQL
для кабинета/оплаты плюс Prometheus для технических метрик. Она документирована,
но ещё не реализована: [архитектура](design/django-product-plane.ru.md).

## Android Stage 5: восстановление при запуске службы — 2026-09-14

ConnectionService теперь проверяет managed state под существующим owner и запускает
journal recovery на том же worker до подключения. Pending откатывается; IDLE и
успешный rollback не переходят к legacy/Auto. Orphan files/keys и ошибки Keystore
не допускают обычное подключение; import/clear gate сохранён. Без явной команды
connect обычный WG больше не запускается. При отсутствии engine служба завершается.
50 Java tests passed (7 новых); компиляция app Java с Android35 и cached engine/R passed.
Это не Android runtime/full Gradle/lint/новый APK. Safe resume committed config,
explicit enrollment/identity+WG binding/init journal, admission ручных операций,
Keystore/AtomicFile/process-death/VPN acceptance и RNS carrier остаются впереди.
Версии, установка и серверы не менялись.
[Результат, проверки и возврат](releases/2026-09-14-android-control-startup.ru.md).

## Android Stage 5: native application adapter подготовлен — 2026-09-14

ControlApplication выполняет snapshot/apply/health/rollback над фиксированными
wg/awg/tcp slots; private WG key подставляется из device identity, прочие профили
сохраняются. Partial write/crash восстанавливает snapshot; отмена и expired lease
запрещают reconnect. ConnectionService содержит внутренний dispatcher через свой
worker/engine и точный owner; второй VPN lifecycle не создаётся. DNS+HTTPS health
привязан к VPN Network, добавлены cancellation/lease timers.
Trust anchor — packaged resource, побайтно равен desktop roots; version проверяется
по Android package version, без подмены0.2.9.43 Java tests passed, app Java compilation
passed с cached engine/R; Native runtime/full Gradle/lint пока не приняты.
Dispatcher ещё не вызывается из UI/Reticulum/startup; legacy managed-state gate
сохраняется. Следующий блок — startup recovery/enrollment и isolated Android
Keystore/AtomicFile/process-death/VPN acceptance. APK/версии/серверы не менялись.
[Реализация, проверки и ограничения](releases/2026-09-14-android-control-application.ru.md).

## Android Stage 5: владелец службы и профильных операций — 2026-09-14

ConnectionService удерживает отдельный owner от начала worker-сессии до успешного
engine.down/awaitShutdown и завершения destroy cleanup. Auto/health/stop callbacks
проверяют owner; старая служба не освобождает новую сессию. ProfileStore save/clear
согласованы с тем же owner, удаление вынесено из UI-потока. Control receive/recover
также отказывают при активном legacy owner; ACK flush остаётся независимым.
Connect/Import/Clear проверяют любые Stage5 files/base/bak/new и orphan aliases:
пока native recovery adapter не подключён, managed state блокирует legacy mutation,
а не обходится/удаляется. Это защитный gate, не готовое автоматическое восстановление.
33 Java tests passed; все текущие Java app sources скомпилированы с Android35 и
ранее собранными engine/R dependencies. Native runtime, full Gradle/lint и APK
не проверялись/не выпускались; один missing-annotation warning сохранён в отчёте.
Следующий блок: native recovery/application adapter через существующий service
lifecycle и isolated Android Keystore/AtomicFile/process-death acceptance.
[Изменения, проверки, ограничения и возврат](releases/2026-09-14-android-control-owner.ru.md).

## Android Stage 5: журнал и восстановление ядра — 2026-09-14

Добавлены ControlJournal/ControlTransaction, device-signed ACK и ограниченная очередь,
Keystore/AtomicFile adapter для отдельного зашифрованного журнала. Намерение записи
предшествует apply; commit и ACK сохраняются вместе. Pending после перезапуска
откатывается; floor не уменьшается. Ошибка rollback блокирует вход manual/receive.
Отправка ACK не удерживает общий owner и не теряет новые concurrent events.
JDK17 + Android35 compilation passed; **23 Java tests passed**, включая все16 шагов
трёх immutable Python transcripts, прежние30 configs/15 ACK/32 structural/4 cipher
refusals. Проверены сбои до/после записи, lease expiry, clock regression, повреждение
журнала и точные canonical ACK. Existing fixture manifest не изменён.

Это библиотечное ядро и скомпилированный OS adapter, ещё не Android runtime acceptance.
Activity/ConnectionService/ProfileStore пока не подключены к owner/journal;
production operation coordination не заявляется. Следующий блок: интеграция с
существующим service lifecycle и проверка Keystore/AtomicFile/process death, затем
native apply/health/rollback и RNS carrier. APK/серверы/версии не менялись.
[Отчёт, проверочные команды и возврат](releases/2026-09-14-android-control-journal.ru.md).

<a id="release-gates-three-platforms"></a>
## Обязательные условия выпуска Linux / Windows / Android

- [ ] **Android Stage 5.** Identity runtime; journal/outbox/runtime persistence;
  общий owner Activity/service/import/clear/Auto; recovery перед mutation;
  native apply/traffic health/rollback; enrollment/binding и RNS carrier.
  Identity/journal/transaction source и legacy service/profile owner готовы;
  native startup/enrollment/RNS wiring и live WG/AWG2/TCP apply/ACK, process recovery
  проверены на beta04; beta05 TCP reconnect3/3, expiry stop и UI idle passed.
  Managed Auto, relay outage, Doze/handover и стабильность открыты.
- [ ] **Windows Stage 5.** Защищённые identity/journal/outbox по SID, общий broker
  owner, SCM restart recovery, native apply/health/rollback, enrollment и carrier.
  Verifier принят ранее; это не полная native интеграция.
- [ ] **Управляемый AWG3.1.** Версионированная подписанная схема и согласованная
  поддержка parser/engine/recovery на трёх платформах, migration и refusal tests.
  Ручной Android AWG3.1 работает; schema2 control по-прежнему отказывает3.1.
- [ ] **Stage 6.** Проверяемая независимость служебных входов и альтернативных
  gateway; полная недоступность старого сервера → доставка/проверка/применение новой
  конфигурации → реальный Интернет через новый сервер; отказ самого relay.
  Amsterdam уже существует; старые строки «второго VPS нет» ниже исторические.
- [ ] **Эксплуатационная приёмка.** Реальные Linux/Windows/Android; полный routing,
  DNS и cleanup; sleep/Doze, restart, Wi-Fi/mobile handover, длительные соединения,
  одновременные пользователи и устойчивость TCP/AWG. Отложенные ранее реальные
  device/load tests остаются незакрытыми условиями выпуска, не считаются пройденными
  на основании unit/CI; выполнять при доступных целевых устройствах и согласованном окне.
- [ ] **Согласованный сервисный выпуск.** Самостоятельное подключение пользователя
  без ручной выдачи профиля оператором; platform CI/UI/runtime, подписанные неизменяемые
  сборки, установка/обновление/rollback; мониторинг, резервные копии и восстановление,
  отзыв доступа и эксплуатационные инструкции. Для платного публичного выпуска —
  подписки/уведомления/оплата и поддержка; закрытая техническая beta не закрывает этот пункт.

Мессенджер и iPhone начинаются после перечисленных пунктов. Порядок между ними
пока не выбран. Наличие прототипов и исторических релизов не заменяет эти критерии.

## Android Stage 5: identity сохранение подготовлено — 2026-09-13

По уточнению пользователя продолжена Android-часть Stage 5. Добавлены независимые
RNS/WG ключи, совместимый enrollment proof и отдельный AndroidKeyStore/AtomicFile
vault с явным create/load, запретом неявной смены identity и read-back после записи.
JDK17/Android35 compilation passed;8 Java tests и51 Python tests passed, включая
неизменённые conformance vectors и точное совпадение proof с Python reference.
Keystore/AtomicFile runtime ещё не проверен. Activity/service пока не подключены;
следующий блок — durable journal/outbox, общий operation owner и process-death
recovery, затем native apply/health/rollback и RNS carrier. APK/серверы/версии
не менялись. Предыдущие незакоммиченные изменения сохранены.
[Отчёт, проверки, ограничения и возврат](releases/2026-09-13-android-control-identity.ru.md).

## Android archive GIF renderer prepared — 2026-09-13

Full candidate archive49 GIF/374251 bytes added with SHA256 provenance;69 text
aliases, unchanged signed text, no image bytes on RNS. ChatSmileyTextView uses
bounded built-in GIF reads, up to8 animated occurrences, foreground/visibility
checks and callback cleanup. SDK35/JDK17 compilation and crypto/token checks passed;
Pillow verified every hash/frame/size. Actual Android rendering/lifecycle untested.
Exact official ICQ pack provenance/release rights still pending; no APK packaged.
No chat screen or RNS/Store bridge wired. Next: Android carrier/Store bridge and
Keystore/lifecycle runtime acceptance, then AWG3.1 signed schema and chat UI.
[Report, integration contract and rollback](releases/2026-09-13-android-icq-renderer.ru.md) ·
[49 animated samples](design/icq-animated-gallery.html).

## Android chat key foundation; exact classic ICQ smileys requested — 2026-09-13

Separate AndroidKeyStore wrapping alias and bounded61-byte AES-GCM Store-key file,
explicit create/load and fail-closed missing/corrupt state. SDK35 compilation and
JDK17 crypto/token checks passed; device Keystore/AtomicFile runtime untested.
User requires original animated ICQ2000s smileys. Custom drawing removed; archived
GIF samples available for visual comparison, exact provenance/version still pending.
Text-only2–3-byte tokens prepared; no image renderer/picker or Android RNS bridge yet.
No APK/server deployment. Next: original asset match and lifecycle-aware rendering,
RNS/Store bridge, runtime Keystore acceptance, versioned AWG3.1 signed schema.
[Report and boundaries](releases/2026-09-13-android-chat-foundation.ru.md) ·
[Animated reference preview](design/icq-classic-preview.html).

## Event-driven foreground mailbox sync — 2026-09-13

SyncController coalesces lifecycle/refresh events into one bounded worker and one
pending pull. No periodic polling or event-free retry. Foreground+online required;
background/network loss cancels, generation fence ignores late results.30s cooldown,
error backoff capped300s; close/join must finish before Store closes. Receive-only:
outbox and Android callbacks not wired. Real local RNS resume delivery/purge passed;
20 duplicate lifecycle events produced one attempt. Full suite51 passed/71.64s; final close refinement verified by10 sync tests/3.29s.
No server/APK changes. Next: Android carrier/Keystore/lifecycle integration and
versioned AWG3.1 signed configuration; push/hints, outbox and Doze remain open.
[API, tests, limits and rollback](releases/2026-09-13-messenger-event-sync.ru.md).

## Compact mailbox batch accepted — 2026-09-13

Mailbox.publish_many sends1–4 messages on one authenticated link with a shared
bounded deadline and individual durable ACKs. Partial failure/cancellation preserves
completed and queued messages; unchanged ciphertext retry/deduplication.42 messenger
tests passed (65.86s). Amsterdam four-message send: 4419 → 2373 RNS interface
bytes (46.30% reduction in this run); all8 messages delivered/purged.
Empty fetch and65s idle measured separately; not full TCP/IP or a capacity estimate.
No daemon/Android deployment or APK packaging. Next: event/resume-driven bounded
sync and adverse-link traffic/recovery, then Android carrier/Keystore/AWG3.1 schema.
[Measurements, reproduction, rollback and limits](releases/2026-09-13-messenger-compact.ru.md).

## Amsterdam mailbox live; compact messages remain a requirement — 2026-09-13

Dedicated closed RNS1.5.1/LXMF1.1.1 service on TCP4243 deployed for two diagnostic
identities. Offline delivery, volume/service restart persistence, commit-before-purge,
empty repeat fetch and reply passed live. Separate64MiB volume,192MiB memory ceiling;
actual post-test memory23.3MiB. Existing VPN/control services active; no APK packaged.
34 messenger tests passed (59.59s). Four-byte text:115-byte signed LXMF,208-byte
ciphertext; cold publish RNS interface counters855 TX/416 RX, excluding TCP/IP overhead.
Next: measure message-series/empty-fetch/idle budgets and reduce control exchanges
without weakening signatures/durable delivery; then Android carrier/Keystore/UI and
versioned AWG3.1 signed schema. Compact binary payloads are an explicit user requirement.
[Live evidence, bootstrap, rollout/rollback and limits](releases/2026-09-13-amsterdam-mailbox.ru.md).

## Closed messenger ingress and bounded spool — 2026-09-13

Authenticated Family Connect RNS put endpoint, closed sender/recipient allowlist,
pre-insert global/per-sender byte+count limits, rate limiting, FULL commit ACK and
stable encrypted retries. Native anonymous LXMF uploads/peering not registered;
closed ingress requires Mailbox.publish (not unmodified PROPAGATED clients).
SQLite file ceiling plus actual16MiB ext4 ENOSPC test passed: no false ACK,
previous message preserved, recovery/reopen successful. Combined521 passed/2 existing
warnings (58.46s), including31 messenger checks. No server/APK changes.
Next: dedicated bounded runtime volume and service/identity/bootstrap in Amsterdam;
Android RNS carrier plus versioned AWG3.1 signed schema for automatic conf delivery.
Linux signed conf delivery via Amsterdam RNS already has live acceptance; Android
currently uses manual AWG3.1 import. Chat remains separate from VPN control.
[Evidence, conf status and limits](releases/2026-09-13-closed-mailbox.ru.md).

## Offline messenger delivery and commit-before-purge — 2026-09-13

LXMF1.1.1/RNS1.5.1: explicit propagated send with relayed status; new bounded
Mailbox pull stores verified text before requesting node deletion. Fresh links,
trusted node public key, cancellation, duplicate-safe retry and download limits.
Three-process loopback acceptance passed: recipient offline, node restart, denied
fetch, injected storage failure preserving spool, retry, recipient restart/dedupe,
quota cleanup, aged-record expiry and explicit purge after durable commit.
Combined local suite516 passed/2 existing warnings (53.71s), including26 messenger
checks. No APK/version/server changes. Remaining: anonymous upload admission limits,
hard disk quotas and service lifecycle before Amsterdam; Android Keystore/UI,
automatic sync, application delivery ACK and TCP adverse-network measurements.
[Evidence and limitations](releases/2026-09-13-messenger-offline.ru.md).

## Transport reliability and messenger text core — 2026-09-13

User paused additional APK packaging; continue transport/messenger source work.
RNS1.5.1 adapter now waits for establishment callback after LRRTT send, not early
ACTIVE status. Deterministic old-code regression fails2/current passes2; real
control lifecycle/extracted preview pass. Previous CI timeout attribution remains
unproven. Linux TCP/WG/AWG health probes share8s budget and force interface names
(`if!`), avoiding hostname interpretation if the interface disappears.
Messenger prototype: LXMF1.1.1/RNS1.5.1, independent encrypted identity/contacts/
history/outbox, signed text, duplicate suppression, restart/manual retry and stale
callback fencing. Actual two-process DIRECT delivery/receipts pass; no Android UI,
Keystore, automatic retry scheduler or offline propagation service yet.
Local combined suite506 passed/2 existing warnings; Docker control350 passed.
No app/server deployment or APK version change. Source commit intentionally uses
[skip ci] to prevent existing workflows packaging clients; new messenger-only
workflow added, remote CI not claimed. Next: isolated offline propagation acceptance,
key/lifecycle integration for Android, TCP adverse-network runtime measurements.
[Evidence and limits](releases/2026-09-13-transports-messenger.ru.md) ·
[Prototype](../messenger/README.ru.md).

## Android beta03 health feedback accepted in emulator — 2026-09-13

Source6383130: manual VPN-bound DNS health feedback, session-bound public-IP
HTTPS checks and stale-result refusal. Manual probe failures retain the tunnel.
Client CI34776015693 Android/Linux/Windows success;JVM30+lint,6 instrumentation
cases including screen-off5s,≥20s UDP outage/recovery, terminal Disconnect and
new session IDs passed. ARM64 beta03/code3 signed with existing beta key,
51,154,127bytes;v2/v3/alignment/payload verified. Existing beta02 profile reused.
User postponed Russian-phone tests while in Ghent: physical5min sleep, Doze,
battery and Wi-Fi/mobile handover remain open. No server/profile changes.
Separate phase0 failover build failed on extracted-preview RNS initial challenge
timeout;local focused2 tests passed, root cause not fixed. Next: diagnose RNS
startup/request intermittency and later physical Android checks.
[Beta03 instructions](testing/android-beta03.ru.md) · [Evidence/CI limits](releases/2026-09-13-android-stability.ru.md).

## Android beta02 calls reported working; load checked — 2026-09-13

User reports AWG3.1 working on MTS Vladikavkaz and home Rostelecom, WhatsApp and
Telegram calls with clear uninterrupted audio. Current20s idle measurement: host
CPU0.301%, AWG0.0161%, AWG RAM7.16MiB/peak15.63MiB, available RAM720MiB, restarts0.
Historical sysstat resolution10min. User clarified call times19:07/19:17 were
apparently Brussels time, i.e.20:07/20:17MSK: matching intervals show host CPU0.53%
and1.56%, with VPN activity. These are whole-host10min means, not per-call peaks.
No server upgrade indicated for the current small pilot; concurrency untested.
Next: synchronized call measurement if needed, screen sleep and network handover.
[Evidence and limits](releases/2026-09-13-android-calls-load.ru.md).

## Android AWG3.1 beta02 ready for first phone — 2026-09-13

Source d0709bc: Android CI34768083248/job103752559759 passed native4ABI build,
JVM30+lint and5 emulator runtime tests. Engine b5928ef + S4 patch, manual HPK/
content padding/trailers/cookies fields; custom timings and signed control3.1 unsupported.
ARM64 APK0.1.1-beta02/code2 packaged from accepted payload,51,154,127bytes, signed
with the same beta01 key; v2/v3/alignment/hash verified. Remains a debug technical pilot.
Separate Amsterdam AWG3.1 UDP443/fcawg31 service active+enabled. DNS/HTTPS(NL),
1MiB download, reconnect and namespace cleanup passed. Existing WG/RNS preserved.
Python485 passed/2 warnings. Phone/WhatsApp acceptance still pending; no claim of
DPI resistance in the user's network. Next: install over beta01, Auto off, import new
AWG profile, verify IP/sites/messages/calls, then sleep/handover.
[Phone instructions](testing/android-beta02-awg31.ru.md) · [Evidence and rollback](releases/2026-09-13-android-awg31.ru.md).

## Android-first technical beta01 prepared — 2026-09-13

User selected Android for initial testers. Accepted CI34758085225 APK downloaded;
archive matched official GitHub digest, all4 ABI hashes/licenses/fixture exclusion
checked. Local persistent beta signing key created; final APK v2/v3 verified,
only signing META-INF changed. APK0.1.0/code1 debug, not a mass-release build.
Separate Amsterdam WG peer10.79.0.4/fd79:92::4 prepared; prior peers preserved,
no server restart. DNS/HTTPS(NL)/download/reconnect passed in Linux namespace.
Physical Android install/network not yet tested: next gate is one real phone,
then sleep/handover/device matrix before expanding testers. AWG3.1/recovery is
not in this APK; Reticulum native onboarding still pending. No public release.
[Tester steps](testing/android-beta01.ru.md) · [Hashes, signing and rollback](releases/2026-09-13-android-beta01.ru.md).

## AWG3.1 managed recovery prototype — 2026-09-13

Three isolated repeats recovered server restart in3.7529/3.7665/3.7531s vs previous
~16.1s automatic recovery. One pinned-profile reset each; healthy controls zero resets.
Policy:3 consecutive failed probes, at most2 resets/invocation,10s cooldown,20s
observation budget checked between callbacks; stop on cancellation/ownership loss.
Focused7, full Python485 and Docker test-stage348 passed. No client/server deployment.
Linux control CI passed; initial phase0 failover image-build failure retained (logs403).
One retry34761940493 on unchanged code passed tests+failover; cleanup verified.
Production broker lease/revision/expiry/disconnect integration remains the next step;
H4 recovery,1CPU/PMTU/long-run and Amsterdam AWG acceptance remain open.
[Measurements and limitations](releases/2026-09-13-awg31-managed-recovery.ru.md).
[Own transport roadmap](own-transport-roadmap.ru.md): current RNS1.5.1 dependency is
confirmed; an independent Reticulum replacement/new VPN wire protocol is a goal,
not an implemented result. Existing control/journal work remains the foundation.

## AWG3.1 adverse-condition experiment — 2026-09-13

Experiment2 adds strict u16 tools parsing: reject65536 instead of truncation;
12 negative C cases and valid boundary ranges passed, selected engine suite count=3.
Three live virtual repeats passed wrong HPK/H4, invalid S1/padding, tunnel MTU,
1% configured loss with1MiB integrity, brief blackhole, link cycle, server restart,
and accelerated5s rekey. H4 recovery~15.1s and server restart~16.1s remain slow;
original15s failure retained.30s observation acceptance is not a reconnect fix.
Python478 passed; full upstream Outline remains unresolved. No deployment/app update.
Source c2bbd9a: phase0 CI34761027324 tests+failover passed; ordinary4-case sanity
also passed, namespace/IPC cleanup verified.
Next: managed recovery,1CPU load and path-MTU/long-run checks, then Amsterdam AWG.
[Evidence and limitations](releases/2026-09-13-awg31-resilience.ru.md).
[Reticulum/LXMF messenger proposal](reticulum-messenger.ru.md) documented; no messenger
code/service deployed. Messaging identity/history/lifecycle must be separate from VPN.

## AWG3.1 isolated experiment accepted within limits — 2026-09-13

Pinned engine v3.1.20260828 b5928ef + tools v3.1.20260812 ee0f0a9.
Unmodified device tests failed: first packets lost with S4 startup configuration.
Local explicit patch refreshes padding after blocked TUN Read; original device
and five new first-packet cases passed in the selected suite count=3.
Full go test ./... still fails Outline external integration; no full-suite claim.
WG/base/padding/trailers virtual comparison:12/12 runs,96MiB, zero measured ping
loss; AWG ~16.4Mbps on shaped20Mbps/~70ms RTT. Trailers cost ~6.4% more link bytes
than AWG base here; no DPI or VPS-capacity acceptance. Both engines RSS <14.59MiB
at sampled transfer end, not peak/service budget. No server/app/catalog/main change.
Source b90e39a: phase0 CI34759917018 tests+failover passed; local Python478 passed.
Next: negative profiles and loss/MTU/reconnect/rekey checks,1CPU load, then separate
Amsterdam AWG pilot; schema3.1 and Windows/Android migration remain open.
[Recipe, regression, metrics and limitations](releases/2026-09-13-awg31-experiment.ru.md).

## Managed Linux control route accepted — 2026-09-13

Source7ad40c0: once --managed-route leases a root-pinned UID/TCP relay route,
cleans it after exchange/client death, and recovers broker crash intent on next use.
Root helper/pin/Polkit installed locally; desktop current remains0.2.8.
GUI/control entry contention waits at most5s without bypassing journal ownership.
478 tests passed. Isolated kernel lifecycle/uplink tests and host client-SIGKILL
cleanup passed. Real canonical launcher revision7 + active-VPN duplicate + GTK/HTTPS
+ signed ACKs passed without manual rule. Initial two unexplained OPERATION failures
retained; physical handover/suspend/long-run tests remain open.
Final VPN off, rules removed, journalIDLE/floor7/committed7/outbox0.
Linux preview CI hash matched; AWG/TCP/Linux/Windows passed. Docker test-stage COPY
fixed in0136c54; repeated phase0 tests+failover passed. Android CI103725874969 also passed (checked13.09).
Next: AWG3.1 compatibility/runtime/profile migration and separate Amsterdam pilot;
3.1 is still rejected until implemented. [Initial upstream/schema audit](awg31-migration.ru.md) started.
No release/catalog/main update.
[Version hashes, expiry, evidence and rollback](releases/2026-09-13-managed-control-route.ru.md).


## External Reticulum pilot accepted with operator route — 2026-09-13

Amsterdam186.246.45.246:4242 now serves the pinned trusted RNS relay as fc-relay,
active+enabled; same VPS as WG, not independent infrastructure. Existing device
identity/journal preserved, second WG peer10.79.0.3 added; manual peer.2 preserved.
Revision4 committed but lost ACK connectivity after full VPN; outbox3 retained.
With temporary TCP4242→main policy rule, revision5 committed, all6 signed ACKs
arrived, duplicate delivery made no new profile; real GTK and bound HTTPS confirmedNL.
Relay restart preserved identity/configs/ACKs and duplicate fetch passed with VPN off.
Final: VPN off, temporary rule removed, journalIDLE/floor5/committed5/outbox0.
Next priority: managed trusted-relay route lifecycle in Linux runtime/helper, then
repeat without manual operator rule. Current installed0.2.8 unchanged; not a release.
Native protected state and independent infrastructure/alternate transport remain open.
[Evidence, exact lease expiry, limitations and rollback](releases/2026-09-13-external-reticulum.ru.md).


## Amsterdam paired Linux GUI pilot passed — 2026-09-13

Accepted preview66152538ee2a4f3e completed two real GTK Connect → Check IP →
Disconnect cycles: UI and interface-bound HTTPS both confirmed186.246.45.246/NL.
Profile fc-app-Amsterdam-pilot retained inactive, autoconnect=no. Host rules/default
routes/resolver/active connections restored; pending marker clear; GUI closed.
Import used app backend: native file chooser automation timed out. A harness profile
naming mistake was corrected; both preliminary failures retained in the receipt.
Installed0.2.8 unchanged; no server/release/catalog updates in this step.
Next: external trusted Reticulum relay and signed Amsterdam configuration delivery,
with peer/device identity binding and existing anti-replay state preserved.
[GUI evidence, limitations and rollback](releases/2026-09-13-amsterdam-gui.ru.md).


## Amsterdam real-network pilot passed — 2026-09-13

User authorized new empty VPS186.246.45.246: Ubuntu26.04,1 vCPU,955MiB RAM.
Native WireGuard UDP51820/MTU1280 installed, one locally generated client peer;
server key generated on-server. Service active+enabled, scoped nftables NAT/filter.
Final isolated Linux netns run passed DNS, two HTTPS egress checks (IP186.246.45.246,
countryNL),1MiB download, private-network/IPv6 refusal, server service restart and
full client reconnect. Server rekey readiness16.615s; host routes/rules/DNS unchanged.
Two preliminary failures retained: HTTPS immediately after server restart, then DNS
failure after bare client link down/up. Bare link toggle remains unaccepted; final
scenario recreates the complete connection. Not a fix/closure of TD-1 stability debt.
SSH key access verified; mandatory initial password change handled outside Git.
Private profile retained in ignored state-enroll/amsterdam-pilot, not imported in GUI.
Next: Amsterdam profile in paired Linux application, then external trusted Reticulum
relay and alternate transport checks. Native Windows/Android protected state remains.
Python462 and operator-script syntax checks passed.
No existing gateway/client install/catalog/main changes; Stage6 only partially begun.
[Deployment, evidence and rollback](releases/2026-09-13-amsterdam-pilot.ru.md).

## Android Stage5 verifier accepted — 2026-09-13

Source24159206a661bc7cea31a8f19d7c57c19f5796a1: Java schema2 configuration/ACK
verifier, pinned BC1.85.2/Gson2.13.2 with APK licenses. Local JVM:30 configurations,
15 ACK,32 structure+4 authenticated-cipher+12 JSON/UTF8 refusals passed; Python462.
Clients34750425107: linux:success, android:success, windows:success, release:skipped.
Phase034750425189 passed. Android runtime acceptance: True.
Manifest SHA256 c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
Fixtures confined to test assets; APK gate checks their absence and dependency licenses.
Next: protected Windows identity/journal/outbox and shared broker ownership, then
Android protected state. Native transcripts/carrier/VPN apply remain unimplemented.
No release/install/catalog/server/main changes; Android0.1.0/code1 unchanged.
[Implementation and CI receipts](releases/2026-09-13-android-control.ru.md).

## Windows Stage5 verifier accepted — 2026-09-13

Source38b055431758e3f2b80de1adfbf9df04cb299fcb (implementation581f83f): native
C# schema2 configuration/ACK verifier. Windows CI34749302222/job103702791743
passed30 configurations+15 ACK and31 extra structure refusals plus legacy checks.
Manifest SHA256 c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd
confirmed by Windows annotation. Local .NET and Python462 passed; phase034749302284
passed. Clients34749302204: linux:success, android:success, windows:success, release:skipped.
First CI had five startup_failure runs before jobs; GitHub unexpected error recorded.
AWG/TCP/Linux-control original runs did not execute; no new acceptance claim for them.
Next: Android verifier, then protected Windows identity/journal/outbox and broker
ownership. Native transcripts/carrier/VPN apply remain unimplemented.
No release/install/catalog/server/main changes; desktop0.2.9, installed Linux0.2.8.
[Implementation and CI receipts](releases/2026-09-13-windows-control.ru.md).

## Stage5 conformance corpus accepted — 2026-09-13

Source598454bad71fdf290a673c0f10a7f4afa61e2b18: immutable PUBLIC TEST ONLY
30 configuration inputs,15 ACK inputs,3 transcripts/16 steps.50 vector checks,
full local462 Python passed. Linux control34748501643 and phase034748501640 passed.
CI vector manifest digest matches committed corpus; paired archive digest unchanged
from the accepted live Linux bundle.48 corpus files preserve bytes under autocrlf=true.
Generator refuses overwrite and has no key-file inputs. No runtime/client/server changes.
Next: Windows native verifier against these exact bytes, then Android verifier and
protected identity/journal/ownership. Native Stage5 not implemented by this corpus.
[Conformance acceptance](releases/2026-09-13-control-vectors.ru.md) ·
[Portable fixture format](../tests/vectors/README.md).

## Linux health CI and Android diagnostic rerun — 2026-09-13

Health source d7c3d79: Linux control34747139792, phase034747139671,
AWG34747139717 and TCP34747139660 passed. CI archive SHA256 matches the live bundle.
Initial Clients34747139704: Windows/Linux passed, Android emulator failed; raw logs
API403, precise cause unavailable. This failure remains recorded, not erased.
Diagnostic-only source9092594 adds bounded JUnit annotations and scoped Android CI,
without app/test/timeouts changes. Android34747632083, Clients34747632066
(Windows/Linux/Android) and phase034747632071 passed. Initial transient cause unproven.
All public pilot reports and final CI receipts documented in the acceptance branch.
Next: native Stage5 interop vectors, protected identity/journal/outbox and shared
ownership; Windows broker first, then Android service. No native Stage5 implementation
claim, release/main merge/install/server changes. TD-1, AWG3.1 and Stage6 remain open.
[CI evidence](releases/2026-09-13-linux-control-ci.ru.md) · [Native plan](stage5-native-binding.ru.md).

## Linux paired live pilot passed — 2026-09-13

Corrected bundle66152538ee2a4f3e passed real RNS config2 apply/ACK, GTK selection,
interface-bound HTTPS gateway egress and DNS. Config3 process death after actual
apply preserved pending ownership; recover restored config2 and HTTPS. Duplicate3
returned ROLLED_BACK with ACK delivery; real GUI Disconnect/close and exact IPv4/6
policy-rule cleanup passed. Final journal IDLE/floor3/committed2/outbox0; pending=null.
Three pilot imports now retained inactive; installed Linux0.2.8 unchanged.
Packet metadata disproved the earlier inference of TCP setup failure: handshake and
client payload reached gateway; large response ranges failed to reach the laptop.
MTU1280 worked and was signed into config2/3, but restored1420 also passed once:
location/cause of size-sensitive loss and long-term stability remain unproven (TD-1).
Local412 tests and corrected package manifest previously passed; no new remote CI,
release, install or server mutation. Next: scoped CI for the health correction, then
native Windows/Android Stage5 binding. Local relay does not close independent Stage6.
[Packet evidence and live acceptance](releases/2026-09-13-linux-control-pilot-pass.ru.md).

## Live Linux pilot: traffic gate correction — 2026-09-13

Real RNS config1 applied, ACK delivered and paired GTK selected the active imported
WG profile. Independent bound HTTPS then failed; pilot stopped before crash recovery.
Bounded diagnosis: direct IPv4 HTTPS passed; both default/IPv4 TUN HTTPS timed out
before TCP connect, interface DNS passed. Cause is not established.
Cleanup passed: all VPN inactive, existing profiles preserved, IPv4/IPv6 policy rules
restored. One inactive pilot import retained. Journal IDLE/floor1/committed revision1:
old active-only health caused this commit; do not treat it as network acceptance.
Fixed control WG health to require interface-bound HTTPS/expected gateway egress
before candidate selection and commit. Local412 Python passed (including extracted
package); new bundle66152538ee2a4f3e manifest verified. No remote CI/release/install.
Next: request-to-flow diagnosis of WG HTTPS, then corrected bundle live acceptance
and crash/rollback/GUI return. Never reuse old accepted preview for live config apply.
Keep permanent identity/journal and issue higher revisions; no state reset.
[Live result, fix and limits](releases/2026-09-13-linux-control-live.ru.md).

## Registered Linux control pilot — 2026-09-13

User requested preparation of the permanent registration and trusted relay.
Prepared private `state-enroll/control-linux-pilot`: permanent device/relay identities,
real API enrollment, explicit local RNS configs, journal and offline-signed envelope1.
Real two-process RNS delivery with the extracted accepted bundle passed; signature,
device binding and byte equality verified. Journal remains IDLE/floor0; no VPN apply.
One isolated gateway peer10.77.0.252/32 installed by the periodic worker; three prior
WG peers preserved. Gateway lease expires 2026-09-13T08:43:59+00:00;
envelope expires 2026-09-13T08:40:14+00:00. Registration is retained for reuse.
Relay was stopped after the check. Local relay is not Stage6 independent ingress.
Next: bounded paired GUI/control apply, independent traffic health, recovery/return.
If expired, renew the gateway lease and issue/publish a higher signed revision using
the same identity/journal; never reset state. Native Windows/Android binding follows.
[Preparation and evidence](releases/2026-09-13-linux-control-resume.ru.md).

## Paired preview acceptance — 2026-09-13

Local409 Python passed, including66 extracted protocol/arbiter scenarios. Scoped
Linux CI34722755860 passed on247d16b; Docker272 tests and full phase034722963403
passed on3a28be7. CI tar.gz SHA256 matches the local preview. Previous Clients
Windows/Linux/Android all passed. Added local-only recover CLI, retaining ACKs
and pending state on failure. Manual paired pilot/return plan prepared.
Observed installed Linux **0.2.8**, previous0.2.7; old GUI has no arbiter. No
installation, profile mutation, release, catalog update or server changes.
Next: separate-directory manual paired preview pilot, then native Stage5 binding.
AWG3.1, TD-1 and Stage6 remain open.
[Acceptance evidence](releases/2026-09-13-linux-control-acceptance.ru.md) ·
[Manual rollout/return](linux-control-preview-rollout.ru.md).


## Paired Linux control preview — 2026-09-12

Operator GUI/core bundle added with an explicit public-file allowlist, integrity
manifest, runtime-only pinned dependencies and extracted launcher. Legacy six-file
desktop archive unchanged. Local405 Python passed; extracted real RNS lifecycle
and GTK smoke passed. Scoped Linux control CI34720569558 passed on source d8aef8a.
AWG/TCP pilot passed. Docker test-stage dependency omission reproduced and fixed
in ac6a22f: complete public desktop bundle + VERSION copied into tests stage only.
Local Docker250 tests passed; phase0 run34720868247 fully passed including build,
failover/auth/offline/revocation/cleanup and Python/Rust. Clients Windows/Linux
passed; Android subsequently passed (see 13.09 acceptance above).
[Docker fix evidence](releases/2026-09-12-control-docker-fix.ru.md).
No release/install/catalog/server changes. CI acceptance completed; manual paired pilot next; native Windows/Android binding, AWG3.1 and TD-1 remain open.
[Preview checkpoint](releases/2026-09-12-control-preview.ru.md).


Общий план и критерии этапов: [ROADMAP](ROADMAP.ru.md). Реализация транспортов Windows/Android завершена и принята в scoped CI. Reference core этапа 5 реализован и проверен локально; далее интеграция/приёмка перед распространением; выпуск и отложенная приёмка этапа4 остаются открытыми.

## Current next work after Linux GUI coordination

Shared GUI/control operation ownership implemented and locally accepted (402 Python,
GTK recovery/24 layouts). [GUI coordination and short network checkpoint](releases/2026-09-12-control-gui-network.ru.md). Coordinated GUI/core packaging and scoped CI,
then native Windows/Android binding remain before background distribution.
Short network tests are now explicitly authorized and resumed: routes/DNS/cleanup
passed, HTTPS4/6 with two timeouts. Matched direct/TUN diagnosis now passed24/24
across Python HTTP1.1 and curl HTTP2; failures did not reproduce, no causal fix.
TD-1 remains open: obtain request-to-flow evidence when a bounded run fails.
Continue coordinated Stage5 GUI/core packaging and scoped CI. No automatic long
load/device campaign. AWG3.1 migration remains TD-2.
Independent entry/alternate gateway acceptance remains Stage6.

## Stage 5 reference protocol/application core — implemented locally

2026-09-12: carrier-independent signed config, journal, apply/health/commit/rollback,
device-signed ACK/outbox and real RNS delivery pass 381 Python tests. [Stage 5 checkpoint](releases/2026-09-12-reticulum-control.ru.md).
Current acceptance is reference Python/Linux; native/background distribution needs
common operation ownership with GUI, native storage/binding, packaging and scoped CI.
AWG3.1 stays a separate migration; Stage5 has explicit transport-version refusal.
Stage6 infrastructure independence and user-deferred device/load tests remain open.

## Completed: 0.2.1 rollout

Platform CI and immutable release published; Linux installed with backup; gateway,
product DB/API and periodic worker deployed. Health and preservation of three legacy
peers verified. Signed catalog sequence 1 published. See STATUS for exact evidence.

## Completed user priority: 0.2.2 visual refresh

Desktop artifacts published, platform CI passed, signed catalog sequence 2 published.
Linux installed through the existing 0.2.1 updater; Windows update available in app.
Temporary editable dodecahedron icon; revisit icon design later.

## Completed: 0.2.3 polish and quiet polling

Windows/Linux polling and layout regressions passed. Artifacts and signed catalog
sequence 3 published; Linux installed with previous version retained. Windows update
available through Check for updates; awaiting user confirmation of 0.2.3 behavior.

## Completed: 0.2.5 Linux fit and responsiveness

Platform CI passed; catalog sequence 4 published; Linux upgraded from 0.2.3 with
rollback retained. Real laptop startup visibility and themed-dialog cancellation checked.
Confirm user perception of startup/steady-state responsiveness: a first probe had an
850 ms gap, follow-up warm measurement max 17.9 ms. See STATUS for exact evidence.

## Completed: 0.2.6 narrow window

User preference: narrow window, one action per row at every width, height by content.
Platform CI and real-display checks passed; catalog sequence 5 published; Linux
installed with previous version 0.2.5 retained. Await user visual confirmation.

## Completed: 0.2.7 native Linux frontend

User reports sequential redraw and wants a finished visual design. GTK 4/libadwaita
implementation passed local, real-Wayland and platform CI checks. Immutable release
published, catalog sequence 6 signed, Linux upgraded through the 0.2.6 updater with
rollback retained. Tk is no longer the Linux frontend. One-column, narrow/content-sized
layout and backend behavior preserved. User explicitly approved its appearance and behavior; see STATUS for measured evidence.

## Completed: Windows 0.2.8 visual alignment

User approved Linux 0.2.7 appearance and behavior. Windows now follows its compact composition. Runtime layout/interaction checks passed;
immutable release and signed catalog sequence 7 published. Next: user updates Windows
and confirms its appearance (currently reports 0.2.7). Main catalog propagation verified.
User still needs to import the Windows activation and Android profile and test connectivity.
Linux 0.2.7 remains installed; server unchanged.

## Completed: live product enrollment/revoke smoke

2026-09-10: isolated test identity enrolled through the deployed HTTP API, staged,
installed by the periodic worker, provisioning published/fetched and verified locally.
Replay and post-revoke fetch rejected; worker removed the live and persisted test peer.
All three legacy peers preserved; test entitlement/device revoked, audit/reservation kept.
No client runtime application or real handshake claimed. See [report](live-product-smoke.ru.md).

## User priority: resilience against blocked servers/protocols

2026-09-10: AWG 2.0 added alongside WG on separate UDP/51821. Linux helper/profile
installed, actual host connection and blocked-WG → AWG fallback passed. Original WG
peers preserved. Working-tree client pilot available separately from stable releases.
See [rollout and remaining checks](releases/2026-09-10-awg.ru.md).

## Android WG/AWG/TCP/Auto accepted; next Reticulum

Android WG/AWG passed four-ABI build, 12 unit methods, lint and real API35 x86_64
emulator:24 encrypted UDP,4 stops,cancel,system revoke (clients34660308853).
One runtime fixed WG→AWG→WG crash; profiles remain independent and encrypted.
TCP accepted: clients34676190826/source8d748f5, four ABI,18 unit,18 REALITY HTTP,
3 OS DNS calls,36 WG/AWG UDP and13 cleanup scenarios. Auto accepted in clients34679094884/sourcea51aa52: initial fallback, ongoing health
loss, finite exhaustion, cancellation and revoke. Next stage5 Reticulum.
Device update/testing stays deferred. [TCP report](releases/2026-09-12-android-tcp.ru.md).
See [Android WG/AWG report](releases/2026-09-12-android-awg.ru.md) and [Auto acceptance](releases/2026-09-12-android-auto.ru.md).

## Next, in order

1. Stage5 reference core is implemented locally (381 tests): shared Linux GUI
   operation ownership now passes local checks; native binding, coordinated packaging
   and scoped CI remain before background distribution.
   Android updater/Google Play and user-deferred device/load tests do not gate this work.
2. Before distribution: full-routing/external gateway/REALITY and actual device acceptance,
   Android release signing/versioning. APK updates and extended device/load tests remain deferred;
   short network checks were explicitly resumed and found HTTPS timeouts. Desktop0.2.9/catalogseq8 and TCP Setup0.1.0 remain published.
3. Deferred resilience experiments: concurrency1→4→8, request-to-flow diagnosis and
   second Ubuntu retest. Second independent VPS only when supplied by user; never use
   the test laptop or neighbouring services. Current timeout/stability limits remain open.
4. Native enrollment/storage, signing-root rotation/recovery, then payments/notifications.

Next development stage5; stage4 distribution/device acceptance remains open, not stable multi-platform resilience. Details, results, backups and unfinished
work: [session checkpoint](releases/2026-09-11-session-checkpoint.ru.md).

## Windows и Android реализованы; следующий блок — Reticulum (2026-09-12)

Текущий engine-crash recovery завершён отдельным отчётом; новых подпунктов в него не добавлять.
Мониторинг недоступного соединения при живом процессе завершён и проверен в scoped CI.
Интеграция AWG принята в scoped CI2026-09-12; [результат](releases/2026-09-11-windows-awg-integration.ru.md).
Автоматическое переключение Windows принято в scoped CI2026-09-12:672 макета,7 policy-сценариев,
живой AWG→TCP, отмена, исчерпание и очистка после SCM restart. Android WG/AWG/TCP/Auto также принят; далее Reticulum.
[Отчёт и границы приёмки](releases/2026-09-12-windows-auto.ru.md). Полный маршрут/REALITY требуют отдельной
приёмки до выпуска. Отложенные пользователем испытания на устройствах/под нагрузкой
не возобновлять автоматически и не смешивать с реализацией.
Android WG/AWG/TCP/Auto принят в эмуляторе; следующий шаг — этап5 Reticulum.

Latest bounded network comparison: [Matched HTTPS result](releases/2026-09-12-matched-https.ru.md).
