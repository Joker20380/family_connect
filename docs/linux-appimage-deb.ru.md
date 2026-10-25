# Linux: AppImage и DEB вместо tar.gz preview

## L03.2 — внутренний полный candidate,25.10

**Ubuntu26.04/CPython3.14 — отдельный U2604-COMPAT checkpoint, не host upgrade.**
[Отчёт](releases/2026-10-26-linux-ubuntu2604-python314-compat.md): CHECKPOINT PASS,
exact internal .7 candidate c79b4feb…/system43266d97…, Python [3,14]. DEB/AppImage,
strict imports и real pkexec/READY gates PASS; full suites остаются FAIL/technical debt.
Exact hashes/inventories и локальные installation/rollback boundaries — в отчёте;
это не public download и не разрешение устанавливать candidate на workstation.
Frozen .5 ниже привязан к3.12 и не изменён. Workstation upgrade BLOCKED на ABI;
новые установленные/public/invitation версии не заявляются. NEXT — review U2604-COMPAT.

**Linux AWG/TCP Beta freeze: exact 0.2.12~l03.2.5, internal/unpublished.**
[Final installed review](releases/2026-10-25-linux-installed-awg-tcp-l04-1-final.md)
принимает E/F1/F2; L04.1-LIVE-2 и L04.1 DONE в installed AWG/TCP scope.
[Единый freeze manifest](releases/2026-10-25-linux-awg-tcp-beta-freeze.json) содержит
exact IDs/hashes/размеры и installation/rollback boundary; artifact bytes не менялись.
Registry restart F2 — отдельное operational observation: continuity NOT_PROVEN,
причина неизвестна, assignment/configuration неизменны. F2 не повторять, R3 не создавать.
Parent L04 IN_PROGRESS только из-за L04.2; L04.2/L05/teardown NOT_RUN.
MESH/Auto и messenger вне beta scope. Signing/upload/catalog/publication NOT_RUN.
**STOP. NEXT — решение владельца о signing и ограниченной публикации Linux AWG/TCP Beta.**

Предыдущие package/live checkpoints ниже — исторические receipts, не текущие NEXTs.

[R2 queued Connect/Close](releases/2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md)
Source/package PASS: новый internal **0.2.12~l03.2.5**, source1c2beb6/candidate
f0ee1760…; только user-side GUI correction. Оба exact offline systemd255/pkexec
DEB/AppImage gate и integrity PASS; system8d7d78ec… byte/contract verified unchanged.
Linux/AWG/TCP/package CI PASS; full CI54/54/54 failures сохранены, общего PASS нет.
Hashes/размеры в R2 report. Historical .4 не патчить/не пересобирать
под тем же именем. В самом R2 live E/F NOT_RUN; subsequent final review указан выше.
Public0.2.11/download links/catalog не меняются; internal candidate не опубликован.

[R1 source/package correction](releases/2026-10-25-linux-prestart-journal-l04-1-live-2-r1.md)
CHECKPOINT/source-system-package PASS, review accepted: final **0.2.12~l03.2.4**,
source053c4e5/candidate42ea0699…, authorization-session-v2, новый exact system8d7d78ec…
вместо build-9. Readback связывает inventory/build ID/auth protocol; actual build-9
отвергнут, matching reinstall возвращает READY. Exact DEB/AppImage и real systemd255
package/coherence/rollback gates PASS; hashes/размеры в отчёте. .2 сохраняется только
как historical evidence. Live retest NOT_RUN; общий CI не зелёный.
Финальный аудит R1 сохраняет первую diagnostic category через restart/failed
recovery. Exact gates повторены для .4/system-build-2; .3 остаётся промежуточным
immutable artifact, его evidence не перенесено на новые bytes. Public VERSION0.2.11
не менялся; .4 не опубликован и установлен только в disposable package environment.
Подтверждённый pre-start busy завершает IDLE; неизвестный outcome требует recovery
тем же owner. Нельзя вручную стирать journal, повторять Connect или обходить lock.

