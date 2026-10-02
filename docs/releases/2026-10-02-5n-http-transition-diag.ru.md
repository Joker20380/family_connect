# 5N-HTTP-TRANSITION-DIAG — local diagnosis after attempt #9

## Verdict and evidence boundary

**5N-HTTP-TRANSITION-DIAG = BLOCKED** on exact historical attribution, not on local
reproduction or tests. The recorded schedules reproduce the429 class, including
the seventh non-canary rejection, on the **exact production nginx1.30.4 binary**.
The retained stop-before-start sequence reproduces direct connection refusal and
nginx502. A paced readiness-first handoff passes local A–G and bounded repetition.

However, #9 retained no response headers, ingress request IDs, upstream statuses,
limiter-zone attribution or kernel errors. Production had `access_log off` and
`error_log /dev/stderr crit`; bounded docker logs for the window contain zero bytes.
Two bounded service-journal reads (10s; current-boot15s) timed out, not evidence of
no lifecycle events. Exact rejecting bucket for **each historical429**, and exact
upstream/kernel cause of the historical502, cannot be asserted from that gap.
The strict requested PASS criteria are therefore **not all met**. Do not convert
successful replay into a claim that missing historical fields were captured.

Attempt #3 cause remains **UNKNOWN**. Attempt #9 remains historically failed/rolled
back. Its report, all77 local evidence files and all eight entry dirty/untracked
files are preserved. Only this task's additive documentation and new helper/tests/
templates are changed; no rewrite of #9. No deployment attempt #10.

## Source and immutable inputs

Starting HEAD: `028300e009007e78401cc2431989c18e0810d5f9`.
Code/test checkpoint: `2d37122` (`fix(http-acceptance): pace probes and define
readiness-first handoff`). The separate documentation commit/final HEAD are recorded
in the task's final preservation receipt and handoff; a document does not embed its
own future commit SHA. Neither commit includes retained work or changes production.

- Accepted sync SHA256:
  `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`.
