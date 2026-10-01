# 5N-PROV-1 — production restricted provisioning + bootstrap delivery

## 5N-DIRECTORY-VALIDATION — PASS, offline repair after attempt #4

Starting HEAD `d27156d92fdb829fdc82471b05074270b54cd1a9`. Implementation commit
`29d15d73dae52ac8a1079c52dd349b5b21045742`; separate documentation commit records
the evidence. No production deployment/retry, service start, authority refresh,
Redmi action, APK build, release or push. Only read-only retrieval of the preserved
NL evidence and safe historical journal timestamps. Earlier attempt/rollback
records below remain unchanged, including their initially unknown diagnoses.
**Attempt #3 HTTP root cause remains UNKNOWN; this proof concerns #4 only.**

### Exact private reproduction and proven predicate

Retrieved without editing the private
`canary-rollout-attempt4-d27156d/failed-directory.json`, the expected Family/gateway
bindings, exact deployed Python source dependencies and `restricted-sync.pyz`.
Private values remain in ignored0700/0600 local evidence; no room URL, identity,
credential or raw directory printed or committed. All five retrieved source files
are byte-identical to their deployed closed-archive counterparts. The archive SHA256
is `e7e0c8a2ebefdd8ae6f6829f86fcac214b4c4dadb50f0664f0a4e92ea3498788`.
Replay runs this exact old archive with `python -I`, not a reconstructed validator.

| Evidence | Observed/reproduced fact |
| --- | --- |
| Private directory | Unchanged291-byte BOOT-1 v1, one seed; issued17:13:53.532852358Z, expires18:08:49.62807736Z |
| Native READY journal | 2026-10-01T17:13:53.539049Z |
| systemd stopping journal | 2026-10-01T17:13:54.204369Z, after validation failed and rollback was requested |
| Exact old call | `directory(raw, profile['family'], profile['gateway'], int(time.time()))` from retained `NL_START` |
| Old replay clock | `1790874833` whole seconds (17:13:53Z) |
| Exception/stack | `ValueError`, archived `control/friends/restricted.py:120` → `provisioning/friends_catalog.py:22` |
| Failed predicate | `issued_ns <= now_seconds * 1_000_000_000` is false |
| Safe category | `stage=time predicate=issued_in_future field=issued_at` |
| Unchanged old bytes at next second | PASS at1790874834; no schema/URL/binding changes |
| Precise replay observation | 1790874833539049000ns, the retained READY observation; corrected Python and native PASS |

The exact subsecond Python call instant was not logged; it is not invented here.
The returned bytes, old code and isolated predicate checks prove the incompatibility:
discarding the fractional clock makes the just-issued valid seed appear future
through the rest of its publication second. Within the recorded publication/stop
window, the reconstructed integer53 reproduces the failure; integer54 accepts
the identical bytes. All other predicates accept that same directory. The time
ordering predicate, not parsing/normalization/schema/trust/gateway/URL/replay,
is the proven failing condition. This is not the earlier numeric-offset bug.

Native `bootstrap.ParseDirectory` accepts the preserved bytes at the precise
historical observation. Therefore **producer output is valid**. No producer fix,
rounding of wire timestamps or permissive parser workaround is appropriate.
The 291-byte original remains unchanged through retrieval/replays and its digest
is verified privately; no normalization is written back to the evidence.

### Field-by-field BOOT-1 v1 contract audit

| Field/boundary | Producer, Python and native contract |
| --- | --- |
| version | Integer1; boolean/string/unknown version rejected |
| family | Expected32-character Family reference; no identity remapping |
| issued_at | Absolute RFC3339 timestamp, canonical UTC-Z from Go,1–9 fractional digits; must not exceed precise current time |
| expires_at | Same encoding; exclusive expiry, strictly later than issuance, lifetime≤3600s |
| seeds | Array1–4; producer emits exactly one after READY; directory≤8192 bytes |
| seed identifier | No separate ID field in v1; duplicate join URLs rejected |
| transport | Exact `telemost-webrtc`; not a dedicated-session descriptor |
| join_url | Present string, exact HTTPS `telemost.yandex.ru/j/` plus1–128 ASCII letters/digits/underscore/hyphen; no query/fragment/userinfo/port/encoding substitutions |
| gateway | Each seed binds the expected gateway reference; no fingerprint/identity replacement |
| certificate/binding metadata | Not directory fields; existing delegated authority/X509/CRL and caller's expected bindings are separate prerequisites |
| revision/sequence/floors | Not directory fields; issuer/grant/CRL checks and cache replay floors remain in their existing components |
| null/absent/extra fields | Required exact top-level and seed field sets; null/wrong-type/extra metadata does not substitute for required fields |
| canonical form/replay | UTC normalization preserves absolute instants; no field stripping, URL rewriting, seed substitution or replay bypass |

Preserved wire shape matches this contract, including a14-digit room segment (the
synthetic fixture replaces it with zeros, never the real URL),32-character synthetic
Family/gateway values,9-digit issuance fraction and8-digit expiry fraction. No
optional ID/certificate/floor field was missing: such fields are absent by design.

### Why previous checks missed it — concrete test gap

- `carrier/bootstrap/directory_test.go` fixtures issue a minute before the test
  clock; native comparisons already use full `time.Time`, never Python's cast.
- `tests/vectors/bootstrap-timestamps.json` exercises offset/fractional **expiry**;
  its issuance is11:44:58.966797108 while `now` is11:45:00. The earliest Python
  check still occurs in a later second, so integer truncation cannot reject issuance.
- `configured()` in Python creates seeds with `issued_at=iso(now-1)` and integer
  timestamps. Existing synthetic sync/delivery/native tests therefore age the
  directory before consuming it, rather than validate a real just-published seed.
- Existing real `SeedManager` test checks READY ordering and UTC serialization,
  but previously did not pass those serialized bytes through packaged Python.
- Old deployment preflight checked authority/imports/old synthetic directories;
  the first actual same-second publication check was the live operator's
  `int(time.time())` call. This is a **receiver-clock precision/cross-component
  timing coverage gap**, not an unrecognized production schema or a need for
  wider URLs/larger bounds. Safe predicate diagnostics were also missing.

### Minimal implementation and safe observability

Python directory validation now defaults to `time.time_ns()` and accepts an
explicit integer `now_ns` for deterministic testing. The old positional integer
seconds argument still means exactly that whole-second instant; it is **not**
silently advanced/tolerated. Gateway CLI no longer truncates its clock; RU sync
and both readiness-fetch directory checks preserve the clock's subsecond value.
Injected test clocks remain supported without changing grant/issuer/CRL/envelope
integer-second semantics. Real clocks use `time.time_ns()` directly. Producer and
native production code are unchanged; Go modifications are tests only.

`DirectoryValidationError(ValueError)` carries bounded stage/predicate/field codes
for parse, structure, binding, seed and time rejection. No field value appears in
the error. The new packaged `directory-check` command reads existing directory/
expected profile bindings, samples nanoseconds after reading and writes a redacted
timestamp/generation/verdict/category receipt. Atomic write, file fsync, rename and
directory fsync finish before returning/raising. Failure is not caught-and-ignored;
CLI exits nonzero after reporting the safe category. A failed persistence operation
cannot pass acceptance. Receipt lives outside any replaced/rollback directory.

This command is directory validation only; it does not replace native authority,
signature, CRL, issuer or owner-admission checks, and has no production clock-
override CLI argument. Future operators must use it instead of archived inline
`int(time.time())` snippets. [Updated invocation/order](../../deploy/friends/restricted/README.md).

### Regression, cross-component proof and final artifact

- Synthetic fixture: [`bootstrap-live-issuance.json`](../../tests/vectors/bootstrap-live-issuance.json).
  The old deployed archive rejects its Go-shaped291-byte encoding with the same
  predicate; corrected precise-clock path accepts it. Original private bytes also
  reproduce old FAIL/new PASS without edits. Frozen time is offline replay only,
  not a production expiry bypass. Exclusive directory expiry is still rejected.
- Go's actual `Directory.MarshalJSON` → Python gateway sync/export → signed
  readiness delivery → Android shared-native `wholedevice.ValidateDelivery` and
  `bootstrap.ParseDirectory`: PASS. A real local `SeedManager` publication (stub
  provider/in-memory carrier) also passes through the isolated final Python archive
  and back to native at the exact issuance instant; no Telemost network operation.
- **68 directory tests PASS**, including25 synthetic negative cases checked in both
  Python and native: bad version/Family/gateway/transport, extra/null/absent/wrong-
  type fields, empty/excess/duplicate seeds, invalid lifetime and malformed URLs;
  plus parse/size rejection and issuance/expiry±1ns across fractional edges.
  No future grace window; one-hour+1ns remains rejected.
- **142 focused Python tests PASS** (directory, restricted trust, runtime packaging).
  **306 broader regressions PASS**, no skips, including HTTP, Friends, restricted
  acceptance/provider/Android contracts and optional Go compatibility enabled.
  Final strengthened serialized gateway→delivery test additionally rerun in the
  68-test directory suite. Shell nonzero/EXIT trap/rollback-marker, hard process exit
  and fsync-failure tests verify retained redacted receipts.
- Go `test -race` and `vet`: bootstrap, wholedevice, roombroker, familysession PASS.
  Sandbox denied local httptest sockets; approved local-only rerun passed, not a
  production fault. Final artifact's uncached race run also PASS.
- Final artifact built from **committed files only** at `29d15d7`, not the retained
  uncommitted HTTP work: `state-client-build/directory-validation/final-sync-bundle/restricted-sync.pyz`.
  SHA256 **`cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`**.
  17-entry inventory, isolated `python -I` help for all commands, private replay and
  native replay PASS. Final build/replay receipts in ignored
  `state-client-build/directory-validation/`; private inputs confined to `private/`.
- Supplemental HTTP bundle from the retained HTTP worktree passes the local
  restricted-enabled matrix; it does not replace the immutable/pinned attempt #4
  archive. No public artifact/catalog/invitation or installed version changed.

### Security, Git and stopping boundary

No change to Family/owner/issuer/gateway/admission code, no additional admitted
device, CRL signature/monotonicity/TTL change, or bootstrap/dedicated-session merge.
Existing negative authorization/revocation/replay tests pass. Authority remains the
last documented attempt #4 state; no refresh/service query/start/phone operation
is performed by the offline repair. Read-only SSH evidence retrieval is the only
production access. No root/signing/private client secret is retrieved or committed.

Implementation commit excludes the pre-existing HTTP challenge hunk, workflow and
VPN-health changes. Existing work stays in the worktree; documentation records the
reproduction without erasing previous failed attempts. Logical local commits only;
**push:no; production changed:no; Redmi:no; FIELD-1:no**. No APK needed because
native runtime/producer source did not change. **STOP; no attempt #5 authorized.**

## Attempt #4 — DEPLOYMENT FAILED / ROLLED BACK, 01.10.2026

Explicit user authorization in this conversation covered only attempt #4, preserving
Family/owner/gateway/issuer,0 additional admitted devices, existing TTLs and no
public/beta/FIELD-1/push. Entry/final source HEAD:
`d27156d92fdb829fdc82471b05074270b54cd1a9`,18 pre-existing unpushed commits.
No new commit, branch, artifact rebuild, APK install or version change.

**Attempt #3 root cause remains unknown because decisive HTTP evidence was lost.**
Attempt #4 stopped at a different prerequisite boundary; it does not establish or
reinterpret the cause of #3. No claim that the current HTTP artifact worked in
production: it was staged but never activated in #4.

### Pins, baseline and operator evidence

- Exact accepted `friends-http.pyz` SHA256:
  `eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`.
  All25 inventory digests/current source bytes verified before changes; same
  previously accepted local188 PASS/4 optional Go skips, not re-executed here.
  Receipt helper remains
  `830b5dec96af01fd5650e9afd15d27661dba1a3191f5943aecbdf41fc8d0fc42`.
  Exact existing closed sync bundle/bootstrap binary/helper verified on both hosts;
  no protocol/runtime repair, no rebuilding or fallback to checkout dependencies.
- Local protected evidence/operator: `state-client-build/prov1-attempt4/`.
  `pin.json`, `baseline-http/`, verified host baselines, prepare/refresh/NL/rollback/
  readback receipts and `rollback-http/`. HTTP observations fsync before evaluation;
  safe operator results persisted locally before subsequent gates. No raw response
  body, proof, private device ID, key or OAuth token emitted in command output/docs.
