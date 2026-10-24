# Linux Auto — private candidate / закрытый кандидат

24.10.2026. Source functionality, not a published update. Linux remains0.2.11,
Windows0.2.15. No complete parity AppImage/DEB/Windows installer is ready. The
internal Linux system-component archive is not the whole application; do not
replace public downloads or activate an unverified installation with it.

## Русский

- GUI запускается обычным пользователем. Установка системного компонента и запуск
  его службы используют штатный polkit/helper; не запускайте весь интерфейс root.
- Auto появляется только при наличии проверенного Auto-компонента и продуктового
  модуля identity. Страна остаётся предпочтением для обычных транспортов. Общий
  orchestrator проверяет доступные возможности и выбирает AWG/TCP либо MESH;
  отказ авторизации не разрешает слабый fallback.
- В интерфейсе различаются выбор `Auto` и фактический `Auto → AWG 3.1`,
  `Auto → TCP REALITY` или `Auto → MESH`. MESH-шлюз не выдаётся за выбранную страну.
  Профиль P0/P1 выбирается в настройках для новой MESH-сессии, не выдаёт новых прав.
  Реальное согласование RS/CREDIT выводится только из активной MESH-сессии;
  AWG/TCP не объявляются P1.
- «Отключить» действует при подключении, восстановлении и ошибке. Неизвестный
  ответ запуска сначала сверяется со службой, не повторяется автоматически.
  Старый запрос остановки не может завершить новую generation.
- При закрытии окна выводится предупреждение: служба продолжает работу.
  Повторный запуск читает состояние службы. Для остановки используйте «Отключить».
- Проверка IP привязана к фактическому TUN и попытке подключения, а не к обычному
  соединению компьютера. Проверка во время смены сессии отклоняется.
- Обычное обновление не требует новой identity. Подписанный общий catalog floor
  сохраняется отдельно от ключей и проверяется перед следующим ручным AWG/TCP.
  При повреждении этого состояния не удаляйте его для обхода проверки: сохраните
  диагностику и обратитесь в поддержку. Автоматическая отправка не включается.

Примечание AWG: после аварии процесса исчезновение TUN ещё не
означает завершённое отключение. «Отключить» должно завершить очистку через helper;
переход на другой транспорт и установка обновления запрещены при незавершённой
очистке. Не удаляйте journal и не выполняйте общий сброс firewall/routes. Если
проверка владельца ресурса отклонена, сохраните диагностику для поддержки.

## English

After an AWG process crash, a missing TUN does not mean teardown has finished.
Disconnect must reconcile the helper's owned resources before switching transports
or updating. Do not remove the ownership journal or globally flush routes/firewall
rules. Retain diagnostics for support if resource ownership cannot be verified.

- Run the GUI as an ordinary user. System-component setup and service startup use
  the existing polkit/helper; do not run the entire interface as root.
- Auto requires the verified Auto component and product identity module. Country
  is a normal-transport preference. The shared orchestrator checks actual
  capabilities and selects AWG/TCP or MESH; authorization rejection does not
  permit a weaker fallback.
- Selected `Auto` differs from actual `Auto → AWG 3.1`, `Auto → TCP REALITY` or
  `Auto → MESH`. A directory-selected MESH gateway is not the preferred country.
  P0/P1 is a next-MESH-session setting, not an access grant. Actual RS/CREDIT
  negotiation is shown only for active MESH, never claimed for AWG/TCP.
- Disconnect works during startup, recovery and failure. An uncertain start is
  reconciled with service status, never blindly retried. Generation checks prevent
  an old stop request from terminating a newer session.
- Closing the window warns that the system service continues. Reopening reads
  its state; choose Disconnect to stop it.
- IP checking binds to the actual TUN/attempt and rejects a concurrent reconnect,
  rather than testing the computer's ordinary Internet connection.
- An ordinary upgrade does not create a new identity. The signed shared catalog
  floor is kept separately from keys and checked before the next manual AWG/TCP
  configuration. Do not delete damaged state to bypass validation; save diagnostics
  and contact support. Automatic diagnostic uploads are not enabled.

## Acceptance boundary

Local GTK/IPC/floor tests are not proof of an installed MESH VPN. Still required:
root socket authorization on the target OS; normal/MESH TUN handoffs; DNS/IPv6
containment; actual gateway/P1 agreement and bounded transfers; network/sleep/crash
recovery; Disconnect cleanup; previous-version installation upgrade. Windows
broker/WinForms integration and physical Windows acceptance remain unfinished.
See [phase16 evidence](../releases/2026-10-23-desktop-parity106.md) and the
[implementation contract](DESKTOP_AUTO_NORMAL.md).
