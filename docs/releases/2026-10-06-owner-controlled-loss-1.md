# OWNER-CONTROLLED-LOSS-1 — FAIL / UNKNOWN

Subsequent offline analysis: [SELECTED-RETRY-EVIDENCE-GAP-1](2026-10-06-selected-retry-evidence-gap-1.md)
proves DATA19 acceptance/ordered delivery and ACK generation at protocol level,
but does not recover exact remote media/acceptance callback records. Quantified
ring eviction and a local-only pinned-watch patch do not change this physical
gate's FAIL/UNKNOWN result or erase post-cleanup reverse104 exhaustion.

## Single physical experiment, 2026-10-06 07:27–07:28 UTC

This supersedes the historical preflight STOP retained below. Exactly one owner
session and one arm command were executed. No repeated experiment or reconnect.
The application traffic completed, but the strict diagnostic gate is **FAIL**:
the full paired receive chain is unproven and extended closeout contains gateway
retry exhaustion after intentional client cleanup. Classification **UNKNOWN**.
No earliest missing transport stage for selected DATA19 has been proven; the
earliest unproven traversal is remote RTP reception, not a proven reception failure.

### Exact pair and immediate preflight

Source `5327deb414ae8aa77ce2f9490fd99c9485eba740`, sealed beta66/code66:

| Member | Verified SHA256 |
|---|---|
| Installed APK | `e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81` |
| Installed restricted JNI | `e433a4910d218065bd4a217b1c87aaad1698d3f4716179b7559248d41b49c792` |
| Loaded gateway | `6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec` |

Owner package com.familyconnect.app.friends, UID10283, arm64-v8a,
non-debuggable, Support FC-4D8Q-REEG. Encrypted identity and enrollment fingerprints,
activation and identity decryption matched accepted deployment before and after.
No private profiles/keys were exported. Phone mobile-data1/Wi-Fi0, actual active
network cellular and not Wi-Fi/VPN checked before session. Gateway exact loaded
hash matched immediately; embedded revision reconfirmed in closeout.
PID1000816/NRestarts0 before and after, no service restart/deployment.

07:27:46UTC preflight: owner admitted/non-revoked, revision3, beta66 native
READY/PRESENT_VALID/orchestrator_usable ACK07:25:13UTC, expiry11:03:32UTC.
Actual served chain contains one leaf, fingerprint
849e0fce6f5d53c41cb55b8d41a62facf0afcca8aaa58fad6e5ca4f00b165656,
matching profile and hostname; signature verified against profile issuer.
Leaf expiry11:03:25UTC, issuer13:51:23UTC, signed CRL8623 expiry11:27:19UTC.
RU/NL directory version1 and generation07:03:34.867854224Z identical, SHA256
32b8b5afe109b98a6daf378c9186f8993c9bd852f846ef5f2b019063fff33f23.
Effective minimum credential/directory/grant/readiness headroom12938seconds.
No renewal was needed or performed. Idle fault status UNAVAILABLE/armedfalse;
active-session status explicitly DISARMED before arming, count0/consumedfalse.

Only a separate temporary signed instrumentation helper was built/installed.
The sealed product APK, JNI and gateway were not rebuilt or modified. Initial
helper build failed at sandbox socket creation; outside-sandbox final build PASS.
One controlledLoss instrumentation test PASS means harness traffic/assertions
passed, **not** that this strict paired diagnostic gate passed.

### Session and fault receipt

Session tag `4b0d85ac8060b0e4fbc66c5645a865de7381a08f88794ae8bb715acd3505f3f8`.
Gateway FAMILY_TLS established07:28:06.098, GATEWAY_SESSION07:28:07.113UTC.
Client recorder active before ordinary DNS/HTTPS sanity; HTTPS200/full577bytes
completed07:28:09.624UTC, active DISARMED receipt09.625UTC.

Arm07:28:09.627UTC: generation `a7c58a19b153daa34011829cc612006c`,
target outbound_data_attempt0_after_established, armedtrue/consumedfalse/count0.
Exactly one logical outbound DATA **N=19**, attempt0, consumed09.632UTC.
Fault hook runs before carrier send; attempt0 deliberately has no carrier/VP8/RTP
identity. ACK, heartbeat, signaling and attempt1+ are not selected by this hook.
The fault receipt later proves consumedtrue/count1/armedfalse, same generation.
Raw Reliable epoch, DATA byte length and payload subcategory are not exported by
this sealed schema; UNKNOWN. Direction and session tag distinguish reverse DATA19.

