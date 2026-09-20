# План развития Family Connect

## Глобальный checkpoint — 2026-09-20

Текущий основной блок — завершение этапа4 (платформы, реальная приёмка и выпуск).
Linux Friends RU/NL × AWG3.1/TCP прошёл короткую проверку4/4; выявлен повторный
pkexec UX, исправление первым. Windows доступен, live ещё впереди. Российская сеть
недоступна. Этап5 (управляемый служебный канал) частично реализован; Friends через
HTTPS не закрывает Reticulum/native rollout. Для этапа6 оба gateway существуют,
но независимость control ingress и смена полностью недоступного endpoint ещё
не приняты. Этап7/коммерческий запуск не закрыт. Android beta19 VPN/чат — пилот;
desktop messenger/QR/карта и анимационная полировка ещё остаются. AWG2 не считаем
рабочим российским транспортом: ориентир AWG3.1/TCP REALITY.

[Текущий live checkpoint](releases/2026-09-20-desktop-live.ru.md).

## Действующий порядок — 2026-09-19

Android VPN и обмен сообщениями между телефонами подтверждены в пилоте.
Публичное скачивание — beta19; текущие смайлики оставлены, перерисовка отложена.
Пользователь перевёл работу к продуктовому оформлению GitHub. Приглашения для
друзей уже реализованы; прежние указания «APK пока не собирать» и «native экраны
впереди» ниже относятся к прошлым этапам.

Текущие задачи: обновление Linux и Windows по новому запросу владельца
([план](desktop-modernization.ru.md)); оформление публичной документации подготовлено
локально, публикация остаётся впереди; решение лицензии
с учётом намерения владельца зарабатывать на сервисе; оставшиеся проверки
мессенджера на других устройствах/offline/restart и VPN release gates.
Платная подписка и готовый коммерческий запуск пока не заявляются.

[Текущее состояние](STATUS.md) · [Рабочий план](PLAN.md).

## Утверждённый порядок выпуска — 2026-09-14

Пользователь: сначала выполнить весь план VPN-сервиса на Linux, Windows и Android.
Мессенджер и iPhone отложены до завершения этого плана; текущий код мессенджера
сохраняем, новых задач по нему и iOS сейчас не начинаем. Все результаты, ограничения,
версии и оставшиеся проверки документируем. Этот порядок имеет приоритет над
историческими разделами ниже, где следующим шагом названы chat/Store bridge или iOS.

