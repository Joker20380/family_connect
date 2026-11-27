# OWNER finite maintenance boundary — implementation checkpoint

This is the selected implementation within CONTROL-HA-20261123/HA-02, not an installed
all-writer adapter or permission to take a fleet capture. Installed image/source pins remain
in `scripts/owner_runtime_20261127.json`. No accepted component is reinstalled by these helpers.

## Finite domains and remaining launch guarantee

| Data / current writer | Already accepted work | Required admission / launch closure | Physical lifetime and late-work disposition |
| --- | --- | --- | --- |
| `/var/lib/docker/volumes/fc-control-plane-0_synthetic_state/_data/synthetic/registry.sqlite3`; console backend, `seed_fixture`, management/manual native Access | Existing transactions, seed `initializing.sqlite3` then rename, `registry.sqlite3-wal`, `-shm`, `-journal`; Docker exec/import and detached descendants | Mandatory owner-console gate plus actual Docker executor launch boundary; not just HTTP completion or stopping its parent collector | Whole executor cgroup must be empty before native seal; hold seed.lock EX, SQLite BEGIN IMMEDIATE and PG boundary together. Unknown sidecar/seed state refuses, never deletes. Preserve PG operation UUID/payload and SQLite event history; reconcile before replay, never mark UNKNOWN complete. |
| `/etc/family-connect-support/panel-pseudonym-aliases.json`, bound read-only at `/run/fc-pseudonym-aliases.json` in console | Host temporary-file/rename and alias-generation rotation; readers already holding old bytes | Close the actual host maintenance/manual launch authority before stopping that domain; container read-only leaf mount alone does not close host parent rename | Seal the parent, not only the file; capture panel and collector aliases with matching key/generation. Any known unmanaged old FD/mmap refuses. No implicit generation refresh on restore. |
| `/var/lib/fc-support-bindings/current.json` and `subscriptions.json` | `provisioning.support_bindings`, `provisioning.subscription_collector`, SSH children, `.bindings-*`/other temporary outputs and IPC cursor work | Root mandatory collector gate and operation-owned start conditions for `family-connect-support-bindings.service` and `family-connect-subscription-notifications.service`; finish full cgroups, not timers alone | Parent directory seal after clean domain exit; projections are evidence only, preserve original expiry and cursor/history. Rebuild through current accepted support authority after resume, not by treating old bytes as fresh permission. |
| Inventory/probe manual imports from the three accepted b49c76c0 roots | Host process tree, SSH clients and already submitted Docker exec which may outlive the client | Existing distinct mandatory host/manual gates; actual launch closure for `family-connect-readonly-monitor.service`, `family-connect-network-probe.service` and the three pinned roots | Host termination does not prove Docker/remote completion. Require executor or receiver lease for every dispatched row; preserve 3+12+6 inventory, probe14 and later groups separately. |
| Console PG / `public.console_operationrequest`, all qualified persistent relations/sequences | Accepted transactions, scheduler/ORM/CLI writes and previously submitted imports | Existing console/publisher mandatory gates plus qualified PG boundary and independently controlled executor domains | Exact PG scope/event-trigger prerequisites unchanged. Pair PG operation history with SQLite receipts while both leases remain held. Late reconciliation uses operation/event/payload identity; no generic RUNNING/UNKNOWN retry. |
| `fc-control-plane-0-system_publisher-1`, installed35158514, RU `/friends/notices/publish` | HTTP accepted downstream effect may outlive publisher/client; remote notice DB plus both exports and parent rename | owner-publisher admission is necessary, not a RU receiver/file fence | RU receiver/export row remains OPEN. Do not resume a pending effect without receiver replay/generation proof or qualified journal reconciliation. |
| Support state roots from accepted panel01 plan; support key/identity, cursor, queue, history | Retained support33 and additional records; NL1 mailbox generation and accepted link work | Accepted stopped-support8b9355db procedure, its exact root/controller/gate/NL1 checks and a new operation | A new stopped snapshot and independent reader must run inside the fleet interval. Do not nest `capture()` inside `boundary()` (distinct flock descriptions conflict). Reusing historical e4eace1a or completed Resume.run is forbidden. |
| Remaining OWNER configuration/credential inputs in custody `origins.json` / compose closure | Host maintenance or rotation of HMAC, collector aliases, publisher token, source maps, eight effective compose inputs and two effective env inputs | Pin exact installed origins and close their known launch/rotation authority; no secret values in report | Include exact bytes/bindings under the same closed-writer contract; never restore base synthetic/seed compose as the working panel command. Unknown paths/rotation domains refuse coverage. |
| RU/NL peer/operator/profile and remaining receiver-file rows of the accepted finite matrix | Remote receiver children, journals, queue and file rename after SSH returns | Receiver-side admission/generation authority and physical executor/file lease | Still OPEN; retain initial uncertainty and require linked late-effect handling. The new RU `ru-connect-bounded-4da8d7dc` source/unit closure must be included. |

