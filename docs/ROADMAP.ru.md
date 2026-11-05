# План развития Family Connect

## Актуальная продуктовая очередь — 05.11.2026

**Работающий многосерверный пилот → эксплуатационная надёжность Android MESH →
контролируемая платная Android-бета → расширение по результатам пилота.**

Текущая веха — небольшая согласованная группа пользуется сервисом без регулярного
ручного восстановления соединений разработчиком. Основной незакрытый блок исходного
плана — этап5 (служебный канал, парк серверов, ограничения сети). Части этапов6/7 и учёт
подписок реализованы; это не приёмка автоматического восстановления или коммерческого запуска.

Поставлено ранее: многосерверный пилот, opt-in APK118, основной updater113. Текущая работа
ничего из этого не меняет. Authenticated exchange, интеграция и положительный двухузловой
стенд с двумя renewal проверены изолированно, не активированы в production. G1 аварийный
переход реализован и проходит адресные Python-проверки, но G1–G4 целиком ещё не приняты.
G2 — независимые процессы/отказы; G3 — фактическая Android HTTP/cache доставка;
G4 — квалифицированный online runtime/API пакет. [Точные gates/evidence](releases/2026-11-05-mesh-online-renewal.md).
Историческая проверка b1d17d3: root/package118 PASS, online entrypoint отсутствовал.
Этот пакетный дефект устранён в отдельном default-off кандидате; штатные controller/node
проходят SSH COMMIT/replay и адресные отказы процессов. Новый отдельный packet driver
на общем runtime создаёт seed штатно и передаёт TLS/mux/TCP/DNS/verified HTTPS на обоих NL
после15s; реальный supervisor проверяет restart и approval-gated recovery. Исправлен
обнаруженный lost-start-response/fencing дефект. Старый proxy остаётся отрицательным тестом.
Это не Telemost/live/systemd-приёмка и не закрытие G1–G4: revoke, оставшиеся process/race,
Android HTTP/cache/native и два renewal через реальные сроки ещё требуют проверки.
Frozen source8eeb9f0: адресная root/package/core-выборка263 PASS/0 SKIP; это
самостоятельный implementation checkpoint, не принятая А и не разрешение начинать Б.
Следующая локальная дельта закрывает сценарий G1 с настоящим revoke после COMMIT и после
approval, TLS-отказом на обоих NL и новой рабочей сессией разрешённой identity. Frozen9369e65:
G1 isolated core PASS, адресная выборка138 PASS/0 SKIP. G2/G3/G4 и Б остаются открыты.
Новая G2-проверка обнаружила принятие receipt уже погибшего gateway. Source-исправление
добавляет фактический reader-readback до delivery-ready; parallel cleanup сохраняет
SSH120/1395s+lateness. Квалификация этого кандидата продолжается, без поставки.
Для G3 выделен общий whole-device transport seam; отдельный x86_64 test-only build
подключает packet relay через штатный protect, release-проверки его отвергают.
Это подготовка контура, не Android HTTP/cache/owner PASS и не начало Б.
Frozen5043d72:347 PASS/1 optional SKIP в адресной выборке; пропущенный native gate
отдельно1 PASS на том же source. G1 повторён, process/RPC-сценарии G2 пройдены;
реальное истечение predecessor блокируется до journal/owner writes. Новый длительный
harness проверяет два renewal по wall clock, но пока не является G4 PASS.

**Один действующий следующий шаг: закончить G1–G4 того же MESH incident.** После этого:

В рамках выбранного задания после отдельного принятого source/package checkpoint renewal
выполнить ограниченную Android-задачу **ANDROID-APP-VPN**: «Приложения и VPN», единая
локальная политика ALL/INCLUDE/EXCLUDE для AWG/TCP/MESH/Auto и приёмка маршрутизации.
Она не начата и не заменяет незакрытые G1–G4; её изменения отделимы от срочного renewal.
Ни одна фаза не разрешает production/поставку/публикацию. Эксплуатационная очередь:

1. Квалифицировать точные immutable release-артефакты клиента, обоих gateway и publisher/runtime;
   подготовить контролируемую поставку. Не начинать поставку автоматически.
