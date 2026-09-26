# Linux: AppImage и DEB вместо tar.gz preview

Статус: реализовано, собрано и проверено (CI + чистая Ubuntu 24.04); публикация на
HTTPS release infrastructure и переключение invitation landing ещё не выполнены.

## Результаты приёмки (26.09)

Source commit: `70f594a0` (packaging `398a2e5`, `4c7549c`, `b1e96f0`, `0a56210`,
`2ff3821`, `4cae8a2`, `70f594a0`). CI run `36261639780` — linux job green, все шаги
(сборка AppImage/DEB/tar.gz, `dpkg-deb --info/--contents`, desktop MimeType, smoke
packaged launcher, `--appimage-extract`, sha256) success. Python/runtime baseline:
ubuntu-latest = Ubuntu 24.04, system `/usr/bin/python3` 3.12; compiled vendor wheels
собраны под cp312.

Артефакты (собраны в чистом `ubuntu:24.04`, те же что прошли acceptance):

| Artifact | Size | SHA256 |
| --- | --- | --- |
| `FamilyConnect-0.2.11-x86_64.AppImage` | 8 559 096 B | `7dfaca6022a275e62eeac5b8c402477d493d5833181d238f2080aa62014ba83b` |
| `FamilyConnect_0.2.11_amd64.deb` | 6 685 688 B | `a336624808b96de4455963307c609be1d3bddbbadf29976a9a0176207f415697` |
| `FamilyConnect-Linux-0.2.11.tar.gz` (legacy) | 83 911 B | `e5906431fb458dd463c46c58dd249b9882b101bc2d768ec375c5002b6445ea5d` |

### AppImage

- Portability (clean Ubuntu 24.04 **без** GTK/GI): запуск падает `ModuleNotFoundError:
  No module named 'gi'`. AppImage **не** self-contained по GTK-стеку. Launcher выдаёт
  понятное сообщение и exit 2 вместо traceback.
- Минимальные host prerequisites (те же, что DEB Depends): `python3-gi`,
  `python3-gi-cairo`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `librsvg2-common`
  (+ `libqrencode4`, `libzbar0` для QR; `network-manager` для VPN).
- С этими пакетами: smoke exit 0, restart exit 0, `--integrate` создаёт
  `~/.local/share/applications/com.familyconnect.Client.desktop` (`Exec="...AppImage" %u`),
  icon, `x-scheme-handler/familyconnect` → `com.familyconnect.Client.desktop`.
- Без git/pip/venv/source checkout/ручного PYTHONPATH.

### DEB

- `apt install ./FamilyConnect_0.2.11_amd64.deb` разрешает Depends (в т.ч.
  `librsvg2-common`) и ставит 0.2.11; `/usr/bin/family-connect`, desktop entry,
  icon, MimeType `x-scheme-handler/familyconnect` — ok.
- `/usr/bin/family-connect --smoke` exit 0, без SVG/GDK ошибок.
- `familyconnect://invite/<64hex>` аргументом доставляется приложению (GUI остаётся
  запущенным; только безобидные Gtk theme-parser warnings от CSS gradient).
- Upgrade (reinstall) сохраняет `~/.local/share/family-connect/*` (simulated
  friends-identity); `apt remove` удаляет `/usr/bin/family-connect` и
  `/usr/lib/family-connect`; пользовательские данные сохраняются; reinstall —
  state снова доступен. Launchers ставят `PYTHONDONTWRITEBYTECODE=1`, чтобы root-run
  не оставлял `.pyc` в `/usr/lib`.

### Package-content audit

DEB и AppImage (`squashfs-root`): в собственных файлах нет private keys, test
identities, invitation tokens, Friends state, real provisioning, `.env`, DB,
developer home paths, build credentials, signing keys. Vendor проверяется по
filenames (нет `.env`/state/pycache).

### VPN prerequisites (отдельно от GUI)

GUI/application installation — **PASS** (чистая Ubuntu 24.04). Friends activation и
VPN runtime (NetworkManager/WireGuard/polkit/helpers/TUN/routing) в контейнере не
проверялись: NetworkManager не запускается без systemd. Root AWG/TCP helpers и их
бинарники по-прежнему ставятся отдельно (`install-awg.sh`/`install-tcp.sh`) и не
входят в пользовательский пакет.

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
- `libqrencode4`, `libzbar0` (QR в Friends UI);
- `librsvg2-common` (SVG loader gdk-pixbuf — без него не рендерится встроенный
  terminal-виджет; приложение запускается, но виджет пуст).

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

- AppImage НЕ self-contained по GTK-стеку: требует host `python3-gi`,
  `python3-gi-cairo`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `librsvg2-common`.
  Термин «self-contained» для AppImage не используется без оговорки про host deps.
- AppImage bundling `gi`/GTK4/libadwaita надёжно не решается; они остаются системными.
- Root AWG/TCP helper и их бинарники не входят в пользовательский пакет.
- Полный AppImage/DEB self-update не реализован в этой задаче.
- Пригласительная landing переключается на AppImage только после публикации реальных
  артефактов и чистой-Ubuntu приёмки.
