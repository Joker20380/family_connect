# 5N-PROV-1 controlled deployment — authorization required

## Candidate preflight after #10 — local policy, no deployment authorization

`scripts/friends_http_transition.py` contains the machine-readable `PORT_OWNERS`,
`CANDIDATE_PORTS`, `ROUTES`, `DIRECT_PROBES` and `EXTERNAL_PROBES` contracts.
The immutable HTTP/sync archives and production limits are unchanged.

| Local TCP port | Ownership / evidence | Candidate use |
| --- | --- | --- |
| 18080 | Documented XHTTP origin default, `scripts/xhttp_gateway_config.py`; not a current live audit | Forbidden |
| 18082 | Existing product API, `deploy/product-https/nginx.conf.template` | Forbidden |
| 18084 | Ordinary Friends HTTP; #10 retained readback, PID1566654 | Forbidden |
| 18085 | Friends TCP/Xray API; #10 read-only02.10 11:01:32UTC, PID1908885; `deploy/friends/awg-gateway.py` | Forbidden, never stop/rebind |
| 18444 | NL restricted bootstrap loopback broker, committed unit; inactive in #10 | Forbidden |
| 18086 | Newly defined singleton candidate allowlist; no earlier reservation found | Conditional only; production availability UNKNOWN |

These are source/retained observations, **not a fresh production socket audit**.
The18084/18085 PID evidence is specifically RU;18444 is the documented NL broker.
Friends AWG registration invokes the Xray18085 API, not a separately reserved HTTP
candidate port. Public VPN data listeners are outside this localhost HTTP policy.
No other alternate HTTP port is approved.18086 is a policy choice, not evidence
that it is free. Future operators must explicitly construct
`Candidate(port, generation, artifact, sha256)` with port18086; no default, scanning,
fallback to another port, wildcard or Internet-facing allocation. Pin the helper
and immutable archive. Before any candidate/runtime modification, `preflight`
checks Linux `ss` for **any** listener at that port, then attempts a127.0.0.1 bind.
Unknown ownership and inspection failures fail closed. Existing candidate identity
from a trusted prior PID/start receipt may classify `occupied_previous_candidate`,
but still STOP; it is never adopted, overwritten or killed automatically.
SO_REUSEADDR matches the handler's normal TIME_WAIT behavior; SO_REUSEPORT is not
used and existing listeners still prevent startup.

The service file is now an **unrendered template**, not installable as supplied.
`Candidate.render_unit(template)` replaces its single `@CANDIDATE_PORT@` only after
successful preflight. Do not manually bypass this with an Environment override.
The free check cannot reserve the port through exec: if another process wins the
race, startup fails and ingress stays untouched. The bounded start adapter returns
the newly launched process handle (or a systemd adapter with authoritative `pid`/
`poll()`), waits for its own socket, and never substitutes a pre-existing process.
`capture`/`verify` recheck process liveness, Linux PID/start identity, isolated argv,
archive SHA and exclusive127.0.0.1 listener ownership. Wildcard, IPv6, other local
address, foreign/unknown PID and process/artifact changes all fail closed.

### Direct and ingress contracts

| Probe | Route owner | Direct candidate | External ingress |
| --- | --- | --- | --- |
| A status `/status/server-load.json` | nginx static alias | Never probed; handler GET501 is intentional, not readiness failure | 200 + correlated nginx generation |
| B ordinary malformed challenge | Friends application | 400 | 400 through candidate |
| C safe ordinary chat challenge | Friends application | Established400 | Established400 through candidate |
| D restricted malformed challenge | Friends application | 400 | 400 through candidate |
| E non-canary challenge | Friends application | 403 | 403 through candidate |
| F canary challenge | Friends application | 200 + bounded validated shape | Same through candidate |
| G canary readiness fetch | Friends application | 200 + cryptographically validated readiness | Same through candidate |

Use `Session(..., layer='direct_candidate', candidate=..., generation=...)` and
`matrix` for B–G; it refuses A before sending any request. Direct generation comes
from verified process/socket metadata, not invented handler headers. Then use
`layer='ingress_external'` with the same candidate/generation for A–G. Correlated
ingress generation/route origin and upstream status are mandatory for this matrix.
Both matrices require proof/validation callbacks and pace requests at≥1s intervals.
Synthetic identities are for local fixtures only; production still requires the
real admitted owner and real non-canaries, without extracting private identity keys.

The public `transaction` requires old-generation health before preflight, then
candidate start → direct matrix → render/validate → switch → external matrix →
commit → confirmed old-worker drain → retirement. It refuses a ready/accept callback
that merely returns true without completing the corresponding matrix. Render the
ordinary/restricted location snippets with exactly two `@FRIENDS_HTTP_UPSTREAM@`
placeholders using `Candidate.render_upstreams`; it derives both targets from the
verified live candidate **after** direct PASS. Preserve static status and unrelated
upstreams. The `render(upstream)` callback validates the whole configuration in a
separate file before the atomic switch; never overwrite active config during render.
`_transaction` is only an internal rollback-order primitive, not a deployment API.

Rollback still persists failure → restores original routing → verifies external
old-generation200/400/400 → confirms worker drain → stops only the newly owned
candidate handle. A preflight collision never invokes start, switch or stop.
Unknown restoration/drain/process identity retains the candidate. If old-worker
drain cannot be confirmed **after commit**, retain old runtime and record the
committed state; do not blindly replay deployment or kill either generation.

Probe receipts add `layer`, `candidate_port`, `route_owner`, `probe_id`, observed
`active_generation`, status, origin/upstream/limiter classifications and transport
error. Direct limiter class is `not_applicable`; unavailable external correlation
remains UNKNOWN, never inferred from status. Port/process decisions persist before
verdict; no body, proof, identity, credentials or raw process command is recorded.

### Attempt #11 authority handoff — not performed by this gate

