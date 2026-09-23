# Windows0.2.13 — отдельный канал обновления

Windows0.2.13 опубликован в GitHub/HTTPS; отдельный подписанный каталог включён. Пользователь обнаружил, что кнопка обновления
не видит0.2.12. Проверен публичный updates/pilot.json: общий schema1, версия0.2.9, sequence8.
Windows0.2.10–0.2.12 новее каталога и показывают «последняя версия»; их updater требует
общий номер Windows/Linux и фиксированные ссылки v{version}. Ручные preview в него не попадали.

Пользователь выбрал отдельный канал Windows и согласился на одну переходную установку вручную.
0.2.13 читает updates/windows.json: schema2, platform=windows, один artifact, новый домен
подписи family-connect/app-update/v2 и фиксированная ссылка windows-v{version}.
Публичный anchor прежний, private key остаётся offline. Старый pilot.json и Linux не меняются.
Сохраняются lease90 дней, монотонный sequence, digest, проверка размера/SHA256 перед UAC.
Состояние sequence8 мигрирует на9 без сброса защиты от отката.

Проверки: Python/C# fixture, offer более новой версии, отсутствие offer равной/старой,
миграция floor8→9;19 отказов для неверной подписи, платформы, домена, срока, URL, полей,
размера и rollback. Offline signer --platform windows работает без Linux artifact;
пять Python-тестов сохраняют совместимость общего schema1 signer.

Native Windows CI и публикация установщика завершены. Каталог подписан offline (sequence9),
страница и RU/EN документация обновлены. Публичная проверка Updates.Check фиксируется ниже.
До ручной установки0.2.13 старые приложения продолжат смотреть старый канал.


## Артефакт и проверки

Source `c2984363222c1547917337bb5b66ea12bb992522`. [GitHub](https://github.com/Joker20380/family_connect/releases/tag/windows-v0.2.13).
[Установщик](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.13-pilot-unsigned.exe), 49934846 bytes.
SHA256 `88f4274cd2aff07a73a5366f09b2f37301ccd442a67574a30eeaf7c587d4ae5b`. Установка поверх прежней версии сохраняет ключи/доступ.

- [Windows UI/startup](https://github.com/Joker20380/family_connect/actions/runs/35921509381) — success.
- [Windows installer/broker/URI job](https://github.com/Joker20380/family_connect/actions/runs/35921509278) — success.
- [AWG](https://github.com/Joker20380/family_connect/actions/runs/35921509421) — success.
- [TCP](https://github.com/Joker20380/family_connect/actions/runs/35921509348) — success.
- [Ordinary user](https://github.com/Joker20380/family_connect/actions/runs/35921509214) — success.
- [Phase0](https://github.com/Joker20380/family_connect/actions/runs/35921509244) — success.
- [Windows control](https://github.com/Joker20380/family_connect/actions/runs/35921509334) — success.

UI снимки просмотрены. Python signer:5 тестов; C# проверяет Python fixture, миграцию floor,
предложение версии и19 отказов. GitHub/HTTPS EXE скачаны и совпали с CI; ZIP digest также проверен.
Страница SHA256 `37cdb194b2ae6c9e3753f262ab4bba24afbdbf6ee6458dd82d75355c1ff76368`, CSP проверен. Android discovery сохранён.
Новый подписанный каталог: schema2, Windows0.2.13, sequence9, issued_at `1790199329`,
expires_at `1797975329`. Прежний `updates/pilot.json` не менялся.

## Откат и приёмка

Сервер `185.251.89.19:/opt/apps/family_connect/state-product-https/config`.
Backup `rollbacks/windows0213-c298436`: прежние invite.html/nginx.conf/nginx-final.conf.
Для возврата ссылок восстановить файлы, проверить nginx-t и отправить HUP только HTTPS контейнеру.
Каталог нельзя откатывать на меньший sequence: при ошибке публиковать корректирующий каталог
с большим sequence; установленные клиенты и данные сохранять. Выпущенные EXE не заменять.
Windows publisher signing пока отсутствует; Ed25519 каталога — отдельная проверка.

Пользователь один раз вручную устанавливает0.2.13. В ней сообщение «последняя версия Windows:0.2.13»
соответствует новому каналу. Следующий Windows-выпуск должен быть предложен встроенной кнопкой.
Проверка плавности интерфейса на пользовательском ПК остаётся открытой.

Publisher [35923408333](https://github.com/Joker20380/family_connect/actions/runs/35923408333) — success.