Correction [L04.1-LIVE-1-R](releases/2026-10-25-linux-poll-disconnect-l04-1-live-1-r.md)
DONE/review accepted (source/package): internal **0.2.12~l03.2.2**, source57f8eff/candidate d9c0d07f…;
exact inventory и оба real systemd255/pkexec package gates PASS. Linux/AWG/TCP/native/
package CI PASS; full suites54/54/53 failures, общий CI не зелёный.
[Live RETEST](releases/2026-10-25-linux-installed-awg-tcp-l04-1-retest.md) DONE/review accepted:
новая KVM, DEB/setup/AWG/TCP/traffic и AppImage close/reopen/single Disconnect PASS;
fresh nonce DNS вернул валидный terminal NOERROR/NODATA, принятый review наряду
с positive/NXDOMAIN. Cleanup/state сохранены; guest уничтожен, test state оставлен.
[LIVE-2](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-2.md) PARTIAL/review accepted:
A tamper/reinstall PASS; B1 не создаёт transport, но оставляет pending/APPLYING после
освобождения root lock. First-failure STOP, B2–F NOT_RUN; guest уничтожен, исходный
state сохранён. Никаких source fixes, автоматического L04.2/L05/teardown.
Final-2/0.2.12~l03.2.1
retired для завершения L04.1 после принятого PARTIAL; не заменять его bytes/hash.
Публичные version/catalog/download links не меняются.

L03.1/L03.2 приняты; parent L03 DONE в scope внутреннего кандидата. Source VERSION
и опубликованный Linux остаются0.2.11; прежний L03 candidate — **0.2.12~l03.2.1**.
[Точные артефакты/evidence](releases/2026-10-25-linux-candidate-l03-2.md).
Для исторического [L04.1](releases/2026-10-25-linux-installed-awg-tcp-l04-1.md) использован только
final-2 candidate `9d4b13cc…`, не CI rebuild `f7f6e765…`. Integrity PASS.
[L04.1-AUTH](releases/2026-10-25-linux-test-activation-l04-1-auth.md)
и продолжение
[L04.1-AUTH-PROVISION](releases/2026-10-25-linux-test-provisioning-l04-1-auth.md)
DONE/review accepted: одна отдельная identity/nl assignment, без повторного issuance.
[L04.1-LIVE-1](releases/2026-10-25-linux-installed-awg-tcp-l04-1-live-1.md) PARTIAL:
exact DEB/setup/реальные AWG/TCP/transfers/cleanup PASS в disposable Ubuntu24.04 VM;
original AppImage AWG PASS, но Disconnect после GUI reopen отказал на operation lock.
Остановлено без patch/rebuild; cleanup-only восстановил baseline, guest уничтожен.
L04.1 IN_PROGRESS до завершения positive gate, LIVE-2 и review; device teardown NOT_RUN.
Оба формата включают GUI/user daemon/vendor и exact embedded system/runtime;
candidate manifest связывает весь user inventory, source SHA, ABI и system build ID.
Это integrity/provenance, не подпись и не разрешение доверять неизвестному пакету.

Для чистой Ubuntu24.04: DEB устанавливается обычным `apt install ./<candidate>.deb`,
AppImage запускается обычным пользователем с прежними host GTK/GI/Secret Service/
GStreamer/Codec2 prerequisites. Python нужен3.12; pip/venv/checkout не требуются.
Если нет FUSE, допустим `--appimage-extract-and-run` с executable temp filesystem.
`--integrate` добавляет меню/URI handler; chat owner заново открывает original image.

Установка приложения не устанавливает root runtime и не активирует службы.
Общие **Опции → Установить системный компонент (без VPN)** доступны до создания
чата/identity; альтернативно фиксированный packaged `--setup-system` без аргументов.
Это явный pkexec, только вложенные проверенные bytes, без сети/произвольного файла.
Затем отдельное **Подготовить защищённый доступ чатов** / `--prepare-chat` включает
только idle DIRECT/service-only hosts. Setup не меняет VPN intent/фоновые настройки.
Live owner/sticky cleanup отклоняют reinstall; не удаляйте их markers ради установки.

DEB remove останавливает только собственный user chat unit и удаляет user package;
identity/history/settings и независимый root runtime/backups остаются. Root units
не enabled; работающие idle hosts не имеют dangling paths в удалённом GUI.
AppImage: сначала `--remove-integration`, затем удаление самого image. Это снимает
собственный menu entry и user owner, не удаляя данные/root runtime; общий icon остаётся.
Legacy six-file updater сохранён, но не применяется к internal candidate: upgrade/
миграция старого клиента — L08, не принята. Rollback — reviewed matching full pair
с explicit root reinstall только при idle/confirmed cleanup. L04.1 AWG/TCP принят;
parent L04 открыт только из-за L04.2, L05 NOT_RUN. Freeze не выполняет install/rollback.

Исторические версии/ограничения ниже не являются текущим составом L03.2.

## L03.1 — отдельный system/runtime checkpoint,25.10

