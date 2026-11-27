# HA-02 common capture preparation — 27 November2026

## Result and exact boundary

The requested **production encrypted RU/NL1/NL2/OWNER kit does not exist yet**.
No production stop/capture/resume operation was started. Existing accepted components
were not reinstalled. This change qualifies a missing causal four-host protocol and
checks delayed read-model imports on the exact installed console image. Neither result
is an all-writer permit. HA-02, independent custody, source-host-free current/post-ACK
restore and FLEET-PRODUCTION-ONBOARDING-1 remain open.

Work continues on feature/device-technical-metadata-20261115 from de41922a; main remains
da94566a. Fetch found no subsequent feature commits. Independent GitHub readback now
confirms all five d7d8b9a9 workflows SUCCESS, including runs45941591986/91987/92002/92021/91970.
The accepted native360/0-skips scope and OWNER custody format are retained, not rebuilt.

## Fresh bounded operational preflight

At12:28UTC normal real panel login, overview, subscriptions, payments, two existing
cards and logout pass. No test message or manual business-data mutation is performed.
Console3af9fbf9/publisher35158514/PostgreSQL18cfe3ef remain running, restart counts0.
Read-only observer8b9355db returns ACCEPTED_SUPPORT_READ_ONLY_NORMAL. SupportPID240065,
archive621009b8, authorityb0c470dc, NL1 generationb75ef2a2, cursor and accepted history
are byte/binding-identical to the05:05 checkpoint. No completed Resume.run is executed.
The actual runtime directory is0750 fc-support:fc-support-ipc and contains worker.sock0660;
an initial check of a nonexistent `ipc` child is retained, not treated as IPC failure.

NL1 PID2822717/invocation09bbec58 and NL2 PID3203344/invocationf37b8845 are active/running,
NRestarts2 each. Existing authorized FLEET_MESH_PROBE_1 passes4HTTPS/3DNS/expected egress
for each node at12:31/12:32UTC, without an SSH tunnel or normal-broker fallback. Its existing
identity is unchanged. Process status alone is not this traffic result. Two initial local
probe launches fail before dispatch on missing Python imports; those logs remain separate.
The correct existing support venv plus repository source resolves those prerequisites.

RU has about6GiB free/79% used; IO PSI avg10 some3.34/full2.27, memory pressure0 at this
sample. This is not the earlier severe-pressure observation or a root-cause diagnosis.
Normal renewal/directory-sync invocations exit0, both timers enabled/active/waiting.
Current renewal scheduled-1795778757-6f85e99b1d8ed952 is COMMITTED, first_cause null.
The bounded searched renewal state has no owner.json; this readback is not a held
maintenance lock and must be refreshed when the actual operation starts.

No production hold is acquired by this iteration. Root authentication uses the ordinary
local sudo dialog; sudoers/polkit are unchanged, and Docker is not used to obtain host root.

## Finite writer/endpoint matrix

“Required” below is an outstanding production adapter obligation, not a claim of a held fence.
Each adapter must check installed sources/UIDs/paths, take the actual local constraints,
keep them continuously until sealing, and issue receipts for the same operation. An old
UNKNOWN need not become settled; its possible future effects must be covered by these rows.

