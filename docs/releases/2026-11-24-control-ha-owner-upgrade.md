# 24 November 2026 — OWNER image activation/revert qualification

Selected task: **CONTROL-HA-20261123 / HA-02**, following the
[installed-source decision](2026-11-24-control-ha-owner-source-binding.md). This closes the
source-image/isolated OWNER transition slice, not deployment, independent approval or all-writer
capture. Replication remains PASS; the same three HA-02 acceptance blocks remain partial.

## Built versus installed

| Role | Still installed / rollback image | Locally built candidate |
| --- | --- | --- |
| console | `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a` | `sha256:b62e66930cd672ed5350c1e5b7c19f48f0f77ffcdbe3ce9b2b2b9a85a608e8e0` |
| system_publisher | `sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab` | `sha256:2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79` |

No application version, public installer/catalog/link, release tag or signing sequence changes.
These are local immutable image IDs, not pushed registry artifacts or independently approved
release images. Original images remain installed; neither working OWNER service has a gate.
No RU/NL connection, working-container exec/restart, policy or production state change occurred.

`scripts/control_ha_owner_upgrade.py` creates a deterministic closed tar containing a two-line
Dockerfile and the same ten fixed Python sources as the preceding observation. The Dockerfile
uses the exact installed role image as its base and one root-owned source COPY. There is no
RUN, pip/apt, dependency rebuild, complete worktree/context, migration file, private state or
credential in the input. Build uses the local Docker socket, no pull and network disabled.
The candidate must retain the exact image Config, OS/architecture/variant and complete existing
RootFS layer prefix, adding exactly one layer. It cannot change default identity, environment,
entrypoint/command, healthcheck, dependency layers or declared volumes as a hidden upgrade.
This does not provide reproducible-build or independent signature/approval attestation.

The workload validator additionally pins the installed role/image, configured user, working
directory, empty entrypoint, read-only rootfs and absence of an existing gate. A closed command
shape accepts the observed console migrate/collectstatic/Gunicorn chain and publisher loop,
including its fixed `FC_SYSTEM_PUBLISHER_ORIGIN` environment reference. Extra seeding, shell
commands, arbitrary substitutions, redirected outputs and changed dispatch flags refuse.
Full argv/environment/mount details remain private; only hashes enter receipts.

## Actual native result

**Final PASS 2026-11-24 18:02:31.561639–18:04:00.368232 UTC.**
`tests/fixtures/owner_upgrade/native.py` runs both original images, both candidates and both
original images again, using the actual validated installed command arrays byte-for-byte,
configured users (`console` / `1000:1000`) and `/app/control_plane` working directory.

- Disposable pinned PostgreSQL image
  `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`
  has network mode `none`; test applications share only that isolated network namespace.
  No published ports, host-network path, Docker socket or production bind mounts are exposed.
- Fresh labeled volumes hold PostgreSQL, synthetic SQLite, separate UID10001/1000 gates and
  a fake publisher token owned by UID1000/mode0600. Lab credentials and HTTPS origin are fake;
  support IPC is disabled, publication queue empty. There are no external requests to settle.
- Synthetic fixture initialization is an explicit lab setup command **before** service start,
  not an added `seed_demo` step in the real command. Both actual startup chains become ready.
- Each candidate refuses management dispatch with exit75/`CAPTURE_BUSY` while its own gate is
  drained. Invalid gate configuration makes the console's exact startup command fail with exit1.
- Candidate-admitted work commits a Django session to PostgreSQL and a label to native guarded
  synthetic SQLite. After reverting both images and disabling opt-in admission, original code
  reads both acknowledged changes. No database backup, rewind, reverse migration or replacement
  is used. The Django migration set is unchanged and no migration is pending after revert.
- A caught-by-the-harness management failure leaves a durable unsettled-operation marker.
  Drain refuses. Its exact name/content hash survives image revert; rollback does not silently
  resolve unknown outcomes. Gate owners and0700/0600 permissions remain intact.
- Pre/post live OWNER bindings match. All owned fixture containers/volumes are removed, with
  label-scoped cleanup verification. Only private logs, source pins and local images remain.

**Limitations:** this tests fresh fixture state, not current production data, load or mounts.
The unmodified publisher shell loop needs the fixture's bounded Docker stop/force fallback
(8s); an empty queue with no external dispatch makes this safe only in the stand. This is
**not** approval of forced termination with real in-flight publication or evidence that remote
work has settled. Healthcheck configuration is inherited unchanged by the built images, but
the stand disables automatic Docker healthchecks and explicitly polls readiness. Working
mount/environment/token-source preservation and guardian namespace/inode binding still need
an independently reviewed live transition plan. No live drain/capture permit is issued.

