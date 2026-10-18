# WARM-START-EVIDENCE-ATTRIBUTION-1

## Result: PARTIAL — functional PASS preserved; historical attribution incomplete

**Функциональный warm-start доказан, но для формального gate требуется один новый
прогон с улучшенной серверной атрибуцией.** No new live run was performed here.
The prior attempt remains consumed; this task creates no new CONNECT authorization.

| Result | Classification |
|---|---|
| CORE_WARM_START_FUNCTIONAL | PASS_IN_TESTED_SCENARIO |
| FULL_TUNNEL_EGRESS | PASS |
| TRAFFIC_AFTER_LEASE_DEADLINE | PASS; three complete requests started after the old deadline |
| HISTORICAL_TIMELINE | Reconstructed from sealed receipts, with provenance/confidence per row |
| HTTP403_ATTRIBUTION | Both ATTRIBUTION_NOT_RETAINED; neither assigned to owner or another client |
| OWNER_PROVISIONING_CLIENT_BLOCK | PASS; two pre-dial blocks, unchanged cache/native input |
| OWNER_DIRECT_PROVISIONING_CLIENT_SIDE | BLOCKED / PASS |
| OWNER_PROVISIONING_SERVER_ATTRIBUTION | PARTIAL |
| OWNER_DIRECT_PROVISIONING_SERVER_SIDE | ATTRIBUTION_INCOMPLETE; NO_ACCEPTED_REQUESTS_PROVEN within the measured DB interval |
| LEASE_CLIENT_EVIDENCE / LEASE_CLIENT_CONTINUITY | PASS; authenticated confirmation, same session, sequence1 |
| SERVER_LEASE_RENEWAL | CLIENT_PROVEN_SERVER_RECEIPT_NOT_RETAINED |
| LEASE_SERVER_CORROBORATION | NOT_RETAINED as an independent renewal/state receipt; post-deadline gateway traffic corroborates continuity |
| ORIGINAL_ACCEPTANCE_CRITERION | Owner-scoped B (zero owner attempts), plus D (no import/ACK), not C alone |
| HISTORICAL_FORMAL_ACCEPTANCE / FORMAL_ACCEPTANCE | PARTIAL; criterion not relaxed |
| PROVISIONING_COLLECTOR_PATCH | LOCAL_SOURCE_ONLY; real closed HTTP handler integration and fixture accepted |
| LEASE_COLLECTOR_PATCH | LOCAL_SOURCE_ONLY; real authenticated Family/Mux renewal fixtures accepted |
| LOCAL_TESTS/RACE/PRIVACY | Targeted PASS; executed baseline differential has no new failure name; full legacy suite NOT_GREEN |
| NEW_LIVE_RUN_REQUIRED | YES to close the original strict evidence gate |
| DEPLOYMENT / OWNER_CONNECT | NOT_RUN / NOT_RUN |
| WHITELIST_WARM_START_READY / WHITELIST_COLD_START_READY | NO / NO |
| PUBLIC_RELEASE / REAL_RESTRICTED_NETWORK_FIELD | NOT_RUN / NOT_RUN |

## Integrity and immutable inputs

Previous report: [Telemost workability](2026-10-12-telemost-workability-proof-1.md).
All **1616** entries in its `SHA256SUMS-final` were verified before analysis and again
at closeout. Manifest SHA256:
`0b63d1e4115ae20bdc3fdadda5bc8f76c8f593a86f634c5358cf6d5517229f29`.
The earlier classifier capsule's **122** entries also verify; manifest SHA256:
`b445353a408971ac478072ce54e472921881df6e35359126be2de31f57cdcba3`.
Original RESULT, captures, TIMEOUT receipts and reports were not rewritten.

New protected/local capsule:
`state-client-build/field65-export16/warm-start-evidence-attribution-1/`.
It includes `timeline.md`, `receipts/timeline.json`, `receipts/http403-attribution.json`,
`receipts/historical-evaluation.json`, `source.diff`, `scope.txt`, `manifest.json`,
`SCHEMAS.md`, two JSON schemas, fixture receipts, test logs and `SHA256SUMS`.
`evaluate.py` re-verifies immutable inputs before independently recomputing the result.
No SSH, journal, systemd query, ADB or owner lifecycle action was executed.

