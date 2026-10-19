# Existing-users private Android update / Частное обновление Android

## Current status / Статус

**19.10 product-fix update:** signed recovery candidate
`0.1.18-beta88-recovery` / code88 is available at
`state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk`.
SHA256 `968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`.
Same package/signer, Android12+ arm64, all12 native libraries unchanged.135+34
local JVM checks pass. Fixes the reproduced signal-close recovery classification
and bounded repeat recovery; no speed increase or production IPv6 is claimed.
Owner phone updated87→88 at11:55:55UTC after ordinary Disconnect; exact installed
APK/code88, same UID and restricted-native hash verified. No uninstall/data clear.
Same-identity/key-binding/Support ID proof/import READY and production DNS/HTTPS
PASS. Fresh88 export confirms one automatic reconnect in29.083seconds around
normal gateway rotation, followed by successful traffic. Repeated/overnight
recovery is not yet accepted. Comparison does not show a speed improvement.
No APK was automatically distributed or placed in the public catalog. The file
is available as a limited private recovery update, not fully field/overnight-accepted.
[Current report and limitations](../releases/2026-10-19-beta87-product-fix.md).

**Russian handoff:** это файл обновления, не отдельное приложение. Установите
поверх текущего Family Connect, выбрав «Обновить», затем подключитесь. Не удаляйте
приложение и не очищайте данные; приглашение, новый ID и повторная активация не нужны.
Подпись, установка поверх87 и сохранение identity/ключевых привязок подтверждены
новым proof/READY, не только signer и UID. Один автоматический reconnect проверен;
ускорение, многократное ночное восстановление и IPv6 пока не подтверждены.

### Historical beta87 checkpoint

**DELIVERY_READY=NO. Beta87 is signed and installed over86; same-identity READY and
initial production Android-TUN DNS/HTTPS pass. Automatic87 recovery is not yet
observed. Export86 proves restoration after rotation, then another carrier loss
and terminal authenticated HELLO_RECEIVE/CLOSED_PIPE. Beta87 fixes only that
bounded-recovery classification, not the underlying carrier loss.**
Do not distribute rejected85 or unaccepted86/87. No public release/updater changed.
See the [dated report](../releases/2026-10-19-existing-users-private-beta-1.md) for
installed server packages, tests, failed beta85 evidence and current acceptance.

## Current APK / Текущий APK

- File: `state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk`
- Version: `0.1.18-beta88-recovery`, versionCode88.
- Package: `com.familyconnect.app.friends` (same application, not a parallel install).
- SHA256: `968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` (matches UI84).
- Android12/API31 or newer; arm64-v8a. Other Android/ABI combinations are unverified.
- Physical package upgrade observed: UI84→beta85→beta86→beta87→beta88, no uninstall/data clear.
  Code60/65 and additional remote phones are not claimed as physically tested.
- Post-upgrade identity/key bindings and Support ID match the pre-upgrade record;
  authenticated beta88 import/READY and production Android-TUN DNS/HTTPS pass,
  including after ordinary rotation with freshCRL27130. One88 automatic recovery
  is explicitly correlated in the supplied export; no repeated/overnight claim.
- All12 native libraries match the accepted UI84 APK; transport settings are unchanged.
- Beta88 local JVM suite:135 PASS/19 suites plus34 ownership/startup/floor tests.
  Local tests and the single physical recovery have distinct acceptance boundaries.

## Инструкция пользователю после приёмки

«Установите APK поверх текущего Family Connect, выбрав “Обновить”.
Откройте приложение и подключитесь. Регистрация и ваш ID сохраняются».

Не удаляйте старое приложение и не очищайте его данные. Новый QR-код, приглашение,
активация или ручное продление FIELD-доступа не нужны. Если Android действительно
запросит разрешение на установку или VPN, подтвердите его сами. Это системное
разрешение Android, а не повторная регистрация Family Connect.

Владелец передаёт файл самостоятельно после приёмки; автоматической рассылки нет.

## User instructions after acceptance

Install the APK over your current Family Connect and choose **Update**. Open the
application and connect. Your registration and ID remain in place. Do not uninstall
or clear application data. No new invite, QR code, activation or individual FIELD
extension is required. Confirm Android installation/VPN permissions yourself if
the operating system actually requests them; these are not new registrations.

## Access and maintenance / Доступ и обслуживание

Existing activated, non-revoked identities use their existing proof-of-key workflow;
Support ID is not authorization. Explicit revocations and security floors remain.
Short-lived credentials refresh automatically under the existing approved schedule.
The finite90-day shared authority has planned operator maintenance by
17 December2026 22:36:48UTC; this is not an individual user renewal or daily activation.
See [lifecycle and limitations](../../deploy/friends/restricted/EXISTING_USERS_LIFECYCLE.md).

Restricted-network recovery requires either the verified API path or the existing
pinned control path to be reachable. No claim of universal operator availability,
zero network interruption, months of physical uptime or remote-phone acceptance
is made. Preserve existing identities and security state when reporting a failure.