Freshly inspect **delegation/issuer, owner grant, CRL and gateway credential**;
renew all expired/insufficient-lived material through the existing accepted
offline delegation signer / restricted grant and CRL machinery before starting
NL/RU. Do not assume only CRL/gateway need refresh: #10 observed delegation,
issuer and owner grant expired02.10 10:44:11UTC. Gateway expired10:31:33UTC,
CRL18 at09:48:20UTC; staged16 cannot lower the authoritative floor18.
Preserve the same Family, issuer key, gateway, sole owner,0 other admissions,
TTL/security policy, monotonic delegation/revision/CRL floors and rollback evidence.
No signing, refresh, SSH, production service action, phone, APK, push or attempt #11
is authorized by this local correction. Repeat all NL/RU/HTTP/physical gates only
under separately explicit deployment authorization.

## HTTP transition diagnosis after #9 — local contract, not deployment

[Diagnosis, evidence limits and local reproduction](../../../docs/releases/2026-10-02-5n-http-transition-diag.ru.md).
The candidate policy above supersedes the old18085 assumption. Do not reuse the archived stop/restart/fast-observer
wrapper: its probe schedule exceeds the existing per-IP policy, and restarting the
sole18084 listener while ingress still references it creates an unavailable window.
This locally reproduced mechanism does not retroactively identify every historical
429's bucket or the502 kernel error: #9 did not capture those fields.

Future separately authorized activation must use the following transaction contract,
implemented as injected actions in `scripts/friends_http_transition.py`. This helper
does not execute deployment commands, find credentials or obtain owner proofs.
Stage it alongside the unchanged `scripts/friends_http_acceptance.py` under those
exact names; both load with `python -I` outside checkout. Pin both source files.
Do not substitute the old receipt CLI bundled with the immutable HTTP artifact for
the new paced operator. The runtime archive and its existing inventory stay unchanged.

1. Save original ingress/unit metadata and fsync rollback/evidence outside runtime
   replacement paths. Verify the ordinary unit remains active on loopback18084.
   All authority/NL/RU prerequisites still apply; this diagnosis changes none of them.
2. Verify the explicitly configured allowed candidate port is unused with `Candidate.preflight`, and available memory is sufficient for a second
   bounded process. Stage the exact pinned archive, venv and candidate unit
   rendered `family-connect-friends-http-candidate.service`; do not restart the ordinary unit,
   overwrite a running candidate or enable a candidate at boot before acceptance.
3. Start candidate with a bounded command. Prove local socket accept readiness,
   direct B–G application contract and unchanged artifact/process generation; A is ingress-only.
   Readiness polling may wait for a **not-yet-routed** candidate, never retry external
   429/502 until it happens to pass. Preserve direct ECONNREFUSED/timeout categories.
4. Prepare/validate the full ingress candidate without touching limits. Add the
   existing restricted locations and change only Friends ordinary/restricted
   upstreams18084→verified candidate port; static status and unrelated upstreams stay unchanged.
   Install `http-transition-trace.conf` in HTTP context and declare a validated
   constant `$fc_http_generation` map for this configuration. In the8443 server,
   enable `access_log /protected/probes.jsonl fc_probe if=$fc_probe_log;` and include
   `http-transition-headers.conf`. Include these headers also in status/other target
   locations that already declare `add_header`, preserving existing cache/security
   headers: nginx header inheritance is not additive by default. Check rendered
   configuration with nginx before switch; record its hash, never a private body.
5. Fsync switch intent; atomically replace only the ingress file, reload nginx with
   a bounded command, and confirm expected generation. Keep both application
   listeners alive while old nginx workers drain. A reload exit code alone is not
   evidence that all workers switched or that the candidate is ready.
6. Use **one serialized Session**, one request/second, for all external A–G probes
   including all real non-canaries. Do not run an independent tight-loop observer
   concurrently. Session pacing is local to that operator, not a distributed lock:
   concurrent operators are forbidden. User traffic may still consume a shared
   bucket; any unexpected429/502 is immediate FAIL, never automatically retried.
7. `Session.matrix` requires a real-owner proof callback and a readiness validator;
   it cannot omit G. Do not extract identity keys, substitute synthetic/diagnostic
   credentials or log callback inputs/results. Validate material through the
   accepted consumer. The local test fixtures are not real-owner production proof.
8. Only after complete external acceptance, commit by enabling the selected candidate
   unit for reboot and durably recording the accepted generation. Keep the old
   listener available throughout commit/receipt writes; do not terminate it in the
   commit callback. Any later retirement needs confirmed drain and a retained
   recovery path, not a kill during ingress handoff.

Failure order: fsync primary receipt → atomically restore/validate/reload original
ingress → confirm old generation → confirm no old nginx worker references candidate
→ disable/stop only candidate. If restore/drain cannot be confirmed, **retain the
candidate**, record rollback-incomplete and stop for operator recovery. Never kill
a potentially routed process. Do not roll back DB/CRL history. A storage failure
forbids PASS; still restore routing where safe. Process death requires readback of
durable intent/current ingress/service generation, not blind replay.

`transaction` callbacks must use bounded commands (prepare/start≤30s, config
check/reload≤5s each, generation/drain≤20s); the adapter does not make an arbitrary
Python callback preemptible. Give both matrices explicit total deadlines sized for
the actual non-canary count,1s spacing,3s/probe HTTP I/O and up to two3s socket-owner
inspections per direct probe. The historical fixed20s readiness cap is insufficient
for27 paced non-canaries. Check remaining authority lifetime against the complete
planned budget before startup; abort on first failure, never retry failed probes.
Restore commands need their own bounds and evidence; an unconfirmed rollback must
not be reported as success. Source tests inject failures at every phase and use
real isolated nginx for switch/rollback, not production systemd acceptance.

Receipts add random probe ID, expected/current generation, correlation-checked
origin, upstream status/connect/header timing, direct transport error and limiter
classification. Unknown remains unknown. Nginx exposes rejected request/connection
policy, **not the exact rejecting zone**; rule IDs explicitly retain alternatives
(`per_ip_or_global_rate`, `connections_or_global_connections`). No tokens, raw proofs,
device IDs, response bodies, client IPs or arbitrary headers in probe/access logs.
The trace snippets are **not installed in production** by this task. Global limits
remain2r/s+burst8 per source,10r/s+burst20 globally,8/32 concurrent connections.

## NL acceptance after attempt #8 — local correction, not deployment

