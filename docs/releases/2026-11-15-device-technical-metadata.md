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

## Source follow-up and isolated bench preparation

Source d89cd2923a8885f012691d0b17f9d395fd3e5be7 pushed/remote SHA verified.
Hosted panel43657720733, paid43657720741 and readiness43657720823 PASS; local
committed-source paid packaging/HTTP tests27PASS/14 explicit integration skips.
Full pipelines/Android were still running when this follow-up was prepared.
Own review found a canonical RU gateway being serialized through the raw-name mapper
twice; mapping is now idempotent and a regression test covers every supported name.
Network/session sampling is invalidated across a concurrent session transition.
19 Java17 JVM checks PASS. Panel now also renders the independent client error time.

One new API35 AVD runs with shared qualification lock, PRIME offload, `-gpu host`
and `-accel on`. Actual guest GLES identifies NVIDIA GTX1650Ti; the emulator process
holds `/dev/kvm`. Existing AVDs/owner phone are untouched, no parallel emulator.
Current public125 independently downloaded over normal verified HTTPS:50470304bytes,
SHA256 f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c;
package/code125/ARM64/minSDK27 and original67a90d1b signer verified. Signed v2 catalog8
signature/source bytes and legacy descriptor agree. This is only the125 baseline,
not evidence that126 is built, installed, compatible or publicly available.
Fresh RU read-only resource check:7511MiB disk available/1089MiB available RAM;
HTTP PID2345109 remains active, ordinary AWG/TCP not restarted. GeoIP still local-only.

Rollback must restore code/config only, preserving later user events and metadata
revocation tombstones. Never restore old databases over live data. No transport
restart, kill-switch bypass, new dangerous permission or RU persistence changes.

## Baseline-derived overlay and browser gate

Fresh serving HTTP archive617c7d752a20631d624b301c59142af34f3624483a5d2d5adc2a7c7722dd74b1
differs from main: its access module lacks main's unrelated revoke_device method.
The explicit two-member patch plus two new modules preserves that accepted runtime
and every unrelated archive member, including paid policy. Candidate HTTP SHA256
70a924dbc02c4ebdb15fe2b935f29070bda0a5fa37f140ac2d35765b34500614 is local-only.
Overlay unit2PASS; exact candidate with complete isolated test companions:
42PASS/1SKIP (external pinned sync artifact not supplied). Actual nginx/TLS checks
prove forged XFF/Forwarded/client peer headers cannot choose the forwarded peer;
the header is not a client-location proof and is not used for GeoIP.

Isolated PostgreSQL/browser gate PASS at1440/390px: model/city filters, sources,
attribution and existing subscriptions/server navigation, no horizontal overflow.
Screenshots contain synthetic fixtures, NOT a production end-to-end observation.
Exact public125 installed successfully on the new API35 NVIDIA/KVM emulator;
package/code125 read back. No activation or125→126 preservation claim yet.

Source46a8686ab8e84aff7994aef34299690c35a94722 hosted panel43658628417,
paid43658628518 and readiness43658628548 PASS. Android132642755619 fails lint on
READ_PHONE_STATE/getDataNetworkType; no suppression or new dangerous permission is
accepted. Linux-control132642792242:5684PASS/1FAIL/276SKIP in standard context,
root258PASS and snapshot31498PASS. The failing subscription source assertion finds
the legacy device regex changed by the new endpoint; repair must preserve it.
PR test-merge source24d98766816d8fff68d773f721bf8baacda26688 is distinct from head.
Desktop runtime checks passed, but unrelated appimagetool download failed in132642755597.
These failures block acceptance, not reasons to bypass gates. No production writes,
paid descriptor126, signed APK, public catalog change or user-ready rollout.

## Permission and legacy-path correction

Android33+ radio uses public getDataNetworkType with normal READ_BASIC_PHONE_STATE,
declared and checked; no dangerous READ_PHONE_STATE declaration/request or lint
suppression. API27–32 retain explicit permission-not-granted radio fallback while
SIM/network names remain independently available. Runtime tests retain the dangerous
permission denial assertion and validate either a real radio category or its reason.
The legacy service regex is restored verbatim; one exact metadata-v1 path is added
separately. Existing source/security assertions are preserved, with an additional
exact-path assertion. Only the reviewed metadata delta pins change; reverse-applied
beta125 source/UI/MESH hashes remain unchanged.67 targeted subscription/public-source
checks PASS after the correction. Hosted lint/runtime acceptance is still pending.

## Capacity, privacy and protected-state preparation

The5000-device metadata store needs more than the inventory4MiB envelope. Its separate
collector/monitor/importer now have a64MiB transient bound, UTF-8 export and strict
duplicate/nonfinite JSON rejection; ordinary inventory4MiB assertions remain intact.
19 projection tests and14 monitor tests PASS, including a full-capacity size bound,
independent failure cleanup and no retained payload file. The local monitor budget
is500s including that independent path, not a change to RU service limits.
The metadata nginx location discards both access and error logs to avoid raw peer IP
retention on proxy failures. Three actual nginx/TLS/header tests PASS against the
same immutable candidate HTTP archive. SIM labels explicitly refer to the default
data subscription rather than claiming every observed SIM is the tunnel underlay.

