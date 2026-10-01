# 5N-HTTP-ARTIFACT-REFRESH — local provenance gate, 01.10.2026

## Result

**5N-HTTP-ARTIFACT-REFRESH = FAIL**

The required exact source commit contains the accepted nanosecond fix, but does
not contain the accepted HTTP packaging prerequisites. No new production HTTP
artifact was built. No source was changed, no main-worktree overlay was used,
and no retained uncommitted implementation was incorporated or committed.
This is not a failure of the accepted nanosecond fix.

## Clean exact source

- Requested/observed HEAD: `8663128a4ee433c29adb90340b8d4573ac2ba161`.
- Equivalent exact source view: `git archive` export to
  `/tmp/fc-http-refresh-8663128/source`, not a dirty checkout or copied worktree.
- All1569 exported tracked entries verified against Git blob IDs and executable
  modes; zero additional files. Symlink payloads checked as Git blob content.
- After local tests, every exported content SHA256 was rechecked and no extra
  files were present. Python bytecode/pytest cache writes were disabled; synthetic
  test state remained outside the source view. No new branch/worktree registration.
- Main worktree entry was8 modified/7 untracked files; all15 paths/hashes recorded
  before investigation. Only additive STATUS/PLAN notes and this new report are
  task documentation changes; unrelated files are not changed.

## Blocking packaging facts

The following paths are absent from the exact committed source:

- `scripts/package_friends_http.py`
- `deploy/friends/restricted/http-runtime-files.json`
- `deploy/friends/restricted/http-runtime.conf`
- `scripts/friends_http_acceptance.py`
- `tests/test_friends_http_runtime.py`
- `tests/test_friends_http_evidence.py`

In addition, committed `deploy/friends/access-api.py` has no `main()` entrypoint
used by the accepted HTTP zipapp builder. It unconditionally prepends
`/opt/apps/family_connect/friends-access/app` to `sys.path`, and lacks the packaged
`--root`/`--port` configuration entrypoint. Those changes exist only in the retained
main-worktree diff. The accepted builder's `friends_http:main` contract cannot be
satisfied by silently calling this code a clean HEAD build.

The retained tools/tests were inspected to identify the discrepancy, not executed
or imported as build inputs. No ad-hoc replacement builder/wrapper or source
patch was invented to bypass the source pin or hidden-fallback requirement.
Source fixes would require a new accepted commit and therefore could not honestly
retain the requested exact HEAD provenance. Existing work was not staged.

## Accepted precision behavior independently verified

`control/friends/restricted.py` at HEAD has SHA256
`9b5d5ce2b994dd5d89fe147536cccfd998b351c17673c4183eae7f9db05a011f`.
`timestamp_ns` accepts offset-aware RFC3339/UTC-Z with up to9 fraction digits.
The two BOOT-1 checks in `RestrictedReadiness.fetch` sample
`clock_nanoseconds(self.access.clock)`, not integer-second time. RU sync samples
the precise clock after receiving the directory; NL gateway's default directory
validation uses the current nanosecond clock. Existing whole-second certificate,
grant and challenge TTL handling remains unchanged; it is not the directory clock.
`provisioning/friends_catalog.py` is the ordinary schema2 parser/signature/binding
validator and supplies strict parsing helpers; it has no BOOT-1 time truncation.

**59 targeted committed tests PASS (0.26s)** from the exact export: live-shape
rounding reproduction; ±1ns/future/expiry bounds; malformed/private-safe category
checks; precise default clock; gateway→delivery; simulated RU receive; valid and
invalid offset-aware timestamps. No sync artifact was rebuilt by these selections.
These source tests are explicitly **not** acceptance of a new HTTP artifact.

Runtime: `/tmp/fc-boot1-venv/bin/python`, Python3.14.4. Every installed package
specified by both committed `control/requirements.lock` and
`device_identity/requirements.lock` matches its pinned version. Full safe Python,
OpenSSL/platform and package provenance is retained in the local receipt.

