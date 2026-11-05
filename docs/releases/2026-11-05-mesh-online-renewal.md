# Online MESH renewal qualification / 5 November 2026

## Continuation from354513d — G1 implementation checkpoint

HEAD matched354513dd9f8a9558b800963664eb9ea053e457ab; no subsequent source delta. All
pre-existing dirty documents and historical untracked files are preserved. No production
access or changes. This checkpoint does not accept G1–G4 or enable the production constructor.

`recover_online_emergency` reuses the existing controller lock and node owner/lock,
quiescence barrier, issuer custody, validator, ProfileStore CAS, grant planning/apply,
directory publication, reconciliation, service resume intents and archive/cleanup ledger.
There is no second signer, writer, timer or authorization database. A durable continuation
ID binds the original COMMIT/plan/prepared receipts/fence; the original decision is never
changed to ABORT. Node handoff archives the original bytes before replacing staged work,
preserves services-before, and moves the owner to a higher fenced emergency epoch.
Stale online publish/fence/abort and ordinary rollback cannot mutate that owner.

States: ONLINE_EMERGENCY_REQUIRED → EMERGENCY_HANDOFF → EMERGENCY_APPROVAL_REQUIRED →
EMERGENCY_AUTHORIZED → EMERGENCY_PREPARED/PUBLISHING → EMERGENCY_COMMIT_DECIDED → existing
resume/cleanup → EMERGENCY_RECOVERED. Missing approval yields a durable state-bound request;
invalid/denied/expired approval leaves all readers stopped. Leaf/CRL emergency uses the
existing operator outage authorization, not a fabricated root signature. Changed pinned
policy/authority is not automatically authorized; offline authority approval remains separate.

The emergency successor is signed from the committed authenticated material with the
current registry. It includes current revocations and advances to committed CRL floor+1,
even if one participant never published the earlier floor. Skipping that unpublished floor
requires the locally retained exact parent plan/prepared receipt proof; ordinary sequence
rules are unchanged. No intermediate forbidden profile is published and no DB is restored.
After both gateways reconcile and publish current directories, RU publishes a matching
delivery marker before resuming HTTP. Intentional quiescence closes old sessions: this is
availability recovery, not TCP continuity. New runtime/TLS acceptance is still a gate.

Checks: `test_online_emergency.py`20 PASS; a containing selection with online renewal,
multi-gateway and activated maintenance192 PASS/1 optional SKIP. Do not add these totals.
The selection covers both pre-node-decision and post-NL-publication revoke, missing/invalid/
expired/denied outage approval, six controller boundaries, nine node handoff response-loss
boundaries, stale owners, immutable parent COMMIT/floor advance, revoked readiness rejection
and surviving identity readiness. These are in-process Python handlers, NOT G2 process death.
Logs: ignored `state-client-build/mesh-online-gates-20261105/python-g1-second.log`.
An initial invocation used a nonexistent test filename (collection NOT_RUN); it is retained
as `python-g1-first.log`, not counted as a passing execution.

G1 runtime handoff, G2 real RPC/process faults, G3 disposable Android HTTP/cache and
G4 final online API/runtime package remain qualification work. Existing accepted maintenance
API archive, old stand provenance and bootstrap success below are not silently replaced.

### Follow-up: current registry and start-intent reconciliation

The stopped, not-yet-prepared continuation can refresh its expected registry snapshot;
the old outage approval then fails binding and the same continuation emits a fresh request.
This permits a second revoke while awaiting approval without manual DB/marker edits.
Archive directory links are fsynced before publishing the handoff owner. An unknown start
response does not manufacture another stop/start: the explicit repeat rechecks reconciliation
and the existing start-intent against service state. Deterministic authorization/policy
failures still fence readers; unavailable/corrupt transport receipts never count as commit
success. There is no background recovery loop. The existing ambiguous-start guard remains.

