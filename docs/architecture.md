# Architecture map / Карта архитектуры

Family Connect contains a product client path and separate networking experiments.
Use [STATUS](STATUS.md) for platform integration and deployment facts; older design
records describe their named stage, not the entire current application.

## Product and device path

Invitation/entitlement → device identity → provisioning → client verification and
protected state → platform VPN adapter → transport/gateway.

- [Registration: EN](registration.en.md) / [RU](registration.ru.md): product admission,
  single-use challenges and entitlement. Dated module boundaries are historical.
- [Device identity ADR: EN](adr/001-identity-provisioning.en.md) / [RU](adr/001-identity-provisioning.ru.md).
- [Provisioning/cache: EN](provisioning-provider.en.md) / [RU](provisioning-provider.ru.md).
- [Stage 5 control design](stage5-architecture.ru.md) and [native binding](stage5-native-binding.ru.md):
  signed configuration delivery, verification and recovery. Initial AWG/platform limits
  in these dated documents are superseded where STATUS has newer runtime evidence.
- [Android source](../clients/android/), [Linux source](../clients/desktop/),
  [Windows source](../clients/windows/).

Android friends currently exposes AWG 3.1 and TCP REALITY options. Published desktop
v0.2.9 has its own capabilities and activation. Do not infer identical feature support
from shared architecture. Device provisioning/configuration is distinct from the
[offline-signed application update catalog](updates.en.md).

## Messenger

[Design](reticulum-messenger.ru.md) · [Core](../messenger/README.ru.md) ·
[Android voice/UI checkpoint](releases/2026-09-23-voice-scroll-beta49.ru.md) ·
[Foreground delivery/animation evidence](releases/2026-09-19-android-beta16.ru.md).

The core uses separate chat identities, encrypted storage and existing RNS/LXMF
components. Android integrates native screens and a carrier. Early core notes saying
there is no Android UI are historical, not the current pilot state. Android now has a foreground delivery service, notifications, text edits and voice.
Screen-off notification delivery was confirmed; deep Doze latency and broader
restart/offline acceptance remain open. There is no FCM integration.

## Experimental relay network

[Original QUIC architecture and threat model: EN](architecture.en.md) /
[RU](architecture.ru.md) · [Data plane: EN](data-plane.en.md) / [RU](data-plane.ru.md).

The inner/outer QUIC laboratory is separate from the current Android VPN data path.
Its mTLS, revocation timing and failover claims must not be generalized to every client.

## Trust and operations

[Security](../SECURITY.md) · [Privacy](privacy.md) ·
[Documentation map](README.md) · [Current plan](PLAN.md).
