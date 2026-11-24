# CONTROL-HA — OWNER image custody, 24 November 2026

Task: CONTROL-HA-20261123 / HA-02, existing complete-recovery acceptance block.
Preparation only at this checkpoint. Installed, public and invitation versions unchanged;
no gateway operation, production deployment, service restart, schema or policy change.

## Prepared scope

The previous native recovery used three already available Docker images. Losing that daemon
must not also lose the console, publisher and PostgreSQL runtime dependencies. The exact
linux/amd64 image roots pinned in `scripts/control_ha_owner_runtime.py` are now exported into
a private187,475,968-byte Docker/OCI archive. This is a read-only image export, not a dump of
container environment, running processes or original volumes. Treat all image contents as
private, including any configuration embedded in their history; no archive goes to Git/CI.

`scripts/control_ha_owner_images.py` verifies the closed graph: three selected roles,
59 content-addressed blobs,48 unique layers/65 references,519,261,696 expanded bytes.
It checks blob/descriptor hashes and sizes, exact platform/root coverage, layer diff IDs,
Docker/OCI compatibility and bounded expansion. Missing non-selected PostgreSQL platforms
are allowed; the selected amd64 manifest/config/layers must all exist. Unknown members,
links, traversal, duplicate JSON, unreferenced blobs and incorrect pins fail closed.

AES-256-GCM packaging retains the original archive, the pinned Ubuntu
`umoci_0.4.7+ds-4_amd64.deb` and the two standalone recovery modules. The external checkpoint
binds purpose/platform/image roots, archive/tool/source hashes and ciphertext; the fresh
32-byte key and checkpoint are retained separately. The tool package SHA-256 is
`fa84af91f6ca20630bf1aa83392423a59b54ff5e95bcab9ba3aff13d5ef666b2`;
its extracted executable is pinned independently. The package is extracted locally, not
installed; no maintainer script is run. Its retained copyright/license files remain with
the private package. This is a qualification tool, not a new product dependency.

`scripts/control_ha_owner_image_bootstrap.py` is designed to run from the authenticated
restored files. An unprivileged, network-unshared bubblewrap namespace extracts each image
using umoci. Only derived OCI media-type metadata is normalized; original config/layer bytes
and the encrypted original export remain unchanged. Native probes mount only the restored
rootfs, their private temporary work area and fresh proc/dev. They cannot see the working
repository, Docker socket, original containers/volumes, home or runtime secrets. Default
image entrypoints, the publisher worker, migrations and service commands are never started.

The console/publisher probes check native Django imports, SQLite, psycopg/libpq and Ed25519
sign/verify while rejecting network/process dispatch. The PostgreSQL probe uses one synthetic
row, Unix sockets only, restart readback and a fresh custom-dump restore. This establishes
runtime dependency availability, NOT another restore of the actual39-table OWNER database.

Preparation checks:69 tests PASS,0 skips, covering custody tampering/framing/path rules,
strict role/platform pins, extraction boundaries and the existing OWNER runtime contract.
Actual encrypted handoff/cold execution is pending; no cold result is inferred from unit tests.

## Prerequisites and fixed remainder

Recovery host requirements remain explicit: Linux amd64, working unprivileged user/PID/network
namespaces, bubblewrap, dpkg-deb, compatible host glibc for umoci, Python and cryptography,
private free disk space, and independently retained key/checkpoint. Native image probes do
not use host Python libraries. The host toolchain itself is not bootstrapped from bare metal.
Local separate key custody is not proof of an off-machine/off-site backup or owner approval.

The fixed four HA-02 blocks are unchanged: replication PASS in isolation; current independent
trust, coherent all-writer/in-flight dispatcher capture and complete final machine-loss
recovery remain partial. Finish the other source/image dependencies and combine the final
approved coherent checkpoint with post-ACK readback/stale-copy refusal. This slice does not
close those gates, authorize live rollback, or start HA-03..05. See the
[previous actual integration and fixed remainder](2026-11-24-control-ha-owner-joint.md#fixed-remainder-of-stage-2).

## Rollback and retention

Source rollback is an ordinary revert of this logical change. On a failed qualification,
stop only the owned contained process and retain its private logs; never stop/remove original
OWNER containers, prune images or restore a lab dump over production. Keep private encrypted
capsules and separate keys/checkpoints; any cleanup applies only to owned temporary paths.
No service/config/version rollback is needed because none is changed. A source push is not
a deployment or HA-02 acceptance result.
