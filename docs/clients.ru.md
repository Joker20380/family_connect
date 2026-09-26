# Установка клиентов

Windows: версия0.2.15, Windows10 1809+ /11 x64. .NET включён в установщик.
После неудачной установки0.2.13 запустите новый установщик поверх оставшихся файлов.
Ручная настройка служб не требуется. Проверка на проблемном Win10 ПК ещё ожидается.

[English](clients.en.md) · [Главная](../README.ru.md)

Сверено 23.09.2026. У платформ разные версии и возможности.

## Android

[Инструкция Friends beta](getting-started.ru.md): Android 8+, ARM64 beta51,
доступ по приглашению, VPN, текст и голосовые. APK распространяется
через страницу приглашения и HTTPS; в GitHub Releases и магазинах её пока нет.
Для сборки используйте требования [client workflow](../.github/workflows/clients.yml).
Debug APK из CI не предназначена для обновления установленной Friends beta.

## Текущие загрузки со страницы приглашения

[Linux 0.2.11 AppImage](https://185.251.89.19:8443/downloads/FamilyConnect-0.2.11-x86_64.AppImage) · [Linux 0.2.11 .deb](https://185.251.89.19:8443/downloads/FamilyConnect_0.2.11_amd64.deb) · [Windows 0.2.15 / 2ffba77](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe)

Установите клиент, затем откройте его по ссылке приглашения или кнопкой «Открыть Family Connect»
на странице приглашения. Windows устанавливает обработчик ссылки вместе со службой;
существующая активация сохраняется.

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
