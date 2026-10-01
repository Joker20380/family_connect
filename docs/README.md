# Documentation

**Current product critical path — 30.09.2026:**
[5N-BOOT-1 → 5N.6 → MVP Orchestrator → Krasnodar FIELD-1 → 50–100-user beta](PLAN.md).
Начните с [CURRENT PRODUCT STATE](STATUS.md), затем [продуктовой архитектуры](architecture.md):
implemented beta / proven experimental / planned разделены явно.
[MVP Orchestrator implementation / текущая acceptance](releases/2026-09-30-mvp-connectivity-orchestrator.ru.md):
одно CONNECT, bounded normal fallback/BOOT-1, existing VPN owner и fail-closed guard;
isolated physical PASS01.10 с сохранённым initial FAIL; не public rollout/не FIELD-1.
5N.1–5N.5, ReliableStream/DNS containment и automatic Room Broker приняты;
Whole-device path принят isolated; production rollout ещё не выполнен.
[5N-PROV-1 local implementation / authorized deployment preflight STOP](releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md):
existing Friends identity → restricted provisioning/BOOT-1 → secure Android cache;
[owner-only deployment, migration, secrets и rollback](../deploy/friends/restricted/README.md).
Required production material подготовлен; rollout не начат. Это текущий integration
gate перед actual-Friends readiness/rehearsal и final FIELD APK.
[Current deploy preflight READY / no deployment](releases/2026-10-01-5n-prod-deploy-preflight.ru.md):
same authority, CRL refreshed to3, owner-installed provider config schema PASS;
no token value/hash/size exposed. Recheck expiry before separately authorized use.
[5N-PROD-AUTHORITY READY / staged only](releases/2026-10-01-5n-prod-authority.ru.md):
explicitly authorized first Family, sole owner grant, existing NL identity binding,
signed delegated issuer/real CRL and native validation. No service/API deployment;
provider-token phase excluded. Refresh short-lived CRL before future use.
[Historical material inventory / initial BLOCKED audit](releases/2026-10-01-5n-prod-materials.ru.md).
[5N-BOOT-1 PASS / isolated physical cached-state acceptance](releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md):
[cached directory, rendezvous, bounds и isolated runbook](../carrier/bootstrap/README.md).
[5N.5 evidence](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md) ·
[Room Broker PASS и temporary ingress](releases/2026-09-28-webrtc-5n-room-broker.ru.md) ·
[Rebaseline report](releases/2026-09-30-product-engineering-rebaseline.ru.md).
Второй restricted carrier, Home Gateway и RNS-over-WebRTC — backlog.

Следующие датированные priority notes — историческая навигация, не текущий порядок.

**Приоритет25.09 уточнён:** [Restricted Android→Telemost VP8→Linux EU](PLAN.md)
без обязательного Windows Home Gateway/IP-over-RNS. Reticulum control/recovery
сохраняется. [Решение в существующем дизайне](reticulum/HOME_GATEWAY_DESIGN.md).
Добавлены WEBRTC-EU-1–6/5N; сначала binary/auth, затем TCP+DNS/full-device.
Preparation-only относилось к25.09; текущие runtime/gates — в STATUS/PLAN.
Существующие AWG/TCP/XHTTP не заменяются.

**WebRTC underlay — подготовка25.09 (backlog):** [существующий Home Gateway design](reticulum/HOME_GATEWAY_DESIGN.md)
расширен path manager/provider/IPC contracts, исследованием WB/Telemost и gates
WEBRTC-1–5. [План5H–5M](PLAN.md) · [Лицензии](legal/DEPENDENCY_LICENSE_AUDIT.md).
Реализация и устройства пока отложены; новый статус — подготовка5A/5H.

**Стратегия25.09 уточнена (backlog):** [Home Gateway](reticulum/HOME_GATEWAY_DESIGN.md) —
Reticulum для control/discovery/negotiation, выбранный защищённый transport для IP.
Сейчас этап5/начало5A: доказать достижимый control и data ingress при активных
мобильных белых списках; затем телефон↔домашний ПК. [Глобальный план](ROADMAP.ru.md).

**Новый приоритет25.09: [Personal/Home Gateway over Reticulum (backlog)](reticulum/HOME_GATEWAY_DESIGN.md)**
— требования, integration points, threat model, Stage5A–5G и gates RNS-1–RNS-5.
[PLAN](PLAN.md) · [Статус](STATUS.md) · [Лицензионный аудит](legal/DEPENDENCY_LICENSE_AUDIT.md)
· [Third-Party Notices](../THIRD_PARTY_NOTICES.md). Дизайн зафиксирован; рабочий
Home Gateway и приёмка RNS-2 пока отсутствуют.

[XHTTP/TLS: исследование, реализация и границы5.3в](xhttp-implementation.ru.md).

[Режим сетей с белыми списками: требования и план5.3в](allowlist-connectivity.ru.md).

[Android: подключение выбора gateway к службе/UI](releases/2026-09-24-android-selection-service.ru.md).

**Новому разработчику: [общая карта кода по модулям](code-map/README.ru.md)** —
сервер, клиенты, мессенджер, эксплуатация, зависимости и границы готовности.

