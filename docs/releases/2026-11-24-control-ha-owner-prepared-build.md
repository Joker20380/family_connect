# 24 November 2026 UTC — normal OWNER build context repaired

Selected task: CONTROL-HA-20261123 / HA-02. This closes a concrete build-path defect,
not another writer census or a new acceptance gate. No deployment, service/unit/timer
change, product version/catalog/signing/release change or RU/NL access. Main remains
navigation only. Replication PASS; current trust, coherent capture and independent
custody/final recovery remain partial.

## Defect and source correction

`control_plane/Dockerfile` copies `control/capture_gate.py` and the management entrypoint
imports it. However, the explicit allowlist in `control_plane/prepare_local.py` included
only `control/friends/*.py` from that directory. The normal documented preparation path
therefore omitted a mandatory COPY source. An extracted prepared context also failed
with `ModuleNotFoundError` before the optional gate could refuse or allow a command.
Previously built images do not prove that this preparation path works.

Add exactly the shared module to the source allowlist. No recursive copy of `control`,
new dependency, changed gate semantics, startup command or Compose settings. Four new
regression cases cover the defect: every Docker COPY source exists, and the actual
prepared admission module imports and handles closed, missing and unconfigured gates.
The tests run from outside both source trees and do not inherit the checkout PYTHONPATH.
They verify manifest hashes, exclude the generated private .env and leave no pending
marker after refusal/help. No skip hides a missing module or dependency.

## Actual prepared image, not installation

A fresh private shadow contains only the selected repository sources and Dockerfile.
Normal `prepare()` creates its disposable .env outside the build context; it does not
touch the working OWNER .env/context. The resulting272-entry manifest includes the
Dockerfile. Every selected file hash is checked before `docker build --network=none
--pull=false`; the existing digest-pinned base and dependency layer satisfy that build.
The test image has a new isolated local tag; installed tags/containers are not replaced.

| Artifact | SHA256 |
| --- | --- |
| Prepared source manifest | `f9e0ded1400b1b401c617c51be11e7ec144918cbe81cf748274877c277a3cc50` |
| Locally built image ID | `4392d4b7ba7b73886e03b0449a6074aadd8c6638da029f0cda75a05586b82f3f` |
| Native image probe | `ed3949abe16b77272e9d27bcbd7458ac58640bea653524188d867d93be5d7e84` |

`tests/fixtures/owner_upgrade/prepared_image.py` runs via stdin in two disposable containers,
at UID/GID10001 and1000. Each has no network, read-only root, dropped capabilities,
no-new-privileges, bounded memory/PIDs and a fresh /tmp tmpfs. No host/product/DB/socket
mounts, production secrets, service startup or Compose dispatch. Only help invocations
are made, so a broken admission check cannot migrate/seed/publish actual state.

Both probes pass on image Python3.13.17:

- Closed gate: `migrate`, `collectstatic`, `seed_demo`, `publish_system_messages` and
  `shell`, each with `--help`, return75 and only `CAPTURE_BUSY`.
- Missing gate: generic help returns1 and only `CAPTURE_UNAVAILABLE`.
- Unconfigured and open/admitted gates: generic help succeeds; pending remains empty.
- All18 installed package versions match `control_plane/requirements.lock`.
- Ten selected image source hashes match the prepared manifest, including the shared
  gate, management entrypoint, middleware, settings, backend, support and publisher.

Both test containers are removed. GET-only selected installed OWNER bindings before/after
the build/probes are equal: the same running instance/image/config/mount/start/restart/PID
bindings. Installed images remain5ce82415/50de6f25, with no configured gates. This is a
point comparison, not proof that no product write occurred or a coherent quiet interval.
No working container is executed into, stopped, recreated or mounted by the test.

## Validation and retained evidence

`/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q
tests/test_control_plane_prepare.py tests/test_capture_gate.py`:
**40 PASS,0 skips,5.09s**, including four new regressions. The initial management-CLI
reproduction produced four failures on the missing module. After the one-line fix,
the control-only venv produced37 PASS/3 failures because Django is absent there; a
panel-lock environment with all18 versions verified produced40 PASS in5.33s.
The final root-suite regression tests the packaged admission module directly, so it
does not add an undeclared Django requirement to the existing control CI environment.
No skip/stub or application workaround was added. Actual management CLI behavior is
covered separately by both native image probes with all18 panel lock versions verified;
those runs are not counted again in the final40 tests.

Private source shadow, generated disposable .env, manifest, build log/receipt, exact
native fixture/stdout/stderr and redacted before/after binding receipts remain under
`~/.local/share/family-connect/control-ha/20261124-prepared-owner-*` (private parent).
The local pointer is `/tmp/fc-ha-prepared-owner-current`. No capsule, generated .env,
raw runtime data, image archive or build output is committed. Documentation/link and
whitespace checks pass: five documents,1096 link targets, zero errors; external URLs
are enumerated, not fetched. No unrelated full suite is claimed.

## Activation limit and rollback

The image demonstrates packaging/import/admission behavior only. It is not an approved
installed replacement and does not inherit the earlier b62e6693/2162635c exact-command
activation/revert acceptance. Those prior proofs remain retained for their own images.
Ten source hashes are not a complete deployed runtime/config/namespace attestation.
Tmpfs test gates are disposable test state, not durable production gates. There is no
product PG recovery or transport completion assertion in these probes.

No live rollback is needed. Preserve the installed image/config/volumes and recovery
access; do not run the default Compose startup or database migrations to adopt this
image. A future approved activation must bind this exact candidate's full intended
delta to effective startup, users, mounts, dependencies and distinct durable gate
participants, with current prestate and image-specific rollback. Abort/release capture
before reverting an admitted participant; retain post-upgrade data and unknown markers,
never restore stale DBs or delete a marker to make rollback look clean.

Continue the existing [joint activation matrix](2026-11-24-control-ha-collector-admission.md#joint-activation-proposal--not-executable-authorization):
actual OWNER candidate/runtime/config approval, remaining RU/NL/manual/transport bindings
and exact scope, then coherent capture and independent checkpoint/custody/final recovery.
Working-NL changes are not currently authorized. The earlier [collector packages](2026-11-24-control-ha-collector-binding.md)
remain prepared but uninstalled. Do not repeat this build or the completed collector/NL2
diagnosis slices as additional gates; do not claim HA-02 complete from a source push.
