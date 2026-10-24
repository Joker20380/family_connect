# Desktop diagnostics106 — private development, not released

## Scope / Область проверки

Linux GTK source now includes the accepted106 native JSON projection and an explicit
online-diagnostics switch. `clients/shared/android106-diagnostics.json` pins41 native
projection vectors; `clients/shared/android106-support.json` pins54 online-snapshot
vectors and the accepted source hashes. The comparison compiles only unchanged
pure-Java projectors from the verified capsule; it neither rebuilds nor installs APKs.
The online adaptation changes platform to `linux`, not the computer's identity.
P2 is recognized only in historical diagnostic data; it is not enabled as a transport.

Local GTK tests exercise actual windows/file saving but use synthetic VPN state and
an isolated upload sender. Separate HTTP tests execute the real existing Access and
diagnostics handlers through a local in-memory transport, including proof/digest,
revocation, rate limiting and private storage. They do not contact production.
Installed Linux/Windows acceptance, a complete updater package and Windows UI are
still pending. An internal root-component archive does not contain this full GUI.

## Linux user instructions — English

In Settings → About / Diagnostics, **Send diagnostics** first explains what is
included, then opens the system save dialog. Save the JSON and send it to a recipient
you choose. This action does not upload anything. The bounded file includes full
projected native receipt/flow/Mux/startup/lifecycle data, Support ID, versions and
loss counters, not raw logs, messages, browsing destinations or credentials.
The file is written atomically with mode0600. Export failure does not stop the VPN.

**Online diagnostics (7 days)** is OFF by default, including existing installations.
Turning it on requires a separate confirmation. It sends only a small allowlisted
technical snapshot (at most4096 UTF-8 bytes), not the local JSON export. The existing
server associates this computer's authenticated proof with its own Support ID and
retains only the latest snapshot for up to7 days. No remote-control ability or VPN
permission is granted. No bootstrap/route bypass is created for support uploads.

The consent expires after7 days. Turn the switch off to stop further requests and
cancel the current attempt; a request already received by the server cannot be
recalled. Cancellation is checked before/after the challenge and during response
reads, with a shared15-second request deadline. A stalled OS resolver/transport is
not force-killed; at most one daemon upload thread exists and no overlapping retry
is launched. Turning the switch off does not delete an already retained server
snapshot. Normal server retention still applies.

Cadence is60 seconds after successful completion,300 after failure, using monotonic
time. There is at most one in-flight snapshot. Authentication failure never enables
a weaker fallback. State shows waiting/sending/stored/rate-limited/rejected/timeout/
unavailable; raw exceptions are not displayed. If saving withdrawal fails, uploads
stop in the service and the UI explicitly asks you to check consent after restart.
If the service reply is lost, the switch shows unavailable until state is read back;
the UI does not claim that an unconfirmed withdrawal stopped remote work.

The existing non-root session service now owns consent and the single uploader.
Closing GTK only detaches its status/control connection: valid consent keeps
collection running, independently of chat background preferences or a locked chat
keyring. The service reads VPN status itself, without starting VPN or accepting a
GUI-supplied report. A service restart reloads this computer's valid consent.
Logout ends this user-session service; cold login/autostart and exact installed
Type=dbus/AppImage/upgrade behavior still require package acceptance. No boot-wide
root uploader is installed. Windows support remains incomplete.

## Инструкция Linux — русский

Откройте «ОПЦИИ» → «О приложении / Диагностика». «Отправить диагностику» сначала
показывает состав данных, затем предлагает сохранить JSON. Передайте файл выбранному
получателю самостоятельно. Эта кнопка ничего не загружает в сеть. Полный ограниченный
экспорт содержит проверенные поля native/сессии, Support ID, версии и счётчики потерь,
но не переписку, сайты, адреса назначения, ключи или необработанные журналы.

«Онлайн-диагностика (7 дней)» по умолчанию выключена, в том числе после обычного
обновления. Включение требует отдельного подтверждения. Отправляется только снимок
разрешённых технических полей размером до4096 байт, а не полный JSON-файл. Привязка —
к identity и Support ID этого компьютера. Сервер хранит последний снимок до7 дней.
Удалённое управление, дополнительные права VPN и обход VPN не включаются.

Выключение останавливает последующие отправки и отменяет текущую попытку; уже
полученный сервером снимок отозвать нельзя, он удаляется по обычному сроку хранения.
Успешные отправки разделены минимум60 секундами после завершения, неудачные —300.
При ошибке сохранения отзыва согласия отправка в службе прекращается,
а интерфейс просит проверить настройку после перезапуска. Ключи и identity не меняются.

Согласием и единственным uploader теперь владеет существующая пользовательская
служба, не root-процесс и не GTK. Закрытие окна не прекращает добровольную отправку
до отзыва/истечения согласия. Блокировка хранилища чатов и выключенная фоновая доставка
сообщений не мешают отзыву согласия. Служба самостоятельно читает состояние VPN,
не включает его и не принимает снимки от GUI. Перезапуск сохраняет действующее
согласие этого компьютера. При потере ответа состояние перечитывается: неподтверждённый
отзыв не показывается как успешный. Выход из пользовательской сессии завершает службу;
холодный вход/автозапуск, установленный Type=dbus, AppImage, обновление и Windows
остаются отдельными незавершёнными проверками.

## Storage, replay and packaging

`support-consent.json` is atomic0600 metadata in the existing0700 Friends identity
directory: schema, registration reference, expiry. It contains no key or report.
Missing/corrupt/duplicate/oversized/unsafe/link metadata means OFF. A different
registration never inherits consent. Support does not create or replace identity.
Withdrawal removes only this consent file; messaging/history/configuration remain.

Run `scripts/check_support106_reference.py --jdk <verified-jdk> --gson <accepted-gson>
--output <fresh-evidence-directory>` under the existing thermal limiter. Python
golden tests need no JDK. The fresh GTK fixture uses the extracted Xvfb tools on PATH,
private session D-Bus, explicit X11 backend, isolated XDG metadata directories and
disables portals only inside the test, so its native GTK
save chooser can be controlled without a host desktop portal. Installed application
portal behavior is unchanged and remains a separate installed-OS acceptance gate.
125/150% fixture checks use font DPI; they are not compositor fractional-scale tests.

Support IPC permits only status and consent boolean plus a service-issued revision;
no snapshots, paths, URLs, commands or private keys. Same-UID authorization and
one dedicated control worker keep withdrawal independent of the chat command queue.
Old/replayed revisions fail, including across restart. An ambiguous mutation is
never automatically retried. A fresh status read resolves the displayed state.

The full Linux bundler includes the support service/client modules and VERSION;
the six-file legacy archive shape remains unchanged. This is not a signed/public release. No update
catalog, server policy, Android artifact, existing installation or key is changed.
