# Existing-users private Android update / Частное обновление Android

**31 October — beta107 publicly distributed, Android12+/ARM64.**
The invitation page and both Android update catalogs now offer107 with MESH support and
quiet foreground-notification updates. Hosted CI, signed APK and public HTTPS byte checks PASS.
The owner authorized expedited general rollout without phone debugging; physical107 upgrade
and owner runtime remain NOT_RUN. Updates are optional; install over the existing app, never
uninstall, clear data or reenroll. Restricted admission is unchanged; canary stays PAUSED.
RU: общий выпуск107 опубликован; Android12+, установка поверх без удаления данных.
[Same-operation evidence](../releases/2026-10-30-nl-gateway-replacement.md).



## Current status / Статус

###23 October / closed group READY — актуальная передача

RU: **PRIVATE_FIELD_READY** для FC-4D8Q-REEG + FC-ZMVK-MM7C + FC-YHQB-9VJN.
Прежний подписанный106, без новой установки owner. Серверная политика P1 для
трёх устройств включена и проверена; после штатного gateway restart owner106
восстановил P1, малый HTTPS PASS. Раздаёт владелец, без публичного выпуска.
Волгоградский отчёт21 подтверждает **beta96/CELLULAR/MESH** и передачу; владелец
передал точное сообщение тестировщика об успехе в белых списках. Это положительный
полевой результат96, не проверка106/P1 или холодного bootstrap. Старый incident94
и ненулевые счётчики96 сохранены. Краснодар/106 P1 ещё не проверены в поле.
EN: the unchanged signed106 is ready for manual private handoff to the exact three.
Server policy, post-deploy owner P1/body, prior Wi-Fi/recovery and static65/96 upgrade
paths pass. The positive Volgograd96 field result is separate from future106/P1
acceptance. Install in place, select ordinary P1 while disconnected, make one mobile
MESH attempt without a mandatory Wi-Fi warmup and return JSON regardless of outcome.
[Current report/file/rollback](../releases/2026-10-23-tester-p1-cohort.md) ·
[Exact RU/EN steps and checksum](OWNER_RECOVERY_CANDIDATE.md).

The owner-only paragraphs below are earlier dated checkpoints, not the current gate.

###23 October / earlier signed106 installed owner-only

RU: readback105 сохранён до изменений; свежий JSON был недоступен при активном
USB-допуске. Завершён узкий diagnostic106:219 JVM/replay PASS,12 native-библиотек
неизменны. Подписан прежним ключом, установлен поверх105 без удаления данных;
UID10283/Support ID сохранены, свежий JSON работает. Обычный Connect сохраняет
Android P1 на Wi-Fi; полная передача и автоматическое recovery — отдельные gates.
EN: same-signer106 is signed and installed over105 on the owner, not distributed.
Fresh diagnostics/identity and ordinary Wi-Fi P1 Connect are verified. No global
profile change; tester P1 still single-owner, whitelist NOT_RUN. PRIVATE_FIELD_READY
remains NO pending group policy. Public versions unchanged.
Follow-up: bounded106 Wi-Fi19/19 bodies, ordinary Disconnect/Connect and small
HTTPS pass. RU: после ручного отключения/возврата Wi-Fi новая MESH/P1-сессия
восстановилась без Connect; полный1КиБ HTTPS PASS3,733с. Восстановление заняло
106,578с от появления Wi-Fi, не мгновенно. EN: automatic Wi-Fi return independently
passes with both-end P1 and a full small response; this is not merely explicit
Connect or overnight stability. Next: confirm the current closed P1 cohort and
extend the single-owner server policy; no global switch/new enrollment. Historical
tester IDs FC-ZMVK-MM7C/FC-YHQB-9VJN do not establish current cohort/versions.
[Current evidence/next action](../releases/2026-10-23-wifi-resume.md).

The following dated checkpoints are historical, not the current owner installation.

### Wi-Fi correction / reconciled beta105 —22.10

