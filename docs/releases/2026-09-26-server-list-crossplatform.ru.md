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

1. Пуш ветки → CI собирает/тестирует Windows/Linux/Android.
2. Скачать и проверить артефакты CI (Windows installer, Linux tar, APK).
3. Офлайн-подпись каталогов `updates/windows.json` (sequence+1) и Linux/Android metadata.
4. Публикация неизменяемых артефактов по HTTPS и проверка live URL/хешей.
5. Отдельные release notes/теги GitHub: для Linux `v0.2.11` имя `0.2.11.en.md`
   пересекается с исторической Windows-заметкой — при фактическом выкате нужен отдельный путь/имя.

## Откат

`git revert` коммитов этой задачи; вернуть прежние версии в `VERSION`, `APP_VERSION`,
`FamilyConnect.csproj`/`setup.iss`/`build.ps1` и `build.gradle`. Публичных артефактов не создавалось.
