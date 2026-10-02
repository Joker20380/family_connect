# 5N-HTTP-READINESS-ADAPTER-PACKAGING — 02.10.2026

**5N-HTTP-READINESS-ADAPTER-PACKAGING = PASS.** Local packaging/runtime/observability
only. No production connections, authority renewal, NL/RU service operation, Redmi,
live Telemost, main-artifact rebuild, public release, push or deployment attempt14.

## Source and exact diagnosis

Starting HEAD: `4bb53b0605c2c898b6a3feca6ee15fd34b943a94`.
Fix/build source: `037331f8aee029e22312b565f5d025d50f284e0b`, subject
`fix(friends): package candidate readiness adapter as closed runtime`.
The subsequent documentation-only checkpoint does not change any adapter input.
Existing unrelated tracked/untracked work was snapshotted and preserved; only task
additions to STATUS/PLAN are staged, not their earlier uncommitted history.

Before the first source edit, retained attempt13 operator/transition/acceptance/recipe
bytes were reconstructed and verified against their recorded SHA pins. Its exact
`fixture()` function was invoked without service/authority/device actions using the
original isolated import behavior. Safe evidence:
`state-client-build/http-readiness-adapter-packaging/reproduction.json`.

- Entry: `http_operator.py:121`, `runpy.run_path(BASE / 'fixture_recipe.py')`;
  recipe line7 imports `control.friends.restricted`.
- Exception: **ModuleNotFoundError**, exact missing module **`provisioning`**.
- Transitive importer: **`control.friends.restricted`**, line21,
  `from provisioning.friends_catalog import fields, key, parse, require`.
- Earlier `runpy.run_path(friends-http.pyz, run_name='__main__')` with `--help`
  temporarily supplied the archive as an import root, then removed it. Cached
  `control.friends.__path__` still resolved the restricted module, but the first
  top-level `provisioning` import could not find the removed archive root.
- The unchanged HTTP artifact contains `provisioning/__init__.py` and
  `provisioning/friends_catalog.py`. This is **B + D**: accidental extracted-test
  recipe dependency and a concrete outer-adapter import-layout defect, not an
  absent module in the HTTP service artifact.

Original invocation was the Friends venv Python with `-I`, operator under the
retained staging backup, candidate artifact in its sibling `http-candidate`,
candidate endpoint127.0.0.1:18086. Failure occurred before fixture HTTP/direct B–E.
Replay retained the original operator import roots and byte-identical modules;
no production credentials/configuration were loaded. Search roots recorded in the
receipt are operator directory, stdlib ZIP/stdlib/lib-dynload and locked venv
site-packages, **not the HTTP archive** after `runpy` returns. A second regression
repeats this boundary in a fresh `python -I` process outside the repository.

The production minor Python version and cwd were not captured during the failed
live attempt; do not invent them. The reconstructed layout uses an isolated local
staging cwd and Python3.14.4. Operative import/layout behavior and pinned deployed
bytes are reproduced, not an assertion of bit-identical production host/OS.

Previous full-checkout tests preloaded producer modules or resolved checkout roots.
The standalone transition-loader test checked exports only, not the later recipe
after the HTTP archive disappeared from sys.path. Those tests masked the unclosed
operator. New subprocess tests cannot borrow pytest imports or checkout paths.

## Runtime decision and artifact

Use the existing transaction/Session contracts, not a new deployment architecture.
`control.friends.readiness_fixture` is the supported disposable runtime helper;
no test imports/extracted recipes. The stable ZIP root includes all13 Python source
dependencies. The stdlib bootstrap catches runtime import failures before return.
The native public-input wrapper reuses accepted `wholedevice.ValidateDelivery`;
no owner proof interface or new crypto/admission policy is introduced.

Final artifact:
`state-client-build/http-readiness-adapter-packaging/final-bundle-v2/candidate-readiness.pyz`

SHA256: `f7827aeed45cb508bc3499bf9f7b31a4d5dfcd99ba9a0eab1e613150c717d929`.
Native checker SHA256:
`39c50ce56fd54e52c0d74e052b09bf73ba9b88eff4cad0626c36beb53a62be35`.
Inventory: **13 Python sources /14 hashed ZIP payload files** including lock;
embedded inventory is additional metadata. Native source inventory36 tracked files;
104 non-stdlib Go package dependency entries, locked by existing go.mod/go.sum.
Python3.14.4; Go1.26.0 linux/amd64, CGO0. Existing Python lock:
rns1.5.1, cryptography46.0.7, cffi2.1.1, pycparser3.0, pyserial3.5.
No production pip install; no PYTHONPATH or sys.path modification workaround.

