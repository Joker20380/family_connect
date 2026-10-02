# 5N-PROV-1 — controlled attempt #8, 02.10.2026

## Result / stopping boundary

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK**

Explicitly authorized single production attempt. NL live directory validation
passed, but the attempt-local NL wrapper incorrectly treated diagnostic journal
collection as mandatory. Its5s timeout aborted the attempt before RU installation/
precheck, complete sync acceptance or HTTP activation. Failure receipts were fsynced
before scoped rollback. No automatic retry, production hotfix or phone interaction.

**This was an operator error:** non-authoritative journal collection should not have
gated acceptance. It does not prove a provider/bootstrap/runtime defect or invalidate
either pinned artifact. The timeout step is deduced from the executed source order
and durable timestamps: after the persisted successful directory validator, the
only timed command before the failure was `journalctl` with timeout5s. The primary
receipt records `TimeoutExpired`, not the exact argv. No stronger raw-command
evidence is claimed. The underlying reason journal retrieval exceeded5s is UNKNOWN.

Historical facts unchanged: attempt #3 HTTP cause **UNKNOWN**; #6 stopped before
production for stale HTTP; #7 stopped before production for stale sync. Neither
#6 nor #7 changed production. Their reports and the long historical report are
preserved byte-identically relative to this session's entry.

## Source and immutable artifacts

- HEAD: `f4c06df5f16593273b4c8bffa75646f1df17c2fb`, unchanged throughout.
- Sync: `state-client-build/sync-artifact-refresh/bundle/restricted-sync.pyz`.
  SHA256 `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`.
