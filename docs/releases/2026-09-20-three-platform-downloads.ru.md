# Три платформы на странице загрузок — 20.09.2026

Публичная страница: https://185.251.89.19:8443/invite/
Android beta25, Linux 0.2.9 preview d93611e с общей навигацией и Windows
0.2.9 preview21b740a. Старую универсальную beta13 (241 МБ) убрали из основного
списка; файл и прежний URL сохранены. Новые имена неизменяемые.

Linux — исходный paired архив с ручными зависимостями и отдельными VPN helpers,
не автономный установщик. Эта граница указана на странице и в инструкции.
Windows — unsigned publisher installer; физическая приёмка ещё отложена.
Подписанные автоматические каталоги и stable v0.2.9 не изменялись.

## Точные файлы

- `FamilyConnect-Test-0.1.18-beta25.apk` — 36395084 байт; SHA256 `8d350572bfca0d955f37858d2c957e379f04d93762a3a3355b21d673d8f1cb3b`.
- `FamilyConnect-Control-Linux-preview-11c53d18c3bc10a9.tar.gz` — 114644 байт; SHA256 `f0f877cb7a6933a950d3c53c100da41f231963912c9cfbc5ebee2ee326cbd037`.
- `FamilyConnect-Setup-0.2.9-preview-21b740a.exe` — 49928867 байт; SHA256 `5ce1d67781a4bede2d0f5c50cd7cfdf5ff407524e8406b8cc1e0abd38bfaea0f`.
- `FamilyConnect-Linux-preview-20260920.txt` — 3039 байт; SHA256 `1a1ac65b6b6c9a336373226cab69013f8e893d73734b983d6c32b60239780a1e`.

## Приёмка

Android: ранее принятые140 unit/4 native UI и lint0errors/18warnings, установленный
beta25 APK проверен. Пересборки и повторной подписи нет.
Windows: исходник21b740a, UI CI35501348376 и Windows installer job35501348219
passed; публикация отдельного immutable prerelease desktop-preview-20260920-21b740a
workflow35502270287 success. Скачанный installer сверён с receipt.json и CI manifest.
Linux: source d93611e, control CI35503217768 success, job106058546158 подтвердил
побайтно совпадающий public archive SHA256. Локальные24 layouts, Friends interaction
и закрытие встроенного экрана прошли. Рендер просмотрен; установлен bundle11c53d18c3bc10a9.
Подробности: [исправление навигации](2026-09-20-linux-invitation-navigation.ru.md).
Общий Client builds не объявляется успешным: Android setup имел отдельные отказы.

Rollout: проверка всех staged SHA/размеров; новые exact nginx locations;
nginx -t -c /etc/fc/nginx.conf passed, HUP только family-connect-product-https.
Inline script/style страницы побайтно сохранены, CSP не менялась.
Проверка не использует invite token и не создаёт приглашений.
Все три файла и Linux-инструкция скачаны целиком по публичному HTTPS; размеры и
SHA256 совпали. HTML совпала с локальной страницей, оба CSP hash проверены;
HEAD старой universal beta13 вернул200. Браузерный рендер страницы просмотрен.

## Откат

185.251.89.19:/opt/apps/family_connect/state-product-https/config:
nginx.conf.before-three-platforms-20260920,
nginx-final.conf.before-three-platforms-20260920,
invite.html.before-three-platforms-20260920.
Перед восстановлением учесть последующие изменения, проверить nginx -t с явным
/etc/fc/nginx.conf, затем HUP только family-connect-product-https.
Опубликованные файлы не заменять/не удалять. Клиентские данные/БД/ключи не менялись.
Откат установленного Linux — по отдельному отчёту навигации. Android откат кода
доставлять новым versionCode с прежней подписью, без удаления данных.

Остаётся: физическая Windows-приёмка, российская сеть, длительная устойчивость,
удобный самостоятельный Linux installer. Расширение парка серверов пока проект:
[добавление по нагрузке](../server-capacity-plan.ru.md); никакие VPS не заказаны.
