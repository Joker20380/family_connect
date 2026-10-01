# 5N-PROV-1 — controlled attempt #6, 01.10.2026

## Result and exact stopping boundary

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK**

For the requested result taxonomy: deployment inputs failed before production
access. **No production modification occurred, so no rollback was needed or
performed.** This is not a claim that a live deployment or rollback ran.
Verification receipt:2026-10-01T18:31:33.858431+00:00. No automatic retry/hotfix.
Attempts #1–#5 remain unchanged in the
[historical report](2026-10-01-5n-prov1-production-restricted-provisioning.ru.md).
Attempt #3 historical HTTP cause remains **UNKNOWN**.

## Inputs and source mismatch

- Source HEAD: `8663128a4ee433c29adb90340b8d4573ac2ba161` — confirmed.
- `scripts/restricted_sync_acceptance.py` exactly matches committed HEAD;
  SHA256 `b7e130f5a23daaeaca5580b4667995d9153be5de50dac2ba6f461e941063ac97`.
- Sync artifact: `state-client-build/directory-validation/final-sync-bundle/restricted-sync.pyz`;
  SHA256 `cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`.
  Pin/all17 inventory entries/embedded source versus bundled source **PASS**.
- HTTP artifact: `state-client-build/http-activation/validated-bundle/friends-http.pyz`;
  SHA256 `eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`.
  Pin/all25 inventory entries/embedded source versus bundled source **PASS**.
- Neither artifact was rebuilt, modified, uploaded or installed by attempt #6.

The one source mismatch is `control/friends/restricted.py`:

| Source | SHA256 |
| --- | --- |
| Pinned HTTP embedded/bundled module | `c63c1eca5d553f3d4e5fcd63aee9cd8a27b73c3f50466fe8df8cc0edb95327c9` |
| Current HEAD / pinned sync module | `9b5d5ce2b994dd5d89fe147536cccfd998b351c17673c4183eae7f9db05a011f` |
| Retained worktree module | `ab3542b9f696c15a90211d7ff814f82de38cbb134b3b6287dc10af6a11513755` |

HTTP contains the pre-fix integer-second directory consumer/delivery path; it
does not contain the accepted `clock_nanoseconds`/nanosecond delivery fix.
The source diff is not merely the retained HTTP malformed-challenge hunk.
Sync matches HEAD; its difference from the worktree is only that retained hunk,
which was neither overwritten nor incorporated into a new build.
All other mapped bundle inputs match current local source bytes.
The runbook already says future HTTP packaging must include the corrected shared
consumer. Thus intact pins do not satisfy the additional current-source gate.
The explicit instruction to stop on mismatch takes effect before JIT refresh.
No new isolated runtime/dependency smoke or native validation was run after STOP;
the complete zip/source inspection is not a new production `python -I --check`.

## Gates not reached

| Requested gate | Attempt #6 result |
| --- | --- |
| Fresh CRL sequence/issue/expiry; gateway certificate expiry | Not refreshed or queried |
| Baseline ordinary status200/malformed400/safe ordinary400/restricted-disabled404 | No attempt #6 receipts; not probed |
| RU AWG/TCP and NL normal service baseline; restricted inactive/drop-ins absent/provider metadata/rollback inputs | Not queried; no new health/config assertion |
| NL provider/gateway identity/bootstrap READY/restart count/UTC-Z | Not run |
| Live BootstrapDirectory validation/issued_in_future recurrence | Not run; recurrence unknown this attempt |
| RU isolated read-only --check | Not run |
| Complete RU live sync acceptance | Not run |
| Generic-shell rejection / stale-CRL rejection / monotonic final readback | Not run, not PASS |
| HTTP A ordinary status / B malformed challenge / C safe ordinary challenge | Not activated/probed |
| HTTP D restricted malformed / E real non-canary / F real owner challenge | Not activated/probed |
| HTTP G real owner readiness fetch | Not run |
| Normal Friends API/AWG/TCP regression; registrations/grants; sole canary/26 rejected | Not queried; admission not changed by this task |
| Friends API downtime | No restart/change by this task; no live uptime observation |
| Redmi restricted provisioning / BootstrapDirectory / effective readiness expiry | Not run/unknown; phone untouched |
| Restart persistence / restricted rehearsal / Android VPN | Not run |
| Chrome two HTTPS/TLS sites / Family DNS / concurrent TCP | Not run |
| Direct DNS leak / protected TCP bypass | No attempt #6 evidence or tested scope |
| UDP/QUIC / IPv6 fail-closed / underlay socket protection / light-use smoke | Not run |
| Final FIELD APK path/SHA/version/signature/native provenance | Not produced |

Last documented production readback is attempt #5 rollback: restricted stack off,
ordinary API/AWG/TCP unchanged then, authoritative DB/RU/NL CRL sequence14,
CRL expiry2026-10-01T18:10:45Z and gateway leaf expiry2026-10-01T18:54:54Z.
These are **historical**, not fresh attempt #6 material or a live final-state check.
CRL14 was already expired at this attempt's input verification. Do not use it as
fresh authority or assume a current floor without live reconciliation.
Family/owner/issuer/gateway/delegation/grants/TTL were not changed by this task.
No SSH/production request, no private credential/provider token access.

## Worktree protection and durable evidence

Entry status was exactly8 modified files and6 untracked files. Safe paths/SHA256
for all14 were recorded before subsequent investigation. Input verification
confirmed all14 unchanged before documentation. STATUS/PLAN receive only inserted
attempt #6 notes; their prior bytes and all other retained files are preserved.
No stage/reset/restore/stash/delete, no commit/branch, no push. A separate new
report avoids editing retained historical report content.

Local evidence, ignored by Git:
`state-client-build/prov1-attempt6/worktree-before.json`,
`state-client-build/prov1-attempt6/input-verification.json`,
`state-client-build/prov1-attempt6/verify_inputs.py`, and final
`state-client-build/prov1-attempt6/worktree-after.json`.
JSON receipts are flushed/fsynced; evidence directory is fsynced. They contain
only safe source hashes/paths and verdicts, no private response bodies or keys.
Original documentation snapshots are additionally retained in
`/tmp/fc-prov1-attempt6/` for exact additive-change verification.

## Remaining work and rollback boundary

Do not rebuild the accepted HTTP pin during this attempt. Separately reconcile
and accept a current-source HTTP artifact, rerun offline HTTP/readiness contracts
and inventory/isolation checks, and obtain a new explicit deployment scope/pin.
Any later authorized attempt must restart all live gates, refresh from current
monotonic authority without resetting floors, and use the committed sync operator
with both mandatory negatives before HTTP activation. No new task is started here.

Rollback was not necessary/performed. For a future live failure the existing
runbook restores ordinary API/ingress, removes restricted HTTP drop-ins, stops
restricted sync/timer/NL seed/forced authorization, preserves DB/CRL floors, and
requires durable ordinary-route/normal-service readback; no AWG/TCP restart or
whole-DB restore. None of those production operations was executed in attempt #6.
No public version, installed client, catalog or invitation-page version changed.
**Git push:no; distributed beta:no; Krasnodar FIELD-1:no. STOP.**
