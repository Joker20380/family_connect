# Automatic basic technical data — separate, non-public candidate

This is Part B, separate from HA-02. Do not install its server/console migrations or clients
inside A's qualification/capture. A continues using its accepted source/image closures. This
candidate is not published, signed for release, or evidence of a completed HA recovery kit.

## User experience and processing contract

Ordinary setup leads to an informational disclosure before any basic sample, without a support
enable switch. «Понятно / Understood» records notice delivery, **not consent**. Back/Cancel leaves
NOTICE_PENDING and no collection. «Возражаю / Object» and Support → Privacy stop collection and
queue a payload-free revoke. These choices do not gate VPN, payment, updates or support. Existing
optional diagnostic controls remain independent. A review/resume after objection requires the
previous revoke acknowledgment first, then a new notice; the epoch is never raised to bypass it.

28 November native candidate checks use an isolated `.metadata` package, NVIDIA host GPU and KVM.
Disclosure is invoked onPostResume, not only onCreate: Back keeps NOTICE_PENDING, and returning
to the same activity shows it again before sampling. The synchronized old-APK regression fails;
the fixed UI passes. Native SharedPreferences/AtomicFile checks cover init/notice/reserve/ACK
failure before and after publication, separate-process reopen, oldOFF/revoke and missing binding.
After Understood, the real consumer reserves only after storing notice, rejects absent synthetic
identity locally and retains backoff/VPN status. No authenticated synthetic backend transmission,
VPN traffic independence or production-package/signature upgrade acceptance is implied.

Wire schema2 on the existing authenticated `/friends/device/technical-metadata/v1` endpoint:
`processing_mode=automatic_basic`, `policy_version=basic-2026-11-v1`, receipt
`consent=not_requested`. The retained `consent_epoch` wire name is only the monotonic decision
generation for v2, not proof of consent. Existing identity/proof digest, rate limits, bounded
integers, backoff, freshness and same-generation replay/revoke protection remain. New sample bytes
are strict: extended fields are rejected, not silently dropped. Old v1 clients remain compatible
with the new server for identities not transitioned to basic. Once basic is accepted, a late or
restored v1 sample cannot downgrade that identity back to extended, even with a higher epoch;
payload-free v1 revokes preserve the basic policy floor. Old v1 servers reject schema2; the new client backs off without falling back
to an extended v1 sample or affecting VPN. Revokes intentionally use payload-free v1 for backwards
compatibility. The canonical synthetic PG repository explicitly refuses v2 until separately
migrated; this change supports the actual SQLite metadata endpoint, not an HA-03 database cutover.

## Fields, sources, retention and release basis

| Basic field | Purpose | Actual source and UNKNOWN rule | Retention | Processing basis / release condition |
| --- | --- | --- | --- | --- |
| Android OS/version, app version | Version-specific support/compatibility | Build/package APIs; null has bounded reason/status | Latest only, up to7 days | Owner/controller must document necessity, applicable jurisdiction and basis; not presumed consent |
| Connection type | Explain active connection failures | Default non-VPN network or unambiguous VPN underlay capabilities; ambiguous remains UNKNOWN | Same | Same necessity/basis assessment; notice and objection required |
| SIM operator | Distinguish subscription operator | Public TelephonyManager for default data SIM; no SIM/permission/service reason | Same | Separate necessity and local-law review; public activation blocked pending review |
| Registered network | Distinguish actual registered operator | Public network operator for same subscription; absent/ambiguous UNKNOWN | Same | Same separate review; never inferred from SIM or ASN |
| Actual transport/gateway/state, bounded error/time | Explain current transport outcome | ConnectionService/ConnectionTerminal, not preferred route; old error expires | Same | Necessity/proportionality and error-category review required |
| ASN/organization | Identify network-level compatibility | Local pinned DB-IP ASN database from fresh authenticated RU/NL1/NL2 AWG peer; TCP/MESH relay/service IP is not substituted | Same; full IP ephemeral, never stored in metadata | Network observation's lawful basis and objection handling must be documented; no external GeoIP service |

