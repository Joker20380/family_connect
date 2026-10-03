# 5N-PROV-1 — controlled attempt #9, 02.10.2026

## Result and stopping boundary

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK**

Single explicitly authorized attempt. NL authoritative acceptance and complete RU
sync acceptance passed. HTTP activation failed: ordinary transition probes observed
429/502, and the real non-canary matrix stopped on429 instead of403. Durable receipts
preceded verdict and scoped rollback. No retry, live hotfix, phone access, APK build,
public release, push, distributed beta or Krasnodar FIELD-1.

Attempt #3 cause remains **UNKNOWN**. #6 remains stale-HTTP pre-production STOP;
#7 remains stale-sync pre-production STOP; #8 remains a rollback caused by the old
operator incorrectly gating on diagnostic journal timeout after valid NL READY.
All previous reports and their retained uncommitted changes are preserved.

## Source, artifacts and local checks

- Source HEAD throughout: `028300e009007e78401cc2431989c18e0810d5f9`.
- Sync: `state-client-build/sync-artifact-refresh/bundle/restricted-sync.pyz`.
  SHA256 `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`.
- HTTP: `state-client-build/http-packaging-git-recheck/final-bundle/friends-http.pyz`.
  SHA256 `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
- All17/25 inventoried entries and embedded members verified; every bundled tracked
  source/config/lock input matches its current HEAD blob. No extra archive members.
  Earlier build commits are allowed because bundled sources have not changed;
  literal artifact build-commit equality was not used. Neither artifact rebuilt.
- Both archives pass isolated `python -I` CLI/import-origin checks outside checkout,
  without PYTHONPATH/PYTHONHOME or first-party working-tree imports.
- Two exact-artifact local tests PASS: fresh synthetic sync `--check`/real-entry
  tracing, and exact-sync→unchanged-HTTP signed-readiness/startup fixture. Approved
  host execution used loopback only. Synthetic PASS does not substitute for real G.
- Both committed acceptance harnesses are present and source-pinned. NL and RU
  execute their unchanged HEAD bytes on the respective host.

Evidence is owner-only/ignored: `state-client-build/prov1-attempt9/`.
Operator adapts retained installation/rollback steps only for the new attempt
namespace, current artifacts, current authoritative CRL location and a planned
60min acceptance window. No runtime/harness predicate, TTL, authority or route
redesign. The initial read-only audit inherited the literal `attempt8-baseline`
label; its fresh timestamps and separate #9 files identify this attempt. This
label defect is disclosed in `operator-provenance.json`, not silently rewritten.
HTTP baseline and all acceptance generations explicitly say attempt9.

## Authority, JIT and baseline

Read-only RU/NL audit09:20:40–41UTC: restricted services inactive; RU restricted
drop-ins/ingress absent; NL forced authorization/directory absent. `provider.env`
is regular root:root0600; token not displayed, copied into receipts or hashed.
Existing rollback inputs and accepted staged native components verified. New
root-only snapshots completed09:29:46–49UTC before runtime modification.

| Material/property | Safe observation |
| --- | --- |
| Delegation / issuer | Sequence1; issued01.10 10:44:11UTC; expires02.10 10:44:11UTC; unchanged signature/key/binding |
| Owner grant | Sole restricted grant, revision1, expiry02.10 10:44:11UTC; real Owner binding checked |
| Validity window | 4459s remaining09:29:51UTC; >3600s planned window, checked again before JIT; no renewal required |
| Device registry | 28 total,4 revoked; one restricted owner,27 denied; no new admission |
| Initial floor | RU DB/stage15 and NL15; inactive RU runtime14 explicitly not used as authority |
| JIT CRL | 15→16 at09:31:33UTC; expiry09:46:33UTC; existing15min policy |
| Gateway leaf | Same gateway/key, expiry10:31:33UTC; existing≤1h policy |
| Native authority | Gateway/canary compatibility and Family/revision/CRL negatives PASS; effective server validation expiry09:46:33UTC |
| Canary validation leaf | Server-only validation, expiry09:46:33UTC; not real owner product delivery |

Existing machinery publishes valid monotonic sequences. Family, gateway, owner,
issuer, delegation, grant and security policy unchanged. Root signer not invoked.
Private credentials/profiles/provider values remain out of Git/output/receipts.

Baseline file+directory-fsynced receipts09:29:41–42UTC:

| Probe | Status | Transport | Generation |
| --- | --- | --- | --- |
| A ordinary status | 200 | none | attempt9-baseline |
| B ordinary malformed challenge | 400 | none | attempt9-baseline |
| C safe ordinary Friends chat challenge | 400 | none | attempt9-baseline |
| D restricted malformed while disabled | 404 | none | attempt9-baseline |

RU API/AWG/TCP healthy; NL AWG/TCP/Reticulum/mailbox active with stable baseline
PIDs/start times. No neighbouring services/hosts operated.

## NL and RU authoritative acceptance

NL bootstrap starts09:31:36UTC. Fresh one-seed READY-path directory issued
`2026-10-02T09:31:40.421030377Z`, expires
`2026-10-02T10:26:37.382199933Z`; canonical UTC Z, precise validation and expected
Family/gateway binding PASS. Stable healthy same process, NRestarts0, successful
final readback. Authoritative PASS fsynced **09:31:41.637052Z**.

Optional journal result separately fsynced **09:31:46.895731Z**:
`diagnostic_timeout`, configured5s, elapsed5.257s. This does not alter PASS.
No journal event is substituted for a true authoritative check.

RU accepted exact archive installed; production-local `python -I ... sync --check`
from `/`, without PYTHONPATH, exits0 with exact expected stdout/empty stderr
09:31:48UTC. `ru-check.json` fsynced before its verdict.

Committed `restricted_sync_acceptance.py` completes **09:31:58.272226Z**:

1. Blocking sync start and oneshot success PASS.
2. Fresh signed CRL16→17 and DB floor agreement PASS.
3. Valid current directory PASS.
4. Generic-shell rejection PASS.
5. Stale-CRL rejection PASS.
6. Final monotonic/authority/readback and total deadline PASS.

No mandatory negative skipped. Completed set:
`unit,fresh_readback,generic_shell,stale_crl`. RU journal is not a gate and was not
requested. Timer activation later normally advances CRL17→18; no history reset.

## HTTP activation, exact failure evidence and hard stop

Only after both authoritative gates PASS: exact accepted HTTP artifact/drop-ins
and additive ingress enabled. No rebuilt archive or live route redesign.
Production receipt generation `attempt9-http-460e75205eb9`; separate external
ordinary-route observer generation `attempt9-transition`.

| Matrix gate | Durable production evidence | Verdict |
| --- | --- | --- |
| A ordinary status | 09:33:21.985270Z →200 | Individual matrix sample PASS, transition not healthy |
| B ordinary malformed challenge | 09:33:22.060577Z →400 | Individual sample PASS, transition not healthy |
| C safe ordinary Friends challenge | 09:33:22.130725Z →400 | Individual sample PASS, transition not healthy |
| D restricted malformed challenge | 09:33:22.199689Z →400 | Bounded rejection PASS |
| E real non-canaries | Six403 receipts09:33:22.341091–22.626328Z; seventh09:33:22.680946Z →429 HTML, expected403 | FAIL; remaining20 not tested by HTTP |
| F real owner challenge | Not reached | NOT PASS |
| G real owner readiness fetch | Not reached | NOT PASS |

Ordinary transition observer:27 receipts,7 HTTP429,1 HTTP502,1 interrupted probe.
First difference: safe ordinary chat09:33:20.300386Z →429, expected400.
Malformed ordinary challenge09:33:20.755802Z →429; chat09:33:20.920215Z →502;
status09:33:21.174758Z →429. No transport error on these HTTP responses.
Full sorted evidence remains in `http-transition/` and `final-summary.json`.
Interrupted last probe resulted from observer termination, not an independently
proven server failure. Earlier429/502 already require hard STOP.

The retained observer fsyncs each sample immediately, but its wrapper evaluates
them after the short remote activation/matrix call returns. Thus first external
failure was persisted09:33:20.300Z; the wrapper stopped after matrix E failed
09:33:22.680Z, not synchronously at the first external sample. No restart/retry
attempt was made to turn this into PASS. This ordering limitation is retained,
not concealed as instant failure detection. Backend wait also recorded four
connection failures during restart before400; these do not erase external failures.

Server `ProbeFailed`/FAIL receipts and local failure verdict precede rollback.
429 is observed HTTP rejection, **not proof of its precise cause**;502 demonstrates
an observed ordinary-route failure, not its full duration or root cause. Probe
cadence/ingress behavior needs separate analysis. No log investigation/hotfix or
new deployment was performed after STOP. Historical #3 remains UNKNOWN.

## Rollback and final production state

Scoped rollback09:33:22–29UTC: RU restricted HTTP drop-ins removed, original
ordinary handler/ingress restored and API restarted; restricted sync/timer stopped
and disabled. NL bootstrap stopped/disabled, forced SSH authorization removed,
private directory quarantined. Provider file retained unchanged. Backups/evidence
on each allowed host:
`/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-attempt9-028300e/`.
No DB restore, certificate-ledger reset or CRL rollback.

Post-rollback durable HTTP09:33:29.141650–30.713443Z: **200/400/400/404**, no transport
errors. Safe final service audit09:33:32UTC: RU ordinary API active; RU/NL AWG/TCP
active and original PIDs/start times unchanged; NL Reticulum/mailbox unchanged.
Friends API PID/start changed as expected from activation and rollback, not claimed
unchanged.09:34:49UTC RU read-only audit confirms handler/ingress byte-identical to
baseline, drop-ins absent, devices/invites/restricted-grant row digests unchanged.
Admission remains the same sole owner plus27 denied. No completed post-A–G normal
product regression is claimed: A–G itself failed.

Final authoritative **CRL18**, issued09:33:20UTC, expires**09:48:20UTC**, agrees in
RU DB/runtime and NL profile. Staged RU CRL16 is older: never use it to reset floor18.
Gateway leaf expires10:31:33UTC; delegation/grant/issuer expire10:44:11UTC. Runtime
archives remain inert on disk, restricted units off; artifact presence is not
successful deployed provisioning. Validity timestamps are historical observations,
not a promise of ongoing freshness while services are disabled.

Supplemental historical final-audit helper failed on its NL quarantine-summary
expression after the successful RU audit (redacted frames32/32 retained). No retry
of deployment or change to runtime followed. Separate successful09:33:32UTC final
NL audit already records inactive bootstrap, absent directory/authorization,
provider metadata, CRL18 and leaf expiries. Local baseline/final comparison proves
normal NL service state/PID/start preservation. The supplemental failure does not
invalidate or retroactively replace any acceptance/rollback receipt.

## Physical gates, versions, Git and next boundary

- Redmi not touched. Real product identity/activation/restricted provisioning and
  BootstrapDirectory readiness not inspected; effective **device** readiness expiry
  unknown. No product prewarm, in-place APK install or re-enrollment.
- Restart persistence, Orchestrator usability, local restricted rehearsal,
  whole-device VPN, Chrome≥2 sites/TLS, Family DNS, concurrent TCP, scoped direct
  DNS leak/protected TCP bypass, UDP/QUIC and IPv6 fail-closed, underlay protection
  and ordinary-use smoke: **NOT REACHED**, no stale isolated evidence substituted.
- Final FIELD APK not produced: path/SHA/version/signature/native provenance N/A.
  Existing installed/public/invitation versions unchanged, not reverified here.
- Entry seven dirty/untracked files snapshotted byte-for-byte; only new additive
  STATUS/PLAN notes and this new report are task-owned documentation changes.
  Previous sections/reports/runbook/VPN-health work preserved; no staged changes,
  commits or push. Source/runtime/harness files and both archives unchanged.
- STOP. Future work needs a separate HTTP-transition diagnosis and explicit new
  deployment authorization, fresh authority/JIT and complete server/physical gates.
  No automatic attempt #10, distributed beta or Krasnodar FIELD-1.