### Mandatory evidence table

Client index references refer to deduplicated native boundary indices. Gateway
references distinguish lifecycle sequence numbers from boundary indices.
Zero attempt/fragment fields are omitted in JSON by the sealed Go schema.

| Stage | attempt0 | attempt1 | Evidence |
|---|---:|---:|---|
| Reliable created | PASS | PASS | Client654 at09.632; client818 at10.686, seq19, attempt1; elapsed1054ms |
| Fault selected | PASS | Not selected | Generation/target receipt; attempt0-only contract |
| Intentional drop | PASS, exactly1 | Not dropped | Consumed seq19/count1 at09.632; auto-disarmed |
| Carrier identity | None by design | PASS | Client819/822: sender3220232525, message842410499, fragment0/total1 |
| VP8 identity | None by design | PARTIAL | Frame timestamp1213693474/track1; PictureID not exported |
| RTP seq range | None by design | PASS | Client821:9063–9063, packets1, exact message/seq19/attempt1 |
| RTP emitted | No, intentional | PASS | Client821 rtp_written/ok; writer invoked, positive byte count and nil error |
| Remote RTP received | No traversal expected | UNKNOWN | No retained gateway boundary for selected message; incomplete ring is not negative proof |
| Carrier reconstructed | No traversal expected | UNKNOWN | Selected remote VP8/carrier completion not retained |
| Reliable accepted | No traversal expected | UNKNOWN direct boundary | Returned ACK19/255 and later cumulative ACKs consistent with healing, not substituted for remote boundary |
| ACK generated | Gap ACKs only | UNKNOWN healing ACK boundary | Gateway801/803 and807/809 generated/sent19/254; healing19/255 generation not retained |
| ACK returned | Gap ACKs PASS | PASS | Client837:19/255;844:20/127;845:21/63;935:27/0 |
| Base advanced | Head19 blocked | PASS | Client flow lifecycle23 at11.559:base34,next42,pending8; laterbase108,next108,pending0 |
| App recovered | Head gap observed | PASS controlled requests | Three concurrent modest HTTPS200/full577-byte bodies, DNS and independent TCP response |

Attempt1 is a newly allocated carrier/media attempt; there is no attempt0 media
identity to compare because the injected drop precedes allocation. Do not invent
an attempt0 RTP range or PictureID. The rtp_written observer wraps the actual RTP
writer and requires positive returned bytes, rather than relying on WriteSample.
This proves sender emission at the instrumented writer boundary, not receipt.
SFU rewriting is observable on other messages; do not equate nearby RTP numbers
or timestamps between peers to selected-message receipt.

### Gap, retry and ACK/base progression

Client sends later DATA20,21,22,23,24,25,26 after the dropped19. Gateway retained
DATA23–26 acceptance boundaries758/768/786/800. Gateway lifecycle25 at11.116UTC
has receive_next19, receive_mask254 (bit0 absent, bits1–7 set), buffered7.
Gateway ACK19/254 generated/sent at10.446 and10.676UTC, client sees19/254 at10.653.
This is positive paired head-gap/SACK evidence, not absence inferred from a ring.

Client retry seq19 attempt1 at10.686UTC, new message842410499; rtp_written/ok
same millisecond, RTP9063, timestamp1213693474. Client receives ACK19/255 at11.115,
then20/127 and21/63 at11.120,24/7 at11.132,25/3 and26/1 at11.139,27/0 at11.144.
Base34 is directly sampled11.559, eventually108 with no sender pending frames.
Gateway later receive_next77/mask0/buffered0 at13.115 confirms aggregate receive
progress beyond buffered20–26, but does not restore missing per-DATA release events.
No exact epoch, retry timer deadline or instantaneous send_next/pending snapshot
at the drop is available; do not infer these from later non-simultaneous snapshots.

Gateway lifecycle25 exports only boundary752–815; next lifecycle27 exports2358–2421.
Selected-message receive/reconstruction/acceptance/healing-ACK boundaries are not
retained. Client reverse-direction DATA19 from sender975650243/message3486193000
is unrelated and excluded. Returned healing ACKs are for the correct outbound
sequence space, but cannot independently establish every preceding media boundary.

