# CONTROL-HA — stopped OWNER replacement and data-preserving revert

Date:25 November2026 UTC. Selected task:CONTROL-HA-20261123 / HA-02, the existing four
acceptance gates. This is an executable **stopped-container** transition component,
not a drain, working deployment, capture permit or completion of stage2.

## Result

`scripts/control_ha_owner_replacement.py` stages one already stopped OWNER role from
the reviewed effective configuration and reverts it without restoring a database.
It has no start, stop, kill, exec, image-build, volume-delete or data-restore operation.
The old container and its exact image/configuration stay available under a retained name.
Unknown operations and acknowledged data are not reset to make rollback pass.

174 focused Python tests PASS,0 skips, including57 new replacement tests. Native Docker
qualification passes6 cases: one normal transition with application writes and five
**actual SIGKILL deaths of a separate coordinator process** after create, retain-name,
promote-name, candidate removal and original-name restoration. A new coordinator reads
the retained journal and completes the interrupted stage/revert without repeating the
already applied operation. These are coordinator deaths, not Docker-daemon crashes or
host power-loss qualification.

Working OWNER read-only observation at06:28:58UTC confirms both original containers are
running/healthy, unchanged effective configuration, PIDs, start identities and restart
counts. The proposed create bodies cover18/19 Config fields,65/66 HostConfig fields and
two networks for console/publisher. Both working containers refuse `STOPPED_REQUIRED`
before any journal manifest or Docker mutation. Only Docker GET requests were sent to
working resources. No server connection, working container/unit/image/gate change,
client version, installer, catalog or release change occurs in this checkpoint.

## Transition contract

The input remains the private, hash-pinned observation accepted by
`control_ha_owner_activation_plan.py`. Before initial staging, the implementation
validates that proposal again and compares the stopped original with the observed
effective configuration. It refuses running, paused, restarting or dead containers,
nonzero PID, outstanding Docker exec IDs, source/configuration drift, unknown network
fields, inherited/anonymous mounts and unsupported namespace/host features.

The only requested application changes remain the approved source-only image, one gate
environment assignment and its private writable bind. All other Config and HostConfig
fields are submitted intact, including argv, identities, environment, health checks,
restart policy, resources, security, port bindings, named volumes and existing binds.
No default Compose file, seeding command or environment reconstruction is used.

Network requests retain the exact network IDs, aliases, explicit IPAM configuration,
driver options and gateway priority. Generated endpoint IDs, DNS-name lists, dynamic
IP/MAC addresses and route observations are not request policy and are not copied.
**Dynamic addresses need not remain identical.** The observed working configurations
use dynamic addressing. Do not use this component where a consumer requires an unchanged
generated address without separately qualifying that dependency. Readback verifies
network identity and requested policy, not continued production network connectivity.

The sole observed HostConfig normalization is Docker29.1.3's unset `OomKillDisable:null`
becoming `false` on recreation. Only this direction is accepted; `true`, other fields
and reverse drift remain refused. Docker API is explicitly1.52. Different engines or
new inspect fields need qualification rather than a generic ignore-differences switch.

The protocol:

1. Retain a private0700 directory with immutable0600 manifest, configuration and pins.
   Subsequent invocations require the original manifest SHA and an exclusive journal lock.
2. Recheck stopped original, existing bind sources, exact local bridge networks and both
   images. Create the candidate **stopped**, under a transaction-specific staging name.
3. Read back its complete effective configuration, mounts and network policy. Pin its ID.
4. Rename the stopped original to its retained name, then candidate to the original name.
   Each mutation has an fsynced intent before dispatch and a readback-confirmed receipt.
5. Revert requires both containers stopped and unchanged. Remove only the pinned candidate
   with `force=false&v=false`; restore the original name and verify its original ID/config.
   Neither direction starts a service or deletes volumes, gates, markers or journal files.

A timeout is not success. A known applied result can be recovered by readback; if the
result is still unknown, the operation refuses and retains its intent. It does not blindly
repeat create/rename/delete. An externally removed candidate, changed configuration or
unexpected running process also stops progress. A failed transition may leave the original
under its retained name and both services stopped; this is **recovery required**, not a
successful rollback or permission to force/remove unrelated resources.

## Native qualification and failures

Final native transition interval06:31:39.864436–06:31:44.169832UTC uses the existing pinned
publisher baseline/candidate, two fresh internal Docker bridge networks, a private named
SQLite volume, synthetic read-only token bind and a separate host gate. The workload
uses UID1000, supplementary group100, read-only root, dropped capabilities, no-new-privileges,
resource limits, tmpfs, an explicit localhost port, `unless-stopped` and an actual health
check. Its fixture-only SIGTERM handler finishes with exit0; no force-stop is needed.