«For quality of service» is not a completed legal basis. Until this table's required decisions and
store disclosures are accepted, `BASIC_METADATA_APPROVED=false` in friends/release. Only a separate
debug application ID `.metadata` accepts `-PfcBasicMetadataCandidate=true` for qualification.
This is a compile-time release safeguard, not the removed user-facing enable switch.
Model/manufacturer, detailed geography, radio and readiness are outside automatic basic. No phone
number, IMEI, SSID/BSSID, cell IDs, app lists, messages, payloads, browsing, GPS or location/IP history.

## Durable initialization and migration

Before collecting, one synchronous preferences commit stores contract, processing state, positive
epoch/sequence and a random no-backup installation binding. Every upload reserves its sequence
synchronously before sampling. A commit failure immediately closes collection; a separate local
no-backup storage-fault marker attempts to preserve that refusal across restart. If both storage
mechanisms fail no software can claim a durable write: the client remains disabled in the process,
and storage recovery is a release acceptance item, not a fake successful revoke.

| Prior state | Transition |
| --- | --- |
| Proven fresh package install, no identity/metadata, firstInstall=lastUpdate | FRESH → NOTICE_PENDING; positive counters committed first |
| Legacy enabled=true with existing counters | LEGACY_ENABLED → NOTICE_PENDING; same epoch, never auto-extended |
| Legacy explicit disabled/refused | OFF, never enabled by migration/notice |
| revoke_pending | Preserve original epoch and pending revoke; no sample or resume before ACK |
| epoch0 with pending revoke, invalid counters or storage failure | STORAGE_FAULT; no sample |
| Old installation with no saved decision (including old Cancel/Back) | LEGACY_UNDECIDED → basic notice; absence is not fresh-install evidence or consent |
| Restored v2 preferences with missing/different no-backup binding | RESTORED_BLOCKED; no sample/epoch escape; existing pending revoke may finish |

Android backup remains disabled; restoration of arbitrary raw filesystem/Keystore clones is not
proved by the binding check. A normal app-data restore must not silently recover the notice as
authority for another installation. Storage/restore UI recovery and native platform tests must
be completed before public release. Clearing app data/uninstall is not a recommended recovery.

## Server, collector and console rollout (NOT EXECUTED)

**Deployment gate: CLOSED.** Installed-v1 SQLite has user_version=0 and seven metadata columns.
Request/read/retention never migrates it. V2 samples on that schema fail without changing its
schema. The disposable B fixture explicitly migrates to user_version=2 and nine columns; this is
not a production migration entrypoint. Installed A capture/import rejects it as unsupported.
Before deploying B API, any migration, collectors or console0016, qualify a separate versioned
HA contract with capture/restore of policy, revoke, replay floors and original expiry. The Android
public flag is not a server migration barrier. No accepted importer allowlist/pins are widened.

The candidate SQLite schema adds explicit processing_mode/policy_version columns; tombstones contain
no observations. Console migration0016 adds the same policy identity. Collectors pass these fields
without translating them into consent; basic queries ASN only, never city. Panel rejects basic
rows containing geography/extended fields, displays source/reason/age and distinguishes UNKNOWN
from not collected. Transition to basic must not reuse an earlier extended geographic projection.
Seven-day expiry is retained during projections/restore, not renewed from old bytes.

Deploy only after A completes and exact source/image bindings are renewed: qualified API/collector/
console first, then a new separately accepted signed client release. The current twelve-file A
overlays are immutable history, not this candidate's closure. Preserve database prestate and replay
floors; rollback to v1 source must first stop v2 admission/collection and use a reviewed migration,
not silently interpret automatic rows as opted-in extended data. No production rollback is executed
in this source task.

## Draft store disclosure, not a submitted declaration

For this candidate: basic OS/app/network/operator/transport/error and network ASN information,
linked through existing device identity, for technical support/compatibility; encrypted in transit;
latest observations up to7 days; no advertising/sale/third-party analytics, precise location or
browsing/message content added. Users can object in Privacy; offline deletion waits for delivery.
Minimal payload-free anti-replay floors last with device registration. Exact Google Play/other
store category mapping, legal basis and deletion/contact disclosures need owner review before
submission; no store form or public privacy-policy acceptance is claimed here.