## UTC timeline

Full rows, source filenames, request/session correlation and confidence are in
the capsule's `timeline.md`. UTC is for presentation, not proof of cross-host clock
identity. Monotonic clocks from different hosts are not compared. The existing Mux
correlation uses its saved gateway clock mapping; session tags, protocol sequence,
wire tuples and endpoint nonces supply the joins, not temporal proximity alone.

| UTC, 12 October | Event | Evidence / correlation |
|---|---|---|
|16:52:44 | Gateway start | Saved systemd invocation1613fa1c…6829f, PID1415977; historical only |
|17:35:22.700 | Operator ACK | Host operator receipt |
|17:35:51.106 | Gate ARMED | Generation a73e95dd…34e3; absolute expiry17:50:51.106 |
|17:36:22.028 | Block operation1 | Client provisioning-only receipt, same generation |
|17:36:28.793 | Physical CONNECT corroborated | ORCHESTRATOR DISCONNECTED→CONNECTING, connection5d93a06c…568b |
|17:36:28.894 | Block operation2 | Client provisioning-only receipt |
|17:36:29.087 | Native attempt1, exact cached directory | Directory252c3535…e4341, same connection |
|17:36:46.018 | Descriptor issued | Client authenticated-session trace; independent server exchange start NOT_RETAINED |
|17:36:52.604 | Dedicated Family TLS established | Session776990f9…e5f3 |
|17:36:57.466 /17:37:00.090 | Native session established / harness READY observed | Same session; observer polling time is not transport event time |
|17:37:00.736 | Initial authenticated lease confirmed | Trace event23; deadline17:46:39.097 |
|17:37:03.860 /17:37:07.613 | IPv4 / normal HTTPS complete | Separate Android nonce, Mux/outbound/endpoint/response joins |
|17:37:17.384 | Controlled DNS complete | Gateway DNS path, separate nonce |
|17:39:11.903 /17:42:07.108 | HTTPS complete | Separate correlated nonces |
|17:42:19.487 /17:42:19.725 | Two upstream HTTP403 | Probe IDs below; no requester/session join |
|17:44:43.828 | Renewal requested | Same session, lease sequence1, trace event395 |
|17:44:45.849 | Authenticated renewal confirmed | Same session, sequence1, event397; new deadline17:54:44.145 |
|17:46:39.097 | Original lease deadline | Confirmed deadline, not an observed expiry event |
|17:47:16.865 /17:48:38.712 /17:49:03.777 | Three further complete HTTPS responses | All requests began after the old deadline; same gateway session |
|17:49:28.036 | Gate CLEANUP | Client receipt; host receipt arrived17:49:28.984 |

The gate was active from arm through cleanup, not through its unused absolute expiry.
Seven HTTPS responses plus one DNS operation,3581 response bytes,723.814s observation.
Manual reconnect0, automatic recovery0, native attempts1, unexpected closes not observed.
Parallel stream series remains NOT_RUN; no additional performance claim is introduced.

## HTTP403 attribution

| Field | First record | Second record |
|---|---|---|
| UTC |17:42:19.487 |17:42:19.725 |
| Probe/request correlation | `37524ae703d84bc6808820a106cda92d` | `6510b07995814dcca116f254b17bdcb2` |
| Role retained | Restricted-readiness challenge | `other` bucket: exact role NOT_RETAINED |
| Status / upstream_status |403 /403 |403 /403 |
| Limiter result | Request and connection limits PASSED | Same |
| Response-producing boundary | Upstream HTTP403; exact safe application rejection class not retained | Same |
| Method / proof/auth stage / certificate/admission category | NOT_RETAINED | NOT_RETAINED |
| Requester / exchange / owner session | NOT_RETAINED | NOT_RETAINED |
| Gate state | ACTIVE_WINDOW | ACTIVE_WINDOW |
| Classification | ATTRIBUTION_NOT_RETAINED | ATTRIBUTION_NOT_RETAINED |

