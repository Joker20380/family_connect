# HA-02 OWNER continuation after laptop power loss — 27 November 2026

## Panel restoration — 26 November23:38UTC /27 November00:38CET

The owner's immediate priority supersedes the earlier activation sequence below: restore
the existing panel and dependencies first. New overlays, collector binding and HA capture
are deferred. Local sudo authentication succeeded through a local Zenity password dialog
into the same privileged execution session. No password was recorded or printed; no
sudoers/polkit changes or Docker privilege workaround was used.

Fresh root-only prestate contains effective units/journals, container configuration,
the last accepted predecessor, participant/refusal/terminal records, original authority,
support history and gate markers, and the unfinished bound collector-install phase files.
The latter contains preparation/source/plan records only; no activation is inferred.
Actual support refusal is `START_AUTHORITY_CHANGED` at the authority phase, with admission
false and a different boot. Original authority still exactly matches the accepted predecessor;
no terminal failure was found. This is not a diagnosis inferred from exit78 alone.

Docker's missing-mount failure is dated22:48:12.937179608UTC. The runtime directory now
exists and has ctime22:48:14.302085UTC, owner997(fc-support), group980(fc-support-ipc),0750.
The installed unit owns its lifecycle (`RuntimeDirectory=family-connect-support`,
`RuntimeDirectoryMode=0750`, `RuntimeDirectoryPreserve=yes`). The current directory was
empty before restoration. No directory creation, permission change or lifecycle override
was necessary: absence at the Docker startup attempt is distinct from its current state.

After checking the actual installed command/config and34 already-applied migrations
(0 pending), only the existing console container was started by exact ID. Its image
remains5ce82415; ID/Config/HostConfig match prestate. Its installed command has no seed_demo;
repository Compose was not used. PostgreSQL and publisher were not recreated/restarted;
their IDs, image/config and start times remain unchanged.

A fresh Chromium session used the existing local operator credentials through the normal
login form, not a forged session or an account/password reset. Overview, subscriptions,
payments and2 existing subscription-device cards return HTTP200 with authenticated content;
normal logout succeeds. No messages or business mutations were requested. Only standard
login/session bookkeeping occurred. Initial test-harness handling of a same-document anchor
returned no navigation Response; that diagnostic is retained and the URL-normalized repeat
passes. It was not a panel/authentication failure.

Normal dependencies are still under recovery, not PASS. The qualified2f4f83dd resume
preflight refused `SOURCE_CLOSURE`: the accepted192343eb collector component added
`control/capture_gate.py` and `provisioning/owner_capture.py`, and changed the two collector
modules in the shared application baseline. All other baseline source bytes remain pinned.
No new operation/authority/ticket was created by that refused preflight. A source correction
is being qualified to admit only that exact closed four-file source transition, explicitly
selected for new resume preparation, retaining all original baseline pins/history and
every other source/process/authority/gate check. Collectors themselves are not changed.

The correction exposes `--installed-collectors` only on new accepted-predecessor preparation.
It records the exact four source pins and a baseline variant in the new operation, retaining
the original baseline manifest. Seven focused source tests cover explicit selection and
extra/missing/changed collector/changed support/symlink/altered-manifest refusal. Native
forward-resume tests now cover that installed variant, nonempty queue and lost-response retry.
The first local native run had12 PASS and one existing fixture read race (empty JSON while
the remote test probe was writing), before exercising the transition; the diagnostic is
retained. A complete repeat and exact-source native CI are required before activation.
No production authority, ticket or operation was created by these isolated tests.
The combined repeat has56 PASS/1 failure: an unmodified fixture predecessor exited78
(`CANDIDATE_EXCEPTION`) during its initial stop, before preparing the new resume operation.
That diagnostic is retained separately; it is not classified from exit78 alone or waived.
Exact-source native qualification remains the activation gate. Notifications.timer is now
temporarily held by this recovery execution, still enabled, to avoid dependency-failure loops;
restore this additional hold only after one completed successful normal notification invocation.

