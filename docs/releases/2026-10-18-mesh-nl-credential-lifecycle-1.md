# MESH-NL-CREDENTIAL-LIFECYCLE-1 — BLOCKED recovery / verified cause

18 October 2026. All times below are UTC. Read-only RU/NL audit09:05–09:19,
offline decision-path tests and documentation only. No production command that
issues credentials, publishes, resets, stops or starts a service was executed.
No root-key access, signing, Android action, admission change or transport tuning.
[Sanitized evidence](2026-10-18-mesh-nl-credential-lifecycle-1-evidence.json).

## CREDENTIAL_LIFECYCLE_ROOT_CAUSE

**VERIFIED: the leaf/CRL schedule worked, but reached a deliberately unauthorized
authority/grant maintenance boundary. That operator/offline-root handoff was not
completed.** This is not primarily a missing timer, failed leaf publication, or a
systemd start-limit problem. The four-hour gateway process lifetime exposed the
expired credentials at its next startup; increasing that lifetime would not fix
the renewal chain.

The last committed scheduled renewal was02:41:54. Authority sequence16 and both
active grants expired08:57:40; their unchanged six-hour renewal threshold was
**02:57:40**. At03:11:35 the next scheduled evaluation returned
`MAINTENANCE_REQUIRED / MAINTENANCE_BLOCKED_BY_SESSION_UNCERTAINTY`, mutations0.
The operator deadline was already recorded in the accepted17 October maintenance
receipt. No successor authority request/unfinished owner transaction was found in
the inspected live locations. Why the owner did not act is **UNKNOWN**; the audit
does not establish whether a human saw the local alarm.

Installed `ProductionController.run` permits the previously approved automated
scope only when all due items are a subset of `{leaf, crl}`, with no changed
revocations. Authority/grant work first needs the maintenance gate; authority also
requires a request-bound offline-root bundle. Scheduled runtime passes neither an
operator approval nor authenticated zero-session inventory. The gate intentionally
returns before acquiring/quiescing/preparing/publishing. A stopped NL now does not
retroactively authorize maintenance or provide authenticated session inventory.

At05:11:35 leaf/CRL also became due, but authority/grants were still due, so the
same gate blocked the combined work. At06:41:35 leaf/CRL expired. The normal
validator permits an expired *leaf predecessor* for a narrow renewal path, not an
expired CRL or expired root delegation. At08:57:40 authority/grants expired too.
Consequently the current recovery route is the installed, explicit
**`EXPIRED_PREDECESSOR_RECOVERY`** workflow, not ordinary scheduled/operator retry.

| Hypothesis | Finding | Evidence / confidence |
|---|---|---|
| Renewal never scheduled | Rejected | Active15-minute timer; COMMITTED02:41:54; NOOP02:56:34. High. |
| Scheduled renewal failed | Confirmed, precisely gated before mutation | Fourteen maintenance-required records03:11–06:27; first CRL expiry rejection06:42. High. |
| New credentials generated but not installed | Not the observed failing stage | Last live CRL27119 matches DB and last COMMITTED transaction; later gate reports mutations0, no pending authority-request/owner. Uninspected private/offline files are not claimed absent. High for inspected controller path. |
| Installed but not loaded | Not the cause of this missed generation | No newer live generation found; gateway startup rejects expired current profile. No post-expiry replacement load was attempted by this task. High. |
| Inconsistent validity windows | No malformed interval found; lifecycle deadlines missed | Parent24h, children4h within parent; six-hour parent gate precedes90-minute child gate. Gateway execution extends approximately12s beyond leaf expiry. This small edge does not explain the hours-long absent successor. High. |
| Start limit prevents recovery after valid credentials | Consequence, not present primary cause | MainPID0/NRestarts6; no current valid successor. Start-limit reset alone cannot satisfy startup verification. High. |

### Exact source, accepted artifacts and current material

Local HEAD and checked GitHub main remain
`7656f2c65ea2928b71a928c12ee65a2f47f8ac4f`, source parent
`edca5447418141cb44c0706e26d1973d7defd397`. Prior uncommitted performance tests/docs
are preserved. The main maintenance tree includes unaccepted all-activated work;
**it is not the deployed legacy controller**. The actual deployed modules were
read and hash-verified independently. No checkout/build/source replacement occurred.
The preceding PERF-2 CI record still applies: source phase0 failures are not
acceptance of new runtime; client CI success is not physical acceptance.

