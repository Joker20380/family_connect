# Установка клиентов

**Beta64/code64 прошла CI и подписана локально, но ещё не установлена/опубликована.**
SHA256 APK `b1a9f62116265b13a8482292175d3a685dca23ad3a5be0e4af5ef995a4d32d69`,49671035байт;
прежний signer67a90d1b проверен. Нужна owner-приёмка вместе с обновлённым шлюзом и
действующими материалами доступа. Ссылки/хэши опубликованных версий ниже не менялись;
тест повторять не нужно. Публичной ссылки beta64 пока нет.
[Подготовка выпуска](releases/2026-10-04-beta64-paired-candidate.md).

**Beta63/code63 установлена и проверена на Redmi владельца.** CI/offline-подпись и
сохранение регистрации при обновлении PASS. [Отдельный APK beta63](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta63.apk)
проверен04.10 16:57UTC: HTTP200,49654651байт, SHA256 скачанного/установленного файла
`ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`;
SHA256 подписи `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Redmi владельца уже обновлён. При последующем разрешённом обновлении выбрать «Обновить»
поверх приложения, без удаления, очистки данных или новой регистрации; проверить63 и прежний Support ID.
Первичная приёмка использовала моделируемую причину сбоя. Позже на неизменённой63
[настоящий native exhaustion→poll→переподключение](releases/2026-10-04-beta63-native-exhaustion.md)
тоже прошёл при контролируемой потере RTP. Первичный мобильный обрыв не объявлен исправленным.
Тестеру сохранить текущую версию/данные, мобильный тест сейчас не повторять.
Основной канал/updater/приглашение остаются60. [Этапы поставки](releases/2026-10-04-beta63-recovery-candidate.md).

**Beta62/code62 — проверенное целевое обновление только для FC-YHQB-9VJN.**
[Android beta62 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta62.apk)
принят на owner Redmi поверх61 r2; данные/UID/Identity/Support, AWG и экспорт сохранены.
HTTP200, скачанный SHA256 `f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`;
signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Установить **Обновить** поверх текущей версии на рабочем Wi-Fi. Не удалять приложение,
не очищать данные; новое приглашение не требуется. Проверить62 и прежний Support ID.
**Мобильный экспорт(11) уже получен и сопоставлен с сервером; повтор сейчас не нужен.**
[Первый сбой и причина отсутствия восстановления](releases/2026-10-04-field-export11-beta62.md).
Не очищать кэш/данные и не переустанавливать приложение.
Текущая серверная граница04.10 17:30:19UTC (20:30:19МСК), не четыре часа после каждого
открытия приложения; на14:55UTC оставалось2ч35м. Если окно прошло, сначала обновить
материалы на рабочем Wi-Fi и проверить готовность. [Проверка окна](releases/2026-10-04-beta62-four-hour-rollout.md).
Корреляция реального owner-сеанса доказана, исходный разрыв не объявляется исправленным.
[Проверки и ограничения](releases/2026-10-04-beta62-recovery-candidate.md).
Основная загрузка/updater остаются60; опубликованный61 r2 не заменяется.

**Предыдущая целевая версия beta61 r2 — историческая приёмка, текущий кандидат62 выше.**
Сохранность данных/AWG/экспорт и реальная client/server корреляция приняты; исправление
исходного разрыва не заявляется. Отдельная проверенная загрузка04.10:
[Android beta61 r2 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta61-r2.apk).
SHA256 `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb`;
versionName/code `0.1.18-beta61`/61, production signer прежний. Старый61/c98852b3
не передавать. [Полная приёмка/подпись/rollback](releases/2026-10-03-beta61-targeted-acceptance.md).
HTTP200, скачанные SHA256/подпись проверены; [отчёт доставки](releases/2026-10-04-beta61-r2-direct-delivery.md).
Это не основная Android-версия: landing и updater остаются60; остальные ссылки ниже —60.
Передать только подписанный APK, установить **Обновить** поверх60 без удаления,
очистки данных или нового приглашения; проверить прежний Support ID FC-YHQB-9VJN.
До единственной мобильной попытки оператор проверяет свежие leases и READY/ACK;
после разрыва немедленный экспорт. Не менять FIELD admission или public updater.

**Актуально03.10: beta60/code60 опубликована**, принятый APK SHA8ee59352 и signer67a90d1
не изменены. [Установка/обновление](getting-started.ru.md). Support ID регистрации:
Настройки → О приложении / Диагностика → Копировать Support ID; передавать ID, не ключи.
Обновлять поверх, без удаления/очистки. Существующий FIELD cohort owner+FC-YHQB-9VJN
(2/cap3) не расширяется обновлением. Историческая подготовка ниже заменена [отчётом публикации](releases/2026-10-03-field1-release-final.md#beta60-publication--2026-10-03).

## Исторические этапы подготовки

Финальный FIELD-кандидат добавляет Support ID регистрации: Настройки → О приложении /
Диагностика → Копировать Support ID.59 ещё не опубликована;8229a36 — предыдущий
локальный APK, не пересобранный кандидат. [Статус и шаги тестера](releases/2026-10-03-field1-release-final.md).
Обновлять поверх приложения, не удалять и не очищать данные. Передать Support ID,
не ключи; дождаться явного разрешения оператора перед FIELD-тестом.

Пересобранный локальный кандидат: исходники `5abc2da`, SHA256 APK
`6d13720bc8cff25d51d95ff7453127577890bee881685a4a66c86fae163f2148`.
Установлен поверх58 на Redmi владельца03.10, не опубликован. Identity/данные
сохранены; Auto/AWG/TCP PASS. Авторизованная HTTP-доставка возвращает ранее
назначенный ID: отображение/Copy/restart/DIAG PASS, без новой identity/регистрации.
Hosted CI и публикация ещё не завершены. FIELD не расширять.
Указанные ниже `b952c3b` / `8229a36` — предыдущая сборка. Публичная загрузка остаётся51.

FIELD-кандидат03.10: beta59/code59 проверяется локально, **не установлена и не
опубликована**. Основная загрузка51 до приёмки обновления поверх58; не удалять
приложение/данные/Device Identity. [Статус](releases/2026-10-03-field1-release-diag1a.md).

Локальный кандидат собран/подписан из `b952c3b`, SHA256 APK
`8229a36e8b176aa49346f3bf106f4f1229cb492a47c1c50e86593ddcb4c85a3b`.
Это не публичная загрузка и не завершённый rollout; ссылки ниже остаются51.

Последний приватный checkpoint03.10.2026: **`0.1.18-canary58-physical`/58 установлена
поверх57**, те же Friends package/signer/UID/data, encrypted restart READY/ACK_RECEIVED.
SHA256 APK `91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`;
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Private launcher hook исправлен, ON/OFF проверены на устройстве. Physical BLOCKED:
MIUI запрещает ADB input, ручной CONNECT не наблюдался. После restart override OFF,
приложение отключено. Не public release; invitation/download/catalog не менялись и
не перепроверялись. [Текущее состояние/источники](releases/2026-10-03-5n-physical-hook-fix-and-rehearsal.ru.md).

Текущий приватный checkpoint03.10.2026: точная `0.1.18-canary57-physical`/57
**установлена поверх55**, package/signer и данные сохранены; encrypted restart
READY/ACK_RECEIVED. SHA256
`dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
До restricted CONNECT diagnostic Activity упала при переходе в отсутствующую MainActivity.
Override OFF, Auto сохранён, приложение отключено. Physical acceptance FAIL; Stage5N OPEN.
Не public release: invitation/download/update-каталоги не менялись и не перепроверялись.
[Установка, persistence и точный отказ](releases/2026-10-03-5n-physical-restricted-rehearsal-final.ru.md).
Ниже сохранены исторические build-only checkpoints.