- First read-only host audit had a **local harness defect**, before production
  changes: plain SQLite tuple rows used with a named-column validator incorrectly
  counted27 denials; subsequent timer handling raised `KeyError: MainPID` because
  systemd timers have no MainPID. That receipt is retained but **invalid for
  admission**. Corrected read-only audit uses `sqlite3.Row`, catches only `Rejected`,
  and handles timers separately: owner1/26 rejected. No production identity/grant
  modification or admission failure is inferred from that invalid audit.
- Verified baseline17:09:35–38UTC: ordinary status200/challenge400/chat400,
  restricted route404; RU API and both hosts' AWG/TCP active, no restarts;
  restricted units inactive, NL authorization off/directory absent. Delegation/
  owner registry/sole grant match existing reservation. Provider metadata root:root
  regular file0600, token not read by this audit. Health is service-level plus HTTPS,
  not a new AWG/TCP client data-path E2E test.
- Root-only rollback snapshots at both authorized hosts:
  `/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-attempt4-d27156d`.
  Saved unit definitions, applicable API/app/ingress, SQLite online backup and
  relevant restricted state; nginx existing configuration validated. Pinned HTTP
  candidate copied to protected staging only. No neighbouring service touched.

### JIT authority and exact stop

1. **17:13:46UTC:** accepted publisher advances authoritative CRL11→12,
   expiry**17:28:46UTC**, gateway certificate expiry**18:13:46UTC**;
   server-side validation leaf expiry17:28:46UTC (not device provisioning).
   Family/owner/issuer/gateway unchanged, other admissions0. Delegation sequence1,
   grant revision1, expiry**02.10 10:44:11UTC**, unchanged TTL/security policy.
   Stale staging6 was replaced from authoritative preflight floor11 before issuing.
   Signature/bindings checked, native gateway/canary certificates and Family/
   revision/CRL negative compatibility checks PASS. Provider metadata verified
   without reading its token; no signing secret moved into CI/Git/output.
2. **17:13:48UTC:** accepted NL installed components reused, same gateway identity
   receives fresh profile; existing tightly restricted sync authorization restored.
   Isolated helper `python -I ... gateway --help` PASS. No AWG/TCP changes.
3. **17:13:49UTC:** NL bootstrap started, ActiveState active/NRestarts0/PID2095124.
   One native `bootstrap_seed_ready` event exists; quarantined directory has one
   seed, issued **17:13:53.532852358Z**, expires **18:08:49.62807736Z**,291 bytes.
   UTC-Z emission and native READY are observed, **not full NL acceptance**.
   Python live-directory validation raised **`ValueError`**. The receipt does not
   identify the exact rejected predicate; do not guess a timestamp, provider or
   dependency root cause from the exception class. No restart storm or sensitive
   URL/token/key markers in the inspected journal interval.
4. **17:13:54UTC:** NL gate recorded `bootstrap_ready:false`,
   `failure_type:ValueError`, `rolled_back:true`; failed private directory quarantined,
   forced-command authorization disabled. Operator stopped, no retry or live fix.
5. **17:13:57UTC RU /17:13:58UTC NL:** full restricted rollback completed.
   RU `python -I ... sync --check`, live RU↔NL sync, forced-command shell/stale-CRL
   negatives, HTTP activation and its acceptance matrix **NOT REACHED**. Historical
   #3 sync success is not reused as a new #4 acceptance claim.

### Exact durable HTTP receipts

All times2026-10-01 UTC, transport error null. Baseline generation
`attempt4-baseline`; post-rollback generation `attempt4-rollback`:

| Probe | Baseline timestamp | Status/class | Rollback timestamp | Status/class |
| --- | --- | --- | --- | --- |
| Ordinary status | 17:09:35.357883Z | 200/json-object | 17:15:08.343833Z | 200/json-object |
| Ordinary malformed challenge | 17:09:35.506849Z | 400/json-object | 17:15:08.540306Z | 400/json-object |
| Safe ordinary chat malformed challenge | 17:09:35.673008Z | 400/json-object | 17:15:08.704352Z | 400/json-object |
| Restricted malformed challenge, disabled route | 17:09:35.860818Z | 404/html | 17:15:08.884808Z | 404/html |

The unchanged probe helper labels the restricted-enabled contract as expected400;
the baseline/rollback wrapper explicitly requires404 while the route is disabled.
This is not a restricted-enabled400 result. Initial17:08:34 HTTP observations also
persist and show the same200/400/400/404; they were not discarded with the failed
host-audit command. No active-generation A–G HTTP receipts exist because activation
was never reached. **Real non-canary HTTP, owner challenge and owner readiness
fetch: not run**; the read-only authority admission check is not their substitute.

### Rollback readback and final state

17:15:10–11UTC host readback: ordinary API handler/app/ingress byte-equivalent to
backup; new HTTP drop-ins absent. API/AWG/TCP and other baseline units retain their
PIDs/start timestamps; API and AWG/TCP NRestarts0. NL seed inactive/disabled/PID0,
RU sync inactive/static and timer inactive/disabled, sync authorization off, private
directory absent from live location and preserved in the attempt #4 backup.
No normal device/invitation/grant row changes. No database restore.

**Monotonic state retained:** RU authoritative DB12/staged signed CRL12; NL gateway
profile minimum/CRL12. Inactive RU runtime still holds expired CRL11 because the RU
installation/sync gate was not reached. This is not a publisher rollback: next
authorized refresh must reconcile DB/staged/NL floors at least12, not blindly use
inactive RU CRL11 or obsolete staging6. Keep serial and revocation history.

Friends API downtime: **no restart and no observed outage**; baseline/rollback
requests pass. No continuous availability measurement was run during NL-only
activation; do not claim measured zero downtime. No HTTP observer/activation needed
because the attempt stopped before that phase. Normal production remained untouched
by runtime changes; only restricted authority/NL lifecycle changed and rolled back.

Owner Redmi readiness, restricted Family TLS, BootstrapDirectory, effective device
readiness expiry, restart persistence, local cellular Auto rehearsal, Android VPN,
Chrome/end-site TLS, Family DNS/concurrent TCP, direct-DNS/protected-TCP leak,
UDP/QUIC/IPv6 fail-closed and underlay protection: **NOT RUN / device expiry N/A**.
No adb interaction, in-place installation, reactivation, data clear, manual credential
injection, forwarding or diagnostic identity. Existing field52/canary53 build versus
installation/publication distinctions remain as previously recorded; no new release,
catalog/invitation change or final FIELD APK.

Worktree: all pre-existing HTTP/workflow/VPN-health work retained; current tracked
edits in this attempt are STATUS/PLAN/report/runbook only, operator/evidence ignored.
No implementation fix/test rerun after live failure. **New commits0; git push:no;
FIELD-1 started:no; distributed beta:no.** STOP after rollback/documentation;
separate local investigation and fresh authorization required for another attempt.

Final local verification: accepted artifact/source25-entry pin unchanged;
`git diff --check` PASS; four changed documentation files/277 links/0 errors.
Pre-existing STATUS/PLAN sections byte-equivalent after new checkpoints;
VPN-health report SHA256 unchanged. Final HEAD remains `d27156d`.

## 5N-HTTP-LIVE-REVALIDATION — READY FOR DEPLOYMENT AUTHORIZATION

01.10.2026, local validation16:57–16:59UTC. Entry/final HEAD
`d27156d92fdb829fdc82471b05074270b54cd1a9`, branch `main`,18 local unpushed
commits. No new commit/push. Retained HTTP implementation, workflow changes and
unrelated VPN-health edits were present on entry. Added only an explicit
packaged-operator shell EXIT-trap regression and this documentation/runbook update;
no HTTP artifact/source modification in this gate. VPN-health report unchanged;
pre-existing STATUS/PLAN content retained below new current checkpoints.

**Attempt #3 root cause remains unknown because decisive HTTP evidence was lost.**
The previous ordinary HTTP acceptance failed, but neither failing route nor live
status can be recovered from its surviving evidence. Current local success is not
a historical diagnosis. **Attempt #4 was NOT deployed:** this conversation contains
the conditional task, but no separate explicit authorization to cross its deployment
boundary. Prior attempt authorizations do not carry forward.

### Exact local artifact and tests

- Tested existing `state-client-build/http-activation/validated-bundle/friends-http.pyz`,
  SHA256 `eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`.
  All25 inventory entries match their digests and current source bytes, including
  handler, ordinary/restricted dependencies, lockfiles, ingress/drop-ins and probe.
  Archive imports resolve inside the zipapp despite hostile checkout PYTHONPATH;
  runs use `python -I`, isolated cwd/environment and synthetic-only authority/DB.
  This retained archive, not a newly rebuilt/lookalike handler, is the deployment
  candidate. Recheck all hashes immediately before any authorized transfer/start.
- Packaged `friends-http-acceptance.py` SHA256
  `830b5dec96af01fd5650e9afd15d27661dba1a3191f5943aecbdf41fc8d0fc42`.
  The shell-trap regression executes this exact packaged CLI, not a substitute.
- `/tmp/fc-boot1-venv/bin/python` dependencies match control/identity lockfiles;
  `pip check` PASS. Real isolated nginx1.28.0 via retained musl loader.
  Sandbox initially denied loopback socket creation (`EPERM`); this was a test
  infrastructure restriction, not an HTTP acceptance result. Approved local-only
  outside-sandbox rerun:39 focused HTTP/evidence tests PASS. Final run after adding
  shell-trap test: **188 PASS,4 SKIP**,21.39s across HTTP runtime/evidence, Friends
  access/application/catalog/chat/restricted and closed sync-runtime tests.
  Four skipped tests require optional `FC_TEST_GO` cross-language toolchain;
  no HTTP/receipt test skipped. No new full Android/native/physical test claim.
- Restricted disabled/enabled matrices preserve ordinary status, malformed
  challenge/chat/activation/configuration/referral/notice routes, wrong methods,
  unknown paths/trailing suffix rejection, valid ordinary challenge and activation.
  Enabled synthetic canary challenge reaches handler and signed readiness fetch200;
  admitted-vs-non-canary distinction remains200/403. This is not real owner proof.

### Exact persisted receipts — LOCAL ONLY, not production HTTP

Protected ignored evidence: `state-client-build/http-revalidation-20261001/`.
`artifact-sha256.json` pins the full inventory; `tests.log` retains the final result.
`http/`, `https/`, `shell-trap/` contain copies of the original redacted receipts,
file0600/directory0700, fsynced. Fixture credentials/keys/proofs/bodies not copied.

All following times are2026-10-01 UTC; generation `enabled`, transport error null:

| Timestamp | Probe | Status | Classification |
| --- | --- | --- | --- |
| 16:59:20.622140Z | ordinary status | 200 | json-object |
| 16:59:20.622557Z | ordinary malformed challenge | 400 | json-object |
| 16:59:20.623270Z | ordinary chat malformed challenge | 400 | json-object |
| 16:59:20.623926Z | restricted malformed challenge | 400 | json-object |
| 16:59:20.624579Z | synthetic non-canary | 403 | json-object |
| 16:59:20.626323Z | synthetic owner-canary fixture | 200 | restricted-challenge |

HTTPS generation `attempt4-fixture`: intentional untrusted local TLS certificate
at16:59:23.449537Z persists status null/error `tls`. After explicitly trusting only
the synthetic test CA, statuses200/400/400/400/403/200 persist at16:59:23.483056Z,
.491396Z,.498997Z,.505572Z,.563172Z,.571000Z respectively. TLS validation is not disabled.

Ordering proven: probe → timestamp/status/response classification/config-generation
record → file flush/fsync → atomic rename → directory fsync → evaluate → rollback
simulation if failed. No body, proof, identity or OAuth value is recorded. Persistence
errors abort acceptance. Nonzero CLI result, `os._exit(23)` after probe, SIGTERM
during probe and failed upstream retain receipts. EXIT-trap simulation reads the
already durable status200 at16:59:23.765025Z and ordinary challenge502/`html`
at16:59:23.766592Z (generation `shell-trap`) before writing its rollback marker.
The shell exits nonzero; starting the isolated backend restores400 without changing
either receipt; teardown preserves them. This proves local operator ordering and
recovery simulation, not actual systemd/production rollback. Uncatchable kill/power
loss before persistence cannot guarantee a completed observation.

### Authorization boundary, production and remaining acceptance