[L03.1](releases/2026-10-25-linux-system-runtime-l03-1.md) объединяет manual MESH,
Auto, DIRECT/service-only hosts и units, root-owned `update.pub`, изолированный
Python3.12 runtime и штатные AWG3.1/Xray26.3.27 binaries/helpers/notices.
Manifest schema2 связывает весь состав и build ID; native digest отдельно не
является capability. Новый consumer отказывает старому schema1 host.
Installer удерживает startup/lifecycle/ownership locks, временно маскирует только
фиксированные templates, не останавливает живых owners и не стирает sticky cleanup.
Readback native/RNS/imports предшествует публикации capabilities; собственные файлы
имеют root-owned backup/rollback. Существующие безопасные файлы/пользовательские
identity/history/settings не переносятся и не удаляются.

Явное действие в настройках чата через существующий polkit/session подготавливает
только DIRECT и service-only hosts для подтверждённого UID. Не меняет VPN intent,
не включает VPN/boot autostart и не меняет фоновые настройки. После reboot нужен
повтор этого setup. GUI и chat daemon остаются обычным пользователем.

Это внутренний неподписанный system/runtime-компонент для Python3.12/amd64,
сам по себе не полный desktop installer. Теперь он включён в принятый L03.2
состав выше; live gates L04/L05 остаются отдельными. Legacy six-file archive/updater и публичные версии не
менялись. [Воспроизводимый isolated gate](../tests/fixtures/linux_system_runtime/README.md).

## Parity106 — отдельная незавершённая поставка,23.10

Ниже — исторический pre-L03.1 состав, не текущий NEXT.

Последний внутренний компонент — `mesh-system-r18` (24.10,phase22),98 файлов,
22 root-модуля и4 общих модуля. Добавлен UID/device-bound chat-only endpoint для
пользовательской службы через действующий MESH. Для GUI нужны соответствующие
`chat_bridge.py` и `chat_bridge_protocol.py` в полном bundle; обновление только
native/helper не обновляет GUI. Service-only без VPN и защищённый underlying DIRECT
ещё отсутствуют. SHA256 и точные readback-проверки находятся в phase22 общего отчёта.
Компонент не установлен, не подписан и не является AppImage/DEB/готовым клиентом.

Новые native workers и Linux service source находятся в разработке; собранный
`fc-mesh` не заменяет AppImage и не устанавливает systemd/polkit-helper. Будущий
setup должен атомарно обновить mesh-helper, его зависимости и AWG/TCP helper copies
с общим startup-lock, сохранить backup и все user identity/config/history.
GUI остаётся непривилегированным; установка helper — явное действие setup.
Такой offline component setup уже собран как `mesh-system-r13`, с атомарными файлами,
совместным lock, backup/rollback и последней публикацией capability marker.
Он неподписан, ещё не установлен и не заменяет AppImage/DEB. Сам GTK GUI в этот
компонент не входит; source-клиент Auto требует соответствующего обновления GUI.
Два capability marker публикуются последними после проверки; устаревший компонент
не активирует новый Auto. Точный SHA256 и readback — в phase17 отчёта. Обновление
доставляет `awg_lifecycle.py` также рядом с существующим AWG helper; при сохранённом
журнале незавершённой AWG-очистки setup отказывает даже без TUN. Не удаляйте этот
журнал и не сбрасывайте чужие routes/firewall для обхода проверки. Изолированная
установка helper в сетевом namespace не заменяет приёмку точного AppImage/DEB.
AppImage — primary, DEB — secondary, six-file archive/updater остаётся совместимым.
Сначала реальные UI/OS/DNS/upgrade проверки точных файлов, затем закрытая поставка;
public catalog/landing не переключать автоматически. Native SHA256, проверки и
недостающие шаги — в [едином отчёте](releases/2026-10-23-desktop-parity106.md).

В компонент включён изолированный RNS1.5.1 runtime; его источники/лицензии и exact106
канал проверяются отдельно от native worker. Воспроизводимая сборка разработчика:
`python -m scripts.build_desktop_rns --out <fresh-runtime-dir>` в окружении с
зафиксированными RNS1.5.1/pyserial3.5. Затем `scripts/package_mesh_component.py`
получает `--native <verified-native-build> --rns <fresh-runtime-dir> --out <fresh-delivery>`.
Это не инструкция для обычного пользователя устанавливать Python/Go вручную.
Штатный root-helper использует `/usr/bin/python3 -I -S`; установка проверяет
native metadata и RNS runtime до capability marker. Сбой проверки откатывает свои
файлы, не читает и не меняет пользовательскую identity. Для закрытой поставки
AppImage/DEB ещё обязательны установленная приёмка и upgrade проверка.

