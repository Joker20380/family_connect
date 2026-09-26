> Historical design/plan. Current delivery status: [STATUS](STATUS.md); active work: [PLAN](PLAN.md). Goals below are not guarantees of the current pilot.

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


# План развития

[English](roadmap.en.md) · [Руководство](../README.ru.md)

## Продукт и постоянные инварианты

Покупатель в Европе, родственники в России, одна семейная подписка сначала на пять устройств,
приглашение по ссылке/QR, автоматический маршрут и дополнительный выбор региона выхода.
Настройки протоколов/серверов не должны становиться частью обычного семейного подключения.

Identity не зависит от IP. Приватные ключи остаются на соответствующем устройстве. Участие
volunteer — только явный opt-in. Добровольцы никогда не предоставляют публичный Internet egress;
это разрешено только управляемым gateway. Протокол relay не принимает произвольный CONNECT/NAT.
История посещений/DNS и payload не логируются. Автономная работа ограничена сроком разрешения.
До заявлений об устойчивости нужны независимые транспорты и bootstrap-источники. P2P не является
обязательной функцией; AUP/abuse-контроль gateway не должен превращаться в сбор истории посещений.
Концентрация egress не означает юридический иммунитет для добровольцев.

## Текущее состояние приёмки

| Возможность | Реализовано | Осталось |
|---|---|---|
| Аутентифицированные данные | Внешний и внутренний QUIC mTLS; членство и server pins | Публичная регистрация, мобильное хранение ключей, ротация |
| Отказ relay | Переключение активной загрузки с сохранением внутреннего QUIC | Несколько хостов, смена адресов, Wi-Fi/LTE, idle health |
| Non-exit | Gateway выбирается по подписанной роли/имени; нет API назначения; изоляция сети | Egress-защита хоста и независимая проверка атак |
| Signed discovery | Python signer, Rust-проверка, срок, атомарный кэш/защита от отката | Жизненный цикл offline root/intermediate и приватность большого каталога |
| Отзыв | CLI оператора с увеличением epoch и проверкой активных сессий | Связь с коммерческими аккаунтами/подписками |
| Offline bootstrap | Запуск из действительного кэша, настраиваемый список источников | Реально независимые размещённые источники |
| Смена gateway | Не реализована | Egress anchor/состояние и точная семантика отказа |
| Разные транспорты | Только UDP/QUIC | Transport API и независимый запасной транспорт |

## Следующие этапы

1. Закрытый Android VpnService + Rust TUN: IPv4/IPv6/DNS-утечки, kill switch, Wi-Fi/LTE,
   измерения скорости/CPU/батареи.
2. Несколько EU-хостов и небольшая согласившаяся группа: SCR, TTC, выживание по типам отказов,
   агрегированная сетевая телеметрия с ограниченным сроком хранения.
3. Пилот 20–50 семей после проверок безопасности и связи: приглашения, onboarding, support/user.
4. Android MVP, аккаунты/семьи/подписки/billing/admin и обработка abuse на gateway.
5. Явный opt-in для relay Linux/Windows/macOS и квоты; iOS NetworkExtension; дополнительные
   независимые транспорты, path intelligence и географическое расширение.

Успех текущих лабораторных тестов сам по себе не означает завершения Phase 0.

## Отдельный стенд реального трафика

Следующий шаг реализован отдельно от описанного выше стенда аутентификации:
[WireGuard-интерфейс через QUIC и relay](data-plane.ru.md). Он включает управляемый
IPv4-выход и сохраняет прежний запрет выхода на relay.

## Следующий развёрнутый этап

Текущая сеть расширена на вторую VPS: [межсерверный relay и испытание отказа](distributed.ru.md).
Описанные выше результаты остаются исторической проверкой одного хоста.
