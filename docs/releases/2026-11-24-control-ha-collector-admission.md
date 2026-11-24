# 24 November 2026 — HA-02 standalone collector admission

Selected task: CONTROL-HA-20261123 / HA-02. Source-only implementation, not a release,
installation, capture permit or completion of stage2. No RU/NL connection, service change,
deployment, runtime image build, application version/catalog change or public artifact change.
The preceding [NL2 reload diagnosis](2026-11-24-control-ha-systemd-lifecycle.md#nl2-manager-wide-reload-cause--read-only)
is complete and is not repeated. Its strict lifecycle veto is unchanged.

## Completed source boundary

The standalone OWNER inventory monitor and network probe were outside the existing request/
manage.py boundary. They initiate imports through Docker, catch failures, write fallback
observations and, for inventory, publish a local receipt. A Docker-client timeout does not
prove that the server-side import stopped. Gating only the successful import was insufficient.

- `control_plane/collector_admission.py` admits the entire local cycle using the existing
  opt-in `FC_CONTROL_CAPTURE_GATE`, before creating `.local`, lock files, or dispatching work.
  The existing nonblocking cycle lock is retained. A known duplicate cycle exits cleanly,
  without generating an unresolved-operation marker or altering the original cycle.
- `monitor_inventory.cycle()` holds admission through collection, every inventory/subscription/
  transport/metadata import and fallback, snapshot deletion and final receipt replacement.
  All subprocess calls record uncertainty before a caught failure can be converted into a
  normal receipt. A later successful fallback or retry cannot erase the earlier marker.
- `probe_network.cycle()` admits probing and all imports together. A caught import failure
  still permits the existing observations of other endpoints, but no clean capture receipt.
  Network outcomes such as timeout/refusal remain observations, not VPN recovery actions.
- `collect_inventory.collect()` is admitted even when called programmatically. Its CLI parses
  arguments first, so `--help` neither creates a marker nor needs an open gate. HMAC-key and
  snapshot creation occur inside the operation; they cannot start while admission is closed.
- All three actual CLI entrypoints return75/`CAPTURE_BUSY` for a closed gate and
  1/`CAPTURE_UNAVAILABLE` for an invalid gate, without emitting private paths or tracebacks for
  those errors. Programmatic cycle/collect calls propagate the typed refusal.

Gate absence preserves existing behavior. This is not automatic protection: the effective
process environment must explicitly bind the approved gate. Existing collection/import
timeouts, timer/unit definitions, SSH policy and paid-watch/deny enforcement are unchanged.
No long collector is killed or given an extended guardian deadline to make capture succeed.
A cycle still in progress at the5s drain deadline means abort that attempt, not stage2 PASS.

The transient technical-metadata exporter remains a read-only producer, not a new admitted
DB writer. Its normal monitor launch and Docker import are inside the admitted cycle. A
manual export/import pipeline must use the approved importer and exact writer binding;
standalone direct DB access is not implicitly covered by the exporter.

## Verification

**117 tests PASS,0 skips**,6.30s;29 new collector cases:

```text
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_capture_collectors.py tests/test_control_plane_monitor.py \
  tests/test_control_plane_network_probe.py tests/test_capture_gate.py
```

Coverage includes refusal before files/dispatch, actual script exit codes, help, successful
imports and local finalization, duplicate-lock skip without uncertainty, every failed import/
fallback category, cleanup/receipt errors, and retention across a later successful cycle.
Two real local Python collector processes commit a synthetic SQLite record and are killed
while their cycle remains open: drain first refuses the active operation, then refuses its
durable marker; the committed record survives. Every test-owned process is waited/cleaned.
A separate native child commits after the adapter reports a synthetic timeout: the marker
still refuses capture after that late commit and a successful retry. This is an external-
completion oracle, **not** a live Docker/OWNER PostgreSQL import or installed-host qualification.

The initial run had112 passes and3 fixture assertion failures: the reused line reader retains
the newline, unlike the initial test expectation. Those assertions were corrected; no product
code change was needed for that failure. The intermediate115-pass run preceded two extra local
completion-failure cases. Only the final117-pass selection is reported, not an additive total.
Unrelated legacy transport-package/announcement provenance failures were not rerun or repinned.
The test runtime matches all26 distinct package versions in the control and identity lockfiles.
Five documentation files/1088 local link targets and whitespace checks PASS. The checker does
not fetch external URLs. An initial documentation-check invocation used an unavailable bare
`python`; rerunning with the explicit test-venv interpreter completed successfully.

Candidate source SHA256, not installed-source evidence:

| File | SHA256 |
| --- | --- |
| `control_plane/collector_admission.py` | `1e2e52abb618b620f9ba1e38dc9011d0143021d98cb3e5bfa535a3f79669808f` |
| `control_plane/monitor_inventory.py` | `8856e4454d4ecf68895a22a0d2cff0c87353d91b4ea5500c03383b8cd7aa3923` |
| `control_plane/probe_network.py` | `0adde03f5dc2a01756c42c5335f8cf4ff53f8c9d8651a4a3f0b9fa36d8f4407a` |
| `control_plane/collect_inventory.py` | `d3ed036ccd4824e93c50ab8a5fcd26a243664671f8620e245f4b2adba8d16a4a` |
| Existing `control_plane/fc_control_plane/capture.py` | `d4f5a258232d505f3ded09b7ce16a58f013a48dd451fa878d2a191c42ac7d60d` |
| Existing `control/capture_gate.py` | `da28d940e2e17e2dbb1fbbde8cc04c59d29cffc8762ada717135504e2ffa4906` |

## Joint activation proposal — not executable authorization

This closes the identified standalone-collector **source** gap. The following is the bounded
activation design, with unresolved approval/binding fields explicit. Do not substitute new
censuses, another replication rehearsal or test counts for completion of these rows.

| Participant | Exact boundary to approve and bind | Still missing before activation |
| --- | --- | --- |
| Operator workstation | Inventory monitor timer, network-probe timer and manual `collect_inventory.py` use the six admission-related files above plus their existing collector/import dependencies and one explicitly configured gate owned by their actual UID; guardian runs as that UID | Full effective interpreter/dependency/source closure, unit argv/environment, gate path and inode/mount identity, guardian binding and rollback prestate; none was installed here |
| OWNER console and system publisher | Existing admitted WSGI/manage.py/publisher sources, approved images and writer-specific gates; include readback of their real bind mounts | Independent acceptance of actual image/config/UID/mount bindings and installed launch paths; previous local candidate images are not deployment evidence |
| RU management writers | Existing HTTP, background retention, timers, operator commands, peer worker and their receiver dispatchers all participate in the same approved group | Actual loaded closure/dispatcher bindings and outstanding external completion, including collectors that import through Docker rather than HTTP |
| NL1/NL2 receivers and transport | Existing receiver gates, renewal settlement and strict service-lifecycle veto; preserve native application/registration locks, emergency stop and paid-watch | Installed support/helper/transport lifecycle admission and exact runtime completion remain incomplete; current NL permission does not allow working-service installation/change |
| Manual/operator writes | Approved `manage.py` entrypoint for ORM/management work, admitted product CLIs/receivers; explicitly exclude direct DB clients, raw Python ORM/`call_command`, Docker exec/SSH bypasses and deployments during the interval | Owner/operator agreement on the closed writer set and actual access/dispatch binding; this code cannot prevent an unrestricted administrator from bypassing it |

The host-side `FC_CONTROL_CAPTURE_GATE` is inherited by its Python collection child, **not
automatically forwarded by `docker compose exec` to a container**. The container must have its
own explicitly configured admission and guardian. Do not claim the workstation gate covers
arbitrary OWNER writes. Different UID/mount namespaces may require distinct participants;
never make0700/0600 gates world-accessible to share them or use equal path strings as proof
of equal inodes. The source-only collector change does not rebuild or update the OWNER image.
The six hashes are not a closed executable capsule: existing pseudonym, inventory, metrics,
transport, subscription and network-probe modules and configuration-selected sources must also
be bound before activation. No installed-closure approval is inferred from this source table.

Execution order after the exact bindings and required changes are approved:

1. Preserve each approved installed source/config/unit/dispatcher prestate and recovery access.
   Record pending operations; any unknown marker remains a veto. Agree that no manual bypass
   or deployment can occur. Do not reset markers, stop paid-watch, or start previously failed
   services. Working-NL activation requires a separate explicit scope, not this source push.
2. Activate only the approved participants with capture disabled. Verify their actual loaded
   source/config/gates and native completion. The NL2 manager-wide reload flag requires the
   separate host-wide disposition in the lifecycle report; this proposal does not authorize
   `daemon-reload`, hide that flag, or treat four observed services as three allowlisted units.
3. Use the existing sealed guardian/coordinator with all approved participants,5s local drain
   and2s local hold. A busy collector, unsettled child, lifecycle change, pending marker or
   missing participant aborts the attempt. No indefinite wait or silent partial capture.
4. Capture the approved store/file/operation set only during the proven joint interval; verify
   readback and release/expiry. `LOCAL_INTERVAL_CONFIRMED` alone is not capture authorization.
5. Obtain independent approval of that exact checkpoint, off-laptop key/access custody, then
   perform the final combined OWNER/canonical/fleet recovery with post-ACK reads, stale-copy
   refusal and verified cleanup. Earlier isolated replication/recovery results are retained.

No live activation command is supplied while actual bindings and NL change scope remain
unapproved. These are the **same four gates**, not new stages: isolated replication PASS;
current inputs/trust, coherent all-writer capture, independent custody/final recovery partial.
Next selected work is completing these actual activation bindings and the manual/transport
participation decision, not repeating the collector implementation or completed NL2 diagnosis.

## Rollback and publication

No live rollback is needed. Before any future approved activation, preserve the prior collector
files and actual timer/unit environments. On failure, first abort/release this capture and keep
capture disabled; let existing admitted work settle, preserve markers and evidence, then revert
only the approved collector source/environment changes. Unsetting the opt-in while a capture
is active is a bypass, not rollback. Do not restore an old DB, erase observations/tombstones or
stop retention/paid-watch to hide an unfinished operation. Collector rollback cannot cancel
an already dispatched Docker import; that operation still requires independent reconciliation.

Safe source/tests/docs are committed and pushed on the existing feature branch; main receives
navigation only after remote SHA verification. Private gate directories, synthetic databases,
test logs and runtime evidence stay outside Git. No release/tag or installation claim is made.