RU: владелец22.10 сообщил об исчерпании мобильного пакета/ограничении оператора и
нормальной работе на Wi-Fi. Это сообщение, не новая инструментальная приёмка;
скорость/начало/версия той ручной проверки неизвестны. Старые отказы не удалены,
инциденты Волгограда/Краснодара этим не объяснены. Readback receipts подтверждает
104→105 установку12:13UTC, а штатный online19:42UTC —105/Wi-Fi/TUN/P1. Подписанный105
перепроверен без пересборки. USB уже подключён: установленный APK/signer/UID/native
совпали. Штатный USB JSON недоступен, хотя допуск действует; последний status off.
Полученный затем JSON15 содержит старый снимок19:43UTC; общий budget записи
воспроизводимо переполняется локально. В21:10 USB-допуск уже отключён — нужен
штатный диалог на1час, затем свежий readback до передачи/recovery. Новый APK не создан.
Серверный P1 остаётся owner-targeted. **Не PRIVATE_FIELD_READY.**

EN: owner reports exhausted mobile data/throttling and normal Wi-Fi operation;
do not reclassify historical failures as PASS or generalize to testers. Existing105
is signed and installed per receipt, with later reduced online Wi-Fi/P1 evidence.
USB now verifies installed bytes; snapshot export fails despite active consent and
latest VPN status is off. Owner body/recovery awaits normal JSON; tester P1 policy is
not ready. Static88/94/104 update metadata is verified, not physical tester migration.
No automatic/public distribution, catalog or invitation changes.

Follow-up: normal export15 arrived but contains a stale19:43UTC ring. Local105 replay
reproduces aggregate record overflow; no fix shipped. Latest USB status explicitly
denies consent; normal one-hour consent is the next manual gate, not another export.

[Exact APK/hash and RU/EN preflight/field instructions](OWNER_RECOVERY_CANDIDATE.md)
· [Delivery receipt](../releases/2026-10-22-private-field-delivery-receipt.json).
The headings below retain historical release checkpoints, not current readiness.

### Owner recovery102→103,22.10 — not a tester rollout

RU:102 установлен владельцу поверх101 с прежним signer/UID/Support ID; P1 на обоих
концах сохранён. Обрывы RS продолжаются, два HTTPS-контроля не прошли. Исправлен
отдельный DNS-health механизм;103 собран с узким исправлением дедлайна служебного
refresh (213 JVM/12 bridge PASS).103 подписан и установлен поверх102; APK`0d274fe5…`,
подробные receipts в [отчёте](../releases/2026-10-22-owner-disconnections.md).
**Не рассылать как PRIVATE_FIELD_READY:** текущая server policy P1 только owner,
проверка Волгограда/Краснодара NOT_RUN. Публичные каталоги/страница приглашения
не менялись. [APK, checksum и RU/EN инструкция](OWNER_RECOVERY_CANDIDATE.md).

EN: owner-only recovery candidate, not an accelerated tester rollout. Same identity,
signer and native libraries; primary RS loss unresolved.103 is signed/installed;
physical acceptance awaits renewed USB permission. Whitelist field validation
remains NOT_RUN. Existing public artifacts/catalog/invitation versions are unchanged.

### Owner-only101 lifecycle continuation / Продолжение владельцу101

RU:101 `0.1.18-beta101-lifecycle` установлен поверх100, прежний signer/UID/данные.
Улучшена только ограниченная история и классификация lifecycle; сырые счётчики,
транспорт, Q0, окна и восстановление не изменены.203 JVM и Go race PASS. USB-допуск
обновлён владельцем. Повторяемое ускорение P1 сохраняется как доказанный результат;
новая адресная lifecycle-приёмка продолжается. Это не массовый выпуск.

EN:101 installed owner-only over100, same signer/UID/data. Bounded incident retention
and contract classification only; raw counters/dataplane unchanged.203 JVM and Go
race pass. Owner renewed USB access. Confirmed P1 speed evidence is preserved;
fresh bounded lifecycle acceptance is in progress, not a public/fleet release.