The saved nginx configuration logs only requests with a syntactically valid
`X-FC-Probe-ID`. This is correlation supplied by a client, **not authentication**;
unprobed requests are outside that log's coverage. `generation=attempt17-0615953`
is HTTP deployment generation, not the owner test gate generation. `other` also
covers ACK-related routes; it cannot be labelled non-provisioning. Neither source IP
nor time identifies a principal. Exact probe IDs occur only in the saved post-counter
receipt, not in another retained identity-bound exchange record.

The owner DB query counts newly **accepted** challenge/fetch/ACK rows, not rejected
or malformed attempts. All three deltas are0. That observation ends at the saved
counter snapshot17:49:16.785; it is not silently extended to cleanup17:49:28.036.
No owner direct request is proved, but no independent zero-attempt claim follows.
No forbidden historical journal queries were retried.

## Acceptance criterion and lease independence

The original task's shorthand “server requests after arm=0” is owner-scoped by the
owner-only test and explicitly by the final prior report's first missing boundary.
The current task confirms this scope. Thus use **B+D**, not an absolute zero for all
clients (A), and do not silently substitute **C+D**. C+D has strong positive evidence:
accepted owner rows0, no new owner import/ACK, unchanged cache/vault and exact native
cached input. It does not close B. Even a literal global-A reading would not justify
promoting this episode to PASS.

`exchangeLease` in the exact observation source verifies authenticated offer,
setup ID, sequence, expiry/remaining policy, `accepted`/`limited`, and an exact
`confirmed` response before emitting client `confirmed`. It is not a local timer.
Server `leaseBinding.renew` reauthorizes, checks the current Active holder, setup,
security bounds and sequence, extends the existing lease and returns the receipt;
the handler revalidates before confirmation. Sequence1 and unchanged session plus
post-old-deadline egress are strong evidence of real authenticated continuity.

What is missing is an independently retained server acceptance/state transition:
no saved server holder-generation/old-deadline/new-deadline/renewal sequence receipt
for this invocation. Effective argv did not enable the old peer/admission collectors;
stale files/drop-ins from previous invocations cannot be borrowed. The two distinct
bounded journal captures retained `COLLECTION_LIMITATION_TIMEOUT_NO_RETRY`,0 records.
Their results were read locally, not repeated. Mux/TCP/endpoint evidence corroborates
traffic, not a newly invented server renewal log. Therefore use
`CLIENT_PROVEN_SERVER_RECEIPT_NOT_RETAINED`, not “renewal absent” and not independent
server `PROVEN_BY_STRUCTURED_RECEIPT`.

## Source-only collectors and evaluation

Provisioning: optional collector around all four existing HTTP provisioning routes,
including malformed/denied requests and requests without a probe header. Existing
production proof verification annotates the request; no new authentication decision.
Server-generated request IDs, per-capture HMAC requester/challenge tags, explicit
claimed versus signature-verified state, existing import correlation, HTTP outcome.
No source-IP identity inference. No body/profile/key/token/header/raw-error logging.
No new endpoint or changed response. Queue/file I/O is outside handler/DB locks.

Lease: per-operation state receipt after the existing holder lock is released;
immutable separate acceptance, confirmation-write and completion records. It retains
actual old/new deadlines, real sequence, existing session tag, same-holder result,
safe auth/policy/context state. No device identity. A replay appends its own outcome,
never overwrites the earlier success. Confirmation is queued before best-effort done
or cleanup; `WRITE_SUCCEEDED` is not falsely labelled peer receipt. Existing client
done is best-effort followed by Reset, so server `PEER_DONE_RECEIVED` is optional.

Both: private0700 directories/0600 files, bounded queues/retention/lifetime, atomic
small JSON, async file fsync, write/drop/eviction accounting, bounded shutdown drain.
Provisioning also writes a bounded atomic progress checkpoint, so a future capture
can be closed out without restarting the API. The evaluator requires matching capture,
file count, drained queue/no in-flight handler, coverage through cleanup and no loss.
Completed preparation is excluded; an overlapping in-flight owner request is not hidden.
Optional diagnostics are disabled by default; initialization/write failure does not
change the HTTP response or lease decision. There is computational observer overhead;
no production latency/observer-effect measurement is claimed in this offline task.

