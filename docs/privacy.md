# Privacy notes

These are technical observations about the pilot, not a complete commercial privacy policy.
General retention rules outside the explicit technical-information limits below,
a public operator contact and a formal policy remain to be established.
Check [STATUS](STATUS.md) for the actual deployed versions.

## Basic candidate v2 — source only, not publicly enabled

The separate basic candidate removes the support enable switch: after ordinary setup it shows
a short notice before the first new sample. Acknowledging that notice is **not consent**.
Its automatic processing mode is `automatic_basic`, policy `basic-2026-11-v1`; the server receipt
uses `consent=not_requested`, never `enabled`. All public build types keep automatic activation
disabled pending the field-by-field processing-basis review and operational deployment gates in
[the candidate contract](operators/basic-metadata-v2.md). This does not change the deployed126
opt-in description below. No current production schema, writer or source binding is changed.

Basic includes OS/app version, connection type, SIM/registered-network names as distinct sourced
observations, actual transport/gateway and bounded error, and ASN/organization from a qualified
ephemeral server observation. It excludes model/manufacturer, radio detail, readiness detail and
all country/region/city enrichment. City lookup is not invoked for basic; no raw IP/history is added.
Latest-only observations expire within seven days. Payload-free replay/revocation floors remain
for the device lifetime. Support → Privacy offers an objection/disable action; offline revoke
remains pending. VPN, payment, updates and support do not depend on metadata acceptance.

## On the device

Public Android126 technical information uses new, separate,
explicit opt-in, off by default; old seven-day diagnostics consent is not reused.
When enabled it collects model/OS/app, network type, available SIM and registered-network names,
radio category, actual VPN/session/gateway, limited error/readiness and approximate
IP-derived country/region/city/ASN. No phone number, GPS coordinates, IMEI, serial,
advertising ID, SSID/BSSID, cell ID, contacts, installed-app lists, sites, traffic,
messages, keys or tokens are added to this telemetry. Existing split tunnelling is
unchanged. It is support information, never identity/payment/access authority.
Radio detail uses Android33+ normal READ_BASIC_PHONE_STATE (no runtime permission
prompt); older Android or unavailable telephony exposes an explicit reason instead.
No READ_PHONE_STATE dangerous permission is added or requested.
Consent lasts until disabled. Hardware and dynamic observations expire independently
within seven days; no location history. Off stops new collection/upload; the server
deletes the payload on receipt of the revoke. Offline revocation is shown as pending.
Minimal consent/sequence tombstones last for the device lifetime to prevent delayed
resurrection; they contain no device/network/geographic payload. The current metadata
database and panel projection must not enter indefinite backups or append-only logs.
The compatible server/collector/panel path and public126 are deployed; installed
opt-in/revoke/deletion acceptance passes. Previous125 downloads/admissions remain.
[Public release and bounded acceptance](releases/2026-11-16-android126-publication.md).
Current qualified geographic sources are recent RU/AWG and NL1/NL2 AWG
peer endpoints joined through the authenticated device's canonical AWG key, with exact source
archive and current transport-state binding. TCP and MESH have no qualified direct-IP source
in this collector: show unavailable or an older
suitable observation with its own age. Ordinary HTTP/VPN-exit/relay addresses do
not establish the client's city. Local DB-IP Lite supplies network geography/ASN,
not GPS, retail ISP certainty or proof of a person's physical location; an upstream
third-party VPN can affect even a qualified peer observation. No raw IP/coordinates
are retained in the metadata projection, logs or history. DB-IP attribution remains
visible beside results; database version and SHA256 describe local integrity, not
a vendor signature. Missing/stale GeoIP does not block VPN, payments or support.

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