25 focused tests PASS: the original20 plus stale-approval-after-revoke, two real-contract
SSH budget boundaries, lost start response using the existing SystemdBarrier intent logic
(service adapter simulated), and expired online successor followed by a fresh emergency
signature. Window evidence is a model test:120s ×8 +435s =1395s plus supplied scheduling
lateness; equality/insufficient headroom rejects before journal/owner writes. It is NOT an
Android HTTP/cache cooldown experiment or independent-process fault acceptance.

Exact5ef0193252f00000e87da65a5deebadc3688eb19 evidence:
- Separate unbound maintenance source capsule: SHA256
  `2c04d2815edafe69aa8adb33fad0d097e29d01150e007448814541dfb88b8b91`;
  source inventory`bac40c99de0e6d9fca73a99c189e5d085661a5cb90681464f8ebfacf4f0f1d33`.
  This is NOT the G4 online runtime package. Accepted API source/digest remain unchanged.
- Root/network-none container:292 PASS, zero skips, scoped online/handoff/canonical-profile/
  route/package/expired-recovery/fenced-rollback tests (`root-5ef0193.log`).
- Fresh frozen-source sync artifact and synthetic ProductStore fixtures: mandatory
  bootstrap + bootstrap command `-race -count=3` PASS, zero skips/failures
  (`bootstrap-5ef0193.jsonl`).350 parent/subtest/package PASS events are not350 independent tests.
- Family session + broker `-race -count=1` PASS (`native-5ef0193.jsonl`),27 nested skip events:
  canonical root/reader boundaries, four opt-in DNS checks, process-paced helper and long
  online stand.211 PASS events are not an additive suite total. The old999s stand is retained,
  not rerun or relabelled as this candidate's full-path acceptance.
- Android JVM/API27/API35 delivery checks: NOT_RUN in this continuation; no Android changes.
  Previous accepted ownership checks do not cover G3 actual HTTP/cache delivery.

Raw evidence remains ignored under`state-client-build/mesh-online-gates-20261105`.
One sync packaging CLI invocation supplied an unsupported `--source` flag (FAIL invocation);
the corrected frozen-source builder API and smoke completed before bootstrap. No gate was
disabled. No production access, deployment, APK/catalog change or private state is committed.

### Final source checkpoint for this continuation — not G1–G4 acceptance

Source`b1d17d3be8f347c1d991528ecebbe72c962ef21c` is committed/pushed after5ef0193;
origin/main was checked against the pushed SHA. The final targeted root/network-none
selection is118 PASS/0 SKIP:25 handoff/window/start-intent tests, canonical profile/package
construction, deterministic packaging and entrypoint smoke. It overlaps the earlier292;
do not sum them. `root-b1d17d3.log` is the exact receipt. Native/HTTP sync sources are
byte-identical to5ef0193 (`git diff` of carrier and runtime inventory is empty), so the
fresh artifact-enabled bootstrap/native results above retain that exact provenance rather
than being renamed as a new execution. No full-path999s rerun, Android JVM or API27/API35
HTTP/cache acceptance was performed for this source checkpoint.

Final separate **maintenance source capsule, not online runtime candidate**:
- Source SHA`b1d17d3be8f347c1d991528ecebbe72c962ef21c`.
- Archive SHA256`04da90a06e141685573e983f8affe98cbb24141b11fe184cf66ef4b4cc155548`.
- Source inventory SHA256`d11ae8d634fcb7659bb8d923e22442eb5aaad857a5a3df8f162563e3c17937ae`.
- API wrapper SHA256`94ecc55e7282fa8d1a49bb8291065b9b3acf8b8985179a1579313c78616eb718`.
- Manifest SHA256`8d67351fd966043edc11351b3f562bc0244491559001fa1a9eb0e452e69e2fc3`.
The old accepted archive is not overwritten; these are distinct ignored local files.

