# Addressed support conversation

Use the existing operator account at `http://127.0.0.1:8765/`. Open a production
device card and select **«Сообщения · личная поддержка»**. Replies are listed at
`/messages/`. This is separate from `/system-messages/`, which broadcasts to the
entire selected platform audience.

The recipient is an authoritative device identity ↔ chat identity binding, never
a device name or IP address. Missing, ambiguous, revoked or stale bindings block
sending. beta123 does not enroll into this support contract; compatible beta125
is public since13 November for in-place updating. Never copy the phone's private
key into the panel.

Queued means durably stored by the sender; mailbox accepted means server receipt;
recipient stored means a signed ACK after Android storage. There is no read receipt.
A permanent backend receives replies while the browser is closed. After an unknown
send outcome, retry the same form/text/ID rather than creating another message.

## Owner's physical acceptance

Signed ARM64 beta125 /0.1.18-beta125 was installed over123 on the owner's phone on
12 November. Signer, installed bytes, UID, first-install timestamp, data directory
and ordinary launch checks pass. These exact APK bytes became public on13 November
without a rebuild. Retained local artifact:
`state-client-build/support-live-20261111/FamilyConnect-Test-0.1.18-beta125.apk`.
Size50,470,304 bytes; SHA256
`f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c`.
Public catalog8, both invitation paths and the APK link now offer125.
[Download and publication receipt](../releases/2026-11-13-android125-publication.md).

On12 November the owner confirms exchange; panel readback corroborates one verified
addressed thread, an outgoing signed storage ACK and one durably received reply.
The core panel↔phone round trip is confirmed; no reinstall or reenrollment is needed.
The owner confirms the tunnel was OFF during that exchange; this physical condition
is accepted without a rerun. Network type and complete old-history/settings
preservation are not established; MIUI blocked automated UI inspection.
For any new live test approve its text and verify
the canonical recipient binding; do not send a duplicate merely to repeat acceptance.

Ordinary Wi-Fi and an expired synthetic subscription were checked in isolation;
cold no-cache startup on allowlisted networks is still a separate field gate.
Production announcement delivery needs separate approval of exact text and computed
audience. Selecting Android is a platform-wide broadcast, not a one-device test.

Current evidence, limitations and recovery:
[12 November phone installation](../releases/2026-11-12-android125-owner-install.md),
[125 receipt](../releases/2026-11-11-support-chat-125.md),
[STATUS](../STATUS.md), [PLAN](../PLAN.md).
