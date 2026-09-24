# Этап 5.1: аудит и начало реестра серверов — 24.09.2026

Пользователь начал этап5 и добавил требование расширяемого парка серверов,
распределения нагрузки и управления IP. Аудит5.1 завершён в границах ниже;
в5.2 начата локальная основа реестра и планировщика. Этап5 целиком не завершён.

## Матрица текущего кода

| Область | Подтверждено исходниками/проверками | Осталось |
| --- | --- | --- |
| Python protocol | ConfigVerifier, encrypted schema2, journal/floor, rollback, ACK, immutable vectors | AWG3.1 managed, связка Friends и fleet |
| Relay | ControlRelay: binding, challenge/proof, готовые ciphertext, ACK dedup; RNS carrier | Fleet publication/revoke, новый bootstrap rollout и независимость в failure test |
| Linux | runtime once/recover, BackendApplication, общий arbiter и root-pinned route lease | Связать Friends identity/owner, автоматический lifecycle, текущая native приёмка |
| Android | Keystore journal, application/recovery, ConnectionService sync, non-VPN socket | Friends/managed identities раздельны; интеграция без смены ключей; AWG3.1 managed |
| Windows | Общий verifier/identity и Friends per-SID storage | Нет managed broker transaction/journal/outbox/carrier; Wire16KiB не подходит для envelope64KiB |
| Масштабирование | Новый control/fleet.py: строгий инвентарь, revision checks, pure admission ranking | Persistent leases/IPAM, authenticated collectors, reconciliation, signed issuance, dynamic clients |

Проверены `provisioning/{configuration,transaction,relay,reticulum,runtime,application}.py`,
`control/product/gateways.py`, Friends verifier/owner/stores, Android Control*/FriendsIdentityVault,
Windows Broker/Wire/Core/ControlProfiles и существующие runbooks. Локальный checkout
содержит многочисленные прежние незакоммиченные изменения; они сохранены. HEAD3f6f662
не является точной идентификацией всего проверенного дерева.

Старые архитектурные документы отражают checkpoint сентября12–14, а не весь текущий
код. Важные расхождения: Android уже имеет carrier/transaction; managed AWG3.1
по-прежнему отвергается; Friends catalog жёстко ограничен ru/nl и двумя gateways.
Обычная работа Friends не доказывает managed enrollment или независимость от API.

## Сервер и bootstrap

Read-only SSH: `family-connect-reticulum.service` в Амстердаме active/running;
TCP4242 слушает; ExecStart запускает paired runner control serve с отдельными
relay/identity/RNS state под `/opt/apps/family_connect/reticulum`.
`run_control_preview.py verify` успешно проверил установленный manifest, bundle:
`66152538ee2a4f3ec4ac76cb2a0e09936bcc0785fc5afa308b692c3cd472acf5`.
Это checksum целостности пакета, не новая подпись доверия и не доказательство
совпадения всей серверной версии с локальным checkout.

Android assets содержат bootstrap186.246.45.246:4242 с public Reticulum identity.
Выбран этот существующий ingress для5.2; второй VPS не покупался. В этой работе
не выполнялся новый live fetch конкретного production-устройства и не блокировались
API/VPN. Связка actual provider pin и native клиентов входит в следующую приёмку.

## Реализовано в этой работе

- `control/fleet.py`: IDs вместо страны как уникального ключа; endpoints/capabilities,
  lifecycle, непересекающиеся пулы, лимиты, failure domains и bootstrap ingress.
- Безопасная проверка обновления revision, сохранение ID/pool и overlap ingress.
- Планирование новых назначений по свежим trusted observations, country/transport/
  address family, порогам и весам; сохранение здорового текущего узла при draining.
- `scripts/check_fleet.py`: локальная проверка JSON и перехода от предыдущей revision.
- [Контракт и сценарии S5/F](../stage5-fleet-contract.ru.md), включая регистрацию
  нового IP, адресные leases, границу offline signing и отсутствие пересборки клиентов.

Это библиотека/валидатор с тестами, **не включённый production-балансировщик**.
Никакие существующие peers, IP, назначения клиентов, серверные службы или DB не менялись.

## Проверки

| Проверка | Результат |
| --- | --- |
| Новый tests/test_fleet.py | 49 passed |
| Python control channel/vectors/route/Android identity/RNS/register relay | 118 passed в песочнице; 3 socket tests запрещены песочницей, затем все3 passed вне её; всего121 успешная проверка |
| Android control-tests Gradle offline --rerun-tasks | 108 tests, 0 failures/errors/skips; общие30 config/15 ACK vectors также проверены |
| .NET Tests Release --no-restore, Linux host | Exit0;30 config/15 ACK vectors и31 дополнительные отказы, другие существующие проверки passed; Windows DPAPI tests skipped по платформе |
| Установленный Reticulum bundle | Manifest verify passed; сервис не перезапускался |

.NET вывел NU1900 о недоступности NuGet vulnerability index; компиляция и тесты
завершились успешно с локальными зависимостями. Новый dependency audit этим не заявлен.
Java/.NET проверки протокола не заменяют Android device и native Windows broker tests.

## Следующие работы и оценка

5.2: durable fleet store и атомарные leases/IPAM → идемпотентный gateway reconciliation
→ привязка Friends public identities и ciphertext publication на независимый relay.
5.3: managed AWG3.1, dynamic gateway IDs/endpoints, общий corpus новой семантики.
5.4/5.5: владельцы состояния и применение Android/Linux/Windows, migration tests.
5.6: bounded failures, третий gateway, drain/IP-change, принятые сборки и выпуск.

Прежние9–15 рабочих дней относились к служебному каналу без полноценного fleet.
С добавленной работой предварительный ориентир14–22 рабочих дня сосредоточенной
разработки, без календарного ожидания CI/устройств. Уточнить после leases/reconciliation;
это оценка, не обещание фонового выполнения. Главные риски: live Friends migration,
Windows ownership и пересечение новой выдачи со старым peer/address учётом.

## Версии и откат

Версии остаются Android0.1.18-beta50/code50, Linux0.2.10 preview,
Windows0.2.13. Новые клиентские сборки не создавались и не публиковались.
Существующие release/rollback paths неизменны. Новая fleet-библиотека пока нигде
не подключена: отказ от неё не требует изменения серверов или возврата старой DB.
При будущем rollout откат отключает новые назначения, сохраняя keys, leases,
journals и floors; возврат старого состояния базы не является допустимым rollback.

## Продолжение24.09

После этого аудита реализован локальный durable leases/IPAM слой.
[Следующий отчёт:112 tests passed, ограничения и дальнейшая интеграция](2026-09-24-fleet-leases.ru.md).
Исходная матрица выше сохраняет состояние на момент аудита.
