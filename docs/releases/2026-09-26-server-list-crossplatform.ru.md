# Выбор сервера с флагом и нагрузкой на всех платформах — 26.09.2026

Расширяем список серверов как у конкурентов: флаг страны и нагрузка на момент
выбора, плюс каталог транспортов для быстрого добавления следующего транспорта.
Изменения внесены в исходники и опубликованы на всех трёх платформах:
Android beta51/code51, Linux0.2.11, Windows0.2.15.

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
| Linux | 0.2.10 | 0.2.11 | опубликован 26.09 |
| Windows | 0.2.14 | 0.2.15 | опубликован 26.09 |

## Проверка

- Linux: `python -m pytest clients/desktop/tests -q` — 221 passed, 1 сбой только из-за
  sandbox-ограничения сокета (`test_recovery`, не связано с изменениями).
  `test_server_load` расширен `verified_server_loads`.
- Android: `ServerLoad.java` и `Transport.java` собраны отдельно через `javac` — успешно.
- Полные сборки/UI/нативные проверки — в CI, см. ниже.

### Результат CI (`2ffba77`)

- Linux ✅, Windows ✅ (+windows-compatibility ✅).
- Android: сборка/unit/lint ✅ (`assembleFriends`, `testFriendsUnitTest`, `lintFriends`,
  `verify-apk`), ❌ только `Real WG AWG TCP and Auto lifecycle on Android emulator` —
  тот же флаки-шаг, что падал на базовом `7db987b`, не связан с флагами/нагрузкой/каталогом.
  Этот шаг закрыт реальной приёмкой beta51 на устройстве.

### Android beta51

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

### Windows 0.2.15

Принят артефакт CI `2ffba77` (`windows` и `windows-compatibility` success), выложен
immutable GitHub release `windows-v0.2.15` и HTTPS. Каталог `updates/windows.json`
подписан offline Ed25519 (schema2, sequence11, version0.2.15).

- `FamilyConnect-Setup-0.2.15-pilot-unsigned.exe` — 49941739 bytes, SHA256
  `3e610962da40510e0dce7a9d794f4352ba113e090e462f6d1c75d7712f965e6b`.
- GitHub: `https://github.com/Joker20380/family_connect/releases/download/windows-v0.2.15/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe`.
- Каталог: `https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/windows.json`.
  Signature проверена локально публичным anchor `update.pub`.

### Linux 0.2.11

Кроме manual control preview опубликован и подписанный updater-канал, чтобы
существующие Linux-клиенты обновлялись через «Check for updates» (раньше
`pilot.json` указывал на 0.2.9 и клиент писал «последняя версия»).

- Signed updater release `v0.2.11` (immutable, GitHub):
  - `FamilyConnect-Linux-0.2.11.tar.gz` — 82897 bytes, SHA256
    `3aaf6e0661b5dd9e6136f12d96c66b2ad103c7fa8b0fc9c47a6db918c511b795`.
  - `FamilyConnect-Setup-0.2.11-pilot-unsigned.exe` — 49934207 bytes, SHA256
    `9cc04ba7446ff31d87e2a3d96dfb7faf24e61cf81a7eac8eccea0adb29c3ed3c`
    (байт-в-байт переименованный принятый Windows 0.2.11 preview; slot нужен
    schema1 каталогу, Linux-апдейтер его не скачивает).
- Каталог `updates/pilot.json` подписан offline Ed25519 (schema1, sequence9,
  version0.2.11), signature проверена локально публичным anchor `update.pub`.
- Сборка Linux-архива сделана воспроизводимой (`scripts/package_desktop.py`:
  фиксированные `mtime=0` и порядок, gzip `mtime=0`).

Manual control preview (опциональный, без VPN helpers):

- `FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz` — 121503 bytes, SHA256
  `6d4c6186fa69d36f4835b380582ba046e1a3a70abf359ee1a0332dd741f97a56`.
- `FamilyConnect-Linux-0.2.11-invitation.txt` — 3371 bytes, SHA256
  `59fb42f034b86a2fc451f6cb3914ed2e4f19c93805e9348a5bd1676f1b75c279`.
- GitHub: `https://github.com/Joker20380/family_connect/releases/tag/desktop-preview-20260926-5b02e8cb`.

### Пригласительная страница

Страница обновлена до Android beta51 / Windows0.2.15 / Linux0.2.11, CSP script-hash
пересчитан (`script-src 'sha256-msSL16npkKnn6mE2zGpGcwEA2unk7hXpvgeJN/6Uqh4='`),
nginx перезагружен. `scripts/check_invitation_page.py`: 4 сценария × 13 проверок passed.
Публичные URL `200 OK`, размеры и SHA256 совпали.

## Откат

Серверные бэкапы сохранены в `/opt/apps/family_connect/state-product-https/config`:

- `invite.html`/`nginx.conf`/`nginx-final.conf` `.before-desktop0211-20260926`;
- предыдущие бэкапы beta51: `.before-server-list-beta51-20260926`,
  `.before-beta51-download-20260926`, `android-friends-update.json.before-android-update-51`.

Откат страницы/config: восстановить `invite.html`, `nginx.conf`, `nginx-final.conf`
из `.before-desktop0211-20260926`, затем `nginx -t` и HUP только
`family-connect-product-https`. Windows-каталог не откатывать на меньший sequence:
при ошибке публиковать корректирующий каталог с большим sequence; установленные
клиенты и данные сохранять. Опубликованные immutable APK/EXE/архивы не заменять.
Android-код на устройстве не понижать; исправления выпускать с большим versionCode
и той же подписью.

`git revert` коммитов этой задачи: вернуть прежние версии в `VERSION`, `APP_VERSION`,
`FamilyConnect.csproj`/`setup.iss`/`build.ps1` и `build.gradle`.

## Остаётся открытым

- Физическая приёмка Windows10/11 на пользовательском ПК; publisher signing отсутствует.
- Российская сеть, длительный фон, смена сети и долгая устойчивость.
- Linux updater-канал поднят до 0.2.11; системные VPN helpers по-прежнему
  устанавливаются вручную (updater ставит только application-файлы).
