# CONTROL-HA — selected service environment and stop-post, 24 November 2026

## Scope

Selected CONTROL-HA-20261123 / HA-02 continuation after
[mailbox cleanup](2026-11-24-control-ha-mailbox-cleanup.md). This resolves the explicit scoped
environment/source-observation gap from [profile runtime](2026-11-24-control-ha-profile-runtime.md),
and qualifies the exact diagnostic hook in an isolated synthetic stand. It does not qualify the
whole runtime, activate writer admission or complete any of the three remaining HA-02 gates.

NL1/NL2 were accessed with existing strict SSH pins for read-only systemd/proc/source observations.
No RU access, production helper/hook invocation, service start/stop/reload, unit/environment/key
change, product database access, production write, deployment, image replacement or cutover.
Client/build/installed/public-installer/catalog/invitation versions remain unchanged; no binaries
were built or published, no release tag or signing operation. Existing candidate packages remain
unapproved/uninstalled. This is a source/evidence checkpoint, not a release or rollout.

## Observer contract

`scripts/control_ha_service_environment.py` observes only
`family-connect-restricted-bootstrap.service`. It requires root, active/running with ControlPID0,
and a well-formed invocation. It binds MainPID/start ticks, loaded Environment/EnvironmentFiles/
UnsetEnvironment and ExecStopPost with before/after property, process and file checks. Runtime
values never enter the returned receipt or exception text; raw observation stays private.

- Loaded assignments precede provider files; later files win. Exact-value and name-only unsets
  are checked. Missing, different or unexpectedly retained selected names are not MATCH.
- Only an explicit literal UTF-8 environment-file subset is supported. Quotes around whole
  single-line values are supported; escapes/multiline/export syntax refuse, not guessed parsing.
  Paths must be absolute/canonical literals; optional globs/specifiers cannot be mistaken for
  absent files. Missing optional files are rechecked, including dangling symlinks.
- Files must be bounded root-owned regular single-link files without symlink ancestors or
  group/world writes. Hash plus inode/metadata is read back. This is not complete directory,
  executable, namespace or loaded-module attestation.
- Hooks support explicit `/usr/bin/python3`, with no flags or the enumerated isolated/buffering/
  bytecode flags, then an absolute `.py` script. Shell, module, inline or unknown dispatch refuses.
  Source is parsed/pinned, not imported/executed; argv is hashed, not disclosed.
- Results always deny full-runtime qualification, independent approval and capture permission.
  Exceptions return opaque refusal. Exit0 means selected names matched, not service acceptance.

`/proc/PID/environ` is a process environment snapshot, not proof of subsequent in-process changes,
configuration use or all manager-injected values. Two matching observations do not form a
continuous atomic interval and cannot rule out change-and-revert between them.

## Native read-only observations

Final observer SHA256:
`fa28995c984598a929d433ccbcc3ab0a2f138ae70fe3929dd8e9e91e7489cff7`.

| Node | UTC observation | Process | Selected comparison | Stop-post | NeedDaemonReload |
| --- | --- | --- | --- | --- | --- |
| NL1 | 21:35:59.347–21:35:59.410 | PID2147022 | 3 names MATCH | 1 Python hook | false |
| NL2 | 21:36:00.148–21:36:00.221 | PID391384 | 1 name MATCH | none | true |

Both invocations/process-start identities and files remain equal on readback. Each service uses
one provider file; NL1 also has two loaded assignments. No selected value is missing/different
or unexpectedly present after unset. Each process has11 additional names outside the comparison.
Only these services were checked: this is not a fleet-wide health or VPN/data-path assertion.

The first NL1 probe refused because its actual Python hook has no `-B` flag; the initial observer
assumed that flag. Source/tests now explicitly cover zero flags and the supported flag list.
This was an observer limitation, not a service outage. Final NL1/NL2 reads both exit0 with empty
stderr. NL2's reload marker persists: [the earlier14-setting match](2026-11-24-control-ha-runtime-qualification.md)
and this environment match do not explain it or authorize daemon-reload.

## Exact hook qualification

NL1 diagnostic hook source SHA256:
`707a71e7016a21c65a06e14432659e2778aab61a140968177fafc6ea58c1c889` (3842 bytes).
Static inspection finds synchronous `systemctl show` with a two-second subprocess timeout, then
bounded JSON writing via temporary file/fsync/hard-link, retention of32 reports and directory
fsync. It does not spawn detached work. Its top-level wrapper suppresses OSError/ValueError;
zero exit is therefore deliberately insufficient evidence that a report was written.