Текущий `scripts/package_linux.py` дополнительно включает GTK chat UI, закрытый
список модулей общего messenger/owner, LXMF1.1.1 из существующего hash lock и
полные Reticulum/LXMF/PySerial notices. DEB требует `gir1.2-secret-1`; нужен рабочий
Secret Service пользователя, обычно предоставляемый окружением рабочего стола.
При отсутствии/блокировке хранилища приложение сообщает ошибку, не записывает ключ
истории plaintext и не создаёт замену identity. AppImage должен проверяться на
доступность этой системной службы наряду с существующими GTK/GI prerequisites.
Это изменение сборочного workflow, не новый опубликованный пакет и не доказанное
обновление старой установки. Старый шестифайловый архив остаётся шестифайловым;
сам по себе он не доставляет новый messenger runtime. До закрытой поставки нужно
завершить его совместимый переход через полный bundle и проверить upgrade.

Голосовые исходники входят в полный bundle. DEB дополнительно объявляет
GStreamer GI/base/good/PulseAudio и Codec2 shared-library dependencies. Это не
ручная инструкция устанавливать development runtime; setup должен штатно
разрешать зависимости. AppImage bundling этих библиотек ещё не выполнен.
`audio-runtime-notices.txt` фиксирует LGPL/BSD-границы, но не заменяет полные
лицензии и соответствующие исходники будущих bundled библиотек. Synthetic audio
и Xvfb-проверки не заменяют установку точного пакета и проверку микрофона/выхода.

Полный bundle также включает `chat_notifications.py` и `chat_events.py`. Нужна
стандартная пользовательская session-D-Bus служба `org.freedesktop.Notifications`;
приложение не устанавливает свой системный daemon и не обращается к root-helper
для сообщений. Отсутствие службы не теряет непрочитанные сообщения. Проверка
изолированного D-Bus с тестовым сервером не заменяет показ уведомления из точного
установленного AppImage/DEB в целевом desktop session.

Полный bundle включает `chat_daemon.py`, `chat_client.py`, `chat_rpc.py`.
Launcher принимает отдельный `--chat-service` без создания GTK-окна. GUI запускает
фиксированную transient-службу `family-connect-chat.service` через `systemd --user`,
Type=dbus, имя `com.familyconnect.Chat1`; root/SCM-права для чата не нужны.
DEB объявляет `systemd` и `dbus-user-session` как зависимости; отсутствие рабочего
user manager приводит к явной ошибке службы, не запуску второго владельца в GUI.
AppImage-служба повторно открывает исходный AppImage, а не зависимый от GUI FUSE mount.
Уведомление запускает окно в отдельной пользовательской unit, чтобы остановка чата
не завершала GUI вместе с его cgroup. Это исходники workflow, не установленный пакет.
При установочной приёмке проверить user manager, Secret Service, session D-Bus,
закрытие GUI, новое окно по уведомлению, отключение фона и остановку после logout.
Изолированный тест использует Type=exec: реальный user manager не наблюдает имя
на отдельной тестовой шине. Production Type=dbus ещё требует пакетной приёмки.
Upgrade должен завершать старую chat unit после проверки нового bundle, перед
удалением старого runtime; дождаться освобождения store lock и сохранить старый
bundle для отката. Этот handoff и переход шестифайлового updater ещё не реализованы.
Не удалять `~/.local/share/family-connect/chat` или Secret Service при откате.

Полный bundle также содержит `provisioning/chat_admin.py` и
`clients/desktop/chat_announcements.py`; исходный manifest
`clients/shared/android106-announcements.json` фиксирует принятую семантику.
Операции идут через существующую D-Bus chat-службу и proof компьютера, а не
root-helper; установщик не выдаёт операторскую роль и не публикует объявления.
Список ограничен50 записями/страницу и1MiB ответа, запрос публикации/правки32KiB;
сжатые ответы отклоняются до распаковки. Проверки используют отдельные синтетические
identity/сервер и не заменяют приёмку точного установленного bundle.


## Опубликованная основа0.2.11 (историческая приёмка)

Статус: реализовано, собрано, проверено (CI + чистая Ubuntu 24.04) и опубликовано
на HTTPS release infrastructure; invitation landing переключена на AppImage как
основной Linux download (`.deb` и `.tar.gz` — secondary).

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

## 9. Acceptance (выполнено)

Чистая Ubuntu 24.04 (Docker `fc-accept-full` / `fc-accept-minimal`):

