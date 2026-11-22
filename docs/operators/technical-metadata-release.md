# Technical metadata: minimal delivery and recovery

**22 November20:57UTC — NL/AWG collector and reason labels installed.**
The external collector now supports both NL gateways without gateway runtime changes
or copying GeoIP databases. A pinned node/key/handshake observation is followed by a
fresh canonical consent/session read and central lookup. The original45s overall
deadline remains. NL2 live city/ASN and three normal imports are verified; NL1 has
controlled coverage only. Missing reports are not treated as denied consent, while
an explicit revoke clears observations. Retained cities are independently aged and
approximate; TCP/MESH and desktop OS reporting remain outside this change.

Use the [22 November receipt and exercised rollback](../releases/2026-11-22-nl-geoip.md)
for current panel5ce82415 and the two external collector preimages. Do not rerun the
initial14-file metadata overlay or old migrations/signing steps below. Restore only
the previous5ae92f8c presentation image/collector files if needed, preserving the full
effective Compose chain, current stores, consent epochs and HMAC2 aliases. Concurrent
network-probe/audit appends must be verified separately from unchanged old row hashes.
Public Android126/catalog9 is unchanged; later dated sections below are historical.

**22:47UTC update: PR38 merged7123b95e after qualified588e793a checks.** A later
readback finds a new22:07UTC RU watchdog cascade. Public files/catalog9, metadata API,
HMAC2 and protected support state are not rolled back; RU AWG/TCP are down. Source
merge is not a runtime recovery. Do not repeat signing/device/HMAC/metadata deployment
or weaken service deadlines to address this separate incident.
[Bounded incident receipt](../releases/2026-11-16-ru-recurrence.md#new-recurrence--16-november2207utc).

**Current16 November20:42UTC: PUBLIC126 / optional catalog9.** Accepted installed-device
network/restart/revoke/restoration and RU/AWG geography gates are complete within the
recorded scope. Public APK/source/audio/signature/Range, both invitations and legacy
discovery pass. No repeated signing/server deployment is required. Preserve sequence9
and immutable bytes; use the journal/compatible ingress for recovery, never an old DB
or key. [Publication and exact acceptance](../releases/2026-11-16-android126-publication.md).
Dated preparation instructions below retain their historical context.

Current receipt: [15 November](../releases/2026-11-15-device-technical-metadata.md).
This is not RU recovery, HMAC rotation or permission to install all of PR38.
Generation2 and the accepted RU recovery are the base. Public125 remains supported.

Installed-chain checkpoint16 November14:49UTC: corrected signed4f288cbb reaches its
original generation2 card after explicit consent, with exact canonical/imported
observations and independent Android/Wi-Fi checks. Real UI1440/390px passes. Observed
AWG/NL1 Wi-Fi does not qualify a city: only the prepared RU/AWG peer source does.
Actual Russia/AWG acceptance now binds the device's canonical AWG key to one fresh
peer and local DB-IP Lite2026-11; required geographic/ASN fields match the real panel.
The raw endpoint remains transient inside the collector process, not evidence/logs.
This confirms database lookup provenance, not physical location. NL/TCP/MESH remain
unqualified. Finish network/revoke tests, then restore the initial NL1/consent state.
Do not treat a latest-report/collector-cycle lag as refreshed old observations.

For native cancellation qualification, `Session.Done()` signals cancellation, not
completed underlying `Close()`. A blocked-write harness must observe actual transport
closure before releasing that write and asserting its error. Retain the existing
deadline/error/bound-cleanup assertions; do not extend timeouts or weaken them.
The current correction changes only the test harness. Frozen APK/source provenance
and loaded paid descriptor are unchanged; hosted corrected-head CI is still required.

## Qualified boundaries

- HTTP: `scripts/package_technical_metadata_overlay.py` changes only
  `friends_http.py`, `control/friends/access.py` and adds the metadata/GeoIP modules.
  Pin the actually serving archive, not the inactive legacy HTTP unit. Preserve
  every other ZIP member, particularly paid policy/support/recovery.
- Panel: `scripts/package_metadata_panel_overlay.py` starts with the accepted
  alias-aware imagee44c3423, checks six old file hashes, preserves both existing
  importers and `pseudonyms.py`, adds fourteen metadata files and query-free logging.
  Compare every other `/app` member. Never use the pre-HMAC metadata image5051f0e7.
- Before recreation, run `validate_deployment` against **actual Docker inspect**,
  candidate image configuration and fully resolved Compose. A self-consistent
  reconstructed Compose is insufficient: it can omit the existing HMAC override.
  Retain the actual config-file label chain, environment, UID/groups, volumes and
  read-only `/run/fc-pseudonym-aliases.json` mount. No `seed_demo` startup.
- Monitor delta is only the independent bounded metadata collection/import block.
  Keep current inventory/subscription paths, key and alias normalization unchanged.
  Metadata source configuration pins the current HTTP archive and dedicated GeoIP
  Python environment; it contains no client IP or identity mapping.
- When the serving HTTP archive changes, inspect **both** private subscriptions and
  metadata source pins. Updating only the new metadata source leaves subscriptions
  fail-closed on the previous archive. Verify the accepted archive provenance and
  live hash, back up/roundtrip the configuration, drain only the local monitor under
  its normal lock, then atomically update the exact pin with other fields/owner/mode
  preserved. Resume normal cycles and require subscription source `ok` with the
  expected archive hash and preserved handles/events, not just importer exit0.
  Retain a mismatched-pin negative check; never remove the digest guard. This
  configuration-only repair needs no server restart, image rebuild or DB restore.

## Preflight and backups

1. Re-read live HTTP/node/reconciler hashes, panel image, service states, effective
   config and disk capacity. Accept the separate RU receipt; do not redo recovery.
2. Snapshot canonical SQLite with the backup API; check integrity/FKs and full table
   fingerprints in an isolated copy. Preserve configs and previous runtime bytes.
   Keep encrypted off-host backup and its key separately, outside Git/CI/output.
3. Take a consistent panel `pg_dump` and restore to an isolated PostgreSQL with no
   external network/ports. Wait for TCP readiness, not the temporary init socket.
   Size tmpfs/memory from current database size, including restore indexes/WAL.
   Apply candidate migrations; compare protected table contents and preserve
   immutable snapshot/event/audit digests. Exclude `console_technicalmetadata*`
   data from long-lived dumps; never copy the latest payload into history/audit.
4. Run exact overlay HTTP/real-nginx tests and generation-aware panel/retention
   checks. Keep the original public125 APK/hash/signer, not a rebuilt substitute.

## Installation order

1. Stage the verified local DB-IP Lite pair centrally under
   `/opt/apps/family_connect/geoip`, using `scripts/update_geoip.py` and the pinned
   GeoIP lock. Check at least1536MiB free for staging/rollback. Installer retains one
   previous pair and atomically replaces `current.json`; inspect `update-status.json`
   after any failure. Monthly updates use the same bounded tool, never a client-IP
   external API. A stale/missing/corrupt database must remain an unavailable reason.
2. Back up and patch the **loaded** nginx configuration. Current ingress is the
   `family-connect-product-https` container, `nginx -c /etc/fc/nginx.conf`, whose
   directory mount is read-only. The host file is under `state-product-https/config`.
   Add the exact metadata location to the8443 TLS server and test using that same
   container/config. Host-default `nginx -T` is not a check of this ingress.
3. Atomically install the four-member HTTP overlay; restart only
   `family-connect-friends-http-candidate.service`. Verify18086, negative auth and
   loaded archive, then reload the verified nginx configuration. Keep metadata
   access logging off and error logging `/dev/null`; do not trust forwarded IP
   headers for client city. No VPN/watcher/paid reconciler restart.
4. Pause only the local read-only monitor timer; let its current cycle drain and
   acquire its normal lock. Recreate **console only**, with the actual HMAC override
   followed by the metadata override, no dependency recreation/build/seed. Apply
   additive migrations0014/0015; preserve database volume and all other services.
   Validate actual environment/mounts/user/groups again before resuming imports.
5. Install the three monitor/collector files and private source pin. Keep generation2
   key/manifest unchanged. Local monitor timeout500s covers the bounded optional
   path; this is not a RU service timeout change. Resume timer and observe at least
   three complete normal cycles; require metadata source `ok`, not merely an
   importer exit0 for an unavailable export. Check existing device handles/events.
6. Check authenticated real cards at1440/390px and query-free loaded logging.
   Snapshot digests and names must survive. Support store bytes can change during
   ordinary binding refresh: compare consistent decrypted records in-process,
   excluding only binding sequence/expiry, not identity pins, requests, messages,
   baseline/cursor/jobs or ACK state. Never print record IDs/content/keys/mappings.

## Release gates still separate

The server may serve old clients before126 is released. Do not add a placeholder
paid descriptor, publish an unsigned APK or reinterpret server readiness as an
installed-device result. Sign the exact qualified CI artifact via the existing
KeePassXC signer and certificate pin, then retain immutable signed bytes. Verify
original125→126 in-place on compatible ARM64 with unchanged identity/activation,
settings/support/subscription and new consent OFF. No ARM64-on-x86 translation
workaround or recompiled125. Owner password input stays in the local dialog.

Only after the signed descriptor's isolated payment/renewal/grace/replay checks,
load that exact policy in HTTP/operator/reconciler, retaining108/119/123/125.
For this126 release, original125→126 device acceptance also precedes that loading;
the exact source descriptor and isolated tests may be prepared without ADB.
Then prove enabled installed126 → API → generation2 collector → real panel and
revocation/cleanup. RU/AWG is the only qualified IP-source design in this release;
NL/TCP and MESH city remain unavailable or independently age-labelled. Controlled
MMDB resolver lookups are database checks, not observed device geography.

Publish the same signed APK/audio source, increasing signed discovery sequence,
legacy descriptor and both invitation paths only after those gates. Verify full
HTTPS bytes, signature/package/signer/code, Range/resume and updater behavior.

If a later mandatory gate proves an Android/native defect also present in the
frozen candidate, keep its signed bytes and acceptance receipt immutable but block
publication. Do not transfer corrected-source CI results to that file or silently
re-sign it. Qualify a distinct replacement candidate with explicit provenance,
hash/signature and exact paid descriptor, then repeat the affected installed gates.
The16November batch/credential-renewal race is such a blocker, not an excuse to
rebuild the already accepted metadata server or repeat HMAC/RU recovery.

### Guarded public delivery

Historical17:41UTC boundary: the corrected4f288cbb artifact and complete f781c77e CI
are accepted; the original native race is no longer its open gate. Publication at
that time is held by the separate new RU outage, not signing or phone consent. See the
[17:41UTC receipt](../releases/2026-11-15-device-technical-metadata.md#restoration-ci-and-pre-publication-stop--16-november1741utc).

1. Require a fresh accepted runtime/service baseline and unchanged paid/HMAC pins.
   A changed HTTP PID may be a scheduled credential-renewal barrier: reconcile the
   successful renewal receipt, its configured service list, bounded manager stop/start
   events and actually loaded archive before refreshing that single PID guard. Do not
   infer a new deployment or RU recovery from PID alone. Failed AWG/TCP/watch guards
   stop publication; do not refresh them to the failed state or weaken assertions.
2. Check actual ingress container/image/arguments and read-only directory mount.
   Preserve the installed privacy-aware configuration, not an older nginx template.
   Snapshot the four exact live files with owner/mode/hash and verify an isolated
   restore. Keep a protected intent/completion journal; never erase it to retry.
3. Stage immutable APK/full source/audio with exact hashes and exclusive creation.
   Validate route-only configuration inside the actual nginx container, then expose
   assets with the first reload, leaving current invitations/catalog/CSP unchanged.
   Verify full trusted-HTTPS bytes, APK identity/signature,206/416 and resume behavior.
4. Validate final invitation/CSP configuration, record intent and perform the second
   reload. Install matching legacy discovery, then the signed catalog last. Verify
   both invitation paths, signature/sequence/hash/size and original125 updater protocol.
   Keep physical UI installation evidence separate from protocol/HTTP results.
5. If an intent lacks a completion receipt, inspect the actual files and nginx state
   before any retry. Keep immutable assets and all new user data; restore only a
   qualified compatible ingress configuration if necessary. Once a signed sequence
   has been exposed, recovery must not lower it. No database/key rollback, transport
   restart, rebuild or automatic user broadcast is part of this publication.

The isolated publication scenarios cover concurrent-change rejection, interrupted
reload/replay guards, invalid syntax and backup/restore on the successful two-phase
path. At17:41UTC the production journal is absent: both guarded attempts stopped
before initialization, so there is no partially installed publication to recover.

## Owner-assisted signing and device session

### Final restoration and updater protocol scope

After a separately accepted service recovery, take one short fresh readback of runtime
pins/HMAC2 and phone state; do not repeat recovery or assume an old OFF receipt is the
current preference. Preserve later consent epochs and distinguish a new authenticated
enable from delayed old-report resurrection. If normal ADB input returns INJECT_EVENTS,
request the specific owner toggle/navigation; do not bypass MIUI or keep re-requesting
an already granted USB connection. Restore original consent/country/network state and
verify resulting server/panel cleanup before closing the phone session.

With only the upgraded phone available, never downgrade/clear it to manufacture a125
updater result. Verify original125 updater source equivalence and run its parser,
signature/sequence policy and bounded download validation against exact release bytes;
label that JVM/protocol evidence separately from Android instrumentation and physical
installation. Repeat public HTTPS/hash/Range verification after actual publication.
An Android job PASS does not imply the whole source workflow or a newer documentation
head PASS. Keep artifact-source, test correction, documentation head and merge results
distinct. [16 November evidence](../releases/2026-11-15-device-technical-metadata.md#delivery-resumption-and-updater125-protocol--16-november1635utc).

### Existing signing and device procedure

Signing and exact signed-descriptor isolated qualification do not require ADB.
The selected126 is now signed and frozen in the current receipt; reuse those bytes,
do not repeat signing. The sequence below also documents future signing sessions.
Discover only known database-location settings or bounded `.kdbx` filenames; never
dump private configuration or search secret contents. Multiple/unconfirmed candidates
require explicit local selection. Cancellation stops the attempt; repeat only at the
owner's request, without silently changing databases.

1. Connect one authorized ARM64 Android device with original public125 by USB.
   Enable Developer options → USB debugging, unlock it and approve this computer's
   debugging prompt. Do not uninstall Family Connect, clear storage or reset keys.
   Classify the actual `adb devices -l` result before requesting an owner action:
   - Empty: check USB enumeration, the selected ADB binary/server and local USB
     permissions. The MIUI security-debugging switch is not a general fix for an
     absent USB/ADB connection; do not reset unrelated devices or ADB sessions.
   - `unauthorized`: ask the owner to unlock the phone and approve this host's RSA
     prompt. Do not confuse this with a permission to inject UI input.
   - `device`: verify the selected device and current app, then test permitted UI
     input separately. Multiple devices require an explicit selection.
   - `device` with SecurityException/INJECT_EVENTS: USB works, but MIUI rejects
     automatic input. The owner may enable USB debugging (Security settings);
     verify the permission after the owner's restart, not merely their toggle.
     Test a harmless actual tap on a known app navigation target: successful
     KEYCODE_WAKEUP alone is insufficient. Do not keep rebooting when taps still
     fail after one completed restart.
     Otherwise use specific owner-performed taps and distinguish owner-observed
     evidence from an automated comparison. Never disable MIUI optimization.
   No translation workaround, uninstall, downgrade or clear-data. A blocked screen
   capture or hierarchy dump is not proof of missing app data. Friends and chat
   windows use FLAG_SECURE; do not remove/bypass it to obtain acceptance evidence.
   Prefer bounded read-only public Android UI observations and authenticated
   canonical comparisons, without exporting Keystore keys or posting IDs/messages.
   An optional disposable read-only instrumentation probe must be a separate
   permissionless/no-network test package, restricted to this app's public UI
   nodes. It must not read the app's private files or inject actions as a workaround
   for denied shell input. Keep evidence local/private; remove only that temporary
   probe when no longer needed. Do not replace/re-sign the production APK.
   If the owner declines data-entry forms, stop those forms. Request only the
   concrete on-device navigation/unlock that cannot be performed with the available
   permissions; the assistant can read/compare the resulting screen privately.
   If the owner also declines repeated navigation taps, stop that workflow and
   finish independent qualification rather than repeatedly asking the same thing.
   In-app USB support is a separate, temporary provider grant: status/snapshot
   success does not authorize Android input injection or change metadata consent.
   Its existing connect operation requires MESH already selected; it cannot select
   RU/AWG, open arbitrary dialogs or toggle technical consent. Do not expand this
   endpoint or rebuild the frozen candidate to get around an acceptance blocker.
   The existing exported FriendsActivity supports its normal navigation extras:
   integer `tab` (1 chats,3 options) and boolean `subscription_access` (read view).
   These can reduce owner navigation without touch injection; they do not authorize
   other extras/private activities, change consent, select a peer or connect VPN.
   A read-only probe receipt must say `captured_read_only` before reading its file;
   an exit0 alone can leave an older capture after a non-target/unavailable result.
   Confirm the expected screen, not just a successful activity launch.
   A contact-list preview is not a full local history or pinned-key comparison.
   Record package verification separately from UI/data-preservation acceptance.
   Compare rendered multiline subscription summaries by their public status
   fragments, not equality with a single resource string. For per-app policy,
   compare the mode spinner and complete saved selected-only set separately from
   the category filter. Keep observed history-page scope distinct from a full DB
   comparison. Never interpret a reader-shape mismatch as lost application data.
   Evidence summaries must construct an explicit scalar allowlist: type-check
   booleans/integers and compute counts with len(), rather than printing a field
   whose name merely sounds like a count. A saved history_rows field can contain
   message/date/status arrays. Compare those privately and publish only equality,
   uniqueness/order/pairing results and the observed scope. Do not print lists,
   private text, identifiers, arbitrary receipt values or exception arguments.
2. Select the existing release KeePassXC vault in the local signing dialog and
   unlock it there. Do not send its password, key or recovery attachment in chat.
   Follow the [vault signer procedure](../android-vault-signing.ru.md); pin the
   original certificate and the qualified unsigned artifact recorded in the receipt.
   Disposable synthetic-vault tests do not authorize replacing the production key.
3. Before installation, retain bounded private evidence of the original package/
   signer, identity proof and activation, settings, existing support contacts/history
   and subscription. Keep raw identifiers outside Git/logs; do not create messages,
   payments or new expiry terms as fixtures. Observe current baseline, not old counts.
4. Install the frozen signed126 over125 through the normal Android confirmation,
   without removal/clear-data. Compare the same evidence, restart and verify new
   metadata consent is OFF. Do not infer retained keystore identity from app name.
5. Only then enable the new consent deliberately and observe the complete production
   chain and real fields. Record actual underlay/session and qualified RU/AWG lookup;
   test available network changes, restart, offline revoke/pending state and online
   cleanup. Preserve consent epochs/tombstones; never inject synthetic production
   observations to fill a card. All screenshots/identity comparisons remain private.
6. After all required phone checks, agree with the owner on restoring temporary USB
   debugging/security-debugging settings to their original state. Do not disable
   them while the acceptance session still requires the connection.

## Recovery without losing new data

### Exact paid126 layer accepted16 November

The independently qualified signed4f288cbb candidate has exact policy
`android-paid-108-119-123-125-126-v2` loaded in HTTP4e2df679, operator19efd0b4 and
reconcilerff4601aa. See the [paid loading receipt](../releases/2026-11-15-device-technical-metadata.md#exact-paid-loading-and-local-pin--16-november1404utc)
for full hashes and preserved-state checks. This is not permission to replace the
immutable APK or publish before the remaining installed acceptance gates.

For any later correction, derive paths from actual serving processes/effective units
and compare exact live hashes. The operator current path is a root-owned symlink to
the accepted runtime archive: validate its exact resolution/hash/target owner and
preserve that link. Do not treat an unchecked symlink as a regular replacement target.
Archive overlays change only the qualified paid module; retain metadata, identity,
support and HMAC members. Pause/drain only the local monitor and preserve its lock;
keep reconciler renewal/timers and VPN/watch services running. Restart only independent
HTTP. Update both subscription and technical-metadata source pins together, retaining
all other fields/permissions, before resuming the monitor. Confirm normal import cycles.

Preservation comparison must distinguish mutable progress and append-only additions
from corruption: compare all protected canonical domains; explain challenge/sequence
changes; verify old panel row/digests as historical prefixes when new normal imports
append snapshots/audit rows. Do not delete new rows to force whole-table equality.
Use the existing protected backup/restore evidence, and record real service PIDs,
new normal reconciliation, source hashes, support IPC and original cursor/anchor.
Policy-only recovery must retain metadata-aware code, generation2 and all current
data/tombstones; restoring a backup database is never the code rollback procedure.

### Installed offline-revoke acceptance

Verify the device really has no active default network before accepting OFF/pending.
Do not call offline state server deletion. Preserve the pending revoke across a normal
process restart without clearing data. After connectivity returns, allow the bounded
retry schedule and normal importer to advance; do not turn consent ON to force upload.
Require canonical enabled=false with the new epoch/sequence and empty payload, then
the same original generation2 panel handle with revoked consent, empty groups and no
GeoIP. Reopen settings normally to refresh the visible status after asynchronous
delivery, then verify OFF/no pending persists across a new process. Check tombstones
stay unchanged over normal cycles; isolated stale-report/TTL tests are separate from
observed production behavior. In browser checks, select the exact handle before
testing presence: the unfiltered inventory is paginated. Metadata-only model/city
filters must stop matching after cleanup, while history/navigation remain available.

### General data-preserving recovery

Keep generation2, aliases, canonical operations, metadata epochs/sequences/tombstones
and all newer user data. Never restore an old database over live operations, reactivate
the retired HMAC key, recreate notification baseline or restart VPN for metadata.
If Compose checks fail, retain monitor pause and repair the missing override before
imports. The15November correction reinstated the exact existing HMAC override and
recreated only console; the original encrypted store and database volume stayed put.
Retain the metadata-aware HTTP overlay and compatible panel image as forward-repair
anchors. Correct configuration or redeploy those exact qualified bytes; additive
metadata tables need not be rolled back. If a code rollback is necessary, it must
still enforce revoke/TTL and generation2, not silently discard the compatibility
layer. Any long-lived backup of canonical storage excludes metadata payloads;
preserve anti-resurrection state without retaining location/history snapshots.