| Object | SHA256 / state |
|---|---|
| NL configured batch1 gateway | `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |
| NL running executable | None observed09:19:36: failed, MainPID0, no18444 listener. Configured hash is not a `/proc/PID/exe` attestation. |
| RU renewal source manifest, also matched on NL | `5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145` |
| Deployed `production_controller.py` | `b9af8199e137e861f9e68db9e5fc1d601e6fcaa3877994bf9f83366e68d9f0b5` |
| Deployed `credential_renewal.py` | `fb83d851b4ac88b7ad90b97c59f516ee327bc7bbb92a642a031da08bbc50d25c` |
| Deployed `runtime_controller.py` | `73c3784855f8fb53140d3ddfdcc7f693cad080c84b3fbec1481f91b2dc076c59` |
| Deployed `expired_recovery.py` | `92fc24346df6b86b0621210e7847a2d17c11a69e8c2ae73bf32609fa2f2ab99e` |
| RU API archive, bytes rehashed09:19 | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` matches configured pin |
| NL management API archive, bytes rehashed09:19 | `9faaa1c27f534e71774f5b4f34872e87747f391409c4958562694f07f86d64d1` matches configured pin; not the gateway executable |
| Authority PEM | `bd0253f87fd18d3b26ac24c4884cefff51363ad442256d5991722b1e46d22169` |
| NL leaf PEM | `a27ffe653dd1e79ec8d075ac2b314b721cba654f2da98572d76c1039ae50e4cd` |
| CRL PEM, RU/NL equal | `f4ee896d344e3906a974f39be33306d851d4375d421dec4f80c715d1eddec4bd` |
| Directory bytes, RU/NL equal | `50aa786cb751a40c8ef6c7ccfdc60a126f6bcd9432d7f78cb912f1f9fc104ad8` |

Authority sequence16:17 October08:57:40 →18 October08:57:40. Leaf and CRL:
18 October02:41:35 →06:41:35. CRL number27119 contains **two revoked entries**;
RU DB CRL sequence is27119. Read-only DB aggregate: two nonrevoked grants, revisions
6 and8, both expire08:57:40. No device references or grant rows are published here.
Gateway minimum revision1 / minimum CRL27088 are observed floors, not instructions
to lower anything. Successor checks must consider current signed27119 and all
client/controller floors, not just the older profile minimum.

Root delegation signature, configured public-anchor pin, issuer self-signature,
leaf issuer-signature and CRL signature verify. **Those are historical signature
checks, not current validity.** Authority, leaf and CRL are now expired. Signature
validity never overrides time, revocation, identity, scope or monotonic checks.

Directory v1 was issued05:41:54.637165993Z and expired06:41:47.650095111Z. Its latest
seed rotation is not a credential renewal. The inspected v1 directory has no
standalone signature field: signed issuer delegation/chain and authenticated
provisioning are separate from strict directory schema, time and family/gateway
binding checks (`control/friends/restricted.py`, retained UI84
`carrier/wholedevice/provisioning.go`). No standalone directory-signature PASS is
claimed. Preserve every existing authenticated-delivery/signature/binding check;
do not introduce a substitute directory or weaken verification to recover.

NL profile is `/opt/apps/family_connect/friends-restricted/gateway.json`, mode0600,
uid/gid979 (`family-restricted:family-restricted`); systemd User is
`family-restricted`, Group is unset. Fresh parent-directory/ACL and actual service
readability checks are still required immediately before any publication.

## RENEWAL_FAILURE_TIMELINE

| UTC | Evidence / event |
|---|---|
| Oct17 08:58 maintenance receipt | `MAINTENANCE_COMMITTED_STRICT_READY`: authority15→16, CRL27111→27112; parent/grant expiryOct18 08:57:40; **next_operator_threshold02:57:40 explicitly recorded**; timer restored. |
| Oct18 02:41:35 | Current leaf/CRL generation starts, expiry06:41:35. |
| 02:41:54.249026 | Renewal journal COMMITTED, operation `scheduled-1792291291-d3bbc76b3aa8dc8d`; coordinator commit receipt matches. |
| 02:56:34.288745 | NOOP, due[], parent/grant headroom21666s; leaf/CRL13501s. |
| 02:57:40 | Parent/grant headroom21600s: exact installed six-hour threshold. Computed from verified expiry/policy, not an invented journal event. |
| 03:11:35.713408 | First observed MAINTENANCE_REQUIRED / SESSION_UNCERTAINTY, mutations0. |
| 03:15:01.083033 | First CRITICAL health record in inspected window, `CONTROLLER_FAILURE_OR_MAINTENANCE_REQUIRED`, remote delivery UNAVAILABLE. |
| 03:26–06:27 | Same maintenance gate on recurring scheduled runs, no mutations; no usable next authority generation. |
| 05:11:35 | Leaf/CRL headroom5400s:90-minute threshold;05:11:46 scheduled run still blocked by combined authority/grant maintenance. |
| 06:41:35 | Current leaf and CRL expire. |
| 06:41:47 | Gateway completes four-hour lifetime; directory expires at06:41:47.650095111. Gateway event from PERF-2 NL journal evidence, not inferred from the timer. |
| 06:42:05.551586 | First renewal FAIL_CLOSED `CRL_EXPIRED_OR_FUTURE`; subsequent15-minute attempts through08:57:32 do likewise. |
| 06:44:52 | NL restart loop reaches start limit after PROFILE/CREDENTIALS_REJECTED startup failures (PERF-2). |
| 08:57:40 | Authority and both active grants expire too. Ordinary current-clock predecessor validation is no longer a recovery path. |
| 09:05–09:12 | Timers active; last coordinator checkpoint COMMITTED, matching plan/reconciliation, no owner marker; health/directory sync fail closed. |
| 09:19:36 | Final readback: unchanged gateway bytes, expired but correctly signed leaf/CRL; NL remains stopped. |