| Writer / endpoint | Captured state and already dispatched work | New admission | Old work and continuous proof required | Queued/late behavior after resume |
| --- | --- | --- | --- | --- |
| OWNER root support/subscription collectors | Local projections/cursor; cursor IPC and SSH exports may have been sent | Accepted mandatory b7f4cbd2 gate | Hold admission/operations; include downstream rows, not deletion of root119/additional markers | Fresh source-bound collection; support cursor/queue continuity remains the accepted linked-resume contract |
| OWNER inventory/probe/manual collectors on three installed roots | Read-model projections, Docker import calls, SSH exports | Accepted b49c76c0 per-role mandatory bindings, including no-env entrypoints | Hold role/cycle locks; already accepted Docker/receiver work requires its own downstream boundary | Inventory/subscription/probe digest/identity dedup; metadata consent/sequence floors; new native checks below |
| OWNER Docker `exec` imports into console | Accepted `import_inventory`, `import_subscriptions`, `import_network_probe`, `import_technical_metadata`; PostgreSQL effects may outlive the invoking client | Installed console gate on actual database operations | **Missing integrated production adapter:** held PostgreSQL/native-write boundary or exact operation terminal proof, including already-created/started execs and their accepted DB work; empty ExecIDs is insufficient | Qualified read-model replay does not regress latest observations, duplicate effects/audits, or resurrect revoked metadata; it is not physical fencing |
| OWNER HTTP, scheduler, management, direct ORM and known native SQL | Business/fleet/auth/audit/read-model PostgreSQL data; synthetic registry and aliases | Accepted image/binding checks and console gate cover admitted application paths | Need exact full database/file coverage, accepted transaction/sequence/native access constraints; the existing two-table PublicationFence is not a whole-database boundary | Application idempotency and retained journals only; arbitrary queued native SQL is not certified by the six import checks |
| Publisher and RU `/friends/notices/publish` | Queued/unknown message IDs, signed payloads, notice store/feed; an HTTP request may already be accepted | Installed publisher gate plus receiver HTTP admission | Need both database publication boundary and continuously held RU notice receiver/store boundary; client HTTP completion is insufficient | Existing stable message ID/immutable payload and explicit unknown retry; canonical receiver/readback must be included, not only sender state |
| RU Friends HTTP and application stores | Registry, diagnostics, notices, metadata, proofs, grants, paid/referral/support/chat/routing state | Installed receiver overlay0d181404 and its actual gate | Existing local SQLite writer locks plus receiver operation coverage must be one continuously held participant; retain sidecar/schema checks | Existing nonce/version/CAS rules must be bound to installed code and captured floors; no guessed historical outcomes |
| RU peer worker, native operator CLIs and deployment paths | Peer allocation, profiles, membership, aliases, support policy and local/file effects; Docker/SSH children possible | Existing optional CLI guards alone are not mandatory native coverage | **Outstanding:** actual storage/operation/receiver boundaries for each path; do not infer closure from stopped sender/absent process | Preserve intent/expected-version journals and use qualified reconciliation; offline signer/deployment changes cannot run concurrently |
| RU renewal/directory-sync and NL receivers | Coordinator, owner/ledger/archive, profile/CRL/lease floors and gateway directories | Existing coordinator/node operation locks and receiver admission | Acquire actual locks and verify all three node ownership/reconciliation states throughout capture; preflight COMMITTED is not a hold | Existing current-generation/native operation identity; do not replay old start intents or downgrade authority |
| NL1/NL2 registration, profile snapshot, fleet/transport receivers | Per-node allocation and installed receiver files; already accepted forced-command work | Existing pinned receiver wrappers/gates where installed | Held receiver operations and native allocation/profile/file boundaries; include possible children rather than sender SSH status | Existing allocation identity, generation/sequence/CAS rules; actual adapter coverage remains required |
| OWNER support lifetime writer ↔ NL1 mailbox | Spool/RNS persistence, cursor, mailbox queues/dedup/floors; old links/envelopes | Accepted managed stop plus closed mailbox generation | New stopped-support snapshot inside the common interval, closed receiver/readback, final persistence and independent exit proof | Accepted fresh linked forward resume and old-generation/link rejection; preserve support33 and all queue/history bytes |
| Paid-watch/deny and transport runtime | Enforcement and runtime-derived leases, not permission to activate stale authority | Do not disable enforcement or change its timing/policy | Explicitly distinguish captured durable authority from ephemeral runtime state; bounded barriers must preserve ordinary watchdog behavior | Restore/reconcile from current authority; no stale lease or stopped enforcement shortcut |

The immediate concrete blocker is production integration of the OWNER Docker-import/accepted
PostgreSQL/native-write row. The isolated logical boundary qualified below now supplies an actual
database lock mechanism, but installed admission gates/replay alone and native file paths are not
its equivalent. The causal protocol still has no integrated production adapter for that row and
always reports capture_permitted=false. No manifest-only or source-only
maintenance hold can satisfy it. Remote/file rows must also be covered before final acceptance.

## Causal protocol and independent reader

