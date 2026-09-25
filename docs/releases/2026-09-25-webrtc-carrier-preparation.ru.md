# 25.09.2026 — подготовка Whitelisted WebRTC Carrier

Пользователь ограничил текущую итерацию обновлением документации и подготовкой
к реализации модуля. Код carrier/path manager, builds и live/device tests не
выполнялись. Это продолжение существующего Home Gateway checkpoint `3bddff0`.

## Delta

Прежний Home Gateway с Reticulum control/selectable data path + сменный WebRTC
underlay = ReticulumOverlay → UnderlayPathManager → direct IPv6/IPv4 либо WebRTC
provider → Windows. Reticulum сохраняет overlay identity/Link encryption/routing;
WebRTC переносит opaque RNS frames. IP-over-RNS-over-WebRTC — отдельная тестовая
ветка после binary/RNS gates. Существующая свобода другого data transport сохранена.

[Дизайн](../reticulum/HOME_GATEWAY_DESIGN.md) расширен на месте; второй конкурирующей
архитектуры не создано. В имеющемся коде есть provisioning ReticulumAdapter и
Android RNS/TCP interface, но нет Home Gateway/UnderlayPathManager/WebRTC provider.
Они должны расширить существующий runtime через RNS Interface, не заменить его.

## Подготовленные решения

- Предпочтительный первый PoC — изолированный Go/Pion process с private stdio IPC,
  ограниченными binary frames и независимым lifecycle; без TUN/SOCKS/HTTP proxy.
- WB Stream / VP8 выбран первым кандидатом по разделимому guest/token/LiveKit flow.
  Guest join не подтверждает guest create: текущий whitelist creator требует cookie
  bearer, olcrtc присоединяется к существующей room. Временная ручная room допустима
  только через session API. Anonymous creation и доступность в белых списках не доказаны.
- Capabilities DC/VP8/TCP fallback/TURN — явные, допускают unknown. Provider API
  failure изолируется, verified config выключает provider без нового build, с
  документированным пределом offline expiry. Все новые flags OFF по умолчанию.
- Семейная авторизация/RNS crypto не заменяются room identity или WebRTC DTLS.
  RNS announces/public metadata не объявлены зашифрованными. Зафиксированы защита
  Android signaling/ICE/media sockets и проблема initial rendezvous без control.
- Прежние5A–5G сохранены; добавлены5H manager,5I carrier,5J RNS-over-WebRTC,
  5K gateway-over-WebRTC,5L multi-provider,5M restricted-mobile acceptance.
  Ближайшая очередь после возобновления:5A reachability →5H→5I→5J.

## Исследование и лицензии

Исходники склонированы только в `/tmp` для read-only inspection:

| Reference | Revision | License | Включение в Family Connect |
| --- | --- | --- | --- |
| kulikov0/whitelist-bypass | `7c19a7ec40900940fe0c43ea1db7768ee632393d` | MIT | Reference-only; ничего не скопировано/изменено/linked |
| openlibrecommunity/olcrtc | `92b2332769c3dd5000584366201572efc448065f` | WTFPL v2 | Reference-only; ничего не скопировано/изменено/linked |

Inspected paths/provenance внесены в [audit](../legal/DEPENDENCY_LICENSE_AUDIT.md)
и [notices](../../THIRD_PARTY_NOTICES.md). Версии Go/Pion/fork graph не закреплены;
перед включением требуется отдельная проверка всех лицензий. Новых dependencies
нет, proprietary LICENSE не менялся. Условия использования сервисов не выводятся
из MIT/WTFPL исходников reference-проектов.

## Проверки, поставка и blockers

Проверены новые локальные ссылки, whitespace и согласованность5H–5M/WEBRTC-1–5.
`git diff --check` прошёл. Runtime test suite не запускалась: исполняемые файлы и
dependency manifests не менялись. В shell PATH нет Go/adb/dotnet; начатая загрузка
Go остановлена после уточнения scope, ничего не установлено. Провайдерские room,
аккаунты/токены не создавались, endpoints не запускались.

Все WEBRTC-1–5 остаются **NOT RUN**. Blockers перед реализацией/приёмкой:
pin/audit minimal RTC graph, проверить live guest/create/media API, выбрать
достижимый ingress на целевой SIM, Android executable/FD protection, доступ к
реальным Android и Windows. Live throughput/RTT/loss/CPU/memory/setup/reconnect
не измерялись; >5Mbit/s и20+ — цели, не результаты. Краснодар: отказ обычного VPN
сообщён пользователем, сравнительный тест нового пути отсутствует.

Обновлены existing PLAN/STATUS/roadmaps/architecture/README, allowlist/XHTTP docs,
Home Gateway design, notices и audit. Existing dirty docs сохранены локально;
commit содержит только чистые до этого изменения design/legal files и этот отчёт,
без присоединения накопленных ранее правок. Push не выполнялся.
Android beta50/code50, Linux0.2.10, Windows0.2.14 согласно предыдущему checkpoint
не менялись; rollout отсутствует, runtime rollback не требуется. Возврат нового
документационного commit не должен сбрасывать прочие локальные правки.

```sh
git diff --check
rg -n '5H|5I|5J|5K|5L|5M' docs/PLAN.md docs/ROADMAP.ru.md
rg -n 'WEBRTC-[1-5]|UnderlayPathManager|WTFPL|guest' docs/reticulum/HOME_GATEWAY_DESIGN.md docs/legal/DEPENDENCY_LICENSE_AUDIT.md
```