Actual RU units: `family-connect-credential-renewal.timer` uses OnBoot2min,
OnUnitActive15min, Accuracy10s; its service calls `runtime_controller.py --mode
scheduled`. `approved_leaf_crl_schedule=true`. Health timer uses5min/10min/1min.
The separate directory-sync timer uses30s/30s/1s and runs `scheduled_evaluate.py`;
it can publish a directory and **must not be invoked as a read-only probe**.
Inactive legacy `family-connect-restricted-sync.timer` is not the renewal timer.

The real OnFailure unit is `family-connect-credential-renewal-alert.service`;
its action is a successful local `/usr/bin/logger`, **not remote delivery**. Every
inspected controller/health record says `remote_alert_delivery=UNAVAILABLE`.
The similarly named `family-connect-credential-alert.service` was absent; that
initial lookup was corrected. Local alarm success does not prove owner notification.
The alert-journal read covers08:58–09:11 only, not all earlier alert invocations.

Coordinator checkpoint structural checks passed: COMMITTED, commit_decided=true,
matching operation and all recorded reconciliation hashes; plan SHA256
`289e59aecffe16a482ef29eb13995393d5b0e37dbe6b678c9a4dfc556052ba4d`.
One historical recovery-request/result file exists in each archive directory;
counts are **not new pending authorization or a reusable recovery bundle**.

## SAFE_REMEDIATION_PLAN

### Immediate legitimate recovery — NOT executed

1. Obtain explicit authorization for the existing expired-predecessor workflow,
   exact existing grant scope and a bounded maintenance outage. Refresh read-only
   state, clocks, process/session inventory, source hashes, permissions, checkpoint,
   revocations and floors. Stop on changed/unexplained state. Do not import main's
   all-activated/longer-validity candidate or rerun old deployment wrappers.
2. Under that authorization, use the **installed** `expired-request` path with a
   new operation ID and private grant-scope/request files. This is **not read-only**:
   it writes a durable request and asks the RU issuer to sign successor CA material.
   Scope is the current complete nonrevoked grant set; no new admission. The request
   binds historical signed predecessor, exact snapshots/checkpoint, identities,
   floors, successor payload and bounded time window. Do not create it during audit.
3. Operator reviews that exact request/hash and explicitly approves offline-root
   signing through the established local vault GUI/memory-only key-FD procedure.
   Never paste/export the key, place it on RU/NL, or use CI. The retained offline
   `sign_authority_offline.py` supports `--expired-recovery`; ordinary handoff is
   not equivalent. Its retained source SHA256 is
   `2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6`.
   The last batch-maintenance offline directory lacks `expired_recovery.py` and
   `grant_cutover.py`: assemble/verify its matching public dependencies and test
   offline first, rather than relying on accidental imports from current main.
   The old batch-maintenance operator wrapper also pins a different gateway; do
   not execute it unchanged. No vault or signer was invoked in this investigation.
4. Before apply, independently verify the proposed root-bound bundle, current
   clock and request expiry, same root/issuer key/Device Identity/family/gateway,
   exact request/operation/snapshot binding, unchanged admission, and all sequence
   and revocation transitions. Installed recovery requires authority sequence+1,
   unchanged minimum revision, same issuer key,24h authority validity; children
   remain at most4h and inside their parent. Retain both existing revoked CRL
   entries and all revoked grant state. Existing grant successor logic controls
   revisions; never hand-edit the DB, extend old grants or reset client floors.
