# Прямая загрузка Friends beta13 — 2026-09-19

По запросу пользователя подготовлена публикация уже проверенной APK для установки
на других телефонах. Новая сборка, версия, GitHub release и подписанный каталог
не создаются. [Проверки beta13](2026-09-19-android-beta13.ru.md): 136 unit,
2 native UI, lint0errors/14warnings; пользователь подтвердил UI/маршрут и VPN
на своём телефоне. Полная VPN-матрица и обмен на двух телефонах ещё не приняты.

Артефакт: FamilyConnect-Test-0.1.12-beta13.apk, versionCode13, Android8.0+,
240501071 bytes. SHA256 `b6144bd3e131a2f43d628f992f3df3d56990127ae192d4e5b65132f389aaea38`.
Постоянный beta-v1 сертификат сохранён, приватные ключи не передаются.

## Развёртывание

Хост `185.251.89.19`, каталог `/opt/apps/family_connect/state-product-https/config`.
APK загружается во временный файл, проверяется SHA256, затем переносится в
`downloads/FamilyConnect-Test-0.1.12-beta13.apk`. Файл с этим именем неизменяем:
существующий допускается только при совпадении SHA256.
В nginx.conf и nginx-final.conf добавляется только точный download location,
GET/HEAD, MIME application/vnd.android.package-archive, Content-Disposition attachment,
immutable cache и nosniff. Доступ к соседним файлам не открывается.

В invite.html заменена старая заметка о подготовке APK на ссылку скачивания и
инструкцию установки. Inline JS/CSS не менялись, существующие CSP hashes проверены.
Claim не вызывается, токены/коды не используются. Nginx проверяется через `nginx -t`,
затем получает HUP. VPN, DB и службы provisioning не перезапускаются.

## Проверки публикации

Публикация завершена: nginx -t passed, HUP выполнен. APK полностью скачана
по HTTPS, SHA256 совпал с локальным и установленным артефактом. Публичная
страница приглашения проверена.

Ссылка: https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.12-beta13.apk

После публикации пользователь попросил уменьшить APK; компактная ARM64-сборка
готовится отдельно. Универсальная beta13 сохраняется неизменной.

## Rollback

В том же каталоге сохранены `nginx.conf.before-beta13-download`,
`nginx-final.conf.before-beta13-download`, `invite.html.before-beta13-download`.
Для немедленного отката этой операции восстановить эти три файла, выполнить
`docker exec family-connect-product-https nginx -t -c /etc/fc/nginx.conf`, затем
`docker kill --signal=HUP family-connect-product-https`.
Если конфигурация позднее менялась, сначала сравнить изменения и убрать только
download location/ссылку. APK сохраняется неизменной; обновление приложения —
новой версией с code>13, без удаления данных.
