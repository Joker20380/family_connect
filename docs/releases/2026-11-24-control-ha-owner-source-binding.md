# 24 November 2026 — installed OWNER source and dispatcher binding

Selected task: CONTROL-HA-20261123 / HA-02. This continues the
[qualified guardian launch](2026-11-24-control-ha-guardian-launch.md) with actual installed
filesystem/configuration evidence, not another gate implementation. No deployment, image
replacement, service restart, version/catalog change or RU/NL access. Replication remains
PASS; the same three HA-02 acceptance blocks remain partial.

## Actual result and decision

Accepted observation: **17:38:42.056560–17:38:42.164965UTC**. Before/after container IDs,
images, start/restart/configuration/mount/argv/environment bindings and the ten selected
source-file records agree. The observer reads both fixed OWNER containers, not other
projects or an unqualified replacement image:

| Service | Installed image SHA256 | Present scoped files | Exact candidate matches | Missing admission modules |
| --- | --- | --- | --- | --- |
| console | `5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a` |8/10|2/10|2|
| system_publisher | `50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab` |8/10|2/10|2|

In each container, `/app/control/capture_gate.py` and
`/app/control_plane/fc_control_plane/capture.py` are absent. The six present files that
differ from the prepared candidate are `manage.py`, settings, middleware, backend,
support and system_publisher. Only `wsgi.py` and the `publish_system_messages` management
command shim match. No capture import/configuration syntax is mentioned in the eight
present scoped files. Syntax mentions would not prove admission even if present.

All ten selected paths resolve to the declared read-only container rootfs, with no covering
bind/volume/tmpfs override in the observed mount configuration. This describes configured
mount resolution, not a physical inode, filesystem durability or runtime-loaded-byte proof.
Neither service has `FC_CONTROL_CAPTURE_GATE` configured. Actual process UID observations
remain the earlier [10001/1000 observation](2026-11-24-control-ha-owner-admission-binding.md);
this source check does not add a new kernel-identity/namespace measurement.

The console's configured command mentions `sh`, `python`, `manage.py`, `migrate`,
`collectstatic`, `gunicorn` and `fc_control_plane.wsgi:application`. The publisher's mentions
`sh`, `python`, `manage.py`, `publish_system_messages` and `sleep`. These are lexical tokens,
not parsed shell control flow, proof of actual invocations or authority to execute startup
migrations. Full command/configuration values are hashed, not printed. In particular, do
not replace the effective commands with the repository's default Compose startup/seed flow.

Both containers expose zero retained ExecIDs in the accepted sample. There is no sampled
manual Docker command to inspect, **not proof that future Docker exec, direct ORM, shell or
administrator writes are fenced**. The source gate cannot cover code that does not enter it.
Remote support/publication completion remains outside this observation.

**Decision: configuration-only enablement is not viable for these installed images.**
Adding an environment variable or mounting empty gate directories cannot introduce missing
application hooks. Actual enablement requires independently approved replacement source/
images, separately owned gate mounts, preserved effective startup/user/token bindings and
qualified activation/revert. The current source push/read-only observation is not permission
to replace images or change NL working services. No capture is authorized from this receipt.

## Observer contract

`scripts/control_ha_owner_source_binding.py` is a stdlib-only bounded Docker Unix-socket
GET observer. It reuses the existing OWNER admission inspector for private configuration
redaction and exact Compose/name validation. It permits only the two named OWNER containers,
their observed immutable IDs, the ten fixed `/app/` source paths and ExecIDs found in those
containers. Wrong installed images or changed pre/post bindings refuse. It never enumerates
other containers, accepts arbitrary paths, reads `.env`/DB/profile/key files, uses Docker
exec, imports installed code, acquires writer locks or sends signals to working services.

There are44 GETs for the accepted zero-ExecID case:four inspections and two observations
of ten source paths per container. Retained ExecIDs, when present, are bounded to64 per
container and their GET-only inspection must match the originating container. Running and
completed executions are distinguished, but neither closes admission for future commands.

Each source response is an uncompressed bounded tar read in memory, **never extracted**.
The Docker path-stat header and exactly one regular member must agree on basename, size
and mode; links, directories, extra members, special files, malformed/duplicate metadata,
unsafe paths and oversized responses refuse. Only the two known optional admission files
may produce a404 absence record. Other failures never become an empty/missing-success result.
Source contents are SHA256-pinned and parsed as syntax, never executed or exported.

Responses are bounded to1MiB JSON or320KiB archive, source files to256KiB, each socket to3s
and the whole CLI to30s via a kernel alarm; core dumps are disabled. Private environment,
argv, mount-source paths, source contents and execution arguments remain in memory only.
Output contains hashes, fixed public source names, whitelisted token mentions and metadata.
Successful receipts always state `capture_permitted=false`, `all_writers_qualified=false`,
`services_changed=false`, `commands_executed_in_containers=false` and explicit unresolved
loaded-code/manual/namespace/external-completion/independent-approval gates.

From the HA worktree, retaining output outside Git:

```sh
umask 077
python -m scripts.control_ha_owner_source_binding > /private/new-owner-source-observation.json
```

Exit0 means observation completed, **not acceptance or approval**. The candidate source set
is read from the worktree's ten fixed files; its digest does not create independent approval.
If deployed images change legitimately, review that transition and update the pinned cohort
deliberately rather than accepting a new image silently or rerunning until a mismatch passes.

## Validation and evidence

108 focused tests PASS /0 skips:66 source/dispatcher tests and42 existing OWNER admission
preflight tests. Coverage includes bounded GET allowlists, image/container/exec ownership,
changed source/config/working-directory/exec sets, rootfs/nested mount resolution, private
value redaction, missing optional versus required/error responses, archive attacks, source
syntax without execution, malformed/oversized commands and refusal to infer coverage from
matching bytes or absent manual commands. No platform/release/native deployment gate is claimed.

Private evidence0700/0600, outside Git:
`~/.local/share/family-connect/control-ha/20261124-owner-source-vhU4wF/`.
The initial CLI refused with its generic redacted error; its reason was not retained and
must not be invented. A separate diagnostic observation completed without a retained receipt
and is not the accepted result. The final fresh observation is retained separately, not
substituted for either attempt. No retries changed services or widened collection scope.

- Accepted `final-observation.json` SHA256:
  `7c276ec40df95e646928d0d5babe1cd258952fc8a513c768c6f3e81933b02874`.
- Observer source SHA256:
  `c1d76679c4c2e2b3a3a89f7bb974fecf4fb4066f453fa1caffeb73318d7a19ee`.
- Candidate source-record-set SHA256:
  `98fe0bef48100fc4749e27fd8e24fad569ee35199d4f454c5ea713cc98ba153f`.
- Observed source-record-set SHA256:
  `ca76fef6f145858076b18645fea67d3a15766ca931727a7ef7ba0794de67c7ab`.

## Rollback and next gate

Nothing is installed or activated, so there is no production rollback. Stop this observer
on refusal; do not restart old failed units, remove uncertainty records, alter ownership or
restore databases as an observational rollback. The same installed image pair remains the
observed reference, not the prepared source or an accepted rollout.

The OWNER source/config/mount observation is now complete for this explicit scope; do not
repeat it as a new gate. Next qualify exact OWNER activation/revert against these retained
bindings with approved replacement images and separate gates, without default Compose
startup or broad service restarts. Finish the remaining actual fleet/manual writer bindings,
settle external work independently and measure real flush/capture latency. Then qualify the
coherent all-store/fleet point, independent current approval/off-laptop key/access custody
and final combined current/post-ACK/stale recovery. No HA-03/cutover or new numbered stage.