### Continuity and extended closeout failure

Three HTTPS requests completed200 with full577-byte bodies at11.377,11.994,
12.081UTC; www.example.com resolution and independent TCP80 request/response
passed by12.843UTC. Healthy final client sample15.818UTC: same session tag,
subscriber/publisher connected, terminalNONE, no signaling/ICE failure.
Retransmissions1→2, no client RELIABLE_RETRY_EXHAUSTED before cleanup. No Family,
Telemost or orchestrator session restart/recovery was triggered. The helper uses
the existing restricted engine/AutomaticVpnOwner, not an Auto fallback simulation.
Background app traffic is visible:13 TCP opens,16 DNS responses, one mux reset/
protocol-error counter; these are not claimed to be exclusively the three requests.

Fault auto-disarmed/count1 verified15.845UTC, before explicit redundant disarm15.847.
Client normal cleanup completed16.020UTC. A later ordinary app restart was solely
the requested safe-state check after cleanup, not a session restart to mask failure.
Idle after cleanup/restart reports UNAVAILABLE/armedfalse, not literal DISARMED.
Temporary test package removed, owner package/identity/enrollment preserved.

Extended paired closeout changes the provisional PARTIAL assessment to **FAIL**:
gateway lifecycle37 at07:28:24.478UTC reports RELIABLE_RETRY_EXHAUSTED,
reverse send_base104/send_next112/pending8/head_retries8/ACK104-mask124;
receive_next108. This is8458ms after client cleanup and on gateway→client DATA104,
not selected client→gateway DATA19. Gateway cleanup completes24.485UTC;
PID1000816/NRestarts0 remain unchanged. No no-exhaustion claim is valid across
this closeout. Whether normal client cleanup explains that terminal is unproven;
do not attribute it to the controlled outbound loss or hide it as irrelevant.

Classification UNKNOWN: no specific missing stage for DATA19 is proven. In
particular RTP_NOT_RECEIVED_REMOTE is NOT established. Application recovery passed;
APPLICATION_NOT_RECOVERED would misstate these controlled-request observations.

### Preservation, rollback and next step

Protected paired evidence: state-client-build/field65-export16/owner-controlled-loss-1/.
instrumentation.log contains303 native snapshots plus fault/traffic/cleanup receipts;
gateway.jsonl is the first bounded interval, gateway-closeout.jsonl includes complete
same-session closeout. Initial SSH collection timeout was retried read-only; the
experiment was never retried. Derived client/gateway-boundaries.json retain indices;
analysis.txt and evidence-manifest.json record evidence and file hashes.
identity-preflight.json, immediate/, immediate-phone.json and cleanup.json retain
preflight/final safety receipts without private identity/profile contents.
Evidence-consistency assertions and sealed source-input hash checks PASS;
requested-document link check (3 files/428 links), privacy checks and
git diff --check PASS. These checks do not promote the physical gate to PASS.

No rollback, product build, version change, credential renewal, transport tuning,
public beta66 publication or catalog/invitation/default update. Public channels
remain as recorded by DIAG-PAIR-DEPLOY-1; no public rollout is claimed here.
Rollback remains the accepted deployment runbook: verify preserved previous gateway
before narrowly restoring its executable; never restore expired credentials or lower
floors. A non-debuggable beta66→65 downgrade is not presumed safe; no uninstall/data
clear of the owner app is authorized or performed.

Exactly one recommended next step: a separate investigation of the selected retry's
remote receive-boundary evidence gap, using preserved evidence and unchanged pair.
Do not repeat the physical fault, start soak/impairment/Krasnodar, or tune transport
as part of this completed task. Strict PASS and local soak promotion remain blocked.

## Historical preflight STOP, PARTIAL — 03:34 UTC (superseded)

The physical gate and subsequent soak were NOT started. Root cause remains
**STILL UNKNOWN**. No missing transport stage was proven.

## Read-only preflight (2026-10-06 03:34:25 UTC)