New `control.capture_fleet` uses signed per-participant receipts with exact source,
coverage and late-policy pins, operation/challenge, boot and immutable journal-path binding.
Every CAPTURED receipt depends on the complete four-host HELD set. Every SEALED receipt
depends on the complete captured set and independently checked exact file manifest while
that participant still owns its original barrier. Release requires the complete seal set.
This causal ordering, not UTC overlap or cross-kernel monotonic comparisons, demonstrates
the interval for the qualified adapter. Local capture_group and strict Gate.drain are unchanged.

Protocol errors, incomplete sets, lost leases, changed bytes/signatures/operations, wrong
boot/journal and controller EOF/deadline yield failure, retaining partial files. A failed
operation is not retried. An exact completed request returns its retained receipt without
re-entering the barrier or rerunning snapshot effects. Journals cannot be reused/rebound.
The reader validates exact bytes and composition; source authenticity/coverage remains
the responsibility of trusted, pinned physical adapters, not self-declared inventory hashes.
No production signer keys or HA activation authority are introduced by lab receipt keys.

Final isolated four-host operation: `715d0af8b59b9ca47ffa9e5c31e71443`.
Protocol SHA256 `e794f6025df08897a6be6b13f8a3af1107bc76a9522a553d28f7c325ccd959da`;
adapter SHA256 `f134c07aa601930eb9e26f3aa48adb656dad9b7575f9c408660e7db91dbeef40`.
Independent exact-set manifest SHA256 `791a4631ca8eb60de023d0db73c849f06f39b1de42def79f7d84558920e10c6c`.
All four distinct real kernels use disposable SQLite data, not product paths. A writer
accepted before capture is blocked by its actual SQLite writer lock, its queued intent
is captured, and after release its journal reconciles exactly one effect; a duplicate
adds none. Four independent post-release readbacks confirm completion, not merely SSH exit.
Lab private keys/state remain in new private operation directories, never Git/CI artifacts.

## Qualification and retained refusals

-112 focused tests/0 skips pass: causal protocol, existing local group and strict gate.
  Real process/channel tests cover controller EOF, incomplete frames/deadline, lock release;
  other tests cover response loss, incomplete participants/files, barrier loss during capture,
  changed snapshots, replay and boot/journal binding. CI at the source commit is required.
- The first protocol draft allowed reuse of an operation at a different journal path.
  A failing counterexample is retained. Boot/path/identity binding fixes it; the final
  four-host qualification is a new operation, not a reinterpretation of the earlier run.
- Exact console3af9fbf9 and PostgreSQL18cfe3ef pass6 new isolated late-import/replay checks,
  operation39a42a1fe54c6ca6d840ec927e77afe0. Actual loaded inventory/probe/subscription/metadata/
  model hashes match source. No product mounts, external network, live database or messages.
  The disposable native containers are removed; existing PostgreSQL is never recreated.
- Retained native prerequisites: first PG fixture used wrong UID999 and timed out. That
  attempt lacks server logs, so its detailed initiating cause is not claimed; image identity
  subsequently verifies UID70. The next attempt names a test absent in the old installed
  image. A self-contained six-case fixture then passes; both refusals remain recorded.

Private evidence: `/mnt/data/fc-ha02-common-20261127`. Source-only changes can be reverted
normally without changing installed images, bindings, support or any product data.

## Preserved history, custody and next step

Fresh readback verifies the prior160 root marker bytes/inodes/modes/UID/mtime,29 inventory
and14 probe markers unchanged. A non-atomic name census observes175/37/14; additional names
are retained separately, not declared settled or assigned a historical outcome. Original
root119, inventory3+12+6, later additions, probe14 and support33 remain separate. Accepted
support history is identical. No marker is deleted, whitelisted or used to weaken drain.

The mandatory encryption input still has no supplied approved HA wrapping-key reference;
a protected path was requested, never the secret in chat. Joker, NL2 destination
`/opt/apps/family_connect/ha-recovery/`, KeePassXC and Family-Connect.kdbx remain fixed.
Actual off-laptop custody/access remains unconfirmed. This input is not the only blocker:
the production downstream adapters above are still required independently.