[Единый список условий выпуска](PLAN.md#release-gates-three-platforms).

Текущий этап: Android Stage 5 journal/transaction source проверен, native runtime
и service binding ещё открыты. Затем Windows Stage 5, управляемый AWG3.1, Stage6,
эксплуатационная приёмка и согласованный выпуск. Актуальные checkpoint находятся в
[STATUS](STATUS.md), условия выпуска — в [PLAN](PLAN.md#release-gates-three-platforms).
Разделы со состоянием12.09 ниже сохранены как историческая детализация; второй VPS
уже подключён, полная приёмка Stage6 ещё не завершена.

Amsterdam186.246.45.246: native WG real-network pilot accepted13.09; Stage6 partly
started, independent control ingress/alternate transports still pending.
[Evidence](releases/2026-09-13-amsterdam-pilot.ru.md).

Состояние на 12.09.2026. Главная цель: приложение сохраняет или восстанавливает VPN,
а при полной недоступности старого сервера получает проверенные новые настройки
по независимому служебному каналу и подключается к другому серверу.

**Matched network follow-up:** Python HTTP1.1 and curl HTTP2 direct/TUN pairs
passed24/24 at fixed targets; prior timeouts did not reproduce. Cleanup passed,
no network/code adjustment; stability debt remains open. [Matched HTTPS result](releases/2026-09-12-matched-https.ru.md).

**GUI/control integration update:** shared Linux operation arbiter accepted locally,
402 Python/GTK recovery/24 layouts. Short installed TCP network tests resumed by user:
DNS3/3, HTTPS4/6, routing/cleanup passed; stability remains open.
[GUI coordination and short network checkpoint](releases/2026-09-12-control-gui-network.ru.md). No release or Stage6 acceptance.

**Актуальный checkpoint Stage5:** reference protocol/application core реализован;
381 Python tests, реальный локальный RNS commit/ACK и rollback/ACK. Native/background
rollout требует отдельной интеграции/приёмки. AWG3.1 migration остаётся TD-2; версия
явная, текущий verifier отказывает до apply. Stage6 не выполнен.
[Stage 5 checkpoint](releases/2026-09-12-reticulum-control.ru.md). Подробности предыдущей платформенной приёмки ниже.

**Следующая разработка: этап5 Reticulum; выпуск и приёмка устройств этапа4 остаются открытыми. Desktop0.2.9 опубликован, exact platform CI прошёл, catalog sequence8 подписан офлайн. На устройствах обновление ещё не применялось. TCP Setup0.1.0 опубликован с отдельной офлайн-подписью. Windows TCP-движок прошёл изолированную приёмку TUN/VLESS 12/12 и очистку. Подписанный REALITY-профиль и DPAPI-импорт через Windows broker прошли приёмку. Владение TCP-процессом и очистка прошли CI18/18. Сетевая сессия broker/SCM с маршрутами/DNS прошла ограниченную LocalSystem-приёмку24/24. Упаковка и TCP UI прошли platform CI (288 макетов, установка/удаление). Восстановление после падения Xray прошло CI (ограниченные повторы и отмена). Health-monitor прошёл scoped Windows CI (живой Xray, отказ целей, восстановление и отмена). Windows AWG worker/profile/DPAPI/broker/installer/UI прошли scoped CI (24/24 LocalSystem UDP,504 макета); Windows Auto WG→AWG→TCP принято в scoped CI (672 макета,7 policy-сценариев, живой AWG→TCP); Android WG/AWG/TCP/Auto принят в эмуляторе (24 REALITY HTTP/4 OS DNS/48 UDP/отмена/отзыв); далее этап5 Reticulum, full-routing acceptance до выпуска; Android updater отложен. Сетевые тайм-ауты остаются известным ограничением; нагрузочные испытания отложены пользователем.**
Предыдущая серия первого ноутбука120/120 — исторический результат, не подтверждение
устойчивости текущего второго устройства. Последний offload A/B/A неоднозначен из-за
сбоев прямого контрольного пути; исходные настройки адаптера восстановлены.
Это ещё не законченная система защиты от блокировки IP сервера.
Установленный Linux 0.2.7 и опубликованный desktop 0.2.8 не включают весь эксперимент.

| Этап | Состояние | Критерий завершения |
|---|---|---|
| 1. Базовый продукт и WG | Работает; сервер 0.2.1, регистрация/отзыв проверены | Существующие клиенты и peers сохраняются, подключение и выдача конфигураций работают |
| 2. AWG 2.0 и автоматическое восстановление | Проверено в Linux-пилоте, не во всех стабильных клиентах | WG-блокировка → AWG; восстановление уже установленной сессии. Измерено 44.05 с при открытом приложении |
| 3. TCP VLESS+REALITY | Функциональная приёмка Linux/review/integration выполнены; сетевая устойчивость открыта | Локализованы оставшиеся тайм-ауты (ещё открыто); исправленный helper проходит короткий host-тест, точную очистку и established AWG → TCP recovery |
| 4. Платформы и стабильный выпуск | **Desktop0.2.9 и TCP Setup0.1.0 опубликованы; Windows TCP engine + защищённый профиль проверены, lifecycle/session проверены, packaging/UI проверены; recovery/AWG проверены в scoped CI; автоматическое переключение принято в scoped CI; Android WG/AWG/TCP/Auto принят в эмуляторе; далее Reticulum** | Linux/Windows/Android: native интеграция, установка, переключение, отмена, восстановление; platform CI, UI/runtime, подписанный неизменяемый релиз |
| 5. Служебный канал Reticulum | Reference core: реальный локальный RNS + transactional apply/ACK/rollback, 381 tests; native/background rollout открыт | Подписанная конфигурация доставляется, проверяется, применяется с ACK/откатом, защищена от повторов; канал доступен при блокировке обычного API |
| 6. Независимые серверы и сквозной тест | Второго VPS пока нет | Полная недоступность старого endpoint → получение новой конфигурации → другой gateway; независимость служебного пути проверена реально |
| 7. Сервисные функции | После устойчивой доставки | Уведомления об обновлениях и подписке, затем платёжная интеграция; подпись/проверка событий и восстановление после офлайна |

Этапы 5 и 6 проектируются совместно: Reticulum через единственный недоступный узел
не решит задачу смены заблокированного сервера. Нужен доступный вход в служебную сеть
и альтернативный VPN gateway. Второй VPS подключается после получения адреса и доступа
от владельца; сейчас для локализации TCP-задержек покупка сервера не требуется.
Исключённый сервер 186.246.51.201 не используется.

## Ближайшие действия

1. Сетевые/нагрузочные испытания отложены пользователем; не возобновлять автоматически.
2. Интеграция setup и ревью client patch выполнены; desktop0.2.9 уже опубликован.
3. Client0.2.9 и подписанный TCP Setup0.1.0 опубликованы; первичный verifier/anchor получают доверенным каналом.
4. По подтверждённому порядку: Windows transport implementation завершена и принята в scoped CI; Android WG/AWG/TCP/Auto принят в API35 эмуляторе (24 REALITY HTTP, 4 OS DNS, 48 UDP, остановки, отмена, системный отзыв); далее этап5 Reticulum. Full-routing/device acceptance остаётся условием выпуска, отложенные тесты не возобновлять автоматически.
5. Сразу после интеграции Windows/Android — этап5 Reticulum: доставка/проверка/применение/ACK/откат. Google Play и Android updater не являются условием старта. Второй VPS нужен для этапа6, не для реализации обмена Reticulum.

TCP setup и signed component установлены на втором Ubuntu, независимая Debian VM прошла
установку. Дефект повторной авторизации исправлен в рабочем клиенте; TLS-тайм-ауты остаются.
Offload A/B/A выполнен, исходные настройки возвращены; вывод о причине не получен из-за
плохого прямого контроля. Полный итог: [checkpoint](releases/2026-09-11-session-checkpoint.ru.md).

Последняя диагностика первого: [paired capture](releases/2026-09-11-first-laptop-paired.ru.md).

Offload comparison: [итог и точное восстановление](releases/2026-09-11-first-laptop-offload.ru.md).

Isolated transport comparison: [результаты](releases/2026-09-11-first-laptop-isolated.ru.md).

Текущий приоритет и интеграция: [checkpoint](releases/2026-09-11-setup-integration.ru.md).

Платформенный CI и артефакты: [checkpoint](releases/2026-09-11-platform-ci.ru.md).

Выпуск0.2.9: [evidence](releases/2026-09-11-release-0.2.9.ru.md).

TCP Setup release: [evidence](releases/2026-09-11-tcp-setup-release.ru.md).

Windows TCP engine: [приёмка и границы](releases/2026-09-11-windows-tcp-engine.ru.md).

Windows TCP profile/broker: [приёмка](releases/2026-09-11-windows-tcp-profile.ru.md).

Windows TCP lifecycle: [результат и границы](releases/2026-09-11-windows-tcp-lifecycle.ru.md).

Windows TCP broker session: [полный итог](releases/2026-09-11-windows-tcp-session.ru.md) · [runbook](windows-tcp-session.ru.md).

Android TCP: [приёмка и границы](releases/2026-09-12-android-tcp.ru.md).

Android Auto: [приёмка](releases/2026-09-12-android-auto.ru.md). Следующий этап разработки5; отложенная приёмка устройств и выпуск этапа4 остаются открытыми.
