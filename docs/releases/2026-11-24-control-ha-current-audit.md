# 24 November 2026 — scheduled current-content audit and stage2 exit criteria

## Selected scope and result

Continuation of [legacy custody](2026-11-24-control-ha-legacy-custody.md), not a new
lettered stage. The selected gate remains **IN_PROGRESS**: validate the actual installed
completed scheduled/service-bearing current operation, original gate provenance and
current issuer/both-publication/five-table DB binding. This checkpoint implements and
tests a read-only content audit on native synthetic data; it does not claim installed
acceptance, a production backup, service health or recovery qualification.

The owner also asks when stage2 finishes. The [four-block exit checklist](../control-ha.md#когда-заканчивается-этап-2)
now makes the endpoint explicit: journals; installed schemas/writer barrier; full
off-host/current-state recovery; strict PostgreSQL/Patroni quorum/RPO0. The first remains
partial and the other three unqualified. No measured calendar ETA or percentage exists;
this is not one final small patch. HA-03 fencing, HA-04 API/client failover and HA-05
shadow/cutover still follow; even completed HA-02 alone does not remove RU dependence.

## Content checks versus acceptance

- [Auditor](../../scripts/control_ha_current_audit.py) authenticates the full custody
  bundle against its independent checkpoint. It selects the current archive and native
  coordinator bytes without rewriting full ledgers, synthesizing missing history or
  interpreting unselected legacy/fenced/adjunct bytes. Unequal cohorts remain unequal.
- [Native validator](../../scripts/control_ha_stopped_v1.py) retains the original stopped,
  offline and emergency recovery entrypoint. A separately purposed content-only entrypoint
  checks scheduled COMMITTED/acquired/quiesced/reconciled state, current CLEANED receipts,
  exact archive manifests/material, unchanged scheduled authority, signed current validity,
  both gateway publication hashes and original plan bindings.
- [Service checker](../../scripts/control_ha_current_services.py) matches services-before
  unit coverage and permitted start-intent indices to native SystemdBarrier rules. RU
  resumes only eligible indices0/3; NL resumes active/activating/failed readers. Unit,
  field, state, PID and timestamp contradictions refuse. Native float timestamps within
  the integer completion-receipt second are allowed; bool/early/future timestamps refuse.
- The existing current binding verifies issuer delegation/CRL/primary directory and the
  exact devices/invites/grants/certificates/CRL-sequence projection. Both supplied NL
  publication bytes must match their native accepted receipts and trust/gateway identities.

Every successful content check still returns CURRENT_CONTENT_CHECKED_RECOVERY_BLOCKED:
original_gate_provenance NOT_ESTABLISHED; unit_order_provenance CALLER_SUPPLIED_NOT_ATTESTED;
service_liveness NOT_OBSERVED; capture_consistency NOT_ATOMIC; recovery_acceptance BLOCKED.
It exposes no private payloads and offers no database import, filesystem restore, journal
execution, service commands or override/acceptance flag. Activation remains FORBIDDEN.

Why the distinction matters: `ProductionController.run` derives the scheduled gate from
its `scheduled` and `approved_leaf_crl_schedule` inputs and stores the resulting gate,
not the original configuration/approval. `runtime_controller.py` reads the approved flag
from configuration. The historical gate is not reconstructed from a present-day flag.
`SystemdBarrier.resume` writes a start intent before invoking systemd; the intent alone
is not an independent service-success receipt. Neither observation proves original
evidence is absent from every backup or that any live service is currently stopped.

## Qualification

[Tests](../../tests/test_control_ha_current_audit.py) run the native three-node controller
with the actual scheduled branch and SystemdBarrier implementation; only systemd state/
invoke and gateway directory refresh are simulated. Ephemeral keys and local DB fixtures
are generated. Tests retain unequal2/2/1 ledgers, opaque invalid-UTF8 legacy bytes and an
unknown old adjunct; all four source trees are removed before content readback. Host I/O
and subprocess execution are forbidden during that readback. These are not exported
production payloads or an installed service-state capture.

Negative cases rebind archive manifests/ledgers/custody checkpoints before semantic
checks: missing/mismatched starts, scope/PID/state/time contradictions, pending/current
unknown state, missing/fenced/future current receipts, wrong unit order, both publications,
each of the five DB projections, issuer substitutions, stale material and old ciphertext.
The legacy stopped recovery purpose still refuses the new scheduled content purpose.

Commands use the existing control/identity-lockfile environment:

```sh
python -m pytest -q tests/test_control_ha_current_audit.py \
  tests/test_control_ha_stopped_capsule.py tests/test_control_ha_legacy_custody.py
```

Private JUnit: `/tmp/fc-control-ha-20261124/current-audit-regressions.xml`.
No private archives, generated keys, state bundles or production databases enter Git.

Final run:212 PASS /15 explicit skips in151.52s. Breakdown:56 new current-content tests
/0 skips;111 stopped/offline/emergency regressions /15 PostgreSQL skips;45 custody
regressions /0 skips. All15 skips require `FC_HA_PG_PORT` and the protected password-file
setting; PostgreSQL was not started. No new DB-import, crash/restore, full historical
suite, runtime package or platform-release qualification is claimed. Six documentation
files/1007 local links and whitespace checks pass.

Qualified source SHA256:

| Source | SHA256 |
| --- | --- |
| control_ha_current_audit.py | bceafe4f645d325b811c6e9e66462e64a759d836544c0193b2a10039a9db831e |
| control_ha_current_services.py | 2069a95e3f52e46a3e2ab0f022fc6cc34a2b49587b5f71e147d63f96c5b3ea30 |
| control_ha_stopped_v1.py | dcf4a2edf02364b5f3260f73f383e12099457fc304dbb173bcb5f3a2eb09cc05 |

## Remaining work and rollback

Continue the **same** selected task: locate and bind trustworthy original schedule/
configuration provenance and qualify actual installed current inputs. Do not infer
approval from this new source, the operator's general migration request or a present-day
flag. A live service observation, installed unit-order/source pins and coherent state
capture remain required. If original evidence cannot be established, keep the result
unqualified and record the precise unresolved decision instead of generating approvals.
This checkpoint does not select another variant, deploy the new code or advance HA-03.

No gateway SSH, service/timer/policy change or version release occurs. Latest known
console image remains `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`;
NL GeoIP collectors22 November20:53:48UTC; installed renewal aggregate e9fd3175;
RU HTTP archive `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`.
Android126/catalog9, public/invitation versions,8/12/120s deadlines and all-three-node
ACK remain unchanged. These versions were not requalified and no fresh health is claimed.

Rollback: stop using/revert this source-only audit checkpoint, retaining independent
custody receipts and native evidence. No server rollback, service restart, old database
restore or historical journal rewrite is needed. The authoritative branch/worktree stays
`feature/device-technical-metadata-20261115` at `/home/joker/.codex/worktrees/dad9/family_connect`;
old divergent main is navigation only and original dirty/untracked work must be preserved.
