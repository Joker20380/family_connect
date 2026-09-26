# Linux: живая проверка одного сеанса авторизации — 2026-09-20

Источник helpers7a8036a; установленный paired bundle5a9ca444046993a7; logo source7835b4f.
Один запуск существующего Friends owner с постоянной identity, NL/TCP, catalog sequence3.
Внешняя control_transaction с тем же owner удерживала общий lock на весь сценарий,
включая disconnect: GUI не мог параллельно изменять соединение. Перед началом подтверждены
IDLE journal, отсутствие pending lease и активного VPN. Никаких новых invite/device.

Итог12.18s: connected=true, healthy=true, cleanup=true, journal_idle=true,
authorization_processes=1, authorization_exited=true, vpn_interfaces=[], passed=true.
Счётчик оборачивает Popen только для pkexec; измерен ровно один запуск/успешный выход.
Видимое число polkit dialogs пользователем отдельно не подтверждено. Отдельные действия
Connect и Disconnect в обычном UI имеют отдельные ограниченные сеансы авторизации.
После отключения IPv4/IPv6 all-table routes, rules и resolvectl DNS совпали с baseline
(исключены volatile cache/expiry fields). Приватный результат хранится в ignored
state-client-build/desktop-live-20260920/authorization-live-result.json.

После вопроса пользователя о зависании проверен завершившийся процесс: exit0;
проверка не перезапускалась, VPN интерфейсов нет. Следующий шаг: Windows live.
Это текущая сеть пользователя, не проверка доступности у российского провайдера.

Установка/поставка не менялась: GUI paired preview5a9ca444046993a7 через desktop entry,
legacy current0.2.8, public desktopv0.2.9, Androidbeta19. Rollback прежний: закрыть paired
GUI, штатно recover/disconnect при необходимости, вернуть desktop entries из
~/.local/share/family-connect/backups/linux-launcher-20260920 и при необходимости
root helpers из /var/backups/family-connect/linux-auth-20260920. Identity/journal и
private profiles не удалять. Новых серверных изменений/публикации/подписи нет.

CI перед тестом: source7835b4f Linux preview35495850974, Client35495850992,
TCP35495851005 ещё in_progress; принятые helper source7a8036a AWG/TCP и desktop platform
jobs success. Повторный CI этим сетевым тестом не запускался.