| Requested gate | Outcome | Exact scope and remaining transition |
| --- | --- | --- |
| G1 full emergency runtime acceptance | NOT_RUN | Implementation and25 focused tests PASS, including protected SystemdBarrier start-intent reconciliation with simulated service commands. No claim of actual gateway restart/TLS admission acceptance on the final package. |
| G2 independent-process distributed failures | NOT_RUN | Existing in-process fault matrix remains evidence only. No claim that multiple Python objects or fault exceptions are remote process death. |
| G3 Android HTTP/cache delivery | NOT_RUN | SSH120 budget1395s+lateness and pre-write rejection tested; Android300s cooldown/HTTP/Keystore/owner integration on API27/API35 still needs the isolated endpoint. |
| G4 qualified online package | FAIL | Current separate source capsule's ordinary CLI rejects `--mode online` with exit2; `node.construct` still has no online reader/capability configuration and dispatch remains `ONLINE_QUALIFICATION_ONLY`. |

G4 reproduction (no configuration read or mutation): unpack the separate source capsule;
run its `renewal/runtime_controller.py` using the documented Python `-E -s -B` invocation,
`--config <disposable-path> --mode online`. The parser accepts only evaluate/scheduled/
operator/recover/expired-request/expired-apply/expired-resume. Evidence:
`online-entrypoint-contract.log`. An earlier `-I` invocation wrongly excluded the script
module directory and failed import; retained separately, not used as the gate diagnosis.

Required remaining implementation: a distinct pinned current readiness/API/runtime package
and explicit opt-in controller/node entrypoints with capability and actual-reader checks;
then its own real RPC/process, disposable Android HTTP/cache and both-node full-path
qualification. Do not simply enable the in-process qualification flag or replace the old
API archive. The lack of production authorization is NOT the reason these isolated gates
remain unfinished. There is no assertion that the requested stage is complete.

Automatically recoverable within the qualified Python scope: stopped handoff/archive and
lost replies, repeated authorization request, stale approval after another revoke, same
emergency plan/floor publication and already-executed service start. Explicit outage
approval remains required; pinned policy/authority changes require their separate trusted
authorization, not continuity priority. Normal compatible online renewal retains earlier
TLS/mux/TCP evidence; emergency quiescence deliberately closes those sessions and requires
new permitted connections. No live user connection was touched by this work.

Release/live/field gates stay queued, not started: exact immutable client+both-gateway+
publisher artifacts, separately authorized controlled delivery, actual scheduled renewal
on both NL, paired-DNS/WebSocket, weak-link/loss/screen-off/mobile allowlists; only then
controlled paid beta on an accepted baseline with roster/opt-in/terms/access-revocation/
monitoring/stop ownership. No canary replay, payments, enrollment or arbitrary expansion.

## Prior accepted evidence (not current instructions)

**Latest outcome,12:55UTC: positive isolated online stand PASS; requested stage INCOMPLETE.**
Source checkpointa8e1db9 plus narrow negative-test/strict-JSON delta2cbd304 is pushed.
The mandatory bootstrap gate now passes including its isolated Python artifact contract.
Emergency reconciliation/handoff, complete distributed failure/cache acceptance and
online runtime packaging remain source gates. The qualification RPC is disabled by the
production constructor. Earlier checkpoint paragraphs below are historical progress,
not additional active NEXTs or permission to activate anything.

## Entry and boundary

Entry HEAD is exactly `15ef592bf92c143839130da7884328e4a7d9918f`. The four pre-existing
dirty documents and six untracked historical files are preserved. This is the existing
Android MESH incident, source/isolated qualification only: no production access, installed
APK change, catalog, timer, paid/cohort/admission/boot change or activation permission.
Installed/opt-in118 and updater113 remain unchanged. Paired-DNS/WebSocket remain OPEN.

## Dependency map and selected contract (implementation in progress)

- RU's existing issuer signs leaf/CRL materials using the existing local custody key.
  ProductionController owns the operation under DurableOperation.lock; ProductionNode
  uses the existing owner, staging/archive ledger, membership and canonical ProfileStore.
- The controller transaction.json/plan.json carries the durable decision. Online prepare
  must not promote files before this decision; normal quiesced/emergency paths remain.
