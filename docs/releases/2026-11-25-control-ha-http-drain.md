# HA-02 — receiving HTTP graceful stop

Date:25 November2026. Selected task:CONTROL-HA-20261123 / HA-02, stage2 of5.
Source/package qualification, not production adoption, capture acceptance or HA-03.
[PLAN](../PLAN.md) · [STATUS](../STATUS.md) ·
[Preceding receiving export repair](2026-11-25-control-ha-notice-export.md).

## Actual installed boundary

Read-only strict-pinned SSH to authorized RU at13:22:32.721405UTC observes
`family-connect-friends-http-candidate.service` active/running, MainPID43082,0 restarts.
Actual executable is Python3.14; the running command names
`/opt/apps/family_connect/private-paid-transport-v2/friends-http.pyz`.
Its84746-byte SHA256 is
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`.
The exact archive is retained privately, not added to Git. No gate argument/environment is
present. Effective unit uses `KillMode=control-group`, SIGTERM and90s stop timeout.
Installed source has ordinary daemon-threaded `ThreadingHTTPServer`, no TERM drain handler,
and retention stop events without joins. Default termination can interrupt exports and signal
admitted subprocesses. The observed three threads do **not** attest idle/settled request state.

The full newly built source archive is not a minimal patch on this installation:21 existing
Python members change,3 are added and1 removed. Do not deploy it as an implicitly approved
one-file notice hotfix. Historical served-baseline pins remain untouched.

## Repair and stop contract

`control/friends/http_lifecycle.py` supplies the production receiver loop. TERM/INT only set a
main-thread stop flag; they do not raise through a writer or invoke blocking shutdown inside
the signal handler. The loop stops accepting, closes its listener, signals both retention
workers, and joins non-daemon retention/request threads before returning. Repeated signals
continue waiting rather than reverting to immediate termination. Signal handlers are restored
after cleanup, including listener-bind or second-worker startup failure.

Accepted sockets have the existing five-second I/O timeout **before** header parsing, not only
inside POST. A client that sends incomplete headers and stops transmitting cannot indefinitely
hold shutdown. This is an I/O inactivity deadline, not a total transaction/slow-client deadline.
An already admitted request can still complete its database/file writes and HTTP response.
The previous export repair retains pending on failure or lost ACK; successful process exit is
not permission to clear earlier uncertainty or infer capture readiness.

Both real retention loops return a joinable stop event and use non-daemon workers. Their data
projection imports do not acquire a new eager HTTP dependency. The closed HTTP manifest and
metadata HTTP overlay inventory carry the new lifecycle module. The historical metadata
overlay is not built or installed here; this inventory update is not renewed release acceptance.

The separately packaged `http-graceful-stop.conf` must accompany any qualified new receiver:

```ini
[Service]
KillMode=mixed
KillSignal=SIGTERM
SendSIGKILL=no
TimeoutStopSec=infinity
```

This avoids sending TERM to admitted child commands and disables automatic forced termination.
A stuck write leaves the unit stopping and requires diagnosis; it is not a timed permission to
kill, delete pending markers, restore stale databases or start a competing writer. The drop-in
alone cannot make the old installed program graceful. No unit policy is changed on RU here.

## Validation

Final run13:33:49.940875–13:34:53.114172UTC: **269 PASS,0 skipped**, pytest58.90s, including
**12 new lifecycle cases**. Python3.14.4/pytest9.1.1/psycopg3.3.9 and disposable PostgreSQL17.11
with pinned image `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
Selection: lifecycle, notice publication boundary, capture gate/integration, HTTP startup,
diagnostics/metadata repositories, metadata panel overlay, and HTTP final artifact closure.

New cases cover actual TERM/INT/repeated signals during a paused durable first-file export;
successful ACK only after completion; caught partial failure; actual SIGKILL; TCP reset/lost ACK;
both actual retention loops; incomplete headers; partial startup cleanup; closed PYZ execution.
Only synthetic destinations/failure pauses are injected; publication, file durability, gate,
socket handling and lifecycle code are real. Nonempty notice fixtures are not working data.

With `FC_TEST_SYSTEMD_HTTP_DRAIN=1`, a uniquely owned user-systemd service uses the packaged
settings. A real request spawns an actual child in the same service cgroup. `systemctl stop`
closes admission while the unit is `deactivating/stop-sigterm`; both processes survive until
release, publication returns200, child/parent finish and gate drain succeeds. Effective mixed
kill mode, TERM, no SIGKILL and infinite timeout are read back. The child is not replaced with
a mock success. No existing systemd service is stopped. Final fixture units and owned PG
container are independently confirmed absent. This is not a live-RU restart qualification.

Earlier focused selection:96 PASS. Two test expectation mismatches (busy versus retained
uncertainty) and a later child-fixture quoting error were corrected before the final all-green
run; intermediate failures are not acceptance results. No nginx/TLS configuration changed;
no full TLS activation/release gate is claimed.

Private locator: `/tmp/fc-ha-http-adoption-current`. Receipts include `ru-runtime.json`, exact
installed source archive, `ru-after.json`, `candidate.json`, `final.xml`, `final.log`, `run.json`,
`cleanup.json`, `owner-health.json`. Source capsules, fixture databases, tokens and raw runtime
observations remain private outside Git. Safe digests:

| Evidence | SHA256 |
| --- | --- |
| Lifecycle source | `3b25ad6378991ec9703aaf0b1ab8f9f1896e97cc4ddf2e52df7ab450eb5240de` |
| New tests | `08c106332637ae8b13c2b866da3fde4c0fa19175e9ae811cf3f43e18cc94306a` |
| Final JUnit | `9d59c43a845d25eb5a262d3bf3cb195d75eaf19e5f8aa68dd4eebdd127c2fb7b` |
| Initial RU observation | `e92fd72fb65c87ab009b22b31d8e0fd67c00b9a6181e4db7bc28e489b2a9454a` |
| Candidate/delta receipt | `ece18dd0f4aaf6ab16e5a194ec75da50e2ea6c0c1f643522667f866636546608` |

## Rollout, rollback and next action

Full candidate SHA256 `25763b05fa15c660be6c35e5e26364146133a5cb5f7b8de202beee6b4f8fd7c1`:
built and tested, **not installed or distributed**. No client/product version, catalog,
installer, signing operation, public feed or invitation-page change. Follow-up RU readback
confirms the same PID/archive, active and0 restarts. OWNER console/publisher/PostgreSQL remain
healthy with0 restarts; both collector timers active. No NL host contacted or policy changed.

There is no working installation to roll back. Retain the verified installed archive and exact
effective unit prestate privately. Source rollback is an ordinary revert, not history rewriting.
Future deployment must independently close legacy admission and settle old handlers/children,
review the actual installed-shape source delta, and pair source with verified effective unit
settings. Never terminate the old daemon-threaded server to manufacture settlement. Abort
before replacement if that proof is missing; keep current data and uncertainty evidence.
After new writes, rollback must preserve current DB/feed/pending state, never an old snapshot.

Immediate next action remains that installed-shape/legacy-work adoption boundary, not another
isolated replication rehearsal. Remaining support/manual coverage, actual gate/runtime
attestation and guarded OWNER startup/abort, fleet participation, coherent capture, independent
custody/trust/approval and final recovery remain in HA-02. Replication PASS in isolation;
the other three fixed acceptance blocks remain partial. No HA-03 or automatic failover.