Use the standalone `scripts/restricted_bootstrap_acceptance.py` for a future
separately authorized rollout, not the archived inline NL_START wrapper. Attempt
#8 produced a valid READY-path directory but the wrapper incorrectly turned a5s
journal timeout into failure. It remains historically rolled back; no bootstrap/
provider failure is established. [Reconstruction and local proof](../../../docs/releases/2026-10-02-5n-nl-acceptance.ru.md).

Preconditions remain unchanged: pin accepted runtime/native binary/unit/helper,
verify the existing expected gateway identity and native authority/JIT material,
keep RU sync/timer and HTTP disabled, save rollback inputs, and use an owner-only
evidence location outside replaced runtime trees. This operator does not refresh
credentials, deploy files, admit devices or perform rollback. It starts only the
NL bootstrap unit once, only with explicit `--execute`; this local fix grants no
permission to run it on a server.

```sh
venv/bin/python -I /path/to/pinned/restricted_bootstrap_acceptance.py --execute \
  --runtime /path/to/pinned/restricted-sync.pyz \
  --evidence /protected/attempt-evidence/nl-bootstrap --generation attempt-N \
  --journal
```

Use a **new** evidence directory for every invocation; existing directories are
rejected, never erased/reused. `--snapshot` is a read-only internal material probe,
not acceptance. Its transient public-binding digest is omitted from durable
receipts; do not publish raw snapshot output. No cwd/PYTHONPATH source fallback.

Authoritative success: inactive unit and absent old export before start; CRL and
gateway leaf have >600s left; successful blocking start; active/running service,
Result=success/ExecMainStatus0, NRestarts0, new start identity; one **fresh** seed
published after this start, accepted by the pinned directory validator with valid
precise timestamps and canonical UTC Z, same preflight profile identity; final
healthy readback of the same PID/start and unchanged still-valid directory.
`SeedManager.Run` calls `Publish` only after connector READY; `Cache.Store` validates
and atomically fsyncs the export. There is no sd_notify/READY systemd completion
signal here. A disk export can survive process exit: its existence alone, an old
valid export, or a journal event is never enough. Native authority validation remains
a separate prerequisite; this operator does not replace it with Python metadata.

Bounds: state commands2s, material snapshots5s, start30s; READY wait≤120s including
commands, at most60 observations/2s sleeps; authoritative total165s including
prechecks and final readbacks. Waits are clamped to remaining monotonic budgets;
any authoritative command/deadline/state/material failure is FAIL. No unbounded
polling, background start, restart retry, clock rounding or grace interval.

Each authoritative observation and the immutable authoritative verdict is file+
directory-fsynced **before** optional diagnostics. `--journal` requests one bounded5s
read; omission skips it. Diagnostic receipts use a separate kind/filename namespace:
`diagnostic_available`, `diagnostic_timeout`, `diagnostic_unavailable` or
`diagnostic_not_requested`. A journal timeout/nonzero exit/spawn failure does not
change PASS or FAIL, and cannot overwrite authoritative evidence. Output explicitly
separates `authoritative: PASS|FAIL` from `journal: diagnostic_*`. No raw journal,
private IDs, room URLs, proofs, credentials or provider token enter receipts.
Receipt-storage failure is an evidence error (nonzero exit), not a hidden PASS or
a rewritten runtime verdict. Verdict is a point-in-time observation, not a promise
of continued liveness during later diagnostics. Keep original receipts on rollback.

RU policy is unchanged: `restricted_sync_acceptance.py` already bases acceptance
on blocking unit/material/negative checks, not journal retrieval. The independent
NL operator is not merged into RU or into either immutable runtime archive.
No production deployment/refresh/Redmi/APK/push or automatic attempt #9.

## Committed HTTP packaging checkpoint — local only, 01.10.2026

The production HTTP builder, explicit source manifest, isolated entrypoint, durable
receipt harness, nginx matrix and CI integration are now committed in
`f7b3b6c29526fb600990f60d57449571a8538f22`. Later evidence-only commits do not
change these runtime inputs. Build from an exact clean Git export/worktree, never
overlay retained uncommitted files. The candidate inventory and final clean-HEAD
receipt are described in the [packaging Git report](../../../docs/releases/2026-10-01-5n-http-packaging-git.ru.md).

```sh
/path/to/locked-venv/bin/python -I /clean/source/scripts/package_friends_http.py \
  --output /new/empty/http-bundle --python /path/to/locked-venv/bin/python
```

The builder normalizes ZIP order/timestamps/modes so identical inputs do not change
archive bytes with checkout/copy timestamps. All24 explicit source/config/lock/
harness inputs plus the archive are hashed. The packaged handler's `main()` supports
`--root`/`--port`; production uses the existing loopback/default state layout.
External packages remain in the venv pinned by both supplied lockfiles. The zipapp
does not prepend the external app directory or rely on cwd/PYTHONPATH. The guarded
external app path is retained only for legacy direct-script execution, not zipapp
imports. Never deploy that legacy script as the new isolated artifact.

Candidate HTTP SHA256:
`460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
Old `eb9eb06f…` is retired as a deployment input, retained only as historical
evidence. Accepted sync remains `cb6f050e…`, unchanged; shared precise-directory
compatibility is tested without rebuilding or deploying it.

Use `FC_TEST_HTTP_ARTIFACT` for the exact built bundle, `FC_TEST_NGINX` for isolated
local nginx, and `FC_TEST_SYNC_ARTIFACT` for the accepted sync archive when running
the HTTP runtime/evidence tests. Mandatory local A–G includes synthetic signed
readiness fetch200; the production receipt CLI itself covers A–F, since it does
not possess the physical owner's private proof key. Real owner readiness remains
a separate mandatory production gate, never substituted by synthetic tests.
No live attempt, JIT refresh, service activation, phone or beta is authorized by
this checkpoint. The production order/rollback contract remains unchanged.

## RU acceptance after attempt #5 — local operator, not deployed

Use `scripts/restricted_sync_acceptance.py` instead of the archived inline RU_SYNC
block for a separately authorized future attempt. Pin the operator, closed runtime,
unit and forced helper first; keep the sync timer disabled during one-shot acceptance.
The source/runtime/authority policies are unchanged; this command is not a refresh
or deployment authorization. It starts only the existing restricted sync unit once.

```sh
venv/bin/python -I /path/to/pinned/restricted_sync_acceptance.py --execute \
  --runtime /path/to/pinned/restricted-sync.pyz \
  --evidence /protected/attempt-evidence/ru-sync --generation attempt-N
