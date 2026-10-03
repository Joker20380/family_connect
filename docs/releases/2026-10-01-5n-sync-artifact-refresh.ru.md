# 5N-SYNC-ARTIFACT-REFRESH — local artifact and provenance, 01.10.2026

## Result and scope

**5N-SYNC-ARTIFACT-REFRESH = PASS**

Local artifact/provenance task only. No production access/change, credential refresh,
system-service operation, Redmi, APK, commit or push. Source HEAD remains
`f4c06df5f16593273b4c8bffa75646f1df17c2fb`. No exact-source exception or waiver.

[Attempt #7](2026-10-01-5n-prov1-attempt7.ru.md) remains historically unchanged:
stopped before production; HTTP source pin PASS; old sync internal17-entry inventory
PASS; one exact-source mismatch in `control/friends/restricted.py`; no production
access/change and no rollback required/performed. That mismatch was not evidence
of a sync runtime defect. Attempts #1–#6 are untouched; attempt #3 cause **UNKNOWN**.

## Dependency audit and manifest decision

**Classification A: required runtime dependency.** The real zipapp entrypoint runs
`control.friends.restricted_sync:main`; sync imports `DirectoryValidationError`,
`bounded_file`, `clock_nanoseconds`, `delegation`, `directory`, `from_env`, `iso`
and `utc` from `restricted.py`. The CRL publisher in `restricted_admin.py` also
imports its authority/trust helpers. Removing the module prevents CLI startup.

Real-entrypoint `python -I` tracing was run from an unrelated `/tmp` working
directory with PYTHONPATH/PYTHONHOME absent. All10 manifest modules load from the
zipapp itself, not the checkout or bundle's adjacent `app/` directory. Full loaded
module origins are retained; non-archive origins are limited to the interpreter's
standard-library/locked-venv library roots. Both dependency lockfiles match the
venv, including cryptography46.0.7 and RNS1.5.1. Python3.14.4, pytest9.1.1.
No Reticulum daemon or network instance was started.

Observed first-party edges:

- `restricted_sync` → `access`, `restricted`, `restricted_admin`, `friends_catalog`.
- `restricted_admin` → `access`, `restricted`.
- `restricted` → `access`, `device_identity.device`, `friends_catalog`.
- `access` → `device_identity.device`.
- `friends_catalog` → `clients.desktop.profile_config` (standard-library-only parser).
- Package `__init__.py` entries are loaded package scaffolding, not extra application
  implementations. Desktop GUI/backend and ordinary HTTP runtime are not bundled.

Seven removal-negative probes each remove one non-`__init__` module from a scratch
copy; every real isolated entrypoint fails with ImportError/ModuleNotFoundError.
This includes `restricted.py`. The smallest existing closed module manifest is
therefore retained; no broad-copy fallback, dead-module retention, source exception,
manifest edit or production redesign is needed.

## Clean source and immutable candidate

Fresh source view: `/tmp/fc-sync-artifact-refresh/source`, exported using `git archive`
at exact accepted HEAD. All1578 tracked blobs and modes verified; no untracked input
or dirty overlay. The committed `scripts/package_restricted_runtime.py` runs with
`python -I` from `/tmp/fc-sync-artifact-refresh/run`. Only its explicit allowlist is
packaged; the full source export is not the runtime bundle.

| Artifact | SHA256 |
| --- | --- |
| Old sync, retained unchanged | `cb6f050ec49ee4b65fa65c5327e32d6271d714ef6f8e695f16cb3c85b60f386f` |
| New sync | `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d` |
| Current HTTP, unchanged/not rebuilt | `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71` |

New artifact: `state-client-build/sync-artifact-refresh/bundle/restricted-sync.pyz`.
Inventory: adjacent `sha256.json`,17 entries. Ten Python source entries, three
unit/helper templates, two dependency locks, one manifest and the archive itself.
Every tracked input is byte-identical to its Git blob at the accepted HEAD; every
embedded source member is byte-identical to the inventoried source.

Exact tracked Python module list:

```text
control/friends/__init__.py
control/friends/access.py
control/friends/restricted.py
control/friends/restricted_admin.py
control/friends/restricted_sync.py
device_identity/__init__.py
device_identity/device.py
provisioning/__init__.py
provisioning/friends_catalog.py
clients/desktop/profile_config.py
```

The only additional Python member is the builder-generated `__main__.py`.
No extra ZIP files. No claim of byte-reproducible future sync builds: the accepted
sync builder uses zipapp metadata without the HTTP builder's normalization. This
task pins and validates these exact retained bytes; it does not silently rebuild
them for deployment. Builder/source modernization is outside this task.

## Validation

**194 committed tests PASS, no skips,33.23s**, from the clean source view:
`test_sync_acceptance.py`, `test_restricted_runtime.py`,
`test_directory_validation.py`, `test_friends_restricted.py`,
`test_friends_http_evidence.py`. Go/native contract fixtures ran with the cached
Go toolchain, GOPROXY/GOSUMDB off; no dependency download or production access.

**7 additional exact-archive checks PASS, no skips,4.84s.** Old/new archive tests
use byte-verified copies, not a replacement build. They exercise:

| Gate | Result and boundary |
| --- | --- |
| Isolated startup/imports | Four committed CLI help smokes PASS; real entrypoint origins traced |
| `python -I ... sync --check` | PASS for both pinned archives from outside checkout, no PYTHONPATH, no authority/DB/file mutation |
| Blocking sync start | Real isolated sync CLI returns synchronously; SSH replaced by local gateway CLI |
| Oneshot completion semantics | Committed operator requires success/inactive/dead; systemd state/reload simulated, no real systemctl |
| Fresh signed CRL/current directory | Actual synthetic CRL1→2 and signed trust validation PASS |
| DB floor agreement | Actual SQLite floor2 equals CRL2 |
| Generic-shell rejection | Exact bundled forced wrapper rejects `id` with126 and empty stdout before exec/SSH |
| Stale-CRL rejection | Actual pinned gateway CLI rejects original CRL1 after accepting2, exit1/empty stdout |
| Final monotonic readback | Actual committed operator snapshot confirms unchanged final state; no rollback |
| Timeout/receipt regressions | Fast/slow success, mandatory timeouts, late/background completion, missing/invalid readback, negatives, total budget, fsync failure, interruption and exit-trap persistence covered |
| Attempt #4 live-shape fixture | Committed redacted291-byte shape accepted by each embedded validator at precise observed nanosecond time |
| Offset/canonical UTC Z | Equivalent RFC3339 +02:00 input normalizes to identical UTC Z |
| Nanosecond/future/malformed | Valid same-second issuance accepted; future+1ns rejected; four malformed variants rejected; native expiry/issuance edges covered |
| False issued_in_future | No recurrence on valid precise-clock input; intentional future-input rejection remains |
| New sync→current HTTP | Exact new archive validates synthetic NL-shaped directory; unchanged HTTP accepts synthetic canary challenge/proof and returns200 with identical directory/revision/CRL floor |

The complete exact-archive operator sequence uses the **unchanged committed**
`scripts/restricted_sync_acceptance.py`. Only host systemd/SSH boundaries are replaced
by local test callbacks. Actual archive publisher, CRL crypto, SQLite, gateway CLI,
forced-shell wrapper, snapshots and durable operator receipts execute locally. No
skipped negative gate; no journal prerequisite. This is not production acceptance.

The existing committed HTTP interoperability test hardcodes the old sync hash. It
was not edited to waive that pin. The new archive is tested by a separate local
fixture using the committed HTTP fixture and exact unchanged HTTP artifact. HTTP
builder is not invoked. All fixture identities/keys are synthetic and remain outside
the artifact/Git; no real owner proof or live room is used.

Initial sandbox candidate run:6 PASS, HTTP fixture denied loopback socket creation
(EPERM). Approved outside-sandbox local rerun:7 PASS. Two initial evidence-helper
issues were corrected before audit PASS: copying mutable ZipInfo objects while
constructing deletion-negative scratch archives, and accepting ImportError as well
as ModuleNotFoundError for a missing namespace child. Neither changed candidate
bytes, production code or acceptance predicates. Synthetic failed-run evidence is
retained; no failed production run is being relabeled.

## Old versus new and security

Inventory additions/removals: **none**. Changed entries: only
`app/control/friends/restricted.py` and `restricted-sync.pyz`.

- Old shared module SHA256:
  `9b5d5ce2b994dd5d89fe147536cccfd998b351c17673c4183eae7f9db05a011f`.
- New/current HEAD module SHA256:
  `ab3542b9f696c15a90211d7ff814f82de38cbb134b3b6287dc10af6a11513755`.
- The source change moves HTTP challenge field checks ahead of environment loading
  and adds key validation. ASTs are identical after excluding the HTTP `request`
  function. Shared sync/authority/directory implementation and all other source
  entries remain identical.
- Old/new exact-archive tests support unchanged behavior for the tested sync/check/
  publisher/gateway/negative/directory paths. This is **not purely ZIP metadata or
  provenance relabeling**: a real HTTP helper source change is incorporated. No
  unqualified behavior-identity claim for every callable in the module.

Secret/content scan PASS: exact source/member allowlists plus checks for private-key
PEM, token patterns, credential literals and concrete Telemost room URLs. No
provider.env, OAuth token, issuer/gateway/device private material, live-room fixture
or private receipt is packaged. No production material was opened. This is a bounded
artifact scan, not an audit of all historical Git objects or all possible secrets.

Old sync is now **retired as a deployment candidate**; bytes/inventory remain
untouched for history and old/new tests. No artifacts are uploaded or distributed.

## Evidence, preservation and next boundary

Evidence: `state-client-build/sync-artifact-refresh/` (ignored/local).
`clean-source.json`, `artifact-audit.json`, `new-import-trace.json`,
`full-import-trace-final.json`, both test logs/JUnit files, source-only helper scripts,
before/final preservation ledgers and the pinned bundle. Verification receipts and
final evidence manifest are fsynced. Temporary synthetic test state stays under
`/tmp/fc-sync-artifact-refresh/`, never in source/bundle/Git.

All five entry dirty files/hunks preserved: STATUS/PLAN after removal of only this
task's additive notes; historical PROV-1, VPN-health and attempt-#7 reports remain
byte-identical. New task changes are additive STATUS/PLAN/runbook notes and this
report. No runtime source, manifest, release version, package or catalog changed.
No commits; index unchanged; no push. Production untouched, no rollback needed.

The local exact-source blocker is resolved. Future rollout requires separate
authorization naming the new sync pin and unchanged HTTP pin, then fresh baseline,
JIT authority, NL READY/live directory, RU isolated check/full sync negatives,
HTTP A–G, ordinary regression and physical gates. No automatic attempt #8, distributed
beta or Krasnodar FIELD-1. **STOP.**