- NL gateway profiles feed Family TLS, credential exchange, lease and broker monitors.
  Runtime receipts must come from the actual reader, bound to its process instance and
  exact profile digest, not merely a successful rename. Unknown runtime contract rejects.
- RU CRL/issuers and per-node directory feed authenticated readiness. A delivery gate
  must hide the committed successor until both corresponding runtime readers acknowledge.
  Directories retain the running rooms; no restart/new seed is evidence of continuity.
- Readiness's existing certificate retention (expires > now+300) must be reconciled with
  the Android300s persisted cooldown,30s owner polling,30s request and bounded exchange.
  Otherwise an early CRL-only delivery may produce a refused, non-retried candidate.
- Recovery follows the same durable decision/fenced owner, not the newest local file.
  Pre-decision abort requires unchanged live state; post-decision may only roll forward.

Online controller/node/publication/native qualification is NOT yet complete at this
checkpoint. No production route is enabled by committing this source.

## Bootstrap diagnostic contract

The inherited six assertions are a phase-classification regression: OpenServer sent
profile/TLS-open failures to the callback for an authenticated broker exchange, although
no authenticated exchange or provider admission occurred. The preserved contract requires
that callback only after Family authentication. Admission failures are not successful
exchanges, but their errors must still be observable.

OpenServerObserved separates the admission observer from the authenticated exchange
observer. The command records structured bootstrap_admission_rejected with stage/reason;
the existing exchange event remains reserved for authenticated protocol failures. The
legacy OpenServer contract and all six negative assertions are unchanged. Added negative
checks require exactly one family_open admission report and zero exchange reports, no
descriptor/provider call/authentication; valid control has no rejection report.

Raw local evidence: `state-client-build/mesh-online-renewal-20261105/`.
Baseline15ef592 is rerun from an isolated source archive; updated bootstrap `-race -count=3`
passes. An initial broader run retains a transient existing authenticated-busy wire-reason
failure; it is not erased or attributed to this fix without evidence. No tests are disabled.

## Remaining gates

Finish online transaction, runtime/readiness integration, both-node continuity and fault
matrix before claiming this stage complete. Then stop. Full release CI, new immutable
artifacts, equal gateway builds, scheduled live renewal and physical/mobile allowlist
acceptance remain separate, unexecuted gates. No independent timer or writer is authorized.

## Implementation checkpoint (not stage acceptance)

The explicit `MESH_SAME_HOLDER_ONLINE_V1` path reuses the controller/node locks,
owner journal, issuer, membership, staged file CAS, ProfileStore, SQLite sequence and
existing archive ledger. It does not change the ordinary quiesced transaction. Node RPC
requires an explicit in-process qualification flag; packaged production construction
does not set it. There is no new timer, production online CLI activation or second signer.

Window calculation after initial read: eight bounded RPC rounds plus explicit scheduling
lateness, Android cooldown300s, owner polling30s, readiness request30s, maximum ordinary
lease control attempts55s, credential exchange15s and skew5s. Thus local1s-RPC/0s-schedule
qualification requires443s; configured SSH120s plus schedule requires1395s+schedule.
Neither production validity nor timeouts are increased. Unknown timing rejects.
Both gateway bindings, authority, keys, grants, policy revisions, CRL floors and current
material validity are checked. Existing client certificate records also need headroom.

States: ONLINE_ACQUIRING/FENCING → PREPARED/STAGED → durable COMMIT_DECIDED →
per-node DECIDED/PUBLISHED → RU delivery-ready → CLEANING → COMMITTED. Before the
decision, explicit ABORT requires unchanged credential files and does not restore DB rows.
After COMMIT, retry uses the same plan/digests and higher fencing epoch, never a new CRL
or rollback. Lost RPC results reconcile against node state; completed cleanup is archived.

During NL-only publication, existing peers retain their authenticated generations and RU
still gives predecessor readiness. Runtime receipts use the same native credential loader,
cryptographic successor validation and process-instance nonce. RU only exposes the new
CRL/readiness generation after both exact profile hashes acknowledge. It copies validated
current directories without creating seed rooms; no distributed instantaneous atomicity is
claimed. Readiness uses a fixed committed issuance target, not a moving target per refresh.
Local publication is not a native session commit; only authenticated exchange advances it.

