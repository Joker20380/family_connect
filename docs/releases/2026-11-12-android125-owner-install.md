# Android125 — owner in-place installation, 12 November 2026

## Result and scope

**INSTALLED_IN_PLACE**,12 November13:06:44UTC. The owner explicitly requested a phone
update. Fresh ADB readback identified the connected Redmi Note9 Pro /Android12,
ARM64, on `com.familyconnect.app.friends` versionCode123 /0.1.18-beta123. The existing
qualified signed125 APK was installed using ordinary `adb install --no-streaming -r`.
No uninstall, clear-data, downgrade, new registration, identity/key export, unrelated
package operation, server deployment or public announcement was performed.

This is installation on one owner phone, not a general rollout or completed
SUPPORT-CHAT-1 round-trip/traffic acceptance. Public APK links, invitation-page
version and updater/catalog metadata were not changed. No new artifact was built
or signed; the existing immutable125 and its prior CI/runtime evidence are reused.

## Exact artifact and provenance

- Qualified source: `b293f9ac5f2cc6fe2d11777dae97f4423e2d073a`.
- Existing hosted qualification: run43048235831; contracts/panel/Android PASS as
  recorded in the [commissioning receipt](2026-11-11-support-chat-125.md).
- Package `com.familyconnect.app.friends`, versionCode125, version0.1.18-beta125,
  minSdk27, native ARM64; compatible with the observed Android12 phone.
- APK size50,470,304 bytes; SHA256
  `f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c`.
- Original signer certificate SHA256
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Private artifact:
  `state-client-build/support-live-20261111/FamilyConnect-Test-0.1.18-beta125.apk`.

The actual installed123 APK was pulled before replacement and retained privately,
with its hash verified against the phone. Both APKs pass `apksigner verify` with
exactly one matching original certificate. Candidate package/version/ABI and16KiB
alignment pass. The first verifier attempt lacked Java in PATH; its failure is
retained. Rechecking with the existing local JDK passes; no downloaded replacement
toolchain, signing key access or modification of either artifact was needed.

## On-device checks and preservation boundary

Installation returns Success. Fresh package-manager readback reports125 and the
installed APK SHA256 exactly matches the qualified artifact. UID, first-install
timestamp and data directory match the immediately preceding123 snapshot. The
application was updated in place; Android private data was neither copied off the
phone nor reset. This preserves the ordinary Android update boundary, but these
metadata checks alone do not prove equality of every chat or cryptographic key.

Ordinary exported FriendsActivity launch reports `Status: ok`; the process stays
unchanged for30.561s and the bounded PID-scoped startup log has no FATAL EXCEPTION.
This is a bounded startup check, not a long-duration, UI-rendering or VPN test.

Pre-update UI automation could not obtain an idle hierarchy; screenshot capture
did not produce a usable image. MIUI also rejects shell input injection with
INJECT_EVENTS denial. These limitations were not bypassed or relabelled as PASS;
device security settings and USB-support consent were not changed. Automated
physical history/settings/cryptographic-identity checks are **NOT_RUN**. Prior
isolated125 preservation tests remain separate evidence, not physical acceptance.

No addressed support message or public broadcast was sent. Installation alone does
not prove enrollment of the support binding, incoming delivery, reply persistence,
ordinary-network operation without VPN, expired-subscription behavior or cold
restricted bootstrap. The remaining owner action is to open Chat, confirm retained
history/settings and authoritative enrollment, then approve the exact recipient/text
for the separate addressed round trip described in the
[RU guide](../operators/support-chat.ru.md) / [EN guide](../operators/support-chat.en.md).

## Evidence, capacity and recovery

Private0600 evidence and the pre-update APK are retained under ignored
`state-client-build/owner125-install-20261112/`. Receipts include fresh package
metadata, artifact/signature/alignment verification, installation readback and
bounded launch logs, including unsuccessful verification/UI attempts. No raw phone
identifier, private key/profile, user database or private log is committed.

Local root starts at1.7GiB free and the data partition at2.7GiB; the phone has27GiB
free. Only the approximately50MiB old public APK and small diagnostic receipts are
added; no build or cache/data/backup deletion is required. Keep the private125,
old APK, accepted release evidence and existing rollback material.

Do not uninstall or clear data to troubleshoot and do not force an ordinary
downgrade to123. The retained123 APK is evidence/recovery material, not authorization
to replace newer app data with an older schema. A corrective build needs a new,
qualified versionCode and the same signer under the normal release gates. Server
or product-DB rollback is not part of this phone update.

RU remains [RECOVERED_CAUSE_OPEN](2026-11-12-ru-recurrence.md) at its prior recovery
checkpoint; no fresh VPN/root-cause PASS follows from this installation. Confirmed
subscription notifications, payment partner, cold restricted bootstrap/recovery,
RU replacement and later Windows/Linux acceptance remain separate tracks.
