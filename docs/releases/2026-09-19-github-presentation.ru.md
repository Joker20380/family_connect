# Продуктовое оформление GitHub — 2026-09-19

## Аудит

До изменений README называл проект изолированной лабораторией, README.en/ru отрицали
наличие Android-приложения, clients.en/ru описывали старые Tk/Windows-обёртки.
Главная и docs/README были инженерными индексами. Новые Android beta и приглашения
не имели понятного входа для внешнего посетителя. STATUS содержит последовательные
исторические записи: актуальным считался верхний проверенный checkpoint.

GitHub API: public/main, About `vpn_service`, topics пусты, лицензия не определена.
Последний desktop prerelease v0.2.9: Linux tar.gz, Windows pilot-unsigned EXE,
release.json, SHA256SUMS, Windows-preview.png. TCP helpers опубликованы отдельно.
Последний полученный Actions run phase0 на 3f6f662d — success; Client builds на
f4f320fc — success. Эти результаты не подтверждают текущие незакоммиченные изменения.
В clients.yml release job зависит от Android/Linux/Windows и выпускает desktop assets;
текущая Android Friends APK туда не включается. Семантика CI не менялась.

В корне отсутствовали LICENSE, SECURITY, CONTRIBUTING, CHANGELOG, issue/PR templates,
CODE_OF_CONDUCT; Dependabot и отдельный Markdown checker не найдены. Вместо формального
CHANGELOG создана карта существующих releases, CODE_OF_CONDUCT без необходимости
не добавлен. Dependabot и серверные настройки secret scanning не включались автоматически.
Приватный канал уязвимостей и SLA не выдумывались. .gitignore исключает runtime state,
но это не доказательство сканирования секретов или чистоты всей истории.

Найдены старые desktop screenshots и актуальный native render Android beta19.
На главной использован только проверенный dashboard-native.png без изменения пикселей;
нет токенов, личных сообщений или приватных идентификаторов. Это View.draw при
инструментальном тестировании, не OS screenshot и не синтетический дизайн.

## Изменено

- README.md — английская продуктовая страница; README.ru.md — смысловой эквивалент.
- README.en.md — совместимая ссылка вместо третьей расходящейся копии.
- docs/getting-started.en/ru.md — приглашение, APK, обновление, ограничения и помощь.
- docs/clients.en/ru.md — актуальные платформы; прежние версии сохранены в clients-legacy.en/ru.md.
- docs/README.md — Users / Operators / Developers / Project / Engineering history;
  прежний индекс сохранён в docs/history-index.md.
- docs/architecture.md — разделение продуктового пути и QUIC-эксперимента;
  architecture.en/ru.md помечены как исторический lab design.
- SECURITY.md, docs/privacy.md, docs/licensing.md — фактические границы и пробелы доверия.
- CONTRIBUTING.md, .github/pull_request_template.md, .github/ISSUE_TEMPLATE/bug_report.md.
- docs/releases.md — существующая модель выпуска и рекомендации без изменения pipeline.
- docs/assets/android-beta19-home.png и README.md — актуальный кадр и provenance.
- scripts/check_public_docs.py — локальные ссылки/anchors/images публичных входных страниц.
- STATUS, PLAN, ROADMAP и этот отчёт — актуализация приоритетов и незавершённых пунктов.

Порядок главной: название/ценность → CTA → платформы → экран/семейная схема →
причины выбора → история автора → как работает → статус → установка → безопасность →
архитектура → разработка → карта документации → участие → лицензия.

## Лицензия и коммерческая цель

Владелец уточнил намерение зарабатывать на сервисе. MIT обсуждалась, но НЕ одобрена.
Лицензия не добавлена. В README нет обещания бесплатного доступа к серверам;
скачивание APK отделено от серверной авторизации. Биллинг не объявляется реализованным.
Из-за отсутствия лицензии не заявлена уже лицензированная open-source-дистрибуция.
У classic GIF provenance явно не установлены права распространения; это отдельный gap.

## GitHub About

gh CLI отсутствует; API использован для публичного read-only аудита. Metadata не менялась.
Для завершения About владелец может выполнить после `gh auth login`:

```sh
gh repo edit Joker20380/family_connect --description 'Private networking for families and personal devices.' --add-topic privacy --add-topic networking --add-topic vpn --add-topic wireguard --add-topic family --add-topic android --add-topic windows --add-topic linux
```

Тема open-source намеренно отложена до выбора лицензии. Права записи и private
vulnerability reporting не подтверждены; приватность репозитория не менялась.

## Проверки и публикация документации

Финальная проверка проводится в отдельном worktree от публичного main `3f6f662`,
ветка `docs/product-presentation-20260919`. Включены только документация, одно
проверенное изображение, шаблоны и Markdown link checker. Runtime-код, зависимости,
CI workflows, приложения и серверы не включены. Публикация не является release.