**One next step within the same NEXT:** connect the qualified OWNER logical PostgreSQL boundary
to the causal participant with exact installed database/schema/readback binding and native-file coverage,
then complete the remaining matrix coverage before any production common stop/capture.
There is no production kit ID, new stopped-support snapshot, independent encrypted-kit
PASS or linked normal-resume receipt from this iteration. e4eace1a remains history.
Normal services continue; no production holds were left by these qualifications.
Console automatic reboot startup remains unqualified: order runtime directory creation,
accepted support/IPC recovery and effective-config console startup in an isolated fixture
before any installed startup change. Current HTTP success is not reboot acceptance.
Onboarding remains the separate required result: prepared VPS → IP/access/roles →
normal enrollment → verified active node, not a consequence of an encrypted recovery kit.

## Logical PostgreSQL boundary follow-up

13:25UTC source-only `fc_control_plane.capture_pg_boundary.PostgresBoundary` closes a concrete
mechanism gap rather than treating an empty ExecIDs census as proof. It holds SHARE locks on the
exact persistent public tables and PostgreSQL catalogs and ShareRowExclusive locks on all sequences.
Sequence locks are obtained by same-value ALTER CACHE inside the never-committed transaction;
release rolls it back. It refuses unsupported/uncovered relations, changed schema, an already
accepted conflicting transaction, reacquired/different XID, missing locks and expired deadline.
PostgreSQL17 transaction/idle timeouts bound an abandoned controller independently of its client.
The first failure survives a cleanup failure. Logical read/dump remains possible while writes wait.

This is a dedicated database/cluster operation, not a general-purpose host fence. It does not
cover native filesystem/configuration writes, external SQL-function effects, another database,
arbitrary unknown SQL replay or remote receivers. No integration or installation into working
console/publisher images is claimed. Existing helpers and their accepted meanings are unchanged.

Exact final native operation2cbcb034addbfbb90ac7851eb19bcd04, boundary source SHA256
96ce0c6354ba69fb1c8279abe39de42823d2594c518a1cea121a226d3f0b0b28:

- 20 checks PASS on console3af9fbf9/PostgreSQL18cfe3ef, private network/tmpfs, no product mounts.
- INSERT/UPDATE/DELETE/TRUNCATE, nextval/setval, table/schema DDL and large-object writes block;
  reads remain usable. Incomplete coverage, an active earlier transaction, lost/reacquired barrier,
  server timeout and killed controller are explicitly exercised. A pre-existing CACHE32 sequence
  allocation cannot bypass the lock; last_value/is_called/cache survive the barrier unchanged.
  Original history/schema survives.
- An actual Docker exec and its DB connection exist **before** the boundary. Its late INSERT
  independently appears as a server lock wait. The barrier holder reads no late effect; pg_dump
  succeeds. After release, the original request and identical retry leave one unique effect.
- A separate pg_restore/psql reader restores that held dump into another disposable database and
  finds only the original history/unchanged sequence. Dump SHA256
  1b6fc5561008bd37dc88cefd34c0b1a8e4e721ca2ddf0cf8fa6d562cd9c81949,2241 bytes.
  Reader projection SHA2567f224f12486feedd0a36c93a3ae9c8ba3432a3620307a3d7383a28bf610b2b89.
- Native01 retains the fixture's malformed Docker mount argument refusal before console execution.
  Native02 retains17 PASS/one failed test expectation: PostgreSQL reports TransactionTimeout during
  rollback after its timeout already releases locks. Explicit failure/cleanup behavior is now tested;
  it is not hidden as a normal release. Native03–06 remain earlier qualification receipts.

This dump is **synthetic and unencrypted**, not a component of the requested production kit.
The actual delayed business-import replay checks remain the separate6-case qualified scope.
No history marker is settled by the new boundary; ordinary Gate.drain is unchanged.

Causal checkpoint010d8c6c3dbe77734f6a44ed210e32ea8ecdf72f is committed/pushed and independently
matches the feature remote. Causal CI46005005447, Control panel46005005254 and Android46005005298
are SUCCESS; phase0/Linux/native support are still running at13:25. The new database-boundary
source's applicable CI must be checked separately after its own push. No source push is deployment.