## Rollout and rollback boundary

There is deliberately no production `up`, replacement, gate-directory initializer or restore
command in the builder. Do not use repository-default Compose: its startup contains seeding
and is not the observed command. Before any working-container transition:

1. Independently approve both candidate/source pins and retain the exact old image pins and
   private effective configs. Verify they are still present; building is not custody approval.
2. Bind each fresh gate to its existing service UID and trusted guardian/inodes. Never share
   one0700 gate between UID10001 and UID1000, loosen permissions, change service identities or
   take ownership of the existing publisher token as an enablement shortcut.
3. Review a private effective-config diff. Allowed intended deltas are the approved role image,
   one opt-in gate variable and its separately owned writable gate mount. Preserve every other
   argv/user/environment/token/mount/network/port/security/resource/health/restart binding.
   This stand does not construct or approve that production delta.
4. Close new work and independently settle existing publication/support/manual work before
   stopping any working process. Do not infer settlement from HTTP return, an empty sample,
   a Docker client timeout or this stand's8s stop. Paid-watch/deny enforcement remains running.
5. Check schema/data compatibility and retained current-state recovery before startup: the
   preserved actual console command still invokes `migrate`. Here the source-only layer changes
   no migration files; a later image with schema changes needs its own qualified rollback.
6. If activation/readiness fails, restore the exact old role image and effective config,
   removing only the newly enabled gate variable/mount. **Keep current PostgreSQL/SQLite data**;
   never restore a pre-upgrade DB snapshot over acknowledged payments, grants or revocations.
   Retain gates/pending markers and private evidence even when the app stops using the gate.
   Reverting to an ungated image also invalidates any capture-readiness claim.

Actual working-container change remains a separate approved boundary; it was not performed.
Next selected implementation is remaining fleet/manual coverage and external settlement/real
latency, then coherent all-store capture, independent current approval/key/access custody and
final combined post-ACK/stale-copy recovery. Do not repeat this stand or create a new HA stage.

## Validation and retained evidence

Final focused run **161 PASS,0 skips**:53 new overlay/workload/fixture-safety checks,
66 installed-source observer checks and42 admission-preflight checks. Includes exact immutable
base/layer/runtime preservation; deterministic allowlisted source tar; unsafe source/command/
origin refusal; no container operation in the builder; distinct PG/application volumes and
foreign-volume ownership refusal; fixture-only network/mounts/credentials. Existing application
admission tests are not rerun as a substitute for this native image integration.

Two earlier fixture attempts did not pass: the initial application volume name collided with
the disposable PG volume (ownership refusal prevented cleanup of the wrong scope; the outer
PG owner cleaned its own volume); the second attempted readiness before synthetic fixture
initialization. Separate volume names/ownership assertions and setup ordering were corrected.
Neither attempt touched production; their private logs are retained, not presented as PASS.
The third execution passed17:58:12–17:59:38UTC. After explicitly disabling core dumps before
reading private live configuration, the final fixture rerun also passes18:02:31–18:04:00UTC,
with unchanged installed bindings and complete cleanup. The final receipt is authoritative.

Private evidence directory:
`~/.local/share/family-connect/control-ha/20261124-owner-upgrade-e3uI2I/` (0700/0600), with
image manifests, tests XML, source pins, initial diagnostics and accepted `native-final.json`.
Disposable state is removed; remaining fixture logs live in private `/tmp/fc-owner-upgrade-*`
directories. Do not commit these logs, source build archives or any product/custody state.

| Artifact | SHA256 |
| --- | --- |
| Builder | `07b0f7e4ae1f8fd09746b876fe09b57c5f8cf9ca4ebe9941f6ad9e92c8efc269` |
| Final native fixture | `2158c0d7723c1c161815805feaf82712ec361a8e8e87ad4a0f9fef4d79d71d0e` |
| Accepted native receipt | `2dc9d3eba4c752d08eb42ce1a7c750540b07a7550123423897dd8caf44a71625` |
| Console context | `a43006ffd3eaa0353e7d581ce3b4539d65d581c70fc4bf873e6852d850c3af94` |
| Publisher context | `3c1398a064ee4548875111dafb6c127f744a4132af57cca909ccc14bcfa2070e` |

No general release/rollout PASS, independent approval, live latency claim or HA-02 completion.
