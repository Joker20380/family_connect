# HA-02 — manual operator admission, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02 continuation after the
[support lifecycle qualification](2026-11-25-control-ha-support-lifecycle.md).
This closes three source-level operator entrypoints, **not installed manual-writer coverage,
support deployment or stage2 acceptance**. The existing four stage2 gates and their dependencies
remain unchanged; no new stage, product release or completion-date claim is introduced.

## Finding and bounded correction

`paid_beta_admin` already honored the optional capture gate. Three other manual entrypoints did
not: `control.friends.restricted_admin` (5 actions), `control.friends.support_admin` (6 actions)
and `scripts.service_notices` (6 subcommands). A drained HTTP/worker gate therefore could not
alone prevent these operator paths from opening SQLite, changing grants/FIELD admission or
publishing files. Repository source is not proof of installed command selection.

Each now accepts `--capture-gate` before the action/subcommand and acquires the existing gate
before constructing/accessing its store or reading private inputs. Closed admission produces
exit75 and `{"error":"CAPTURE_BUSY"}` without creating a database, token, lock or publication.
Missing/invalid/symlink/wrong-mode gates fail closed instead of reverting to ungated operation.
The same admission covers the entire action, database commit, publication and explicit store
close. Support's existing sanitized error handler runs only after gate exit, so it cannot hide
an admitted failure from the marker mechanism. Process death, post-commit failure, failed close
and publication uncertainty retain durable markers; a subsequent successful invocation does
not remove an earlier marker. No reconciliation shortcut or marker-deletion API is added.

The existing CLI action semantics, FIELD cohort limits, grant expiry checks, public feed formats
and schemas are unchanged. Optional `argv` permits exercising the actual parser/entrypoint;
action bodies remain independently callable for their existing library users. Restricted/support
gate imports are local to the CLI so old helper-only committed-source capsules do not acquire a
new import dependency. The support operator archive already contains the gate module; the normal
HTTP archive likewise contains the notices CLI and gate. No pinned installed receiver overlay is
rebuilt, altered or selected for deployment.

**Omitting the option intentionally preserves legacy ungated behavior.** This source change does
not enforce a system policy, wrap every executable, attest an old process or settle prior work.
Installed source/argv/UID/gate bindings, forced commands/queues and remaining sender/routing/alias/
offline writers still need a complete census and guarded integration before a coherent capture.
The gate is single-host/per-UID; do not weaken its permissions to imply cross-user coverage.

## Qualification

Python3.14.4, pytest9.1.1; all26 control/identity lockfile pins match. Final **211 PASS/0 skips**,
62.83s. **89 new cases** exercise all17 actions under closed admission and missing/symlink/mode
failures, ordinary opt-in/ungated success, real SQLite lock waits, admitted process death,
post-commit uncertainty, explicit close failure and durable rename outcomes. Three isolated
archive invocations use `-I` outside checkout and assert module provenance, refusal and successful
recovery. Support archives are deterministic; only synthetic fixture identities/stores are used.

```sh
FC_TEST_RECEIVER_BASELINE="$BASELINE" python -m pytest -q -ra \
  tests/test_operator_capture.py tests/test_support_ids.py \
  tests/test_device_notices.py tests/test_notice_publication_boundary.py \
  tests/test_capture_gate.py tests/test_capture_gate_integration.py \
  tests/test_package_paid_canary_crl.py tests/test_package_receiver_capture.py
```

`$BASELINE` is the privately retained, digest-checked original receiver archive, not a download
or working service. The13 installed-shape regression cases test the already pinned overlay,
not deployment of the new CLI source. Earlier85-case and196-pass/13-skip runs overlap the final
suite; they are not additional acceptance totals. The latter lacked that fixture environment;
the final run supplies it and has no skips. Review also corrected a close-failure test proxy to
forward transaction context methods and independently verify the committed data, preventing a
close error from masking an unrelated fixture failure. No implementation gate was relaxed.
Five changed documentation files/1169 local-link targets and whitespace checks pass.

## Actual working state and access

The initial noninteractive `sudo -n true` still returns `sudo: interactive authentication is
required`. Existing owner authorization is sufficient but does not supply technical privileged
execution. No alternate escalation, password collection or working service stop is attempted.
Guarded support activation remains blocked on that access; its qualified lifecycle change must
not be replaced with a kill-policy-only update.

Read-only OWNER checks at15:39:12UTC confirm all19 installed support source hashes and all
recorded effective unit fields unchanged from the preceding lifecycle preflight. Support remains
active/running, PID2022541,0 restarts, no daemon-reload warning. At15:39:23UTC the exact three
previously observed OWNER containers (console, system publisher, PostgreSQL) remain healthy,
running,0 restarts, with unchanged PIDs/images. No user data is printed or copied into Git.
RU and NL hosts are not contacted in this continuation; the prior15:25UTC RU receiver readback
remains historical evidence, not a fresh remote liveness claim.

No installation, deployment, product/client version, public installer/catalog/invitation-page,
signature, schema, policy, paid-watch/deny enforcement or working database change occurs.

## Evidence, rollback and remaining work

Private locator `/tmp/fc-ha-operator-capture-current` retains qualification logs/JUnit and
sanitized OWNER readbacks outside Git. No production private key/profile/database is captured.

| Evidence | SHA-256 |
| --- | --- |
| Final211 JUnit | `ed24524e2ecfaeb8c179b402487bb01b3d5fc17125f057f47b2693a7a14ac2bc` |
| Support unchanged readback | `d223791815412d263772ba4f9aa6c29862b4897cf1318bee88e76923497a08f8` |
| OWNER unchanged readback | `58eb32a85a676f927331b9a4c789f0bdf78aefc7180279b0528019e08058e053` |

No operational rollback is needed. Source rollback is an ordinary revert of the three CLI
boundaries/tests/documentation; it never restores an older data file or deletes uncertainty.
Before future installation retain the exact old launchers/archives/units and qualify a guarded
code/config-only rollback. New successful writes must survive any rollback. A fresh empty gate
cannot certify old ungated operations; unresolved markers require independent reconciliation.

Next remains privileged support activation and exact runtime/background persistence closure,
installed CLI/forced-command census/binding and remaining manual paths, guarded OWNER integration,
then coherent fleet capture, independent current-input trust/custody/approval and combined
post-ACK recovery. Replication PASS in isolation; the same other three HA-02 gates remain partial.
No HA-03 production cutover, automatic failover, complete client E2E or new ETA is claimed.