The original commits row1, the candidate commits row2 and deliberately retains one unknown
gate marker. After revert, the **same original container ID** commits row3 from the same
volume. Row2 and the pending marker survive. Config, mounts, named-volume identity, network
policy and rollback identity are verified. This is native SQLite persistence, not a new
production PG, nonempty publication or support-settlement test; their prior evidence is
not rerun or silently generalized.

Earlier owned attempts refused on two real engine differences: unset OOM configuration
normalization, then an empty NetworkID on a merely created endpoint. The first is now
narrowly handled as described above; the second is fixed by explicitly supplying the
retained network ID instead of accepting a missing binding. Those attempts did not pass.
Their private records are retained. A preceding in-process interruption stand also passed,
but the final six-case receipt uses real killed child processes. All owned test containers,
networks and volumes are removed and the label-filtered resource counts are0/0/0.

Validation command:

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_control_ha_owner_replacement.py \
  tests/test_control_ha_owner_activation_plan.py \
  tests/test_control_ha_owner_upgrade.py
```

The native fixture is `python -m tests.fixtures.owner_upgrade.replacement NEW_PRIVATE_TMP_PATH`.
It requires the exact already available images, Docker and UID1000; no production mounts
or destinations are accepted by its setup. Control/identity test interpreter is Python3.14.4.

## Retained evidence and image pins

Private root: `/home/joker/.local/share/family-connect/control-ha/20261125-owner-replacement-luu7c3fl`.
Raw current configuration, journals, source copies, test XML and native/preliminary receipts
remain outside Git. The successful native capsule is `native/`; its data volume was disposable.

| Item | SHA-256 |
| --- | --- |
| Replacement source | `83e8e3bd2757a3ae9dd1606efec6b9676dbb89df20c418418861cf53d1ce49a4` |
| Native fixture source | `721d3a2844eb3b4bf4e50b0309833e1aba9c47cb2aae309039aecef7edc2a3c0` |
| Replacement tests | `782627d88acb1ad4d415d7d8b884e58200a4e8fc24106a486fa01ea32c607b38` |
| Focused test XML | `4134bb64b5a5285399a9aeb2585964b49467cc2b2b6c07dd82017a2ca0bfc540` |
| Native receipt | `1be4d444d767af348057d9c97bd789fe9124dd1ac3c1c5a877420b8920b88d8d` |
| Working read-only receipt | `83b68a1b7346d33afbe96cbfe37fef515e0cad8362dff55bc046b7c35ac20a83` |

Original console `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`
and publisher `sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab`
remain installed. Candidate console `sha256:b62e66930cd672ed5350c1e5b7c19f48f0f77ffcdbe3ce9b2b2b9a85a608e8e0`
and publisher `sha256:2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79`
are unchanged source-only overlays, not installed by this work.

## Operational use and remaining boundary

This command is **not** a safe way to obtain a stopped prestate. The controller must first
close new work, independently settle publication/support/manual operations and manually
stop the old writers under the qualified bounded drain/abort protocol. An exited process,
empty queue, HTTP return, database sample or this journal cannot prove that settlement.
This component does not create/attest gate directories, obtain independent approval, exclude
other operators or fence Compose/systemd/collector writers. Those remain prerequisites.

Within that exclusive maintenance window, one private journal per role is used:

```sh
python -m scripts.control_ha_owner_replacement stage \
  --input PRIVATE_INPUT --input-sha256 REVIEWED_INPUT_SHA \
  --role console --journal EXISTING_EMPTY_PRIVATE_DIRECTORY
python -m scripts.control_ha_owner_replacement status \
  --journal RETAINED_DIRECTORY --journal-sha256 RECORDED_MANIFEST_SHA
python -m scripts.control_ha_owner_replacement revert \
  --journal RETAINED_DIRECTORY --journal-sha256 RECORDED_MANIFEST_SHA
```

Retain the emitted manifest SHA separately. If interrupted before it is returned, inspect
the manifest against the reviewed input before pinning it; do not reconstruct a replacement
journal or infer success from absent receipts. Staging/reverting two roles is not an atomic
multi-container transaction. The old retained container preserves its Compose labels and
restart policy: **do not run Compose lifecycle commands or start the retained original while
the candidate is active**. Old-container manual-stop state and daemon-restart behavior must
be covered by the surrounding operational protocol; this test is not a daemon-restart proof.

Next selected engineering work is the controlled ingress/dispatcher drain with independent
old-work settlement, gate/runtime attestation and guarded candidate startup/abort integration,
then the remaining RU/NL/manual/transport participants. Do not repeat this replacement
implementation or its isolated fault cases as new stage2 gates. Coherent capture, independent
checkpoint/pin/floor/key custody and final recovery remain open. Replication PASS; the same
three acceptance blocks remain partial. No HA-03 cutover, percentage or ETA is asserted.