Private APK:`state-client-build/p1-lifecycle-101-20261021/delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk`.
SHA256:`3c023e39d95e29fe0561dc462e28f1e643b9e14558cf49700d58df528b2963d9`.
Invitation/catalog/download URLs unchanged; no publication or tester delivery.

### Owner-only100 lifecycle,21.10 / Наблюдение100 владельцу

RU:100 `0.1.18-beta100-lifecycle` установлен поверх99 тем же ключом/UID, без удаления
данных. Новая P0/P1/P1/P0 серия дала2,30×/2,28× single, все60 тел получены.
Но15мин P1 имеет не полностью разобранные9/3 события Android/gateway: P1 не принят.
Владелец возвращён в P0, TUN DNS/HTTPS smoke проверен. Другим пользователям не рассылать.

EN:100 is installed owner-only over99, same signer/UID and preserved data. Bounded
lifecycle observation; repeated single speed2.30×/2.28×,60/60 matrix bodies.
P1 not admitted:15min event provenance incomplete. Owner restored P0 with TUN
DNS/HTTPS smoke verified; no fleet delivery.

Private APK:`state-client-build/p1-owner-acceptance-20261021/delivery/FamilyConnect-0.1.18-beta100-lifecycle.apk`.
SHA256:`1eb04cc6082f6a03380b99e8a47053d51efd8e6098c0c135075ac030228061e0`.
[Acceptance status and limits](../releases/2026-10-21-p1-owner-acceptance.md).
Public invitation/catalog links are unchanged.

### Owner-only99 support timing,21.10 / Исправление интервала99

RU:99 `0.1.18-beta99-support` установлен владельцу поверх98 тем же ключом/UID.
Исправлен отсчёт интервала онлайн-отправки:60с после завершения, не после начала.
Native и все транспортные настройки не менялись.198 JVM/41 Python проверок PASS.
После обновления владелец однократно подтвердил USB-допуск; подключение выполнено
автоматически. Новая99 P0 MESH-сессия подтверждена на обоих концах: READY/TUN открыт,
эффективное RS8/LEGACY64. Онлайн-согласие сохранено, три отчёта дошли с интервалами
62/69с. Короткий текущий ноль ошибок не объясняет старые отказы. Другим пользователям
сборка не разослана, диагностика не включена.

EN: Owner-only99 fixes completion-based upload cooldown; same signer/package/UID and
byte-identical native libraries.198 JVM/41 Python tests pass. Package replacement
ends the VPN and process-local USB consent; after a renewed grant, automated P0
reconnect is verified on both ends. Online opt-in persisted and three99 reports
arrived62/69s apart. No long-term/speed acceptance or tester/public rollout.

Private APK: `state-client-build/support-cadence99-20261021/delivery/FamilyConnect-0.1.18-beta99-support.apk`.
SHA256: `fae38b81f39b4f813d172f07380b3fd6265b0c3bee3a99ff1d7539d4f1213b0e`.
Native: `3f700aef7952c67de69de1de7cd6878287ed51d6b97be28c464d304a4cfb6673`.
Invitation page/public catalogs remain unchanged. The98 section is historical.

### Owner-only98 support automation,21.10 / Автоматизация поддержки98

RU: На телефоне владельца установлен98 `0.1.18-beta98-support` поверх97, без очистки
данных, тем же ключом. Это автоматизация поддержки, **не новый speed-профиль**.
Онлайн-диагностика включается отдельно добровольно на7дней; отправляет только
ограниченные состояния/счётчики, не сайты, ключи, сообщения или полный журнал.
Первая реальная квитанция98 получена. Рядом отдельная кнопка USB-поддержки на1час:
после её подтверждения доверенный ADB-компьютер забирает снимки и управляет
подключением/P0/P1/P2 для новой сессии. Доступ других приложений закрыт; сетевого
удалённого управления нет. USB выключается повторной кнопкой/по истечении часа/
перезапуску процесса, онлайн — своим переключателем. Telegram JSON больше не нужен
для текущей owner-проверки. Приложение не является постоянным background collector
при убитом процессе. Другие пользователи пока не обновлены/не включены.