5. Only with **separate install/service authorization** use `expired-apply` with
   its explicit outage approval. Existing transaction acquires/serializes writers,
   quiesces readers, stages, validates and durably commits both endpoints. Keep
   current gateway4b722d…8fab7 and accepted UI84, not an experimental supervisor.
   Check existing guarded profile publication against observed uid/gid/mode/ACL;
   preserve service readability. Require current Python and matching native
   acceptance before start; reconcile the stale systemd start limit only as an
   authorized recovery step after credentials pass, never as the credential fix.
6. After authorized start, attest `/proc/MainPID/exe`, served chain, loaded validity,
   listener, fresh Telemost directory, RU/NL directory equality and authenticated
   readiness delivery. Preserve served HTTP/ALPN requirements in the existing
   runbook. Verify UI84 refresh/reconnect with the same Device Identity and no
   clearing data, reactivation or APK replacement. Do not claim compatibility
   solely from a successfully parsed offline bundle.

Existing procedures: [gateway credential publication](../../deploy/friends/restricted/GATEWAY_RENEWAL.md),
[native authority verification](../../deploy/friends/restricted/NATIVE_AUTHORITY.md),
and the retained installed `runtime_controller.py` / `expired_recovery.py` /
`production_controller.py`. Their live hash pins, not their filenames or main's
unaccepted source, determine the procedure. The earlier
[authority-renewal report](2026-10-06-authority-renewal-1.md) is precedent, not
permission to replay its older policy/artifacts.

### Sustainable operation without changing cryptographic policy

- Preserve24h authority/grants,4h leaf/CRL, current validation and15-minute schedule.
  A short-lived offline-root authority requires a human/approved offline signing
  step each cycle. This trust model cannot promise indefinite unattended service.
- Schedule owner coverage **before** each newly verified `authority_expires_at-6h`
  threshold, with enough margin for signing, approval, controlled cutover and
  directory/UI84 refresh. Record the next deadline from actual successor validity,
  not from deployment wall-clock or an assumed timer reset. Current03:11 warning
  left3h30 until the leaf expired, but no handoff completed.
- Provide an owner-approved external alert/acknowledgment path for upcoming
  authority/grant maintenance, first MAINTENANCE_REQUIRED, publication failure and
  failure-to-recover. Current logger/health exit status is insufficient as sole
  paging. Name the due scopes and remaining headroom in operator presentation;
  the current generic gate result masks the underlying offline-root deadline.
  Select a channel and obtain authorization separately; no notification service,
  scheduler or policy was created here.
- Keep scheduled leaf/CRL scope narrow. Do not resolve session uncertainty by
  pretending count0, enabling scheduled outages for authority/grants, moving the
  root key online, disabling revocation, or merely lengthening validity. Existing
  renewal quiesces/restarts readers; this is not a zero-downtime hot-reload design.
- Acceptance for sustainability: observe at least two ordinary scheduled leaf/CRL
  renewal cycles **and the next operator-authorized authority/grant cutover**, with
  readback of the new loaded generations, alert acknowledgment and reconnect.
  Recovery of one start is not proof the next daily deadline will be met. If valid
  credentials cannot be obtained, keep failing closed and report the outage.

## GATEWAY_RECOVERY_PREREQUISITES

| Gate | Current status |
|---|---|
| Exact existing gateway / deployed controller identified | PASS, configured bytes and source hashes read; no loaded process |
| Current generation, expiry, historical signatures and floor state | PASS for recorded metadata; refresh immediately before mutation |
| Coordinator consistency / no unfinished owner transaction | PASS structural readback; archived recovery records not replayed |
| New recovery request and offline-root authorization | **BLOCKED**, no request or successor signed in this task |
| Proposed replacement validity and native compatibility | **NOT TESTED**, no replacement exists to attest |
| Operator-maintenance / credential installation / service reset-start approval | **NOT GRANTED** by investigation task |
| Offline signer dependencies and full expired-recovery integration tests | **PENDING**, public source is available; current probe is not this acceptance suite |
| Live UI84 same-identity refresh and reconnect | **PENDING**, requires restored legitimate service and authorized physical run |

Rollback is not “copy the expired predecessor back and restart.” Before any
commit, preserve private backup/receipts under the existing runbook; abort and
leave unavailable if staged material fails. After durable commit, reconcile exact
operation state and use the existing forward-resume path for unknown/partial
outcomes. Never replay signing/apply with a new ID to hide an uncertain outcome,
roll back monotonic floors, discard revoked entries or reuse expired material as
current. Restoring source/binary is unnecessary: neither changed. Production
availability may remain blocked while an authorized valid successor is obtained.

