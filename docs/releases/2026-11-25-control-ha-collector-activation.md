# 25 November 2026 — HA-02 workstation collector activation

Selected task: CONTROL-HA-20261123 / HA-02, not a new acceptance gate.

## Authorization and starting state

Owner: «дальше давай тогда. делай все что надо. все разрешения у тебя есть.
утром посмотрю на результаты. все документируй. нужно качественно».
This authorizes the selected participant installation and bounded operational work with
verified rollback on OWNER/RU/NL1/NL2. It supersedes the previous NL read-only restriction,
not technical access, independent trust, preservation of paid-watch/deny enforcement or
the prohibition on silently erasing uncertain operations. HA-03 cutover is not selected.

At00:51:18UTC the two existing OWNER containers are running/healthy with their original
5ce82415 console and50de6f25 publisher images and unless-stopped restart policies.
A subsequent nonprivileged `docker exec` probe in the actual console reads matching self/PID1
mnt4026532679, pid4026532682, user4026531837 and time4026531834 namespace inodes (device5).
UID/GID10001, supplementary groups980/10001; uid/gid maps are0:0:4294967295. This resolves
the specific namespace-read limitation without sudo, host-PID helper, chmod or policy change.
It is a point observation, not gate installation, loaded-source proof or future continuity.

The same probe uses a read-only PostgreSQL transaction with3s statement/1s lock timeouts:
one published system message, no other sessions observed. No row bodies, device identifiers,
credentials, tokens or keys are printed. An empty activity sample is not an all-writer drain.

## Source preparation

`probe_network.py --runtime-base` selects an existing absolute runtime directory, resolved
before invoking the existing admitted cycle. Without the option the original source-derived
base remains the default. Compose, .env and .local continue to come from that base, not the
new executable capsule. Invalid/missing/file/relative bases refuse before dispatch; a held
gate returns75 before any local writes or network/Docker work. No automatic root discovery,
state copying, credential movement or service mutation is added to this CLI.

The closed collector packager now pins the new probe source and still recognizes the prior
reviewed admitted probe as an input. Other sources and admission semantics are unchanged.
This avoids copying implementation over the main navigation checkout merely because a user
timer currently launches from there. The inventory runtime retains its existing source root.

Validation:68 tests PASS/0 skips in1.57s,6 new CLI cases, using the existing control/identity
environment. JUnit is private `/tmp/fc-ha-collectors-runtime-base.xml`. This is source
qualification; deployment/normal-cycle success must be recorded separately below.

## Planned bounded installation and rollback

Retain exact source preimages, loaded unit/drop-in and timer state privately. Stop only the
two collector timers, let active oneshot cycles settle without killing them, and refuse
installation if their service/process/job or existing cycle lock cannot be cleared. No
VPN, paid-watch, system publisher, OWNER console or PostgreSQL service is stopped.

Install only pinned inventory changed-source members with their preimages retained; place
the full probe capsule in a fresh private directory. Preserve the existing probe runtime base,
inventory known-hosts argv and all other unit settings. Create separate same-owner private
gates and add only the reviewed user-unit environment/ExecStart overrides. User-manager
daemon-reload is scoped to these installed user units, not a remote host/system reload.

Verify held-gate refusal without dispatch, ordinary admitted cycles and loaded unit/source
bindings before resuming original timer scheduling. A failed/unknown external action keeps
its pending marker: later success, service exit0 or rollback is never permission to clear it.

On installation failure keep capture disabled, stop new timer dispatch, wait for owned work
to settle, restore exact changed source preimages and unit drop-ins, then restore the original
timer activity. Never rewind product data, remove another process's files, kill outstanding
imports or restart a service that was previously failed/inactive as an inferred rollback.
Keep private new gates/capsules/evidence, including unknown markers, for reconciliation.

## Acceptance boundary

At this source checkpoint no collector is installed yet. Source push is not deployment proof.
Even after host collectors are admitted, their Docker imports require separate container-side
participation. Manual direct ORM/DB/SSH/Docker entrypoints and the other OWNER/RU/NL writers
remain separate participants. The three unfinished HA-02 gates remain current-input trust,
coherent all-writer capture and complete independent recovery; replication remains PASS.
No product/client/image version, catalog, installer or public release changes.

## Actual installation — 01:00:32UTC

Source checkpoint93f4ce3c is pushed and remote-SHA verified before installation. At
**01:00:32.902740UTC** the two workstation collectors are installed, not merely built:

| Participant | Installed source | Kept runtime/state | Gate and unit delta |
| --- | --- | --- | --- |
| Inventory |5 changed files from the16-file pinned package in the original collector-runtime root | Existing .local/.env/Compose and known-hosts argv | Separate UID1000 private gate; environment-only user drop-in |
| Network probe | Fresh9-file capsule, probe SHA19ed2bf5e2769cc4f5f1b5bd2b94b4ac74212ecd0059d95f5ff8af6c6cd3f9bf | Original main control_plane base selected explicitly; main sources untouched | Separate UID1000 private gate; environment plus ExecStart override |

