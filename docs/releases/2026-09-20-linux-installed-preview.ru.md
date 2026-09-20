# Установка Linux Friends preview и нового логотипа — 2026-09-20

Auth source7a8036a принят CI: AWG35495112337, TCP35495112351 success;
Windows/Linux jobs35495112338 success. Android setup и phase0 failure сохранены.

Установлены backend/helper/profile_config и authorization-session-v1 для AWG/TCP;
выполнен один root installer через pkexec. Перед заменой взяты оба helper locks,
проверено отсутствие VPN интерфейсов и TCP services. Private profiles и pinned
движки не менялись. Полная копия каталогов: /var/backups/family-connect/linux-auth-20260920.
Installed backend SHA256:5fddfc6b3f64d404210ffdd7caecc6e5994693665480c207f52c177995c846b5.

Логотип Linux раньше оставался многогранником и в ICON_PNG, и в ~/.local/share/family-connect/app.png.
Теперь PNG воспроизводится из экспортированной Android vector door geometry,
clients/assets/linux-door.xml, через scripts/generate_linux_icon.py (Pillow).
ICON_PNG встроен в прежний app.py; standalone archive остаётся из шести файлов.
Installer/runtime используют filename с hash, а GTK hicolor icon установлен под
com.familyconnect.Client. SHA256 PNG:27734a28522bbb989d5282e04404ee22a67436d776276363f0af6803aa96e684.
Android/Windows binaries и логотипы не изменялись.

Установленный paired bundle5a9ca444046993a72d016af64a55f054617fae47cf9d0e3b6183292cd29a38c6:
~/.local/share/family-connect/control-previews/5a9ca444046993a7/FamilyConnect-Control-preview.
Рядом постоянный venv системного Python с --system-site-packages и provisioning lock.
Manifest verify и imports GTK/Friends dependencies passed.
Archive SHA256:9b2ec1f8181a4adb8c075f27926313460fa0e95e40b8252329f9c5b8908914cd.
Это локальный preview на7a8036a плюс logo change, не подписанное публичное обновление.

Desktop entry family-connect.desktop запускает этот paired runner через его venv.
com.familyconnect.Client.desktop — скрытый alias; прежний AWG pilot скрыт и переведён
на тот же paired runner. Кэш icons/applications обновлён. Backup desktop entries и
предыдущего theme icon: ~/.local/share/family-connect/backups/linux-launcher-20260920.
Legacy current/previous symlinks не менялись: current0.2.8-766194f6f3df-9c6f2e52a84f.
Не использовать legacy current для Friends: теперь рабочая точка входа — desktop entry.

Проверки:28 targeted authorization/update tests; GTK Friends activation/referral,
configuration/TCP, parent startup recovery/modal ownership; PNG логотипа просмотрен.
Запуск GUI через transient user unit family-connect-preview-20260920: active/running,
ExecMainStatus0. Первые запуски через tool child process не сохранились после завершения
команды, traceback не было; запуск передан пользовательскому systemd.
Реальных VPN apply в этой сессии не было; fcawg/fctcp отсутствуют. Открыто: ручная
проверка одного auth-сеанса на установленном preview, затем Windows live, РФ сеть.

Rollback: закрыть GUI (или systemctl --user stop family-connect-preview-20260920),
штатно отключить/recover VPN если он включён. Вернуть desktop entries/theme icon из
backup и обновить icon cache. Только при необходимости вернуть полные root helper
каталоги из linux-auth-20260920 при отсутствии активных туннелей. Сохранять identity,
journal и private profiles. Не возвращать старый journal для обхода sequence.
Никакого нового release/tag, offline signing или server deployment не выполнялось.