```

`--snapshot` instead of `--execute` is a read-only safe metadata probe. No default
execution mode. No raw profile, directory, URL, proof, private identity or OAuth is
printed. Runtime archive dependencies are loaded through the isolated archive.

Completion is **synchronous**: SSH is bounded15s, systemd Type=oneshot25s, blocking
`systemctl start` retains45s. Require its successful blocking return, inactive/dead,
Result=success/exit status0, CRL=previous+1 with valid issuer/signature/current time and
matching DB floor, valid BOOT-1 directory with nondecreasing issuance. Directory v1
has no revision counter: record version/issued/expires, not an invented revision.
Then require strict known-host verification and forced-command generic shell exit126,
stale CRL exit1 with empty stdout, and unchanged authoritative readback afterward.
No retries, `--no-block`, async convergence shortcut or CRL-only acceptance.
Exited-unit execution metadata may be cleared (ExecMainCode0 versus CLD_EXITED1);
it is not a standalone freshness proof. Blocking start plus fresh signed material
and the negative gates remain mandatory even when that metadata is unavailable.

Journal retrieval is not an authoritative completion signal. Attempt #5's mandatory
journal10s request preceded the first service receipt and aborted an otherwise
completed unit before negatives. The new success path does not launch journalctl;
any separate log investigation must stay redacted/bounded and cannot replace these
checks. A timeout of any mandatory command remains FAIL even if subsequent diagnostic
state/readback reports success. No timeout is caught and silently accepted.

Per-command bounds: before/safe after/final snapshots5s each, before/after unit show2s
each, daemon-reload5s, start45s, shell/stale probes15s each =99s. Reserve2s timeout-state
and5s timeout-readback plus1s margin: total107s monotonic command budget. Each wait is
clamped to remaining time; no unbounded polling. Existing sync/SSH/unit/start bounds
are not enlarged. Filesystem fsync is required; this is not a hard-real-time guarantee
against an unresponsive kernel/filesystem. Local timings are not a WAN latency SLA.

Receipts record generation, step, fixed redacted executable/argv class, configured/
effective timeout, monotonic start/end/elapsed, exit code or null, TimeoutExpired,
bounded stdout/stderr classifications and safe material metadata. Primary failure
is fsynced **before** timeout diagnostics. Supplemental records retain observed unit
state and before/after material metadata, with unknowns explicit; later observations
are not claimed to be an instantaneous snapshot at the timeout. No raw argv/stdin.
Failure verdict is fsynced before returning nonzero to the external rollback handler.
Keep evidence outside runtime/rollback replacement paths; never erase old receipts.

## Directory validation gate — corrected locally after attempt #4

Attempt #4's producer emitted valid BOOT-1 v1; the old inline Python operator
rounded its current clock down with `int(time.time())`, falsely treating a
same-second nanosecond `issued_at` as future. Production remains rolled back;
this local fix does not authorize attempt #5. Attempt #3 HTTP cause remains UNKNOWN.

Use the corrected committed-source closed runtime, not the archived operator's
inline directory call/imports. Candidate built from `29d15d7`:
`state-client-build/directory-validation/final-sync-bundle/restricted-sync.pyz`,
SHA256 `cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`;
all17 inventory entries pinned. Producer binary/native consumer unchanged.
The previously accepted HTTP archive is not rewritten: future HTTP packaging must
include the corrected shared Python consumer and pass its own activation gate.

After separate authorization, the NL validation step is:

```sh
venv/bin/python -I /path/to/pinned/restricted-sync.pyz directory-check \
  --profile /protected/gateway.json --directory /protected/directory.json \
  --receipt /protected/attempt-evidence/nl-directory.json --generation attempt-N