Two clean Git exports produced identical bytes for all four files: ZIP, native
checker, lock, provenance. The first clean-export builder run exposed an ancillary
Go inventory VCS-stamping requirement; it failed locally before completing a bundle.
`go list -buildvcs=false` and clean-export regression fixed it before final build.
The incomplete first directory is retained as evidence, not an accepted artifact.

## Final isolated acceptance

The committed final bundle was copied into an external `/tmp/.../opt/apps/
family_connect/http-operator` tree alongside the accepted HTTP archive. Fresh
`python -I`, non-checkout cwd, exact locked packages; deliberately poisoned
PYTHONPATH is ignored. No repository/test modules in runtime search roots.

| Gate | Result |
| --- | --- |
| Startup/import + configuration + inventory/pins | PASS |
| B ordinary malformed | 400 |
| C established safe ordinary challenge | 400 |
| D restricted malformed | 400 bounded rejection |
| E synthetic non-canary contract | 403 rejected |
| F controlled challenge semantics | 200 PASS |
| G controlled delivery/native crypto | 200 PASS |
| Owned local18086 fixture candidate B–E | 400/400/400/403 PASS |
| Pinned isolated sync --check on disposable authority | PASS, no network |
| Transaction callback / generation binding | PASS, direct only |
| Real owner F/G | NOT RUN; never claimed |

F/G receipt class **`server_contract_fixture`**; `owner_product_ready=false`.
No direct static/nginx status request. Serialized≥1.1s probes, no retries.
The candidate-mode test listener/state are entirely synthetic/local, not production.
Redacted durable final receipts retained under
`state-client-build/http-readiness-adapter-packaging/final-receipts/`.

Future import failures persist step, class, missing module, importing module,
safe file/line stack, import classification, archive digest, cwd/search roots,
isolated flag, Python version and redacted argv shape. No exception message/locals,
source text, credentials, proofs, private identity IDs or response bodies. Owner-only
exclusive files, file/directory fsync; reused evidence/storage failures cannot PASS.
Missing `__main__` cannot run a receipt writer: pre-execution artifact pinning and
the caller's durable failure event cover that bootstrap boundary.

No embedded private keys/credentials/OAuth/provider.env/live room fixtures. Only
fresh synthetic authority/identities in disposable private state are used for F/G;
never production owner key access or proof construction. Temporary fixture stops
on completion/failure and deletes that state.

## Tests and preserved artifacts

Final focused run: **74 PASS,9 explicitly deselected,0 skips**; JUnit saved as
`state-client-build/http-readiness-adapter-packaging/final-tests.xml`.
Includes30 packaging tests plus44 existing owner-handoff/transition unit guards.
Every one of13 required manifest Python files removed in turn fails startup or
inventory; removing the entire proven `provisioning` package records the exact
ModuleNotFoundError/importer. Tests cover redaction/storage failure/reuse, candidate
callback timeout/wrong generation/nonzero/missing receipt, clean-export/repeat builds,
controlled B–G/native crypto and local candidate mode. Nine unrelated historical
nginx/live-switch or duplicate artifact-building fixture cases were deselected;
no claim of running the full repository suite. `py_compile` and `git diff --check`
PASS. No Android build or public network test.

Accepted artifacts **unchanged, not rebuilt**:

- Sync SHA256 `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`;
  all17 inventory entries valid and source-compatible with the fix commit.
- HTTP SHA256 `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`;
  all25 inventory entries valid and source-compatible with the fix commit.
- Canary54 APK SHA256 `f81920412089bd87950d8055daf883b754fea3323b412ccb28b0c092b9a909c6`;
  file bytes unchanged. No new package/signature/device observation claimed.

## Final boundary

Task-owned fix and documentation only committed; unrelated work retained, index
empty after finalization. No push. Production changed: **no**. No runtime rollback
needed for this local task. Last documented production state remains resumed
attempt13 rollback with normal service restored/restricted disabled and monotonic
CRL23 retained; it was **not rechecked** here. The earlier no-device stop remains
a pre-production block, not retrospectively reclassified as a production failure.

PROV-1 owner prewarm/import/restart/rehearsal/browser/DNS/TCP/fail-closed gates remain
unproved and require separate authorized production/physical execution. This report
does not extend validity, grant admission, retire old HTTP or authorize attempt14.
STOP. No DIAG-1, distributed/regional beta or FIELD-1.
