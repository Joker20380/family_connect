# HA-02 — installed-shape receiver candidate

Date:25 November2026. Selected task:CONTROL-HA-20261123 / HA-02.
This closes installed-shape **source qualification**, not live activation or stage2 acceptance.
[PLAN](../PLAN.md) · [STATUS](../STATUS.md) ·
[Preceding graceful-stop qualification](2026-11-25-control-ha-http-drain.md).

## Why the full candidate is not the deployment input

The previous full source package changed21 existing Python members, added3 and removed1 versus
the exact RU archive. Most changes were canonical repository adapters, not receiving-maintenance
requirements. Deploying that whole package would unnecessarily change the legacy data/policy
implementation during HA-02. This checkpoint instead prepares a closed, reviewed delta against
the retained installed SHA256 `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`.

`scripts/package_receiver_capture.py` applies only the pinned patch in
`deploy/friends/restricted/receiver-capture-v1.patch`, using the independent before/after/source/
unit pins in `receiver-capture-v1.json`. Arbitrary baseline overrides are not a CLI option.

| Changed member | Exact scope |
| --- | --- |
| `friends_http.py` | Whole-request gate, external registration boundary, optional gate CLI, gated route administration, graceful HTTP/retention lifecycle; existing routes retained |
| `scripts/service_notices.py` | Durable single-transaction/time export and persistent external uncertainty; original legacy class/schema/other methods retained |
| `control/friends/diagnostics.py` | Gate-aware, joinable retention only; existing consent/data code retained |
| `control/friends/technical_metadata.py` | Gate-aware, joinable retention only; existing consent/data code retained |
| `control/friends/chat_sync.py` | External uncertainty around the existing locked publication; no canonical-only API guard |
| `control/friends/transport_membership.py` | External uncertainty around existing command/ACK handling; no payment, policy, protocol or ACK-format rewrite |

Only `control/capture_gate.py` and `control/friends/http_lifecycle.py` are added, pinned to the
already qualified sources. No archive members are removed. The other38 entries remain exactly
byte-identical, including unchanged access, paid subscription, routing, restricted access,
support, identity and transport-reconciliation source. No SQLite schema migration, alternate
canonical backend or new payment/revocation API is introduced by this overlay. Timeouts, lease
durations and paid-watch/deny behavior remain unchanged.

The builder validates the entire baseline digest before use, each changed member before/after,
patch/helper/unit digests and the complete output member set. It bounds input/expanded ZIP
sizes, rejects unsafe/duplicate/symlink/encrypted members and unsafe local inputs, never extracts
unselected members, and compiles changed/added Python. Output is deterministic, private and
exclusive-create. It fsyncs files and directories; an interrupted/partial output is retained and
cannot be silently replaced. It emits an archive, paired unit drop-in and sanitized hash receipt,
but neither executes the candidate nor contacts/reconfigures a host.

```sh
python -m scripts.package_receiver_capture --baseline "$BASELINE" --output "$NEW_DIRECTORY"
```

The output directory must not already exist. This is a build command, not deployment permission
or a production installer. Changes to pinned source require a newly reviewed contract/delta.

## Qualification

Final run **13:55:42.768948–13:56:33.503712UTC**, pytest50.25s:
**171 PASS,0 skipped,35 new top-level tests**. Included are two archive-contract runners, each
with **129 PASS,0 skips**: one against the exact installed baseline and one against the candidate.
The129 case identities are verified equal; these nested runs are not counted as258 additional
top-level tests or as independent stage-completion gates.

The legacy cases cover invitation identity/replay, parallel claims, existing status/revocation
behavior, device notices/editing, chat/service identity, paid billing/idempotency/concurrency,
referrals, diagnostics and consented technical metadata. All loaded modules that exist inside
the archives are asserted to come from those archives, both before and after tests. No checkout
implementation silently substitutes for an old packaged API. Provisioning/messenger fixture-only
helpers may come from source; they are not promoted into the receiving runtime. Three new
operator-revocation API cases are not part of the older installed API selection.

Shared enrollment/proof test helpers move to `tests/fixtures/receiver_access.py`, eliminating an
irrelevant canonical operator-CLI import from diagnostics/metadata fixtures. Their real signing,
challenge, registration and SQLite operations are unchanged; ordinary source tests also pass.

New package checks cover exact closure/determinism, all binding-drift refusals, failed patch,
existing/partial-output preservation, unsafe paths/FIFO/symlink/ZIP inputs and isolated imports.
Six native export fault cases in the actual installed-shaped candidate cover both feed versions
and file fsync/rename/directory fsync. A caught failure rolls back the export transaction and
retains pending; a subsequent successful retry does not clear earlier uncertainty.

