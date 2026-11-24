# RU-TRANSPORT-RECOVERY-2 — 8 November 2026

Base: main `ba969a94fced2953143f47360e34eb78c054d17f`. Closed PR8 and the
[own-subscription PASS](https://github.com/Joker20380/family_connect/pull/8#issuecomment-6717509534)
are not reopened. The owner authorizes RU incident diagnosis, controlled recovery,
minimal accepted node changes and two physical RU transport checks only. NL is read-only;
its existing central lease refresh continues. Paid/identity/period data, APK119,
G4/renewal and cold provisioning are outside mutations.

## Historical evidence preserved before mutation

All times UTC,8 November. Private files include installed hashes, effective units,
service properties/InvocationIDs, jobs, state/bindings, attempt, locks/processes,
canonical fingerprints, bounded unit/central/system/kernel journal windows.

| Time | Observed fact |
| --- | --- |
| 02:34:07.936 | Last successful watcher pass:0.119839s; useful-progress gap2.120327s. |
| 02:34:18.298 | First error: pass8.361993s; readback8.356218s; engine queries0.029919s; lock0.000029s; plan0.005138s. |
| 02:34:18.313–20.083 | AWG/TCP protective shutdown, after the watcher error; no claim that this was an initiating external stop. |
| 02:34:19.985 | Watcher exit-code failure, not a recorded watchdog termination. |
| 02:34:25.084 onward | Watcher restarts, startup plan completes, engines remain down; repeated wait/error passes and subsequent failures. |
| Adjacent central cycles | RU changes from applied to unavailable; both NL nodes continue applied. |

The bounded kernel window contains no OOM/reboot evidence. Last Result/exit-code or
generic wrapper text does not identify the first exception. The eight-second budget
was exceeded during readback, while recorded native queries were short; persistence
or scheduling delay is a **hypothesis**, not an established historical cause.
Precise first exception/command/persistence phase is **UNKNOWN**. No production fault
injection or trigger reproduction was performed.

## Controlled availability recovery

Actual RU node/gateway and drop-ins match the previously accepted kit. Retained cache,
ownership/modes and bindings validate; current disk/memory checks did not establish an
ongoing blocking resource failure. The narrow central command fence affects only RU;
full three-node first-enrollment configuration remains intact. Stop watcher and both
engines → verify all PID0 and no remaining service jobs → start through exact preflight.
Services started05:14:46; original central command bytes restored. No initial prepare,
cache deletion, manual deadline extension, ledger restore or HTTP restart.

The first recovery window spans more than135s with stable PIDs/restart counters,
matching live/persisted sets, expected/applied revisions and paid lease refresh through
120s. Observed sets are RU20, NL1 48, NL2 5, not historical assumed counts. RU includes
the owner's ordinary profile registration retained from the failed smoke; this is not
a new paid/cohort entry. Authenticated panel HTTP200/no-store shows fresh successful
sources. Its retained incident history contains133 RU unavailable snapshots; errors
were not rewritten into zero devices or paid denial.

## Minimal diagnostic correction

- Persist/report the safe first failure before cleanup; cleanup errors remain separate
  and cannot replace it. Retain the first local record across automatic watcher retries
  and successful recovery, without overwriting it with later ENGINE_START_TIMEOUT.
- Allowlisted mode/phase/class/reason, command family/rc/timeout, elapsed/budget,
  PID/InvocationID only. No argv, raw command output, exception text, key or identity.
- Preserve command failure identity through the gateway wrapper; distinguish file fsync,
  replace and directory fsync. Keep8s operation budget,12s watchdog,120s lease, BindsTo,
  engine readback and explicit operator-driven recovery; no automatic restarter.
- No policy, HTTP/operator/reconciler, schema, Android or paid-baseline change.

Node payload (before final source commit, bytes checked by the native fixture):
`paid-transport.pyz` SHA256 `f747759cfcf5b2881a18f984c81c95647db90cd30e93eea78e60066826c73131`;
gateway SHA256 `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234`.
The only changed nested module is `control/friends/transport_gateway.py`; policy and
other nested inputs match the actually installed accepted archive. Final source SHA,
outer archive/inventory, CI, merge and RU-only installed pins belong in the final PR
receipt. Historical bundles are not overwritten or reassigned new provenance.

## Checks and remaining gate

Forty-one targeted Python checks PASS: safe diagnostics, cleanup precedence, first-record
retention, command timeout/redaction, deterministic persistence-budget crossing,
existing expiry/stale/revision/membership/package contracts. Real isolated systemd,
packaged preflight, actual AWG/Xray, production user/sandbox and63 synthetic records
with19/48/5 registration layouts PASS. Positive HTTPS precedes terminal revoke;
injected TCP query rc73 produces the exact safe first-failure record before cleanup,
stops engines in0.262s in this run, and controlled stop/PID0/start restores noncohort
traffic while terminal-denied AWG/TCP/mux remain denied. These are **synthetic** flows,
not physical production acceptance. Failed fixture attempts remain private evidence:
an incomplete scratch kit and overly compressed transition sequences hitting the
fixture's120s start-limit. The final narrow run omits unrelated historical transitions;
no service limit/assertion was disabled. Fixture cleanup PASS.

Before final RU diagnostic delivery: ordinary review and applicable hosted green CI,
compare exact overlay to installed bytes, preserve state and per-node collector pins.
After delivery: actual processes/sets, lease boundary, several central cycles and fresh
authenticated panel. Then only physical RU AWG HTTPS and RU TCP HTTPS on existing119;
restore NL1/MESH/OFF and compare protected records. Final receipt must use
RECOVERED_CAUSE_OPEN if both physical checks pass but the historical cause remains
unknown; source instrumentation is not a historical root-cause fix.

Code rollback uses the preserved accepted node bytes with the same stopped/PID0/start
sequence and retained restrictions; no old ledger, unfenced gateway or removal of deny.
If a continuing failure prevents safe start, leave RU transports unavailable and record
NOT_RECOVERED rather than bypassing enforcement. No automatic NL rollout or next task.
