# 24 November 2026 UTC — OWNER cross-container gate binding

Selected task: CONTROL-HA-20261123 / HA-02. This is a **test-only integration checkpoint**,
not production activation, approval, a new stage or full capture. The existing
[four stage2 gates](../control-ha.md#когда-заканчивается-этап-2) remain unchanged:
replication PASS, the other three partial. No product/application/runtime version changes.

## Gap exercised

The previous [guardian stand](2026-11-24-control-ha-guardian-launch.md) used different UIDs
inside one container. The [private activation plan](2026-11-24-control-ha-owner-activation-plan.md)
specified distinct bind mounts but did not prove that separately mounted applications and
guardians lock the same kernel inodes. This stand exercises that integration without changing
the installed OWNER containers or creating the proposed production gate paths.

`tests/fixtures/owner_upgrade/cross_mount.py` creates only labelled disposable containers and
fresh private fixture directories. Two writers import the gate from the already built role
images, not from the guardian package or a substituted application checkout:

| Role | Exact image | UID:GID |
| --- | --- | --- |
| Console candidate | `sha256:b62e66930cd672ed5350c1e5b7c19f48f0f77ffcdbe3ce9b2b2b9a85a608e8e0` |10001:10001|
| Publisher candidate | `sha256:2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79` |1000:1000|
| Guardian coordinator | `sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962` |0:0, then separate10001/1000 children|

Each application mounts its own fresh gate at `/run/family-connect-capture`; guardians reach
the same backing directory through different paths. The backing filesystem is ext4, outside
the container writable layer and tmpfs. This proves persistence across container replacement,
**not power-loss/storage-controller durability** or persistence of uncreated production gates.
No migration, publisher command, user data, PostgreSQL, token or remote operation is run here.

The probe compares all four gate device/inode pairs, owner/group/modes, gate source SHA,
uid_map/gid_map hashes and user/time namespaces. Mount/PID namespaces must differ; namespace
remapping is not silently accepted. Actual Docker writers have supplementary group[primaryGID];
guardians have none. No additional group or DAC override is permitted.0700 directories and0600
locks stay unchanged. Docker readback checks exact image/user, private bind source/destination,
read/write flags, rprivate propagation, read-only root, network=none and resource/capability limits.

## Accepted native run

**23:50:26.584566–23:50:41.502811UTC:**

- A real active console gate operation prevents drain after guardian startup. The probe waits
  200ms with no HELD response before allowing that operation to finish; it does not kill it.
- Both separately mounted candidate writers report BUSY inside the joint interval. The measured
  assertion interval is3.745843ms, not a full-copy latency budget or production flush benchmark.
- Final ACK/release completes; both writers can enter afterward. Guardian children are reaped.
- A deliberately terminated disposable writer leaves one uncertain marker. A new container
  sees the same four inode identities and retained marker; another successful write does not
  erase it, and the guardian refuses the next drain. The marker remains private evidence.
- All owned labelled containers are removed and absence is checked. No installed container,
  timer, service, image tag, source directory, permission or policy is changed. No RU/NL access.

Installed OWNER pre/post binding digest is identical:
`d7dc99f12e6bed339423ab51009937f836124068dee6536a16ddbf07d97b2307`.
This compares actual container/config identities and observed UID/GID sets, not quiescence
or complete external-operation settlement. Working images remain5ce82415/50de6f25, ungated.

| Evidence | SHA256 |
| --- | --- |
| Final fixture | `8ba16a96c22af5b925b1787450192f41fdaef856081ddb2d71a82caa1eb3668f` |
| Sealed guardian source package | `12e83c6596c9416cd6fcfff8e01b584c48078641d7653d678b309ca4da410d21` |
| Candidate and guardian gate source | `da28d940e2e17e2dbb1fbbde8cc04c59d29cffc8762ada717135504e2ffa4906` |
| Native receipt | `39389b25b7bbbe583e998895f8d05cdb711f1957c2694a808b6098f43afcddea` |

Private receipt/observations/markers remain under
`~/.local/share/family-connect/control-ha/20261124-owner-cross-mount-*`;
`/tmp/fc-ha-owner-cross-mount-current` locates the accepted run. Parent0700, receipts0600;
source-only mount copies are readable inside that private parent. Nothing private enters Git.

The initial fixture attempts failed before acceptance: a host-only repository path calculation
ran inside the short container path; the supplementary-group expectation omitted Docker's
primary group; the root launcher correctly refused a package owned by the workstation UID.
The fixture now retains the exact observed group boundary and makes its approved-for-fixture
root-owned source copy, without relaxing production launcher checks. Failed owned containers
were removed; their private directories/markers are retained. These were fixture failures,
not working-service incidents or accepted intervals.

## Validation and rollback

`python -m pytest -q tests/test_owner_cross_mount.py tests/test_capture_launch.py
tests/test_capture_group.py tests/test_capture_gate.py`: **182 PASS,0 skips,14.67s**,46 new cases.
Tests cover exact identity equivalence/refusal, namespace/map/source/inode/permission drift,
aliased gates, unexpected mounts/images/users/network/capabilities, response bounds and fresh
non-symlink fixture paths. No old OWNER application activation/revert or database stand is rerun.
The native run above additionally executes the actual candidate gate code and guardian launch.
Documentation checks pass: four files/1079 link targets/zero errors and clean whitespace;
external URLs are enumerated, not fetched. Test and documentation receipts remain private.

No production rollback is needed. Cleanup targets only names with the fixture's random label;
never remove a marker or restore old product state to make drain pass. The prior private
configuration proposal and image rollback references remain unchanged and **uninstalled**.

## Remaining installed boundary

The current workstation account can inspect publisher namespaces but receives PermissionError
for the working console's `/proc/<pid>/ns/*`; noninteractive sudo is unavailable. No chmod,
sudo policy change, privileged host-PID helper or production exec was attempted. Consequently
this stand is not an attestation of the installed console's namespace/inode topology.

The existing candidate/configuration and actual runtime/gate/guardian setup still need independent
acceptance within an authorized activation scope. Settle existing publication/support/manual
work before replacement; an empty sample or forced stop is not proof. The actual collector,
RU/NL/manual/transport coverage and approved coherent capture remain required, followed by
independent current checkpoint/key/access custody and final combined recovery. Working-NL
deployment remains outside current permission. Do not repeat this accepted stand as a new gate,
infer production approval from its self-generated fixture binding, or advance to HA-03.
