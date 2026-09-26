# Выбор сервера с флагом и нагрузкой на всех платформах — 26.09.2026

Расширяем список серверов как у конкурентов: флаг страны и нагрузка на момент
выбора, плюс каталог транспортов для быстрого добавления следующего транспорта.
Изменения внесены в исходники всех трёх клиентов. Android beta51 собран, принят
на устройстве и опубликован; Linux0.2.11 и Windows0.2.15 остаются кандидатами
в исходниках — сборка, подпись и публикация desktop не выполнялись.

## Изменения

- Android (Friends): сервер RU/NL с флагом и нагрузкой (vector drawables,
  `ServerLoad.fetchAll()`), транспорт вынесен в `TRANSPORTS` каталог; `Transport`
  enum получил `label` для managed/pilot пикера.
- Linux GTK: флаги CSS-gradient + нагрузка в dropdown страны, `verified_server_loads()`
  и `Linux.server_loads()` (один запрос, обе страны), транспорт через `TRANSPORTS`.
- Windows: OwnerDraw-флаги и нагрузка в `ModernComboBox`, `ServerLoad.FetchAll()`,
  обновление дропдауна после загрузки.

## Версии

| Клиент | Было | Стало | Состояние |
| --- | --- | --- | --- |
| Android | 0.1.18-beta50 / code50 | 0.1.18-beta51 / code51 | опубликован 26.09 |
| Linux | 0.2.10 | 0.2.11 | кандидат в исходниках |
| Windows | 0.2.14 | 0.2.15 | кандидат в исходниках |

## Проверка

- Linux: `python -m pytest clients/desktop/tests -q` — 221 passed, 1 сбой только из-за
  sandbox-ограничения сокета (`test_recovery`, не связано с изменениями).
  `test_server_load` расширен `verified_server_loads`.
- Linux GUI (`map_check`, `layout_check`) локально не запускались — нет X-дисплея/xvfb.
- Android: `ServerLoad.java` и `Transport.java` собраны отдельно через `javac` — успешно.
- Windows и полная Android-сборка — откладываются на CI.

### Результат CI (`2ffba77`)

- Linux ✅, Windows ✅ (+windows-compatibility ✅).
- Android: сборка/unit/lint ✅ (`assembleFriends`, `testFriendsUnitTest`, `lintFriends`,
  `verify-apk`), ❌ только `Real WG AWG TCP and Auto lifecycle on Android emulator` —
  тот же флаки-шаг, что падал на базовом `7db987b`, не связан с флагами/нагрузкой/каталогом.
  Этот шаг закрыт реальной приёмкой beta51 на устройстве.

### Android beta51: сборка и публикация

Подписанный APK собран локально для ABI `arm64-v8a`, проверен `pilot/android-awg/verify-apk.py
--abis arm64-v8a` и установлен поверх beta50 без очистки данных на Redmi Note 9 Pro:
`versionCode=51`, `versionName=0.1.18-beta51`, запуск без сбоев, `FriendsActivity`
возобновлена, Chaquopy Python3.10 загружен. Визуально подтверждены серверы RU/NL
с флагом и нагрузкой и каталог транспортов.

Публичный артефакт:

- `FamilyConnect-Test-0.1.18-beta51.apk` — 36456636 bytes, SHA256
  `79a2d28667332ea442eae1b895b4fc632b52734cbed1e75bd95f32b7175ad366`.
- Certificate SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`
  (тот же подписант, что у beta50).

Публикация:

1. APK выложен на HTTPS-хост и добавлен точный nginx `location` `/downloads/...beta51.apk`.
2. Discovery-манифест подготовлен `prepare-android-manifest.py` и атомарно опубликован
   `install-android-update.py`: `updates/android-friends.json` теперь code51.
3. Пригласительная страница обновлена `Beta50→Beta51`, CSP script-hash пересчитан
   (`script-src 'sha256-WyVIGrrQ2wnvZXFUcQR+D3WzFzmQ6TCi73vs+9IjzuY='`), nginx
   перезагружен. `scripts/check_invitation_page.py`: 4 сценария × 13 проверок passed.
4. Публичные URL проверены: APK `200 OK`, манифест code51, страница содержит только beta51.

## Осталось для выката desktop

1. Собрать и проверить артефакты CI для Windows0.2.15 и Linux0.2.11.
2. Офлайн-подписать каталог `updates/windows.json` (sequence10→11) и Linux metadata.
3. Опубликовать неизменяемые desktop-артефакты по HTTPS и проверить live URL/хеши.
4. Отдельные release notes/теги GitHub: для Linux `v0.2.11` имя `0.2.11.en.md`
   пересекается с исторической Windows-заметкой — нужен отдельный путь/имя.

## Откат

Серверные бэкапы сохранены в `/opt/apps/family_connect/state-product-https/config`:

- `invite.html.before-server-list-beta51-20260926`;
- `nginx.conf`/`nginx-final.conf` `.before-server-list-beta51-20260926` (до CSP/страницы);
- `nginx.conf`/`nginx-final.conf` `.before-beta51-download-20260926` (до добавления location);
- `android-friends-update.json.before-android-update-51` (discovery beta50).

Откат страницы/config: восстановить файлы `invite.html`, `nginx.conf`,
`nginx-final.conf` из `.before-server-list-beta51-20260926`, затем `nginx -t` и HUP
только `family-connect-product-https`. Откат discovery: восстановить
`android-friends-update.json.before-android-update-51`. Опубликованный APK beta51
оставить неизменяемым; Android-код на устройстве не понижать, исправления выпускать
с большим versionCode и той же подписью.

`git revert` коммитов этой задачи: вернуть прежние версии в `VERSION`, `APP_VERSION`,
`FamilyConnect.csproj`/`setup.iss`/`build.ps1` и `build.gradle`.