The precise first production gap is Docker's executor-side launch authority for the installed
console: an accepted `/containers/{id}/exec` plus `/exec/{id}/start`, or a later
`/containers/{id}/start`/create, is not covered by the host caller's flock or a system unit condition.
The installed console is `fb1e6e64…`; its synthetic volume is RW and container mounts are private.
The source helpers do not yet provide a continuously held, reconciled per-Family-Connect Docker
launch boundary or prove all its prior mount namespaces/descendants gone. A root mount seal in the
controller's namespace is explicitly not that proof. Do not modify the whole daemon, neighbouring
applications or arbitrary OWNER directories to compensate. Enroll the specific console/publisher
executor domains and their launch authority, then qualify real old Docker exec/detached children,
late start and namespace views before production maintenance. Empty ExecIDs is not acceptance.

## Implemented lifetime components

- `UnitLaunchHold`: operation-owned system start condition, effective sd-bus readback on one
  connection, inode/content/inotify continuity, own-only removal. It does not stop a writer or
  implement a user-manager/Docker authority. The same operation can own distinct unit holds.
- `ClosedCgroup`: after actual launch closure, bounded SIGTERM of the recursive domain and kernel
  `populated=0`, then freeze to contain late attachment. No SIGKILL fallback is silently accepted.
  A late task or freeze rewrite invalidates the lease; a surviving writer refuses. No PID census
  substitutes for cgroup closure. The caller must prove that members cannot migrate out of it.
- `ReadOnlyTrees`: only explicitly scoped parent trees, unique mount IDs and a retained mount-event
  descriptor. RW→RO on the same mount and unmount/rebind both invalidate the lease. Conservative
  refusal on any mount-namespace event is intentional; there is no broad freeze/chattr operation.
  Old-FD/shared-mmap audit uses inode identity, including bind aliases, and is explicitly non-atomic:
  it is additional refusal evidence, never launch permission.
- `HeldSynthetic`: seed/SQLite locks outlive snapshot return; SQLite transaction-boundary statements
  invalidate the lease even if rollback/BEGIN occurs between checks. Actual qualified PG and native
  leases are checked before/after serialization. New purpose `family-connect/owner-held-pair/v1`
  captures PG operation history and expiry-preserving projections with the pair; legacy helper and
  accepted custody-format semantics are unchanged. A supplied stopped hash is not independent
  support verification (`stopped_support_reader_verified=false`, `fleet_capture=false`).

External restriction journals distinguish intent, observed physical identity, held, release intent
and confirmed release. Loss of response after unmount/thaw is read back without repeating effects.
Process death/hard deadline is not cleanup: mounts can remain and need explicit same-boot/namespace,
same-identity reconciliation. A new process may remove proven own restrictions, not adopt an old
capture lease or rerun incomplete effects. First failure survives cleanup/receipt errors. Complete
native release records do not themselves mean writers/support have resumed.

## Qualification and next integration gate

Native checks require root in a **private mount namespace**, isolated cgroups, disposable system
units and an isolated PostgreSQL container at the exact installed image digest. Product data/mounts
are never passed. They cover old writable FD/prefaulted mmap including alias paths, detached child,
late launch/rename, bounded refusal of a non-exiting writer, controller death/hang, loss/reacquisition,
lost release response, unchanged SQLite, held PG history and explicit late reconciliation.

This source qualification does not authorize production. Missing integration is the real Docker /
manual launch-domain enrollment, accepted stopped-support lifetime plus independent receipt binding,
and final OWNER custody-format adapter. Gate.drain remains strict and unmodified. Before stopping
anything, complete the existing-key consumer check outside the interval and qualify bounded recovery
using the installed panel image/config, prepared `/run/family-connect-support`, support/IPC and
ordinary collector cycles. HTTP PASS does not accept reboot startup.

Only then close the remaining RU/NL receiver rows and run one common causal operation. Keep root119,
inventory3+12+6, probe14, support33 and all later groups/history separate. No source-only hold, local
pair receipt, saved intent or matching UTC timestamp is a fleet capture permit. HA-02 custody,
source-host-free recovery, reboot startup and FLEET-PRODUCTION-ONBOARDING-1 remain separate/open.