EN: Owner-only98 adds explicit, expiring USB automation and optional online technical
snapshots, not a transport/speed change. Default OFF; existing identity authentication,
no traffic content, public debug endpoint or remote network commands. Initial real
upload and automatic USB snapshot are verified. No tester/public rollout; desktop
upload integration is not shipped. The ordinary APK update interrupts the owner's
VPN; confirm a new P0 session rather than assuming continuity. Disable features in
Settings without downgrading or resetting identity/security history.

Private APK: `state-client-build/support-automation-20261021/delivery/FamilyConnect-0.1.18-beta98-support.apk`.
SHA256: `a6f534f8a4258fc51ea961b7ca4f9b0512b8a38a96655fc57e2bb5c343be56c8`.
Native: `3f700aef7952c67de69de1de7cd6878287ed51d6b97be28c464d304a4cfb6673`.
Package/signer unchanged. No invitation-page/catalog/public download update.
[Report / Отчёт](../releases/2026-10-21-owner-support-automation.md).

### Owner-only97,21.10 / Только владелец97

RU: У владельца поверх96 установлен подписанный97 `0.1.18-beta97-speed`, UID,
ключ подписи, identity и Support ID сохранены; READY97/MESH подтверждены.
Это кандидат RS32/Mux128/Q1 для ограниченного сравнения, **не рекомендация
тестировщикам**. Возврат P0 был проверен на обоих концах: effective8/LEGACY64.
В финальном P0b single и12 малых ответов получены; два parallel оборвались при
подтверждённом штатном renewal шлюза. Нагрузка остановлена, повтора нет. На шлюзе
после renewal новая P0-сессия подтверждена и телефоном в `(14)`: CONNECTED/READY,
effective8/LEGACY64. В ней17 protocol errors, причина не установлена; это не17
потерянных загрузок. **Цикл закрыт, оставляем P0. Больше действий и JSON не нужно.**
Все ошибки сохранены, чистой приёмки нет; новой сборки/отката не нужно.
P1/P2 не включать автоматически; ключи, identity и история безопасности сохраняются.

EN: Owner-only signed97 is installed over96, preserving signer, UID and identity;
READY97/MESH verified. It is not a tester/public release or speed-admitted build.
Return to P0 was verified at both ends: effective8/LEGACY64. Final P0b single and
12 small responses completed, but two parallel bodies were truncated during proven
scheduled gateway renewal. Load stopped, no repeat. A new gateway P0 session is
confirmed by Android `(14)`: CONNECTED/READY, effective8/LEGACY64,17 protocol errors
in the new session, cause unknown (not17 lost downloads). **Cycle closed; keep P0.
No more actions or diagnostic exports required.** All failures remain, no clean admission.
No new build/downgrade or automatic P1/P2 enablement; identity/security history retained.
Do not forward this experimental97 to the Volgograd tester automatically.

Private artifact: `state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk`.
SHA256: `d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f`.
No public download/catalog/invitation link changed. The tester96 handoff instructions
below are historical/separate; tester receipt and installation remain unverified.
[Owner integration, limitations and current state](../releases/2026-10-21-android-speed-candidate.md).

### Previous96 handoff / Предыдущая передача96

**20.10 bootstrap candidate96 / Кандидат96:** signed with the existing key;
**owner95→96 installed14:48:37UTC**, same package/UID and native95/A0. Fresh server
identity/Support ID bindings unchanged; post-update96 READY/device proof and Connect
remain NOT_RUN. The candidate fixes a reproduced RNS availability/cache classification
defect and adds bounded diagnostics; historical Volgograd cause/mobile restoration
remain unproven. Last negotiated LEGACY64;128 OFF, no active VPN after update.
Owner requested private handoff to FC-ZMVK-MM7C; tester receipt/update from94 not yet
confirmed. No public download/catalog/invitation link is published.