No SSH, provider read, authority refresh, service change, deployment or phone access.
Fresh CRL sequence/expiry: **not issued**. Last documented authoritative sequence11,
issued14:40:41UTC/expiry14:55:41UTC; gateway certificate expiry15:37:13UTC. Expired
at this validation; staging6 is not authoritative. Last production evidence remains
attempt #3 rollback: NL seed/timer/auth off, RU ordinary200/400 and restricted404.
This session did not refresh that live observation or infer present service state.

After separate authorization only: back up relevant live state; verify selected
artifact/config/harness hashes; accepted publisher refresh from current DB/live
floors and gateway certificate, no TTL extension or identity/admission change;
same Family/owner/issuer/gateway,0 other devices. NL accepted bootstrap/broker,
provider/gateway identity and sync authorization → READY and accepted UTC-Z directory;
RU accepted closed `restricted-sync.pyz`/config/authority → `python -I ... --check`,
RU↔NL sync, no import error, stale CRL and generic shell rejected. On failure stop
and rollback restricted runtime before API activation. Only then install tested
Friends HTTP archive/drop-ins/additive ingress and collect six durable live receipts.
Any ordinary regression requires saved exact error/status and immediate rollback;
no Redmi and no speculative cause. See [runbook](../../deploy/friends/restricted/README.md).

Rollback must restore saved ordinary API/ingress and remove both new API drop-ins;
stop/disable only restricted seed/sync/timer/auth. Preserve DB, serial history and
all newer monotonic floors; never restore an older DB over new revocations. No
rollback performed here because production was not changed.

NL bootstrap/RU sync/API activation and real canary/non-canary HTTP: **not run here**.
Owner Redmi readiness, Device Identity/normal provisioning/restricted TLS/directory,
restart persistence, cellular Auto restricted rehearsal, Android VPN, Chrome≥2
HTTPS sites, Family DNS, concurrent TCP, direct-DNS/protected-TCP leak, UDP/IPv6
fail-closed and underlay checks: **not run**. No installation/uninstall/data clear or
manual credential injection. Existing private canary53 (`0.1.18-canary53-prov1`)
from attempt #2 remains a prior build, not a fresh installed/public artifact claim;
field52 installation is last documented, not rechecked. No client version change,
public distribution/invitation/catalog change or final FIELD APK. Production final
state: unchanged by this gate; last documented restricted rollout rolled back.
**Commits:new0; push:no; FIELD-1 started:no. STOP pending authorization.**

Final checks: `git diff --check` PASS; four changed documentation files/274 links/
0 errors; all25 artifact/source entries still identical. Existing STATUS/PLAN
content after the new checkpoints matches the protected entry snapshots exactly;
unrelated VPN-health report SHA256 unchanged. HEAD remains `d27156d`.

## Попытка №3 — DEPLOYMENT FAILED / ROLLED BACK, 01.10.2026

Source HEAD: `2705db4a9d0d813c21b6010c478c5d36b6bcd429`. Отдельное разрешение
владельца распространялось только на прежний single-owner canary. Попытки №1/№2,
их rollback и локальные исправления ниже сохранены. Эта попытка **не PASS**:
закрытый sync runtime доказан live, но после включения API не прошёл normal smoke.
Немедленно выполнен rollback; live-исправлений и повторной активации не было.

### Source, artifacts и preflight

- Три параллельных VPN-health файла не изменялись и не входят в task commit:
  `docs/STATUS.md`, `docs/PLAN.md`, `docs/releases/2026-10-01-vpn-health.ru.md`.
  Их исходные SHA256 и patch сохранены в ignored `state-client-build/prov1-attempt3/`;
  итоговая проверка byte identity обязательна. Текущий checkpoint поэтому здесь,
  в code map/docs index/runbook, а не поверх чужих STATUS/PLAN edits.
- `state-client-build/runtime-packaging/final-bundle/restricted-sync.pyz`:
  SHA256 `e7e0c8a2ebefdd8ae6f6829f86fcac214b4c4dadb50f0664f0a4e92ea3498788`.
  Весь inventory, archive и overlay совпали с текущими исходниками. Повторные
  isolated runtime tests: **32 PASS**; именно final archive с `python -I ... sync
  --check`, cwd `/tmp`, без PYTHONPATH, на новой synthetic-only fixture: PASS.
  Fixture не передавалась на production. Предыдущие311 PASS/2 skips не объявляются
  повторно выполненными в этой попытке.
- Android/carrier source не менялся после `e808f50`; accepted canary53 APK hash
  перепроверен: `de6426be9bfd197433101857f4e41afc3880bd514aa380a80563455473bf9dbf`.
  Путь: `state-client-build/prov1-attempt2-e808f50/artifacts/FamilyConnect-canary53-prov1-e808f50-arm64.apk`.
  Сборка/подпись/JNI provenance из попытки №2 сохранены; **новой Android сборки,
  установки или физического взаимодействия не было**. Это не final FIELD artifact.
- RU/NL host identities проверены через strict существующие SSH pins и server-side
  address. Normal units/PIDs/start times совпали с rollback №2; RU HTTPS verified:
  status200, обычный challenge400, restricted challenge404. DB integrity/schema,
  devices/invites/grants и единственный owner grant без drift;26 остальных rejected
  через production admission validator. Provider проверен только server-local
  schema/metadata: root:root0600; значение/hash/размер токена не выводились.
- До runtime changes на обоих хостах создан отдельный root-only rollback snapshot:
  `/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-2705db4`.
  Сохранены definitions, API app/handler, ingress, online SQLite backup, прежние
  материалы/helper. Предыдущие backup/evidence не перезаписывались.

### Deployment order и результаты

1. **14:37:13UTC:** accepted publisher обновил CRL5→6, expiry14:52:13UTC;
   gateway certificate expiry15:37:13UTC. Та же Family, owner, issuer и gateway;
   других admitted devices0; grant revision1/delegation sequence1 неизменны,
   grant/delegation expiry02.10 10:44:11UTC. Native gateway/canary certificate
   validation и revision/CRL negatives PASS. TTL не продлевались; миграций нет.
2. NL получил проверенный archive/overlay/helper и свежий gateway profile.
   Forced command использует `python -I .../restricted-sync.pyz gateway`.
   **14:37:16 старт;14:37:47 READY:** directory issued
   `2026-10-01T14:37:19.717431985Z`, expires
   `2026-10-01T15:32:16.537670305Z`; Python принял живой каталог, required bootstrap
   seed join_url присутствует. Ни URL, ни credential bundle не выводились.
3. RU установлен тот же archive, SHA совпал. **14:38:15:** production-local
   `python -I ... sync ... --check` PASS, до publisher/SSH; API source ещё не менялся.
   **14:38:18–28:** live sync PASS, CRL6→7, expiry14:53:18UTC; fresh directory
   получен, UTC-Z принят. Dedicated SSH strict pin/forced command работают;
   запрос `id` отклонён exit126/empty stdout, предыдущий signed CRL6 после7 —
   exit1/empty stdout. **ModuleNotFoundError не повторился.**
4. Только после sync PASS включён30s timer, точный overlay/handler, API drop-in
   и новые ingress locations; nginx validation с `-c /etc/fc/nginx.conf` PASS.
   API restart отмечен systemd в **14:39:06.694802UTC**. После reload не прошла
   проверка `status/server-load.json == 200 && friends/challenge == 400`.
   Это конкретный stop-trigger; какая из двух проверок/какой HTTP-код вызвали
   failure, из сохранённого evidence установить нельзя. Root cause **не установлен**;
   отсутствие import errors в journal не является доказательством API acceptance.
5. Rollout остановлен **до** owner/non-canary HTTP acceptance и до Redmi.
   **14:40:45UTC RU /14:40:47UTC NL:** timer/sync/seed остановлены, timer/seed
   disabled, forced-key authorization выключена, NL directory quarantined.
   API app/handler/ingress восстановлены, drop-in удалён; обычный API перезапущен
   на сохранённом коде. DB **не восстанавливалась поверх monotonic state**.

### Downtime: граница измерений

Во время API restart работал HTTPS probe каждые≈100ms. Но его observations и
status map хранились в памяти операторского процесса, а assertion оборвал процесс
до записи receipt. Они потеряны; настроенные access logs выключены, journal не
содержит request-кодов. **Точный фактический HTTP downtime не измерен/не доказан;
0s не заявляется.** Systemd фиксирует99-секундный интервал между запуском нового
API14:39:06.694802 и восстановленного14:40:45.510708; это окно новой конфигурации,
не доказанная продолжительность недоступности. Следующий локальный prerequisite:
сохранять безопасные probe receipts/statuses в `finally`, проверить API/ingress
transition из точного staged layout, не делать ещё один слепой production retry.

### Финальное состояние после rollback

Readback14:41:59–14:42:09UTC: RU ordinary HTTPS status200/challenge400;
restricted challenge404, drop-in отсутствует; app/handler/ingress byte-identical
backup. RU API active, изменился PID из-за deployment/rollback restart.
**AWG/TCP RU/NL и прочие baseline units без restart/PID/start-time изменений.**
Devices/invites/grants byte-equivalent SQL rows, admission по-прежнему owner1,
других0.26 отказов подтверждены preflight validator, **не** новым live HTTP gate.

Timer успел штатно продвинуть CRL до **11**, issued14:40:41UTC,
expiry**14:55:41UTC**; RU и NL consumer согласованы. Последняя CRL/DB sequence11,
certificate history и authority сохранены, floors не сброшены. Root-only staging
после JIT содержит6: перед будущим refresh нужно опираться на authoritative DB/live
CRL11, не запускать старый stage-only script как будто6 — текущий namespace floor.
Gateway certificate expiry15:37:13UTC. Archive и NL бинарник остаются установленными,
**неактивными**; RU sync inactive/static, timer inactive/disabled; NL seed
inactive/disabled/PID0, NRestarts0. Provider root0600 сохранён. NL journal содержит
один `bootstrap_seed_ready`, без sensitive URL/token/private-key markers и без
dedicated-session events. Yandex token остаётся только NL; KeePass не открывался.

Physical provisioning/BOOT-1/readiness expiry/restart persistence/rehearsal/Chrome/
Family DNS/concurrent TCP/leak/UDP/IPv6/underlay proof **не запускались**.
Не выдавать старые isolated результаты за production-canary proof. Final FIELD APK
не создан, текущий Redmi не трогали. Public release/push/FIELD-1: **нет**.
Локальные redacted receipts: ignored `state-client-build/prov1-attempt3/`;
protected host backup содержит rollback evidence. **STOP после документации;
новое разрешение не подразумевается, автоматического retry нет.**

Итоговые локальные checks: public docs412 files/2515 links/0 errors;
source guard1563 index entries/0 blocked files; `git diff --check` PASS.
Все три защищённых parallel файла byte-identical исходным SHA256. Worktree после
task commit должен содержать только эти три исходных чужих изменения.

## 5N-RUNTIME-PACKAGING — PASS локально, production не изменён

Starting HEAD: `7350d32c36ae30b4625ab8518caa87bbba887b26`.
Implementation commit: `460bbe9e8028700e0245600a7c1d734668a91285`.
Только локальное исправление RU runtime packaging после попытки №2. Нет SSH,
production deployment/start/reload, authority/CRL refresh, provider access, Redmi
или physical tests. Успешная живая timestamp-проверка, ошибка импорта и откат
попытки №2 ниже сохранены без переписывания. Общий 5N-PROV-1 не объявляется PASS.

### Воспроизведение и root cause

Прежний runtime воспроизведён **до правок** с тем же layout:
`friends-access/app/{control/friends,device_identity,provisioning}` и командой
`venv/bin/python -m control.friends.restricted_sync --help`, cwd=`friends-access/app`.
PYTHONPATH/PYTHONHOME отсутствуют. `sys.path` содержит cwd как пустую строку,
stdlib Python3.14 и locked venv site-packages; root checkout отсутствует.
Результат: exit1, `ModuleNotFoundError: No module named 'clients'` до parser/main.
Даже `--help` не проходит, точно как импорт production sync до publisher/SSH.

Причина — **неполный ручной source-copy manifest**, не неверный cwd/install root,
не relative import и не отсутствующий PyPI-пакет. Цепочка:
`restricted_sync` → `provisioning.friends_catalog` →
`clients.desktop.profile_config`. `clients` — namespace исходников проекта;
установка одноимённого стороннего pip-пакета не является исправлением.
Прежние pytest/build запускались с полным checkout на module path, а authority
staging содержал больше файлов, чем минимальный RU runtime. Тестирования точного
deployment artifact вне checkout не было; эта разница скрыла зависимость.

