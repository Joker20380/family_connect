# Linux: AppImage и DEB вместо tar.gz preview

Статус: design + implementation plan. Runtime-артефакты ещё не собраны и не опубликованы;
этот документ не объявляет rollout завершённым.

## 1. Как работает текущий Linux-поток

Пригласительная страница `deploy/friends/invite/index.html` ведёт Linux-пользователя на
`FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz` (121 KB, source-only bundle
из `scripts/package_control.py`). Дальше оператор по `FamilyConnect-Linux-0.2.11-invitation.txt`
выполняет: распаковка → `python3 -m venv --system-site-packages` → `pip install -r
provisioning/requirements.lock` → `scripts/run_control_preview.py gui`. Отдельно ставятся
root VPN helpers (`install-awg.sh`, `install-tcp.sh`). Обычный пользователь получает архив
Python-файлов, а не устанавливаемое приложение.

## 2. Почему сейчас требуется venv/оператор

`app.py` — GTK 4/libadwaita приложение. Friends-активация подключается через
`provisioning.friends_owner.FriendsOwner` (опциональный `try/except ImportError`), который
тянет `rns`, `pydantic`, `httpx`, `cryptography` из `provisioning/requirements.lock`.
Эти пакеты не являются системными Debian-пакетами (`rns` в дистрибутиве отсутствует),
поэтому их нельзя объявить обычными `Depends:` — их нужно vendoring внутрь пакета.
GTK/GI, наоборот, обязаны остаться системными: `gi` не устанавливается через pip, а
bundled GTK без согласованного с Python runtime `gi`/libgirepository нестабилен.

## 3. Целевые артефакты

- `FamilyConnect-<version>-x86_64.AppImage` — основной Linux download.
- `FamilyConnect_<version>_amd64.deb` — Ubuntu/Debian/Mint.
- `FamilyConnect-Linux-<version>.tar.gz` — сохраняется как advanced/manual и ради
  существующего signed update catalog (`updates.py` ожидает именно это имя).

Immutable names; уже опубликованную версию не перезаписывать.

## 4. Разделение зависимостей

Bundled (application dependencies, vendor-каталог внутри пакета):

- `rns`, `pyserial`, `cryptography`, `cffi`, `pycparser`;
- `pydantic`, `pydantic_core`, `annotated-types`, `typing-inspection`, `typing_extensions`;
- `httpx`, `httpcore`, `h11`, `anyio`, `idna`, `certifi`.

Ровно версии из `provisioning/requirements.lock`.

Host/system dependencies (документируются, не bundle):

- `python3`, `python3-gi`, `python3-gi-cairo`;
- `gir1.2-gtk-4.0`, `gir1.2-adw-1`;
- `network-manager` (`nmcli`);
- `libqrencode4`, `libzbar0` (QR в Friends UI).

## 5. Привилегированные VPN helpers

Текущая модель уже безопасна: клиент вызывает `pkexec <helper> session` (одна авторизация
на сессию через ограниченный stdin-liveness lease), а не тихий `sudo python` при каждом
подключении. Helpers:

- `/usr/local/lib/family-connect-awg/helper` (`clients/linux/awg-helper.py`);
- `/usr/local/lib/family-connect-tcp/helper` (`clients/linux/tcp-helper.py`).

Сами бинарники AWG (`awg`, `amneziawg-go`, `awg-quick`) и TCP (`xray`) приходят из
отдельных pinned-сборок и **не** включаются в AppImage/DEB. Установка helper остаётся
явным one-time setup через `clients/linux/install-awg.sh` / `install-tcp.sh`. DEB не
устанавливает root helper молча; GUI при отсутствии helper показывает понятную ошибку
(`Update the Linux VPN helper to support single authorization`).

## 6. Persistent state

Состояние хранится в `$HOME` и не зависит от способа установки:

- `~/.local/share/family-connect/friends-identity`, `releases/`, `current`;
- `~/.config/family-connect/ui-language`, `~/.config/family-connect/route.json`.

AppImage/DEB не пишут в эти пути при установке. `postinst`/`prerm` не трогают
пользовательские данные; upgrade/remove/reinstall сохраняют Device Identity, Friends
state, provisioning и не расходуют новое invitation.

## 7. Layout пакета

Общий launcher `launcher.py` (устанавливает `sys.path` в порядке `vendor`, root пакета,
`clients/desktop` и запускает `app.py` через `runpy`). DEB ставит `/usr/bin/family-connect`
→ `/usr/lib/family-connect/launcher.py`; AppImage использует `AppRun` → тот же launcher.

```
/usr/lib/family-connect/
  clients/desktop/{app.py,backend.py,profile_config.py,updates.py,update.pub,friends_qr.py,friends_ui.py}
  device_identity/{__init__.py,device.py,friends.py}
  provisioning/{*.py,requirements.lock}
  vendor/           # pinned pip deps
  launcher.py
```

Desktop integration: `/usr/share/applications/com.familyconnect.Client.desktop`,
icon `/usr/share/icons/hicolor/256x256/apps/com.familyconnect.Client.png`,
`MimeType=x-scheme-handler/familyconnect`, `StartupWMClass=com.familyconnect.Client`.

## 8. Update strategy

`updates.py` подписанный каталог продолжает ожидать legacy `FamilyConnect-Linux-<ver>.tar.gz`;
мы его не удаляем. `.deb` обновляется новым `.deb`, AppImage — новым AppImage.
Автоматический self-update AppImage не вводится: сначала сохраняется hash/signature
проверка и downgrade protection. Полный AppImage/DEB updater — отдельная задача.

## 9. Acceptance (план, ещё не выполнен)

Чистая Ubuntu:

- AppImage: скачать → `chmod +x`/разрешить выполнение → запуск GUI; без `pip`, без venv,
  без source checkout; корректный icon; state writable; restart; invitation URI где поддержано.
- DEB: `dpkg -i`/`apt install` → пункт меню → запуск; update/reinstall/uninstall; state
  сохранён; URI handler `x-scheme-handler/familyconnect`.

CI: artifact exists + executable + arch + AppImage `--appimage-extract` + `dpkg-deb --info`
+ package-content audit (нет identity/token/WG private/.env/DB) + xvfb/dbus smoke.

## 10. Known limitations

- AppImage bundling `gi`/GTK4/libadwaita надёжно не решается; они остаются системными.
- Root AWG/TCP helper и их бинарники не входят в пользовательский пакет.
- Полный AppImage/DEB self-update не реализован в этой задаче.
- Пригласительная landing переключается на AppImage только после публикации реальных
  артефактов и чистой-Ubuntu приёмки.
