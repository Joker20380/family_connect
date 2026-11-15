# DEVICE-TECHNICAL-METADATA-1 — 15 November 2026

## State

Android source candidate:0.1.18-beta126/code126, package remains
com.familyconnect.app.friends. NOT_BUILT / NOT_SIGNED / NOT_INSTALLED /
NOT_PUBLISHED; no APK/source hash exists yet. Public125/catalog8, invitation routes
and accepted paid108/119/123/125 remain unchanged. Never publish a rebuilt125.

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

### Third source checkpoint: Android126 candidate (not runtime qualified)

Separate support-information switch defaults off and does not inherit support-upload
preferences. New consent persists until disabled; revoke is a separately persisted
pending operation and cancels the old request. Only a latest pending refresh is kept;
each retry samples current public APIs, not an unbounded queue of old reports. One
asynchronous request, completion-based60s minimum and exponential capped30min backoff;
app/session/default-network events and a six-hour active-process refresh. Requests
use the existing ordinary HTTPS route, NOT a new protected/bound bypass or speed probe.
The old seven-day diagnostics switch, body and expiration remain separate.

Build/Package gives manufacturer/model/Android/API/app/versionCode. Public telephony
APIs use the default data subscription, not a fabricated combination of two SIMs;
no READ_PHONE_STATE permission is requested. Unavailable radio has a concrete reason.
Default non-VPN network is explicitly labelled default, never tunnel underlay.
The first source incorrectly attempted getUnderlyingNetworks (not a public SDK35
method); source30f68b69 Android CI correctly rejected compilation. The correction
uses public capabilities propagated by Android onto its VPN network, only when one
VPN and one concrete physical transport are exposed; API29+ also checks owner UID.
Ambiguous/absent propagation remains underlay_not_exposed, not first-NOT_VPN inference
from ChatNetworkAndroid. Runtime underlay transition qualification remains pending.
Auto gets active transport only in CONNECTED; attempt/preference
remain separate, gateway is recorded at the actual successful connection transition.
Bounded last terminal-error time is collected only with the new consent and cleared
on off. MESH readiness remains a reported diagnostic, not a grant of VPN access.

18 Java17 JVM checks PASS (new snapshot/backoff/consent cases plus existing terminal
tests).84 Python metadata/Android-release/notification/orchestrator/subscription-source
checks PASS. Existing accepted pins are preserved: two additive integration changes
are pinned as an explicit125→126 overlay and reverse-applied in tests before checking
the unchanged125/reference hashes. AutomaticConnection/native transport files retain
their existing bytes. API27/API35 instrumentation is added to the normal Friends CI
list but has NOT_RUN locally. No emulator, physical phone, new APK, signing, paid
descriptor, production metadata route, projection migration or public change yet.

Implementation/security/lifecycle tests, Android API27/API35 and NVIDIA/KVM runtime
qualification; installed125→new identity/settings/support preservation; local MMDB
positive/provenance/negative checks; latest-only panel projection and UI; exact APK
CI/signing/source archive/hash; isolated paid compatibility; consistent production
backup/restore; minimal runtime/panel/policy delivery; public discovery/invitations/
full HTTPS byte verification; PR/own review/ordinary merge and remote SHA readback.
Physical5G/carrier cases may be NOT_OBSERVED with fallback tests, not fabricated PASS.

## Local GeoIP preparation and CI correction · source checkpoint, not deployment

The verified ingress is nginx8443 → loopback18086 → serving HTTP candidate archive,
not inactive18084. The prepared new route overwrites X-FC-Ingress-Peer and clears
XFF/Forwarded, but metadata does NOT geolocate that header: normal service requests
can arrive through VPN/relay. No new protect/binding/IP-echo path was added.

The candidate external collector joins consented stable device identity to the
canonical registry's full AWG public key, then RU fcopen31 endpoints AND recent
handshakes (≤180s). It never matches an identity by coincident IP. Only a current
RU/AWG connected session is eligible. Public peer addresses are lookup inputs in
process memory only; no raw address, port, coordinates or peer key is exported to
the panel. Known VPN exits/nonpublic/relay/unverified/stale observations get explicit
unavailable reasons. NL/TCP direct-peer enrichment is NOT_IMPLEMENTED here; other
fields work independently and last suitable geo remains age-labelled for ≤7days.
The retained location is the peer network's database entry, not proof of where a
person is physically located; an upstream third-party VPN can still affect it.

Centralized candidate location: `/opt/apps/family_connect/geoip` on the canonical RU
collector host only, not every gateway or the web container. No server installation
has occurred. Official HTTPS DB-IP Lite2026-11 City and ASN were downloaded locally
to a disposable preparation directory after checking ≥1536MiB staging/rollback free
space. Download bounds160MiB compressed/256MiB expanded per file, allowed origin,
MMDB type/month/IP structure, hashes and atomic pair replacement are enforced.
One previous set retained; update failures visible in update-status.json. Missing,
invalid or >45day database does not reject metadata. SHA256 is local integrity,
NOT a supplier signature. Exact local MMDB receipts:

- City126873350bytes: `5f64491f77c2c78b56cd83a88db4ea6c4666874322da38805498bbb754ccc735`.
- ASN9648279bytes: `81565a450281c949fc83745f5ec9cfea70b035163b1152b055645884765d153d`.
- Controlled public resolver IPv4/IPv6 lookups: city/country/region/ASN/organization
  populated, no coordinates exported. Synthetic key-binding fixture proves exclusion
  of another identity, revoked key and unknown peers. This is NOT an observed live
  production peer or installed-APK→panel chain. Real peer attribution still required.

Migration0015 adds a replaceable GeoIP projection with independent age/expiry, city
filter, source/version/SHA detail and DB-IP attribution. Missing current direct
evidence may retain the last suitable observation without changing its timestamp;
revocation and TTL clear it.47 focused metadata/GeoIP tests and315 panel tests PASS
locally (95 existing static-directory warnings). Core/identity/panel installed
versions match current lockfiles; GeoIP reader uses its separate hash lock.

CI for source30f68b699c65c1112e6ff140620fb9bbb4d4fc38 is not accepted: Android job
132634376299 failed at the invalid SDK method, paid132634345643 failed because the
closed committed-source packager omitted the new nginx snippet. Both source causes
are corrected, not waived. Panel132634343669:305PASS/1FAIL, existing network-probe
test's “yesterday” window contains its120-second-old fixture at UTC midnight; no
assertion weakened. New source must pass ordinary applicable CI. Readiness wire
43655938216 PASS is independent and does not qualify the APK or complete delivery.

Rollback must restore code/config only, preserving later user events and metadata
revocation tombstones. Never restore old databases over live data. No transport
restart, kill-switch bypass, new dangerous permission or RU persistence changes.