Signed file: `state-client-build/mobile-bootstrap-20261020/delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk`.
SHA256: `07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d`.
RU: Передавать именно этот подписанный96, не95 и не unsigned APK. Установить поверх
текущего Family Connect через «Обновить», не удалять приложение и не очищать данные.
Новая регистрация/приглашение не нужны. Затем один раз подключиться на мобильной
сети, без Wi-Fi, и сразу экспортировать штатную JSON-диагностику независимо от исхода.
Не повторять попытки серией. Сохранить Support ID FC-ZMVK-MM7C и указать время попытки.
EN: Install this signed96 over the existing app; do not uninstall, clear data or
reenroll. Make one cellular connection attempt with Wi-Fi off, then export the normal
diagnostic JSON whether it succeeds or fails. Keep Support ID and attempt time.
This is a targeted candidate, not a proven whitelist/mobile fix.
[Exact scope, signed artifact and validation limits](../releases/2026-10-20-volgograd-mobile-bootstrap.md).

**20.10 owner-only95 / Только владелец:** owner updated94→95 with existing package,
signer, UID and data preserved; fresh READY and identity/Support ID checks PASS.
Negotiated64/128 support is implemented. Three manual A/B pairs completed20.10:
**INCONCLUSIVE**, not an accepted speed release. All24/24 phase requests completed,
but final pair single gain3.65% accompanies aggregate−13.61% and control latency+23.28%.
New-session128 is **OFF**. Owner's ordinary manual reconnect created VPN336;
actual LEGACY64/65536 both endpoint contracts confirmed20.10 13:39:52UTC via
authenticated ALPN/runtime and pinned binaries. Owner remains95/A0; return complete.
Compatible gateway preserves b9/1011 and legacy clients. Counters OFF, no background
collectors or more bulk. No public artifacts changed; no APK/install change this phase.

Owner-only APK: `state-client-build/mux-profile-20261020/delivery/FamilyConnect-0.1.18-beta95-mux-profile.apk`.
SHA256 `e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159`.
RU: Тестировщику оставляем94 ниже;95 ему не рассылать. На owner не ставить94
поверх95, не удалять приложение/данные и не активировать повторно. Возврат окна64
подтверждён после обычного ручного переподключения; дальнейших действий не требуется.
Новый APK для удаления счётчиков не нужен; дополнительных замеров не планируется.
EN: Keep testers on94. Do not distribute95 as a speed update. Owner must not
downgrade or clear data. Return verified on a new LEGACY64 session after ordinary
manual reconnect, not reinterpretation of128. No further action or bulk is required.
[Implementation, completed experiment and current gateway](../releases/2026-10-20-mesh-mux-credit.md).

### Tester94 and historical owner94 handoff

**20.10 preceding Mux check / Предыдущая проверка Mux:** ordinary tester APK is
still94/A0, not93. No new APK was needed for the server-only counters; exactb9/1011
is restored and final10:30UTC phone control passes. No accepted speed fix yet.
Private handoff copy: `/home/joker/Downloads/FamilyConnect-0.1.18-beta94-stability.apk`,
SHA256 `fe32f36d0705d83705e549f598512305d63fd942a415f71afaebfd91534f8e13`.

RU: Если тестировщику уже передан этот94, версия правильная, повторно отправлять
тот же файл не нужно. Обновлять поверх приложения с сохранением данных; без
удаления/очистки/повторной активации. Пользователь сообщил об отправке, но версия
на устройстве тестировщика и работа в условиях белых списков ещё не подтверждены.
EN: If this94 was already sent, it is the correct build; no identical resend is
needed. Same-app update preserving data, no uninstall/reenrollment. Reported private
delivery is not verified tester installation or whitelist acceptance. No public
download/catalog/invitation artifact changed.
[Mux results and compatibility limit](../releases/2026-10-20-mesh-mux-credit.md).

**20.10 RTP experiment closed / Эксперимент завершён:** owner now has
`0.1.18-beta94-stability` / code94, installed over93 at09:30:02UTC; final09:44UTC
readback confirms VPN, exact baseline92 native and unchanged b9/1011. Candidate93
was tested, not speed-accepted.94 restores the original arrival-driven100ms policy;
it is **not a new speed release**. Same package/signer, UID10283 and data preserved.

