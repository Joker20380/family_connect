# Documentation map

Start with [STATUS](STATUS.md) (what is actually installed/deployed) and [PLAN](PLAN.md)
(the next work). `AGENTS.md` in the repository root directs new sessions here.

| Topic | Русский | English |
|---|---|---|
| Native Linux UI 0.2.7 | [GTK report](releases/0.2.7.ru.md) | [GTK report](releases/0.2.7.en.md) |
| Release 0.2.1 | [Release](releases/0.2.1.ru.md) | [Release](releases/0.2.1.en.md) |
| Client updates | [Updates](updates.ru.md) | [Updates](updates.en.md) |
| Product registration | [Registration](registration.ru.md) | [Registration](registration.en.md) |
| Provisioning and cache | [Provider](provisioning-provider.ru.md) | [Provider](provisioning-provider.en.md) |
| Gateway operations | [Reconciliation](gateway-reconciliation.ru.md) | [Reconciliation](gateway-reconciliation.en.md) |
| Desktop layout | [Layout](desktop-layout.ru.md) | [Layout](desktop-layout.en.md) |
| Implementation history | [Log](implementation-log.ru.md) | [Log](implementation-log.en.md) |

Historical descriptions of an earlier stage are not the deployment state. STATUS is
updated after verification; plans and unrun checks must never be marked complete.

Windows visual alignment: [RU](releases/0.2.8.ru.md), [EN](releases/0.2.8.en.md).

Live product enrollment/revoke validation (2026-09-10): [report](live-product-smoke.ru.md).

Connection resilience / AWG pilot: [rollout](releases/2026-09-10-awg.ru.md).

Linux established-session recovery: [report](releases/2026-09-10-recovery.ru.md).

TCP experiment (unstable; resume here): [checkpoint](releases/2026-09-11-tcp.ru.md).

TCP diagnosis and routing defect: [report](releases/2026-09-11-tcp-diagnosis.ru.md).

TCP routing correction (isolated tests passed; not installed): [report](releases/2026-09-11-tcp-routing.ru.md).

Matched TCP/direct/SOCKS timing and remaining errors: [report](releases/2026-09-11-tcp-matched.ru.md).

Paired client/server TCP-header diagnosis: [report](releases/2026-09-11-tcp-packets.ru.md).

Development stages and acceptance criteria: [roadmap](ROADMAP.ru.md).

Local Wi-Fi/gateway/VPS comparison: [report](releases/2026-09-11-local-link.ru.md).

Retest after Wi-Fi change (120/120 isolated probes): [report](releases/2026-09-11-network-change.ru.md).

Corrected TCP helper installed; short laptop smoke passed: [report](releases/2026-09-11-tcp-host-smoke.ru.md).

Established AWG → TCP backend recovery (two passes; GUI acceptance pending): [report](releases/2026-09-11-awg-tcp-recovery.ru.md).

Real GTK/pkexec recovery and remaining manual acceptance: [report](releases/2026-09-11-tcp-gtk.ru.md).

Manual polkit cancellation passed: [report](releases/2026-09-11-polkit-cancel.ru.md).

TCP integration into main, review fixes and packaging gap: [report](releases/2026-09-11-tcp-integration.ru.md).

Linux TCP component bundle: [installation](linux-tcp-install.ru.md), [validation](releases/2026-09-11-tcp-bundle.ru.md).
