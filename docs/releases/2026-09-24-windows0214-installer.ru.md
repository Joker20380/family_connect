# Windows0.2.14 — совместимость установки и восстановление

Опубликован неизменяемый установщик0.2.14. Основание: первая установка0.2.13
на Windows10 Pro22H2/build19045.2364 завершается CLR0x80131506 до создания
службы; повторная попытка запускает повреждённый/несовместимый старый host.
По trace и CPU основная гипотеза — CET на старых системных патчах;
[аналог .NET](https://github.com/dotnet/runtime/issues/108589#issuecomment-2396857957).
Точное подтверждение на пользовательском ПК ожидается после установки0.2.14.

## Изменения и границы

- CETCompat=false только у host FamilyConnect: аппаратная shadow-stack защита
  процессов приложения не включается. Настройки защиты Windows не меняются.
  Это осознанный компромисс совместимости, не исправление Windows целиком.
- PrepareToInstall использует системный Windows PowerShell5.1/SCM, не старый EXE.
  Ожидает остановки/удаления службы; сохраняет ключи и профили.
- SetupLogging=yes, различение ошибки запуска и exit code; managed install errors
  включают stage, тип, HRESULT и Win32 code без ключей/конфигураций.
- .NET10.0.12 включён, MinVersion Windows10 1809/build17763, x64.
  Windows7/8/8.1/32-bit не поддерживаются; Windows10/11 targets не означают
  runtime acceptance каждой сборки. Совместимость конкретного Win10 ещё открыта.

## Артефакт

Source `6eed30ceb8333275bade123ecb50375478f331c7`, отдельная ветка `fix/windows10-installer-0214` от
принятого0.2.13: новые экспериментальные Core изменения не включены в этот EXE.
[GitHub](https://github.com/Joker20380/family_connect/releases/tag/windows-v0.2.14) ·
[HTTPS](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.14-pilot-unsigned.exe).
Размер 49942347 bytes; SHA256 `7b1af167a55a977c357c47b94407916fe27d1b343d33ecb69c42b2d11b85e886`.
Publisher signature отсутствует; канал имеет отдельную Ed25519-подпись offline.
Windows schema2/sequence10; legacy Linux/shared каталог сохранён.

## Проверки

- Local C# build и core runner passed; Windows-only DPAPI ветки локально skipped,
  выполнены на native CI.
- Проверка PE подтверждает CET flag отсутствует у нового host и присутствует у
  исходного SDK host — положительный контроль парсера.
- [Client CI](https://github.com/Joker20380/family_connect/actions/runs/36058000764):
  windows и windows-compatibility success; один и тот же EXE на Server2025/2022.
  Общий workflow failure из-за отдельной Android-задачи; в Windows release gate
  приняты именно две Windows-задачи, Android в этот выпуск не входит.
  Повреждённый остаточный EXE, создание службы, драйвер, broker, UI/URI, upgrade
  работающей службы, сохранение sentinel в data root, uninstall passed.
- [TCP](https://github.com/Joker20380/family_connect/actions/runs/36058000805) — success.
- [AWG](https://github.com/Joker20380/family_connect/actions/runs/36058000952) — success.
- [Phase0](https://github.com/Joker20380/family_connect/actions/runs/36058000759) — success.
- [UI](https://github.com/Joker20380/family_connect/actions/runs/36058000729) — success.
- [Ordinary user](https://github.com/Joker20380/family_connect/actions/runs/36058000753) — success.

UI screenshots просмотрены; ZIP hashes проверены по GitHub artifact digest;
EXE hash/size проверены по CI и полным публичным GitHub/HTTPS downloads.
Подписанный каталог проверяется production verifier и public anchor.
Физический Win10/Win11 прогон нового выпуска здесь не выполнялся.

## Rollout и откат

Страница приглашения указывает на0.2.14; HTTPS-конфиг меняется через nginx-t/HUP
только контейнера family-connect-product-https. Backup:
`state-product-https/config/rollbacks/windows0214-6eed30c`.
Для возврата страницы восстановить invite.html/nginx.conf/nginx-final.conf,
проверить nginx-t и HUP. Артефакты неизменяемые; каталог нельзя откатывать на
sequence9: коррекция только новым большим sequence. Не удалять пользовательские данные.
С0.2.13 — Проверить обновления; с0.2.12 и старше или после сорванной установки —
одна ручная установка нового EXE. На проблемном Win10 подтвердить install/start/connect.

Publisher: [36059536269](https://github.com/Joker20380/family_connect/actions/runs/36059536269) — success.
Локальный production verifier принял подпись, version0.2.14 и sequence10.
Страница: Firefox4 сценария ×13 проверок прошли;355 Markdown,2045 ссылок без ошибок.
