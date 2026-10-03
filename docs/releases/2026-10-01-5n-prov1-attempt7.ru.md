# 5N-PROV-1 — controlled attempt #7, 01.10.2026

## Result and stopping boundary

**5N-PROV-1 = DEPLOYMENT FAILED / ROLLED BACK**

This uses the requested result taxonomy, not a claim that deployment or rollback
ran. The attempt stopped at the pre-production input gate. **No production access
or modification; rollback neither needed nor performed.** No automatic retry.
Input receipt timestamp: `2026-10-01T19:55:41.559442+00:00`.

Attempts #1–#5 remain untouched in the
[historical report](2026-10-01-5n-prov1-production-restricted-provisioning.ru.md);
[attempt #6](2026-10-01-5n-prov1-attempt6.ru.md) remains its separate pre-production
HTTP-source mismatch stop. **Attempt #3 cause: UNKNOWN.** This attempt establishes
no new production failure cause.

## Pinned inputs and verification

Source HEAD: `f4c06df5f16593273b4c8bffa75646f1df17c2fb` — PASS, unchanged.

| Artifact | Exact path | SHA256 |
| --- | --- | --- |
| Sync | `state-client-build/directory-validation/final-sync-bundle/restricted-sync.pyz` | `cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f` |
| HTTP | `state-client-build/http-packaging-git-recheck/final-bundle/friends-http.pyz` | `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71` |

Both requested hash pins PASS. All17 sync and25 HTTP inventoried files match their
inventory hashes. Embedded source matches bundled source; no extra ZIP files beyond
the expected generated entrypoint. HTTP's mapped source/config/lock/harness inputs
all match the accepted Git HEAD. Sync has exactly one source mismatch:

| `control/friends/restricted.py` provenance | SHA256 |
| --- | --- |
| Pinned sync archive and bundled source | `9b5d5ce2b994dd5d89fe147536cccfd998b351c17673c4183eae7f9db05a011f` |
| Accepted HEAD, worktree and pinned HTTP archive | `ab3542b9f696c15a90211d7ff814f82de38cbb134b3b6287dc10af6a11513755` |

The only diff moves challenge field validation ahead of `from_env` and adds
public-identity/WireGuard-key input checks. It is the HTTP-specific hunk already
acknowledged in the [accepted packaging report](2026-10-01-5n-http-packaging-git.ru.md),
which explicitly retained the old sync bytes and tested directory compatibility.
This is **not** corrupt archive data, a new timestamp defect, or evidence that the
sync execution path fails. No functional compatibility failure is inferred.

Nevertheless, this deployment authorization separately requires inventory against
current accepted source and STOP on **any** mismatch. The pinned sync bytes and
exact-source equality cannot both pass for this module. The operator did not infer
an exception, rebuild either archive, substitute bytes, or change accepted HEAD.
The stricter input gate stopped the attempt before SSH/production inspection.
No production-contact requirement was allowed to bypass the prior pinning gate.

## Durable evidence and checks

Ignored local evidence root: `state-client-build/prov1-attempt7/`.

- `verify_inputs.py`: local read-only artifact/Git verifier; creates evidence only.
- `input-verification.json`: both pins, inventory and source comparisons; failure
  receipt is file-fsynced and parent-directory-fsynced before nonzero return.
- `sync-source-difference.patch`: exact source-only mismatch, likewise fsynced.
- `worktree-before.json`, `entry.patch`, `entry-*`: entry SHA256/bytes/diff ledger
  preserving all four pre-existing modified documentation files.
- `worktree-after.json`: final preservation, unchanged artifacts/HEAD/index and
  worktree ledger. No credentials, private identities, room URLs or proofs read.

Attempt #7 verification: SHA256, all inventoried bundle files, embedded-source
comparison and Git-blob comparison. No runtime tests or production acceptance were
run after the STOP; earlier274 HTTP/local tests and194 sync-acceptance tests remain
historical local evidence, not newly executed production gates. No version change.

## Requested live and physical gates

Every unperformed gate below is **NOT RUN / NOT VERIFIED**, never PASS.

| Requested gate | Attempt #7 result |
| --- | --- |
| Fresh CRL sequence/issue/expiry; gateway certificate expiry | Not refreshed or queried |
| Baseline receipts: ordinary status200, malformed400, safe ordinary established behavior, restricted disabled404 | No live baseline receipts; not probed |
| RU AWG/TCP, NL normal services, inactive restricted units, absent old HTTP drop-ins, provider.env root:root0600, rollback material, drift | Not queried |
| NL provider initialization, same gateway, bootstrap READY/seed count/restart stability/UTC-Z | Not run |
| Live Python directory validation/no issued_in_future | Not run |
| RU `python -I ... --check` | Not run |
| Full RU↔NL sync acceptance, oneshot success/inactive, fresh CRL/DB floor/current directory/final monotonic readback | Not run |
| Generic-shell rejection | Not run |
| Stale-CRL rejection | Not run |
| HTTP A — ordinary status200 | No attempt #7 receipt; not activated/probed |
| HTTP B — ordinary malformed challenge400 | No attempt #7 receipt; not activated/probed |
| HTTP C — safe ordinary route/challenge | No attempt #7 receipt; not activated/probed |
| HTTP D — restricted malformed challenge | No attempt #7 receipt; not activated/probed |
| HTTP E — real non-canary rejection | No attempt #7 receipt; not activated/probed |
| HTTP F — real owner restricted challenge | No attempt #7 receipt; not activated/probed |
| HTTP G — real owner readiness fetch200/valid response | No attempt #7 receipt; not activated/probed |
| Friends normal API, registrations/grants, sole owner canary/26 other devices restricted-denied | Not queried; no admissions changed by this attempt |
| Friends API downtime/observations | No restart/change by this attempt; no fresh uptime/health measurement |
| AWG/TCP health | No changes by this attempt; live health unverified |
| Redmi identity/normal/restricted provisioning | Phone untouched; no install, clear, activation or prewarm |
| BootstrapDirectory readiness/effective readiness expiry | Not queried; unknown |
| Restart persistence | Not run |
| Local restricted rehearsal | Not run |
| Android VPN/Chrome two controlled HTTPS sites/end-site TLS | Not run |
| Family DNS/concurrent TCP | Not run |
| Direct DNS leak/protected TCP bypass | Not measured; no verified scope and no zero-leak/bypass claim |
| Unsupported UDP/QUIC and IPv6 fail-closed | Not run |
| Underlay socket protection/short ordinary-use smoke | Not run |
| Final FIELD APK path/SHA/version/signature/native provenance | Not produced; prerequisite gates not reached |

## Final state, rollback and next boundary

No live rollback needed/performed because no live access/change occurred. This
attempt leaves production untouched; **actual current state was not freshly
observed**. Last historical rollout state is attempt #5 rollback, not a current
health assertion. No DB/CRL floors, authority/Family/issuer/gateway/canary, TTL policy,
provider material or ordinary Friends/AWG/TCP services changed by attempt #7.

Future authorized rollback must follow `deploy/friends/restricted/README.md`:
remove only additive restricted HTTP/ingress activation, stop restricted sync/NL
seed runtime, restore saved ordinary runtime/configuration, and preserve monotonic
DB/CRL history. No old full-DB restore and no unrelated production fix.

Remaining prerequisite is an explicit resolution of the exact-source/pinned-sync
conflict: accept the documented exact source difference as an exception, or
separately accept a matching artifact/source checkpoint and updated pins. Neither
is done or authorized implicitly here. A newly authorized attempt must repeat
baseline, JIT authority, NL bootstrap, RU check/full sync negatives, HTTP A–G, normal
regressions and physical gates in order; final FIELD APK remains conditional.

Pre-existing modifications in STATUS/PLAN remain byte-for-byte when this task's
additive notes are removed; historical PROV-1 and VPN-health reports remain entirely
byte-identical. Only STATUS/PLAN additions and this new report are task-owned tracked
changes. No evidence commit was made; index untouched. Final worktree: four original
modified documents plus this new untracked report. Private local receipts stay ignored.

**Push: no. Public Android release: no. Distributed beta: no. FIELD-1 started: no. STOP.**
