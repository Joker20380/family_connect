# Owner recovery106 — private candidate / закрытый кандидат

**31 October —107 candidate, not distributed / кандидат107, не опубликован.**
RU: владелец разрешил общий MESH-выпуск. Кандидат107 сохраняет принятую106 и12 native-библиотек;
исправляет повторные оповещения и обработку отказа микрофона.219 JVM-тестов и lint PASS.
APK не подписан/не установлен; требуются CI, совместимость (Android12+/ARM64) и проверка
обновления на телефоне без потери данных. Общий updater/приглашение остаются60, owner —106.
EN:107 is an unsigned local candidate, not a public download or installed acceptance.
Public updater/invitation stay60. CI, compatibility, signing and device gates remain required.
Do not uninstall, clear data or reenroll. Canary paused.
[Same-operation evidence](../releases/2026-10-30-nl-gateway-replacement.md).


**SIGNED_APK_READY=YES; PRIVATE_FIELD_READY=YES** for the confirmed three existing
devices only. No public release or automatic sending.23 October: actual105 readback
preserved first, Wi-Fi/VPN off, active consent but full JSON unavailable. Finished
the existing106 aggregate diagnostic-budget fix:219 JVM checks and recorded replay
PASS, all12 native libraries unchanged. Signed once through the existing vault;
105→106 installed04:38:17UTC, same UID10283/APK/signer/native. Fresh normal JSON
now works and confirms FC-4D8Q-REEG; ordinary Connect retains Android P1/RS32/
CREDIT128 on Wi-Fi. Full-body/recovery gates are separate, not inferred from READY.
Fresh Wi-Fi control19/19 complete (single1.189/parallel2.276Mbit/s); ordinary
Disconnect/Connect and a full1KiB response pass. Automatic Wi-Fi return now passes:
new both-end P1 session and full1KiB HTTPS without Connect;106.578s from Wi-Fi
creation to CONNECTED, not instant recovery. P1 policy is now deployed for exactly
FC-4D8Q-REEG, FC-ZMVK-MM7C and FC-YHQB-9VJN. Post-deploy owner106/both-end P1 and
full1KiB HTTPS PASS3.422s. Export21 corroborates reported Volgograd whitelist success
on **beta96**, not106/P1; Krasnodar and106/P1 field validation remain NOT_RUN.
[Latest acceptance, exact group and rollback](../releases/2026-10-23-tester-p1-cohort.md).

## Artifact / Файл