- HTTP: `state-client-build/http-packaging-git-recheck/final-bundle/friends-http.pyz`.
  SHA256 `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
- Sync17/HTTP25 inventoried files verified; every bundled tracked source/config/
  lock/harness input matches HEAD, every embedded source matches its inventory,
  no unexpected archive files. Both artifacts retained byte-identical; no rebuild.
- Isolated `python -I` CLI and loaded-module origin checks PASS outside checkout,
  no PYTHONPATH/PYTHONHOME or first-party working-tree import dependency.
- Fresh synthetic exact-sync `--check`/real-entry tracing:1 PASS. Fresh exact-sync→
  exact-HTTP signed readiness/startup fixture:1 PASS. These are local fixtures,
  **not** RU production precheck or real owner acceptance. The HTTP fixture's first
  sandbox run could not create sockets; approved loopback-only host run passed.
  No broad274/194-test suite rerun is claimed for this deployment task.

The committed `scripts/restricted_sync_acceptance.py` was source-pinned and staged
unchanged, but never executed against production. No mandatory negative is marked
PASS based on old attempts or local fixtures.

## Authority / admission / JIT

Read-only production audit08:26UTC and current-source authority validation08:31:55UTC:

| Material or property | Observed result |
| --- | --- |
| ControlTrust delegation | Sequence1; issued01.10 10:44:11UTC; expires02.10 10:44:11UTC; signature/bindings accepted |
| Issuer | Same delegated CA/key; validity01.10 10:44:11–02.10 10:44:11UTC |
| Owner canary grant | Sole restricted grant, revision1, expiry02.10 10:44:11UTC; existing Owner registry/binding checked |
| Available authority validity | 7935s at08:31:55UTC; >90min checked again just before refresh; no renewal or arbitrary TTL extension |
| Actual normal device registry | 28 rows, including4 revoked;1 owner restricted-admitted,27 others denied |
| Historical26 non-canaries | Remain covered by deny-all-except-owner admission; actual count differs from historical snapshot, no device created by this attempt |
| Initial monotonic state | RU DB/runtime14; older RU stage13; NL profile14; old CRLs/gateway leaf expired |
| JIT CRL | Authoritative14→15; issued02.10 08:36:45UTC; expires08:51:45UTC; existing15min policy |
| Gateway credential | Same gateway/key; issued08:36:45UTC, expires09:36:45UTC; existing1h policy |
| Canary native-validation leaf | Expires08:51:45UTC; validation material only, not product delivery or re-enrollment |
| Native authority check | Gateway/canary and Family/revision/CRL negatives PASS; effective validation expiry08:51:45UTC |
| Provider token | Existing NL `provider.env`, root:root0600; metadata-only check, token not read/displayed by operator; consumed only by accepted service |

Family, gateway, owner, trust hierarchy, issuer, grant revision and admission policy
unchanged. No device enrollment or additional restricted admissions. Root signer
not needed/invoked. Private keys/token/profile bodies absent from Git and output.
Public credential transport between authorized hosts stays in the operator's memory;
only redacted receipts are copied into the local evidence directory.

## Durable baseline / live observations

Baseline receipts08:26:46UTC were fsynced before runtime modification:

| Probe | Baseline | Post-rollback08:37:07–08UTC |
| --- | --- | --- |
| Ordinary status | 200 | 200 |
| Ordinary malformed challenge | 400 | 400 |
| Safe ordinary chat challenge | 400, established malformed-input behavior | 400 |
| Restricted malformed challenge, route disabled | 404 | 404 |

All eight probes used verified HTTPS and recorded no transport error. Receipts
contain safe timestamp/probe/status/classification/config-generation metadata,
never request credentials/proofs or private response bodies. The safe ordinary
chat probe is not a successful signed ordinary device-proof challenge.

RU Friends API, AWG/TCP were active. NL normal AWG/TCP/Reticulum/mailbox were active;
NL has no ordinary Friends access unit. Restricted services/timer were inactive,
HTTP drop-ins absent, NL forced sync authorization disabled and directory absent.
Protected rollback snapshots, SQLite online backup and accepted candidate inventory
were persisted/fsynced on both hosts before runtime changes. Only Family Connect
at the two authorized hosts was operated; excluded host and MicroTrader untouched.

## NL bootstrap and failure sequence

| UTC02.10 | Observation |
| --- | --- |
| 08:36:45 | RU JIT CRL15/gateway leaf created; original authority/owner unchanged |
| 08:36:46 | NL exact new sync archive installed inertly; same-identity gateway refreshed; source-restricted forced SSH authorized |
| 08:36:47 | Accepted NL bootstrap service start |
| 08:36:52.303143974 | One seed directory exported, canonical UTC Z; expiry09:31:47.411330475Z |
| 08:36:53.695341 | Exact sync artifact's live `directory-check`: `result=passed`; no issued_in_future |
| 08:36:58 | NL wrapper persisted failure `TimeoutExpired`; process still active/running, NRestarts0 |
| 08:36:59 | Local server-failure receipt fsynced before rollback |
| 08:37:04 | RU scoped rollback complete; API restart not needed |
| 08:37:07 | NL bootstrap stopped/disabled; forced authorization removed; directory quarantined |
| 08:39:35 / 08:40:27 | Final read-only RU/NL invariants verified |

Provider/READY-path progress is supported by the real one-seed export, which the
accepted producer publishes only after READY, and the successful live validator.
The intended `bootstrap_seed_ready` journal-event count/leakage scan did **not**
complete. Do not call the entire NL acceptance PASS: it was aborted by the wrapper.
No restart storm observed; a short observation is not a long-duration stability test.
No secret/token output was emitted; full service-journal leak scanning is unverified.

## Unreached mandatory gates

Every entry below is **NOT RUN / NOT ACCEPTED**, not inferred PASS:

| Gate | Result |
| --- | --- |
| RU deployed exact-artifact `python -I ... --check` | Not reached; local synthetic check does not replace it |
| Complete blocking RU↔NL sync / unit completion / fresh CRL+DB floor / current directory / final monotonic readback | Not run |
| Generic-shell rejection | Not run live |
| Stale-CRL rejection | Not run live |
| Exact HTTP activation | Not run; archive only staged for this attempt |
| HTTP A ordinary status | No post-activation receipt; baseline/final200 only |
| HTTP B ordinary malformed challenge | No post-activation receipt; baseline/final400 only |
| HTTP C safe ordinary challenge | No post-activation receipt; baseline/final400 only |
| HTTP D restricted malformed | No enabled-route probe; disabled404 only |
| HTTP E real non-canary HTTP rejection | Not run; read-only admission deny27 is not the HTTP probe |
| HTTP F real owner restricted challenge | Not run |
| HTTP G real owner readiness fetch | Not run; no production readiness200 |
| Redmi identity/normal provisioning/restricted Family TLS/BOOT-1 usable state | Not inspected or changed; phone untouched |
| Product effective readiness expiry | Unknown/not delivered; native validation expiry is not phone readiness |
| Restart persistence | Not run |
| Local restricted CONNECT rehearsal / Android VPN | Not run |
| Chrome≥2 HTTPS sites / end-site TLS / Family DNS / concurrent TCP | Not run |
| Direct destination DNS leak / protected TCP bypass | Not measured; no zero-leak/bypass claim or accepted scope |
| UDP/QUIC and IPv6 fail-closed / underlay socket protection | Not run |
| Ordinary-use smoke on physical restricted path | Not run |
| Final shareable FIELD APK | Not produced; path/SHA/version/signing/native provenance not applicable |

No physical gate was started after failure. No uninstall, data clear, reactivation,
diagnostic identity/credentials, manual provisioning, adb reverse or SSH product
forwarding. No public artifact/version/catalog/download change.

## Rollback / final production state

Root-only rollback/evidence path on **each** authorized host:
`/opt/apps/family_connect/restricted-materials-stage-20261001/canary-rollout-attempt8-f4c06df/`.
Private SQLite backup is evidence/recovery input, **not** a DB rollback instruction.

- Rollback needed and performed. Ordinary API/ingress are byte-identical to baseline;
  both restricted HTTP drop-ins absent. No normal API/AWG/TCP restart took place.
- All normal service ActiveState/PID/restart count/start timestamp remain identical
  to baseline. This proves service continuity, not new end-to-end AWG/TCP throughput
  or user traffic acceptance. Normal HTTPS observations remain200/400/400.
- Full sorted devices/invites/restricted_grants row digests unchanged; sole owner
  grant/admission preserved. No reset or restored old DB over revocations.
- Restricted RU sync and timer inactive; NL bootstrap inactive/disabled; forced
  authorization removed; live NL directory absent, failed snapshot private/quarantined.
- RU authoritative DB/stage retain CRL15. **Inactive RU runtime still contains
  expired CRL14**, since RU install was never reached. NL profile retains floor15
  and renewed gateway credential. Never lower any floor or treat runtime14 as current.
- NL retains inert `9d965b95…` sync archive; RU retains inert retired `cb6f050e…`.
  Neither is running. Staged exact HTTP was never activated. This is not a completed
  artifact rollout and old RU archive must not be used for a future attempt.
- `provider.env` ownership/mode unchanged; token not read or rotated. Monotonic
  authority/CRL/certificate history retained, not rolled back.

Local ignored evidence: `state-client-build/prov1-attempt8/`, including input/origin
checks, entry-byte backups, baseline/final receipts, refresh/NL/rollback records and
safe final audit. The first post-rollback NL metadata collector assumed a nonexistent
top-level directory gateway field and exited read-only; corrected diagnostic selector
uses each seed's gateway. Its failure receipt is retained; no service/gate was retried.

## Documentation / remaining work / STOP

Only additive STATUS/PLAN notes and this dated report are task-owned repository
changes. All seven entry dirty/untracked files retained: five unrelated paths remain
byte-identical; STATUS/PLAN retain exact original text after removing only this task's
additions. Index unchanged/empty; no commit, branch, push or source/manifest edit.

Documentation verification:418 Markdown files/2554 links,0 errors; targeted public
source/secret guard for the three task-owned documents PASS; `git diff --check`
PASS. Final preservation ledger also rechecks HEAD and both immutable artifact pins.

Before any future separately authorized attempt: correct the **operator's** NL
journal-gating/error-attribution behavior locally; keep diagnostics non-authoritative,
then re-pin accepted sources/artifacts, recheck authority validity and authoritative
floors, safely renew only when required, JIT refresh and repeat every live/physical
gate. Do not retry under the consumed attempt #8 authorization. No architecture or
admission expansion is proposed. FIELD APK remains conditional on all gates passing.

**Push:no. Distributed beta:no. Krasnodar FIELD-1 started:no. STOP.**