## VERIFICATION_RESULTS

| Check | Result / limitation |
|---|---|
| RU/NL service/timer/process/binary/file audit | PASS read-only; no production runtime invocation |
| Historical delegation/issuer/leaf/CRL signatures | PASS; current validity FAIL as expected; not a recovery waiver |
| Timer→gate→expiry timeline | PASS, correlated live journal, recorded generation and exact deployed source |
| Offline deployed-source decision reproduction | **12 PASS** in0.012s; five module SHA256 pins enforced; no remote nodes/process launch |
| Wrong-source negative check / evidence consistency | PASS: current main rejected by source pins; JSON, recorded source/probe hashes and report links checked |
| Existing guarded publication unit tests | **19 PASS,22 SKIP** in0.12s; skipped cases require isolated root DAC testing, not production sudo |
| Full expired-recovery signing/native/live acceptance | NOT RUN, authorization/material missing; no claim of cryptographic end-to-end acceptance |
| Production recovery / sustained renewal / physical throughput | NOT RUN; remains BLOCKED |

Reproduce the decision test using **read-only copies** of the five deployed public
Python modules named in `PINS`, from
`/opt/apps/family_connect/friends-restricted/renewal/` on authorized RU. Do not copy
node/controller configs, databases, key files or profiles into the repository.
The audited copies currently reside in `/tmp/fc-credential-lifecycle-audit/RU`:

```sh
python3 tests/fixtures/mesh_credential_lifecycle_probe.py \
  --source-dir /tmp/fc-credential-lifecycle-audit/RU -v
python3 -m pytest -q tests/test_gateway_credential_publication.py
```

Probe scope: threshold boundary02:57:40, NOOP02:56:34, blocked parent and combined
renewal, allowed leaf-only decision reaching a sentinel *before* transaction,
revocation/outage/stale-approval gates, required offline handoff, expired-CRL
rejection despite expired-leaf flag, and required committed recovery checkpoint.
Validated metadata and the expiry-branch x509 loaders are **stubbed**; this neither
signs credentials nor verifies actual cryptography. No new production code or
alternate renewal mechanism is introduced. Its parent-success case does not prove
publication or restart succeeds. Current main with different hashes is rejected.

Initial broad journal reads timed out; narrowed bounded reads of the system journal
successfully returned26 renewal and40 health records from02:30 onward. Relevant
fields were allowlisted. Raw journals, identity references, signed delivery payloads,
private keys, grant rows, and profile contents are not committed or printed.
Latest source/CI provenance is linked from PERF-2; no full CI rerun/release occurred.

## PERFORMANCE_TEST_READINESS

**BLOCKED, unchanged.** The [PERF-2 physical run card](2026-10-18-mesh-perf-2.md#next_safe_action)
remains the next transport experiment after legitimate recovery. Preserve the
previously attested installed Friends code84 `0.1.18-research84-ui60-4-batch1`:
APK SHA256 `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`,
restricted native SHA256 `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`;
all12 native libraries matched in PERF-2. These are prior same-day phone attestations,
not a new running-session measurement. No APK rebuild/install or VPN action here.

Require ready current credentials/directory, matching loaded gateway, adequate
headroom and no scheduled cutover inside the bounded test interval. Reattest phone,
obtain the authorized physical session, prove traffic traverses MESH, then measure
download/upload1/4 flows, byte integrity, idle/loaded RTT and paired existing
SessionTrace/ACK/VP8/RTP support samples. Keep batching, pacing, retransmission,
windows, crypto and timeouts unchanged. Missing exact DATA-size/flight-byte
distributions in accepted exports remain a separate evidence limitation. Do not
substitute a synthetic probe for physical performance acceptance. IPv6 and
all-activated/UI84-consolidation/supervisor acceptance remain separate workstreams.

## FINAL_RESULT

**BLOCKED for recovery and physical testing; root-cause investigation complete
within its read-only scope.** The missed stage is the explicit parent-authority/
grant maintenance + offline-root handoff, with local-only alert delivery. Scheduled
leaf renewal, publication and valid startup previously worked; a next authorized
generation was not produced by the audited controller after its03:11 gate. Expired
CRL/parent validation and subsequent start limit are downstream fail-closed results.

Next safe action: separately authorize preparation/review of the existing
snapshot-bound expired-recovery request (including RU successor-CA issuance), then
the offline-root vault signing ceremony. Installation and the bounded RU/NL service
maintenance need explicit authorization before apply. No successor validity,
recovered connection, sustainable future renewal or performance improvement is
claimed before those independent gates pass.
