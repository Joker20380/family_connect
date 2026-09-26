# План развития Family Connect

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
