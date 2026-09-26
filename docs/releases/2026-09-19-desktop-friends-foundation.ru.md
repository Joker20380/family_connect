# Desktop Friends: первый протокольный блок — 2026-09-19

Пользователь поручил актуализировать Linux и Windows; компьютер Windows для
пользовательской приёмки доступен. [План и разница платформ](../desktop-modernization.ru.md).

## Изменения

`provisioning/friends.py` — desktop-клиент существующего Friends API:
активация, referral URL и регистрация отдельного chat public key. Использует
предоставленную device identity, не создаёт ключи, не применяет VPN-профили.
Проверяет поля/TTL/привязку ответа, размер/JSON, отказ перенаправлений, очищенные
коды ошибок. На сервере используются прежние challenge consumption и entitlement.

Windows Core/ControlIdentity.cs — совместимая с Python/Android подпись enrollment,
раздельная RNS identity и прежний WG-ключ при создании, клонирование/очистка материала.
Это класс в памяти, НЕ готовая DPAPI persistence. Core/FriendsAccessClient.cs —
bounded HTTPS activation/referral, без redirects; отдельный 12-секундный deadline
включает чтение тела. Нет новых broker actions, UI, подписанного каталога или VPN apply.

## Проверки

- Новый Python клиент: 25 тестов, включая disposable настоящий Access/Referrals/ChatAccess,
  повторы, revoked/неактивное устройство, плохой TTL/audience, JSON/размер/redirect и chat node.
- Совместно с referral/chat regression: 40 passed.
- Полный Python suite: **537 passed, 2 upstream deprecation warnings**, 15.05s.
  Первый sandbox-запуск имел отказы локальных сокетов/зависание TestClient и был
  завершён; штатный outside-sandbox повтор passed. Lockfiles не менялись.
- .NET10.0.401/Linux: весь существующий Tests executable passed, включая 30 configurations,
  15 ACK fixtures и 31 structural check. Новые Windows проверки: точное совпадение
  proof с Python fixture, сохранение WG, restore/clone/dispose, activation/referral
  и семь отказов ответа. Это не Windows UI/DPAPI/runtime acceptance.
- `git diff --check` passed. Версии APK/desktop не повышались, упаковка не менялась.

## Git и CI

Отдельный worktree `/tmp/fc-desktop-friends-ci`, ветка `desktop/friends-access-20260919`,
коммит `0595f884` (сокращённый). В GitHub отправлены только семь Windows protocol/test
файлов, включая явно тестовый disposable fixture. Python-интеграция и документация
остаются в основном незакоммиченном рабочем дереве; чужие изменения сохранены.

Windows control CI: [run35468900333](https://github.com/Joker20380/family_connect/actions/runs/35468900333),
**completed/success** на 0595f884. Остальные запущенные scoped workflows:
Client builds35468900315, Linux control preview35468900324, Windows TCP35468900392,
phase035468900358. Прочие workflows на момент первого опроса были running; их результаты не
используются как доказательство готовности нового desktop release.
Это branch CI без release-тега/Release-коммита в main; публикация не запускалась.

## Выпуск и следующие шаги

Публичный desktop остаётся v0.2.9. Публичный Android — 0.1.18-beta19/code19,
SHA2565ebe38168f084d3e19bb740722ec7c3a7ceb5e9ed63508efc3e3ff3f5e0bf3a4.
Установки, серверы, device state и offline signing не менялись. Откат этого блока
до интеграции не требует действий пользователя; branch commit можно отдельно revert,
не затрагивая main. Новые бинарные версии выпускать после platform gates, не
перезаписывать v0.2.9. Существующие ключи/история/floors сохраняются.

Остаются: Windows DPAPI identity/journal/broker integration, Linux identity owner,
подписанные Friends profiles/актуальные native transports, полноценные UI и messenger,
Windows packaging, межплатформенная переписка и пользовательская приёмка/обновление.
Текущий результат — foundation, а не готовые актуальные Linux/Windows приложения.