### Решение по границе зависимостей

Выбран разрешённый вариант **B — явная lightweight dependency**. `profile_config.py`
содержит161 строку чистой проверки/построения профилей; imports только
`base64/ipaddress/re/json/uuid`, без GUI, backend, сети или persistence. Проверка
Friends catalog действительно использует его `parse_tcp`, `parse`, `validate`
для подписанных AWG/TCP templates. Это намеренное переиспользование parser, не
необходимость серверу запускать desktop app.

Перемещение parser сейчас затронуло бы несколько desktop/TCP packagers и
шестифайловый legacy archive. В этом gate безопаснее явно поставить **только этот
файл** в его существующем namespace; не копировать весь clients/desktop/репозиторий,
не дублировать parser и не менять его source. Регрессия фиксирует stdlib-only
границу. Общий parser/provisioning/Android source неизменён — Android rebuild
не требуется и не выполнялся. Trust roots, Family, admission, TTL, revisions,
подписи, BOOT-1/descriptor/session semantics не изменены.

### Закрытый artifact и entrypoints

- `deploy/friends/restricted/runtime-files.json`:10 явных Python-файлов —
  Friends access/restricted/admin/sync и package marker, device identity/marker,
  Friends catalog/marker и один profile parser.
- `scripts/package_restricted_runtime.py`: проверяет source list/отсутствие
  symlinks/пропусков, не перезаписывает output, создаёт `app/` overlay и стандартный
  stdlib zipapp `restricted-sync.pyz` из **тех же bytes**. Также поставляет два
  существующих lockfile, unit/timer/helper и SHA256 inventory; без state/fixtures.
- RU unit и NL forced-command теперь запускают
  `venv/bin/python -I /opt/apps/family_connect/friends-access/restricted-sync.pyz`
  с прежними `sync`/`gateway` параметрами. Корень модулей — archive, не cwd;
  sys.path/PYTHONPATH hacks **не используются**. Venv зависимости по обоим locks
  проверены: все установлены с точными версиями, включая RNS1.5.1/cryptography46.0.7.
- `app/` — overlay для existing API, **не полная замена** старого API app; normal
  API modules сохраняются. Новый runbook запрещает ручной выбор трёх папок.
  NL helper сохранит exact forced-command/argument restrictions; любые другие
  команды отвергаются с126. В production новые templates не устанавливались.
- Новый **локальный** `sync --check`: загружает issuer/anchor/admission/CRL,
  проверяет существующие signatures/expiry и read-only SQLite sequence/integrity,
  bounded sync-key/known-host files; затем останавливается перед publisher/SSH.
  Нет writes/room creation. Это не SSH authentication check и не автопродление CRL.
  Ошибки выводятся только как `Restricted synchronization unavailable`.

Финальный local artifact:
`state-client-build/runtime-packaging/final-bundle/restricted-sync.pyz`.
SHA256: `e7e0c8a2ebefdd8ae6f6829f86fcac214b4c4dadb50f0664f0a4e92ea3498788`.
Содержимое: ровно10 source modules + stdlib-generated `__main__.py`, без credentials.
Это source runtime; сторонние библиотеки предоставляются declared locked venv,
а не неявно из checkout. Safe receipts: ignored `state-client-build/runtime-packaging/`.

### Изолированные доказательства и регрессии

| Проверка | Результат |
| --- | --- |
| Старый трёхпапочный runtime, прежний `-m` entrypoint | Точный missing `clients` воспроизведён |
| Готовый zipapp: `--help`, `sync --help`, `gateway --help`, `python -I` | PASS вне checkout |
| Module origin probe | Все project imports из archive, не checkout/site-packages |
| Exact unit command с fixture `--check` | PASS из штатного app cwd и постороннего cwd |
| Отдельный запуск **финального artifact** из `/tmp`, без PYTHONPATH | PASS, `Restricted runtime pre-network check passed` |
| CLI authority/config fixture | Полностью синтетическая test authority; production material не читалось |
| DB/CRL/fixture files после `--check` | Bytes/mtime неизменны, publisher/SSH/socket запрещены отдельным spy-тестом |
| Malformed authority, expired CRL, sequence mismatch, private-key mode | Fail closed без repair/writes/secret output |
| Удаление каждого manifest source | Builder отказывает до создания artifact |
| Удаление каждого транзитивного runtime module из zipapp | Import fails, даже с checkout в cwd/PYTHONPATH |
| Forced-command wrapper и точные unit paths/flags | PASS; другие команды/аргументы отвергнуты |
| Focused Python suite | **311 passed,2 skipped**,9.01s; внутри32 новых packaging tests |

Suite включает Friends catalog/access/client/store/owner/application, provisioning
security, restricted backend/native delivery, provider input/Android source
contracts и desktop AWG/TCP/profile parsers. Все4 Go-backed delivery fixture tests
запущены с locked toolchain, не skipped. Два skip — существующие TCP installer
preflight cases: у local host нет TUN device. Это не physical/PERF testing.
Промежуточные ошибки test harness (повторяющиеся Environment в systemd и удаление
уже отсутствующего PYTHONPATH) исправлены до итогового полного прогона.

CI path filters теперь включают server modules, runtime manifest/helper/builder;
новый regression входит в существующий pytest job. CI удалённо не запускался.
Docs guard:412 файлов/2514 ссылок,0errors; staged source guard1563 entries,
0blocked; `git diff --check` PASS. Runtime/test artifacts остаются ignored.
Runbook/architecture/docs index/report обновлены. Три параллельных VPN-health
файла (`STATUS`, `PLAN`, VPN-health report) **побайтно сохранены**, не staged и не
включены в commits этой задачи; их новые правки/перестановка не выполнялись.

**STOP:** deployment не повторять автоматически. Никакого push, production change,
authority refresh, restricted service start, Redmi или FIELD-1 в этой задаче.
Следующий rollout требует отдельного разрешения и свежего preflight/JIT материала
с сохранением действующих monotonic floors, а не использования истёкшего CRL5.

## Попытка №2 — DEPLOYMENT FAILED / ROLLED BACK, 01.10.2026

Исходный clean HEAD: `e808f503c2fcf05f5f3c016988fbe25ca88a89dc`.
Пользователь отдельно разрешил controlled canary retry, но не push, public Android
release, расширение admission или Krasnodar FIELD-1. Предыдущая неудача и локальное
исправление timestamps сохранены ниже. Итог этой попытки **не PASS**.

### Место и полный Android build

- Очищен только `/tmp/fc-boot1-tools/cache` штатным `go clean -cache` с явным
  GOCACHE после проверки task ownership. `/tmp` free: **3 284 455 424 →
  6 246 584 320 bytes**. SDK/NDK/JDK, APK, evidence, ключи и чужие файлы сохранены.
- TMPDIR/build output — ignored `state-client-build/prov1-attempt2-e808f50/`;
  Go cache — `state-client-build/time-compat/go-cache`. Disk free после очистки
  17 547 005 952 bytes; после сборок/артефактов около15.45GB.
- Оба JNI построены заново из текущего source, старые `.so` не использованы.
  Gradle8.11.1, JDK17, Python3.10, Go1.26.1, NDK27.2.12479018, arm64-v8a.
  `assembleFriends`, `testFriendsUnitTest`, `lintFriends`: **BUILD SUCCESSFUL**,
  58s,68 выполненных задач; **194 tests,0 failures/errors**;
  lint0errors/36warnings. Gradle deprecation warnings не исправлялись.
- Private packaging override: `.friends`, versionCode53,
  `versionName=0.1.18-canary53-prov1`, non-debuggable; public beta51 defaults и
  каталоги неизменны. Diagnostic activities отсутствуют; debug-only forced-failure
  hooks не активны. APK/вложенные Python-assets:1074 entries,0 findings после
  одного ранее проверенного stdlib false-positive. Это bounded secret scan.
- Подписан существующим защищённым beta PKCS12 через memfd без вывода секретов.
  ZIP alignment/APK v2 signature PASS. ADB read-only: Redmi Note9Pro, Android12,
  arm64, установлен field52; публичная подпись совпадает, update53 совместим.
  **Установки нет**, Device Identity/private app data не читались.

| Артефакт / provenance | Значение |
| --- | --- |
| Canary APK, не FIELD release | `state-client-build/prov1-attempt2-e808f50/artifacts/FamilyConnect-canary53-prov1-e808f50-arm64.apk` |
| APK SHA256 | `de6426be9bfd197433101857f4e41afc3880bd514aa380a80563455473bf9dbf` |
| Signing certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Packaged fresh `libfc-awg.so` | `1263b9395d28713c96807f0eb888fa9b586a2e28180b2764a8c875c8874406b4` |
| Packaged fresh `libfc_restricted.so` | `3be3838edb9bf68c2ef4cdf49fa544cb72e19b07306d48dca4064f644ab6641b` |
| Xray revision, оба builder | `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` |
| Amnezia Android / engine revision | `5420011143f9dd42831cc95fcdb0d6ac9bde868f` / `b5928efb6ca19f0153958460c3d141f04abc5c2e` |
| restricted gVisor | `v0.0.0-20260122175437-89a5d21be8f0` |
| Fresh host bootstrap-broker SHA256 | `e17e1fe77aa0121847c276fa15db9064d29b714977a57b568183e9950149b1b8` |

Packaged native bytes совпадают со свежими outputs/manifest. Финальный shareable
FIELD APK не создан. Go race/vet и Python91 timestamp checks — предыдущий local
fix checkpoint, повторно здесь не запускались. Physical/PERF tests не запускались.

### Preflight, backup, JIT authority

Read-only RU/NL: strict SSH/host identity, normal service PIDs/start times,
API/ingress bytes, DB integrity/четыре additive restricted tables и normal rows
совпали с attempt1 rollback. Локальный audit сначала ошибочно требовал active для
штатно отключённых на данном хосте служб; полное baseline-сравнение подтвердило
**нет drift**, проверка исправлена локально. RU free8827MiB/MemAvailable1110MiB;
NL free14086MiB/MemAvailable540MiB. HTTPS trusted/200, certificate до
05.10 12:25:56UTC; certificate infrastructure не менялась. provider.env на NL:
root:root0600, server-local schema/non-empty PASS; token не выводился, не
передавался, его хэш/длина не публиковались, KeePass не открывался.

До runtime изменений оба хоста получили root-only backups:
`/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-e808f50/`.
RU SQLite online backup, API app/handler, ingress, unit baseline; NL прежние
helper/app/binary/gateway/unit. Ключи/profile/DB остаются на соответствующих хостах.
Rollback подготовлен до первого старта; прежние backups не заменялись.

JIT publisher **01.10 13:31:55UTC**: CRL **4→5**, expiry **13:46:55UTC**;
gateway leaf expiry **14:31:55UTC**. Прежние Family/owner/issuer/gateway,
других admissions0. Grant revision1/delegation sequence1, оба до
**02.10 10:44:11UTC**. TTL неизменны, namespace не сброшен. Native gateway/canary
certificate validation и negative Family/revision/CRL cases PASS. Новых миграций
нет: schema уже применена ранее. При начале NL CRL оставалось >10min, перед RU >8min.

### Последовательность и точный новый блокер

1. Staging обновлён текущими Go/Python артефактами. При установке NL `copyfile`
   поверх service-owned gateway.json отклонён `fs.protected_regular=2` в sticky1770
   каталоге. Служба ещё не запущена. Readback: binary обновлён, старый профиль цел,
   sync authorization отсутствует. Завершена atomic create/fsync/chown/rename
   замена профиля; защитные sysctl/права не ослаблялись, CRL повторно не выпускался.
2. NL bootstrap старт **13:35:34UTC**, READY подтверждён **13:36:07UTC**.
   Один seed,0 restarts; provider initialization/gateway join PASS. Snapshot:
   `issued_at=2026-10-01T13:35:36.694506508Z`,
   `expires_at=2026-10-01T14:30:34.419780801Z`.
   Go exporter → исправленный Python directory parser **PASS**, canonical UTC
   проверен без ручной правки snapshot. Bootstrap join_url присутствует, не
   выводился. Journal: один `bootstrap_seed_ready`, без secret/URL markers;
   dedicated-session request/descriptor не создавался.