Приватная acceptance-сборка03.10.2026: `0.1.18-canary57-physical`/57 arm64 подписана,
**не установлена и не опубликована**; Redmi остаётся canary55. Те же package/signer;
debuggable-упаковка включает существующие diagnostic Activities только для приёмки.
SHA256 APK `dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
Public/invitation/update-каталоги не менялись; не распространять diagnostic-сборку.
[Подпись, тесты и блокер credential reload](releases/2026-10-03-5n-physical-restricted-rehearsal.ru.md).

Windows: версия0.2.15, Windows10 1809+ /11 x64. .NET включён в установщик.
После неудачной установки0.2.13 запустите новый установщик поверх оставшихся файлов.
Ручная настройка служб не требуется. Проверка на проблемном Win10 ПК ещё ожидается.

[English](clients.en.md) · [Главная](../README.ru.md)

Сверено 23.09.2026. У платформ разные версии и возможности.

## Android

Локальная проверка совместимости,02.10.2026: `0.1.18-canary56-challenge`/56 arm64
**собран без подписи**, не готов для установки/обновления, не установлен/не опубликован.
SHA256 `5ca1d29101df529cce197e5eeb82f231b50e3f4fc76c8835ba12fdad0c2122b0`.
Последние задокументированные installed55 и public/invitation51 не менялись и не
перепроверялись. Новых download/update ссылок/каталогов нет. Причина production503
не доказана; [локальные тесты, pins и BLOCKED gate](releases/2026-10-02-5n-real-owner-challenge-503.md).

Attempt15,02.10.2026: приватный `0.1.18-canary55-receipt`/55 **установлен поверх54**
на Redmi владельца; APK/подпись проверены, uninstall/data reset не было. SHA256
`680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
Реальный app challenge503 не позволил подтвердить READY; серверный restricted rollout
откачен. На телефоне55, не public/FIELD release. Public beta51/страница приглашений
не менялись и не перепроверялись. Build-only блоки ниже — исторические checkpoint.
[Доказательства и ограничения attempt15](releases/2026-10-02-5n-prov1-attempt15.ru.md).

