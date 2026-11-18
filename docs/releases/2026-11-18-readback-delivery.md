# 18 November — readback delivery qualification, NOT_DEPLOYED

## Entry and recovered handoff

Remote readback confirms main `bc8f7b5b42800269aeb43bcf54059205e7a7cbf7`,
accepted PR44 head `ea6619962a7197d95d578d089971b8d859db206f`, identical tree
`037783c0db372a6290917420319a0b6de56d399d`. All ten applicable head workflows
and eight automatic merge push workflows succeeded; merge runs are attempt1.
[Terminal head receipt](https://github.com/Joker20380/family_connect/pull/44#issuecomment-6970610003).
No additional source work was present in the clean readback worktree. It was
fast-forwarded to main without resetting the divergent primary checkout, its
eighteen local commits, dirty files, recovery checkpoints or other worktrees.

The latest recovery handoff lives in local commits `275d0118` and `ef55433c`;
ordinary pushes from that divergent main were rejected, not force-pushed. This
safe summary publishes their result without copying private backup/state/evidence.
RU AWG/TCP were recovered at12:18UTC on unchanged legacy bytes. Both NL MESH
resumed13:05; shared HTTP resumed13:10 after unprepared ownership cleanup and
fresh normal leaf/CRL renewal COMMITTED. No old DB or expired credentials restored.
RU and both NL signed configuration HTTPS responses passed. Each NL separately
passed public auth, four HTTPS, three DNS and expected-egress tests. Final RU
14:38 readback retained original invocations, NRestarts0, exact20/20 transport
sets,68 matching revisions and fresh readback. Scheduled renewal/directory-sync/
paid reconciliation succeeded. Owner later reported “все работает да”; this is
affected-device recovery confirmation, not a specified device/transport matrix.

Installed node SHA256 remains
`125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c`, gateway
`9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`, reconciler
`ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa`,
HTTP `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`.
Maintenance remains the fcb31164 capsule. observations-v1 was NOT_DEPLOYED.
The recovery preserves paid-v2, HMAC2, metadata tombstones, support state and
notification baseline/cursor. A later legitimate support_sender change is retained,
not overwritten to manufacture equality with the backup. Initial renewal writer,
storage latency and future due-rotation continuity remain unresolved. This task
does not repeat recovery, access production, restart services or send messages.

## Watcher race and source qualification

On accepted merged bytes, a real watcher process throws ENGINE_READBACK_MISMATCH,
requests asynchronous stop and exits. A second real registration process obtains
the actual application flock, makes three engine queries and returns a successful
ACK while modeled stop completion is still pending. The synthetic clock correction
preceding that reproduction is retained locally; it was a fixture error, not proof.

Candidate serialization arms an `application-incomplete` intent directory under
the application lock before the body. It is removed only on successful operation;
failure keeps/rearms it before external stop and diagnostics. Subsequent writers
fail with TRANSPORT_RECOVERY_REQUIRED even after the failing process exits and
releases its flock. The collector also rejects the fence. Intent creation/removal
does not add per-cycle fsync; it is a same-boot exclusion mechanism, not a claim
of disk power-loss durability. Reboot still requires fresh validated authority and
readback. `paid-recover` is explicit: application lock, loaded/inactive-or-failed
watcher/AWG/TCP, MainPID/ControlPID0 and no pending Job; retain authority and first
failure. Operator fencing is required before recovery to prevent external starts.

PR44's budget still begins before lock open; the handle outlives final deadline
validation and error handling, ACK remains after successful operation exit.
190 transport tests pass, including process/flock reproduction, first error,
all previous serialization regressions and explicit recovery after interrupted
durable writes. This is NOT real systemd acceptance or physical power-loss testing.

## Installed systemd acceptance and final review gates

Installed c188b591 bundle already passes real systemd cold-start/effective units,
18 native queries/zero repeated syncs, watcher failure with both actual engine PIDs
still deactivating and stop Jobs pending (no concurrent ACK), actual termination,
explicit recovery, generation/collector negatives and mandatory write error/delay.
The same fixture on exact merged PR44 reproduces a successful concurrent ACK with
both real engine stops pending (`REPRODUCED_UNSAFE_ACK`, not an acceptance PASS).
The first full c188 run fails later at terminal reconciliation: the dense sequence
of intentionally restarted fixture cases exhausts TCP's unchanged5-start/120s
systemd limit. Preserve that FAIL; subsequent cases are separated by the real125s
quiescent interval, not increased service deadlines or reset-failed/restart loops.
The new packager preserves package_ru_lifecycle.py unchanged and checks its exact
PR15 baseline hashes before replacing only transport_gateway within the node ZIP.
It carries coordinated gateway, all five collector modules, units/drop-ins, explicit
legacy/observations configs and verified rollback bytes. It excludes live state and
central HTTP/operator/reconciler archives. A separate self-review regression rearms
the intent fence if explicit recovery's final deadline fails after directory removal.

The complete6aba3211 installed run is PASS with cleanup PASS. Runtime node SHA256
`f454af6a36d4005c0b159bc5c6ade992951a1ca583d0a25e1e59344ea0c55c70` is verified
at the real ExecStart import path, not imported from the checkout. Systemd PID1,
private cgroup/network/PID/mount namespaces, no host mounts/ports/socket and bounded
resources are checked. Cold-start/dependency order, READY before completed readback,
WATCHDOG only after it, mandatory write error/9s delay and actual watchdog kill on
a30s blocked write pass. Both engine PIDs and stop Jobs remain real during the
concurrent-registration attempt: no ACK/collector ok, then all three processes stop.
First error survives explicit recovery and subsequent faults. No service deadline,
StartLimit, restart policy or production setting is increased to pass this test.
Sanitized installed-run receipt SHA256:
`118707c81ea4192a2b12c9b2871d6373c12edced0bc5f26ae15617b8a3c282a7`;
separate exact-PR44 real-systemd unsafe-ACK reproduction receipt:
`c0e64a16cdba7a9b667e56f26b49923283f4973c5b7d44858c00a341880653a4`.

Live expiry/renewal/revoke flows pass. Generation changes and missing/corrupt/stale/
old-generation observations and an active writer all produce unavailable. After
post-install paid extension/revoke and a prepared operation, rollback to exact node
125c796a/gateway9023d2c3 retains every decision/boot/deadline/prepared field; no DB
or transport-state is restored. Actual legacy readback/deny traffic and return to
candidate also pass. Six unchanged cycles of the installed legacy and candidate
each execute18 real AWG/Xray queries, collector6/6; durable/file/directory sync
counts12→0. Each experiment records its actual archive loader/hash. This does not
attribute historical storage latency or guarantee mandatory-write latency.

Final refinement adds the runnable operator-side collector source closure, closed
manifest verification (reject unlisted files/path escape/symlink/permission drift),
installed unknown-mode negatives, effective-unit/native hashes and explicit no-late-
application/no-notify-during-durable-fault assertions. Runtime node bytes remain
f454af6a; final rebuilt manifest and repeated strengthened installed qualification
are mandatory PR receipts.197 transport/package tests and public-source/links/
whitespace gates accompany these changes. Applicable exact-final-head CI and
self-review must complete before PR45 leaves draft; no previous PASS substitutes.
Production NOT_DEPLOYED; no installer/catalog/version change. Final refs, run IDs
and manifest hashes belong in the PR receipt, without another cosmetic commit.

[Future RU-only delivery, pins, compatibility and code-only rollback](../operators/transport-readback-delivery.md).