**Remaining collector boundary:** an unauthenticated claimant is not authenticated
as a device; a malformed/unidentified request remains ambiguous. Pre-HTTP/TLS ingress
is outside application capture. The evaluator must still return PARTIAL in those
cases, not guess another client. Before any deployment reconcile this archived API
source with the actual closed server artifact and explicitly review capture coverage.
The gateway base is exact; no fresh API/gateway/phone query was made here.

## Local validation and provenance

| Check | Result |
|---|---|
| Python collector matrix |13 PASS; real packaged challenge/fetch/ACK, two concurrent clients on same loopback IP, spoofed shared probe ID, missing correlation, rejection, retention, write failure, expiry, late callback, privacy |
| Packaged HTTP baseline/patched | Same200 challenge/fetch,400 malformed challenge,503 existing malformed fetch,403 unrelated rejection, same revision/floor |
| Existing Python differential | Baseline and patched each97 PASS,4 SKIP,1 identical old Android source-guard assertion failure |
| Lease baseline race×3 |96 test/subtest PASS events, no skips |
| Lease patched race×3 |141 test/subtest PASS events, no skips; accepted/rejected/stale/replay/timeout/cancel/wrong generation/expiry/cleanup/two renewals/write failure, plus existing races and real Family/Mux traffic |
| Fatal/peer/ownership regression race×3 |69 test/subtest PASS events, no skips |
| Evaluator |9 PASS: unknown403, shared correlation, exact authenticated exchange join, incomplete coverage, missing receipt, wrong generation/collector/sequence, pre-arm/in-flight handling |
| Privacy/retention | Allowlisted synthetic receipts, no raw identity/profile/token/URL/IP; bounded per-process output |
| Full bootstrap | Not rerun; six historical diagnostic failures and baseline busy-wire flake remain separate, NOT declared fixed/green |

Initial new fixture expectations exposed two existing contracts, not product regressions:
duplicate probe correlation conflicts with the readiness DB; malformed fetch is503,
and final Mux done is best-effort. Fixtures were corrected to measure those contracts;
existing baseline assertions were not weakened. Initial failing logs are retained.

- Exact base commit: `a4087e000fdbe674b72ede3a6c8822445c87c654`, plus sealed SIGNAL_READ delta
  `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b`.
- Prior deployed gateway binary: `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` (historical, untouched).
- New collector diff: `0cb0e59da551a2291be0225a8ef885fea6d3a3e1441e9dc09952071387fec22a`.
- Local source-tree digest: `c774f04dad946b8500668269aa3ed6b9e33b4319d6fd2afeb377a05880545fab`.
- Local-only candidate binary: `972613a702f1e32a673cebed4cdee3c4dabfd474c44bc14e9c3616734d68a9c1`.
- Toolchain go1.26.1, `-trimpath -buildvcs=false`; manifest/file hashes, not a falsely claimed new clean commit.
- No commit/push/tag/release; main dirty product tree preserved. Patches exist only
  in the isolated capsule, and include no Telemost/Reliable/TUN/APK behavior changes.

## Final state and one next operation

All task owner/gateway live-action counters are0. Research84 and production gateway
were not touched. Last **historical** owner state: VPN OFF, app/chat ON, gate CLEANED;
current state was not re-read. Last historical gateway invocation1613fa1c…6829f,
PID1415977/NRestarts0; not represented as current liveness or credential readiness.
Cache/enrollment/publisher/history/AWG and all original receipts remain untouched.

First formal blocker remains **OWNER_PROVISIONING_SERVER_ATTRIBUTION_NOT_RETAINED**;
independent server lease receipt is also not recoverable from the sealed inputs.

**One next operation:** a separately authorized evidence-completion run with accepted
structured collectors (including separate controlled deployment/preflight), reusing
research84, exact cache selection, ACK-before-arm two-phase gate and the existing
ordinary Android egress harness. It requires one new physical CONNECT authorization;
none is exercised automatically. No cold-start, FIELD, public release or tester delivery.