- Path: `state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk`
- Version: `0.1.18-beta106-recovery`, versionCode **106**.
- SHA256: `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Package: `com.familyconnect.app.friends`; Android12+/API31; arm64-v8a;16KiB aligned.
- Restricted native SHA256: `37ba4fac656811dd979688a274f45aed85a3aa567f1fafb3987a81c020fa91f1`.
- Includes102 DNS-progress health,103 deadline/cancel,104 bounded750ms reorder,
  105 queue-pressure drain,106 bounded diagnostic export with explicit detail-omission
  accounting. No increased windows/retries, Q1, FEC/QUIC or security bypass.

Static package/signer/increasing-code checks pass for retained beta88,94 and104.
Physical104→105 and105→106 receipts exist; static88/94/104/105→106 metadata checks
also pass. Exact signed65/96→106 metadata now checked too.106 needs API31+;
recorded Krasnodar API31 and Volgograd API34 meet this floor, but the server's65
version observation is old05 October. Supplied22 October ring establishes Volgograd96.
Actual tester installations and physical65/88/94/96/104→106 remain unverified;
do not generalize to all versions or overwrite a newer installed code.
Owner106 does not need another installation for a receipt.
No public URL/catalog/invitation change; the existing private local file is retained.
[Evidence](../releases/2026-10-22-owner-disconnections.md) ·
[Delivery receipt](../releases/2026-10-22-private-field-delivery-receipt.json).

## RU — preflight и ограниченная проверка

Источник уточнения — сообщение владельца22.10: мобильный пакет закончился,
оператор ограничил скорость; на Wi-Fi приложение работает нормально. Скорость
ограничения, начало и версия той ручной проверки неизвестны. Это не новая
инструментальная приёмка и не объяснение всех инцидентов тестировщиков.

Перед попыткой записать: версию/code, сеть, выбранный и фактический профиль,
оператора/время; состояние пакета и известное ограничение **со слов пользователя**,
либо UNKNOWN. Для Wi-Fi — известен ли источник интернета; hotspot на той же
ограниченной SIM не является независимым каналом. Приложение не знает остаток
тарифа автоматически; SMS/личный кабинет/новые разрешения не нужны.

**Инструкция тестировщику после разрешения владельцем передачи кандидата:**

1. Установить APK **поверх** согласованной поддерживаемой версии с тем же signer.
   Не удалять приложение/данные, не активировать заново. Сверить106 и прежний Support ID.
2. Записать preflight. Не требовать предварительного подключения через рабочий Wi-Fi:
   это может скрыть bootstrap-зависимость. Истёкшие материалы фиксировать отдельно,
   использовать штатный refresh, не обходить проверки/floors.
3. Выключить Wi-Fi, выбрать именно **MESH**, выполнить одну попытку на мобильных
   данных. Перед Connect, пока VPN отключён: Настройки → **«MESH owner-тест · новая
   сессия» → «P1 · RS32/32 · CREDIT128»**. Это историческое название обычной кнопки106,
   она доступна тестировщику без USB. Серверная политика уже подтверждена для трёх
   указанных ID. Не выбирать P2/Q1. Auto/AWG/TCP не доказывают MESH; фактические
   лимиты сверяются по JSON, не по одному выбранному пункту.
4. Открыть новую страницу/проверить небольшую передачу, записать результат и время.
   CONNECTED недостаточно. На ограниченном тарифе не запускать bulk/speedtest.
5. При любом результате: Настройки → отправка диагностики → штатный JSON; передать
   файл владельцу вместе с preflight. Не очищать историю/incident/logcat.

USB-допуск «разрешить поддержку на1час» нужен только для адресной диагностики owner,
не для права пользоваться VPN, выбора профиля или обычного JSON-экспорта. Не отключать
MIUI-защиты. Экспорт15 сохранён как старый снимок19:43UTC. На106 свежий штатный
JSON уже получен23.10, USB-допуск действует; повторное нажатие кнопки отключает его.
Не запрашивать новый допуск без фактического отказа. Не очищать историю и не считать
старый CONNECTED текущим.
Owner-шаг23.10 выполнен: новая сессия MESH/P1 восстановилась без Connect, малый
HTTPS завершён полностью. От появления Wi-Fi до CONNECTED прошло106,578секунды;
мгновенное восстановление не обещается. Повторять отключение/нагрузку не нужно.
Состав закрытой P1-группы и серверная политика подтверждены23.10. После её
развёртывания owner прошёл ещё один малый контроль; дополнительных отключений
не нужно. Старые допуски к сервису не равны выбору P1-группы.
Контролируемое выключение Wi-Fi — после объяснения сценария и исключения mobile fallback;
возврат передачи без Connect — auto recovery, ручной Disconnect/Connect — другой тест.
Старые TCP-соединения и прикладные операции не обещано сохранять/повторять автоматически.
Доступность произвольного внешнего сайта не является условием запуска MESH.

## EN — preflight and bounded field attempt

On22 October the owner reported an exhausted mobile allowance and carrier
throttling, with normal operation on Wi-Fi. Rate, onset and version at that manual
check are unknown. This is user testimony, not a new measured PASS or an explanation
of all tester failures. Record version/code, network, selected/effective profile,
operator/time, user-reported allowance/throttling or UNKNOWN. Record the Wi-Fi
upstream if known; a hotspot using the same throttled SIM is not independent.
The app does not automatically know the remaining allowance; no SMS permission.

After the owner authorizes delivery: install over the agreed same-signer supported
version; never uninstall, clear data or reactivate. Verify106 and retained Support ID.
Do not require a successful Wi-Fi refresh before the first field attempt: preserve
bootstrap evidence. If credentials are expired, record it separately and use normal
secure refresh. Turn Wi-Fi off, choose **MESH**, make one mobile-data connection
attempt and request a new page/small body. Before Connect, while disconnected,
Settings → **“MESH owner test · next session” → “P1 · RS32/32 · CREDIT128”**.
The old label is an ordinary persistent control in106, not an owner/USB restriction.
Do not choose P2/Q1. Record operator/time/allowance and result.
Do not run bulk on known throttled mobile data. Export the normal Settings diagnostic
JSON **whether successful or not**, and send it to the owner; preserve history.

The persistent P1 selector needs no USB; gateway P1 policy is now verified for the
exact three IDs listed above. Service entitlement, transport profile and USB
consent are distinct. No new invitations/enrollment/daily activation. No arbitrary
external website is a mandatory startup gate in whitelist networks. Wi-Fi success
does not establish mobile-whitelist success. Separately, the supplied cellular96
Volgograd export corroborates the tester's reported whitelist success, with valid
cache after failed refresh. That is not106/P1, cold-bootstrap or Krasnodar proof. No automatic
sending/public release. Controlled recovery requires a pre-explained manual Wi-Fi
outage with no mobile fallback, followed by transfer without another Connect.

Latest owner follow-up23.10: the old supplied JSON remains a stale historical file.
106 fixes aggregate export budgeting without mutating retained memory or counters;
fresh normal JSON works, Support ID is preserved, and USB consent is active. Do not
toggle an active grant or treat it as a VPN entitlement. Current body/recovery and
tester-policy results are tracked separately in the latest report.
The explained owner outage/return completed23.10: automatic new MESH/P1 session
and full small HTTPS pass without Connect. Wi-Fi creation to CONNECTED took106.578s;
do not promise instant restoration or repeat the outage/load. The exact closed
group policy and post-deploy small-body acceptance are complete. Next is manual
delivery and one real106/P1 field attempt; no hidden waiting collector is running.