2. После отдельно разрешённой поставки принять настоящий renewal обоих NL, paired-DNS,
   WebSocket, медленную сеть/потери/погашенный экран/мобильные белые списки.
3. При достаточной эксплуатационной приёмке вернуться к ANDROID-CONTROLLED-BETA:
   актуальная базовая версия, доступ/отзыв, согласованные участники и opt-in, условия подписки,
   мониторинг и ответственный за остановку. Существующие лимиты платного пилота сохраняются;
   завершённый внутренний canary не повторяется без причины. Новых оплат/участников сейчас нет.
4. Расширяться только по успешности подключений, обрывам, восстановлению, поддержке и стоимости.

Online renewal не закрывает paired-DNS/WebSocket, полевую стабильность, этап5 целиком или
платный запуск. Desktop parity, iOS, Home Gateway, новые провайдеры/серверы и платёжный
агрегатор не входят в зависимости этой технической задачи. Историческая цель50–100
не является разрешением расширить группу. [STATUS](STATUS.md) · [PLAN](PLAN.md).

## Историческая продуктовая очередь — 30.09.2026

Ниже сохранены сентябрьские сведения и прежние NEXT; они не действуют вместо сводки05.11.

Family Connect — resilient connectivity для семей, не набор протоколов.
Foundation существует, normal AWG/TCP работают в beta; restricted data plane
5N.1–5N.5 + ReliableStream/DNS containment и automatic Room Broker доказаны
изолированно на physical Android, но ещё не стали released whole-device VPN.

**5N-BOOT-1 → 5N.6 Android full-device → minimum viable Connectivity Orchestrator
→ Krasnodar FIELD-1 → 50–100-user beta.** Это текущий порядок; authoritative
phase A–I statuses, acceptance и будущие privacy-safe metrics ведутся в [PLAN](PLAN.md).
[Архитектура/три planes](architecture.md) · [Фактический статус](STATUS.md).

Второй carrier (VK/WB/прочие), Home Gateway и RNS-over-WebRTC — backlog;
FEC/HOL/performance — позже по evidence. iOS, load/scale, новые gateways/carriers,
monetization/referrals — после реальной beta evidence, не текущие blockers.
Ни bootstrap, ни FIELD-1 не считаются выполненными этой документацией.
Исторические стадии ниже сохранены без перенумерации; их preparation-only,
«next» и обязательный WB fallback не являются текущим решением.

## Current priority25.09 — Restricted Android→EU (5N)

**Stage5 now prioritizes Android → Telemost VP8 → headless Linux EU Gateway →
Internet.** Windows Home Gateway and IP-over-Reticulum are not prerequisites.
Reticulum control/recovery/provisioning/identity/discovery remains first-class.
The user-reported Krasnodar cellular→Belgium video call supports provider selection,
not a claim of working Family binary transport. Current scope: preparation only.

Preserve5A–5M; add **5N.1–6 = WEBRTC-EU-1–6**: desktop/Linux binary → Android/EU
binary → authenticated Family session → single HTTPS stream → multiplexed TCP/DNS
→ full-device Android. Reuse generic5H/5I work; validate in Krasnodar (5M/5F), then
WB fallback (5L). RNS/Home Gateway5J/5K and home-specific5B–5E remain secondary.
No earlier gate is closed by this reprioritization. Meshtastic stays future control
bootstrap. [Plan/gates](PLAN.md) · [Existing design](reticulum/HOME_GATEWAY_DESIGN.md).
Earlier immediate-next-step orders below are superseded by this section.

## Whitelisted WebRTC Carrier extension — 2026-09-25

Current scope is **documentation/preparation only**, per the owner's latest request.
We are at global stage5, preparing5A/5H. Existing5A–5G retain their numbering and
open gates. Added work: **5H** UnderlayPathManager → **5I** single-provider carrier
(WEBRTC-1/2) → **5J** RNS-over-WebRTC (WEBRTC-3) → **5K** Home Gateway-over-WebRTC
(WEBRTC-4/5) → **5L** multi-provider support → **5M** restricted-mobile acceptance
(linked to5F). Execution starts with5A reachability,5H/5I/5J; earlier letters are
not thereby complete. [Current plan](PLAN.md) · [Design](reticulum/HOME_GATEWAY_DESIGN.md).

