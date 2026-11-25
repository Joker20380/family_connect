# 25 November 2026 — expiring OWNER console TCP admission

Selected task: CONTROL-HA-20261123 / HA-02. This closes the bounded console TCP admission
component alongside the already qualified publisher dispatcher hold and stopped replacement.
It does **not** establish independent publication/support/manual settlement or complete OWNER
drain. Replication remains PASS; current-input trust, coherent all-writer capture and final
independent recovery remain the same three partial gates. No HA-03 cutover or new ETA.

## Implementation and boundary

`scripts/control_ha_ingress.py` applies one atomic nftables transaction in the **console's own
network namespace**, never the host firewall. It creates a uniquely named `inet` table, an
input chain with accept policy and a timed set containing only TCP port8000. The only rejection
matches initial SYN without ACK; established TCP traffic continues. It does not stop Gunicorn,
pause its workers, touch outbound connections or operate another service's network namespace.
Table creation is exclusive (`create`, not idempotent `add`); a collision must not modify an
existing table. Deletion requires exact owned table/chain/set/rule readback, not a ruleset flush.

The set element expires in the kernel after1–5 seconds **from insertion**, without a persistent
userspace watchdog. There is no renewal/retry loop. A conservative local deadline begins before
dispatch; remaining lifetime is checked again after readback. A delayed/unknown Docker start or
nft commit can occur later than that deadline: do not claim expiry within5 seconds of controller
death in every failure mode. Unresolved helper outcomes veto subsequent operations and cleanup
through the lease; keep their intent/name/ID journals for independent reconciliation.

The one-shot helper is an offline-built scratch image containing only the host nft executable
and its12 ELF dependencies. Root-owned, non-group/world-writable inputs, bounded context and
individual file hashes are recorded. No package download, shell, Python, credential, host bind,
Docker socket mount, host PID/network namespace or privileged container is used. It drops all
capabilities except NET_ADMIN in the target network namespace, has a read-only root, no-new-
privileges,64MiB/8-PID limits and no restart policy. This does grant scoped firewall control;
it is not an unprivileged operation. Target identity/runtime, image/config and helper scope are
checked before use. Other Docker containers sharing the target namespace cause refusal.
This observation is not protection against a concurrent administrator changing that namespace.

Qualification tooling: Docker29.1.3/API1.52, Linux x86_64, nft1.1.6. Tool image built locally:
`sha256:cce90404f74be19e67dc9451e774f7e6b6e823787d88e325f89091a74844d98e`.
Context SHA256:`06898f7269643437fbedba2fa3f999c7fa115cb1331a799b69d1d1c1ba4a775e`.
It is not published or installed as a permanent service. The two existing OWNER application
images and configurations remain unchanged; no application/client version or catalog changes.

Existing/preaccepted HTTP connections, external effects, support IPC/transport work and manual
Docker/CLI imports are **not** proven settled. Installed Gunicorn23.0.0 sync workers force-close
responses, but this is not a drain receipt. Neither HTTP failure nor the rejection counter alone
authorizes capture or stopping writers. Every successful receipt explicitly retains
`work_settlement_proven=false` and `capture_permitted=false`.

## Verification

Python3.14.4 environment matches all26 control/identity lockfile pins. Final command:

```sh
python -m pytest -q tests/test_control_ha_ingress.py \
  tests/test_control_ha_owner_replacement.py tests/test_control_ha_owner_upgrade.py
```

**175 tests PASS /0 skips**,0.80s;63 new ingress cases. They cover strict rule/timeout/scope
validation, foreign objects/fields, expiry and early abort, changed runtime, confined helper
configuration, shared network refusal, unknown create/start outcomes and no retry/blind delete.

`tests/fixtures/owner_upgrade/ingress.py` qualifies four native cases at
**11:57:44.636171–11:58:01.363458UTC**. The original console image runs Gunicorn with a synthetic
WSGI response, isolated Docker bridge and loopback port; no product credentials or data loaded.

- A response started before closure finishes; a new connection is refused, counter increments,
  and explicit early removal restores access.
- Actual controller SIGKILL leaves new connections closed initially; kernel timeout restores
  access without a surviving controller. Expired owned table is subsequently verified/removed.
