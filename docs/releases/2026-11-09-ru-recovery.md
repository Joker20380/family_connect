# RU recovery — 9 November 2026 Brussels

Owner explicitly approved the proposed controlled RU recovery after the
[8 November diagnosis](2026-11-08-ru-incident-diagnosis.md). Times below are UTC on
8 November;23:03UTC corresponds to00:03 on9 November in Brussels.

**Result: SERVER_RECOVERED; USER_HTTPS_NOT_RUN; CAUSE_OPEN.** This restores service
availability without claiming that the initiating delay or physical user traffic
has been fixed/verified. No new transport implementation or release was deployed.

## Accepted baseline and preservation

The accepted PR9 [final operational receipt](https://github.com/Joker20380/family_connect/pull/9#issuecomment-6718134611)
and current upstream recovery source were checked, not inferred from the divergent
local checkout. RU installed files match the accepted diagnostic delivery:

- paid-transport.pyz: `f747759cfcf5b2881a18f984c81c95647db90cd30e93eea78e60066826c73131`.
- awg-gateway.py: `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`.

Before mutation, retained private copies of node state/settings/configuration,
first-failure record, accepted runtime and original central commands. Consistent
SQLite backups of registry and peer bindings pass quick_check. Backups remain
root-only under `/opt/apps/family_connect/private-paid-ru-recovery3-20261108`;
no live database was restored, and no private state was added to Git or printed.
The installed Gateway loader validates63 cached decision records before recovery.

## Controlled sequence

| UTC | Action and verified result |
| --- | --- |
| 23:02:58 | Precheck passes. Both engines PID0; watcher retry count202, with another automatic retry before quiescence. |
| 23:02:58.188 | Atomically replace only gateway-ru's central apply command with `/usr/bin/false`; preserve both NL commands and the complete three-node enrollment set. The central timer keeps running. |
| 23:03:18.342 | After20s for an existing bounded RU command to finish, stop all three units. Verify MainPID0, ControlPID0, no jobs and no residual service cgroup processes. Retained cache and accepted byte checks pass again. |
| 23:03:18 | Normal systemd start of watcher/AWG/TCP through existing dependencies and root-only preflight. No direct engine bypass, new runtime, unmask or policy change. |
| 23:03:21.878 | All three units active/running; watcher329509, AWG329511, TCP329514; NRestarts0. |
| 23:03:21.901 | Restore exact original command bytes; both NL command entries were unchanged throughout. |
| 23:03:21.923 | Protected before/after projections and retained first-failure bytes match. |

Original commands SHA256:
`d07803df7c82d4dfabd6eb1131d8c9132a1df8f1a84f2103ca33fe13a5d48b11`.
First diagnostic retained unchanged:
`6b26e765fb9989cab5fc1f8092f9ab0b11fe0550d2b70ee5642ee762bdbd72c4`.

## Post-recovery validation

Thirteen read-only samples23:05:44–23:08:44 span180.103s:

- All original recovered PIDs/InvocationIDs remain stable; every sample is active/
  running and NRestarts0.
- Actual AWG allowed-IP bindings match the expected20; actual Xray identities/flows
  match the expected20. These are provisioned transport sets, not concurrent users.
- All63 cached records have matching expected/applied revisions and result applied;
  observed state age0.49–2.49s.
- The cohort lease refreshes from1794179260 to1794179430; the observation crosses
  the initial120s lease boundary without loss of expected applied state.
- paid_beta_events, paid_beta_subscriptions and device/wg/tcp/revoked projections
  are unchanged. Original central command bytes and first diagnostic still match.
- AWG has no sampled recent handshake or payload bytes in this window. No synthetic
  user was enrolled and no phone or installed client was operated. Physical RU AWG
  HTTPS and RU TCP HTTPS therefore remain NOT_RUN, not inherited morning PASS.

Central journal evidence includes the last RU-unavailable cycle23:03:26 and ten
consecutive all-node applied cycles23:04:00–23:09:06. Both NL nodes remain applied
in every retained cycle, including the fenced interval. NL services were not
restarted or redeployed. This is central ACK evidence, not NL user-traffic testing.
The watcher journal retains one startup engine-not-yet-active check at23:03:18.592,
duration0.0505s with no apply stages; it is not silently removed or counted as a new
runtime shutdown. Final summary:166 completed operations, no transport_failure,
maximum operation2.382s and useful-progress gap4.382s, below existing8s/12s limits.
At23:09:14 all original recovered PIDs remain active/NRestarts0; TCP8446 listens and
fcopen31 reports UDP51823. This confirms listeners, not external authenticated traffic.

## Scope, rollback and remaining checks

Only existing RU services were restarted and the RU apply command temporarily fenced.
HTTP, paid policy, timers,8s operation budget,12s watchdog,120s lease, clients,
public artifacts, signing and update catalogs are unchanged. No fresh client version
or rollout is claimed. Observer/recovery helper syntax and targeted operational
gates pass; no unrelated historical code suite was rerun.

No code rollback is needed: installed bytes did not change. If the failure recurs,
retain its new journal evidence and keep enforcement fail-closed; use the same
guarded procedure only within an authorized recovery. Never restore an old ledger,
remove deny/prepared state, extend deadlines or start an unfenced old gateway.
The exact cause of the9.368s plan delay remains unresolved. Physical client HTTPS
and any durable slow-plan correction are separate follow-ups, not automatically
started by this recovery. Existing unrelated local edits remain preserved.
