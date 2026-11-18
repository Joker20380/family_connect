# 18 November 2026 — guarded RU / MESH recovery

## Scope and current gate

The owner explicitly requested recovery after the read-only incident report.
This is not a PR44 deployment or a change to installed transport/runtime bytes.
The ordinary RU recovery was already executed in another session at12:18UTC;
this session detects it before any stop and does not repeat it.

At12:38:51UTC the original started PIDs/invocations remain stable, NRestarts0,
68 revisions match, actual/expected AWG20 and TCP20 sets match and attempt age is2s.
All eight protected tables, generation2 material, command map and effective units
match the saved baseline. The first failure survives with its original inode/hash
under `transport-failure.20261118-0149.preserved.json`.
The existing fresh27-table backup and isolated paid-projection restore passed;
off-host AES-GCM backup has a verified decrypt roundtrip. No live DB was restored.
This is server-side continuity, not a new physical-client HTTPS acceptance.

## Expired unprepared MESH completion

Installed runtime is the fcb31164 maintenance capsule, not source main. Its normal
expired rollback terminal requires a same-operation plan, absent in this incident.
The new explicit operator helper completes only an all-acquired, never-prepared,
uncommitted STALE_NODE_STATE operation with expired leaf predecessors.

- Default `reconcile` still rejects expired credentials. Its explicit predecessor
  option validates signatures, current authority, grant bindings and absence of
  pending revocations; both predecessor leaves must already be expired.
- Existing immutable rebase intent preserves the original transaction/owner and
  current registry digest. Only the RU ownership comparison is rebound; no DB,
  authority, grant, profile or directory is restored or rewritten by this step.
- Each node independently checks its exact owner, expected state, stopped readers
  and an allowlist excluding preparation, staging and commit artifacts before using
  the installed no-op rollback and fenced-terminal methods.
- Durable controller binding replaces no plan: it explicitly records unprepared
  completion. Existing fenced cleanup archives the evidence and releases ownership.
  The helper never starts a reader. Normal fresh renewal remains mandatory.
- Partial node finalization is replayable; unfinished nodes, active readers, changed
  owner/profile/intent, unexpected artifacts and invalid predecessors fail closed.

Qualification:27 selected tests pass on current source and again against the
fcb31164 source capsule matching installed production-node/controller/grant hashes.
These tests are qualification only; live MESH recovery is not yet claimed here.

## Remaining live gates

Pause/drain only credential-renewal and restricted sync schedules; ordinary paid
reconciliation and RU/NL AWG/TCP stay running. Preserve an incident state backup.
Apply the qualified non-activating completion sequentially, renew credentials using
the installed controller, regenerate expired directories using the already installed
bounded publisher with new current bindings, and restore readers only after COMMITTED
and ownership cleanup. Retire temporary publisher configurations and restore schedules.
Verify exact crypto/directory bindings, sustained service continuity, fresh panel
imports, real restricted traffic and the next due renewal. Failure remains fenced;
never restore historical product DBs, certificates or private publisher configs.

See [fresh incident diagnosis](2026-11-18-mesh-ru-incident.md).
