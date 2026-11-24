# 24 November 2026 — HA-02 actual collector launch/source binding

Selected task: CONTROL-HA-20261123 / HA-02. This fills the workstation source/launch portion
of the [joint activation proposal](2026-11-24-control-ha-collector-admission.md#joint-activation-proposal--not-executable-authorization).
It is not installation, approval of the whole runtime, a coherent capture or stage2 completion.
No RU/NL connection, Docker dispatch, product DB read, timer/service mutation, version change,
release/signing or public artifact update. The completed collector admission is not reimplemented.

## Actual launch targets

Read-only local user-systemd observation starts22:49:23.554869UTC. Both services are loaded,
inactive/dead with MainPID/ControlPID0 and no queued job at that point; both timers are active/
waiting. This is a point observation, not a global quiet interval or proof of no manual writer.
The unit and user-manager environment have no `FC_CONTROL_CAPTURE_GATE` assignment; no unit
EnvironmentFiles are configured. The monitor has an existing known-hosts argv override/drop-in,
which remains unchanged. Private argv/unit-property evidence is retained without printing secrets.

| Role | User service | Observed entrypoint root | Interpreter / budget |
| --- | --- | --- | --- |
| Inventory | `family-connect-readonly-monitor.service` | `/mnt/data/fc-subscription-operations-20261107/collector-runtime` | `/usr/bin/python3`, UID1000,500s |
| Network probe | `family-connect-network-probe.service` | `/mnt/data/PycharmProjects/family_connect` (main working checkout, canonical `/home/joker/PycharmProjects/family_connect`) | `/usr/bin/python3`, UID1000,95s |

Both entrypoints match the exact pre-admission source from c5e404ca, not the source candidate
b5dce8de. The monitor SHA256 is `2b56e0c3504e28bf644e17cf0cc4c14d5106c9862a9af80e97c8d7d62b490fd7`;
probe `cabe6f1a49f80e6aa9afff8d8f813c921a191a40eb61f7313af110a8037e64eb`.
Neither root contains the three shared admission helpers. Therefore a source push or changing
only one timer's environment cannot activate the new collector boundary.

At22:56:58UTC the selected loaded configuration fields and parsed ExecStart argv still match;
timers remain active, monitor timer running and probe timer waiting. Normal timer progress is
not a mutation by this task. No timer was stopped, restarted, triggered, reloaded or disabled.
The original selected source hashes still match after final package generation22:58:13UTC.
This is not attestation of Python objects already loaded by another process or all inherited
environment, library, Docker/SSH, import-path or host trust settings.

## Prepared candidates and rollback

`scripts/package_capture_collectors.py` reads only a fixed role-specific Python source set.
Caller pins must cover every selected present/absent member. Entry replacements accept only
the reviewed old or current admission bytes; different installed modifications are refused,
not overwritten. Existing dependencies are preserved byte-for-byte. Unexpected namespace
initializers, changed helpers, missing/extra/wrong pins, symlinks, hardlinks, special files,
world-writable/set-ID/oversized sources and observed changes during reading are refused.
Candidate sources are pinned to b5dce8de's reviewed hashes; they are compiled, not executed
by the builder. No state/config/keys, arbitrary tree traversal, installation or live dispatch.

Output is a deterministic0600 source archive outside both source roots, created exclusively
without overwrite. It contains candidate sources, a manifest and original changed-source
preimages under `rollback/`. The manifest distinguishes files to restore from newly added
files to remove. It always says `installed=false`, `runtime_qualified=false`,
`capture_permitted=false`. It contains no installer or automatic rollback command.

| Role | Candidate Python files | Changes | Rollback | Final private archive SHA256 |
| --- | ---: | ---: | --- | --- |
| Inventory | 16 | 5 | Restore2 entrypoints; remove3 newly added helpers | `2ac21a87f0507aa235933126dda9c1839775d5c434adc4a172996ad4584c7659` |
| Probe | 9 | 4 | Restore1 entrypoint; remove3 newly added helpers | `85199c65e70cfe1a5b6d0af360cb8762e39c4527e11ca24bce0a44ee40813a0d` |

Inventory changes only monitor, manual inventory collector and the three shared admission
helpers;11 selected dependencies remain identical. Probe changes only its entrypoint and those
helpers;5 selected dependencies remain identical. Full candidate archives are **not** permission
to overwrite either whole runtime directory, its `.local`, `.env`, Compose or current Git work.
The probe currently runs from main: an approved source change there must be deliberate and
tracked, not a blind copy over the working checkout. Do not silently redirect either unit to
a new directory: the collectors derive data/config and subprocess paths from their source root.

Group-writable source inputs are allowed for offline content-pinned assembly: the existing
main probe and feature source files are0664. Their modes were not changed. This does not qualify
them as an immutable trusted runtime, and does not weaken the sealed launcher's checks or
0700/0600 gate ownership. The resulting selected source set still needs exact runtime/config/
gate bindings and independent approval; a byte hash alone is not an execution trust boundary.

## Verification

**33 new package tests PASS,0 skips,2.37s**:

```text
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q tests/test_package_capture_collectors.py
```

Coverage: deterministic closed output, exact dependency preservation and rollback preimages,
excluded synthetic state, no overwrite, every pin/namespace/entry refusal, bounded unsafe-source
reads, source changes during assembly, output scope, actual unpacked script refusal and sanitized
CLI errors. No full historical or replication/recovery suite rerun. The previous117 collector
checks are retained evidence, not added to this count.
All26 distinct control/identity package pins match the test runtime. Five documentation files/
1092 local link targets and whitespace checks PASS; external links are not fetched by the checker.
Builder source SHA256: `57aea92a458ff46b3c63cd2a9750d8a7e12c66512d0fd4274ac8c28942c84990`.

Separate actual-baseline qualification uses `/usr/bin/python3`3.14.4, executable SHA256
`52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`:
all three extracted CLI entrypoints refuse a closed test gate before creating `.local` or
dispatching; both role-specific candidates then complete an admitted isolated cycle with a
synthetic SQLite commit and no remaining marker. Subprocess/network adapters are test doubles;
there is **no live Docker/OWNER PostgreSQL/SSH import or installed-gate acceptance**.
The final archives add rollback metadata/preimages to the initially qualified packages; their
complete candidate-source maps are verified identical, with deterministic repeated builds.

Initial package tests had20 failures/11 passes because the source-reader policy rejected ordinary
group-writable development files. The offline-assembly policy was corrected without chmod or
loosening runtime gates. A first isolated harness imported both roles from the inventory-only
package and refused before work; it was corrected to import only its selected role. Those failures
and the superseded pre-rollback packages are retained privately, not counted as acceptance.

## Activation and remaining fixed gates

The workstation source/launch mapping and rollback materials are now concrete. Before any
activation, approve the exact gate path/UID/inodes/mounts, loaded source/import/runtime/config
closure, both unit environments and manual entrypoint policy. Keep the current known-hosts argv
and existing deadlines. Deploy only approved file deltas, coordinate source replacement against
new and already-running collector launches, and validate the actual resulting bindings before
enabling capture. Neither this source push nor preparing test gates performs that activation.
Host gate environment is not forwarded automatically through Docker exec; OWNER container
admission and independent guardians remain required.

Next selected work is the remaining OWNER/RU/NL/manual/transport activation bindings and exact
change approval, then the real joint interval and independent checkpoint/custody/final recovery.
Working-NL changes and host-wide daemon-reload remain outside present authorization. Do not
repeat this source packaging or the completed collector/NL2 diagnostics as new acceptance gates.
The four original gates remain fixed: isolated replication PASS; current inputs/trust, coherent
all-writer capture and independent custody/final recovery partial. No new stage or ETA.

No live rollback is needed. For future approved activation, first abort/release capture and
reconcile dispatched work, then restore only exact previous source bytes or remove only newly
created helpers whose current bytes still match the approved candidate. A mismatched target
aborts rollback for review; never overwrite unrelated edits. Preserve pending markers, DBs,
consent state and access. Source rollback cannot cancel Docker work; disabling gates during
capture, deleting uncertainty or stopping paid-watch/retention is not a valid rollback.
Private source bundles, raw unit/argv evidence, synthetic DBs and logs remain outside Git.
