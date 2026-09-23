> Historical design/plan. Current delivery status: [STATUS](STATUS.md); active work: [PLAN](PLAN.md). Goals below are not guarantees of the current pilot.

# Публичный GitHub Family Connect: задание после мессенджера

Обязательный следующий этап, поручен пользователем19.09.2026. Начинать после
реализации и приёмки минимального мессенджера, не вместо него. Пользователь
сообщил, что GitHub уже публичный. Репозиторий:
https://github.com/Joker20380/family_connect.

## Цель и критерий приёмки

Сначала человек и продукт, затем технологии и архитектура. За20–30 секунд новый
посетитель должен понять, что это open-source private networking application/platform
для семей и личных устройств, зачем она нужна, историю возникновения, доступные
платформы, как попробовать и где изучить код, архитектуру, privacy и security.
Главный README — лицо продукта, глубокая инженерная документация сохраняется.

## 1. Аудит перед изменениями

Прочитать README.md/en/ru, актуальные STATUS/PLAN/roadmap, architecture/security
docs, clients, установку, Actions, version/release/signing infrastructure, assets
и screenshots. Проверить реальные GitHub Releases и About. При противоречиях
актуальный STATUS важнее старых README; проверить, что действительно выпущено,
а не только собрано в CI. Сначала кратко сообщить найденные проблемы.

Не выдумывать функции, платформы, downloads, security policy или production
readiness. Статусы beta/pilot/development должны оставаться явными. К моменту
выполнения повторно сверить готовность VPN и мессенджера, не копировать нынешние
статусы как вечные. Аудит публичной части пока не выполнен этим документом.

## 2. Landing page и история

README.md — международная английская landing page. Сверху ссылка на README.ru.md.
Возможный заголовок: **Private connectivity for families and devices across borders.**
Описание —2–3 предложения, далее реальные CTA: Download/Getting Started/How it
works/Security/Architecture. При отсутствии пригодных downloads использовать
честный Try the current build или Build & Install; никаких мёртвых кнопок.

Подлинная история, предоставленная автором: он живёт в Европе, близкие — в России.
Проект появился для своей семьи: хотелось настроить соединение один раз, чтобы
близким не приходилось разбираться в конфигурациях VPN, серверах и протоколах.
Из личной потребности вырос проект private networking для людей, семей и устройств
в разных странах. Короткое вступление и отдельный спокойный блок Why I built it.
Не превращать историю в политику или идентичность «VPN для России».

Не использовать bypass censorship, unblock Russia, evade Roskomnadzor,
access banned websites, defeat government blocking, лозунги о скорости,
100% secure или impossible to track. Тон спокойный, точный, минималистичный,
без корпоративной риторики и неподтверждённых обещаний.

Порядок главного README:
1. Logo/name, one-line value proposition, краткое описание, CTA.
2. Platforms: компактная таблица реальной готовности Windows/Linux/Android;
   macOS/iOS только с подтверждённым статусом или планом.
3. Screenshot/простая визуальная схема, понятная обычному человеку.
4. Why Family Connect: простота для семьи как цель либо доказанная возможность,
   открытый код, личные/семейные устройства, несколько транспортов с честными
   ограничениями automatic selection.
5. Origin story; How it works без требования знать provisioning/WG/TUN/proofs.
6. Project status: active development, experimental features/platforms;
   инженерные оговорки вроде isolated research laboratory убрать с первого экрана,
   но реальную стадию разработки не скрывать.
7. Installation / Getting started.
8. Security & privacy.
9. Architecture: короткая реальная схема и ссылки на подробности.
10. Development; Documentation; Contributing; License.

Естественно употреблять open-source private network, secure networking, family
devices, Windows, Linux, Android, encrypted connection, privacy, а WireGuard —
в техническом слое. Не делать keyword stuffing. Название везде Family Connect.

## 3. Визуальная часть

Первая Mermaid-диаграмма — семья и её устройства либо столь же простое объяснение;
не выдавать концептуальную схему за готовую функцию family management. Ниже
отдельная архитектурная диаграмма строго по реализованным компонентам.

Проверить существующие изображения. Показать максимум2–4 актуальных настоящих
скриншота (главный экран, connection, devices, settings/status — только если есть).
Использовать docs/assets/ либо существующую структуру. Не генерировать фиктивный
UI, не брать устаревшие скриншоты, не оставлять пустые broken images. Если кадров
нет, подготовить место/инструкцию для будущего добавления без неработающих картинок.

## 4. Языки и карта документации

README.ru.md — естественный смысловой эквивалент английского. README.en.md либо
синхронизировать с главным, либо превратить в совместимую ссылку на канонический
README.md. Реализовать простой механизм поддержки двух языков, исключающий
три расходящиеся самостоятельные версии; сохранить существующие ссылки.

docs/README.md упорядочить по аудиториям:
- Users: installation, getting started, troubleshooting.
- Operators: deployment, provisioning, monitoring.
- Developers: architecture, protocols, device identity, transports, testing.
- Project: status, roadmap, releases.

Старые инженерные документы не удалять. Исторические отчёты отличать от текущих
инструкций. Главный README ссылается на карту, не копирует огромный индекс.

## 5. Доверие и repository hygiene

Проверить LICENSE, SECURITY.md, privacy docs, threat model, release signing,
build verification, vulnerability reporting, CONTRIBUTING.md, CHANGELOG.md,
issue/PR templates, .github/, Dependabot, secret-scanning-compatible configuration,
release workflow, устаревшие инструкции. CODE_OF_CONDUCT.md — только при реальной
необходимости. Не создавать документы ради количества, не придумывать лицензию,
контакт для уязвимостей или политику privacy. Недостающие документы создавать лишь
на основе имеющейся подтверждённой информации; отмечать оставшиеся пробелы.

Security-блок README должен дать понятные ссылки без абсолютных обещаний.
Публичность исходников не заменяет аудит безопасности.

## 6. About и Releases

Если доступ и инструменты позволяют, изменить GitHub description, например:
`Open-source private networking for families and personal devices.`
Topics только по реальному проекту: privacy, networking, vpn, wireguard,
secure-network, family, android, windows, linux, open-source. Если изменить
metadata невозможно — дать владельцу точную команду/инструкцию. Публичный доступ
сам по себе не означает наличие права записи; не менять visibility.

Изучить существующую release model и путь GitHub → Releases → платформа → Install.
Проверить, пригодны ли CI artifacts для release assets; не менять release pipeline
автоматически. Для требующего отдельного решения автоматического выпуска —
рекомендации. Сохранять offline signing, неизменяемые версии и platform gates.

## 7. Границы и финальная проверка

Это documentation/product presentation, не рефакторинг core. Не менять протоколы,
криптографию, provisioning, transports, server architecture или CI semantics.
Никакой публикации APK только ради улучшения README.

Проверить Markdown links (включая anchors), rendering Mermaid, image links,
актуальные статусы платформ, существующие documentation/lint checks; не ломать
тесты. Представить список изменённых файлов и итоговую структуру README.

Финальный отчёт должен содержать Changed, Why, User-facing improvements,
Developer-facing improvements, Remaining gaps: реальные пробелы public launch
(screenshots, installers, signed releases и др.), не обещания вместо результата.

Аудит и локальное оформление выполнены19.09.2026: [отчёт](releases/2026-09-19-github-presentation.ru.md).
README EN/RU и карта документации подготовлены; About/публикация пока не выполнены.
Владелец уточнил коммерческую цель и затем поручил актуализировать Linux/Windows:
[действующий desktop-план](desktop-modernization.ru.md). Лицензия не выбрана.