3. После NL PASS на RU скопированы принятые modules/materials и sync unit/timer.
   **13:37:55UTC**: первый start sync завершился `exit1/ModuleNotFoundError:
   No module named 'clients'`,0 restarts. Цепочка: `restricted_sync.py:15` →
   `provisioning/friends_catalog.py:14` → `clients.desktop.profile_config`.
   Минимальный RU deployment не содержит `clients`. Publisher/SSH внутри sync
   не достигнуты: БД/CRL сохранили sequence5. Timer не включён, API drop-in/
   ingress reload/API restart не достигнуты.
4. **STOP**, без ad-hoc live добавления зависимости и повторного запуска.
   Локальное воспроизведение: ровно `control/friends`, `device_identity`,
   `provisioning`, `python -I -B`, cwd вне checkout → тот же missing `clients`.
   Полный authority staging/checkout скрывал транзитивную зависимость;
   isolated runtime closure не был проверен. Нужен отдельный локальный packaging
   fix/import smoke, не изменение trust/TTL или ручное редактирование credentials.

### Откат, downtime и окончательные проверки

- **13:39:05UTC RU**: sync service/timer выключены; API app/handler/ingress
  восстановлены byte-identical. Friends API PID/start всё время прежние:
  перезапусков0, ingress reload0. DB назад не восстанавливалась, sequence5,
  ledger/отзывы сохранены. Root-only материалы и новые не включённые units
  остаются инертными; sync status failed/PID0 сохраняет evidence.
- **13:39:07UTC NL**: bootstrap stopped/disabled/MainPID0; sync authorized key
  в protected backup, directory quarantined, listener18444 отсутствует.
  Исправленные binary/helper, account/unit/gateway/provider остаются инертными;
  token сохранён root:root0600. Rollback не затронул AWG/TCP.
- **13:44:44–45UTC** final readback: все исходные normal PIDs/start times
  неизменны,0 restarts. RU API/AWG/TCP active; NL AWG/TCP/control-provider/mailbox
  active. Timer inactive/disabled, bootstrap inactive/disabled/0restarts.
  HTTPS status200, обычный malformed challenge400, restricted challenge404.
  devices/invites/restricted_grants неизменны. Actual `_grant`: owner1 admitted,
  **26 non-canary rejected**,0 others. Это authority check, **не** acceptance
  ещё не включённого restricted HTTP endpoint.
- API interruption: restart/reload не выполнялись, наблюдаемого перерыва нет.
  Непрерывный HTTP downtime probe планировался вокруг API restart, до которого
  rollout не дошёл. Это **не непрерывное измерение нулевого downtime**.
  Normal activation/provisioning rows не переписывались; user-session normal
  data-plane smoke не проводился, service/control regression checks PASS.
- Redmi остаётся field52. Installation/product-prewarm/readiness expiry/restart
  persistence/restricted rehearsal не выполнены. Chrome, Family DNS, concurrent
  TCP, DNS leak count, protected TCP bypass, UDP/IPv6 fail-closed, underlay и
  10min light smoke **не измерены** — не заявляются нули/PASS.

Safe receipts/build logs: ignored `state-client-build/prov1-attempt2-e808f50/`;
приватный runtime не коммитится. Параллельные изменения VPN-health документации
сохранены отдельно от этой работы. Docs check:412 файлов/2509 ссылок,0errors;
staged source guard1559 entries/0blocked; `git diff --check` PASS. Это bounded
проверки, не полный аудит secrets/history. Перед новым отдельно разрешённым retry:
исправленный isolated deployment manifest, JIT refresh **после sequence5**,
health/rollback checks. Не возобновлять rollout автоматически. Push/public Android
release/FIELD-1: **нет**. Предыдущие failure/fix evidence сохранены далее.

### Исторические результаты перед попыткой №2

## 5N-TIME-COMPAT — PASS locally, production remains rolled back

Entry HEAD `e77aea8eb78c74197197d0ebbbe1d87053c36f0c`, clean worktree.
The owner authorized **local repair/tests only**. The failed production attempt
below is preserved unchanged. No SSH, provider/OAuth access, authority refresh,
service operation, deployment, physical Android/PERF run, public release or push
was performed in this repair task. **5N-PROV-1 is not promoted to PASS.**

### Contract audit and minimal repair

- Root cause: Go seed expiry inherited a context deadline's local timezone while
  issuance used UTC; Python accepted only `Z`, although Go/native uses RFC3339
  instants. `2026-10-01T15:39:55.760348939+03:00` is the same instant as
  `2026-10-01T12:39:55.760348939Z`, not an extra3h validity window.
- Producer: `SeedManager` explicitly converts deadline to UTC; `Directory.MarshalJSON`
  canonicalizes both fields for every Family-owned Go serialization. No host
  timezone change, manual snapshot rewrite or string suffix substitution.
- Consumer: Python accepts strict offset-aware RFC3339 and converts via UTC
  arithmetic. It compares exact integer nanoseconds, retaining the production
  fixture's9-digit fraction. It canonicalizes timestamps in the returned delivery
  object. Integer envelope expiry still floors conservatively to seconds.
- Native parser: strict shared lexical checks reject malformed offsets/clock
  forms that standard-library parsers can normalize permissively. Parsed Go
  timestamps are UTC instants. Shared wire precision is0–9 fractional digits;
  naive/malformed/invalid dates, leap seconds, excess precision and trailing junk
  are rejected. Python3.14's newly permissive `24:00:00` is explicitly rejected.
- RU sync imports the same authenticated bounded snapshot and validates through
  the fixed parser; no new signature/root. Raw sync/cache input bytes need not be
  rewritten. New Go producer and Python API serialization emit UTC trailing `Z`.
- No **cryptographic** dependency on raw directory timestamp spelling found:
  standalone directory signature is absent; Family-authenticated delivery is the
  trust boundary. Signed issuer payload, X509/CRL signatures, challenge proof,
  admission, revisions, gateway identity and AES-GCM vault remain unchanged.
- Go cache replay compares `time.Time` instants and canonical payloads; equivalent
  offset spellings are idempotent, changed same-issued content rejected. Android
  `RestrictedCache` already orders with `Instant.parse`; production Java code is
  unchanged, including stricter equal-issued JSON equality. Tests explicitly keep
  that conservative conflict rejection and restart/preservation behavior.

### Regression proof and exact scope

One shared `tests/vectors/bootstrap-timestamps.json` contains canonicalZ, +03:00,
-05:30, actual failed expiry/issuance with nanoseconds, and invalid variants.
Family/gateway references and join URL are synthetic; no production identifier,
credential, room URL or token is in the fixture.

- OLD Z-only parser reproducer rejects the actual +03:00 expiry; NEW parser accepts
  the same semantic directory and emits equivalent UTC. Z and negative-offset
  fixtures resolve to the same epoch instant and pass native directory validation.
- Fake READY seed connector with a non-UTC **parent context deadline** proves fresh
  `SeedManager` publication uses UTC in memory and in JSON, without global timezone
  mutation or any Telemost call.
- Shared fixtures exercise Python sync gateway → Python authenticated delivery →
  native `ValidateDelivery` / `ParseDirectory`, including signatures and bindings.
  Historical fixed-date vectors use explicit validation time; the existing fresh
  wall-clock fixture still exercises `DeliveryMaterial` and Family TLS configuration.
- Both directory fields reject malformed inputs. Expiry before/at/after boundary,
  positive/negative offset equivalence, subsecond expiry, future issuance and
  lifetime one nanosecond over1h are checked without TTL extension. Go and Android
  tests reject stale instants even when lexical string order is reversed.
- Family/gateway/seed URL, CRL/sequence/revision, revoked grants, replay, size bounds,
  old-cache preservation, on-demand dedicated session and trust tests retained.

Validation:

| Local check | Result |
| --- | --- |
| Python restricted readiness, sync/native fixtures, Android contracts, provider-input and restricted/Orchestrator acceptance contracts | **91 passed**,0 skipped |
| Go `test -race` bootstrap/wholedevice/roombroker/familysession | **PASS**,4 packages |
| Go `vet` same4 packages | **PASS** |
| Local bootstrap-broker and delivery-check builds | **PASS**, not deployed |
| Friends RestrictedCache JVM tests using shared fixture | **6 passed**, direct javac/JUnit |
| Physical Android / PERF / APK build/install | Not run |

Initial test execution hit `/tmp` quota (SQLite I/O and Gradle cache initialization
errors); Python/Go outputs moved to ignored disk-backed
`state-client-build/time-compat/`. Gradle did not reach compilation; the actual
Java cache/parser/test classes were compiled directly with the existing JDK,
Gson/JUnit jars and shared resources; all6 tests passed. This is not a full Android
Gradle/APK build claim. Initial Python `24:00:00` regression was fixed and rerun.
The final91-test Python run also passed under `TZ=Pacific/Honolulu`; uncached Go
race tests passed under `TZ=Europe/Moscow`. No dependence on host UTC timezone.
Implementation commit: `f0cc04040177795a44d7b2448204ae4db512850c`.
Documentation validation:412 files/2502 links,0errors; staged source guard1559
entries,0blocked files; whitespace PASS. The guard is bounded pattern/path
checking, not an exhaustive secret audit. Test/build outputs stay in ignored
`state-client-build/time-compat/`; no private fixture or build output committed.

Remaining boundary: rebuild/re-stage the modified Go/Python artifacts and JIT
refresh expired authority material **only in a separately authorized deployment**.
Inert NL still contains the earlier unfixed binary/helper. Do not start it or retry
rollout automatically. No TTL, admission, trust or dedicated-session changes.

## Authorized canary rollout, 01.10.2026 — DEPLOYMENT FAILED / ROLLED BACK

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** Source HEAD
`33255fe32308128fe9cf0ea272bf0dee6a52bc10`, entry worktree clean. The owner explicitly
authorized only this canary rollout. NL reached bootstrap seed READY, but its
exported directory was incompatible with the accepted Python delivery/sync parser.
Rollout stopped **before RU runtime/synchronization/API/ingress activation**.
Only the new NL service was stopped/disabled; existing production remained healthy.
No physical acceptance, final FIELD APK, public release, push or FIELD-1.

### Exact deployment order and validity

1. Read current status/plan, architecture and deployment contract. Strict SSH to
   the two authorized IPs; authority, service PIDs/start times/restart counters and
   live API/ingress hashes matched the previous baseline. Same Family, owner
   canary, gateway identity, issuer and ControlTrust; **0 other admissions**.
2. Final prerequisite checks: RU SQLite integrity/four additive tables PASS;
   RU/NL free disk8837/14186MiB and available RAM1137/527MiB. Public HTTPS
   certificate/hostname verification and status HTTP200 PASS; certificate expires
   05.10 12:25:56UTC. Provider validated only server-side for schema/metadata:
   root:root0600; no value/hash/length exported, token not transferred to RU/local.
3. Protected rollback backups completed on both hosts at11:39:02UTC under
   `restricted-materials-stage-20261001/canary-rollout-33255fe/`: RU online SQLite
   snapshot, API app/handler, ingress and relevant unit state; NL prior service
   state. Rollback preserves current DB revocations/serial ledger/sequence floors.
   Ingress test uses the actual running `nginx -t -c /etc/fc/nginx.conf`.
   A preliminary default-config test hit read-only `/run/nginx.pid`; actual-config
   test passed without changing/reloading ingress.
4. Accepted issuer/publisher JIT refresh at **11:39:06UTC**, CRL **3→4**. No
   sequence reset, grant change, issuer rotation, new key/Family or TTL extension.
   CRL/effective profile expires **11:54:06UTC**; gateway leaf **12:39:06UTC**.
   Delegation sequence1 and grant/global peer revision1 unchanged, expiry
   **02.10 10:44:11UTC**. Actual native certificate/Family/revision/CRL negatives PASS.
5. NL installed only the new `family-restricted` account, source-matched Friends
   helper modules, separate venv with accepted control/identity locks, restricted
   binary/profile, forced-command key and bootstrap unit. No fleet/ProductStore
   runtime copied. Existing gateway private key retained; provider remains
   root:root0600. Service directory root:family-restricted01770, binary directory
   root:family-restricted0750, gateway profile service-owned0600; code/venv root-owned.
   Traversal permissions and helper import working directory were corrected and
   validated **before** first service start; no product-code patch or live workaround.
6. Systemd definitions reloaded, only the new bootstrap service started. Existing
   AWG/TCP/control-provider/mailbox not restarted. One server-created bootstrap
   seed joined and emitted **`bootstrap_seed_ready` once** at about11:44:58UTC;
   one private directory exported. No dedicated-session request/descriptor created.
