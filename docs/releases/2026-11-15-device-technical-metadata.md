# DEVICE-TECHNICAL-METADATA-1 — 15 November 2026

## State

IN_PROGRESS / NOT_DEPLOYED / NOT_USER_READY. This is the selected product work,
not recorder architecture or production failure-writer work. RU CAUSE_OPEN and
PR36 NO_GO_PREFLIGHT remain. PR37 sourcea5067ae2 and merge53a780d9 are the entry
baseline, not qualification of this change. No delegated agents.

Remote main53a780d9ccfcdb2c3ec6141a197917190f9be7a5 verified by fetch. Primary
checkout8937e71e has unrelated modified/untracked files and diverged history;
all preserved. Worktree branch: feature/device-technical-metadata-20261115.

## Observed ingress and deployment boundary

Read-only authorized RU inspection: TLS nginx listens8443; Friends routes proxy
to loopback18086, NOT the inactive legacy18084 unit. Current Friends locations
do not overwrite a client-address header. Therefore neither self.client_address
nor arbitrary X-Forwarded-For is suitable for city attribution. No header, route,
service, policy or production data has been changed. RU filesystem available7514MiB
at entry; recheck before any GeoIP staging (including rollback space).

Latest prior verified paid rollout uses exact108/119/123/125 descriptors and
separate HTTP/operator/reconciler archives; reuse their actual runtime baseline,
not arbitrary main. Fresh baseline and consistent private backups/restoration
checks are required immediately before deployment; historical64/118 counts are
not today's acceptance expectations. No production payment/period changes.

## Contract and retention design

New versioned endpoint; old support and seven-day diagnostics contracts unchanged.
New consent is off by default and lasts until explicitly disabled. Latest hardware,
application, network, mobile, session and diagnostic observations each expire in
seven days, independently of readiness/support updates. Revocation deletes payloads;
minimal identity-bound consent/sequence tombstones prevent delayed resurrection.
No raw IP persistence, coordinates, SIM IDs, traffic, messages or identity secrets.
Collector projections must replace current data, not append it to inventory history.

## Pending delivery gates

### First source checkpoint: authenticated storage

Separate `/friends/device/technical-metadata/v1` schema1 binds exact report bytes
to `technical-metadata-v1:SHA256` identity proof. Strict bounded groups distinguish
SIM operator/registered operator/radio and preference/attempt/established transport.
Consent epochs plus monotonic sequence-derived IDs reject replay/conflicts; immediate
revoke bypasses per-device rate limiting and retains only an anti-replay tombstone.
Replaying after expiry cannot extend retention. Per-group monotonic age, server
received_at, clock-skew annotation and seven-day expiry do not use support/ACK times.
Latest-only private SQLite has secure_delete and independent minute cleanup.
Store ceiling5000 devices; sample interval60s; maximum report6144UTF-8 bytes.

Local control + identity lock versions verified. Focused API/lifecycle/security,
legacy support/diagnostics and packaged real HTTP tests:82 PASS,14 SKIP (13 nginx
matrix without FC_TEST_NGINX;1 separately pinned sync artifact absent). These skips
are NOT ingress/GeoIP/Android/release acceptance. This checkpoint does not yet
collect Android observations, enrich GeoIP, populate the panel or publish an APK.
Ingress snippet is prepared for actual18086 and overwrites X-FC-Ingress-Peer;
the API intentionally does not trust or use that header as source-location proof.

### Second source checkpoint: replaceable panel projection

Migration0014 adds current metadata and a source cursor, keyed by full existing HMAC,
not InventoryDevice PK. A separate archive-pinned, isolated read-only SSH collector
passes transient output directly to the importer; no new metadata is inserted in
inventory files/history/audit. Monitor records only import status, prunes on source
failure, and does not couple metadata failure to VPN/subscription/support actions.
Revocation/epoch fencing is also enforced at import. Templates hide expired groups
before the next cleanup; the import command physically removes expired values.

Production object templates (not /demo/) now display profile, network, separate SIM/
registered operators/radio, actual-session fields and sources/individual ages, with
model/Android/app/network/operator/transport search filters. These are SOURCE changes,
not evidence of currently populated or deployed metadata. City/ASN remain unfinished.
The normal existing panel address is http://127.0.0.1:8765/ with existing login.

Local disposable PostgreSQL17 (no production DB mounted), matching panel lock versions:
23 focused projection/object checks PASS; full panel suite306 PASS/94 known static-dir
warnings. Initial test start raced PostgreSQL initialization and one synthetic key
fixture was34 not32 bytes; fixed fixture and waited for pg_isready before these passes.
Local Python3.14.4 results do not substitute hosted Python3.13 CI. PR38 is DRAFT:
https://github.com/Joker20380/family_connect/pull/38. No merge/release acceptance.

Implementation/security/lifecycle tests, Android API27/API35 and NVIDIA/KVM runtime
qualification; installed125→new identity/settings/support preservation; local MMDB
positive/provenance/negative checks; latest-only panel projection and UI; exact APK
CI/signing/source archive/hash; isolated paid compatibility; consistent production
backup/restore; minimal runtime/panel/policy delivery; public discovery/invitations/
full HTTPS byte verification; PR/own review/ordinary merge and remote SHA readback.
Physical5G/carrier cases may be NOT_OBSERVED with fallback tests, not fabricated PASS.

Rollback must restore code/config only, preserving later user events and metadata
revocation tombstones. Never restore old databases over live data. No transport
restart, kill-switch bypass, new dangerous permission or RU persistence changes.
