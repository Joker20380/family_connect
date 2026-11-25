# 25 November 2026 UTC — nonempty OWNER publication settlement

Selected task: CONTROL-HA-20261123 / HA-02. This is a **test-only completion-boundary
checkpoint**, not settlement of production work, deployment or a new acceptance gate.
The [four existing stage2 gates](../control-ha.md#когда-заканчивается-этап-2) remain fixed:
replication PASS; current-input trust, coherent all-writer capture and full recovery partial.
No product, installed application, image, public artifact or catalog version changed.

## Concrete missing case

The [OWNER activation/revert stand](2026-11-24-control-ha-owner-upgrade.md) used an empty
publication queue. Its bounded forced-stop fallback did not establish what happens to a real
outstanding request. Earlier admission tests substituted the publisher function; they did
not observe a native HTTPS acknowledgement together with a blocked PostgreSQL COMMIT.

`control_plane/tests/test_publication_settlement.py` adds three cases using the actual
`manage.main` → `publish_system_messages` → `Publisher`/`publish_next` path in a separate
Python process. The only child settings adjustment selects pytest's disposable database;
the HTTPS trust anchor is a freshly generated private fixture certificate, with hostname
verification enabled. No publisher implementation, transport response or database operation
is monkeypatched. Fixture `SSL_CERT_FILE` does not affect any installed application.

The local HTTPS endpoint persists the synthetic event to a separate SQLite database with
synchronous=FULL **before** replying. A separate PostgreSQL transaction holds the actor row
lock. After the HTTP reply/feed checks, deferred audit-FK validation blocks the publisher's
real COMMIT. An independent query observes its uniquely named backend as active/Lock/COMMIT.
This makes the remote-complete/local-not-yet-committed interval observable without sleeps
being treated as proof of completion. Polls and subprocess/server cleanup are bounded.

Both the unresolved HTTP interval and the native COMMIT interval reject gate drain with
DRAIN_TIMEOUT. The fixture then releases the blocking transaction; it does not terminate
the successful publisher to obtain a quiet sample. A separate explicit failure case kills
only the fixture's own Python child while COMMIT is waiting. It never kills a working service.

## Observed result

Focused run: **2026-11-25 00:22:26.342340–00:23:08.720638UTC**, including disposable PG
startup/cleanup. **67 tests PASS,0 skips,36.75s**, of which three are the new native cases.
An initial three-case run also passed; the focused result above is the final source version.

| Case | Remote event | Local state after sender exit/backend completion | Pending marker / capture |
| --- | --- | --- | --- |
| Normal HTTPS ACK, feed readback and PG commit | One persisted event, one POST | published | Zero; drain succeeds only after completion |
| Reply lost after remote commit | One persisted event, one POST | unknown; command itself exits0 | One retained; drain refuses UNSETTLED_OPERATION |
| Sender killed during blocked COMMIT | One persisted event, one POST | **published after the sender was killed** | One retained; drain refuses UNSETTLED_OPERATION |

The last result is important: process death does not cancel an already submitted PostgreSQL
COMMIT. In this run PostgreSQL completed it after the blocking transaction was released.
The test permits either rolled-back queued state or completed published state after a killed
sender, waits for that exact backend to disappear, and **requires refusal in both cases**.
Its receipt records the actual state, not merely the range of allowed outcomes.

In both uncertain cases a later successful management command preserves the exact original
marker name and bytes. An unknown message is not automatically resent. If a killed sender's
transaction rolls back, retry uses the same message payload/ID; the synthetic endpoint is
idempotent. The actual final run needed no second POST. Fixture idempotency is not evidence
of installed gateway behavior or permission to erase an uncertainty marker.

## Scope, pins and reproducibility

- Disposable PostgreSQL17.11, pinned
  `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
  A fresh owned/labelled container is removed with its volumes after the run.
- Panel venv: Django5.2.18, psycopg3.3.6, pytest9.1.1, cryptography46.0.7;
  all17 declared `control_plane/requirements.lock` pins match. The existing disposable
  PG orchestrator uses the control venv's psycopg3.3.9, not the panel's application driver.
- Native connections are to ephemeral loopback PG/HTTPS fixture ports only. New synthetic
  DB role, database, token, TLS key/certificate and test users/messages; no real data or token.
- Tests execute the feature source at baseline82dbcbc3 plus this test file, **not a newly
  installed image**. All10 runtime overlay sources are unchanged. Prior candidate-content
  and cross-mount proofs remain accepted, not rerun or superseded by a new candidate.
- No OWNER working-container inspect/exec/restart, production DB query, RU/NL connection,
  working source/unit/environment/permission or service change. No health observation is
  inferred from this isolation; the preceding installed observation remains historical.

With the ordinary private synthetic panel PostgreSQL test configuration, from `control_plane`:

```sh
python -m pytest -q tests/test_publication_settlement.py tests/test_system_messages.py \
  tests/test_capture_admission.py
```

The native fixture is intentionally in the panel suite: it requires that suite's PostgreSQL
and locked dependencies, not the root control-only environment or a SQLite substitution.
Private retained evidence: `~/.local/share/family-connect/control-ha/20261125-owner-publication-settlement-*`;
`/tmp/fc-ha-publication-settlement-current` identifies it. It includes final JUnit, synthetic
scenario receipts, sanitized summary and private fixture TLS material/logs. Do not commit keys,
raw evidence or database files even though these fixtures are synthetic.
Documentation checks: four files/1080 link targets/zero errors; whitespace clean. External
URLs are enumerated, not fetched. The validation receipt remains with the private test evidence.

| Evidence | SHA256 |
| --- | --- |
| New test source | `2989ce333bcfcfef3e342549981e45e912d788257112f1ee848f4d2ae7357822` |
| Sanitized final summary | `9b929aa8777b1da4b05be2277af73f4ec098b8f4ffc567c779c7d8e40218a314` |
| Final JUnit | `95864cb35033cbcb7a925fcfb85a690c71dcf56c81ca597cd86ae9eb90a4e87e` |

## Operational consequence and remaining boundary

This closes the **nonempty publication integration-test gap**, not existing production-work
settlement. Exit0, process disappearance, a successful HTTP acknowledgement or a sampled
published/empty queue alone cannot authorize replacement/capture. Gate uncertainty is retained
even when later evidence shows a database commit; no marker-clearing tool or reconciliation
shortcut was added. The working old images do not acquire this gate retroactively.

Before an actual transition, close new dispatch through the approved paths, account for already
started publication/support/manual operations at both ends, and preserve any uncertain result.
If that cannot be established, abort the transition without killing the publisher or clearing
markers. A new idle gate cannot prove that pre-existing ungated work has settled. Existing
independent candidate/config/runtime acceptance and authorized OWNER gate/guardian setup,
RU/NL/manual/transport participation, approved coherent capture and independent current
checkpoint/key/access custody plus final recovery remain. Working-NL deployment is outside
the current scope. Do not repeat this native completion test as a new stage2 prerequisite.

There is **no production rollback** in this test-only change. Keep the original images/configs
and uncertainty evidence; do not restore stale DBs. The earlier activation rollback remains
exact old image/config with current data preserved, not evidence of a safe live stop. Test
cleanup removes only owned disposable processes/PG resources. No HA-03/cutover or new ETA.
