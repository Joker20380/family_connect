# Persistent reconciliation supervisor

Deployed on the RU gateway on 2026-09-29 to avoid creating/removing a Docker
container on every reconciliation pass. Uses the existing
`family-connect-product:0.2.1` image and mounted project; no image or schema update.

`worker.py` starts a fresh existing `control.product.admin reconcile-peers`
process each time. It preserves a 15-second delay after completion, including
failures, and bounds each child to 60 seconds. Timeout kills/reaps the child
process group. SIGTERM/SIGINT stop new cycles and allow the current bounded cycle
to finish. Docker stop allows 70 seconds; systemd stop allows 90 seconds.
As with the old worker, a timed-out external Docker exec may require the next
idempotent reconciliation to confirm the resulting gateway state.

The wrapper emits only the cycle exit code: 124 means timeout, 127 means process
launch failure. Child stdout/stderr are discarded to avoid logging device IDs or
exception details. Inspect private state locally through the existing operator
tools when a cycle fails; do not publish DB rows or credentials.
Docker logs use the local driver with two 1 MiB files. The attached CLI also
delivers the small cycle summaries to the system journal.

## Install or update

1. Copy the reviewed worker to `deploy/product-peer-worker/worker.py` under the
   existing `FC_PROJECT_ROOT`; copy `deploy/systemd/family-connect-peer-worker.service`
   to `/etc/systemd/system/`. Do not copy or change the private product env/DB/keys.
2. Refuse an existing unrelated container named `family-connect-peer-worker`.
   Check the installed image and environment paths. Keep the old timer/service
   available for rollback. Run `systemd-analyze verify` on the new unit.
3. Run `systemctl daemon-reload`, disable/stop `family-connect-peers.timer`, then
   wait for `family-connect-peers.service` to finish. Do not overlap workers.
4. Enable/start `family-connect-peer-worker.service`. Check at least two cycle
   exit codes, aggregate outbox errors/matches/check ages and unchanged VPN/API
   start timestamps. Inspect the running container's logging configuration.

The new unit conflicts with the old service and timer. Do not enable both.
Its image, no-network/read-only/cap-drop isolation and permitted writable mounts
are the same as the old worker. Fresh child processes avoid retaining DB
connections, imported application state or leaked per-cycle resources.

After code/unit updates restart only this supervisor and repeat acceptance.
Systemd restarts a failed supervisor after five seconds. If an unclean Docker
daemon shutdown leaves a conflicting named container, inspect its ownership/state
before removal; do not delete arbitrary containers to clear a name conflict.

## Rollback

```sh
systemctl disable --now family-connect-peer-worker.service
systemctl enable --now family-connect-peers.timer
```

Wait for the new worker to stop before starting the timer. Verify the first old
cycle succeeds. No database restore/downgrade, VPN/API restart or peer deletion
is needed for this supervisor-only rollback.

Focused checks:
`python -m pytest -q tests/test_peer_worker.py tests/test_gateway_reconciliation.py tests/test_gateway_adapter.py`
with the control and identity lockfiles installed.