[Android: транзакционная смена gateway и восстановление](releases/2026-09-24-android-gateway-transaction.ru.md).

Разработчику: [карта managed-кода, проверки и восстановление](managed-control-code-map.ru.md).

[Android AWG3.1 journal и фактический статус публикации документации](releases/2026-09-24-awg31-android-journal.ru.md).

[AWG3.1: согласование Java/C#/Python и границы проверки](releases/2026-09-24-managed-awg31-native-verifiers.ru.md).

[Защита от блокировок: требования и приёмка](blocking-resilience.ru.md) ·
[Managed AWG3.1: локальный checkpoint5.3а](releases/2026-09-24-managed-awg31.ru.md).

[Как другие проекты восстанавливают доступ и доставляют адреса](releases/2026-09-24-competitor-recovery.ru.md).

Этап4 принят пользователем как пилотный выпуск. Этап5 начат: независимый служебный
канал и расширяемый парк серверов. [Контракт](stage5-fleet-contract.ru.md) ·
[Аудит5.1 и первые компоненты](releases/2026-09-24-stage5-audit.ru.md).
[Текущий план](PLAN.md) · [Основание приёмки](STATUS.md).
[Приоритет AWG3.1 и исследование третьего транспорта](releases/2026-09-24-transport-priorities.ru.md).

Последние доработки: [голосовые beta50: жесты, прокрутка и фон](releases/2026-09-23-switch-colors-beta50.ru.md) · [мессенджер и уведомления](testing/messenger-notices.ru.md).

- [family_connect: обновления Android, язык, бренд и карта](releases/2026-09-20-updater-language-brand.ru.md).

- [Native Friends AWG 3.1 на Linux/Windows: проверки и rollout](releases/2026-09-20-desktop-awg31.ru.md).

[Product introduction](../README.md) · [Русская версия](../README.ru.md)

Updated30 September2026. Last documented distribution: Android beta51/code51,
Linux0.2.11 / Windows0.2.15; Windows0.2.14 compatibility fallback retained.
This documentation task does not revalidate installed/public/invitation artifacts.
[Current distribution](releases.md) · [Documentation required with every version](releases.md#documentation-with-every-version).

Start with the guide for your role. [STATUS](STATUS.md) is the source of truth for
installed/deployed versions; dated reports preserve what was checked at that time.

[Windows0.2.14: интерфейс, ключ и приглашение](releases/2026-09-24-windows0214-installer.ru.md) · [English](releases/0.2.14.en.md).

## Users

- Getting started and troubleshooting: [English](getting-started.en.md) / [Русский](getting-started.ru.md).
- Client installation: [English](clients.en.md) / [Русский](clients.ru.md).
- [Detailed Android friends walkthrough](testing/friends-quickstart.ru.md).
- Desktop updates: [English](updates.en.md) / [Русский](updates.ru.md).
- [Security](../SECURITY.md) and [privacy](privacy.md).

## Operators

- [Friends deployment](../deploy/friends/README.md).
- [Fleet leases/IPAM: хранение, API и recovery](fleet-leases.ru.md).
- [Fleet proof авторизация и scheduler](fleet-access-scheduler.ru.md).
- [Fleet offline publication: подпись, доступ и схема3](fleet-publication.ru.md).
- [Checkpoint5.2:269 тестов signed publication](releases/2026-09-24-fleet-publication.ru.md).
- [Checkpoint5.2:201 тест и миграция](releases/2026-09-24-fleet-services.ru.md).
- [Fleet gateway fencing и worker](fleet-gateway-fencing.ru.md).
- [Fleet WG/AWG и SSH: контракт, установка и границы](fleet-wg-ssh.ru.md).
- [Native fleet-приёмка:12 сценариев WG/AWG+SSH](releases/2026-09-24-fleet-native.ru.md).
- [Повторяемый изолированный стенд](../pilot/fleet-native/README.ru.md).
- [Этап5.2: WG/SSH checkpoint,163 теста](releases/2026-09-24-fleet-wg-ssh.ru.md).
- [7.1: единая Django-админка серверов, доступа и платежей](PLAN.md#django-admin).
- [Этап5.2: проверки постоянных выдач](releases/2026-09-24-fleet-leases.ru.md).
- Registration: [English](registration.en.md) / [Русский](registration.ru.md).
- Gateway reconciliation: [English](gateway-reconciliation.en.md) / [Русский](gateway-reconciliation.ru.md).
- [Persistent peer worker: deployment/rollback](../deploy/product-peer-worker/README.md)
  and [RU/NL disk I/O diagnosis](releases/2026-09-29-disk-io-recovery.ru.md).
- [Paired Linux control rollout](linux-control-preview-rollout.ru.md).
- [Linux AppImage + .deb packaging design](linux-appimage-deb.ru.md).
- Operations/diagnostics for the original lab: [English](operations.en.md) / [Русский](operations.ru.md).
- [Release distribution and signing](releases.md).

## Developers

- [5N.5: bounded TCP mux + Family DNS](releases/2026-09-28-webrtc-eu5-mux-dns.ru.md):
  **PASS**, physical4 simultaneous public HTTPS,304.138s mixed5 TCP+171 DNS,
  exact/fair/bounded, native local destination DNS denied, independent lifecycle.
  [DNS dependency audit/manual procedure](testing/webrtc-dns-containment.ru.md).
  No TUN/full-device DNS/Room Broker/production rollout; STOP after5N.5.

- [5N.4: single admitted TCP stream](releases/2026-09-28-webrtc-eu4-single-tcp.ru.md):
  **PASS**, physical public HTTPS10MiB, controlled exact duplex300.821s,
  half-close/errors/security/regressions/cleanup; failed attempts preserved.
  No mux/TUN/production rollout; STOP before5N.5.

- [5N-PERF-2: reliable long-duration operating envelope](releases/2026-09-27-webrtc-5n-perf2-reliable-envelope.ru.md):
  **PASS**, physical Android/Telemost/Amsterdam, fixed reliable defaults;
  1.742311Mbit/s/30min, conservative1.480531Mbit/s/15min; ceiling not established,
  cleanup/regressions complete, no5N.4.

- [5N-REL-1: reliable ordered bytes before Family TLS](releases/2026-09-27-webrtc-5n-rel1-reliable-stream.ru.md):
  bounded selective repeat/SACK, deterministic fault matrix, natural/injected live
  gap recovery and300s physical Android validation, **PASS**; cleanup complete.
  [Wire format, limits and threat boundary](../carrier/reliablestream/README.md).

- [5N-PERF-1: physical VP8 capacity measurements](releases/2026-09-27-webrtc-5n-perf1-carrier-capacity.ru.md):
  window/offered-load/payload sweeps, timing and raw media evidence; long-run
  integrity failures prevent accepting a sustainable carrier ceiling. No5N.4/rollout.

- [Telemost5N.1 carrier: build и live runbook](../carrier/README.md),
  [recovery/results27.09](releases/2026-09-27-webrtc-eu1-telemost-binary.ru.md):
  real Linux↔Telemost VP8↔Amsterdam PASS27.09 (291 checks +30s/5min);
  production/версии не менялись.
- [Android5N.2: standalone APK и operator runbook](../clients/android/telemost-runtime/README.md),
  [physical-device results27.09](releases/2026-09-27-webrtc-eu2-android-binary.ru.md).

- [Contribution and build checks](../CONTRIBUTING.md).
- [Architecture map](architecture.md): current product versus experimental relay paths.
- Device identity: [English ADR](adr/001-identity-provisioning.en.md) / [Русский ADR](adr/001-identity-provisioning.ru.md).
- Provisioning: [English](provisioning-provider.en.md) / [Русский](provisioning-provider.ru.md).
- [Stage 5 control protocol](stage5-architecture.ru.md), [native binding](stage5-native-binding.ru.md).
- [Messenger design](reticulum-messenger.ru.md) and [core](../messenger/README.ru.md).
- [Android runtime acceptance](testing/android-stage5-live.ru.md).
- Lab testing: [English](testing.en.md) / [Русский](testing.ru.md).

## Project

- [Current state](STATUS.md) and [working plan](PLAN.md).
- [Desktop Friends TCP recovery and refined Linux UI](releases/2026-09-20-desktop-friends-apply.ru.md).
- [Desktop identity storage and recovery checks](releases/2026-09-19-desktop-identity-storage.ru.md).
- [Desktop modernization](desktop-modernization.ru.md) and [first integration checks](releases/2026-09-19-desktop-friends-foundation.ru.md).
- [Roadmap](ROADMAP.ru.md); historical plans are linked separately.
- [Release model](releases.md) and [GitHub Releases](https://github.com/Joker20380/family_connect/releases).
- [Three-platform download verification](releases/2026-09-20-three-platform-downloads.ru.md).
- [Licensing gaps](licensing.md).
- [Public presentation audit](releases/2026-09-19-github-presentation.ru.md).

## Engineering history

All detailed reports remain available in [releases](releases/) and the
[preserved session index](history-index.md). Implementation logs:
[English](implementation-log.en.md) / [Русский](implementation-log.ru.md).
Older instructions may name retired hosts or superseded interfaces; follow current
runbooks and STATUS before operating anything.

- [Коммерческая гипотеза: восстановление после блокировок и конкуренты](releases/2026-09-24-vpn-market-assessment.ru.md).

- [Reticulum: перенос службы, discovery и границы восстановления](reticulum-recovery-design.ru.md).

- [Критические секреты и аварийное восстановление](secrets-and-recovery.ru.md).

- [Локальная подпись с ключом из KeePassXC](vault-signing.ru.md).

- [Закрытые серверные копии и проверка восстановления](server-secret-backup.ru.md).

- [Время серверов и диагностика chat-sync](server-time-and-chat-sync.ru.md).

- [Изолированная проверка восстановления KeePassXC](vault-restore-rehearsal.ru.md).

- [Потребители секретов и состояние миграции](secret-consumer-register.ru.md).

- [Подпись Android APK из KeePassXC](android-vault-signing.ru.md).

- [Актуальность локальных SQLite и границы классификации](local-sqlite-backup-review.ru.md).