45 focused tests cover17 controller crash boundaries,17 node crash/lost-response points,
four durable abort positions, stale epochs, maintenance contention, client headroom,
duplicate delivery/commands and two revoke positions. Positive/unit readers are doubles;
those tests alone are NOT native continuity proof. Existing affected Python/package scope
is214 PASS/5 optional skips. A real two-node stand has reached two authenticated native
generations on both nodes; its complete cross-bound outcome/provenance is pending.

Known blocking gaps at this checkpoint: post-decision emergency detection safely stops
readers and preserves the COMMIT decision, but machine handoff/reconciliation from that
fenced state is unfinished; no manual marker deletion is prescribed. Complete malformed
receipt, expiry, old-peer/new-connection and cache-delay acceptance is also outstanding.
The accepted maintenance API archive is intentionally unchanged; it must not be silently
substituted with the newer readiness implementation. Final online runtime packaging and
root qualification remain separate required gates. This checkpoint is NOT release-ready.

## Additional negative and bootstrap evidence

Source checkpoint `a8e1db900105219b22abae21accd2c2b6e2f5b30` is pushed and remote SHA
verified. The real native stand is repeated from an immutable export of this commit.
The earlier development stand passes999.28s but is not substituted for that frozen-source
acceptance. Isolated root/package scope on the checkpoint passes219 tests. The first root
attempt incorrectly put root-owned fixtures below a user-owned bind mount (UNSAFE_PARENT)
and omitted Git's explicit read-only repository trust; both harness errors are retained.
The repeat uses root-owned tmpfs, without relaxing ProfileStore ownership checks.

Focused online negatives now pass55 tests: add unavailable participant/precommit abort,
rollforward after predecessor expiry versus successor-expiry fencing, corrupt durable
decision, and six readiness-marker failures with an unconsumed proof challenge. Strict
existing JSON parsing rejects duplicate marker fields; no new runtime package dependency.

The six inherited cases (unknown issuer, wrong Family, revoked device, wrong gateway,
stale CRL floor, stale revision) all failed the same baseline `auth_test.go:87` assertion:
expected zero authenticated-exchange reports before TLS admission, actual nonzero reports.
Baseline15ef592 reproduces each case five times. The new observer preserves separate
admission diagnostics and all denial assertions.

The expanded bootstrap artifact gate also reproduces an independent busy-reason assertion:
an ERROR frame gives a direct public Code, while a peer closing before HELLO gives the same
public Code wrapped by the existing startupdiag.Preserve with its receive cause. Comparing
Go error object identity incorrectly calls the latter a changed wire reason. The check now
requires both errors.Is and exact startupdiag.Legacy category; a new deterministic test
also requires the original receive cause and unchanged public Error text, and contrasts
the actual ERROR-frame branch. No production error is suppressed or authorization changed.
Ten race repetitions of busy, both HELLO outcomes and negative admission boundary PASS.
The complete artifact-enabled bootstrap repeat is still required after this assertion fix.

## Frozen-source stand result

`a8e1db900105219b22abae21accd2c2b6e2f5b30` exported with `git archive`, mounted read-only;
one network-isolated Docker container contains three logical node roots, actual
ProductionController/ProductionNode handlers, real authenticated RestrictedReadiness
proofs, and two separate Family TLS/mux/broker runtimes. This is not a physical three-host
or SSH-failure qualification. A local packet carrier and local echo/DNS/HTTPS origins
replace Telemost/Internet. Synthetic signing/device keys never leave private test state.
Server material is written by the real transaction; client material comes from readiness
and wholedevice.DeliveryMaterial, not a manually supplied SessionMaintenance profile.

