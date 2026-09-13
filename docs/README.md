# Documentation map

- [Amsterdam: Linux GUI acceptance, 13.09.2026](releases/2026-09-13-amsterdam-gui.ru.md).

[Amsterdam gateway: real-network pilot and rollback](releases/2026-09-13-amsterdam-pilot.ru.md).

[Android Stage5 verifier](releases/2026-09-13-android-control.ru.md).

[Windows Stage5 verifier](releases/2026-09-13-windows-control.ru.md).

[Stage5 conformance corpus](releases/2026-09-13-control-vectors.ru.md) · [Vector format](../tests/vectors/README.md).

[CI results and Android retry](releases/2026-09-13-linux-control-ci.ru.md) · [Next native binding](stage5-native-binding.ru.md).

[Linux live pilot passed13.09](releases/2026-09-13-linux-control-pilot-pass.ru.md). Scoped CI health correction next.

[Linux paired preview acceptance13.09](releases/2026-09-13-linux-control-acceptance.ru.md) · [Pilot/return runbook](linux-control-preview-rollout.ru.md).

## Paired Linux control preview — 2026-09-12

Operator GUI/core bundle added with an explicit public-file allowlist, integrity
manifest, runtime-only pinned dependencies and extracted launcher. Legacy six-file
desktop archive unchanged. Local405 Python passed; extracted real RNS lifecycle
and GTK smoke passed. Scoped Linux control CI34720569558 passed on source d8aef8a.
AWG/TCP pilot and phase0 Python/Rust passed. General phase0 failover failed at
isolated Docker build; exact cause unavailable (logs API403). Client builds Linux
passed; Windows/Android still running at checkpoint.
No release/install/catalog/server changes. Next: resolve general failover build evidence and prepare paired preview
rollout; native Windows/Android binding, AWG3.1 and TD-1 remain open.
[Preview checkpoint](releases/2026-09-12-control-preview.ru.md).


Latest work/rollbacks: [complete session checkpoint](releases/2026-09-11-session-checkpoint.ru.md).
Ubuntu appearance/terminal: [settings and rollback](ubuntu-laptop-settings.ru.md).

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

Real Linux TCP systemd acceptance: [report](releases/2026-09-11-tcp-systemd.ru.md), [sanitized result](tcp-systemd-result.json).

TCP authenticated delivery: [runbook](tcp-delivery.ru.md), [validation](releases/2026-09-11-tcp-delivery.ru.md).

Published signed TCP 0.1.0: [release evidence](releases/2026-09-11-tcp-release.ru.md).

Root-owned TCP updater and GTK pilot install: [acceptance](releases/2026-09-11-tcp-updater.ru.md).

Manual TCP updater authorization cancellation: [report](releases/2026-09-11-tcp-updater-cancel.ru.md).

Standalone TCP setup, independent VM and second Ubuntu laptop: [checkpoint](releases/2026-09-11-tcp-setup.ru.md).

Second Ubuntu laptop dedicated TCP profile: [checkpoint](releases/2026-09-11-ubuntu-profile.ru.md).

Ubuntu TCP network timeout diagnosis: [report](releases/2026-09-11-ubuntu-network.ru.md).

First-laptop context comparison and TCP cycle: [result](releases/2026-09-11-first-laptop-resume.ru.md).

First-laptop paired headers and remaining loss hypothesis: [report](releases/2026-09-11-first-laptop-paired.ru.md).

First-laptop pinned-control offload comparison: [report](releases/2026-09-11-first-laptop-offload.ru.md).

First-laptop isolated TUN/SOCKS/direct: [report](releases/2026-09-11-first-laptop-isolated.ru.md).

Standalone setup integrated; network tests deferred by user: [checkpoint](releases/2026-09-11-setup-integration.ru.md).

Platform CI180d79f and release preparation: [checkpoint](releases/2026-09-11-platform-ci.ru.md).

Published desktop0.2.9 and offline signed update: [report](releases/2026-09-11-release-0.2.9.ru.md).

Signed standalone TCP Setup: [trust/install runbook](tcp-setup-trust.ru.md), [release evidence](releases/2026-09-11-tcp-setup-release.ru.md).

Windows TCP native engine: [CI result and next integration](releases/2026-09-11-windows-tcp-engine.ru.md).

Windows TCP profile: [operator runbook](windows-tcp-profile.ru.md) · [broker acceptance](releases/2026-09-11-windows-tcp-profile.ru.md).

Windows TCP process lifetime: [native stop/crash acceptance](releases/2026-09-11-windows-tcp-lifecycle.ru.md).

Windows TCP broker network session: [runbook](windows-tcp-session.ru.md) · [LocalSystem acceptance](releases/2026-09-11-windows-tcp-session.ru.md).

Windows TCP installer/transport UI: [report](releases/2026-09-11-windows-tcp-ui.ru.md), [runbook](windows-tcp-session.ru.md).

Windows TCP engine-crash recovery: [report](releases/2026-09-11-windows-tcp-recovery.ru.md).

Windows TCP tunnel health monitoring: [report](releases/2026-09-11-windows-tcp-health.ru.md).

Windows AWG native worker: [report](releases/2026-09-11-windows-awg-engine.ru.md), [build/CI](../pilot/windows-awg/README.md).

- [Windows AWG: активация и эксплуатация](windows-awg.ru.md).

Windows Auto: [implementation and acceptance](releases/2026-09-12-windows-auto.ru.md).

Android WG/AWG: [implementation and acceptance](releases/2026-09-12-android-awg.ru.md), [операции и сборка](android-transports.ru.md).

Android TCP: [implementation and acceptance](releases/2026-09-12-android-tcp.ru.md).

Android Auto: [implementation and acceptance](releases/2026-09-12-android-auto.ru.md).

Stage 5 control channel: [architecture](stage5-architecture.ru.md), [runbook](reticulum-control.ru.md), [Stage 5 checkpoint](releases/2026-09-12-reticulum-control.ru.md).

[GUI coordination and short network checkpoint](releases/2026-09-12-control-gui-network.ru.md).

[Matched HTTPS result](releases/2026-09-12-matched-https.ru.md).
