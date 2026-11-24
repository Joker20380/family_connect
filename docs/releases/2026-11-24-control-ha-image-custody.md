# CONTROL-HA — OWNER image custody, 24 November 2026

Task: CONTROL-HA-20261123 / HA-02, existing complete-recovery acceptance block.
Actual cold image dependency qualification PASS; full HA-02 remains IN_PROGRESS.
Installed, public and invitation versions unchanged;
no gateway operation, production deployment, service restart, schema or policy change.

## Actual execution — 11:43:57UTC

Execution source `56559e414b655ed90e7c9c0e28cdd9d58c278515` was pushed and remote-SHA verified
before sealing the accepted third capsule. The first two immutable capsules remain failed
qualification evidence, not accepted recovery points. At11:46:10UTC final cleanup/preservation
checks also pass. Private detailed evidence stays outside Git under
`/tmp/fc-owner-images-yd27i_ww/attempt03/`; the encrypted capsule and separate key/checkpoint
are retained in the owner's private local custody directories, not only temporary storage.

- All four authenticated files restore byte-for-byte: the original187,475,968-byte image
  export, pinned extractor package and two standalone sources. All59 blobs,48 unique layers/
  65 layer references and519,261,696 expanded bytes pass exact digest/platform/graph checks.
- The restored standalone bootstrap unpacks all three images and runs native probes in
  unprivileged network-unshared namespaces, without Docker, registry, working repository,
  original volumes, host DNS, original credentials or production entrypoints. The extractor
  uses the explicitly declared host glibc/toolchain; native probes use restored image bytes.
- Console and publisher each pass Python3.13.17, Django5.2.18, psycopg3.3.6/libpq180006,
  SQLite and Ed25519 checks, with zero dispatch calls. No publisher worker is started.
- PostgreSQL17.11 initializes a private synthetic database, acknowledges one row, restarts,
  dumps and restores it into a fresh database with exact readback. It binds only a private
  Unix socket and is stopped afterward. This is NOT the previous actual39-table data restore.
- At11:45:32UTC a second fresh namespace uses the restored console image's own Python and
  cryptography, restored verifier sources, encrypted capsule and separately supplied key/pins
  to decrypt/verify all four files again. The host compares every byte exactly. No host Python
  library, Docker or working source is mounted for that readback. Its initial auxiliary
  mount setup correctly refused creating directories on the read-only root; using only
  the existing `/tmp` tmpfs resolves that without making the image root writable.
-71 focused tests PASS,0 skips. Original three OWNER containers retain their identities,
  start times, image roots, configuration and mounts. No owned bwrap/umoci/PG/probe process
  remains, and no lab postmaster PID file remains. No original container/image is removed.

Sanitized SHA-256 evidence:

| Artifact | SHA-256 |
| --- | --- |
| Original image export | `6995abbf8ac97241d212aae19e4ca12eebe6896cfc92ff36619215b8960c0705` |
| Accepted encrypted capsule | `a11bcae2b72e802026371a05bf467e490d13e6c004657cd956557814f4c89704` |
| Cold bootstrap receipt | `12eae8dd52a9229652d1d4c3a963117906c38acb1b31187f8834210e636ac588` |
| Native authenticated readback receipt | `c1eb810ec5191b279177a0ef8d8ae79ea8b27ccb8dda61b9e284192211a11d10` |
|71-test JUnit | `770802ff7295a08a4dfcd2c58a9ecf4bc298e8df33dac7e695b80b95d6a10817` |

This closes availability of the retained OWNER image bytes independently of the working
Docker daemon. It does not claim the recovery host can be built from bare metal, that custody
survives loss of this laptop, or that all fleet/current-state dependencies are covered.
The exact remaining full-state/trust/capture gates below remain unchanged.

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
At preparation, actual encrypted handoff/cold execution was pending; it subsequently passes
above. No cold result is inferred merely from unit tests.

The first actual encrypted handoff restores all four files exactly, but umoci refuses before
native execution: its rootless config needs `/etc/resolv.conf` mount metadata in the empty
namespace. Original OWNER containers are unchanged. The correction provides empty synthetic
resolver/hosts/hostname files, never host DNS configuration; native probes also get a fresh
synthetic passwd entry for the caller's nonroot UID, not the host account database.70 focused
tests pass. Preserve the failed capsule/receipt; the corrected cold run needs a new external
source/ciphertext checkpoint and was pending at that correction checkpoint.

The second actual attempt unpacks the console image successfully. Its native Django setup
refuses the too-short synthetic credentials, as required by the installed settings. Replace
only probe credentials with fresh random64-character values; do not weaken application
validation or use original secrets.71 focused tests pass, including an isolated credential
preflight. The second capsule remains failed evidence; original OWNER containers are unchanged.

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