7. Python compatibility check rejected the actual exported directory. RU rollout
   and synchronization were not started. New NL service stopped/disabled,
   forced-command authorization removed to protected rollback storage; directory
   quarantined, not rewritten or delivered. Rollback confirmed **11:47:18UTC**:
   inactive/dead, MainPID0, NRestarts0, disabled, exit status0, no18444 listener.
8. Final normal-regression and failure-reproduction checks at **11:48:52–54UTC**
   passed. No migration applied this turn; prior additive schema remains intact.

### Concrete compatibility failure — no live fix

`carrier/bootstrap/seed.go` creates `IssuedAt` with `time.Now().UTC()`, but assigns
`ExpiresAt` from the context deadline without UTC normalization. On this NL host
the actual directory has:

- `issued_at`: `2026-10-01T11:44:58.966797108Z`;
- `expires_at`: `2026-10-01T15:39:55.760348939+03:00` (12:39:55UTC).

These describe a valid less-than55min seed lifetime and the same accepted
Family/gateway; required seed join URL format is valid. However
`control/friends/restricted.py:timestamp()` requires `value.endswith('Z')` and
rejects the offset timestamp before synchronization/delivery. The native directory
schema accepts RFC3339 timestamps, so the earlier certificate-only native check
could not expose this live seed-export boundary. No bootstrap join URL is included
in this report or returned to the terminal.

Actual quarantined directory rejection reproduced **PASS**; replacing only its
expiry representation with equivalent UTC **in memory** made the same Python
validator accept it. No file, signed material, TTL or runtime implementation was
changed by this diagnostic check. This is not a deployed fix. Next work is a local
producer/consumer timestamp-compatibility fix and non-UTC regression coverage,
followed by new JIT material refresh and an explicitly authorized retry. Do not
silently change host timezone, manually rewrite directory JSON, extend TTLs or
automatically retry the production rollout.

### Final state / acceptance boundaries

| Item | Result |
| --- | --- |
| RU new runtime/routes/sync | Not deployed; restricted challenge returns404 |
| Normal public status / malformed ordinary challenge | HTTPS200 / expected400 |
| Friends API interruption | No API restart/reload or induced downtime;0 observed probe failures. No continuous availability trace was run |
| RU/NL AWG/TCP | Active, identical PIDs/start times/restart counters; no restart |
| Existing NL control-provider/mailbox | Active, unchanged |
| Normal devices/invitations and restricted grants | Identical row sets to protected pre-rollout DB snapshot; integrity PASS |
| Admission checks | Sole owner allowed by `_grant`; all26 non-canaries rejected; other admissions0 |
| Issuer / native certificate compatibility | PASS, same delegated issuer and gateway identity |
| RU↔NL sync | Not started; full live sync/strict remote-command negatives not claimed |
| NL bootstrap | Provider/seed reached READY once; directory compatibility FAIL; stopped/disabled |
| New NL sync authentication | Disabled after rollback; root-protected authorized-key fragment retained |
| Logs | Only safe seed-ready event;0 URL/private-key/OAuth-assignment markers,0 unknown application events in bounded unit-log check; no token comparison/export |
| Phone provisioning / BOOT-1 / expiry | Not run or changed; actual production READY still unproven |
| Restart persistence / local rehearsal | Not run |
| Chrome / TLS / Family DNS / concurrent TCP | Phone acceptance not run |
| DNS leaks / TCP bypass / UDP/IPv6 fail-closed / underlay protection | Not measured in this attempt; do not report zero or reuse isolated PASS as product acceptance |
| Final FIELD APK | Not produced; previous readiness-only APK is not final FIELD artifact |

New NL account, root-owned helper/venv/binary/unit and protected gateway/provider
files remain installed **inert** for inspection; unit disabled, no active sync key,
no live directory or restricted listener. RU final restricted directory/drop-in/
new API code/sync units remain absent. No old full DB restored: certificate ledger
and CRL sequence4 preserved. Normal production API/ingress unchanged byte-for-byte.
Public catalogs, normal users, phone identity and installed APK untouched.

Safe local receipts: `/tmp/fc-canary-deploy-33255fe/` and
`/tmp/fc-canary-jit-public-20261001/`; protected rollback receipt and quarantined
directory stay on NL. No provider backup, token print/hash/size or secrets in Git.
Documentation checks:412 files/2497 links,0errors; staged source guard1557 entries,
0blocked files; whitespace PASS. The guard is bounded pattern/path checking, not
an exhaustive secret audit. No product source changed or full synthetic suite
rerun; the actual-material/native checks and live parser reproduction above ran.
Historical evidence below is retained. **STOP; no automatic retry.**

## Subsequent authority preparation — not deployment or phone acceptance

01.10 [5N-PROD-AUTHORITY READY](2026-10-01-5n-prod-authority.ru.md): explicitly created
the first canary Family, designated existing NL identity, applied only accepted
additive restricted tables, signed delegated issuer locally, published real CRL and
prepared/validated gateway material. One owner admission; no other beta devices.
All new runtime files remain inactive staging. OAuth/KeePass not accessed; no new
API/service activation, actual phone delivery or rehearsal. Initial CRL expires
01.10 11:02:45UTC. **5N-PROV-1 PASS is still not claimed.**

## Subsequent authority audit — Phase A stop, no deployment

01.10 10:28UTC, entry `9340931`: [materials continuation](2026-10-01-5n-prod-materials.ru.md)
resolved the active Owner Friends operator record, but found no ProductStore
Family membership and no accepted restricted-gateway binding for existing NL
control-provider/mailbox identities. Conditional migration/signing authorization
does not waive Phase A: **BLOCKED before migration/signing**, not a token-only stop.
Existing anchor/staging checks pass; production services/state remain unchanged.
No deployed readiness, physical acceptance or final FIELD artifact claimed.

## Subsequent material preparation — no deployment retry

01.10, entry `f082c10`: [5N-PROD-MATERIALS](2026-10-01-5n-prod-materials.ru.md)
completed only independent inert staging (anchor/deny-all admission/SSH sync
key/pins/NL unit and authorization templates). Result **OWNER ACTION REQUIRED**:
authoritative Family/gateway/canary selection, provider token and CRL sequencing
still unresolved. Existing offline signer verified, no replacement root/signature.
No runtime change, migration, service action, phone action or deployment retry;
preceding BLOCKED/IMPLEMENTED/preflight evidence below remains historical truth.

## Authorized deployment attempt — preflight STOP, 01.10.2026

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK.** Уточнение статуса:
**prerequisite failure до начала rollout; rollback не требовался/не выполнялся**.
Это не «deployed / physical blocked». Production deployment authorization получена
для `ff9fb09af329402e538003a56eaefd0dce2b6c73`, но explicit правило пользователя
требует STOP, если обязательный secret/material отсутствует или inconsistent.
Именно это условие сработало. Ни seed, ни issuer, ни API, ни migration не deployed.

### Entry and exact missing prerequisites

- Начальный worktree clean, HEAD exact `ff9fb09af329402e538003a56eaefd0dce2b6c73`.
  Local origin/main и live `git ls-remote origin refs/heads/main` совпали:
  `26447902137735ac7633f92ba6673395bae078fa`. No fetch/push/ref rewrite.
- Прочитаны AGENTS, STATUS/current PLAN, architecture и exact accepted
  [runbook](../../deploy/friends/restricted/README.md). Runtime source не изменён.
- SSH: `BatchMode=yes`, `StrictHostKeyChecking=yes`, exact authorized IPs;
  host-key verification успешна, `SSH_CONNECTION` server destination и assigned
  interface address соответствуют каждому expected IP. RU `box-932982`,
  NL `box-966556`; соседние MicroTrader services/excluded host не затрагивались.
- RU,09:32:56UTC: `/opt/apps/family_connect/friends-restricted/` **ABSENT**.
  Required `anchor.pub`, `issuer.json`, `issuer.key`, `admission.json`,
  `revocations.pem`, `sync.key`, `known_hosts` отсутствуют по runbook paths.
- NL,09:32:54UTC: тот же protected directory **ABSENT**; required `gateway.json`
  и `provider.env` отсутствуют. Новый bootstrap service not-found; therefore
  `YANDEX_TELEMOST_OAUTH_TOKEN` **не configured на требуемом новом service path**.
  Это не утверждение, что token/gateway identity отсутствует во всех private
  stores. Другие secret locations и остатки isolated fixtures не искались,
  произвольная замена identity/CA/token не выполнялась.
- Restricted bootstrap/sync units not-found, directory snapshots absent,
  loopback18444 не занят на обоих hosts. RU deployed restricted.py absent.
  NL inspected friends-access app files отсутствуют; venv/dependencies и
  forced-command account ещё не подтверждены.

Runbook допускает создание delegated issuer во время подготовки; более позднее
user instruction явно требует STOP при отсутствующих prerequisites. Поэтому
никакая partial secret provisioning/key generation/offline signing в этом attempt
не делалась. Offline root/private device identity не читались. До retry нужны
authoritative Family/gateway material, anchored delegation/issuer, owner admission,
CRL, dedicated pinned sync credentials и server-only provider configuration;
не просить прислать OAuth/private keys в chat, не использовать diagnostic identity.

### Existing production baseline, not a new acceptance

| Проверка | RU | NL |
|---|---|---|
| Friends AWG/TCP units | active/running, NRestarts0 | active/running, NRestarts0 |
| Friends API | active/running, NRestarts0; start30.09 03:28:04UTC | not deployed here, as expected |
| Available RAM |1087.0MiB/1962.5MiB|556.0MiB/955.3MiB|
| Free filesystem space |8.63GiB|13.88GiB|
| Load1/5/15min |1.23/0.94/0.85|0.40/0.25/0.24|
| Relevant TCP listeners |443/8443/8446/18084; no18444|443; no18444|

RU product API/control containers healthy; existing peer-worker container
`family-connect-product:0.2.1` running/unhealthy, как в предыдущем health report.
Это известное pre-existing состояние, не deployment regression; не исправлялось.
Existing RU gateway images: AWG `family-connect-amneziawg:2-pilot1`, TCP
`family-connect-xray:26.3.27-pilot1`. Наличие running services не доказывает новый
end-to-end normal client smoke; activation/invitation mutation и phone traffic
не запускались после prerequisite STOP.

09:33:32UTC independent public check: system-CA/hostname verified TLS1.3 на
`185.251.89.19:8443`, certificate notBefore28.09 20:25:57UTC,
notAfter05.10 12:25:56UTC; `/status/server-load.json` HTTP200. Response body не
сохранялся/не выводился. Общий TLS validity PASS; product data-plane acceptance
не заменяется этим запросом.

### Rollback baseline and migration boundary

Read-only metadata/fingerprints собраны до изменений; secrets/config contents
не копировались в local artifacts/Git. Safe local receipt:
`/tmp/fc-prov1-predeploy-safe.json` (only whitelist metadata/presence/health).
Production roots не предоставляют Git HEAD (`rev-parse` unavailable), поэтому
deployed revision **UNKNOWN**, не приравнивается к `ff9fb09`/origin/main.
RU artifact fingerprints:

- `friends-access/access-api.py` SHA256
  `16e557b1ceb4099897558ade00b53b265566e34e76ab88d4a673af444ab1795a`.
- `friends-access/app/control/friends/access.py` SHA256
  `f37fe6eccdc6609159d26363b457c62e18b71c7036ca449a6d692349c3a3d48e`.
- `state-product-https/config/nginx.conf` SHA256
  `4426bfa9b589fcca124aed99daaaa9dedcf04cbd2c385a322d9fd92ead925267`.

Эти file bytes не совпадают с checkout versions; packaging/semantic differences
не исследованы после STOP. Перед retry сопоставить live layout/artifacts, не
заменять их вслепую wholesale install script. Unit FragmentPath/DropInPaths/hash,
ActiveEnterTimestamp/NRestarts и container image/state записаны безопасно.

RU DB read-only/query_only: devices27 (revoked4), invites81 (revoked5),
`restricted_*` tables **нет**. Inspected `migrate()` содержит только три intended
`CREATE TABLE IF NOT EXISTS`; CRL publisher добавляет restricted_crl_sequence.
Нет destructive DROP/rename/перезаписи old tables; additive schema совместима
с неизменёнными old API queries. **Migration не выполнялась**.