```

This command reads existing inputs and writes only a redacted receipt. It never
starts a service, publishes a CRL, fetches provider data or enrolls a device. It
does not replace authority/native/CRL validation. Sample the real nanosecond clock
after reading the directory; do not pass truncated seconds or alter wire timestamps.
There is no clock-override CLI option or skew allowance. The legacy integer-second
library argument is only for deliberately exact whole-second test snapshots;
use `now_ns` for injected precise test clocks and the default for live checking.

`directory_validation_failed: stage=time predicate=issued_in_future field=issued_at`
is a bounded category, not a dump of the field value. Parse/schema/binding/seed/
expiry/lifetime failures also have bounded categories. Receipt includes safe time,
generation and verdict/category, never URL/profile/identity/proof/body. Keep the
owner-only receipt path outside replaced/rolled-back runtime directories. The
file and containing directory are fsynced before a failure exits; persistence
failure itself forbids acceptance. Only after a successful verdict may the operator
advance; otherwise preserve receipt, perform the scoped rollback and stop. Never
catch-and-ignore the error or retry until a clock boundary happens to pass.

Tests cover receipt ordering, nonzero shell/EXIT trap/rollback marker, hard process
exit, exact issuance/expiry ±1ns, URL/security bounds and real SeedManager serialized
publication through the isolated Python archive back to native validation.
[Detailed proof and limits](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## Latest attempt #4 — rolled back before RU sync/API, 01.10.2026

Explicit authorization followed the local revalidation below. Accepted HTTP bytes
and25-entry inventory/source pin matched, but the HTTP archive was only staged,
not activated. JIT CRL11→12/native authority checks PASS; gateway certificate
expiry18:13:46UTC, CRL expiry17:28:46UTC. NL emitted one canonical UTC-Z seed and
logged native READY once, but Python live-directory acceptance raised `ValueError`.
Exact rejected predicate is not established. No RU `--check`/live sync/API gate;
no Redmi. **STOP, no retry/live repair under the consumed authorization.**

Rollback17:13:57–58UTC/readback17:15UTC: ordinary200/400/400, restricted404;
API/ingress unchanged without restart, AWG/TCP unchanged. Restricted seed/sync/
timer/auth off. Protected snapshot/evidence on both hosts:
`restricted-materials-stage-20261001/canary-rollout-attempt4-d27156d/` under the
authorized Family Connect root. NL `failed-directory.json` remains private there;
do not print/copy its seed URL into Git. Local redacted receipts/operator are in
ignored `state-client-build/prov1-attempt4/`.

Authoritative DB/staged CRL12 and NL profile floor12 are preserved; inactive RU
runtime still has expired CRL11 because installation/sync was never reached.
Future publisher refresh must reconcile authoritative floors, not assume that
inactive runtime is current. Never roll back the DB or use old staging6/CRL11.
Attempt #3 historical cause remains UNKNOWN. [Full attempt #4 record](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

## Historical local HTTP gate — before attempt #4 authorization

01.10.2026 local HTTP revalidation is READY FOR DEPLOYMENT AUTHORIZATION, not
production acceptance. Historical attempt #3 root cause remains UNKNOWN because
decisive HTTP evidence was lost. No retry is implied. [Exact artifact and receipts](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

HTTP deployment now uses the independent closed `friends-http.pyz`, built by
[`package_friends_http.py`](../../../scripts/package_friends_http.py) from
[`http-runtime-files.json`](http-runtime-files.json); sync still uses the separately
accepted `restricted-sync.pyz`. Do not use the minimal sync overlay as an ordinary
Friends API deployment. Candidate retained at
`state-client-build/http-activation/validated-bundle/`, HTTP archive SHA256
`eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`.
Its25-entry `sha256.json` also pins ingress, both HTTP drop-ins, lockfiles and the
receipt harness. Recheck bytes against current source and after transfer; never
rebuild silently and deploy an untested replacement. Venv must match both lockfiles.

Only after separate explicit attempt #4 authorization, fresh live backups/JIT
authority and NL READY/UTC-Z/RU isolated sync check/live sync/negative checks PASS:

1. Install this exact archive to `friends-access/friends-http.pyz` and packaged
   [`http-runtime.conf`](http-runtime.conf) as an additional systemd drop-in for
   `family-connect-friends-access.service`. Preserve existing ordinary app/handler
   for rollback. Keep packaged `access.conf` pointing to accepted restricted state.
   `python -I` starts the archive on the existing loopback18084, no checkout imports.
2. Add only packaged `nginx-location.conf` locations to the existing HTTPS vhost;
   preserve status and ordinary Friends locations. Validate actual nginx config
   before reload. Never run a first-install script on existing production.
3. Use packaged `friends-http-acceptance.py` (SHA256
   `830b5dec96af01fd5650e9afd15d27661dba1a3191f5943aecbdf41fc8d0fc42`)
   with an owner-only evidence directory OUTSIDE any replaced/restored runtime
   tree. Set a unique nonsecret `--generation` mapped to the saved artifact/config
   inventory. Start `observe` before transition; observation is not an acceptance
   verdict. `ready` checks loopback ordinary challenge with bounded readiness retries;
   `gate` checks actual verified HTTPS without retries masking a regression.
4. `gate --origin <verified-HTTPS-origin> --evidence <protected-receipts>
   --generation <generation> --identities <protected-input>` requires existing
   canary public identity/WG binding and all26 existing non-canaries by default.
   Input file must be owner-only; do not print IDs or response bodies. Do not use
   `--expected-non-canary 1` in production (it is synthetic fixture coverage only).
   Exact gate: status200; ordinary malformed challenge400; safe ordinary chat
   challenge400; restricted malformed400; all non-canaries403; canary200 with
   validated bounded challenge shape. Physical readiness is a subsequent gate.
5. Each probe fsyncs its redacted timestamp/status/classification/generation before
   evaluating; only then may a nonzero gate trigger rollback. Do not wrap it in
   an operator that keeps observations only in memory. Local tests cover shell
   EXIT-trap/nonzero exit/SIGTERM/service failure/recovery and retained receipts.
   Preserve receipts on rollback, including failed statuses and TLS/transport errors.
   If persistence fails, acceptance cannot pass. No receipt guarantee is possible
   for an uncatchable kill before an observation has been persisted.

Rollback restores saved ordinary handler/app/ingress, removes **both** new HTTP
drop-ins, reloads systemd and restarts only Friends API; stop/disable restricted
timer/sync/NL seed and its forced-command authorization. Preserve authority, DB and
monotonic floors (last documented11, not staging6). Never roll back a whole DB over
new revocations. Validate ordinary200/400 and restricted404 with durable receipts.
No AWG/TCP restart, phone interaction or FIELD-1 until the respective gates pass.
The older overlay-based HTTP instructions below are historical/superseded by this
section; accepted sync, trust, TTL and admission contracts are unchanged.

## Попытка №3 — rolled back, 01.10.2026 14:40UTC

Source `2705db4`: закрытый archive установлен на RU/NL, RU `python -I ... --check`
и live sync PASS; ModuleNotFoundError не повторился. NL READY/UTC-Z/Python PASS,
generic shell и stale CRL отклонены. После включения API провалился normal HTTP
smoke; немедленный rollback вернул API/ingress, выключил sync timer/NL seed/auth.
AWG/TCP не перезапускались, Redmi не трогали. Причина HTTP failure не установлена;
probe observations потеряны при assertion, точный downtime/zero downtime не доказан.
[Полный порядок, ограничения evidence и финальное состояние](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

DB/live CRL на RU и NL сохранены на sequence11 (expiry14:55:41UTC), root-only JIT
stage остаётся на6. Не откатывать DB/monotonic floors и не использовать stage6 как
текущий sequence при следующем refresh. Следующий шаг — локально проверить API/
ingress transition и crash-safe probe receipt; **не автоматический deployment retry**.
Ниже сохранены предыдущие checkpoints и контракт поставки.

## 5N-RUNTIME-PACKAGING — локальное исправление, не deployment

После попытки №2 исходники sync поставляются только по
[`runtime-files.json`](runtime-files.json), builder —
[`scripts/package_restricted_runtime.py`](../../../scripts/package_restricted_runtime.py).
Manifest содержит10 Python-файлов, включая единственный чистый stdlib-модуль
`clients/desktop/profile_config.py`; GUI/backend/client state не поставляются.
Он намеренно используется для строгой проверки AWG/TCP templates. Перенос этого
парсера сейчас затронул бы несколько desktop/TCP packagers и шестифайловый legacy
archive; поэтому выбран явный lightweight dependency, без копии реализации.

Локальная сборка из checkout с venv, установленным по обоим существующим lockfiles:

```sh
python scripts/package_restricted_runtime.py \
  --output state-client-build/restricted-runtime \
  --python /path/to/locked-venv/bin/python
