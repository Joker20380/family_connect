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