Backup/config snapshots на production **не создавались**, так как preflight STOP
наступил до любого planned write. Rollback path read/reviewed, но executable
backup/restore rehearsal не подтверждён в этом attempt; его нельзя считать PASS.
При retry private on-host backup/definitions/ingress snapshot обязателен до
изменений, без вывоза private data в task artifacts. No rollback needed/performed.
Deployment-induced API interruption **0s: no service transition/reload occurred**;
continuous availability measurement не запускалось, zero-downtime SLA не заявлен.

### Unperformed gates / unchanged product state

- RU/NL deployment, restricted API live security tests, production certificate
  issuance, CRL/directory sync, provider join/READY: **NOT RUN / NOT DEPLOYED**.
  No client fixture fabricated, no production room created, no OAuth acquired.
- Phone deliberately untouched: user permits physical work **only after healthy
  infrastructure**. Last-observed existing Device Identity PRESENT and normal
  PRESENT_VALID; restricted provisioning/BOOT-1 ABSENT (prior field52 evidence),
  not a fresh inspection. Effective production readiness expiry: **N/A**.
- READY process restart, local restricted rehearsal, Chrome2 sites, Family DNS,
  concurrency, leak/fail-closed acceptance: **NOT RUN in this attempt**.
- Final FIELD APK: **not produced**. Existing private field52/code52 readiness-only
  and public beta51/code51 untouched; Linux0.2.11/Windows0.2.15 unchanged. Public
  artifacts/catalogs не менялись и повторно не верифицировались.
- No uploads, production filesystem/config writes, migration, generated credentials,
  service restart, ingress reload, phone install/clear/uninstall, public release.
  No regression attributable to deployment; only baseline health snapshot taken.
- Runtime tests не повторялись: runtime source unchanged. Documentation guards
  PASS для этого docs-only update:409 files/2464 links/0 errors,
  source guard1552 index entries/0 blocked, working/staged diff checks PASS.
  Previous95/JVM193/native PASS
  ниже относится только к implementation checkpoint, не live deployment.

Production current state: **pre-existing services, unchanged; PROV-1 not deployed**.
Commits данного attempt — только local documentation evidence, hash в handoff.
Push: **no**. Krasnodar FIELD-1 started: **no**. STOP per missing-material rule.

---

## Historical implementation result after clarification — 01.10.2026

**5N-PROV-1 = IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED.**
Это local implementation gate, **не PASS** по physical production criteria.
Продолжение начато с clean HEAD `a88b104672e53e2393e16cd45b07e9fa0c2c4e00`.
Original requested local HEAD `3d9fd7ca3d020618ffb7c8f95068094450483ed4` и
`9c82152` сохранены; `a88b104` — docs-only BLOCKED audit, сохранён ниже как история.
Public origin/main по исходному evidence — `26447902137735ac7633f92ba6673395bae078fa`;
production deployed HEAD в этом continuation не проверялся и не менялся.

Runtime implementation commit: `bb71a3f6977c719c06c77bd2d0a98686c3a70102`.
Отдельный documentation commit завершает gate; final HEAD указан в handoff после
commit (не self-referential hash внутри собственного документа). Runtime source
guard:1551 staged index entries/0 blocked files. Final documentation/source guard
receipt:409 docs/2459 links/0 errors,1552 index entries/0 blocked files,
`git diff --check`/`git diff --cached --check` PASS. Это bounded guard, не полный
security audit.

User clarification разрешило bootstrap seed `seeds[].join_url`, сохранило BOOT-1
v1, запретило prewarm dedicated descriptors и лишнюю standalone directory
signature. Initial delivery использует activated Friends identity proof/HTTPS,
а не уже существующий restricted mTLS profile. Directory TTL не расширен.

## Exact gap and implemented path

Original actual Friends `/friends/*` выдавал normal AWG/WG/TCP configuration, но
не имел trusted Family certificate/BootstrapDirectory delivery. ProductStore
`/v2/*` — другая DB/trust integration, disposable Family issuer — не production.
Existing BOOT-1 normal-control refresh требовал уже provisioned Family mTLS,
поэтому не мог bootstrap ordinary activated Friends. Physical evidence до работы:
Device Identity PRESENT, normal PRESENT_VALID, restricted/BOOT-1 ABSENT.

Теперь existing HTTPS handler имеет два POST: `/friends/restricted-readiness/challenge`
и `/friends/restricted-readiness`. Existing transport proof, stored restricted
purpose/Family/revision nonce, exact Device Identity/WG binding, live device/invite/
grant, owner admission policy, expiry/revision и signed CRL проверяются до выдачи.
Nonce одноразовый/100s, outstanding≤8, request8KiB, response64KiB, concurrency4.
Replay/expired/revision-mismatched/revoked devices не получают usable certificate.
Temporary overload/config/seed/CRL failure →503; не tombstone. Valid proof выдаёт
public-only certificate, issuer delegation, signed CRL, metadata и directory v1.
Повторный legitimate refresh повторно использует ещё достаточно свежий certificate,
но не reusable challenge. Grants additive в existing access.db; eligible existing
activation автоматически mapped без re-enrollment/operator action на телефоне.
Perpetual Friends activation остаётся perpetual grant, не выдуманный subscription;
finite grant expiry/revision/revocation поддерживаются отдельно.

### Trust and private-key decision

Online Family CA получает **domain-separated delegation от existing offline control
root**, pinned в `control-anchor.pub`. Это доказательно необходимый bridge между
normal Friends trust и ранее isolated Family issuer, не second independently
trusted root. Server-only delegated private issuer не root. Offline signer
`scripts/sign_restricted_issuer.py` отклоняет другой root. Настоящий root не читался,
подпись production manifest/генерация production secrets здесь не выполнялись.

Reuse accepted 5N.3 certificate URI/Family/role/revision и TLS1.3/ALPN
`family-connect-5n3-test-v1` без incompatible production format. Certificate public
key — **existing Device Identity Ed25519**, не новый client key. Private identity
остаётся в existing encrypted Friends identity vault. Native собирает PKCS8 и
accepted `familysession.Credentials` лишь в памяти; sensitive temporary arrays/JNI
copy wiped, private profile на диске не создаётся. Managed TLS copies подчиняются
existing runtime lifecycle, secure heap erasure всего TLS runtime не заявляется.
Existing control root и gateway private identity не переносятся на Android/API.

### BOOT-1, cache and readiness

`SeedManager` export callback вызывается **только после gateway READY**; bounded
atomic directory export переносится server-only sync NL→RU. Directory неизменён:
v1, family/times/seeds, required authenticated bootstrap `join_url`,≤8KiB/4 seeds/
1h. **Directory не имеет standalone signature**: transport authentication — existing
Friends HTTPS; subsequent restricted carrier — accepted Family mTLS. Signed CA
delegation и CRL — отдельные trust artifacts, не подпись directory.
Dedicated room creation остаётся lazy Room Broker после restricted recovery/Family
auth, unused descriptor60s/session default10min, без persistence/prewarm.

Android `RestrictedVault`: один AES-GCM/Keystore/AtomicFile в noBackupFilesDir,
public response + tombstone + persisted cooldown/floors, separate from unchanged
identity/normal provisioning vaults. Candidate native-validated целиком перед
atomic commit; malformed/expired/wrong-binding/stale/failed refresh не заменяет
valid старое состояние. Issued time, device revision, CRL, delegation sequence и
directory issuance floors переживают expiry/restart; conflicting equal-generation
directory rejected. Authorization rejection persistently disables usability;
old response не может resurrect denied state. Diagnostics — redacted status only.

Activation/normal profile acquisition/foreground resume и60s foreground maintenance
вызывают **local check**, не periodic network polling. Missing/invalid/≤300s material:
one worker,30s deadline, persisted300s attempt cooldown. No background alarms,
no CONNECT refresh wait with usable cache. Orchestrator actual `.friends` получает
validated production bundle через `beginReady`/`OpenProvisioned`, затем тот же
accepted bootstrap→Family→broker→dedicated full-device path. Diagnostic file path
не используется для production Friends.

### Security window is deliberately short

Directory≤1h не изменён. Deployment seed lifetime55min; CRL publisher15min, so
effective readiness≤15min, а не гарантированный час. Device certificate и response
также ограничены текущим CRL/grant/delegation/directory. Server sync every30s,
timeout15s: обычная revocation propagation около30–45s, при sync failure только до
expiry предыдущего signed CRL (≤15min), не instant offline revoke. Existing active
sessions подчиняются accepted expiry. Dead/rotating single seed может быть
недоступен раньше expiry cached directory. Prewarm непосредственно перед тестом;
hours-after-last-contact readiness **не решена**, это отдельный post-FIELD review
compromise exposure, seed rotation и revocation policy.

## Local verification and limits

- Python **95 passed**, включая opt-in real backend→Go compatibility: existing
  RNS identity proof → production response/certificate → native `DeliveryMaterial`
  → accepted Family Configuration + BOOT-1 parser. Device revision2/global peer
  floor1 проверены раздельно. Ephemeral unit-only keys в памяти, no live credentials.
- Server tests: active issuance/public binding, owner eligibility auto-mapping,
  revoked device/invite/grant/certificate, expired/wrong Family/revision/device,
  challenge replay/purpose/expiry, request/response/trust bounds, overload503,
  malformed seed, no client OAuth/private key/dedicated descriptor, idempotence,
  monotonic CRL and forced sync preserving existing gateway key, trailing PEM
  secret rejection, actual HTTP handler dispatch without network deployment.
- Go `test -race` wholedevice/bootstrap/familysession/roombroker and `go vet`
  same packages + cmd/bootstrap-broker **PASS**. Native rejects invalid trust,
  malformed/stale/expired/device/revision/CRL/directory/nonce/bounds; diagnostic
  string redacted; seed publish not before READY. Host broker build PASS.
- Friends JVM **193 passed**,0 failures/errors/skips; five new cache tests cover
  missing/import, simulated restart/expiry/cooldown, atomic storage contract/fault,
  failed refresh preservation, replay floors, denial/idempotence and redaction.
  These use storage/validator doubles; real Keystore/fs crash/process restart and
  Android-loaded JNI are **not** claimed tested by JVM. Native crypto separately
  tested above; physical combined validation remains pending authorization.
- Friends lint **0 errors / 37 existing warnings**. No unrelated lint fixes.
- Fresh arm64 restricted JNI compile/link **PASS**, Go1.26.0, NDK27.2.12479018,
  Xray `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, gVisor
  `v0.0.0-20260122175437-89a5d21be8f0`, patch SHA
  `2d0a556f73cdd7fb9f0d152edf564b126ba00cfdd526bb7c3325f5051b02339b`.
  Binary SHA `403a4625d3a1f8c57c5ba860400f060a256ef0ff10655681eb6bf02e98f4dd15`,
  ignored output `state-client-build/prov1-native-checked/`. Builder still labels
  this smoke manifest `diagnostic_only:true`; **not a signed/installed FIELD APK**.
  Host broker SHA `c2839cd21f2dd2f7171ea8c8d6596f415a16fe5b7fb84b22bb5715b609c47396`.

Reproducible targeted checks (use locked venv/toolchain; local paths are evidence):

```sh
FC_TEST_GO=/tmp/fc-boot1-tools/go/bin/go /tmp/fc-boot1-venv/bin/python -m pytest -q \
  tests/test_friends_restricted.py tests/test_friends_access.py \
  tests/test_restricted_android_contract.py tests/test_bootstrap_acceptance.py \
  tests/test_orchestrator_android_contract.py tests/test_orchestrator_native_provenance.py \
  tests/test_orchestrator_restricted_acceptance.py tests/test_restricted_acceptance.py