- Current private file: `state-client-build/rtp-deadline-20261020/normal94/delivery/FamilyConnect-0.1.18-beta94-stability.apk`.
- APK SHA256: `fe32f36d0705d83705e549f598512305d63fd942a415f71afaebfd91534f8e13`.
- Native SHA256: `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- 169 JVM checks PASS; all12 native libraries equal baseline. Fresh94 READY and
  identity/key-binding/Support-ID proofs pass.9/9 measured bulk requests complete;
  speed acceptance remains unestablished. No public/download/catalog/invitation
  artifact changed; extended trace OFF throughout. Tester88 was the preceding
  recorded version; the current94 handoff and unverified sent version are described above.

RU: На owner установлен94 поверх93 без удаления данных, изменения ID, ключей,
Support ID или повторной активации. Ничего переустанавливать сейчас не требуется.
**Не ставить92/93 поверх94 и не очищать данные.** Для будущего изменения нужна
обычная сборка с прежними package/подписью и code>=95. Архивный93 — эксперимент,
не рекомендация к установке. Доступность удалённого тестировщика не требовалась.

EN: Owner is already on94, a forward policy rollback preserving data and identity.
No action or reactivation is needed. **Do not downgrade to92/93 or clear data.**
Any future change needs the same package/signer and code>=95. Archived93 is an
experiment, not an accepted speed update or a public download.
[Exact A/B/A, limitations and artifacts](../releases/2026-10-20-mesh-receive-path.md).

### Historical beta92 trace-off return

**20.10 trace-off return / Снятие диагностики:** normal code92 installed over91 at
19.10 23:23:16UTC, UID10283 unchanged. Exact90 native/recovery,169 checks PASS.
This is **not a speed fix / не обновление скорости**. Private APK:
`state-client-build/mesh-receive-path-20261020/normal92/delivery/FamilyConnect-0.1.18-beta92-stability.apk`.
SHA256 `1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b`.
Native SHA256 `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
RU: Установлено поверх91 после обычного «Отключить», без удаления данных,
нового ID, приглашения или копирования ключей. Не возвращаться на90/91 downgrade.
EN: Same-app forward update; no uninstall, data clearing, reenrollment or downgrade.
Public/tester88/catalog/invitation artifacts are unchanged; no mass distribution.
Fresh92 READY preserves ID/key bindings/Support ID; final DNS/HTTPS control through
the restored b9/1011 NL gateway passes. Extended trace OFF on both sides. No claim
of faster MESH or overnight stability from this short check.

**20.10 preceding observation / Предыдущее наблюдение:** code91 installed over90 at
19.10 23:02:52UTC, same signer/package/UID, data preserved. This is receive-path
instrumentation, **not a speed fix**. Ordinary UI/recovery remain; no new enrollment.
Private file: `state-client-build/mesh-receive-path-20261020/delivery/FamilyConnect-0.1.18-beta91-receive-trace.apk`.
SHA256 `6f4724ce31ec3ed99a209e8fb673bb6c0d15b0433df60850292aec8bd65cf490`.
Signer unchanged: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
RU: Не ставить90 поверх91, не удалять данные. Удаление наблюдений — обычным code>91.
EN: No downgrade/data clearing; remove observations only with a later same-signer build.
Tester88/public/catalog/invitation versions unchanged; no mass delivery.
[Exact artifact and measurement status](../releases/2026-10-20-mesh-receive-path.md).

**19.10 preceding owner stability update / Предыдущее обновление владельца:**
`0.1.18-beta90-stability` / code90 is signed and installed over89 at17:06:57UTC.
Same package `com.familyconnect.app.friends`, signer and UID; no uninstall, data
clear or registration. All12 native libraries and recovery Java equal sealed88.
Extended89 performance trace is absent. The functional stability delta is a
separate narrowly bounded gateway seed1011 repair;90 is not evidence that trace
caused the failures or that all repeated disconnects are cured.
Fresh90 READY confirms the same identity/key bindings/Support ID; Android-TUN
DNS/full HTTPS and current gateway-PID attribution pass18:07UTC. Five-minute
passive PID/TUN continuity is observed; no natural seed1011 during that window.

