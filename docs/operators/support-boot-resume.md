# OWNER support: forward resume after boot/process loss

Scope: the accepted support archive621009b8 and its installed OWNER/NL1 startup fence.
This procedure restores service, not a coherent capture or HA trust authorization.
Do not run it against the currently accepted, active support merely to refresh tooling.
[Actual incident, qualification and immutable receipts](../releases/2026-11-26-control-ha-owner-boot-resume.md).

## Inputs and prestate

Use the exact qualified controller source `2f4f83dd51cd3814a2da631cb3d95140af5c2a90`
for a **new** operation. Its retained source capsules are
`/opt/family-connect-support/ha02-tools-2f4f83dd` on OWNER and
`/opt/apps/family_connect/state-ha02/tools-2f4f83dd` on NL1. All373 capsule files were
independently compared to the source commit. Revalidate their bytes before reuse.
The18:52UTC working operation is pinned to2f4f83dd. Its14d4dfad predecessor and the
earlier0e4e85b5 tool capsule remain immutable; never replace old operation source files.

The accepted192343eb collector installation changes the shared baseline's closed source
set. The older controller correctly refuses `SOURCE_CLOSURE` there. The bounded recovery
correction adds `--installed-collectors` to **new accepted-predecessor preparation only**:
it admits exactly the four committed192343eb file hashes, retains the original manifest,
and records `baseline_variant` plus the exact source transition in the new operation.
Extra/missing/changed files, source symlinks and altered original pins still refuse.
Use it only after exact-source native qualification and independent installed-byte checks;
the correction is not yet an installed/qualified operational checkpoint in this revision.
Do not alter old plans or use this option for unknown collector versions. Future resumes
inherit the recorded variant. No collector installation or mandatory-gate fix occurs here.

Obtain root using the normal local password prompt in the same execution session.
No permanent sudoers/polkit changes. Retain private copies of effective units, journals,
plan, authority, reservation, terminal/recovery records, pending markers and current
store/notification state before mutation. Do not print keys, message contents or environment.

Identify the **last accepted operation** from the installed entry/authority and its
accepted binding, not from the directory's date. After the26November stopped-capture resume
it is `/opt/family-connect-support/ha02-forward-20261126-stop01`; its linked NL1 control plan is
`/opt/apps/family_connect/state-ha02/forward-support-20261126-stop01/control.json`.
These are predecessor examples, not paths to overwrite on a later boot.

Check the current process/boot/cgroup/argv, source and archive hashes, unit settings,
IPC and retained terminal records. Exit78 alone does not identify the refusal.
The receipt directory comes from the effective entry's `--refusal-directory` argument.
An explicit terminal failure requires diagnosis and a qualified recovery; do not clear it or
retry startup to conceal it.
An old successful witness or a copied PID/boot value is never a new startup permission.

## Ordered transition

Run the following module interfaces from their verified root-owned source capsule with
the installed participant interpreter. Paths are operation-specific absolute paths;
create neither operation directory in advance, since preparation creates them exclusively.
Do not run the illustrative interfaces with literal placeholder paths.

1. On OWNER, prepare a new root below `/opt/family-connect-support` and a new participant
   below `/var/lib/family-connect-support`:

   ```text
   python -m scripts.control_ha_support_resume --root NEW_OWNER_ROOT \
     --prepare-from PREVIOUS_ACCEPTED_ROOT --participant NEW_PARTICIPANT
   ```

   The implementation proves predecessor absence, records its history, preserves the
   existing gate/markers and writes new entry/authority **paths**, not an edited old authority.
   A new boot or independently proven clean exit is required. The narrow interrupted,
   never-admitted startup path additionally requires its exact retained refusal and absence
   evidence; no generic stale-PID exception is available. Active or unexplained writers refuse.

2. Build a fresh private NL1 manifest from the newly prepared plan and authenticated
   predecessor manifest. Its exact five fields are:

   | Field | Source |
   | --- | --- |
   | `schema` | Integer1 |
   | `generation` | Fresh `secrets.token_hex(32)`; never reuse an invalidated generation |
   | `support_public` | Exact predecessor public identity; independently match its ticket digest |
   | `owner_binding_sha256` | SHA256 of `control_ha_mailbox_startup.encoded(new_plan['old_binding'])` |
   | `replacement_plan_sha256` | SHA256 of the exact new OWNER `plan.json` bytes |

   Use the existing private exclusive writer and canonical encoder; retain exact transferred
   bytes/hash. Do not construct a manifest from a previous plan or edit any installed manifest.
   This manifest is not itself permission to open links or to start a writer.

3. On NL1, use a new root directly below `/opt/apps/family_connect/state-ha02`:

   ```text
   python -m scripts.control_ha_mailbox_rollover --root NEW_NL1_ROOT \
     --prepare-from PREVIOUS_CONTROL_JSON --manifest FRESH_MANIFEST
   python -m scripts.control_ha_mailbox_rollover --root NEW_NL1_ROOT
   ```

   Retain the fresh resource preflight: current100% CPU/768MiB limits must not change and
   available memory must meet the256MiB minimum. Preparation does not open anything.
   Activation independently recloses/drains/invalidates the predecessor, installs the
   closed-on-restart guard and advances the native fence without restarting other clients.
   Require exact new manifest/ticket, closed admission, drained work0, no consumed opening
   and unchanged effective limits. A busy/unknown result is not a permit to continue.