Six native outbound cases cover successful ACK, child exit after a durable synthetic effect,
and malformed ACK for transport preparation and mailbox publication. These use actual child
processes and native legacy registry/snapshot code. Mailbox SSH execution is redirected to an
owned local child after verifying the original strict SSH command shape; no real remote mailbox
is contacted and no canned successful command result is substituted. This qualifies the
candidate's uncertainty boundary, not actual remote gateway completion or fleet settlement.

The prior lifecycle suite also runs on the candidate through `FC_TEST_HTTP_RUNTIME`: real HTTP
export/retention, repeated TERM/INT, SIGKILL, lost ACK, incomplete headers and real user-systemd
stop with a surviving admitted child. The full-source package compatibility case remains
separate. Owned systemd fixture units are independently confirmed absent after cleanup.

Environment: Python3.14.4, pytest9.1.1, all26 control/identity lockfile pins match. No new PostgreSQL
replication or TLS activation qualification is claimed; no corresponding implementation changes.

```sh
FC_TEST_RECEIVER_BASELINE="$BASELINE" \
FC_TEST_HTTP_RUNTIME="$CANDIDATE/friends-http.pyz" \
FC_TEST_SYSTEMD_HTTP_DRAIN=1 python -m pytest -q \
  tests/test_package_receiver_capture.py tests/test_receiver_legacy_contracts.py \
  tests/test_friends_http_lifecycle.py tests/test_notice_publication_boundary.py \
  tests/test_capture_gate.py tests/test_capture_gate_integration.py \
  tests/test_support_ids.py tests/test_online_diagnostics.py tests/test_technical_metadata.py
```

Initial development evidence is retained, not counted as acceptance: an extraction mistake
selected canonical export refusal methods instead of the legacy export methods; native tests
rejected that first private candidate. The explicit patch was corrected and its pins regenerated
before the final candidate was built. Two exploratory legacy harness runs failed collection on
fixture-only imports; the shared helper separation and archive-binding checks resolved this.
Neither failed candidate nor an exploratory result was installed or published.

## Evidence and runtime observation

Private locator `/tmp/fc-ha-receiver-overlay-current`: immutable baseline, rejected initial
candidate, accepted `candidate-v2`, hash receipts, initial/final logs, final nested archive reports,
lockfile comparison and sanitized health observations. Raw source capsules, keys, synthetic DBs,
private fixtures and runtime receipts remain outside Git/CI. Safe hashes:

| Artifact | SHA256 |
| --- | --- |
| Qualified candidate | `58c5fde9b91a8997a2ebe2c881c43d8032eb82899d1d3c510390dd61efdab627` |
| Contract manifest | `0a9151f02724f8f2dc2f6e5d16ca7bdc927ad74d9f9673bebe6bf271ceaf9f16` |
| Candidate receipt | `a65847c9ac2954ff5bfd71b9c28795faee3afa83e338fae878878955b5eb5d07` |
| Final JUnit | `a8e04f14fad82cc547d6f42babf48ddd129ad7bbcb020ac7a4cceb1c7ad9918d` |
| Current RU observation | `169c86ad056bd901e303d72f1e134d4804fb95d25d9e4a2f5b5bef5f7d9d66e2` |

Read-only strict-pinned RU observation13:56:39.282490UTC: same installed archive and PID43082,
active/running,0 restarts; still the old control-group TERM/90s stop policy. OWNER console,
publisher and PostgreSQL remain healthy/0 restarts; both collectors' timers active. No NL host
contact, working DB/feed/config changes, restart or deployment. No client version, installer,
signed update catalog, invitation-page or public-distribution change.

## Activation boundary and rollback

Installed-shape source qualification is now complete. The next operation is **legacy receiver
admission closure and independent old-handler/child settlement**, not another broad source build.
The old program does not gain graceful behavior merely because a new archive has been built.
Do not stop it on thread-count/empty-queue evidence alone, replace the archive underneath a running
process, install only the new unit drop-in, or start competing unfenced writers to bypass this gate.
Starting a fresh empty capture directory also cannot retroactively prove old operations settled.

Before activation retain and bind the actual installed archive, effective unit/command/environment,
gate ownership, current stores/feeds and pre-existing uncertainty. Use only the exact qualified
candidate with its main-only TERM/no forced kill/infinite timeout settings, after the legacy-work
prerequisite passes. A timeout or unknown outcome means abort/reconcile, not forced termination
or marker deletion. There is no production deployment to roll back in this checkpoint. Source
rollback is an ordinary revert; a future runtime rollback must preserve all current data and
pending evidence after new writes, never restore an old SQLite/feed snapshot for a clean gate.

Remaining support/manual coverage, guarded OWNER integration, fleet participation, coherent
capture, independent custody/trust/approval and final current recovery remain within HA-02.
Replication PASS in isolation; the same three other acceptance blocks remain partial. No HA-03,
automatic failover or new completion estimate. Main remains navigation-only.