- Private file: `state-client-build/tunnel-restart-20261019/delivery/FamilyConnect-0.1.18-beta90-stability.apk`.
- APK SHA256: `68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a`.
- Same signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Restricted native SHA256: `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
- Android12+/arm64,16KiB alignment verified;169 JVM checks pass. Public/catalog/
  invitation versions and existing tester beta88 delivery remain unchanged.

RU: Владелец обновлён89→90 поверх приложения с сохранением данных. Новая
регистрация, приглашение, копирование ключей и персональная сборка не нужны.
**Не ставьте88/89 поверх90, не удаляйте приложение и не очищайте данные.** Если
потребуется следующая сборка, её code должен быть>=91 с прежней подписью/package.
Короткая успешная проверка не равна доказательству устранения всех перезапусков.

EN: The owner is upgraded89→90 in place, preserving application data. No new
registration, invitation or copied keys. **Do not downgrade to88/89 or uninstall/
clear data.** Any subsequent build needs the same signer/package and code>=91.
A short successful connection does not establish repeated-loss/overnight stability.
[Exact report and acceptance limits](../releases/2026-10-19-tunnel-restart-fix.md).

### Historical beta89 measurement update

**19.10 owner measurement update / Обновление для измерений:** owner phone then
retained `0.1.18-beta89-mesh-trace` / code89, installed over88 at14:40:47UTC with the
same package, signer, UID and verified existing identity/key bindings/Support ID.
This is **observation-only, not an accelerated or generally distributed APK**.
The tested server speed candidate was rejected; original NL gateway restored and
final MESH DNS/HTTPS passed. Existing beta88 recovery delivery below is unchanged
and is not held for this investigation. Public/download/invitation catalogs unchanged.

- Private89 file: `state-client-build/mesh-throughput-trace-20261019/delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk`.
- Code89 SHA256: `b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856`.
- Same signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Restricted native SHA256: `3ca3119ac12c9a3a61b5ebb1ee0244650db39dc36743e355d35bf523b53ef992`.
- Android12+/arm64; only restricted native changes; beta88 recovery sources
  unchanged,169 local checks PASS. No new registration, invite or personal APK.

RU: На телефоне владельца уже89. **Не устанавливайте88 поверх89 и не удаляйте
приложение ради отката.** Для выключения наблюдаемости подходит обычное обновление
с прежней подписью/package и code>=90, сохраняющее данные и recovery.89 не является
обещанием ускорения; повторно активировать ID или копировать ключи не нужно.

EN: The owner already has89. **Do not downgrade to88 or clear application data.**
Remove observation only through an ordinary same-signer/package code>=90 update
preserving recovery and data.89 does not promise higher speed and requires no
reactivation or copied keys. [Exact measurements/limitations](../releases/2026-10-19-mesh-throughput-trace.md).

**19.10 product-fix update:** signed recovery candidate
`0.1.18-beta88-recovery` / code88 is available at
`state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk`.
SHA256 `968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`.
Same package/signer, Android12+ arm64, all12 native libraries unchanged.135+34
local JVM checks pass. Fixes the reproduced signal-close recovery classification
and bounded repeat recovery; no speed increase or production IPv6 is claimed.
Owner phone updated87→88 at11:55:55UTC after ordinary Disconnect; exact installed
APK/code88, same UID and restricted-native hash verified. No uninstall/data clear.
Same-identity/key-binding/Support ID proof/import READY and production DNS/HTTPS
PASS. Fresh88 export confirms one automatic reconnect in29.083seconds around
normal gateway rotation, followed by successful traffic. Repeated/overnight
recovery is not yet accepted. Comparison does not show a speed improvement.
No APK was automatically distributed or placed in the public catalog. The file
is available as a limited private recovery update, not fully field/overnight-accepted.
[Current report and limitations](../releases/2026-10-19-beta87-product-fix.md).

**Russian handoff:** это файл обновления, не отдельное приложение. Установите
поверх текущего Family Connect, выбрав «Обновить», затем подключитесь. Не удаляйте
приложение и не очищайте данные; приглашение, новый ID и повторная активация не нужны.
Подпись, установка поверх87 и сохранение identity/ключевых привязок подтверждены
новым proof/READY, не только signer и UID. Один автоматический reconnect проверен;
ускорение, многократное ночное восстановление и IPv6 пока не подтверждены.

### Historical beta87 checkpoint

**DELIVERY_READY=NO. Beta87 is signed and installed over86; same-identity READY and
initial production Android-TUN DNS/HTTPS pass. Automatic87 recovery is not yet
observed. Export86 proves restoration after rotation, then another carrier loss
and terminal authenticated HELLO_RECEIVE/CLOSED_PIPE. Beta87 fixes only that
bounded-recovery classification, not the underlying carrier loss.**
Do not distribute rejected85 or unaccepted86/87. No public release/updater changed.
See the [dated report](../releases/2026-10-19-existing-users-private-beta-1.md) for
installed server packages, tests, failed beta85 evidence and current acceptance.

## Existing beta88 delivery APK / APK beta88 для прежней частной поставки

- File: `state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk`
- Version: `0.1.18-beta88-recovery`, versionCode88.
- Package: `com.familyconnect.app.friends` (same application, not a parallel install).
- SHA256: `968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` (matches UI84).
- Android12/API31 or newer; arm64-v8a. Other Android/ABI combinations are unverified.
- Physical package upgrade observed: UI84→beta85→beta86→beta87→beta88, no uninstall/data clear.
  Code60/65 and additional remote phones are not claimed as physically tested.
- Post-upgrade identity/key bindings and Support ID match the pre-upgrade record;
  authenticated beta88 import/READY and production Android-TUN DNS/HTTPS pass,
  including after ordinary rotation with freshCRL27130. One88 automatic recovery
  is explicitly correlated in the supplied export; no repeated/overnight claim.
- All12 native libraries match the accepted UI84 APK; transport settings are unchanged.
- Beta88 local JVM suite:135 PASS/19 suites plus34 ownership/startup/floor tests.
  Local tests and the single physical recovery have distinct acceptance boundaries.

## Инструкция пользователю после приёмки

«Установите APK поверх текущего Family Connect, выбрав “Обновить”.
Откройте приложение и подключитесь. Регистрация и ваш ID сохраняются».

Не удаляйте старое приложение и не очищайте его данные. Новый QR-код, приглашение,
активация или ручное продление FIELD-доступа не нужны. Если Android действительно
запросит разрешение на установку или VPN, подтвердите его сами. Это системное
разрешение Android, а не повторная регистрация Family Connect.

Владелец передаёт файл самостоятельно после приёмки; автоматической рассылки нет.

## User instructions after acceptance

Install the APK over your current Family Connect and choose **Update**. Open the
application and connect. Your registration and ID remain in place. Do not uninstall
or clear application data. No new invite, QR code, activation or individual FIELD
extension is required. Confirm Android installation/VPN permissions yourself if
the operating system actually requests them; these are not new registrations.

## Access and maintenance / Доступ и обслуживание

Existing activated, non-revoked identities use their existing proof-of-key workflow;
Support ID is not authorization. Explicit revocations and security floors remain.
Short-lived credentials refresh automatically under the existing approved schedule.
The finite90-day shared authority has planned operator maintenance by
17 December2026 22:36:48UTC; this is not an individual user renewal or daily activation.
See [lifecycle and limitations](../../deploy/friends/restricted/EXISTING_USERS_LIFECYCLE.md).

Restricted-network recovery requires either the verified API path or the existing
pinned control path to be reachable. No claim of universal operator availability,
zero network interruption, months of physical uptime or remote-phone acceptance
is made. Preserve existing identities and security state when reporting a failure.
