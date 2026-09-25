# 25.09.2026 — Restricted WebRTC: прямой Android→EU критический путь

## Решение и основание

По addendum пользователя: первый restricted-network transport должен идти
**Android → Telemost VP8 → headless Linux EU Family Gateway → Internet**.
Windows Home PC не обязателен. Reticulum не удаляется: identity binding,
control/recovery, provisioning, messaging/discovery, Personal Gateway и future
Meshtastic сохраняются. High-bandwidth data plane не помещать в RNS без
подтверждённого benchmark преимущества.

Основание — [пользовательский полевой результат25.09](2026-09-25-telemost-cellular-evidence.ru.md):
штатный Telemost видеозвонок Краснодар cellular→Бельгия успешен при недоступном
прямом Family VPN. Community references содержат binary/video carrier code,
но их работа не была независимо воспроизведена в этой сессии. Это обоснование
эксперимента, не завершённый carrier или гарантия обхода ограничений.

Убираем из критического пути home dynamic IP, home NAT traversal, Windows routing/
NAT, always-on PC и detour через дом. Provider signaling/ICE и доступность EU
Linux endpoint остаются необходимыми. Home Gateway сохраняется для LAN/NAS/RDP,
семейных устройств, residential exit и аварийного alternate gateway.

## Что подготовлено

В [существующий дизайн](../reticulum/HOME_GATEWAY_DESIGN.md) добавлено решение,
control/data diagram, границы WebRtcRestrictedTransport/carrier/EU gateway,
secure-session/mux/reliability requirements, phase1 TCP+DNS / phase2 UDP,
fail-closed и новые gates. Не создан второй TransportManager или identity store.
Изучен Android Xray TUN inbound в `pilot/android-tcp/tcp-android.go` как первый
reuse-кандидат; универсальный bridge к Family mux ещё не реализован.

Критические требования: E2E Family encryption выше untrusted SFU, existing
Device Identity/FAMILY admission до egress, rejection unknown/wrong-family/revoked/
replay; одна carrier session для нескольких TCP streams; DNS внутри E2E;
bounded flow control/reliability, no unsupported UDP/IPv6 leak; protected sockets;
provider disable через verified provisioning, isolated API failures; без публичного
SOCKS/HTTP proxy, логирования DNS/payloads/секретов или отключения TLS verification.
Выбор audited encryption/mux/reliability library остаётся до реализации.

## Положение и порядок работ

Глобально этап5 — resilient communications. Существующие5A–5M не перенумерованы
и не закрыты; добавлен **5N Restricted Android→EU**:

1. WEBRTC-EU-1 /5N.1: desktop/Linux↔Linux binary round trip через Telemost.
2. WEBRTC-EU-2 /5N.2: Android↔EU binary, ещё без TUN.
3. WEBRTC-EU-3 /5N.3: authenticated E2E Family data, negative admission tests.
4. WEBRTC-EU-4 /5N.4: один TCP stream с настоящим HTTPS response.
5. WEBRTC-EU-5 /5N.5: параллельные TCP/API/browser/DNS в одной conference.
6. WEBRTC-EU-6 /5N.6: full-device Android TCP+DNS, EU exit/no direct leaks.

**Все gates NOT RUN.** Ближайший engineering milestone после возобновления
реализации — authenticated data с Android Краснодар cellular через Telemost в EU
Linux. Далее full-device Internet.5H/5I generic contracts используются где подходят;
5M/5F — real-network acceptance, затем5L WB fallback.5J/5K RNS/Home Gateway не
блокируют5N. Meshtastic — будущий control bootstrap, не текущая реализация.

Acceptance: Wi-Fi OFF, ordinary FC FAIL / Telemost video PASS / Family transport
PASS в сопоставимых условиях;5/30/60min,setup/RTT/throughput/CPU/memory/battery,
reconnect count/time; screen,data,airplane toggles,cellular reconnect,room recreation,
EU restart; browsing,large download,video,many HTTP requests. Targets >5Mbit/s PoC,
>10–20 good,>30 strong; не измеренные результаты. Strong success —30–60min normal
traffic/no leaks и automatic recovery на целевой ограниченной мобильной сети.

## Scope, validation и поставка

Сохранено предыдущее ограничение пользователя: **только документация и подготовка**.
Runtime код/dependency pins/device tests/provider sessions/deployment не менялись.
Existing AWG/TCP/XHTTP и defaults не затронуты. Community references остаются
reference-only; proprietary LICENSE прежний, новые crypto/mux зависимости не добавлены.

Обновлены19 документов: design, PLAN/STATUS, roadmap/architecture/README RU/EN и
индексы, allowlist/XHTTP, audit/notices и этот отчёт. Старые решения сохранены с
явной пометкой об изменившемся приоритете. Проверены новые относительные ссылки,
наличие всех WEBRTC-EU gates/сохранение5A–5M и `git diff --check`.
Runtime tests не запускались для документационной правки.

Android beta50/code50, Linux0.2.10, Windows0.2.14 по предыдущему release checkpoint
прежние; новых artifacts/rollout нет, runtime rollback не требуется. Commit включает
design/legal files, чистые до этой правки, и этот отчёт. Existing dirty планы/индексы
сохранены локально без присоединения накопленного diff. Push не выполнялся.

```sh
git diff --check
rg -n 'WEBRTC-EU-[1-6]|5N|TCP.+DNS' docs/PLAN.md docs/reticulum/HOME_GATEWAY_DESIGN.md
git log -1 --oneline
```
