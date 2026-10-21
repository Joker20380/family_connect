# Volgograd mobile bootstrap —20 October2026

## Result and delivery gate

**Local defect reproduced and fixed; historical transport cause not established.**
Private **beta96-bootstrap / code96** is built, checked and signed with the existing key.
175 JVM tests,6 Python bridge tests and8 focused native tests/subtests with race PASS;
actual Java network selector also passes
an Android-stub handoff/TUN fixture. This is not tester cellular acceptance.
**Owner95→96 in-place installation verified14:48:37UTC**, no forced disconnect,
uninstall/data clearing; UID10283 unchanged and fresh server identity/Support ID
bindings match. Post-update96 READY/device proof and manual Connect remain NOT_RUN.
Owner requested private tester file handoff; receipt/installation not confirmed.
Protected signing finished successfully; no dialog/background wait left. FIELD_PASS=NOT_RUN.

Baseline before this update was owner beta95/A0, LEGACY64/65536, CREDIT128 OFF, compatible
gateway`272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4` with1011.
Read-only entry14:22:59UTC reconfirms APK/native hashes, same PID3937546/invocation
`17ec5abfcbc84a9d913e844193e0d931`, NRestarts0, policy64/counters OFF. No server change,
restart, activation, credentials/floors mutation, transport tuning, push or publication.
Mux experiment remains closed/INCONCLUSIVE; no speed measurements repeated.
Current owner96 reuses all native95 libraries/A0; last negotiated profile LEGACY64,
no active VPN/service after update. No new96 session/profile agreement is claimed.
Gateway was not modified/restarted during signing or installation.

Private capsule:`state-client-build/mobile-bootstrap-20261020/`.
Tracked evidence:[sanitized result](2026-10-20-volgograd-mobile-bootstrap.evidence.json).
Exact delta:`tests/fixtures/mobile_bootstrap/beta95-to-beta96.patch`, SHA256
`094779d617dcbb4ee4856daf7b0844277aad681f2119d9b5492f704384aad185`.
Full candidate sources:`state-client-build/mobile-bootstrap-20261020/android-source`;
source inventory/build receipts are in its sibling`build/`.

## FETCH_FAILURE_STAGE_AND_CAUSE

Both supplied exports found in`/mnt/data/joker/Загрузки/` and verified:

| File | SHA256 |
|---|---|
| FamilyConnect-diagnostics(19).json | `6d95570be64d8bf4875049ac6992e842de33f38386f9dda26da03e1ad4d81f8f` |
| FamilyConnect-diagnostics(20).json | `95ce765751371aebacda3c66cac90a1cdba7f4a5345446810f65c3b1fc7ead47` |

Both identify FC-ZMVK-MM7C/API34/beta94, not owner/Krasnodar. File19 ring is Wi-Fi
connection`5791e739…`; its mobile incident is`51808e19…`. File20 ring/incident repeat
the same mobile connection`b624ca0b-8aed-4414-9746-ebd568f03cb1`; historical restricted
sessions are not new attempts. Deduplicating complete event records leaves274 unique
events across the exports, not274 connections. Network class belongs to each saved
snapshot, not automatically to every historical event inside it.

Primary sequence (client UTC): READY11:51:50.681 under`6fe6ae57…`; new CONNECTING
11:52:13.458; VPN_CAPTURE_READY13.493; restricted candidate13.500; FETCH_FAILED13.895;
NOT_READY14.030; BOOTSTRAP_UNAVAILABLE14.039; final FAILED14.112.654ms is attempt
duration, not an HTTP latency. No native startup/session evidence exists for this
attempt because `RestrictedTunnelEngine` received null before `beginReady`.

Exact94 and95 copies of the ten relevant Java classes and`fc_rns_transport.py` are
byte-identical (hashes in evidence). Checkout main differs and was not used as baseline.
`FriendsRestricted.ready` joins the single-flight required refresh after VPN capture.
`RestrictedBootstrap.refresh` catches a fetch Exception and emits FETCH_FAILED unless
it recognizes authorization rejection. Validation/import/storage failures have other
codes. It consults cached bytes **only** if `FriendsReadinessProtocol.unavailable`
recognizes that exception. A non-availability error can therefore return null while
the encrypted snapshot itself is still present and valid.