Локальная сборка02.10.2026: приватный `0.1.18-canary55-receipt`/55 arm64 добавляет
структурированный post-import readiness receipt и аутентифицированный ACK.
Прежние package/beta signer; update-compatible с54; **собран/подписан, НЕ установлен
и НЕ опубликован**. SHA256 `680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
[Локальный путь APK, проверки и контракт](releases/2026-10-02-5n-device-readiness-receipt.ru.md). Установленный54 и
public beta51/страница приглашений ниже — последние документированные состояния;
публичные ссылки не заменены и артефакты не перепроверены. Production/authority не менялись.

Состояние02.10.2026: приватный `0.1.18-canary54-prov1`/54 собран, подписан прежним
beta-сертификатом и **установлен поверх field52 на Redmi владельца** в attempt14.
Финальные APK/hash/signature проверены16:47UTC; uninstall/data clear не было.
Серверная попытка откачена после ошибки UI observation; restricted cache readiness
не подтверждена. На телефоне остаётся54; публичной раздачи/FIELD release нет.
Ссылки public beta51/страницы приглашений не менялись и не перепроверялись.
[Результат attempt14](releases/2026-10-02-5n-prov1-attempt14.ru.md) ·
[Provenance и SHA256 canary](releases/2026-10-02-5n-android-canary-build.ru.md).

[Инструкция Friends beta](getting-started.ru.md): Android 8+, ARM64 beta60,
доступ по приглашению, VPN, текст и голосовые. APK распространяется
через страницу приглашения и HTTPS; в GitHub Releases и магазинах её пока нет.
Для сборки используйте требования [client workflow](../.github/workflows/clients.yml).
Debug APK из CI не предназначена для обновления установленной Friends beta.

## Текущие загрузки со страницы приглашения

[Linux 0.2.11 AppImage](https://185.251.89.19:8443/downloads/FamilyConnect-0.2.11-x86_64.AppImage) · [Linux 0.2.11 .deb](https://185.251.89.19:8443/downloads/FamilyConnect_0.2.11_amd64.deb) · [Windows 0.2.15 / 2ffba77](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe)

Установите клиент, затем откройте его по ссылке приглашения или кнопкой «Открыть Family Connect»
на странице приглашения. Windows устанавливает обработчик ссылки вместе со службой;
существующая активация сохраняется.

Windows 0.2.15 — основная версия. Windows 0.2.14 доступна как compatibility fallback
для некоторых старых установок Windows 10: на странице приглашения она показана как
вторичная кнопка «Скачать совместимую версию 0.2.14»
([immutable EXE](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.14-pilot-unsigned.exe)).

Linux теперь распространяется как обычные пользовательские артефакты:

- `FamilyConnect-0.2.11-x86_64.AppImage` — основной вариант; `chmod +x` и запуск;
  без pip/venv/source checkout. Хост-зависимости GTK/GI — в [отчёте](linux-appimage-deb.ru.md).
- `FamilyConnect_0.2.11_amd64.deb` — Ubuntu / Debian / Mint: `sudo apt install ./FamilyConnect_0.2.11_amd64.deb`,
  приложение появляется в меню и регистрирует `x-scheme-handler/familyconnect`.
- `FamilyConnect-Control-Linux-preview-5b02e8cb9fde119f.tar.gz` — только для опытных / manual.

Системные VPN helpers устанавливаются отдельно. SHA256 и проверки — в [releases.md](releases.md)
и [Linux-отчёте](linux-appimage-deb.ru.md).

[Windows GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/windows-v0.2.15) · [Linux GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/desktop-preview-20260926-5b02e8cb) · [Хеши и проверки](releases/2026-09-26-server-list-crossplatform.ru.md).
Обновляйте без удаления идентичности и данных. Windows0.2.15 использует отдельный подписанный каталог; с0.2.12 и старше нужна одна ручная установка. Linux и прежний общий каталог сохранены. Desktop-мессенджер не принят наравне с Android.
Ниже сохранён отдельный старый сценарий GitHub v0.2.9; для новых приглашений используйте текущие загрузки выше.

Windows0.2.15 автоматически создаёт локальный ключ при первом запуске. Для доступа нужно приглашение: на телефоне **Настройки → Пригласить друга**, отправьте полную ссылку на ПК и откройте её. Либо нажмите на ПК **Активировать по приглашению**, вставьте полную ссылку и нажмите **Активировать доступ**. Сам запуск ярлыка не передаёт приглашение. При обновлении существующий доступ сохраняется.

## Исходный GitHub v0.2.9: Linux

Опубликован [пилот v0.2.9](https://github.com/Joker20380/family_connect/releases/tag/v0.2.9).
Интерфейс — **GTK 4/libadwaita**, не Tk. Нужны системный Python с GI,
GTK 4.8+, libadwaita 1.2+, cryptography и NetworkManager с поддержкой WireGuard.
Для Debian/Ubuntu:

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cryptography network-manager
```

