# Coordinated RU readback delivery — future procedure, NOT_DEPLOYED

This is a reviewed-candidate procedure, **not current authorization to deploy**.
PR45's3f5698e4 manifest is superseded for delivery by the P1 repair; it reproduced
unsafe concurrent ACK after pre-lock failure. Require the new repeat-review receipt,
not its old PASS. [Repair contract](../releases/2026-11-18-pr45-prelock-fence.md).
Require a separate explicit RU-only delivery instruction, terminal PR45 receipt,
successful applicable exact-head CI and the exact installed-systemd/rollback
manifest. No production command in this document has been executed by this task.
Do not touch Amsterdam, payments, messages, admission policy or public releases.

## Inputs and reproducible bundle

Use `python -m scripts.package_transport_readback --node <verified-legacy-node>
--gateway <verified-legacy-entrypoint> --source <full-reviewed-commit>
--output <new-private-directory>`. The builder reads committed Git blobs, not dirty
worktree files. Its manifest records source/tree/builder SHA256, each component,
ZIP member delta, file permissions and retained legacy bytes. Build twice into new
directories and compare every manifest/payload hash. Verify the manifest itself
against the PR receipt before trusting its file list. Never package state or keys.
`scripts/package_ru_lifecycle.py` retains its original exact-PR15/no-gateway-change
contract; do not use it for this candidate or relax its historical guards.

The saved18 November recovery pins are node
`125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c`, entrypoint
`9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`, central
reconciler `ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa`,
HTTP `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`.
These are historical inputs, not proof of a future live match. Fresh mismatches
require review, not overwrite. Pin unchanged native AWG/Xray binaries and inspect
effective unit fragments/drop-ins, ExecStart/ExecStartPre, dependencies, owners,
watchdog12s and operation8s before delivery. Source watcher already has Restart=no;
installed legacy watcher differs (Restart=on-failure). That explicit unit delta
must match the qualified bundle; do not infer installed behavior from source.

Node payload: `paid-transport.pyz`, `awg-gateway.py`, watcher unit and the two paid
dependency/preflight drop-ins. Existing AWG/TCP base units/native executables are
prerequisites, not blindly overwritten. The new archive changes only
`control/friends/transport_gateway.py` relative to accepted PR15; policy bytes stay
identical. Node configuration defaults to the legacy template (no readback_mode).
Only the separately selected observations-v1 template opts in. Unknown modes,
including an unsupported literal readback_mode=legacy, reject rather than fall back.

Collector is an **operator-side** component: the included `operator/` source tree
contains the driver, pseudonym helper and all five collector modules in their
expected layout. It streams read-only collection; the test's node-local `collectors/`
copy validates the exact same bytes, not a requirement to install a second daemon.
Install into the existing verified collector context, preserving its private
`.local`, HMAC2 material, aliases/tombstones, source maps, subscription pins and
notification baseline/cursor. Do not run a new empty context that generates a key.
Update only RU's entry in the complete per-node transport archive pin map, and
retain NL pins. No collector timer/background heartbeat can certify application.

Old pressure observer requires the exact legacy archive and durable timestamp
liveness; it is incompatible with observations-v1 and must remain stopped.
Old schema1-attempt readers cannot certify candidate freshness. The current collector
requires schema2 attempt/observation generation, real live producer, monotonic/wall
freshness and no application writer/fence. The repaired collector also takes the
shared `application-outcome.lock` and rejects sticky `application-failed`; ship it
with the repaired node, not an older single-marker collector. Do not unlink live
lock files (replacement creates a different flock inode). `prepare_paid_transport.py` is a virgin
node initializer, not an upgrade/rollback tool. Existing central reconciliation and
operator ACK/envelope interfaces are unchanged; do not replace their installed
archives or reset authority merely to match a newer source checkout.

## Separately authorized bounded RU-only operation

1. Capture fresh private authority/policy/state and effective configuration; preserve
   first-failure evidence. Back up securely and verify a separate synthetic/offline
   restore without restoring production. Record current decisions, leases, revisions,
   identity bindings, deny/revoke, prepared operations, HMAC2/tombstones, support and
   notification state. Secure copies stay outside Git/CI and command output.
2. Fence only RU's central command entry; keep both NL entries and their renewals.
   Drain in-flight handlers/reconciliation under the established operator interlock.
   Stop watcher/AWG/TCP as a group; require MainPID=ControlPID=0, empty Jobs and no
   forced-command handlers. `systemctl --no-block stop` is never completion proof.
3. Retain current `transport-state.json`, peers DB and central authority in place.
   Atomically replace only verified payload files, preserving required root ownership
   and0700 directories/0600 private code/config. Put the watcher/drop-ins in their
   observed locations, daemon-reload and compare effective definitions with receipt.
   No hidden drop-in may change8/12/120, Restart=no, BindsTo/After or KillMode.
4. Install matching collector source and RU pin; select the authorized explicit mode
   while stopped. For a retained active intent or emergency latch, execute `paid-recover`
   only with the external fence/drain and all three units demonstrably stopped. It
   validates retained authority and removes no first-failure/decision/preparation data.
5. Start watcher, AWG, then TCP sequentially. READY means dependency readiness only.
   Require first completed real readback, first WATCHDOG, collector ok with the live
   producer generation, exact actual/persisted engine sets and applied revisions.
   Expired leases remain deny; restore the RU command entry only after safe convergence
   and observe a normal fresh reconciliation across the next lease boundary.
6. Require bounded real permitted/denied synthetic flow evidence and fresh panel
   readback, unchanged NL service/renewal anchors, and preserved protected state.
   Do not use payments/messages/real-user fixtures. Retain timestamps and failure
   receipts. A later legitimate authority event is retained, not replaced with backup.

Abort on any hash/owner/mode/unit mismatch, active writer/job, unavailable/wrong-generation
observation, operation deadline/watchdog, unexpected admission, state loss or failed
dependency/traffic check. Keep the RU fence and stop the coordinated services; do
not increase timeout, add heartbeat, clear first error or enable automatic restart.
Storage latency remains UNKNOWN: fewer unchanged-cycle fsyncs cannot guarantee
latency of mandatory security writes.

## Authority-preserving rollback and return

While externally fenced/drained and all three units stopped, snapshot **current**
authority, including events after candidate installation. Clear active intent and
the separate emergency latch
only via the new stopped-unit recovery path before removing that code. Restore the
manifest's exact `legacy/` node/entrypoint/watcher bytes plus compatible dependency
drop-ins and explicit legacy config; do not restore old DB, transport-state, attempt,
observation or credentials. Retain the current observation-capable collector with
the legacy archive pin; it also validates schema1 legacy readback. Leave obsolete
observations ignored, never treat them as proof. Daemon-reload and sequentially start;
require fresh legacy durable readback, actual permitted/denied flows and equality of
current decisions/leases/revisions/preparations, excluding only recomputed applied
observations. Roll-forward to the candidate repeats the same guarded code-only
switch, retaining authority again. No rollback is accepted merely because services
show active. If retained state is incompatible, remain fenced for reviewed recovery;
never erase new events to make old code start.