Branches collapsed into FETCH_FAILED include challenge local/proof preparation,
network open/connect/TLS/write/read failures, HTTP status/protocol failures, challenge
or response parsing/binding failures, and RNS initialization/transport errors. Fast
local failures, socket refusal/reset, TLS rejection and HTTP errors can all fit the
short interval. A socket timeout is not established by654ms. Neither exact HTTP stage
nor original exception/route is in94's export; protected proof/body is not needed.

Read-only Friends API lookup by Support ID finds READY ACKs corresponding to the two
prior readiness observations: server challenge/fetch11:24:59/11:25:00, ACK11:25:01;
challenge/fetch11:51:51, ACK11:51:52. Client observed_at values11:24:59/11:51:50 match
the exports within different-clock granularity. Both bundles expire14:35:11UTC,
revision1/minimum_crl27139. Further READY ACKs11:52:57/59 are retained; their network
is unknown. No accepted challenge receipt matches the failing13.458–14.112 second
interval. This does **not** distinguish pre-HTTP failure from a rejected request.
The bounded API journal query11:24:40–11:53:10 returns0 records; no complete access-log
coverage is established. Current API started13:05UTC, archive SHA256
`e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7`.
No proof was forged and no tester private key copied. No claim of carrier blocking
or MESH detection follows from missing logs or FETCH_FAILED.

**Locally reproduced defect:** ordinary Python RNS socket refusal crosses Chaquopy
as a generic Python exception. `FriendsReadinessProtocol.fetch` converts it into
CHALLENGE_INTERNAL_ERROR with availability=false. `RestrictedBootstrap.refresh`
then refuses to select a valid cache. Actual baseline Python code and the real Java
protocol/cache path reproduce the two halves; candidate preserves typed availability.
This is a concrete defect consistent with, **not proven to be**, the historical failure.

## READY_TO_NOT_USABLE_EXPLANATION

READY means the previously imported/revalidated full bundle passed the native
validator and durable vault readback at that observation, not that the next refresh
or seed will succeed. Server ACK evidence supports a fresh successful import, not
expiry23seconds later. The failed attempt lacks its cache fingerprint/validation
result, so its exact snapshot and usability cannot be reconstructed from that ACK.

`DiagnosticRing.readinessResult(FETCH_FAILED)` itself sets bootstrap_directory to
NOT_USABLE; it is not a directory-validator reason. Then null startup selection
causes `Diagnostics.readiness(false)`. Therefore this export does not establish
cache deletion or directory expiry. `attempt` updates cooldown without erasing the
response; AtomicFile import/readback and monotonic rollback checks remain. Failed
import preserves old data but does not bypass a security/protocol rejection.
Disconnect closes ephemeral native/session resources, not the encrypted vault.

Directory/seed discovery is distinct from issuer delegation, Family certificate,
CRL/grant/floors, one-time API challenge and fresh session-bound broker descriptor.
The delivery nonce is checked as part of authenticated issuance; no failed proof is
replayed on a different route. Starting from valid cached delivery still performs
Family authentication and requests a **fresh** dedicated descriptor. No descriptor
is cached/reused indefinitely. A stale prewarm completion may update the shared
identity-bound snapshot, but monotonic import rules and caller cancellation checks
remain; it cannot authorize a cancelled native start. New diagnostic records retain
the fetch's original connection ID and separately mark a changed completion scope.

## REQUEST_NETWORK_PATH

Direct readiness uses literal-IP HTTPS`185.251.89.19:8443`: no application DNS lookup
of a host name in that URL. While not healthy/connected, `ChatNetworkAndroid` selects
a fresh NOT_VPN+INTERNET Network for each HTTP connection and uses
`Network.openConnection`; it does not intentionally use the new TUN. A healthy VPN
can serve readiness by the existing explicit route. The existing RNS fallback also
binds its socket before connect to an eligible underlying Network and pins provider
identity; it is **not** the media seed. No generic protect_ok inference is used.