- HEAD: `8d046321039d0bd1e18ecc1af979ff90f591e029`, dirty worktree including
  FIELD65-DATA-HOLE-1 instrumentation and pre-existing unrelated changes. HEAD
  alone does not identify the diagnostic source. Nothing committed or reset.
- Owner Redmi Note 9 Pro, package `com.familyconnect.app.friends`, UID10283,
  versionCode65 / `0.1.18-beta65`, last update2026-10-04 22:19:48 device time.
  Wi-Fi setting0, mobile-data setting1; active default network197 is validated
  cellular LTE. No network setting changed.
- Owner Support ID `FC-4D8Q-REEG`: admitted/non-revoked, readiness revision3,
  minimum CRL6858. Last stored ACK says READY but expires1791228132; current
  readiness is FALSE. This is server-side enrollment/readiness evidence, not
  fresh validation of the private identity stored on the phone.
- RU admission list has2 devices; both non-revoked/admitted. Tester revision1,
  minimum CRL7377, also currently not ready. No tester contact or test initiated.
  Fresh full signed-grant validity was not established.
- NL service active, PID779376, NRestarts1. These differ from historical
  PID652351/NRestarts0; reason/time of intervening restart UNKNOWN. Do not
  attribute it to this task or to a Reliable DATA hole.
- Loaded gateway SHA256:
  `7c6e1e11208e167309cbe83dac0f5f1f1bb306f4e41628180367aa6fa5e9aa50`.
  This is the previously deployed RTP-timer fix, NOT the new diagnostic binary.
- Actual control-listener TLS leaf equals profile leaf and verifies against
  the profile authority. Expiry2026-10-05 23:53:04 UTC: already expired.
  Issuer expiry2026-10-06 13:51:23 UTC; signed CRL expiry07:34:12 UTC.
  Minimum observed chain headroom **-13282 seconds**. Signature validity is
  not temporal validity; no READY assertion is made.
- RU/NL directory bytes match, SHA256
  `4c6b96bb309e6e45c43cd1c5f2f461cf9f63da75ea28c16ddc761d643ef2eda3`.
  Equal generation does not make expired credentials usable or prove a new
  diagnostic pair compatible.

## Diagnostic provenance and installation gate

Existing FIELD65-DATA-HOLE-1 local artifacts were freshly SHA256-checked:

| Component | SHA256 | Runtime state |
|---|---|---|
| Unsigned diagnostic Friends APK | `f686988d8da15b4ffced81efc6d8e9e9041286b65543bb5e884f7af0419f1d6e` | Not installed; internal beta65 metadata, not publishable replacement |
| ARM64 JNI | `49406ddb8a6672804bf97b75a13131d1c830219791650e1247973d629ab5f6bc` | Local only |
| Diagnostic gateway | `ce017d8fd5b3fa9c7c11597d7002dd6904eccc9b0431445fae07c6af941fc426` | Local only |

Source/build provenance and previous JNI-to-APK equality receipt:
[FIELD65-DATA-HOLE-1](2026-10-06-field65-data-hole-1.md). These are dirty-worktree
artifacts, not an exact-source CI release. Installed signer/install compatibility
was NOT freshly verified; installation remains prohibited until it is verified
and a separate diagnostic build preserves UID/data/identity. No beta65 public
bytes, catalog, default or invitation route changed.

## Fault contract and complete physical evidence table

Planned only: arm one test-only drop after Family session establishment for the
first eligible outbound Reliable DATA, record logical N, drop attempt0 only,
allow all retries and ACKs. Do not modify retry/RTO/pacing/buffers/TLS/Mux/TUN,
session lifetime, keepalive or recovery. Runtime fault hook was not armed or
validated. Unit-test loss fixtures are not a physical injection facility.

Chosen DATA seq: **UNKNOWN / not selected**. No session or attempt was started.
Every row below is physical evidence, not imported deterministic-test evidence.

