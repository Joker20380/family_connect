# 24 November 2026 UTC — exact private OWNER activation configuration proposal

Selected task: CONTROL-HA-20261123 / HA-02. This implements the previously missing
private effective-config diff from the [OWNER transition boundary](2026-11-24-control-ha-owner-upgrade.md#rollout-and-rollback-boundary).
It is not another inventory gate, live activation, permission request or all-writer proof.
No RU/NL access, working-container exec/restart, service/unit/timer/policy change, database
access, image build, version/catalog/tag/signing change or gate-directory creation.

## Actual result

Read-only observation **23:28:36.971965–23:28:37.181744UTC**: the two fixed OWNER containers
retain equal pre/post instance/start/restart/PID, full Config/HostConfig/Mounts/NetworkSettings
and existing workload bindings. Numeric process observations match console UID/GID10001 and
publisher1000; this does not attest user-namespace mappings or gate inodes. Four exact local
original/overlay images are inspected here; the prepared image is checked separately below.
No image is built or run, and no other project/container is enumerated.

`scripts/control_ha_owner_activation_plan.py` materializes the plan offline from those private
inputs. A final read-only verification at **23:30:34.372438UTC** reproduces the same receipt
without modifying the retained plan or contacting Docker. This later verification is of the
saved observation, not a claim that the running configuration was resampled at that time.

| Role | Observed / rollback image | Proposed previously qualified overlay | Planned gate owner |
| --- | --- | --- | --- |
| console | `5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a` | `b62e66930cd672ed5350c1e5b7c19f48f0f77ffcdbe3ce9b2b2b9a85a608e8e0` |10001:10001|
| system_publisher | `50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab` | `2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79` |1000:1000|

The separate normally rebuilt image4392d4b7 is tested as a counterexample and refused with
`IMAGE_LAYERS_CHANGED`: it does not retain the original image's layer prefix. Its successful
[prepared-context build](2026-11-24-control-ha-owner-prepared-build.md) is still valid; it must
not silently replace a minimal overlay or inherit that overlay's activation/revert evidence.
The two overlay IDs above are the retained earlier candidates, not newly built images.

## Closed allowed delta and rollback prestate

The five representational fields that may differ are `Image`, `Config.Image`, `Config.Env`,
`HostConfig.Binds`, and `Mounts`. Semantically these permit only the candidate image, one
`FC_CONTROL_CAPTURE_GATE=/run/family-connect-capture` assignment and one separate writable
private bind. Everything else must match the pinned observation exactly, including token/
environment values, argv, users, workdir, ports, network records, existing volumes, labels,
capabilities/security, healthcheck, restart/resource/log settings and unknown future fields.
The original private configuration is retained with its digest as the rollback prestate;
there are no database files or database restore instructions in the plan.

Proposed host locations, **not created or approved**:

- Console: `/var/lib/family-connect/capture/owner-console`, owner10001:10001.
- Publisher: `/var/lib/family-connect/capture/owner-publisher`, owner1000:1000.
- Each uses its own container mount namespace and planned0700 directory/0600 lock files;
  no shared cross-UID gate, permission widening or product/token ownership changes.

Destination/source overlap, inherited VolumesFrom and inconsistent named-volume bindings
refuse. The actual console's named volume is preserved as a named volume and must match its
resolved observed name/destination. It is never treated as an absolute host-directory path.
Source-path checks are lexical: they do not prove filesystem/mount/inode identity or absence
of symlink aliases in a future gate tree. No path is created, chowned or opened as a gate.

The artifact is explicitly **not an executable Compose or Docker create payload**. It retains
the full NetworkSettings snapshot, including old endpoint/sandbox identifiers, as baseline
evidence; these are not instructions to reuse those runtime identifiers when recreating a
container. An approved executor/readback still needs the actual semantic network/gate bindings.
Image checks bind immutable IDs and config/layer-prefix compatibility; they do not independently
inspect or approve the content of an arbitrary additional layer. Candidate source acceptance
and live setup remain separate. `executable`, `independent_approval`, `runtime_qualified`,
`capture_permitted`, `deployed`, gate-inode and existing-work-settlement assertions stay false.

## Private artifact and repeatable verification

Raw configuration may contain credentials. Input/proposal files are0600 under an owner-only
0700 directory, outside Git, with core dumps disabled. Input is size-bounded and SHA256 pinned;
symlinks, hardlinks, FIFO, wrong ownership/modes, duplicate keys and changed input refuse.
Output is exclusive, fsynced and never overwritten. Failure emits only
`OWNER_ACTIVATION_PLAN_REFUSED`; success prints hashes and non-sensitive role metadata, not
private paths, environment, startup command, token, hostname or network values.

```sh
python -m scripts.control_ha_owner_activation_plan \
  --input /private/input.json --input-sha256 "$INPUT_FILE_SHA256" \
  --output /private/new-proposal.json
python -m scripts.control_ha_owner_activation_plan \
  --input /private/input.json --input-sha256 "$INPUT_FILE_SHA256" \
  --verify /private/new-proposal.json --proposal-sha256 "$PROPOSAL_FILE_SHA256"
```

Use an already trusted, separately reviewed input and fresh private output; these examples
are offline operations, not approval or deployment commands. The actual retained artifacts
are under `~/.local/share/family-connect/control-ha/20261124-owner-config-*`, located by the
private local pointer `/tmp/fc-ha-owner-config-current`. Raw inputs and proposals stay private.

| Receipt | SHA256 |
| --- | --- |
| Final input file bytes | `476a4e6e05ac94108b055e2d7ea83d0a9e1b2110fb7dd06fbbb1f01129fd2b5a` |
| Final proposal file bytes | `edab9507122f720ea03b74e11ab39ccbe94bfa02f1685ccc921bd67621b38fd9` |
| Canonical proposal object | `0b2536bc7466192078500846d7981dce6eff75e162b9a0448f1ea2bc59af05d8` |
| Final planner source | `21a9b5f6389bf1311fcd853c57d6588d5b2b1ba92060ab5030636ff10520b190` |

File-byte pins differ from canonical JSON-object digests intentionally; CLI arguments require
the file-byte hashes. The original failed observation/input and sanitized refusal are retained.

## Validation and remaining boundary

`/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q
tests/test_control_ha_owner_activation_plan.py tests/test_control_ha_owner_upgrade.py
tests/test_control_ha_owner_admission_preflight.py`: **159 PASS,0 skips,1.08s**.64 new cases
cover allowed-delta reconstruction, private-value redaction, unchanged inputs, forbidden edits
to every protected configuration category, image/UID/observation/rollback binding, mount overlap,
named volumes, private-file refusal and no-overwrite/read-only CLI verification. Existing95
tests cover the reused workload/overlay/admission validators; no old native stand is rerun.
Documentation checks pass: five files/1096 link targets/zero errors, plus clean whitespace.
External URLs are enumerated, not fetched. Private receipts and test logs stay outside Git.

The first56 new checks passed, but the actual observation exposed an unhandled named-volume
source and the proposal refused before output/dispatch. Named-volume resolution was added
without converting or weakening its binding:60 new tests/155 combined passed; four verification
CLI cases bring the final counts to64/159. This was a planner limitation, not a production fault.

No live rollback is needed. Before any later replacement, independently accept exact candidate/
configuration and revalidate the current prestate; bind durable gate directories, namespace/
inode ownership and guardians; close new work and settle existing publication/support/manual
operations. Do not use a forced stop, empty queue sample or this plan as settlement proof.
On an approved activation failure, abort/release capture and restore exact old role image/
configuration while keeping current PG/SQLite data and unknown pending markers. Do not reset
state or discard acknowledged writes. The source checkpoint changes no installed rollback path.

Continue these OWNER activation prerequisites and the existing RU/NL/manual/transport coverage,
then one approved coherent interval and independent checkpoint/custody/final recovery. Working-NL
changes remain outside current authorization. Replication PASS; the same three HA-02 gates remain
partial. Do not repeat the completed configuration proposal, build, collector packages or NL2
diagnosis as new acceptance stages. No completion percentage or rolling ETA is asserted.
