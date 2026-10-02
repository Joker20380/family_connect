# 5N-HTTP-CANDIDATE-PREFLIGHT — local contract correction, 02.10.2026

## Scope and provenance

**5N-HTTP-CANDIDATE-PREFLIGHT = PASS** locally. Local configuration, acceptance
harness, tests and documentation only; no production deployment authorization.

- Starting HEAD: `57206fe8a6e3c7d50db1f2759a2aa29e90e6e429`.
- HTTP archive: `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
- Sync archive: `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`.
- No runtime source change, archive rebuild, authority signing/renewal, SSH,
  production service operation, Redmi, Android build, version/public release or push.
- Retained #10 evidence records a pre-deployment STOP, not an unsuccessful live
  switchover. #9's exact historical429/502 attribution remains partially UNKNOWN.
- Ignored owner-only evidence: `state-client-build/http-candidate-preflight/`;
  entry file snapshots, initial/final test outputs, preservation/index receipts.

## Port ownership and candidate policy

No production audit was repeated. The source/runbook plus #10 readback establish:

| Port | Owner / evidence | Policy |
| --- | --- | --- |
| 18080 | Documented XHTTP origin default | Not a candidate |
| 18082 | Existing product API in nginx template | Not a candidate |
| 18084 | Ordinary Friends HTTP; retained RU PID1566654 | Not a candidate |
| 18085 | Friends TCP/Xray API; retained RU PID1908885 at02.10 11:01:32UTC; AWG registration also consumes this API | Explicitly forbidden |
| 18444 | NL restricted bootstrap broker, committed loopback unit | Not a candidate |
| 18086 | New singleton candidate allowlist; no previous documented reservation found | Explicit configuration plus fresh host preflight required |

**18086 is not claimed free on production.** `Candidate(port, generation, artifact,
sha256)` has no default/fallback port. It accepts only18086, never a known reserved
port, boolean/string/zero/public port or dynamically scanned alternative.
Preflight checks all listener addresses at the requested port using bounded `ss`,
then attempts a loopback bind. Existing/unknown listener ownership fails closed.
Trusted prior PID/start metadata can label an occupied previous candidate, but
does not authorize reuse, replacement or stopping it. Receipts precede verdict.

The unit contains `@CANDIDATE_PORT@`, intentionally not a ready-to-install default.
Render it only through successful `Candidate.preflight`/`render_unit`. SO_REUSEADDR
matches normal handler TIME_WAIT behavior; no SO_REUSEPORT/listener override.
Preflight cannot eliminate the bind race: a subsequent collision causes failed
candidate startup, no ingress modification and no stop of the colliding owner.

Before readiness, the process handle must be alive and match PID/start identity,
isolated archive argv/port and expected archive SHA. Socket metadata must show
exclusive127.0.0.1 ownership by that PID. Wildcard, other address, IPv6 and missing/
unknown/foreign ownership fail. Checks repeat around probes and before switch.
Adapters are bounded injected actions; no SSH/systemd deployer is introduced here.

## Route layers, generation and receipts

Machine-readable `ROUTES`, `DIRECT_PROBES` and `EXTERNAL_PROBES` live with the
operator. The existing immutable artifact/receipt CLI are not rewritten.

| Probe | Direct candidate | External ingress | Owner |
| --- | --- | --- | --- |
| A `/status/server-load.json` | Excluded; no GET readiness gate | 200 + nginx generation | nginx static alias |
| B ordinary malformed challenge | 400 | 400 | Friends application |
| C safe ordinary chat challenge | Established400 | Established400 | Friends application |
| D restricted malformed challenge | 400 | 400 | Friends application |
| E non-canary challenge | 403 | 403 | Friends application |
| F canary challenge | 200 + bounded shape | Same | Friends application |
| G canary readiness | 200 + cryptographic validation | Same | Friends application |

Direct handler501 for A is intentional and **not readiness failure**. The direct
Session refuses nginx-owned probes before network I/O. Direct generation is proved
by process/socket metadata; it does not require nonexistent handler trace headers.
External candidate acceptance requires correlated generation, static/proxy origin
and upstream status. Both matrices require proof/validation callbacks and run
serialized at≥1s request spacing, with3s I/O bounds. No independent rapid observer.
Synthetic identity proof is used only in fixtures; real deployment still requires
real owner/non-canary identities and no private-key extraction.

Durable probe fields: `layer` (`direct_candidate`/`ingress_external`),
`candidate_port`, `route_owner`, `probe_id`, `active_generation`, status, response
origin, upstream/connect/limiter classifications and transport error. Direct ingress
limiter is `not_applicable`; absent external correlation is UNKNOWN. Port/preparation
receipts include safe classification, SHA and process start metadata. No credentials,
response bodies, identities, proofs or raw command lines are recorded.

## Transaction and recovery contract

Old-generation health → authorized unused candidate port → start new candidate →
process/socket/artifact verification → complete direct B–G → render/validate whole
candidate ingress → atomic switch → external paced A–G → commit → confirmed
old-worker drain → retire old generation. Candidate location rendering replaces
exactly two explicit ordinary/restricted upstream placeholders with the verified
port; nginx static A and unrelated upstreams are preserved. A callback returning
true without completing its matrix cannot authorize switch/commit.

Rollback: persist primary failure → restore original routing → verify old external
200/400/400 → confirm nginx worker drain → stop only the new owned candidate handle.
Preflight collisions never reach prepare/switch/stop. Uncertain restoration/drain/
identity retains candidate. After commit, failed old-worker drain retains the old
runtime and records committed state, rather than killing it or replaying deployment.
The internal `_transaction` tests preserve prior failure-order coverage; deployments
must use the guarded public `transaction`, not that primitive.

Rollback of this local correction is a revert of its task-owned commit; no server
rollback or database restore is needed. Future live rollback still preserves
authoritative DB/revocation history, ordinary listeners and private evidence.

## Authority handoff for separately authorized attempt #11

Do not assume CRL/gateway-only refresh. Check **delegation and issuer certificate,
owner grant, CRL, gateway credential**, plus acceptance-window coverage; renew through
accepted machinery where necessary. #10 observed delegation/issuer/owner expiry
02.10 10:44:11UTC, gateway10:31:33UTC, CRL18 at09:48:20UTC. Staged16 is older than
RU runtime/DB/NL floor18. These are historical timestamps, not refreshed validity.
Keep the same Family/issuer key/gateway/sole owner,0 other admissions, unchanged TTL
and security policy, and monotonic delegation/revision/CRL floors. Offline root
signing stays local. No authority material was renewed in this task.

## Validation and Git finalization

Focused suite: **118 PASS,0 skips,128.55s** (`final-focused.xml`/`.log`). Tests cover free port, unrelated and
previous-candidate collisions, TOCTOU bind loss, loopback/wildcard/non-loopback,
generation/artifact mismatch, direct B–G and external A–G, route ownership,
incomplete-matrix rejection, real isolated nginx switching and rollback, uncertain
restore/drain, pacing, durable redacted receipts, isolated helper loading and source
guards. Actual systemd/production startup remains untested by design.

Documentation validation:423 files,2574 links,0 errors. Staged public-source guard:
1592 entries,0 blocked. `git diff --check` and staged whitespace checks PASS.
Both immutable archive inventories and bundled tracked sources still match HEAD;
no exception for a changed bundled source is used.

Initial local runs exposed a missing musl loader invocation and an incorrect sync
test environment path (directory instead of archive); neither changed production
or artifacts. A bind probe initially treated TIME_WAIT as collision; it now uses
the handler's normal SO_REUSEADDR behavior while all occupied-listener tests still
fail closed. Initial sandbox socket denial was handled with approved localhost-only
test execution. Failed runs are not reclassified as PASS.

Commit scope is only task-owned harness/config/tests/runbook/report and new
STATUS/PLAN entries, with subject `fix(friends): separate candidate readiness from ingress acceptance`.
All9 pre-existing dirty/untracked files are preserved; their pre-existing changes
are excluded from the index. Final SHA/preservation readback is retained with the
local evidence and reported in the handoff. No push. **STOP: no deployment attempt
#11, DIAG-1, beta or FIELD-1.**
