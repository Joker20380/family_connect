# Выбор сервера с флагом и нагрузкой на всех платформах — 26.09.2026

Расширяем список серверов как у конкурентов: флаг страны и нагрузка на момент
выбора, плюс каталог транспортов для быстрого добавления следующего транспорта.
Изменения внесены в исходники всех трёх клиентов; сборка, UI-приёмка и публикация
не выполнялись. Версии подняты только как кандидаты, production/каталоги прежние.

## Изменения

- Android (Friends): сервер RU/NL с флагом и нагрузкой (vector drawables,
  `ServerLoad.fetchAll()`), транспорт вынесен в `TRANSPORTS` каталог; `Transport`
  enum получил `label` для managed/pilot пикера.
- Linux GTK: флаги CSS-gradient + нагрузка в dropdown страны, `verified_server_loads()`
  и `Linux.server_loads()` (один запрос, обе страны), транспорт через `TRANSPORTS`.
- Windows: OwnerDraw-флаги и нагрузка в `ModernComboBox`, `ServerLoad.FetchAll()`,
  обновление дропдауна после загрузки.

## Кандидатные версии (не собраны)

| Клиент | Было | Стало |
| --- | --- | --- |
| Android | 0.1.18-beta50 / code50 | 0.1.18-beta51 / code51 |
| Linux | 0.2.10 | 0.2.11 |
| Windows | 0.2.14 | 0.2.15 |

## Проверка

- Linux: `python -m pytest clients/desktop/tests -q` — 221 passed, 1 сбой только из-за
  sandbox-ограничения сокета (`test_recovery`, не связано с изменениями).
  `test_server_load` расширен `verified_server_loads`.
- Linux GUI (`map_check`, `layout_check`) локально не запускались — нет X-дисплея/xvfb.
- Android: `ServerLoad.java` и `Transport.java` собраны отдельно через `javac` — успешно.
- Windows и полная Android-сборка — откладываются на CI.

## Осталось для выката (вне этой среды)

1. Пуш ветки выполнен в `main` (`6ad8856..2ffba77`), CI запущен.
2. Скачать и проверить артефакты CI (Windows installer, Linux tar, APK).
3. Офлайн-подпись каталогов `updates/windows.json` (sequence10→11) и Linux/Android metadata.
4. Публикация неизменяемых артефактов по HTTPS и проверка live URL/хешей.
5. Отдельные release notes/теги GitHub: для Linux `v0.2.11` имя `0.2.11.en.md`
   пересекается с исторической Windows-заметкой — при фактическом выкате нужен отдельный путь/имя.

### Результат CI (`2ffba77`)

- Linux ✅, Windows ✅ (+windows-compatibility ✅).
- Android: сборка/unit/lint ✅ (`assembleFriends`, `testFriendsUnitTest`, `lintFriends`,
  `verify-apk`), ❌ только `Real WG AWG TCP and Auto lifecycle on Android emulator` —
  тот же флаки-шаг, что падал на базовом `7db987b`, не связан с флагами/нагрузкой/каталогом.
  До Android-релиза этот шаг закрывается реальной приёмкой на устройстве.

### Android beta51: подготовка публикации

Подготовлен генератор discovery-манифеста `deploy/friends/prepare-android-manifest.py`
и кандидат-патч пригласительной страницы (`Beta50→Beta51`, без публикации).
Порядок после скачивания/проверки APK:

1. Приёмка APK: `pilot/android-awg/verify-apk.py --abis arm64-v8a` + реальная
   активация и 4 сочетания страна×транспорт, повтор/рестарт, отказ по второй ссылке.
2. Манифест: `python3 deploy/friends/prepare-android-manifest.py
   /path/to/FamilyConnect-Test-0.1.18-beta51.apk --version 0.1.18-beta51
   --version-code 51 --output /tmp/android-friends-update.json`.
3. Выложить APK на HTTPS-хост в `/downloads/FamilyConnect-Test-0.1.18-beta51.apk`.
4. Публикация discovery на сервере: `python3 deploy/friends/install-android-update.py
   /tmp/android-friends-update.json` (проверяет размер/хеш APK и атомарно публикует
   `updates/android-friends.json`).
5. После публикации развернуть пригласительную страницу и обновить
   `docs/getting-started.*`, README, `docs/releases.md` и отчёт хешами/размером.

## Откат

`git revert` коммитов этой задачи; вернуть прежние версии в `VERSION`, `APP_VERSION`,
`FamilyConnect.csproj`/`setup.iss`/`build.ps1` и `build.gradle`. Публичных артефактов не создавалось.