The fixture shortens synthetic leaf/CRL validity only: initial500s, successors1000s;
production4h validity is untouched. The real300s Android cooldown is included in the443s
window, not waited by an actual Android process. The native driver validates readiness
and offers each distinct profile through the existing maintenance owner. This does not
claim Android HTTP/cache timing or APK118 continuity acceptance.

All times below are UTC on5 November2026:

| Observation | NL/AMS1 fixture | NL2/AMS2 fixture |
|---|---|---|
| Original security/leaf/CRL bound |12:47:25|12:47:25|
| Original lease bound |12:39:17.030930941|12:39:17.031156091|
| Generation1 native confirmation |12:39:09.588154962|12:39:09.726322421|
| Generation1 security/leaf/CRL bound |12:55:42|12:55:42|
| Generation2 native confirmation |12:47:29.328411896|12:47:29.390912114|
| Generation2 security/leaf/CRL bound |13:04:02|13:04:02|
| Final crossing observation |12:55:43.125387420|12:55:43.127724158|
| Final lease bound |12:55:48.057772975|12:55:48.057092799|

CRL floors1→2→3 and exact common CRL bytes agree on both gateways. Native authorization
generation is checked on both endpoints for each exchange. Original client/server mux
objects and exactly one accepted original TCP are asserted during every traffic iteration;
the same stream survives both crossings with883 verified payloads /18,433 useful bytes
in EACH direction per node. The final explicit fresh TCP makes the final accept count2;
this is a deliberate new-flow check, not replacement of the original connection.
DNS and certificate-verified HTTPS succeed after both old bounds. No mock deadline setter,
service restart or new seed is counted as continuity. Entire stand:999.12s PASS.

Receipt persistence timestamps provide upper bounds on the actual runtime-read observation,
not a claim of distributed instantaneous commit:

| Generation | NL receipt | NL2 receipt | RU delivery-ready receipt | Both native confirmations by |
|---|---|---|---|---|
|1|12:39:07.869196|12:39:07.870507|12:39:08.084377|12:39:09.726323|
|2|12:47:27.635243|12:47:27.637729|12:47:27.785584|12:47:29.390912|

Thus observed RU-ready→both validated native confirmations is under1.643s each round.
The readiness-read and exchange are not separately timestamped; no invented split latency
is reported. Receipt times are retained filesystem timestamps, while native times are
explicit harness observations. At the second issuance the predecessor has495s remaining,
above the443s local budget. A transport with the real120s SSH timeout requires a different,
larger eligibility window; the local result does not qualify deployed scheduling.

Runtime process-instance receipts remain unchanged across both generations:
- NL: `c931f9a6929dc8c82dd277c623f4cf8b40d91771d115c1ef72abaf46e03f0d96`.
- NL2: `fa4f8154f4a37bddbc29f0baa0ab94e9da6136ae16742ace28a7a67ac1260918`.

| Gateway | Generation1 profile SHA256 | Generation2 profile SHA256 |
|---|---|---|
|NL|`cd9983e627d431e1b1c03d9bce53aceb81e5276058a5316b3748780515c2ccde`|`4c48d25db1f0a94a1f4b3d3218c244ad71dfe6c4f75644d0451bef0fdeab4bf6`|
|NL2|`2415d0fbb5cd131b445c2bb9ac26daa49aced789c9db6df7c68205a2803e2557`|`3a2cf95e91930838e79216e4500f185b48f9811f53947b60a41e10f935996427`|

## Final check scope and provenance

- Python scoped controller/node/readiness/multi-gateway/package selection on2cbd304:
  **229 PASS,5 optional harness skips**. Focused online subset: **55 PASS**.
- Isolated root canonical custody, profile routes, archive/recovery, packaging and online
  selection ona8e1db9: **219 PASS**, including existing immutable accepted API checks.
- Go1.26.1 `-race -count=1` on four affected packages (familysession, roombroker, bootstrap,
  cmd/bootstrap-broker) ona8e1db9 with fresh ProductStore fixtures: all packages PASS;
  28 nested optional/root/DNS/stand skip events are not concealed.