Selection currently uses the first eligible Network, not an exported preferred-network
generation. Its exact ordering/liveness during the historical handoff is unknown.
No routing change is justified by these exports; neither stale pool reuse nor TUN
capture of this request is proved. New diagnostics record selected type/Network
handle per failed route, operation/stage, normalized class, HTTP status if obtained,
and monotonic readiness-attempt duration (including any initial reconciliation,
not individual HTTP response time/RTT). HttpsURLConnection's
connect/TLS/write boundary remains combined; exception class distinguishes DNS/TLS/
connect where supplied. No system service, app traffic route, kill switch or DNS changed.

## VALID_CACHE_WITH_API_UNREACHABLE / EXPIRED_REVOKED_CACHE_REJECTED

| Local scenario | Result and scope |
|---|---|
| A: full valid cached bundle, direct failure, RNS socket unavailable | Old generic Python error loses fallback; typed candidate selects exact cached bytes. Existing native delivery/seed handoff validation is separate from this Java/Python boundary test; not a Volgograd field pass. |
| B: absent/expired/tombstoned/invalid/below-floor | No reuse; existing native signatures, issuer/identity binding, expiry, CRL/revision floors unchanged; relevant Java negatives rerun. |
| C: Wi-Fi→cell before/during/after readiness | Actual ChatNetworkAndroid exercised with mutable Android stubs: each call selects current underlay; lost selection fails, next call sees new network. No physical Android handoff claim. |
| D: TUN present first | Same actual-method fixture excludes VPN network; no-underlay fails rather than opening default TUN path. No actual mobile traffic generated. |
| E: old completion/new connection and cancellation | JSON export marks original/completed connection mismatch; existing orchestrator cancellation/late-start tests PASS. Single-flight and cache monotonicity retained, not a new generation framework. |
| F: unavailable refresh with valid old snapshot | Exact bytes retained/selected; atomic-write and persistence failures retain old snapshot, security rejection not suppressed. |
| G: process restart | Persisted synthetic snapshot revalidated by new cache instance; expired/tombstone state still rejected. |
| H: API returns | Valid newer snapshot accepted; late older snapshot rejected and cannot replace it. |

Tests use controlled local exceptions/synthetic payloads, no production firewall,
clock manipulation or real credential corruption. RNS socket-refusal tests execute
actual old/new Python methods with stub sockets; no claim of physical byte-exact
mobile delivery. Python busy/cancel/unknown/malformed/refused cases are not converted
to availability. Trust/authentication errors remain fail-closed.

## TARGETED_FIX

Only explicit RNS socket bind/connect availability failures and bounded RNS wait
deadlines become a typed `TransportUnavailable`. Readiness-only Python bridge methods
return a fixed availability tag; Java translates it to existing `Unavailable`.
Other Python/control uses retain exception behavior; generic exceptions are **not**
classified by matching their messages. No increased retries or proof replay.
Existing full-cache validation and failed-refresh policy are reused. Missing/expired
cache still refuses startup; the automatic-restoration policy is unchanged.

Additive bounded `readiness_fetch` data goes through DiagnosticRing persistence and
the actual `ring`/`incident` JSON serializer: up to4 normalized failures, operation/
stage/route/status, correlation IDs (not proof), network generation/type, original
connection scope, selected REFRESH/CACHE/NONE, age/fingerprint/expiry and bundle
validation. Per-document expiry is decoded where possible; successful full validation
is labelled VALIDATED_AS_BUNDLE, other unproven signatures/bindings NOT_PROVEN, not
invented success or a fabricated precise native validation reason. No response body,
nonce, token, room URL, keys or application payload is exported. Serializer redaction
and bounds checks pass. This is not a new export framework or per-packet trace.