```

Builder отказывается перезаписывать output, проверяет каждый source и запускает
`--help`, `sync --help`, `gateway --help` из готового `restricted-sync.pyz` с
`python -I`. Это стандартный stdlib zipapp, не sys.path/PYTHONPATH workaround.
Python внутри архива — тот же source, что в `app/`; внешние RNS/cryptography и их
зависимости остаются в venv по поставляемым `control.lock`/`identity.lock`.
`sha256.json` фиксирует bytes всех outputs. Сборка не включает runtime state,
fixtures, ключи, provider.env, authority или комнаты.

**Только при следующем отдельно разрешённом rollout:**

- Overlay `app/` из bundle в `friends-access/app/`, сохранив существующие обычные
  API модули; **не заменять весь app** минимальным sync-набором. Отдельно поставить
  reviewed API handler как прежде. Не делать ручной выбор Python-папок.
- Один и тот же `restricted-sync.pyz` разместить на RU/NL по
  `/opt/apps/family_connect/friends-access/restricted-sync.pyz`, root-owned0644;
  родительские каталоги должны быть traversable сервисному пользователю NL.
  В read-only backup включить старые app/архив (если есть), unit и helper.
- RU использует unit из **того же bundle**: `venv/bin/python -I .../restricted-sync.pyz sync ...`.
  NL root-owned0755 helper — [`restricted-sync-command`](restricted-sync-command)
  из bundle, тот же archive с `gateway`; прежние SSH `restrict`/source restriction/
  forced-command сохраняются. Никакого `PYTHONPATH` или зависимости от cwd checkout.
- До старта sync выполнить его точный `ExecStart` с добавленным `--check` и
  `FC_FRIENDS_RESTRICTED_DIR`. Проверка только локально читает/валидирует
  delegation/key/admission/CRL, CRL sequence/SQLite integrity и bounded key/host
  files. БД открывается `mode=ro`; publisher, SSH и writes не вызываются.
  Успех выводит только `Restricted runtime pre-network check passed`.
  Это **не** проверка SSH-аутентификации/удалённого consumer и не обновление
  истёкшего CRL; JIT freshness и последующие live checks всё ещё обязательны.

Regression: `tests/test_restricted_runtime.py` строит точный bundle и читает его
unit/helper, проверяет imports/CLI вне checkout, без/с посторонним PYTHONPATH,
отрицательное удаление каждой runtime dependency, fixture-only `--check`,
неизменность файлов/БД и запрет publisher/socket/subprocess. CI path filters
включают manifest, helper, builder и server modules. Android/shared parser source
не изменены, новый APK для этого исправления не требуется.

**Production остаётся в состоянии rollback попытки №2.** В этой локальной задаче
нет SSH/deploy/start/authority refresh/phone testing/push/FIELD-1.

### Исторический блокер и откат попытки №2

**Попытка №2,01.10 13:39UTC: DEPLOYMENT FAILED / ROLLED BACK.**
Source `e808f50`: NL READY и живой UTC `Z` → Python PASS. RU sync остановлен:
`provisioning.friends_catalog` импортирует `clients.desktop.profile_config`,
которого нет в описанном минимальном RU bundle. Полный authority staging скрывал
зависимость. **Не повторять rollout до локального исправления runtime manifest
и isolated import/CLI smoke точного deployment bundle.** Не добавлять зависимости
ad hoc на production. API/routes не включались; RU API/ingress восстановлены без
restart, NL bootstrap/sync authorization выключены. CRL sequence5 сохранён;
перед новым разрешённым retry нужен JIT refresh, не reset.
В sticky NL directory обновление service-owned gateway.json требует atomic
create/fsync/chown/rename, не copyfile поверх старого файла: сохраняем
`fs.protected_regular=2`, owner/mode. [Доказательства/откат](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

### Исторические checkpoint до попытки №2

**Local repair checkpoint: 5N-TIME-COMPAT PASS, not deployed.** Go seed export
and Directory serialization now emit UTC `Z`; Python/native consumers validate
offset-aware RFC3339 instants with unchanged lifetime/replay/trust bounds.
Before any separately authorized retry, rebuild/re-stage the modified Go/Python
artifacts and JIT refresh expired material. Do not start the inert old NL binary.
[Contract and regression evidence](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).

**Current rollout checkpoint,01.10 11:48UTC: [DEPLOYMENT FAILED / ROLLED BACK](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).**
NL seed joined READY, but generated `expires_at` retained host offset `+03:00`,
rejected by the Python `Z`-only timestamp parser. NL unit/auth disabled and directory
quarantined; RU runtime/routes/sync never deployed. Normal production unchanged.
Do not repeat this rollout until local timestamp compatibility/regression coverage
is fixed and a new controlled retry is authorized. No manual directory rewrite or
TTL extension. Actual ingress validation command: `nginx -t -c /etc/fc/nginx.conf`
inside `family-connect-product-https`, not nginx's unused default configuration.

### Historical preflight

**Current checkpoint,01.10 11:21UTC: [DEPLOY-PREFLIGHT READY](../../../docs/releases/2026-10-01-5n-prod-deploy-preflight.ru.md),
not deployed.** Owner-installed final NL provider.env passes metadata/schema-only
checks; token never returned/hash/size-reported. Same authority, CRL3 expires
11:35:38UTC, gateway leaf12:20:38UTC; no TTL extension. Other material remains
inactive staging, account/units not installed. Stop before deployment; refresh
through the publisher again if this short validity window is missed.

### Historical input checkpoint

**Current preflight checkpoint,01.10:** [refresh / owner hidden-input boundary](../../../docs/releases/2026-10-01-5n-prod-deploy-preflight.ru.md).
Same authority/admission, publisher CRL sequence2 expires11:26:23UTC, gateway leaf
12:11:23UTC. Token access is now owner-interactive only: the staged
[`provision-provider-env.py`](provision-provider-env.py) requires root/TTY,
refuses echoed fallback/overwrite, writes only final root0600 provider.env and
checks schema without outputting the value. No agent unlock/export of KeePass.
Input pending; no runtime service/API/ingress deployment authorized by this step.
Recheck expiry after owner input; never extend TTL or reuse expired CRL to deploy.

**Authority checkpoint,01.10:** [5N-PROD-AUTHORITY READY](../../../docs/releases/2026-10-01-5n-prod-authority.ru.md)
prepared the first signed Friends restricted Family, sole owner grant, existing NL
control-provider gateway designation, issuer/CRL/profile and inactive runtime/sync
templates. Files remain under root-only `restricted-materials-stage-20261001/`,
not these final runtime paths. Only four accepted additive restricted tables were
created. Initial CRL expires01.10 11:02:45UTC; refresh it via the publisher (preserving
sequence) before later use. Do not regenerate Family/identity/floors or rerun first
initialization. Provider token was expressly excluded; do not access KeePass or
activate services/API merely because authority preparation is READY. Previous
implementation-only statements below describe the original checkpoint.

Local implementation only, 2026-10-01. **Do not execute this rollout without a
separate authorization.** No production keys/configuration have been generated
by this task. No diagnostic credentials may be reused. This is an owner-device
canary, not general rollout or Krasnodar FIELD-1.

## Production API and trust contract

The existing RU Friends HTTPS ingress and `family-connect-friends-access.service`
serve two bounded POSTs, using the existing activated Device Identity, not Family
mTLS (which cannot be a prerequisite for initial delivery):

1. `/friends/restricted-readiness/challenge`: existing `public_identity` and
   `wireguard_public_key`. Response: challenge, expires_at, existing enrollment
   audience. The stored nonce is purpose-bound to `restricted`, Family and grant
   revision; maximum eight outstanding device challenges, existing 100s TTL.
2. `/friends/restricted-readiness`: existing transport-key proof. Response keys:
   `version`, `device`, `challenge`, `issued_at`, `expires_at`, `revision`, `issuer`,
   `certificate`, `revocations`, `minimum_crl`, `directory`. No private keys,
   OAuth, dedicated room descriptors or normal transport credentials.

Existing HTTPS authenticates delivery. Proof possession, exact public identity/WG
binding, active invitation/device/grant, admission policy, expiry, nonce replay,
revision, signed CRL and issuer validity are rechecked before issuance. Requests
are at most 8KiB, responses at most 64KiB, existing concurrency limit four.
Responses are no-store. Authorization rejection is 403; unavailable configuration,
provider snapshot or CRL is 503, not evidence of device revocation.

An eligible **already activated** device gets a restricted grant automatically.
Existing Friends activation is perpetual, so this mapping has no invented billing
expiry; certificate/CRL/directory validity remains finite. Optional finite grants
and increasing revisions are supported by the operator CLI. A revoked, expired or
wrong-Family existing grant is never silently recreated. Start with only the
owner's verified device reference in `admission.json`; do not use `*` for the canary.

## Delegated issuer, not another trust root

The existing packaged `control-anchor.pub` authorizes an online Ed25519 Family CA
through a domain-separated offline signature. This bridge is needed because the
accepted Family issuer was an isolated fixture, not an existing production issuer.
The CA alone is **not** an additional trusted Android root. No root key goes to
RU/NL. No standalone BootstrapDirectory signature is introduced.

`issuer.json` is `{payload: base64, signature: base64}`. Decoded payload has exactly
`version:1, sequence, family, gateway, authority, minimum_revision, issued_at,
expires_at`. The authority is one canonical PEM CA certificate, with Ed25519,
CA/pathLen0, cert-sign/CRL-sign usage and validity covering the delegation. Family
and gateway are the selected authoritative 32-hex references, not arbitrary
request parameters. Sequence increases on delegation changes. `minimum_revision`
is the global peer floor; per-device grant revision is checked independently.

After authorization, generate the **delegated issuer** key in protected server
storage (0600, no stdout), transfer only its public CA to the offline signer,
prepare bounded delegation metadata and use, from the repository root:

```sh
python -m scripts.sign_restricted_issuer --input /protected/issuer-payload.json \
  --output /protected/issuer.json --key /protected/existing-control-root.key
