# 5N-HTTP-PACKAGING-GIT — local checkpoint, 01.10.2026

## New-session recovery revalidation

Actual starting HEAD: `d8624dea2cffe3c41d9d136a6f93ee527b8f3812`. Git log and
reflog confirm that `f7b3b6c29526fb600990f60d57449571a8538f22` and the accompanying
documentation commit already completed the requested checkpoint. The expected
8663128 is their ancestor, not the current HEAD. Existing implementation, reports
and evidence were reviewed; no duplicate feature commit, amend or source redesign.

Entry worktree has exactly four modified files, no untracked files or staged work:
STATUS's two VPN snapshots, PLAN's VPN audit, the VPN-health report and the long
PROV-1 report's historical attempt-#5 addition. All are class D retained work;
there are no remaining A/B task-owned sources or E uncertain paths. Safe original
file SHA256 values and the exact entry diff were captured before edits under
`state-client-build/http-packaging-git-recheck/`. Only the new revalidation notes
in STATUS, PLAN and this report are class C and eligible for the new docs commit.
The two unrelated reports remain byte-identical; mixed-document retained hunks
are checked against their entry bytes after removing only these added notes.

A fresh Git archive of the actual entry HEAD contains1578 tracked blobs, verified
against Git without untracked inputs/dirty overlay. Independent rebuild matches
the accepted25-entry inventory and HTTP SHA256
`460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
No source correction is necessary: packaged `friends_http:main` is isolated;
external app-path insertion remains guarded for direct legacy-script execution
only, never the production zipapp. Both dependency lockfiles remain unchanged.

Fresh clean-source suite: **274 PASS, no skips,48.72s**, using the supplied rebuilt
bundle, synthetic loopback nginx/TLS, pinned sync archive and offline Go toolchain.
The sandbox denied socket creation; the passing run used approved local execution
outside the sandbox, not production/system services. A–G remains200/400/400/400/
403/200/200; additive routes, signed readiness, fsync-before-verdict, process exit,
SIGTERM, shell EXIT trap and simulated failure/rollback receipts all PASS.

Additional isolated embedded-code probes use the committed synthetic production-
shape nanosecond fixture: retired old HTTP rejects under its truncated clock;
new HTTP accepts without issued_in_future. Future+1ns is rejected with that exact
predicate; four malformed timestamp variants are rejected as invalid_timestamp.
Equivalent +02:00 input normalizes to identical UTC Z output. No timestamp tolerance
or TTL/schema policy changed. Existing sync SHA256 remains
`cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`;
the same-directory sync-validation→HTTP-readiness fixture passes without rebuilding it.

Final post-documentation candidate path:
`state-client-build/http-packaging-git-recheck/final-bundle/friends-http.pyz`.
The exact new source HEAD is recorded in `final-artifact.json` in that evidence
directory (a commit cannot embed its own hash). Final rebuild/tests/embedded probes
are repeated from a fresh Git export of that HEAD, never the dirty main worktree;
see `final-tests.log`, `final-nanosecond.json` and `final-verification.json`.
Original `http-packaging-git/` evidence and bundles are retained unchanged.

Attempts #1–#5 remain historical rollbacks; #3 HTTP cause stays UNKNOWN. Attempt #6
stopped before production on stale HTTP source pin, without runtime changes.
No access to production hosts, credential refresh, system service start/reload,
physical Redmi, APK/release, push, attempt #7, beta or FIELD-1. No rollback needed
here. Future authorized rollout still requires current authority/JIT, pinned
artifacts, live negative checks and physical acceptance; scoped rollback must
preserve monotonic DB/CRL history. **STOP after local Git/artifact acceptance.**

## Scope and source checkpoint

Previous HEAD: `8663128a4ee433c29adb90340b8d4573ac2ba161`.
Reviewed code/tests commit:
`f7b3b6c29526fb600990f60d57449571a8538f22`
(`feat(friends): package restricted HTTP runtime for isolated deployment`).
The accompanying documentation commit preserves the identical runtime inputs.
Final handoff's `final-artifact.json` records the exact combined HEAD verified by
a fresh complete Git export, not a dirty checkout or an untracked source overlay.

The missing tracked prerequisites were the builder, explicit manifest, production
drop-in, durable receipt operator and HTTP runtime/evidence tests. The handler's
`main()`/configurable root+port and import isolation were also uncommitted.
These were reviewed and committed, not replaced with a new architecture.
No protocol/authority/admission/TTL policy, version, catalog or public release changed.

## Worktree classification and preservation

All16 initial modified/untracked files had safe path/SHA256 snapshots and local
original-byte backups before edits. No uncertain paths were staged.

| Class | Files/sections | Disposition |
| --- | --- | --- |
| A: packaging/runtime | restricted challenge validation, access-api entrypoint, manifest/drop-in, builder | Code commit |
| B: acceptance/receipt | durable harness, two HTTP test modules | Code commit |
| B: HTTP CI | all actual control.yml diff: HTTP triggers, nginx installation/environment | Code commit; no unrelated workflow experiment found |
| C: corresponding docs | runbook, STATUS/PLAN non-VPN sections, attempt6/failed-refresh reports, this report | Documentation commit only |
| D: unrelated | VPN-health report, both STATUS VPN snapshots, PLAN VPN audit update | Preserved byte-for-byte/hunk-for-hunk and unstaged |
| D: historical sync evidence | uncommitted attempt5 addition in the long PROV-1 report | Entire file untouched and unstaged |

Partial documentation staging constructs the index version without the retained
VPN sections; it does not remove or overwrite those sections in the worktree.
No broad add/reset/restore/stash, no amendment of prior history. Generated bundles,
test credentials and private state are excluded from Git. Final index is empty;
remaining dirty hunks are the explicitly retained D work, not HTTP source inputs.

## Code review and minimal additions

- The builder packages only16 listed module sources plus the handler, generated
  zipapp entrypoint and namespace directories; it never copies the whole checkout.
  Manifest path safety, existing-output refusal and symlink-source checks remain.
- ZIP entries have deterministic order, timestamps and modes. A regression changes
  copied-file timestamps and proves identical full output inventory/archive hashes.
- `friends_http:main` runs with `python -I`, configurable synthetic-test root/port and
  production defaults. The archive does not inject `/opt/.../app` or use PYTHONPATH.
  The direct legacy script retains its guarded app path only when run as that script;
  it is not the isolated deployment entrypoint. Missing-module tests cannot recover
  through a supplied repository PYTHONPATH in isolated mode.
- Malformed restricted challenges are bounded400 even before missing config lookup;
  ordinary handler routing is unchanged. Properly shaped unconfigured restricted
  requests remain503. The accepted nanosecond fix is included unchanged.
- Receipts use owner-only files/directory, file fsync→rename→directory fsync before
  verdict. Only fixed safe probe/status/transport/classification/generation metadata
  is written, never identities, proof, response content, room URL or token.
- Added artifact-level nanosecond valid/future/malformed HTTP delivery tests and
  pinned-sync directory-check→same-directory HTTP readiness test. They use generated
  synthetic identities only. Test clock injection lives in tests, not runtime flags.

The receipt CLI covers A–F and checks all26 non-canaries by default. G requires a
real private-key proof and remains separate in production; local tests generate
synthetic proof and exercise readiness fetch200 through the packaged handler.
Do not confuse local G coverage with physical owner acceptance.

## Candidate and reproducibility

Working-source review candidate (not itself a deployment provenance pin):
`state-client-build/http-packaging-git/working-bundle/friends-http.pyz`.
Clean code-commit rebuild:
`state-client-build/http-packaging-git/code-bundle/friends-http.pyz`.
Final clean-HEAD candidate after documentation finalization:
`state-client-build/http-packaging-git/final-bundle/friends-http.pyz`.

All use SHA256
`460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`
when the verified inputs are unchanged. Final handoff requires the last artifact's
fresh inventory/provenance/test receipt, not mere equality with a working build.
Inventory count25:24 explicit module/config/lock/harness inputs plus the archive.
Every source input is compared to the corresponding Git blob at the recorded HEAD;
every embedded module equals the inventoried source bytes. Generated `__main__.py`
is the standard builder entrypoint, not a hidden source overlay.

Bundled `control/friends/restricted.py` SHA256:
`ab3542b9f696c15a90211d7ff814f82de38cbb134b3b6287dc10af6a11513755`.
It includes both committed nanosecond directory delivery and accepted challenge
input validation. Sync archive still has the prior challenge ordering, but shares
the exact accepted directory/time contract; no sync rebuild is needed.
Sync SHA256 remains
`cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`.
Old HTTP SHA256
`eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`
is retired and retained unchanged, never silently replaced.

## Validation

Working source: **274 PASS**, no skips,65.97s. Exact supplied candidate tested with
HTTP runtime/evidence, Friends restricted/access/chat/catalog, directory validation,
restricted runtime and sync acceptance suites. FC_TEST_GO enables the native
compatibility fixtures; FC_TEST_NGINX enables real isolated nginx rather than skips.
The isolated clean-code-commit HTTP suite is **45 PASS**, no skips,22.20s, including
all mandatory local matrix/precision/receipt/sync gates. Its results and a repeat
against the final documentation HEAD are retained for each clean rebuild.

| Gate | Required local result exercised by tests |
| --- | --- |
| A ordinary status | 200; static route remains healthy when backend unavailable |
| B ordinary malformed challenge | 400 |
| C safe ordinary chat challenge | 400; valid ordinary challenge and activation also200 |
| D restricted malformed challenge | 400 enabled;404 with ingress disabled |
| E synthetic non-canary | 403 enabled |
| F synthetic canary challenge | 200 with bounded challenge shape |
| G synthetic signed readiness fetch | 200; precise directory, revision/CRL/expiry metadata |
| Route boundaries | Unknown/trailing-suffix404; wrong-method405; restricted routes additive |
| Nanosecond artifact regression | Same-second valid issued_at accepted; issued_at +1ns future and malformed seed rejected503 |
| Isolated imports/startup | Outside source tree, python -I, no external app path/fallback; configuration loads |
| Receipt durability/privacy | File+directory fsync; fatal persistence errors; nonzero/hard exit/SIGTERM/EXIT trap retain redacted receipts |
| TLS | Wrong trust rejected; synthetic trusted HTTPS gate passes |
| Sync→HTTP | Accepted pinned archive validates synthetic NL directory; packaged HTTP delivers that same directory |
| Source/secret guard | Exact allowlist and Git/inventory/embedded-byte matches; no key material/token/live URL/state payload |

Python3.14.4, pytest9.1.1, cryptography46.0.7, RNS1.5.1; both committed dependency
lockfiles match the retained venv. Local nginx1.28.0 uses the retained musl loader.
The nginx binary/venv are test dependencies, not HTTP source overlays or archive
contents. Production retains its supported lockfile venv layout.

Initial sandbox test attempt could not create loopback sockets (EPERM); tests were
rerun with approved outside-sandbox execution, still only local synthetic data.
An initial new test used Decimal for global time.time(), breaking HTTP date headers;
corrected to a float wall clock plus exact integer time_ns before the passing run.
No production fix/retry or relaxed acceptance predicate was involved.

## Evidence, security and stop

Safe durable evidence under `state-client-build/http-packaging-git/`: classification,
before/final preservation snapshots, candidate/clean/final artifact receipts,
test logs and final provenance. Scratch/clean source exports are retained under
`/tmp/fc-http-packaging-git/`. Synthetic private fixtures stay outside bundle/Git;
no provider.env, OAuth, issuer/gateway/device private key or live room was read.
Secret/path guards cover the new committed changes and archive; they are not a
claim to have audited every pre-existing historical Git object for secrets.

Attempts #1–#6 are preserved; attempt #6 remains a pre-production source-mismatch
stop, and attempt #3 historical cause remains UNKNOWN. Last production state is
only the previously documented rollback, not freshly checked in this local task.
No rollback needed/performed here. Any future explicitly authorized rollout must
re-pin the clean artifact and follow the existing JIT/baseline/NL/RU/negative/HTTP/
physical acceptance order and scoped rollback, preserving monotonic history.

No production access/change, credential refresh, installed/public version change,
service deployment, Redmi operation, APK, distributed beta or FIELD-1. **Push:no.
STOP; do not start attempt #7 automatically.**