## LOCAL_AND_OWNER_VALIDATION / TESTER_CELLULAR_VALIDATION

- Local175 JVM tests PASS, including6 new bootstrap/diagnostic cases and unchanged
  recovery/cancel/bootstrap regressions;6 exact Python bridge tests PASS.
- Actual network-method handoff/TUN stub fixture PASS. Native is byte-identical95;
  8 focused native tests plus subtests PASS with race (delivery crypto/bindings/floors,
  cached deadlines/revocation, actual bootstrap exchange/handoff/replay/cancel and
  atomic cache/restart). Previous1011 checks retained; no Mux speed/matrix rerun.
- Delta applies cleanly to exact95 source; final complete build inventory unchanged
  after validation. `git diff --check` PASS.
- Repaired and retained: initial read-only DB/schema lookup mistakes; Gradle sandbox
  loopback failure; provenance metadata/work-tree binding; one negative test supplied
  the wrong challenge-auth exception shape. Complete relevant suite then passed.
- Owner physical installation: fresh95 hash/native/UID preflight14:47:52UTC showed
  no VPN/service; fresh install gate repeated these checks before `adb install -r`.
  At14:48:37UTC exact signed96/code96/native hash and unchanged UID10283 verified.
  Fresh read-only server identity/Support ID bindings match before/after; new96
  READY/device proof, Connect and recovery **NOT_RUN**. Server-row equality alone
  is not new client proof-of-key. Tester cellular **NOT_RUN**, not inferred from owner.

## SIGNED_APK_OR_SERVER_ONLY_FIX

Client-only; no server fix/rollout needed. All12 native libraries equal95, including
`libfc_restricted.so` SHA256
`66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63`.
Unsigned artifact (not for installation/distribution):
`state-client-build/mobile-bootstrap-20261020/build/android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk`
SHA256`2324906936da9d63d482e811b650fd16acc82b8c351b086342adf16f0d6e95bc`.
Signed private artifact:
`state-client-build/mobile-bootstrap-20261020/delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk`
SHA256`07a90f03269e1df683289bc1fbe7fa7e88647c5629f71db1f784d6566aa9228d`.
Package`com.familyconnect.app.friends`, code96, arm64,16KiB alignment verified;
verified same signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Protected vault signing completed at owner's request; no secret exported. Separate
owner-authorized update used the guarded existing installer with fresh identity gate,
not a saved transition intent. Receipts in the capsule: `delivery/signing-receipt.json`,
`upgrade-intent.json`, `upgrade-receipt.json`, `identity-before.json`, `identity-after.json`.
Signing receipt's installed/distributed=false describes signing-time state; later
upgrade receipt proves owner installation only. Private tester handoff requested;
no automated distribution/publication and no tester receipt or install proof yet.

Next owner action: open Family Connect and tap Connect normally; no input injection
or background waiting. Tester updates94→96 using the exact signed file, without
uninstall/clear-data/reactivation, then performs one cellular Connect and JSON export.
Do not send95 as the bootstrap fix. Rollback
means a subsequent higher-code same-key client with the exact95 behavior if needed,
not Android downgrade or old gateway rollback. No rollback build is made speculatively.

## REMAINING_BOOTSTRAP_DEPENDENCY

Valid material permits existing authenticated seed/Room Broker startup without a
successful direct API fetch **when refresh failure is recognized as availability**.
It does not make the app indefinitely offline. Missing/expired/invalid/revoked material
still needs the approved authenticated challenge+readiness issuance operation over
direct HTTPS or existing RNS service. The media seed brokers dedicated descriptors;
it does not renew expired Family credentials/issuer/grants for this client path.
No new trust model, anonymous relay, built-in shared secret or per-tester manual import.
Even valid cache cannot guarantee an old seed is still live after gateway replacement.

Once signed96 is installed normally, **one targeted cellular Connect and JSON export**
can distinguish the historical-type failure with the new fields. Do not ask for old
attempts to be repeated on94 or announce mobile access restored before that evidence.