At27 November00:15UTC, source39caf062cf6b6b58977dfb7d7a3428246aac852c is pushed and
independently materialized as373-file root-owned source-only capsules on OWNER and NL1.
All files match Git; neither installed app nor an operation/authority/generation was changed.
Corrected read-only preflight independently returns PREVIOUS_PROCESS_ABSENT / BOOT_CHANGED.
The focused repeat passes8 native resume cases;7 source negatives/selection checks also pass.
Android readiness, Linux preview and phase0 CI at that exact source all pass.
Native run45913167010 attempt1 completed349 PASS/2 failures,0 skips, not acceptance.
Artifact15162010234 SHA256541b18a7d41ee414906a8164d50d758e5585e51afa13276c6020dfc9d7b838d8
is downloaded and independently parsed. The failures are OLD_RUNTIME_CHANGED in the legacy
fixture's initial exit and MANUAL_RECONCILIATION_REQUIRED in initial handoff, both before
the new baseline transition. Their initiating causes are not inferred from those labels.
No tests or guards were weakened; one complete same-SHA native repeat is running. A private
read-only diagnostic repeat of the two prerequisite cases also runs independently.
The full qualification gate remains required before production recovery activation.
Independent marker readback confirms exact names/body hashes/mtimes of3 original and12
additional inventory markers plus14 probe markers. All33 prestate support markers remain
unchanged separately. No old dispatch settlement or coherent capture is claimed.

Private restoration evidence is at `/mnt/data/fc-ha02-panel-restore-20261127`; sensitive root
prestate is in its root-only `root` child. Browser screenshots/credentials are not published.
Notifications and the two held user timers remain pending support recovery. The separate
3 original +12 additional inventory markers,14 probe markers and support history are retained.

## Earlier continuation checkpoint — retained history

Observed26 November22:57–23:05UTC /27 November00:05CET. This is an incomplete
operational checkpoint, not a release, installed all-writer PASS or coherent capture.
The selected OWNER/all-writer NEXT is unchanged; HA-03 has not started.

## Recovered stopping point

Both agreed worktrees were clean and matched their upstream after fetch: main8ae94720
and feature/device-technical-metadata-20261115 atb7f4cbd2. The missing-gate correction
was already committed/pushed; it was not lost with the laptop shutdown. No source
rewrite or repetition of the accepted existing-gate collector component was needed.

Current installed `owner_capture.py` SHA256 is
`1997f1bf5da19ad1a2d11b16d83a71c217d1ea1f5f4cc440ef59db9e07e737cf`
(192343eb), not candidate
`b7b1fb3ffe69d9428cb419a30d2473a2bb73a6ffb2e7c6390b6878afc953a45d`.
`/opt/family-connect-support/owner-collectors-capture.json` is absent. The private
bound installer/readback/rollback and source archive already exist; their operation
directory is root-only. Its retained phase records must be inspected before any retry;
directory existence is not evidence of a completed install. No privileged operation
was attempted in this continuation because `sudo -n` requires interactive authentication.
No Docker-based privilege workaround, permission widening or permanent sudo rule was used.

## Exact-source qualification

All five workflows for `b7f4cbd2b96750cb9c97eee61f27a9881d5b4bdb` completed successfully:

| Workflow | Run |
| --- | --- |
| HA-02 native support qualification |45905231638|
| Linux internal candidate |45905231643|
| Linux control preview |45905231639|
| Android Friends readiness wire contract |45905231613|
| phase0 |45905231717|

Native artifact15158386237 was downloaded and independently read, not merely trusted
from a successful run badge. Archive SHA256:
`95830fd5c13988736870f66e0bbed35197723b2c22f3da1c1f3480885dc0fed0`.
The receipt source matches; XML contains342 cases with no skips/failures/errors.
The5 disposable root/systemd sandbox cases bind the exact candidate source hash.
Local `python3 -m pytest -q tests/test_owner_collector_capture.py`:34 PASS. This narrow
local rerun is supplemental; it does not replace the CI lockfile/native qualification.

The saved OCI archive SHA256
`42ffb2afbe8e0752507ecf6c9842c19a7e3ab1b308d568f9082320b71cf4b6d1`
was independently reverified for both candidates. All12 overlay files match exact
Git blobs at `7a91d1278eda8594e448e5794e183e313aed8440` and current source bytes:

- Console: `sha256:3af9fbf95b36b33f1c0414ac41b84687f502391e311ff0bc35658cbf50da5cb1`.
- Publisher: `sha256:35158514371e2a321643dbfe4b64b9a87a9b85b32228a5184d2c95e3b8ac19e8`.

These are archived candidates, not installed or loaded-code attestations. A GET-only
Docker/source readback still finds2/12 matching files in each existing container.

## Actual post-boot state and bounded hold

- `family-connect-support.service`: failed/exit78 since22:48UTC; the precise refusal
  has not been independently read. Old PID1051719/authority/generation observations
  cannot authorize a new boot. No retry, marker deletion or stale-authority edit occurred.
