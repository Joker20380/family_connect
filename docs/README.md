# Documentation

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

Updated24 September2026. Android updater and invitation page: beta50; invitation downloads: Linux0.2.10 / Windows0.2.13 preview.
[Current distribution](releases.md) · [Documentation required with every version](releases.md#documentation-with-every-version).

Start with the guide for your role. [STATUS](STATUS.md) is the source of truth for
installed/deployed versions; dated reports preserve what was checked at that time.

[Windows0.2.13: интерфейс, ключ и приглашение](releases/2026-09-23-windows0213-updater.ru.md) · [English](releases/0.2.13.en.md).

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
- [Paired Linux control rollout](linux-control-preview-rollout.ru.md).
- Operations/diagnostics for the original lab: [English](operations.en.md) / [Русский](operations.ru.md).
- [Release distribution and signing](releases.md).

## Developers

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