- AppImage: скачать → `chmod +x`/разрешить выполнение → запуск GUI; без `pip`, без venv,
  без source checkout; корректный icon; state writable; restart; `--integrate` создаёт
  `~/.local/share/applications/com.familyconnect.Client.desktop` (`Exec="...AppImage" %u`),
  icon и `x-scheme-handler/familyconnect`. На clean Ubuntu без GTK/GI падает
  `No module named 'gi'`; host prerequisites зафиксированы (см. ниже), self-contained
  по GTK-стеку **не** заявляется.
- DEB: `dpkg -i`/`apt install` → пункт меню → запуск; update/reinstall/uninstall; state
  сохранён; URI handler `x-scheme-handler/familyconnect`; `familyconnect://invite/<64hex>`
  доставляется приложению аргументом.

CI: artifact exists + executable + arch + AppImage `--appimage-extract` + `dpkg-deb --info`
+ package-content audit (нет identity/token/WG private/.env/DB) + xvfb/dbus smoke.

### Публикация (26.09)

- `FamilyConnect-0.2.11-x86_64.AppImage` — 8 559 096 B, SHA256
  `7dfaca6022a275e62eeac5b8c402477d493d5833181d238f2080aa62014ba83b`,
  `https://185.251.89.19:8443/downloads/FamilyConnect-0.2.11-x86_64.AppImage`.
- `FamilyConnect_0.2.11_amd64.deb` — 6 685 688 B, SHA256
  `a336624808b96de4455963307c609be1d3bddbbadf29976a9a0176207f415697`,
  `https://185.251.89.19:8443/downloads/FamilyConnect_0.2.11_amd64.deb`.
- Legacy `.tar.gz` остаётся `FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz`.

Производственная invitation landing проверена по `/i/#<token>` и `/invite/#<token>` с
Linux UA: AppImage — primary, `Ubuntu / Debian / Mint — .deb` и «Для опытных
пользователей — .tar.gz» — secondary; checkbox «Приложение установлено» отсутствует.
Скачанные с production артефакты совпадают с записанными SHA256 byte-level.

### Дополнительная runtime-проверка (26.09, рабочая Ubuntu 26.04)

Опубликованные артефакты дополнительно проверены на рабочей машине (Ubuntu 26.04,
GNOME Wayland, все host GTK/GI пакеты и NetworkManager уже установлены). Это
developer-machine smoke, не заменяет clean-Ubuntu acceptance выше.

- AppImage: `--appimage-extract` успешен; launcher GI/GTK/Adw preflight проходит,
  приложение доходит до создания `Adw.ApplicationWindow`. На этой машине нет FUSE
  (`/dev/fuse` отсутствует), поэтому прямой запуск AppImage требует
  `--appimage-extract-and-run` / `APPIMAGE_EXTRACT_AND_RUN=1`; реальное окно из
  sandbox не рендерится (display недостижим, нет Xvfb/sudo) — GUI-init покрыт CI
  xvfb smoke.
- AppImage `--integrate`: полный flow проверен в изолированном writable `$HOME` —
  корректные `~/.local/share/applications/com.familyconnect.Client.desktop`
  (`Exec="...AppImage" %u`, `MimeType=x-scheme-handler/familyconnect`), иконка
  11 896 B, `xdg-mime query default x-scheme-handler/familyconnect` →
  `com.familyconnect.Client.desktop`.
- DEB: `dpkg-deb --info/--contents` подтверждают `Depends` (в т.ч.
  `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `librsvg2-common`,
  `network-manager`, `libqrencode4`, `libzbar0`) и layout `/usr/bin/family-connect`
  → `/usr/lib/family-connect/launcher.py`; launcher preflight проходит, приложение
  доходит до создания окна.

VPN runtime prerequisites на этом хосте: kernel `wireguard` загружен, `network-manager`,
`pkexec`/`polkit`, `ip`, `nft`, `libqrencode4`/`libzbar0` присутствуют; `wg` tool,
`/dev/net/tun` и запущенный NetworkManager daemon в контейнере отсутствуют — реальный
VPN tunnel в sandbox не поднимается (см. Known limitations).

## 10. Known limitations

- AppImage НЕ self-contained по GTK-стеку: требует host `python3-gi`,
  `python3-gi-cairo`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `librsvg2-common`.
  Термин «self-contained» для AppImage не используется без оговорки про host deps.
- AppImage bundling `gi`/GTK4/libadwaita надёжно не решается; они остаются системными.
- Root AWG/TCP helper и их бинарники не входят в пользовательский пакет.
- Полный AppImage/DEB self-update не реализован в этой задаче.
- Пригласительная landing переключается на AppImage только после публикации реальных
  артефактов и чистой-Ubuntu приёмки.