4. Transfer the exact retained `predecessor-reclosure.json` from the new NL1 root into
   the new OWNER root. Independently verify it against the predecessor ticket and exact
   authenticated remote readback. Never synthesize a successful reclosure receipt.
   Prepare a private root-owned channel with exactly `host`, `interpreter`, `entry`,
   `plan`, `local_uid`: retain the authorized NL1 host, interpreter and SSH identity;
   use the new NL1 `endpoint.py` and `control.json` paths. Keep strict existing SSH pins.

5. On OWNER, run the same new operation with that verified channel:

   ```text
   python -m scripts.control_ha_support_resume --root NEW_OWNER_ROOT \
     --mailbox-channel NEW_CHANNEL_JSON
   ```

   It validates predecessor reclosure and the new ticket before candidate startup, issues
   one new exact-process authority through the checked admission procedure, retains the
   reservation and forward-resume witness, then requests one linked mailbox opening.
   Success is `FORWARD_RESUME_OPEN_CAPTURE_DENIED`, not capture permission.

## Readback, interruption and recovery

A separate reader must match `/proc` boot/PID/start/argv/cgroup to accepted receipt and
authority, hash the actual archive, exercise read-only IPC and authenticate a fresh NL1
observation. Require exact ticket/consumed-request binding, `OPEN_LOCAL_ONLY`, non-invalidated
opening, expected process and preserved limits. Compare original records and every previous
marker; live marker counts may grow. Distinguish historical UNKNOWN from current pending work.
Preserve message records, queue IDs and cursor/anchor; normal bindings refresh may change.

Let notifications run normally, or perform one normal oneshot invocation after IPC is ready.
Check the **completed** invocation's Result/exit status and an enabled active timer. A service
currently activating is not a completed success; inactive/dead after success is normal.
Do not enqueue a real message for this check. Nonempty queue/replay tests use isolated synthetic data.

On response loss, inspect the retained intent and fresh remote state before deciding whether
the effect occurred. Do not replay an old generation's advance/open request. Reinvoking the
same operation is allowed only with unchanged bindings: it reconciles retained effects and
does not restart an already accepted candidate. If process/ticket/boot changed, fail closed;
use a qualifying linked fresh operation rather than editing records. If the controller dies
before admission expires, the same still-bound candidate can be resumed; an expired attempt
cannot be restarted in place. Preserve the old attempt and its refusal for the narrowly
validated new-operation path. Explicit terminal failure cannot be hidden by any retry.

`control_ha_handoff --recover` remains code rollback, not this forward procedure.
`--pause` invalidates remote opening and is **not** a local-store writer barrier.
Do not remove markers, overwrite authority, restore old data or weaken gates to make a
resume/capture pass. Retain failed attempts and publish only sanitized evidence outside
the private records. Restore independent trust/custody separately; service restoration
does not choose a signer, approve floors or create an off-origin recovery kit.

## Separate stopped-support component capture

Do not retry ordinary `Gate.drain` against the running lifetime support writer.
After exact-source qualification and preserved root prestate, use a new root-owned0700
operation outside all source roots, with the accepted predecessor and its current pinned
NL1 channel. Keep the normal linked forward-resume inputs and corrected tools ready.

```text
python -m scripts.control_ha_support_stopped --previous ACCEPTED_ROOT \
  --operation NEW_STOP_ROOT --mailbox-channel CURRENT_CHANNEL --stop
python -m scripts.control_ha_support_stopped --previous ACCEPTED_ROOT \
  --operation NEW_STOP_ROOT --mailbox-channel CURRENT_CHANNEL
```

First invocation verifies loaded runtime, recloses/drains/invalidates NL1, retains
pre-stop marker bytes and sends only identity-bound SIGTERM. A timeout is a retained
closed operation, not permission for SIGKILL or a restart. Repeat the same operation
to reconcile a lost response/clean exit. Terminal or cold-boot absence refuses capture.
The second invocation holds both existing gate locks, captures private exact bytes
and invokes a separate reader. Partial output remains private and unaccepted; retry
does not clear history. Busy or unknown writers refuse. Ordinary drain remains strict.

This is a **sensitive local component**, including the store-key file: never copy it to
NL2/Git/CI in plaintext. It is not a coherent full fleet backup or startup permission.
The local reader requires the stopped original filesystem; a full independent kit needs
the separate offline reader/restore gate. Root FD census is not a fence against future
privileged writers. Integrate the proven all-writer boundary before fleet acceptance.
Then follow the fresh linked generation/authority procedure above; never reopen the
invalidated old ticket or edit old authority. Confirm notifications success and timer
readiness, and compare original history/queue/cursor/floors after normal resume.