Telemost is the first candidate after the user-reported Krasnodar→Belgium video
call (25 Sep); WB is the reserve. Binary/headless carrier availability is untested.
Reticulum overlay consumes interchangeable direct/WebRTC underlays; provider logic
stays below it. All WEBRTC gates are untested. Device tests and code are deferred.

## Stage 5 / Home Gateway — active development (strategy revised 2026-09-25)

**Current position: start of 5A — design and ingress reachability validation.**
Primary goal: a secure phone↔home-PC connection while mobile allowlist restrictions
are active. Reticulum supplies control/discovery/authentication/negotiation/recovery;
IP packets use a selected encrypted data transport. IP-over-RNS is optional.
[Current plan](PLAN.md) · [Design and gates](reticulum/HOME_GATEWAY_DESIGN.md).

- **5A Control/discovery and ingress reachability** — verify both control and data paths on the target restricted mobile network; existing Device Identity/FAMILY.
- **5B Android ↔ Windows encrypted session** — RNS-1: negotiated data handshake and reconnect; reachable relay first.
- **5C IP tunnel over selected transport** — RNS-2: real IPv4 packets/return path; RNS packet carriage not required.
- **5D Windows Personal Gateway** — explicit diagnostic Internet, RNS-3.
- **5E existing VPN upstream integration** — same VPN exit IP, RNS-4.
- **5F real mobile-network validation** — Краснодар with active restrictions, measurements and 30–60 minute stability, RNS-5.
- **5G direct paths / zero-config optimisation** — direct IPv6/IPv4, NAT traversal and multiple paths after measurements.

Home Gateway implementation and all RNS gates remain open. Stage4 pilot delivery
was accepted; stage5 is not complete. Numeric5.1–5.6 control/fleet tasks remain
separate from lettered5A–5G. Stage6 recovery and stage7 commercial/service work are
still ahead. Reuse relevant5.3в ingress work without restarting unrelated debt.
An encrypted relay carries data to the home PC; it is not the selected Internet exit.
A reachable RNS destination alone does not make a blocked data endpoint reachable.
Existing VPN defaults and releases stay unchanged.


Действующий порядок: [рабочий план](PLAN.md). Проверенные версии: [STATUS](STATUS.md).
Этап4 принят23.09.2026 как пилотный выпуск. В работе этап5: независимый служебный
канал и расширяемый парк серверов. Подробности готовности — в STATUS.

| Этап | Результат |
| --- | --- |
| 1 | Идентичности устройств, выдача и отзыв доступа, базовый VPN — работают в пилоте |
| 2 | AWG3.1 и восстановление — реализация есть, длительная сетевая приёмка впереди |
| 3 | TCP REALITY — реализация есть, приёмка в разных сетях впереди |
| 4 | Android/Linux/Windows: пилотный выпуск принят пользователем23.09 |
| **5 — сейчас** | Control/fleet частично реализованы; приоритет5N: Android→Telemost VP8→Linux EU; подготовка, real-network acceptance впереди; Home Gateway вторичен |
| 6 | Смена полностью недоступного gateway — сквозная приёмка впереди |
| 7 | Сервис и коммерческий запуск — согласована7.1 Django-админка; оплаты и подписок пока нет |

Android beta50 содержит текст, правки, голосовые и уведомления. Это не означает
равенство desktop-возможностей, мгновенную доставку в Doze или готовность коммерческого
сервиса. Текущая документация обновляется после каждого изменения версии.

[Прежние планы и решения](ROADMAP.ru.before-beta49-2026-09-23.md) сохранены как история.
[Ранний замысел QUIC/семейной подписки](roadmap.ru.md) описывает цели, а не обещания пилота.

[7.1: единая панель серверов, доступа и платежей](PLAN.md#django-admin) использует
общие фоновые операции5.2. Добавление узла не выполняется внутри HTTP-запроса Django.

Приоритет24.09: при незакрытом5.2 первым выполняется5.3а managed AWG3.1.
WG/AWG2 сохраняются для совместимости, дальнейшее отдельное развитие остановлено.
5.3б — исследование NaïveProxy HTTPS/HTTP2 и Hysteria2 как третьего пути;
production-выбор зависит от измерений. [Обоснование](releases/2026-09-24-transport-priorities.ru.md).