At2026-11-15T00:54:38Z, the canonical520192-byte registry backup passed integrity,
foreign keys, table-hash comparison and paid projection recovery in isolated SQLite.
The25335651-byte panel pg_dump restored with --exit-on-error in a disposable
PostgreSQL with --network none, no published port and tmpfs data; it was stopped
after validation. Private encrypted off-host backups plus the local key remain under
/mnt/data/fc-device-metadata-20261115 (not Git). Existing panel environment/HMAC/source
configs are separately encrypted. No real payments, product DB edits or service
restarts. This is preparation, not an old baseline to impose on concurrent users;
fresh comparison is required immediately before deployment. No old DB restore into
production is permitted. Future panel backups must exclude metadata projection rows.
The first backup attempt used system Python without RNS and stopped before creating
the database copy; recovery reused the same pinned archive with the actual accepted
venv. No protected state was changed by that failed preparation.

## API-level and panel-log review

Source5d7be0a2 hosted Android132647466544 passes the radio permission check but fails
NewApi: NetworkCapabilities.getOwnerUid is API30, not29. Guard corrected to30 after
checking the installed SDK API database; no lint suppression/baseline. New runtime
qualification still required. The default-data SIM qualifier is shown explicitly.
The panel's proposed Gunicorn format emits only method/path/status/duration, never
city/operator query strings, referrer or peer IP.20 projection tests include actual
Gunicorn atom rendering;5 build-context checks PASS. Production command must receive
this format at cutover; changing source compose alone is not a deployment.

Baseline-derived panel image5051f0e722661ad63343c964945b8d7f37f7984bdf6b5c709c4e4082c14d94d5
contains only14 metadata-related source files over accepted61e4df54f1e1 image.
No unrelated main or paid modules copied. Isolated checks/migration drift/actual
`/inventory/` render PASS after providing the ordinary tmpfs collectstatic step.
This is NOT the deployed panel. Preserve that preparation image and source receipt;
apply the separately qualified query-free access-log command during deployment.
# Continuation: incident preparation and Android public test APIs

The preceding session exposed an inventory-HMAC value in tool output. Bounded
local/Git/artifact checks are recorded in the HMAC receipt; they do not establish
public disclosure or attest every external log. Values, mapping
tables and private matched lines must not be emitted or committed. No production
key switch is authorized until a successful compatible migration rehearsal report
is presented and the owner confirms the concrete cutover.

Job132651608837 on b195b10d failed compiling instrumentation because the test used
non-public NetworkCapabilities mutators. The correction extracts an exhaustive
eight-combination pure classifier and retains an instrumentation assertion against
a real connected Android default network using public read APIs.20 JVM tests PASS;
this does not constitute instrumentation or APK qualification. Version stays126.

The original public125 was activated on the isolated NVIDIA/KVM x86_64 bench through
the ordinary referral path. Two controlled test devices and three invitations were
created (one unused invitation revoked); no real payments, expiry changes or user
messages. After activation its unchanged ARM64 libfc_restricted.so crashes with
SIGILL in golang.org/x/sys/cpu.getisar0.abi0 under native translation. This precedes
installation of126 and is not evidence of a metadata regression. Upgrade remains
NOT_OBSERVED; a compatible ARM64 environment is required, not a rebuilt125.
HMAC containment, full reference coverage and isolated replay now have a separate
[preparation receipt](2026-11-15-hmac-migration-rehearsal.md). No production key switch
or metadata deployment is implied by that preparation.
Source61b00409e24b92651678b817d2a6f5d4796948f9 now passes applicable hosted contexts,
including the full Android API35/27/28/31 matrix on rerun132675960943 and explicit
support-runtime/closed-kit qualification43672504816. Earlier failed DNS attempts
are retained in the receipt. The metadata runtime tests use actual public Android
observations; no hidden API or instrumentation waiver. HMAC baseline overlays and
real-copy recovery are qualified for a separate owner decision, not installed.
Production metadata and release-signed126 remain absent;125→126 preservation on
compatible ARM64, exact paid descriptor, installed end-to-end chain and public
catalog/invitation publication are still required. Own unused benches are stopped.

## 15 November continuation: narrow HMAC stage complete

The owner-approved [generation2 cutover](2026-11-15-hmac-generation2-cutover.md)
installs only the qualified minimal HMAC overlay and protected aliases/keys.
Three automatic inventory/support cycles and historical identity/request/cursor
preservation pass. No new metadata API, database model, panel UI or beta126 is
deployed. Public125 and its paid descriptors are unchanged;125→126 on compatible
ARM64 and installed APK→API→panel remain release gates.
RU AWG/TCP and paid-watch/reconciler degradation was observed during the window;
the cutover did not restart those services, and triggering causality remains open.
This is not a healthy-VPN or user-release acceptance claim.