| Stage | Seq / attempt | Evidence |
|---|---|---|
| Reliable DATA created | N / UNKNOWN | UNKNOWN |
| attempt0 selected | N / 0 planned | UNKNOWN |
| attempt0 intentionally dropped | N / 0 planned | UNKNOWN |
| Later DATA sent | N+1 onward / UNKNOWN | UNKNOWN |
| Remote receiver observes gap | N / UNKNOWN | UNKNOWN |
| SACK/receive_mask reflects later DATA | N / UNKNOWN | UNKNOWN |
| Retry attempt1 created | N / 1 planned | UNKNOWN |
| New carrier message ID | N / 1 planned | UNKNOWN |
| New VP8/PictureID/timestamp | N / 1 planned | UNKNOWN |
| New RTP sequence range | N / 1 planned | UNKNOWN |
| RTP writer emitted | N / 1 planned | UNKNOWN |
| Remote RTP receiver observed | N / 1 planned | UNKNOWN |
| VP8 frame reconstructed | N / 1 planned | UNKNOWN |
| Carrier message completed | N / 1 planned | UNKNOWN |
| Reliable DATA accepted | N / UNKNOWN | UNKNOWN |
| ACK generated | N / UNKNOWN | UNKNOWN |
| ACK sent | N / UNKNOWN | UNKNOWN |
| Sender ACK received | N / UNKNOWN | UNKNOWN |
| send_base advances beyond N | N / UNKNOWN | UNKNOWN |
| Buffered later DATA released | N+1 onward / UNKNOWN | UNKNOWN |

Real Telemost RTP emission/remote reception, Reliable healing, HTTPS/DNS
continuity without restart, retry exhaustion and resource bounds: **UNKNOWN**.
Gate-session restart: UNKNOWN (no test session). No soak, CPU/RSS sampling or
recovery-count acceptance was performed. No causal inference from counters.

## Regression receipts and safe preparation

This task re-read existing local receipts, NOT rerun tests: full Go and race
14 packages PASS, JVM11 PASS, Python privacy/correlation32 PASS, native packet
race PASS. Prior task records A–E/all attempts0..8, diagnostic bounds, Friends
Gradle258 tests and lint0 errors/37 warnings PASS. These remain prior results,
not a new physical gate or fresh post-change regression. No runtime/code changed.
Before a future physical gate rerun relevant Go/A–E, affected race, Android,
native, privacy and bounds checks against the actual diagnostic build.

Local execution also hit `Quota exceeded`: sandbox could not create `/tmp/.git`
mount target; even an outside-sandbox shell heredoc failed before creating the
proposed preflight script. Read-only preflight instead ran in memory and returned
only allowlisted metadata. No existing files/caches were deleted to make room.

Read and retain the existing
[credential renewal runbook](../../deploy/friends/restricted/GATEWAY_RENEWAL.md).
Safe preparation completed: current installed package/UID/network, server
admission/readiness, actual loaded TLS leaf, gateway bytes and RU/NL generation
checked; exact candidate hashes recorded. Renewal NOT attempted. The chosen
safe-preparation-only stop avoids starting a short-lived window while the
matching install-compatible diagnostic pair and physical injection are not
ready. Renewal requires protected durable receipts and validation scratch;
/tmp-backed sandbox/heredoc paths failed, although direct repository document
writes succeeded. No claim that all local storage is unwritable is made.

## Cleanup, rollback and remaining work

No APK installation/signing, gateway deployment/restart, credential renewal,
admission/floor change, fault injection or phone network change. ADB was used
only for read-only evidence, never transport. No private profiles, keys, product
DB content or release signing secrets exported. No runtime restoration needed;
existing local diagnostic artifacts retained, no new diagnostic APK to remove.
No observer, background traffic generator or fault remains running.

Existing operational rollback reference remains the prior report path:
`/opt/apps/family_connect/restricted-materials-stage-20261001/rtp-gap-8d04632-20261005/bootstrap-broker.previous`.
It was not accessed or used; do not restore expired credentials or lower floors.

Result **OWNER-CONTROLLED-LOSS-1 = PARTIAL (preflight STOP)**, not transport FAIL.
Earliest proven blocker: expired loaded gateway leaf and non-current owner
readiness, before any test DATA. Earliest missing transport stage: UNKNOWN.
Next single step: finish safe diagnostic-pair preparation (durable scratch,
exact source, compatible separate APK and one-shot physical fault control).
Then JIT runbook renewal with fresh native owner READY and RU/NL generation
verification is required before physical gate.
Owner15-minute cellular soak remains conditional on controlled-loss PASS.
Krasnodar stays closed; even a future PASS plus stable soak only justifies a
separate owner impairment/soak gate, not automatic field expansion.