```

Cross-language test requires `FC_TEST_GO` explicitly; otherwise one skip, not the
95-pass acceptance above. Use `TMPDIR=state-client-build/prov1-tmp` as an **absolute**
path with this host's constrained /tmp; GOCACHE/GOPATH under existing locked tools.
Initial JNI attempts failed from /tmp user quota; moving scratch inside repo exposed
enclosing `.git` discovery causing extracted Xray patch not to apply. Builder now
sets `GIT_CEILING_DIRECTORIES` for extracted workspace. Fresh scratch build passed;
initial failures are not erased or presented as accepted artifacts.
Final logs: `/tmp/fc-prov1-python-final.log`, `/tmp/fc-prov1-jvm-accepted.log`,
`/tmp/fc-prov1-native-checked.log`. Go race/vet results recorded in task tool receipt.

## Deployment boundary and remaining physical gate

Deployment required: **yes**. Production deployment performed: **no**.
Exact files/units/hosts/migration/secrets/rollout/rollback in
[controlled deployment runbook](../../deploy/friends/restricted/README.md):

- RU `185.251.89.19:/opt/apps/family_connect`: existing Friends access API/venv,
  `family-connect-friends-access.service` drop-in, existing product HTTPS ingress
  new locations, private delegated issuer/config, new restricted-sync service/timer.
- NL `186.246.45.246:/opt/apps/family_connect`: new dedicated account and
  `family-connect-restricted-bootstrap.service`, fresh broker, private gateway
  profile, forced-command signed-CRL/READY-directory sync, loopback18444 only.
- Same access.db additive tables/online backup; preserve existing activation and
  revocations. `FC_FRIENDS_RESTRICTED_DIR`, offline-signed public issuer delegation,
  delegated server issuer key, existing gateway identity/certificate, owner-only
  admission, pinned dedicated sync key/known_hosts, server-only
  `YANDEX_TELEMOST_OAUTH_TOKEN`. No actual values supplied/generated here.
- Expected short API restart (seconds, not measured), ingress reload, no planned
  AWG/TCP downtime/restart. Verify actual service layout/dependencies before rollout.
- Rollback disable new API/drop-in/sync/seed, restore saved API/ingress artifacts;
  preserve DB tables/revocation/replay floors and private identities. Never roll an
  old full DB over new revocations; Android forward corrective update only.

No physical READY/restart or local restricted rehearsal run in this continuation.
Browser/DNS/fail-closed prior accepted isolated report is **not** new production
cache acceptance. Physical last-observed Friends state still BLOCKED, field52
readiness-only/code52 installed previously; public beta51/code51, Linux0.2.11,
Windows0.2.15 unchanged. No new APK, version bump, signing or public artifact.
After separate authorization: controlled owner canary → private same-signature
update in place → normal prewarm READY → process restart READY → local restricted
rehearsal with actual identity/cache/browser/DNS/fail-closed → only then final
shareable FIELD APK. No uninstall/pm clear/diagnostic identity/traffic forwarding.

Push: **no**. Krasnodar FIELD-1 started: **no**. Stop at deployment boundary.

---

## Historical pre-implementation audit — preserved from a88b104

Следующие разделы описывают состояние **до clarification/runtime implementation**;
их BLOCKED/no-tests/no-build утверждения не являются текущим статусом.

## Результат

**5N-PROV-1 = BLOCKED. Runtime integration не реализована.** Это не
`IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED`: до deploy gate не дошли.
Причина остановки — буквальное противоречие между reuse BOOT-1 v1 и запретом
live Telemost room URLs в directory. Ни новый wire protocol, ни ослабление запрета
не выбраны за пользователя. Ниже точный gap **до изменения runtime**. Отсутствие
реализованного production issuer само по себе не объявляется непреодолимым blocker.

Starting clean HEAD: `3d9fd7ca3d020618ffb7c8f95068094450483ed4`.
Local origin/main: `26447902137735ac7633f92ba6673395bae078fa`.
`9c82152` и `3d9fd7c` сохранены, история не переписана.
Read-only GitHub Actions: последний возвращённый run `36788357526`,
`Linux control preview`, head `2644790`, completed/failure30.09.2026,
updated22:56:45Z. Это не deployment receipt и не проверка этой задачи.
Production hosts/private DB/ключи не читались; deployed HEAD заново не проверен.

## Противоречие BOOT-1

Source: [directory.go](../../carrier/bootstrap/directory.go),
[seed.go](../../carrier/bootstrap/seed.go),
[accepted report](2026-09-30-webrtc-5n-boot1-bootstrap.ru.md).

- `Directory` v1: version, family, issued_at, expires_at, seeds. Каждый `Seed`
  содержит transport, **join_url**, gateway. Parser требует1–4 seeds с
  `roombroker.ValidJoinURL`; пустой URL или opaque seed ID вместо URL не принимается.
- `SeedManager.Run` **создаёт реальную bootstrap room на сервере**, подключает
  gateway, ждёт READY и публикует `room.JoinURL`. Offline client должен иметь этот
  rendezvous заранее. Создать и узнать первый seed только после потери control
  без другого rendezvous принятый протокол не позволяет.
- Dedicated room — другая комната: Room Broker создаёт её после Family admission
  при recovery; её descriptor не входит в directory. Запрет **dedicated** URLs
  при prewarm совместим с v1; запрет **всех live** room URLs — нет.
- У v1 **нет standalone signature/signing envelope**. Accepted authentication —
  existing Family TLS1.3/mTLS, gateway pin, затем protected cache.
  `SeedManager.Handler` обслуживает уже admitted mTLS-клиента. Нельзя назвать
  эти bytes отдельно подписанным directory. Требование может означать
  authenticated delivery, но это отличается от persistently verifiable signature.

Минимальное уточнение: допускается ли authenticated **bootstrap seed join URL**
в v1, если dedicated URLs исключены, а seed заранее создаёт только сервер?
Достаточна ли accepted authenticated delivery, либо необходима отдельная подпись
response через existing trust? До уточнения условия6/11 и reuse v1 одновременно
невыполнимы буквально. Нельзя молча заменить v1 или доверять downloaded CA по TOFU.

## Точный production gap

1. **Friends API — не `/v2/provisioning`.** `FriendsAccessAndroid` использует
   `/friends/challenge`, `/friends/activate`, `/friends/configuration/{ru,nl}`
   через RU HTTPS ingress. Handler — `deploy/friends/access-api.py`, backend —
   `control/friends/access.py`. В routes/purposes нет restricted-readiness.
2. `Access` связывает RNS public identity и независимый WG public key; purpose-bound
   single-use challenge живёт100s, outstanding≤8/device. `complete` проверяет proof,
   binding, purpose, expiry, used и device revoke. `status` дополнительно учитывает
   revoke invitation. Будущая выдача обязана проверять device и grant совместно
   в одной transactional authorization boundary, не только вызвать `complete`.
3. Friends grant бессрочен после activation. Таблицы invites/devices/challenges не
   содержат Family/entitlement revision/certificate serial/CRL state. Нельзя
   объявить эти проверки реализованными или подставить произвольную Family.
4. `control/product/store.py` и `provisioning.py` — отдельный ProductStore контур,
   не доказательство enrollment actual Friends device в этой DB. Миграция туда
   и создание второй identity не выполнялись.
5. Normal response: device/country/address/tcp_id и offline-signed credential-free
   catalog. Android `ControlTrust` pin — offline update/control root;
   `scripts/sign_friends_catalog.py` использует отдельный domain. Это **не online
   Family issuer**. Offline secret нельзя переносить в API для refresh. Будущая
   issuer/delegation chain должна явно связываться с existing root.
6. Accepted issuer `pilot/telemost_family_fixture.py` создаёт disposable authority,
   identities и temporary ProductStore. Он намеренно не принимает production
   DB/identity/key и не подходит для credentials владельца. Source audit не
   устанавливает отсутствие каких-либо ключей на live hosts.
7. `wholedevice.Refresh` сначала читает existing Family profile и создаёт mTLS
   client, затем получает directory. Первый provisioning обычного Friends этим
   не решён. Readiness inspection read-only, field52 cache не создаёт.

## Ключи и Android import

Accepted `familysession.Credentials`: certificate, private_key, authority,
revocations, family, gateway, minimum_revision, minimum_crl; максимум48KiB.
TLS использует **existing Ed25519 signing key Device Identity**, не WG key.
URI SAN связывает full public identity; OU — protocol/Family/role/revision.
Runtime проверяет TLS1.3/chain/CRL/floors/expiry/gateway pin. Fixture сохраняет
plaintext PKCS8 в profile0600 — это не accepted encrypted production key delivery.

Предпочтительная модель для реализации: signing seed остаётся в existing
`FriendsIdentityVault` (Keystore AES-GCM/AtomicFile/noBackup); сервер получает
только authenticated public identity, возвращает certificate/public trust material.
TLS key representation строится локально из existing identity, без новой identity
или private-key download. Эта интеграция **ещё не реализована**.

Normal `FriendsConfigurationVault` уже encrypted/AtomicFile, но ограничен16KiB,
не48KiB profile+8KiB directory. Две независимые записи не являются atomic pair.
Нужны validated encrypted generation/bundle, одна commit point, persisted replay
floors и native import boundary. Не писать signing seed в SharedPreferences или
новый plaintext file. Readiness/Orchestrator должны читать одну committed generation.
Malformed/stale/failed refresh сохраняет valid generation; definitive authenticated
revocation запрещает usability. Timeout/503 не равен revoke; мгновенная offline
revocation не обещается. Runtime/storage changes в этом checkpoint отсутствуют.

## TTL и prewarm

Ничего не продлено: directory≤1h/8KiB/4 seeds. Реальная usability дополнительно
ограничена живым seed/gateway и certificate/CRL expiry. Broker defaults:
unused descriptor60s, session lifetime10min; это разные сроки.
Persistence не гарантирует recovery спустя часы после последнего control contact.
Будущий FIELD prewarm непосредственно перед тестом допустим, но не закрывает
product offline-window limitation. Продление требует анализа compromise/revocation,
seed rotation/lifetime, signing, stale directory и refresh cadence.

Будущая bounded policy: existing normal-control lifecycle, single-flight,
near-expiry threshold/cooldown, отсутствие CONNECT wait при valid cache и
aggressive polling. Числа политики/tests пока не реализованы и не заявлены как PASS.

## Проверки и физическое evidence

Новые server/Android tests требований11–12 **не добавлены и не выполнены**:
operation/import отсутствуют. Existing directory/cache/issuer tests прочитаны
для проверки контракта, не представлены как новый PASS.
`python3 scripts/check_public_docs.py --all`:408 files/2449 links/0 errors;
`git diff --check` и `git diff --cached --check`: PASS.
`python3 scripts/check_public_sources.py`:1534 index entries/0 blocked files,
staged docs-only changes; это не runtime/security acceptance.

[Предыдущий physical BLOCKED](2026-10-01-field1-device-readiness.ru.md) сохранён:
Identity PRESENT, normal PRESENT_VALID, restricted/BOOT-1 ABSENT, после restart
то же. Здесь телефон не трогали; prewarm/restart/rehearsal/browser/DNS/fail-closed
не запускались. Новых APK/JNI/build/install/signing/publication нет.
По последнему accepted report: public Android beta51/code51, private installed
readiness-only field52/code52, Linux0.2.11, Windows0.2.15. Public artifacts и
invitation pages заново не проверялись. Field52 не final FIELD artifact.

## Deployment boundary

Live deployment впоследствии нужен: **да**, но deployable implementation и точного
deployment plan сейчас нет. Сначала clarification, isolated implementation/tests,
затем отдельный `IMPLEMENTED / DEPLOYMENT AUTHORIZATION REQUIRED` с проверенными
artifacts/units/migration/rollback. Текущий BLOCKED не запрашивает deploy approval.

Минимальная ожидаемая зона, **планирование, не команды к исполнению**:

- RU `185.251.89.19:/opt/apps/family_connect`: Friends handler/backend,
  `family-connect-friends-access.service`, ingress `family-connect-product-https`.
  Новая capability сначала только owner device, normal semantics без изменений.
- NL `186.246.45.246:/opt/apps/family_connect`: отдельный ещё не выбранный production
  seed/broker unit, Family admission/CRL synchronization. Не diagnostic listener.
- Secrets/config: accepted anchored issuer/delegation, gateway identity, current
  signed CRL и grant revisions; server-only Telemost OAuth. Offline root остаётся
  локально. Имена env/mounts пока не определены, новые секреты не создавались.
- Migration: определить durable Family/grant/revision/certificate mapping existing
  Friends, backup/backward compatibility. Нельзя обещать «migration не нужна».
- Downtime не измерен, zero downtime не обещается; API restart может кратко
  затронуть control, существующие AWG/TCP units перезапускать не требуется по цели.
- Future rollback: disable новую выдачу, restore сохранённые API/config artifacts
  без отката revocation/replay floors; сохранить DB/keys; stop только новый unit.
  Android только same-signature corrective update, без uninstall/pm clear/downgrade.
  Текущий docs-only checkpoint runtime rollback не требует.

Production deployment: **no**. Diagnostic credentials для продукта: **no**.
Push: **no**. Krasnodar FIELD-1 started: **no**. STOP до уточнения контракта.
