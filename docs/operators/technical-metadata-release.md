# Technical metadata: minimal delivery and recovery

Current receipt: [15 November](../releases/2026-11-15-device-technical-metadata.md).
This is not RU recovery, HMAC rotation or permission to install all of PR38.
Generation2 and the accepted RU recovery are the base. Public125 remains supported.

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
Then prove enabled installed126 → API → generation2 collector → real panel and
revocation/cleanup. RU/AWG is the only qualified IP-source design in this release;
NL/TCP and MESH city remain unavailable or independently age-labelled. Controlled
MMDB resolver lookups are database checks, not observed device geography.

Publish the same signed APK/audio source, increasing signed discovery sequence,
legacy descriptor and both invitation paths only after those gates. Verify full
HTTPS bytes, signature/package/signer/code, Range/resume and updater behavior.

## Recovery without losing new data

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