```

The signer requires the exact existing packaged root; a different key is rejected.
Use the existing protected signing-key/vault workflow, not a new root. Review
Family/gateway identity, sequence, peer floor and delegation duration explicitly;
there are deliberately no production default IDs or private keys in these files.

Device certificate: existing Ed25519 public identity, full public-identity URI,
Family/role/device-revision claims, existing `family-connect-5n3-test-v1` protocol
and TLS1.3. The name is historical, not a request to use diagnostic credentials.
Android assembles the accepted `familysession.Credentials` in memory using the
**existing** encrypted Device Identity secret. No delivered/private second identity,
static APK credentials or plaintext SharedPreferences key.

## Exact deployment scope and order

Before changing anything, verify live paths/service definitions/ports and available
disk on the two authorized hosts; take private SQLite online backup plus saved API,
ingress and unit artifacts. The last deployment receipt is historical; a local
commit/build is not proof that a host runs it. Excluded host `186.246.51.201` and
neighbouring services are out of scope. Do not run first-install scripts over the
existing Friends deployment.

### RU — 185.251.89.19:/opt/apps/family_connect

- Deploy the checked bundle described above: explicit `app/` overlay, the same
  `restricted-sync.pyz` and unit/helper templates on RU/NL; preserve existing API
  modules. Deploy reviewed `deploy/friends/access-api.py` to the existing handler
  path. Use the bundle's existing control/identity lockfiles in `friends-access/venv`;
  verify cryptography compatibility. Never copy only three guessed source folders.
- Create protected `friends-restricted/` (0700): `anchor.pub`, `issuer.json`,
  `issuer.key` (0600), `admission.json` with **only owner device**, initial
  `revocations.pem`, subsequent `directory.json`, dedicated `sync.key` and pinned
  `known_hosts`. Public delegation/CA are not secrets; directories/CRL seed URLs
  are still private operational state. Never print responses or profiles.
- With `FC_FRIENDS_RESTRICTED_DIR=/opt/apps/family_connect/friends-restricted`, run
  `python -m control.friends.restricted_admin --db
  /opt/apps/family_connect/friends-access/access.db migrate` using that venv.
  Same-DB additive tables: restricted_grants, restricted_challenges,
  restricted_certificates; publisher creates restricted_crl_sequence. No existing
  rows/identity/configuration are reset. Migration is explicit, never at request
  time. Run `publish-crl` action to initialize the signed CRL.
- Install the `access.conf` drop-in for `family-connect-friends-access.service`
  only after the seed/sync is ready. Insert `nginx-location.conf` into the existing
  `family-connect-product-https` vhost; validate and reload, not replace the vhost.
  It proxies only the new paths to existing loopback 18084.
- Install the new `family-connect-restricted-sync.service` and `.timer`.
  Every 30s after completion it publishes a 15-minute signed CRL, sends **only CRL**
  to NL and imports the READY directory. SSH timeout15s, unit timeout25s, output
  cap, exact known-host pin, no agent/port forwarding, no provider request here.

### NL — 186.246.45.246:/opt/apps/family_connect

- Deploy a fresh reviewed host `bootstrap-broker` binary under
  `friends-restricted/bin/`, Python sync helper/dependencies in
  `friends-access/app`/`venv` (reuse only if verified present and compatible), and a
  dedicated `family-restricted` service account. Do not change AWG/TCP services.
- Use the selected **existing gateway Device Identity**, keeping its secret on NL.
  Send only public identity to RU; `restricted_admin gateway-certificate
  --public-identity ... --expires ... --output /protected/gateway.pem` enforces
  the delegated gateway reference. Assemble accepted `gateway.json` (0600) on NL
  with that certificate, existing gateway Ed25519 private key, delegated public
  authority, initial signed CRL, Family/gateway and revision/CRL floors. No fixture
  issuer/profile or owner-device private key. Renewal of the gateway certificate
  is operational PKI maintenance before expiry, not Android enrollment.
- The dedicated RU sync public key must have the root-owned `restricted-sync-command`
  wrapper from the checked bundle as its sshd forced command. It invokes the verified
  NL venv with `-I /opt/apps/family_connect/friends-access/restricted-sync.pyz gateway`
  and the existing profile/directory paths, independently of cwd. Use `restrict`, source
  address restriction to RU, no shell/PTY/forwarding, no access to other services.
  This helper accepts a signed monotonic CRL and exports only a validated directory;
  it does not receive private keys. Do not repurpose existing peer-registration keys.
- Install `family-connect-restricted-bootstrap.service`, preflight new loopback
  `127.0.0.1:18444` unused (no public port). Protected `provider.env` supplies
  **server-only** `YANDEX_TELEMOST_OAUTH_TOKEN`; token rotation/revocation stays in
  the existing provider operational process. Neither APK nor RU API receives it.
- Start seed service, wait for READY and bounded directory export, then enable RU
  sync and API drop-in/ingress. No seed directory is published before READY. Rooms
  for dedicated sessions are created only on an admitted recovery request.

The templates are reviewed local artifacts, **not installed units**. Ensure NL
bootstrap process and forced helper can access only the intended private directory.
Current CRL/profile is reloaded on Family admission; no gateway restart per CRL.
Do not expose the legacy mTLS cache-preparation listener publicly.

## Lifetime, refresh, and revocation limitations

- BOOT-1 v1 unchanged: <=1h directory, 8KiB, up to four bootstrap seeds with
  authenticated Telemost `join_url`. Deployment seed process55min; restart30s.
  Export occurs only after READY. A dead seed may remain in a valid cached snapshot
  until expiry; single-seed rotation/restart can temporarily reduce availability.
- Device certificate <=1h and bounded by grant/delegation/current CRL. This CRL
  publisher uses **15min**, so actual readiness is at most15min and may be shorter.
  Dedicated unused descriptor remains60s, established session default10min;
  dedicated descriptor is never stored as readiness or LKG.
- Android refresh: activation, successful normal profile acquisition, foreground
  resume/60s maintenance checks; **not 60s network polling**. Missing/invalid or
  <=300s remaining triggers one worker, persistent300s attempt cooldown,30s network
  deadline. No alarms/background polling. Valid cache doesn't block CONNECT.
- 403 tombstones usability durably; timeout/503/invalid/stale refresh leaves valid
  old response intact. Higher issued/revision/CRL/delegation/directory floors
  prevent replay even after expiry. Restart keeps encrypted state and cooldown.
- Revocation reaches the gateway on the next successful server sync, normally
  about30–45s; failed sync is bounded by the **previous signed CRL's expiry**, up to
 15min, not instantaneous offline revocation. API checks current DB immediately.
  Existing sessions additionally obey the accepted Family session expiry policy.
- Prewarm immediately before an authorized local/field attempt. Offline recovery
  hours after last control contact is **not supported by this gate**. Extending
  seed/CRL/directory validity needs separate security/product review.

## Acceptance, downtime, rollback

Expected impact: one short Friends API restart (seconds expected, not measured),
validated ingress reload, new isolated NL seed service; no AWG/TCP restart or planned
data-plane outage. Canary operational checks must confirm this expectation.

After authorized server deployment: build a **private validation** Friends APK with
fresh normal/restricted JNI, same signing certificate, increasing private version;
install in place (no uninstall/pm clear). Ordinary Internet + actual identity must
produce READY, then process restart must retain READY. Only then run the separately
described local forced-normal-failure rehearsal: Wi-Fi off, cellular on, Auto,
no manual room URL/diagnostic credentials/traffic forwarding; browser, Family DNS
and retained-TUN fail-closed must pass. Only **after** this live integration passes
may the final shareable FIELD APK be produced. Existing field52 is not that artifact.

Rollback: disable new ingress routes/drop-in and stop only the new sync timer/seed
service; restore saved API/ingress artifacts and restart control. Preserve additive
DB tables, latest revisions, certificate serial history and CRL/issuer floors;
**never restore an old full DB over new revocations**. Preserve protected identity
and key material. Existing Android normal paths remain usable; correct Android via
same-signature forward update, not downgrade/data clear. A cached seed may stop
working after rollback; the existing Orchestrator must fail closed on exhaustion.

No deployment, root signing, live proof, APK release, push or FIELD-1 was performed
while writing this runbook. See the [gate report](../../../docs/releases/2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
