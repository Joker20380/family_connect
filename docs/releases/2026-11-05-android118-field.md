# Android118 — opt-in restricted-network field delivery / 5 November2026

## Scope and acceptance boundary

Owner requests a version for users on mobile allowlists; the owner cannot reproduce
that network locally. Publish the already qualified, signed118 bytes as a separate
manual download, not a forced rollout or a claim that MESH stability is fixed.
Default invitation/updater remain **113 / catalog sequence7**. Installed owner version
remains118; field-user installation and real allowlist acceptance are **PENDING**.
Linux public0.2.11 and Windows0.2.16/catalog12 are unchanged.

118 includes the intervening MESH transport work and finite signaling-read diagnostics.
See [exact qualification](2026-11-05-android118-signaling-diagnostics.md) and
[overnight checks](2026-11-05-mesh-overnight-checks.md). One paired-DNS timeout, the earlier117
signaling interruption and the scheduled credential renewal outage remain separate open
issues. Ordinary-network recovery does not constitute restricted-network acceptance.

## Immutable artifacts

- Package `com.familyconnect.app.friends`, version `0.1.18-beta118`, code118,
  ARM64, Android8.1/API27 minimum. No new build, version bump or signing operation.
- Accepted source `13e0b37eb3feba53fae7e281f4e12d49a840e85c`;
  [Client builds41933207129](https://github.com/Joker20380/family_connect/actions/runs/41933207129),
  attempt1 accepted. Downloaded source/native/ABI/16K,839 JVM cases, API27/API35 and
  eight UI samples qualified; original CPU-row crop is retained evidence.
- ARM64 CI archive SHA256 `60077e3761ea18feb9b46cb98a1f953949e4e32ad0abe53bc60deee76ef8e86b`.
- [Signed APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta118.apk),
  **50285984 bytes**, SHA256 `b7b0be92456f522f81d87c71c401c2622d2f823178510b28510a6fb8d5c69fca`.
- Existing APK signer SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- [Matching audio corresponding source](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta118-audio-source.tar.gz),
  **7670650 bytes**, SHA256 `6e3066c08ff87062cfd4e74ee31e5336cabb833ee20a0f97e10c6717b9d4fc1d`;
  extracted unchanged from that accepted CI archive.

Separate phase0/Linux-control failures and newer ff9c602 Android invitation-test failure
remain visible; no whole-repository green claim or newer unqualified APK substitution.

## Publication and verification

Guarded publication adds only two exact118 download routes/files on RU. Existing113
routes and all prior downloads are byte-identical. Invitation HTML, both Android catalog
files, gateway catalog and protected product-table hashes remain unchanged. No invitations,
entitlement changes, admission widening, backend restart or MESH deployment. Nginx config
is checked before activation and after atomic replacement; one HUP, unchanged container
PID/start time. Public/default113 is preserved.

Current config SHA256 `42b95d71f7a33e1cce87304ae1fad93a079f5b61e268c678a435abb057e7bf26`;
predecessor `5f744d0562f7f151a17fa13a2c9a43ff52595edab8e94e34ceaa66cfb81d2f9e`.
09:07:09UTC independent normal-trust HTTPS full-byte readback PASS:118 APK, matching
audio source and retained113 APK all return200 with the exact sizes/hashes above; both
catalog routes return200 with the unchanged baseline bytes. APK signature was independently
checked before publication. The first readback used incorrect root-level catalog URLs
and received404 after successfully checking the binaries; corrected documented `/updates/`
routes pass. This was a local verification-path error, not an updater/server repair.
Private receipts stay under ignored `state-client-build/android118-field-20261105/`.

Documentation: targeted link/content checks and `git diff --check` pass for changed
release/guides. Including full STATUS finds one pre-existing missing historical anchor
in the preserved, unrelated local VPN snapshot; it is not changed by this delivery.

## Инструкция для пользователей

1. Скачайте118 по ссылке выше через работающий интернет/Wi-Fi. APK не даёт приглашения
   или MESH-допуска. Установите **поверх** Family Connect Test, без удаления приложения,
   очистки данных и повторной регистрации. Подтвердите системный запрос обновления;
   проверьте, что в приложении указана118.
2. Включите диагностику в приложении **до** попытки. Отключите Wi-Fi и используйте именно
   мобильную сеть с белыми списками. Root, ADB и Mi-аккаунт не нужны.
3. Выберите явно **MESH → Нидерланды**, не Auto: AWG/TCP не доказывает работу MESH.
   Запишите время и результат, проверьте сайт, внешний IP и обычное приложение.
   Если получается, понаблюдайте20–30 минут, включая выключенный экран.
4. Отдельно повторите с **Нидерланды 2**. Россия пока не поддерживает MESH. Не меняйте
   несколько условий одновременно. Работа одного Telegram не доказывает работу всего
   туннеля: возможна связь без VPN или собственный прокси приложения.
5. Сразу после сбоя сохраните диагностику. При необходимости верните работающий интернет
   и отправьте файл/Support ID **лично владельцу**, не в публичный репозиторий или общий
   чат. Укажите модель, Android, оператора, узел,118, время с часовым поясом, состояние
   Wi-Fi, что открылось и через сколько произошёл обрыв.

Не публикуйте приглашения, ключи, профили и сырые журналы. Отсутствие допуска или истёкшая
готовность — отдельная ошибка, не доказательство блокировки carrier. Владелец не должен
повторять эту проверку на своей обычной сети вместо пользователя.

## User procedure (English)

Download118 on a working connection, then update in place without uninstalling, clearing
data or reenrolling. Android8.1+/ARM64 and existing admission are required. Enable in-app
diagnostics first. Disable Wi-Fi and explicitly select MESH, testing Netherlands and
Netherlands2 separately; Auto may hide an AWG/TCP fallback. Record phone/OS/operator/node/
version/time zone, website/IP result and time to failure. If possible observe20–30 minutes
including screen-off. Export diagnostics immediately after failure and send them privately
to the owner when connectivity returns. Do not post profiles, invitation links or raw logs
publicly. Installation, admission and allowlisted-network acceptance are distinct checks.

## Rollback and next gate

RU recovery journal: `/root/fc-android118-field-20261105/`. To withdraw the test download,
read the current config and reconcile later edits. Restore the recorded predecessor only
if the current hash is still the expected118 config; otherwise remove only the two118
route blocks, preserving newer changes. Validate nginx, HUP and verify113/catalog7 and
the invitation. Retain immutable118 files/receipts. Never blindly replay the publisher.

Installed118 is not downgraded by changing a route. Do not uninstall/clear data to force113;
any client repair needs a higher accepted version. No server binary rollback is involved.
Both NL gateways retain native binary
`70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6`.

Next within this incident: authenticated credential renewal without the measured simultaneous
gateway stop. Leaving processes alive alone is insufficient: existing Family sessions
retain their original certificate/CRL security deadline. Prove authorized successor continuity,
revocation/expiry enforcement and coordinated recovery before changing live maintenance.
Keep field-user restricted-network evidence and paired-DNS/signaling diagnosis separate.
No production expiry relaxation or timer pause.