- Root roombroker race binary:163 parent/nested PASS events,5 skips (four explicit DNS
  subtests and separate long stand). The long stand separately runs actual isolated DNS.
  An earlier broad run with DNS enabled for every test hits an existing fixture collision:
  cross-session proof test creates two independent port53 listeners. That failure is
  retained, not erased or reported as production DNS failure; the proof test passes in
  the normal root suite. No unrelated test is removed or desktop failure repaired.
- Final mandatory bootstrap and command `-race -count=3` on2cbd304 with real disposable
  identity fixtures AND source-built isolated sync Python artifact: **PASS, zero skips**,
  350 parent/nested/package PASS events. Earlier failure logs remain in local evidence.
- Android/JVM/API27/API35 are not rerun: this delta does not change Android/native owner
  integration; those accepted previous-stage checks are not relabelled as new acceptance.

Source and artefact distinctions:

| Item | Provenance/SHA256 |
|---|---|
|Online stand/source checkpoint|`a8e1db900105219b22abae21accd2c2b6e2f5b30`|
|Strict marker parsing/negative bootstrap assertion delta|`2cbd304684e23e855df75a8d9e5666e53a64805a`|
|Isolated root image|`sha256:ca61f885607656ea89f5726853761c4c533d050faf26b71853575c24ca1ed123`|
|Unbound maintenance capsule|`beb68dd770285d7e2a2315111c8ab6075af0834e0be1dfd692941acdeab7a23c`|
|Capsule source-files inventory|`d6bbe45081e7652e76314f97589708028d9129d9ca795a22258e8f679baa3a82`|
|Capsule manifest|`6bb965853b5e75dd49ac7d61891435d31cde4cb66910dcda8da98357b7303e5e`|
|Race native stand test binary|`325d9263acbdf7e787114089be71fae520f786cf762eb0e11d8ef3d906c8fb23`|
|Readiness validation helper|`2ef72dfe1c5ae57eba69cbc013c72a2f75a4fb963284159f39695e26bbca323a`|
|Source-built sync Python artifact|`0227d22ccb5be6b1808e560c35a4dabd3da923dc9ed8aaa830374792968f11ff`|

Capsule keeps accepted API sourceedca544 unchanged; it is NOT an online runtime package.
No archive, native test binary, synthetic identity or raw fixture state is committed or
distributed. Private evidence stays under `state-client-build/mesh-online-renewal-20261105/`;
the sanitized `stand-a8e1db9-public-summary.json` contains no private material or traffic.

## Unfinished source gates and later release gates

The requested stage is deliberately **not marked complete**:
1. Post-COMMIT revoke/emergency safely reaches ONLINE_EMERGENCY_REQUIRED with readers
   fenced and original decision retained, but it lacks the machine handoff to the existing
   quiesced emergency transaction. Do not delete its marker or edit profiles/DB to resume.
2. Complete receipt-corruption/unknown-participant/process-death reconciliation, including
   actual independent controller/node processes and concurrent directory publisher custody.
   Logical crash/lost-response tests do not prove every remote process failure boundary.
3. Qualify late/cached Android delivery and new-session admission throughout partial
   publication, plus unsupported peers within this coordinated stand. Previous native
   legacy/revoke/late-ACK/partial-commit/cancel/control-drain negatives remain in the race
   scope, but are not a substitute for all coordinated end-to-end scenarios.
4. Explicitly package and validate the current readiness/runtime-reader contract; retain
   the old accepted maintenance API and production-disabled qualification guard meanwhile.

Only after these source gates may a separate release decision consider immutable artifacts,
full platform CI, exact matching gateway binaries, approved production scheduling/window,
online live acceptance on both nodes and physical weak-link/screen-off/mobile allowlists.
APK118 is not upgraded by this source work and receives no continuity promise. Production
activation, paid/cohort/boot/catalog changes and fixes for paired-DNS/WebSocket are NOT done.
No rollback of live systems is needed: none were changed. Source fallback is the unchanged
quiesced path; this is not permission to reset Git or alter a live transaction.