All original non-gate environment assignments, inventory ExecStart, both KillMode and
TimeoutStartUSec values are checked unchanged. No timer enable/disable setting changes.
Only these two timers stop dispatch; active oneshots are allowed to finish without signals.
Existing monitor/probe locks are held during file installation. No other service is stopped.
Private0700 gates contain0600 lock files. Two actual source CLI invocations under held gates
return75/CAPTURE_BUSY without output, dispatch or residual pending markers.

At **01:00:50.439377–01:01:00.237839UTC**, actual user-systemd starts of both services finish
with Result=success/ExecMainStatus=0, no remaining process and **zero pending markers in both
gates**. Probe finishes01:00:54UTC; inventory finishes01:01:00UTC. The later ordinary
inventory cycle01:02:15.662261UTC imports all three authorized sources RU/NL1/NL2 and technical
metadata successfully. Both timers are active. Existing OWNER console/publisher remain healthy
on original5ce82415/50de6f25 images; neither is restarted/reconfigured by this operation.
Inventory performs its existing read-only remote collection and local product imports; these
normal local observation writes are not a coherent HA snapshot or a database-version change.

### Failure handling actually exercised

Preparation first catches an umask-sensitive self-test expectation before any live mutation.
The corrected file writer explicitly sets requested mode. Six isolated filesystem cases cover
failure after each of five source replacements plus complete apply/revert with mode preservation.

The first real installation attempt refuses its post-readback: systemd's ExecStart property
contains last-run timestamps/PID/status, which daemon-reload resets even when argv is identical.
Automatic rollback restores all original source hashes, removes both new drop-ins and resumes
both originally active timers. Those facts are independently read back before retry. No unknown
operation marker is deleted, database rewound or outstanding import killed.

The retry compares the full command configuration prefix separately from a strictly parsed
execution-result suffix, plus complete environment assignments. It does not ignore argv,
ignore_errors, interpreter, runtime root, security or timeout differences. The corrected attempt
passes. Failed-attempt artifacts remain private alongside successful evidence.

### Retained operational rollback

Private working record: `~/.local/share/family-connect/control-ha/20261125-collector-activation-4sc56eop/`.
It contains0600 original unit observations, source archives/preimages, new drop-ins, installer,
receipts and a standalone stdlib-only `rollback.py`; directories/gates are0700. Never add this
directory, raw unit environment or source capsules to Git. Preserve them on this workstation.

With no capture in progress, rollback is explicitly invoked as:

```sh
/usr/bin/python3 ~/.local/share/family-connect/control-ha/20261125-collector-activation-4sc56eop/rollback.py --confirm-no-capture
```

It verifies archive/source/drop-in pins, stops only these timers, waits at most520s for existing
services without killing them, and takes exclusive local gate locks. Pending uncertainty, changed
source/drop-ins or conflicting work refuse rather than erase evidence. It restores the two
inventory entry preimages, removes only the three added helpers and two owned drop-ins, reloads
the user manager and resumes originally active timers. It does not delete probe capsule/gates,
private evidence, .local state or observations. On refusal after timers stop, timers may remain
stopped: inspect/reconcile the explicit blocker before restoring dispatch. No blind rollback retry.

Five isolated rollback cases pass using real source files/archives and fake systemd calls:
complete restoration, retained pending marker, later source edit, later drop-in edit and wrong
archive checksum. They do not claim a second live rollback. The earlier first-attempt rollback
is the actual live proof. No power-loss or all-writer/fleet-fencing claim is made.

| Retained artifact | SHA256 |
| --- | --- |
| Inventory package |2ac21a87f0507aa235933126dda9c1839775d5c434adc4a172996ad4584c7659|
| Probe package |201f7346a14116ba033bde4bb24ee121b8cd2db35c2153f137d9163561cac437|
| Installer |7dd3600ad9c8c34b12102d8801ed4bf7b160848de76ccad14c29f14026668de0|
| Rollback helper |88dcea70f4247b6ecd1e18657ee5406607ae28ecaa1c9955b17cff4f3bf73409|
| Rollback test receipt |26ecf0f213649a6b3b97fb2f1a25aea6c51bafff2b245d5ba4a6c90015bca4a8|
| Installed receipt |4d372c775c2580e3eaaed4a5531df497fb693638d35da3fb41ba54efcd9729d3|
| Actual service cycles |885f36120304eaad7703cbcf05c970d8f8f594e1db80a7e7a73d8819ab4d8d88|
| Initial sanitized post-readback |0cf49e8772dfc041066647713eb84317c508ae4c089e39c111880847a4f03237|

The initial post-readback predates the standalone rollback-helper amendment; its older helper
hash is historical. The table pins the tested final helper. The installed source and units are
unchanged by that amendment. The existing container-side/manual/remote participation, actual
coherent checkpoint and independent approval/custody/final recovery remain required.