- A second atomic create collides with an existing table and fails without changing its readback.
- Actual rule commit followed by a synthetic lost helper response retains uncertainty, refuses
  release/retry and expires in the kernel; subsequent independent readback permits scoped cleanup.

The first stand attempts exposed nft's canonical flags expression, inherited set-element timeout,
Docker's CAP_NET_ADMIN spelling and its default PATH environment. Strict checks now use those
observed forms; no scope requirement was dropped. One initial pytest collection failed because
`request` is reserved as a parameter name; corrected before the final175-test run. Earlier
failed receipts remain private, not acceptance PASS. Owned synthetic containers/networks/helpers
are removed; final scoped inventories are empty. Force removal is used only for the explicitly
labeled synthetic workload in fixture cleanup, never the working console or publisher.

## Working result and rollback

At **11:58:52.421164–11:58:57.277053UTC** the working console probe succeeds. This is end-to-end
probe time, not an assertion of a continuously held capture interval. `/health/` returns200
before and after; a new HTTP request fails while the lease is checked, with1 rejected SYN and
3 seconds remaining in kernel readback. The scoped table is deleted and helper containers are
removed. At11:58:57.504684 both OWNER roles are healthy, restart counts0, with the same container
IDs, PIDs/start times and full effective configurations/mounts/network policies. Both installed
collector timers remain active. No container stop/start or publisher signal, DB restore, remote
service policy, RU/NL deployment, installer/catalog publication or durable network change.

Invocation after independent qualification of the selected tool image, using a new empty0700
private directory and the selected implementation branch (not main):

```sh
python -m scripts.control_ha_ingress --journal /absolute/private/journal --image sha256:QUALIFIED_IMAGE
```

Normal rollback deletes only the exact verified owned table and non-force removes exited helper
containers, with volume deletion disabled. On a controller/transport failure, retain all
journals and intent names/IDs; do not retry with a new journal, flush rules, remove running
helpers or signal workloads. Kernel expiry bounds each successfully inserted element to5 seconds;
it does not prove a still-unresolved helper cannot insert it later. First reconcile every
create/start outcome and target runtime, then inspect the precise recorded table. Confirmed
expired matching tables may be deleted through `Lease.release()` only with all original helpers
accounted for and exited. A mismatch remains an operator reconciliation, never blind cleanup.
An expired empty table does not block admission. No product state/config backup needs restoring.

## Evidence and remaining work

Private evidence root is located by `/tmp/fc-ha-ingress-current`; `final/` is authoritative.
Directories0700/files0600 after fixture cleanup. Raw effective configs, helper intents, readbacks,
tool library manifest and failed attempts stay local, outside Git/CI. Safe evidence digests:

| Artifact | SHA256 |
| --- | --- |
| Source | `cf2961c21ad8a60dbd34b1b2a0f8a43fd05751f8cd4ca36f05b039cda68e2e8d` |
| Unit tests | `90fc1efe1f7a9d321447bbcfc6e0c72293d6a0d5a08e0a3a02296fef63a0c77d` |
| Native fixture | `de1cc0cb92bd9839ac0510725d87b1ceee9fd852280e59d47ae352f576ecb2f9` |
| Tool manifest | `82530d19d7e48beabf18d1dd01329a6d02ab544a0cf9699a8534d3b994cf4451` |
| JUnit XML | `554bcb739100546acb4dc95db905b501212901743c722071e48573cc8b7eac91` |
| Native receipt | `6b7dadef63ef15e32b1aef59d481a7fd1f871721a026023d693347766219d8a8` |
| Both OWNER prestates | `f488c69cdabd89a4cfcb935cb2d555e6f65db9996fb5a60dfcf303b5f0108f27` |
| Working receipt | `b6b4b26added9432d1d45e354dd167711c4aeff2dc8e5e5360e84b344f0cf58a` |
| Final health | `d2a0068eaf77687cc75916856718a9e05bf33a8be992f3f386ed6b753dcb3b7b` |

Next within the selected HA-02 task: independently settle old publication/support/manual work,
then combine the qualified ingress/dispatcher/stopped-replacement components with real gate/runtime
attestation and guarded startup/abort. Remaining RU/NL participants, coherent all-store capture,
independent signer/checkpoint/access custody and approval, then final combined current-state
recovery remain. Do not repeat this completed ingress component as a new stage or treat the
source push as installing the pending admission overlays.
