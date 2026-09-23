# Privacy notes

These are technical observations about the pilot, not a complete commercial privacy policy.
Retention rules, a public operator contact and a formal policy remain to be established.
Check [STATUS](STATUS.md) for the actual deployed versions.

## On the device

Android protects saved VPN profiles with Android Keystore-backed storage. The messenger
has a separate identity and encrypted local storage; its Android key handling is in
[ChatKeyVault.java](../clients/android/app/src/main/java/com/familyconnect/app/ChatKeyVault.java).
Loss of the required keys can make local history unrecoverable. Do not uninstall to update.
Voice recordings use private temporary files; leaving before sending cancels the draft.
Sent voice and text edits travel through the encrypted messaging path. Service announcements
are public information, not private E2E messages. Screen-lock notifications hide personal
message text; notification permission and background delivery are separate from VPN.

Windows uses a privileged broker with DPAPI and restricted storage; Linux uses platform
profile storage and privileged helpers. Protection and recovery are not identical across
platforms. [Windows details](windows-native.en.md) · [Client guide](clients.en.md).

The route map may request approximate Android location to place the device. Location is
optional for VPN use; the map is not a traceroute or a precise server-location claim.

## On the service

Registration and invitation handling use device identifiers and authorization records.
The operator must protect the product database and backups. See the dated
[registration design and privacy notes](registration.en.md) for that module's fields
and limits; do not infer that no personal or technical data is processed.

The messenger server relays/stores encrypted payloads and necessarily handles routing
and delivery metadata. Contact key verification matters; a contact identifier alone does
not prove a person's identity. [Messenger design](reticulum-messenger.ru.md) ·
[Core storage and delivery semantics](../messenger/README.ru.md).

A VPN gateway terminates the tunnel. It can observe destination metadata, timing and
traffic volumes; end-to-end application encryption such as HTTPS remains important.
The project makes no anonymity, traffic-correlation resistance or zero-logging promise.

## Before sharing diagnostics

Remove private keys, profiles, invitation URLs/codes, activation files, chat content and
personal identifiers. Report version, OS, network type, reproduction steps and a redacted
error. See [SECURITY.md](../SECURITY.md) for sensitive reports.