Скачайте и распакуйте `FamilyConnect-Linux-0.2.9.tar.gz` из релиза. В каталоге архива
выполните `sh install-linux.sh`, затем откройте Family Connect из меню приложений.
Запускайте интерфейс обычным пользователем; привилегированные действия используют
системное разрешение. Индивидуальную активацию/профиль подготавливает оператор.
В этом релизе нет мессенджера и схемы приглашений Android Friends.

Из исходников: после установки зависимостей выполните `sh clients/desktop/install-linux.sh`.
Экспериментальная парная control-сборка отличается от шестифайлового release-архива:
[инструкция оператора](linux-control-preview-rollout.ru.md).

## Исходный GitHub v0.2.9: Windows x64

Скачайте `FamilyConnect-Setup-0.2.9-pilot-unsigned.exe` из
[релиза v0.2.9](https://github.com/Joker20380/family_connect/releases/tag/v0.2.9).
Установщик включает нативный клиент, .NET runtime, broker и VPN-компоненты.
Для установки нужны права администратора; отдельный клиент WireGuard не требуется.
Доверенной Authenticode-подписи Family Connect пока нет; не отключайте защиту ради
установки. Выпуск Windows ARM64 не проверен.

Нажмите **Получить код устройства**, передайте публичный код оператору, импортируйте
выданный `.fcactivation` и подключитесь. Подробности — в
[инструкции нативного Windows-клиента](windows-native.ru.md).
Активация настольного релиза отличается от новой Android Friends.

## Обновления и ограничения

Настольные обновления проверяют каталог с offline-подписью и хеши файлов:
[описание](updates.ru.md). Android Friends проверяет обновления в приложении; установку APK с прежним beta-ключом подтверждает пользователь.
Успешная сборка или проверка установщика не подтверждает надёжность VPN в любой сети.
[STATUS](STATUS.md) и датированные отчёты разделяют проверки установки, интерфейса,
сети и восстановления.

[Историческая инструкция первых клиентов](clients-legacy.ru.md) сохранена для раннего
WireGuard-эксперимента; старые указания про Tk и Windows-обёртку больше не актуальны.
# FIELD-1: публикация — 2026-10-03

Android `0.1.18-beta60` / code60 подписан, принят на Redmi владельца и обязательными
hosted gates и **опубликован без изменения байтов**. Публичный SHA256:
`8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
Исторический beta59 не публикуется. Приглашения/скачивание и оба Android-каталога
указывают beta60; optional/minimum1, FIELD owner-only/cap3.