Все изменённые Markdown-файлы проверены: локальные пути, anchors и изображения
без ошибок; 17 внешних URL вернули HTTP200. Четыре актуальных Mermaid-диаграммы
повторно отрисованы Chromium с Mermaid10.9.3 (`PASS 4 diagrams`). Изображение
просмотрено: это текущий native render без кодов или персональных данных.
Первый Chromium запуск не прочитал /tmp через Snap; запуск из игнорируемого
каталога проекта прошёл. `git diff --check` passed. Runtime-тесты не повторялись,
поскольку публикуемый diff не меняет runtime или существующие CI semantics.

Android остаётся 0.1.18-beta19/code19, 36 390 988 байт, SHA256
`5ebe38168f084d3e19bb740722ec7c3a7ceb5e9ed63508efc3e3ff3f5e0bf3a4`.
Desktop остаётся v0.2.9. APK, серверы, tags, assets и update catalogs не менялись.
Последний desktop CI на отдельном429eb77: Windows/Linux Client builds прошли,
Android SDK setup failed; общий run не зелёный, release skipped. Это не тесты
данного documentation-only изменения и не новая сборка для пользователя.

README EN/RU и CONTRIBUTING явно сообщают, что main пока отстаёт от распространяемой
Android APK. Не заявлена воспроизводимость beta19 из опубликованного main.
Публикация соответствующего source checkpoint выделена в PLAN отдельно от оформления.
Прежние публичные STATUS/PLAN и инженерный индекс сохранены как исторические документы.
Накопленная локальная работа приложения сохранена, в этот commit не включается.

Откат оформления: отдельный `git revert` документационного коммита с проверкой diff
и последующим push. Не откатывать приложения, ключи, DB или каталоги ради README.

## Что остаётся владельцу и следующему этапу

- About/topics: команда выше; `gh` отсутствует и авторизованный GitHub API недоступен.
  SSH-доступ для git push не даёт API-доступа к metadata. Описание `vpn_service`
  подтверждено публичным API перед публикацией; оно не объявляется исправленным.
- Выбор лицензии/коммерческой модели и права на сторонние assets остаются открыты.
- Private vulnerability reporting/contact, retention policy и Windows publisher signing
  не выдуманы и не объявлены настроенными.
- Исходники соответствующей Android beta, desktop feature parity и приёмка
  мессенджера offline/restart/другие устройства — отдельные инженерные задачи.
- Dependabot, CODE_OF_CONDUCT и новый release pipeline не добавлены ради количества.
  Git ignore не объявляется полноценным secret scanning.

## Следующий запрос пользователя

Обновить также Linux и Windows до актуального состояния. Опубликованные desktop
v0.2.9 признаны более ранними по возможностям относительно Android beta19. Начат
аудит интеграции актуальной активации, приглашений, VPN и мессенджера; выпуск ещё
не выполнен. Продуктовые README показывают текущую desktop-дистрибуцию v0.2.9 без обещания Android feature parity.

## Файлы публикации

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/pull_request_template.md`
- `CONTRIBUTING.md`
- `README.en.md`
- `README.md`
- `README.ru.md`
- `SECURITY.md`
- `docs/PLAN.before-2026-09-19.md`
- `docs/PLAN.md`
- `docs/README.md`
- `docs/STATUS.before-2026-09-19.md`
- `docs/STATUS.md`
- `docs/architecture.en.md`
- `docs/architecture.md`
- `docs/architecture.ru.md`
- `docs/assets/README.md`
- `docs/assets/android-beta19-home.png`
- `docs/clients-legacy.en.md`
- `docs/clients-legacy.ru.md`
- `docs/clients.en.md`
- `docs/clients.ru.md`
- `docs/desktop-modernization.ru.md`
- `docs/getting-started.en.md`
- `docs/getting-started.ru.md`
- `docs/history-index.md`
- `docs/licensing.md`
- `docs/privacy.md`
- `docs/releases.md`
- `docs/releases/2026-09-19-android-beta16.ru.md`
- `docs/releases/2026-09-19-android-beta18.ru.md`
- `docs/releases/2026-09-19-android-beta19.ru.md`
- `docs/releases/2026-09-19-android-chat-ui.ru.md`
- `docs/releases/2026-09-19-beta19-download.ru.md`
- `docs/releases/2026-09-19-desktop-friends-foundation.ru.md`
- `docs/releases/2026-09-19-desktop-identity-storage.ru.md`
- `docs/releases/2026-09-19-github-presentation.ru.md`
- `docs/testing/friends-quickstart.ru.md`
- `scripts/check_public_docs.py`