## Reference archives and old failure reproduction

Old HTTP SHA256:
`eb9eb06fd38a0ec498445877fcfb5908a8566b96c7a25f44e2a4619170743a2f`.
Its embedded restricted module SHA256:
`c63c1eca5d553f3d4e5fcd63aee9cd8a27b73c3f50466fe8df8cc0edb95327c9`.
It does not match HEAD. The old archive is **retired as a production candidate**;
the immutable bytes are preserved only for reference, not reused for a new build.

Unchanged sync SHA256:
`cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f`.
Its embedded restricted module matches HEAD byte-for-byte.

Read-only copies of these archives were probed from outside the checkout with
`python -I -B`, no PYTHONPATH/PYTHONHOME, and explicit archive-only module loading.
The probe asserts the imported module comes from the selected archive and no
repository path is present in the interpreter search path. On the committed
synthetic291-byte attempt-#4-equivalent fixture, the **old embedded HTTP consumer
rejects** valid fractional issuance under the old truncated caller clock, whereas
the **embedded sync consumer accepts** the precise observation. Only safe fixed
outcome classifications are recorded. This directly exercises archive code, but
is not a new HTTP handler startup, HTTP delivery test or complete cross-component
NL→sync→new-HTTP fixture; there is no new HTTP artifact.

## Required gate ledger

| Gate | Result |
| --- | --- |
| Exact clean HEAD source view | PASS,1569 entries, no overlay |
| Accepted directory precision fix in source | PASS,59 tests |
| Fresh HTTP archive / SHA / path / inventory count | Not produced; unavailable |
| New bundled restricted.py/all inventory match | Not run; no new archive |
| Isolated new HTTP startup/config/import closure | Not run; prerequisites missing |
| HTTP A200/B400/C established/D bounded4xx/E403/F200/G200 | All NOT RUN on a new artifact |
| Unrelated/additive routes, shadowing, trailing slash/method | Not run on a new artifact |
| Old artifact mismatch/rejection demonstrated | PASS, embedded-code probe |
| New HTTP artifact nanosecond/future/malformed regression | Not run; source tests are not a substitute |
| issued_in_future recurrence in new HTTP | Not assessed; no new artifact |
| Durable HTTP harness/matrix/failure-before-rollback/no payload leak | Not run; harness absent from HEAD |
| Sync accepted SHA unchanged | Yes; no rebuild |
| NL→sync→new-HTTP readiness fixture | Incomplete; sync fixture alone PASS |
| New artifact secret guard | Not run; no new artifact |

No production OAuth/provider/issuer/device secret was accessed. Test-generated
identities are synthetic and remain in temporary test state; none was packaged or
included in documentation/evidence receipts. New-artifact secret safety is not
claimed without an actual artifact to inspect.

## Attempt #6 and stopping boundary

[Attempt #6](2026-10-01-5n-prov1-attempt6.ru.md) remains stopped before production
because the HTTP source mismatch was detected by preflight. No production change
or rollback happened then; this local task does not rewrite attempts #1–#6.
Historical attempt #3 cause remains **UNKNOWN**.

Further preparation requires reviewed/accepted HTTP packaging prerequisites and
an explicitly updated source pin, followed by all requested build/matrix/receipt/
precision/cross-component/secret gates. That is not performed automatically here.
No new deployable pin is available and the old one must not be used for attempt #7.

Durable safe evidence: `state-client-build/http-artifact-refresh-8663128/` contains
entry/final worktree receipts, exact-source inventory, provenance-gate receipt,
runtime provenance, source-test log and the local audit script. Files and evidence
directory are fsynced. No private fixtures/keys or raw response bodies are included.
Source/probe files are additionally retained under `/tmp/fc-http-refresh-8663128/`.

Commits:none; push:no. Production access/change:no. Credential refresh:no.
Services started:no. Redmi:no. Distributed beta/FIELD-1:no. **STOP; no attempt #7.**