- Accepted HTTP SHA256:
  `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
- Neither accepted artifact/inventory nor bundled tracked source is changed.
  New transition operator is deliberately outside the frozen HTTP bundle.
- Read-only RU baseline/current nginx config SHA256:
  `4426bfa9b589fcca124aed99daaaa9dedcf04cbd2c385a322d9fd92ead925267`.
  Current ordinary API active, restricted drop-ins absent at09:51:04UTC.
- Read-only acquisition copied only nginx executable and five runtime libraries
  from the authorized RU ingress container. Local binary/library inventory retained;
  no container image/source/config/credentials exported. Local tests run1.30.4,
  not the previously available1.28.0. No production process/configuration restarted.
  Container created/started14.09 11:14:20UTC, before #9; read-only rootfs and host
  networking. Its image ID matches the digest pinned in `deploy/product-https/pilot.py`:
  `sha256:dc5069ad14f19660b141b21236140b91656bf89bbc3e2417c70ae650cd66104c`.

Evidence root: `state-client-build/http-transition-diag/` (ignored, owner-only).
`entry.json`/original-byte snapshots, redacted read-only production observations,
binary inventory, initial/final tests, reproduction records and preservation ledger.
No private body, raw proof or identity is in the public fixture/report.

## Applicable rules and response origins

| Layer/rule | Actual policy | Scope |
| --- | --- | --- |
| nginx request `per_ip` | `$binary_remote_addr`;2r/s,burst8,nodelay;1MiB zone | Shared by ordinary status/challenge/chat and additive restricted routes |
| nginx request `global_rate` | `$global_key`, map `$server_name`→constant `family-connect`;10r/s,burst20,nodelay;1MiB | Shared globally, not per route |
| nginx connection `connections` | `$binary_remote_addr`,8 concurrent | Same8443 server |
| nginx connection `global_connections` | Constant global key,32 concurrent | Same8443 server |
| nginx limit response | Request and connection rejection status429 | Built-in HTML response |
| Application concurrency | Four-slot nonblocking semaphore |429 JSON `busy`; not static status |
| Application referral limiter | Referral issue/claim path behavior |429 JSON; not the tested challenge/status paths |

No separate challenge-specific429 bucket appears in the accepted Friends handler;
ordinary malformed requests return400, denied restricted identities403. nginx
serves `/status/server-load.json` from an alias, without the application upstream.
Proxied Friends requests target loopback TCP18084, not a Unix socket. No application
middleware framework sits between this handler and nginx in the inspected design.

Historical HTML429, especially the static status response, points to ingress rather
than the JSON application429 paths. Historical HTML502 and direct-loopback connection
failures point to the proxy/upstream boundary. These are strong source/receipt-based
attributions; absent headers/upstream/zone logs prevent a per-request exhaustive
attribution or excluding unseen shared traffic. **Proven replay origins:** nginx
request limiter `per_ip` for429; nginx proxy upstream connection refusal for502.
No evidence proves application crash, timeout, malformed upstream response, a
provider failure or an ingress reload race as #9's precise underlying cause.

## Actual timeline (02.10.2026 UTC)

Probe timestamps denote request start, not an instantaneous response/PID snapshot.
Coarse events have second precision; independent-host clock error was not measured.

| Time | Actual retained evidence |
| --- | --- |
|09:29:41–42 | Baseline ordinary200/400/400, restricted404; durable receipts |
|09:29:46–49 | Inert artifact/rollback staging complete; later drop-in write timestamp absent |
|09:31:41.637052 | NL authoritative PASS; journal diagnostic later times out without changing it |
|09:31:58.272226 | Full RU sync/negative/final readback PASS |
|09:33:17.340517 | First external observer probe, ordinary status200 |
|09:33:20 (coarse) | API restart requested after HTTP artifact/drop-ins installed; exact old-exit/new-bind times unknown |
|09:33:20.300386 | First ordinary difference: chat429 |
|09:33:20.755802 | Ordinary malformed challenge429 |
|09:33:20.920215 | External chat502; request elapsed149.009ms |
|09:33:20.953278–21.349155 | Four direct18084 readiness attempts record connection errors; errno not captured |
|09:33:21.482122 | Direct18084 malformed challenge400, elapsed4.483ms |
|09:33:21 (coarse) | Ingress reload-complete event, after local readiness by executed source ordering |
|09:33:21.985270–22.199689 | Matrix A–D200/400/400/400 |
|09:33:22.341091–22.626328 | Six real non-canaries403 |
|09:33:22.680946 | Seventh non-canary429; matrix FAIL; F/G not reached |
|09:33:22–29 | Failure verdict followed by scoped RU/NL rollback |
|09:33:29.141650–30.713443 | Restored200/400/400/404 |

The old observer wrote failures durably but the wrapper consumed its verdict after
the remote matrix returned. This was not instant abort on the first external429.
The new serialized Session fails immediately after its durable failing receipt.
Unknown intervals are not filled with invented systemd/socket timestamps.

## Reproduction:429 and acceptance traffic

Sanitized exact schedule/order fixture: `tests/fixtures/http_attempt9_transition.json`.
Two separate source streams are replayed separately with fresh equivalent buckets:
external observer and RU-local public-ingress matrix. Actual source-address values,
other users, network RTT and cross-host clock skew were not captured/replayed.
Requests use synthetic identities and ephemeral loopback ports, unchanged archive,
actual rate directives and exact copied nginx binary. Direct-upstream requests run
alongside matching ingress requests. Scheduling overhead is recorded; this is not
a bit-for-bit reproduction of WAN timing.

- Matrix:11 requests over0.695676s. With initial burst credit,2r/s+burst8 permits
  at most10 at these offsets. A–D then6×403 succeed; seventh E returns429.
  Direct upstream returns403 for that same request. nginx diagnostic log names
  **`per_ip`**, not global_rate/connections. All historical matrix statuses match.
- Observer:26 completed requests over5.269072s;7 request-limit rejections reproduced.
  Six historical429 positions match; one rejection moves from offset4.184409s to
  the adjacent request at3.990938s. At the latter client-start timestamp the model
  is only18 excess units (9ms of refill) beyond the bound. Ingress arrival times
  were not recorded. The historical502 position returns400 while the isolated
  upstream stays healthy. Direct malformed requests stay400. Full per-request
  historical observer sequence is therefore **not exactly reproduced**.
- A deterministic millisecond leaky-bucket test against both schedules yields the
  exact matrix failure and the same observer count/adjacent-position difference
  for2r/s+burst8; none for10r/s+burst20, assuming no competing traffic. The arithmetic
  follows the [nginx1.30.4 limiter implementation](https://github.com/nginx/nginx/blob/release-1.30.4/src/http/modules/ngx_http_limit_req_module.c),
  add-before-clamp with accounting only for admitted requests. Real nginx confirms
  the model independently. No implementation source is bundled or replaced.
- Application route tests remain unchanged. A separate valid ordinary challenge
  sequence at2-second intervals returns200/200/200. Three paced A–G matrices at
  one request/second also pass without429. This is not a population/NAT/load test.

**The old acceptance traffic can cause its own failure.** Do not disable/increase
the protective production limits or bless429 as an acceptable non-canary result.
Actual multi-client/NAT user impact remains **unknown**; users exceeding the shared
source/global policy can legitimately be limited. The tested user-like cadence is
not affected. Unseen actual shared traffic is why the historical bucket assertion
remains distinct from the proven replay bucket.

## Reproduction:502 and lifecycle ordering

Old executed order: copy exact archive/drop-ins → restart sole ordinary service
on18084 → poll local readiness → add/reload restricted ingress → external matrix.
Ordinary ingress already references18084 **throughout**. There is no second
listener, socket activation, atomic symlink handoff or graceful old-process overlap.
The readiness poll protects the later restricted ingress change, not ordinary
traffic during the service stop/start gap. `Restart=on-failure` is not a handoff.

Isolation runs the exact archive healthy on the old port, terminates that process,
probes both paths, then starts the new archive on that same port and reloads ingress:

- Healthy before: direct400.
- Gap: direct **ECONNREFUSED**; ingress **502**; nginx reports
  `connect() failed (111: Connection refused) while connecting to upstream`.
- New process accepting: direct400; ingress after reload400.

Thus a socket-unavailable window is a **proven defect in this activation ordering**,
without a process crash or malformed handler response. #9's overlapping direct
connection errors support this mechanism but did not record errno. Exact historical
502 kernel error and duration remain unproven; no claim of captured production
ECONNREFUSED or a measured production outage duration.

## Minimal local correction and receipts

No authority/CRL/BOOT-1/Telemost/sync/admission/application-handler change.
No accepted runtime rebuild, new public version, Android build or phone operation.

- New `scripts/friends_http_transition.py` reuses unchanged durable Evidence code.
  One serialized1s-paced Session, no parallel fast observer; no retries for failed
  external probes; complete A–G requires proof and material-validation callbacks.
- Separate candidate unit uses existing archive/venv/root with supported `--port
  18085`, loopback-only, existing protection settings. It is not installed/enabled.
  The ordinary18084 listener remains alive during staging/readiness/switch/commit.
- Injected transaction: prepare → direct readiness → fsynced switch intent → scoped
  atomic ingress switch → generation-aware external acceptance → commit. On error:
  persist → restore routing → prove old generation/drain → disable/stop candidate.
  Uncertain restore/drain keeps candidate alive. Storage failure never yields PASS.
- Actions are injected, not a turnkey unattended production deployer. They must be
  bounded; the helper does not preempt arbitrary Python callbacks. Runbook specifies
  command bounds, safe boot commit, drain, crash readback and no old-process kill
  during commit. This is a tested local contract, not live systemd acceptance.
- Optional new nginx snippets correlate safe probe IDs and generation with upstream
  status/connect/header timings and request/connection-limit status. They preserve
  existing limits and must be included where header inheritance requires it.
- Receipts preserve safe enums, never arbitrary headers/body/proof/client IP/device
  identifiers. Missing/untrusted correlation remains unknown. No upstream header
  with an unsuccessful connect differs from an actual upstream HTTP502 response;
  exact errno is not invented. nginx's exposed limiter status distinguishes request
  from connection policy but not individual zones: rule IDs retain alternatives.

Detailed future contract: [restricted runbook](../../deploy/friends/restricted/README.md).
Historical wrapper files stay immutable; the new helper is not silently injected
into them or into the pinned bundle. Existing sync/HTTP compatibility test now uses
the currently accepted sync pin instead of the retired one.

## Local validation and remaining boundary

Actual isolated nginx/immutable handler:

- PRE-SWITCH200/400/400/404.
- Candidate direct ordinary/restricted checks, including synthetic owner proof and
  cryptographic delegation/certificate/CRL/directory validation.
- POST-SWITCH A–G200/400/400/400/403/200/200; **three complete matrices**, no429/502.
- Three additional live reload/switches with paced in-flight ordinary requests:
  seven400 responses, old/candidate1/candidate2 generations, no429/502.
- Real isolated rollback restores routing before stopping candidate; injected
  prepare/readiness/switch/accept/commit failures and uncertain drain fail closed.
- Receipt redaction/order, no blind retry, invalid200 readiness, mandatory G,
  storage failure, isolated helper imports and source guards covered.

Final focused suite: **130 PASS, no skips,62.62s**. HTTP routes/runtime/readiness,
rate-limit schedule/replay, switch/rollback, redacted receipts, complete A–G,
ordinary access/chat, native synthetic delivery and source-guard tests included.
Docs421/links2565/errors0 and `git diff --check` PASS. Code index publication guard:
1589 entries,0 blocked. Final commit/preservation receipts are retained with the handoff.
Initial diagnostic include had an unquoted nginx regex quantifier; config
validation rejected it **locally before server start**. It was quoted and rechecked.
Initial failures are retained, never reclassified as successful reproduction.
The first independent arithmetic model also clamped before charging a request;
source inspection corrected that model. Its subsequent strict per-request observer
comparison exposed the arrival-time limitation above, not a reason to alter the
historical receipts. Both failed local runs remain in evidence. No production
configuration change was made to obtain these results.

Historical attribution remains blocked on missing contemporary header/upstream/
bucket/kernel evidence. More local tests cannot recreate those missing historical
observations; an unapproved deployment is not an acceptable way to fill the gap.
No task starts attempt #10, Redmi work, distributed beta or FIELD-1. **STOP.**