- Subscription notifications: failed; both root collector timers still active/waiting.
  No root unit was changed. Current support/IPC health is not claimed.
- Console5ce82415: stopped/127; Docker records a failed mount of missing
  `/run/family-connect-support`. Its stale health field `starting` is not a healthy process.
- Publisher50de6f25 and PostgreSQL: running/healthy; unchanged images and configuration.
- User readonly-monitor/network-probe services: failed/1. Repeated timer invocations
  were accumulating new retained markers during this outage.

Prestate and exact marker hashes/mtimes were saved privately before stopping only
`family-connect-readonly-monitor.timer` and `family-connect-network-probe.timer`.
Both remain enabled but inactive/dead. No service signal was sent; both services were
observed exited with MainPID0/ControlPID0. No masks, unit/drop-in edits, data rollback
or Docker/service replacement were applied. The timers are deliberately still held
pending healthy prerequisites; normal resume has NOT been achieved.

After the hold:

| Marker population | Retained result |
| --- | --- |
| Original inventory UNKNOWN from25 November |3; original name hashes/body hashes/mtimes independently match prior receipt|
| Additional inventory markers |12; retained separately, not attributed to support history|
| Probe markers |14; retained separately|
| Support history |Not mixed into these sets; root-only post-boot readback still required|

One bounded drain check of each held user gate refuses `UNSETTLED_OPERATION`
(inventory15/probe14). Exact before/after marker sets match. `Gate.drain` is unchanged.
The two Docker containers currently report zero ExecIDs; this does NOT prove completion
of earlier Docker-side/remote dispatches or erase any uncertainty. HTTP, scheduler,
management/manual ORM closure and remaining manual/native SQL/file paths remain open.

## Next permitted sequence and recovery

1. Obtain normal local root authentication in the operator execution session. Read and
   preserve the bound install operation, actual support refusal/terminal/authority and
   current gate/projection state before changing anything. Do not blindly replay the
   old installer after a reboot or infer failure cause from exit78 alone.
2. Follow [linked boot/resume](../operators/support-boot-resume.md) with a new operation
   only after the retained predecessor state qualifies. Revalidate strict NL1 pins and
   exact source/limits; independently verify fresh support/IPC, cursor/queue and histories.
   Do not open NL1 or start support using copied predecessor permissions.
3. Reconcile and commission mandatory collector binding from independently observed
   existing pins; qualify exact installed bytes, closed/missing/replaced/invalid gate,
   no-environment/direct entrypoints and projection preservation. Keep the prior
   failed/rollback records and use the verified rollback helper, not data restoration.
4. Rebase operational preflight on the actual post-boot state, preserving exact12-file
   candidate IDs/source. Restore/activate console and publisher through the qualified
   replacement/recovery procedure, then check loaded code, gate/mount, HTTP, scheduler,
   management and manual ORM. A stale running-console precondition must not be relaxed
   to force the previous activation plan through.
5. Independently settle or retain all additional external uncertainty. Preserve the
   original3 inventory UNKNOWN separately from new observations and support history.
   Restore the two held user timers only when their dependencies are verified healthy
   or at the checked normal-resume boundary:
   `systemctl --user start family-connect-readonly-monitor.timer family-connect-network-probe.timer`.
   Require a completed normal service invocation and enabled/active/waiting timers;
   starting a timer alone is not completion. If recovery fails, retain the hold and
   exact failure instead of restarting an endless failing cycle.
6. Only after installed all-writer/external-work proof, perform a fresh shared
   RU/NL1/NL2/OWNER capture with newly stopped support inside the held interval,
   independent exact-set verification and confirmed normal resume. e4eace1a is history.

Private evidence remains in
`/mnt/data/fc-ha02-boot-continuation-20261126-iYfo2r` (0700; private files0600),
including original Docker inspect/journals, timer prestate/hold/exit records, marker
partition, strict-drain and independent overlay receipts. No private payloads were
committed. Existing prepared operation evidence remains at its original location.
No product/application version, public installer/catalog, release tag, server policy,
paid-watch/deny rule or neighbour service changed. Source pushes are checkpoints only.

## Custody remains factual, not assumed

Joker is the selected signer/custodian; NL2 is the selected ciphertext destination;
KeePassXC is known and project history identifies `Family-Connect.kdbx`. The actual
off-laptop copy and access recovery without the laptop still need factual confirmation.
USB is not required. No vault or secret entries were opened, no new key was generated,
and no transfer, checkpoint acceptance or independent custody PASS is claimed.