Exact retained source, never invoked on NL, passes seven local container cases at
21:35:18.068–21:35:23.349UTC:

1. Successful synthetic systemd query produces a valid0600, single-link report before exit.
2. Duplicate invocation does not overwrite its first report.
3. Invalid output-directory mode returns zero without creating a report.
4. Invalid invocation ID returns zero without creating a report.
5. A different systemd invocation cannot contribute metadata to the report.
6. Timed-out test systemctl child is killed and reaped before the hook returns; the report has
   no matching property metadata. Timeout is not treated as a successful query.
7. Retention leaves32 invocation reports and no temporary files after normal completion.

Stand: UID979, Python3.14.10, existing image
`sha256:43943c65d0c68dbda76eaac635a7f5b708cc659e0996c61853330fdaeb49d419`,
read-only rootfs, no network/mounts/host sockets, all capabilities dropped, no-new-privileges,
64-PID/192MiB/one-CPU bounds, owned16MiB writable executable tmpfs. Synthetic systemctl is
preflighted; output and argv are synthetic. Container is removed after the run. The first stand
did not obtain synthetic query metadata and failed its assertion; no PASS was accepted. The
final fixture explicitly permits its test binary on tmpfs and preflights it before the hook.

This is not the installed NL1 Python3.14.4 runtime or real systemd shutdown/output-resource
qualification. It does not prove power-loss durability, crash cleanup, simultaneous invocations,
full hook-output directory bindings or the settlement of any product writer. Do not remove the
diagnostic hook or alter its failure policy based on this checkpoint. Do not count its diagnostic
receipt as a profile/RPC transaction ACK or infer it caused earlier RU outages.

Private evidence is retained under the local control-ha evidence root; current pointer:
`/tmp/fc-ha-service-runtime-current`. Raw environment discovery, receipts, exact hook source,
final observer and stand stay outside Git (0700 directory/0600 files). Stand harness SHA256:
`0eeaf26f754d81bed88dfd03842974e6bfd4759ae379d936515068ba7e6beb08`.
The sanitized summary records hashes/counts/times, not environment values. Private source is
first inspected and hash-checked; any reproduction must use the same isolation, never the real
output directory or the production hook on a working server.

## Tests and remaining gate

Python3.14.4 HA virtualenv: **162 PASS/0 skips /1.45s**, including70 new observer cases.

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_control_ha_service_environment.py \
  tests/test_control_ha_profile_runtime.py tests/test_control_ha_runtime_qualification.py
```

Coverage includes precedence/unsets, secret-free failure output, ambiguous path/syntax refusal,
file identity/permissions, no-flag dispatch, busy unit/process/file drift and optional files.
No dependency/lock changes. This focused PASS is not a full-suite PASS: the earlier unrelated
announcement-pin failure and GUI/device acceptance limitations remain documented in the mailbox
report. Documentation/local links and whitespace are checked separately; no external artifact
verification or public rollout is claimed.
Changed documentation:4 files/1067 link targets/zero errors; staged whitespace check PASS.

The [fixed four-gate map](2026-11-24-control-ha-support-admission.md#fixed-ha-02-completion-map)
remains: replication PASS in isolation; current inputs/trust, coherent all-writer capture and
independent custody/final combined recovery partial. Next work is remaining full runtime/helper/
AWG external settlement, collectors and bounded manual-write coverage, then the concrete joint
activation/capture proposal, actual coherent interval and independent current-input/custody/final
recovery. In particular, AWG's asynchronous stop is not settled by this unrelated diagnostic
hook. Do not repeat these scoped comparisons as additional gates or silently waive the known
runtime/reload limits. No new stage, percentage or unsupported completion date.

## Rollback

There is no live rollout to roll back. The observer runs from SSH stdin, leaves no remote source
file and performs no mutations. Remove/revert the new observer/tests before future use if needed;
preserve private receipts and existing admission pending markers. Container-only test state is
discarded; no production restore/restart/reload is necessary. Any later gate activation requires
its concrete approved package/configuration, abort/rollback procedure and emergency access;
this source push does not authorize deployment or production cutover.
