# GATEWAY-SEED-READ-OBSERVABILITY-1 — PARTIAL

12.10.2026, observation-only deployment. **Transport fix не выполнялся.**

Точный принятый patch собран и загружен одним controlled restart. Новый observer
сохранил естественный fatal **14:22:01.363107849 UTC: SEED_READ / SIGNAL_READ**,
exit1. Systemd выполнил automatic restart; ручного повтора не было.

PARTIAL, а не полный acceptance PASS: сразу после controlled restart локальный
deployment driver получил `AssertionError` на postcondition; полный немедленный
post-deploy gate и предусмотренный 30-minute collector **не были завершены**.
Повторять mutation не стали. Read-only reconciliation подтвердил загруженные
bytes, успешный первоначальный start, natural fatal и действующий новый runtime.
Причина отказа самого postcheck не восстановлена из сохранённого safe error
class/hash; его нельзя выдавать за отказ запуска observation binary.

## Доказательства и identities

Защищённый локальный каталог:
`state-client-build/field65-export16/gateway-seed-read-observability-1/`.
Основные файлы: `RESULT.json`, `manifest.json`, `SHA256SUMS`, `scope.txt`,
`accepted-validation.diff`, `production.diff`, `systemd.diff`, `receipts/`,
`preserved/receipts/`, `preserved/staged/`. `private/` не является публикуемым
артефактом. Старые evidence и основной dirty checkout не перезаписывались.

| Identity | Exact value |
|---|---|
| Baseline source | `abc604b0f8ce431174f260ff41ef9b3b6455ba0c` |
| Observation source, isolated local commit | `a4087e000fdbe674b72ede3a6c8822445c87c654` |
| Baseline binary SHA256 | `0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a` |
| Observation binary SHA256 | `fa4cf8672c3606c1b6d4d665a6944b4ebe8661076a19a6d2187909263f733eea` |
| Accepted prior two-file diff SHA256 | `c28411686cdee3e855114bfbfc7cc09fc7cc132172d7d69e87e6433f085580c6` |
| Validation diff including tests SHA256 | `45964e2897b63b7a48fb48d93bc3d0408eaaae533901b7da9cd0ffd6ffe1bbc6` |
| Toolchain | Go1.26.1 linux/amd64, `-trimpath`, CGO1, no new tags/flags |
| Embedded source | exact observation commit, `vcs.modified=false` |
| Receipt schema | 1, additive optional `seed_close_source` |

No public tag/release/push. ELF has normal Go build debug information like baseline;
this does not add a debugger, remote-control endpoint or listen port. Product diff
is exactly two files; tests are the exact previously accepted fixtures.

## PATCH_SCOPE / SAFE_CAUSE_MAPPING

`carrier/bootstrap/seed.go`: bounded192-entry existing `sessiontrace.Recorder`,
nil sink, constant non-identity diagnostic tag; transparent PacketEndpoint wrapper
retains existing first terminal CloseSource. No overrides of Send/Recv/Close.

`carrier/cmd/bootstrap-broker/fatal_receipt.go`: preserve existing startupdiag
priority; add typed net closed/reset/timeout mapping and allowlisted FirstClose
fallback only when cause would otherwise be UNKNOWN. First-cause/sealed guards
remain unchanged. Generic unknown stays UNKNOWN, no raw `err.Error()`/payload.

Existing EOF category intentionally covers both `io.EOF` and unexpected EOF;
the patch does not pretend to distinguish information the current taxonomy merges.
Malformed FCB1 and rejected peer auth are not relabelled shared-seed fatal errors.
Diagnostic allocation/locking overhead exists; “observability-only” is not a claim
of literally zero CPU/memory overhead.

No change to transport implementation, provider calls, seed loop, listener,
authentication/admission/holders, timers/retries, exit/restart policy, directory,
Family TLS, Reliable/Mux, framing, APK, UI or native client.

## BASELINE_DIFFERENTIAL / TARGETED_TESTS_AND_RACE

Identical synthetic local fixtures, network restricted to local test sockets;
no owner/production credentials or provider room. Commands and return codes in
`receipts/local-commands.json`; Go JSON logs preserve full assertions.

| Shared reader case | Baseline receipt | Patched receipt | Legacy return/fatal behavior |
|---|---|---|---|
| Clean EOF | EOF | EOF | Same |
| Partial/unexpected EOF | EOF | EOF | Same |
| `net.Error.Timeout()` | UNKNOWN | IO_TIMEOUT | Same |
| Caller deadline | DEADLINE | DEADLINE | Same |
| Caller cancellation | CANCELLED, nonfatal | CANCELLED, nonfatal | Same |
| Reset sentinel | UNKNOWN | CONNECTION_RESET | Same |
| `net.ErrClosed` | UNKNOWN | NET_CLOSED | Same |
| Existing SIGNAL_READ | UNKNOWN | SIGNAL_READ | Same |
| Existing queue-full terminal | UNKNOWN | RECEIVE_QUEUE_FULL | Same |
| Existing conference-ended | UNKNOWN | CONFERENCE_ENDED | Same |
| Unknown / invalid supplied source | UNKNOWN | UNKNOWN | Same |
| Malformed framing / auth rejection | Peer isolated | Peer isolated | Next valid peer succeeds |
| Successful read / controlled shutdown | Existing contract | Existing contract | Same |

- Targeted bootstrap/broker race tests **×3 on each source PASS**;12 matrix cases
  ×3 per side. Immutable first cause, late/stale cleanup, normal stop/SIGTERM,
  panic/write failure, sequential invocations, retention/modes and privacy PASS.
- Per-peer EOF/timeout/reset/cancel/auth failures release their exchange;128
  malformed packets plus following valid peer remain bounded. No behavioral patch.
- Full bootstrap/broker/sessiontrace race suite ×3 **NOT_GREEN on both**. Same six
  `TestProductIdentityOverBootstrapCarrier` diagnostic assertions remain:
  unknown, wrong-family, revoked, wrong-gateway, stale-crl, stale-revision.
  Actual security rejections continue to pass separate checks.
- Baseline busy-wire `TestAuthenticatedBusyExchangeReportsChallengeReason` also
  reproduced on both, with additional ×10 runs. No assertions weakened.
- `NO_NEW_FAILURES_RELATIVE_TO_BASELINE=true`; no race detector reports. Existing
  finite-deadline/overlap tests pass; original timing/directory source unchanged.
- Both exact binaries tested with invalid duration before provider creation:
  same exit1 / STARTUP / invalid_options and correct embedded binary/source hashes.
  New smoke-driver initially expected OPTIONS instead of the actual STARTUP;
  source inspection corrected that driver only, not any product/test assertion.
- Previously accepted22 operator fixtures rerun PASS; runbook/protocol hashes
  included in manifest. No live operator gate displayed or armed.

## PRIVACY_AND_RETENTION

Application receipts service-owned0700; systemd receipts root-owned0700;
JSON0600, max32 files per layer unchanged. Final counts9/10, bounded sizes.
Exact raw receipt bytes copied with verified SHA256 to protected evidence before
closeout; no raw profiles, keys, room URLs, SDP, tokens or user identities in them.
Write failures remain unable to replace exit cause; first failure cannot be
overwritten by cleanup. SIGKILL/OOM still relies on service-manager evidence.

## CREDENTIAL_PREFLIGHT

Fresh13:29 snapshot: original invocation active, loaded/next baseline; leaf expired
at13:36:04 UTC, only~402s left, insufficient for deployment/checks/30min observation/
rollback margin. Pre-renewal metadata, exact old receipts, units and protected
profile/binary/config backups saved first.

One same-key leaf renewal13:39:22 UTC through existing AKI-correct issuer path:
normal14400s policy, new expiry **17:39:22 UTC**. Authority/root/gateway keys,
bindings, grants/admission/revocation/floors unchanged; CRL sequence advances by
the existing sync. No authority/root renewal, vault transfer or new identity.
OpenSSL strict server/client, hostname/SNI, Python MemoryBIO, AKI/SKI, signatures,
existing native positive/negative Family validator and service-readable atomic
publication PASS. Sync timer restored in finally; API/mailbox/AWG/TCP not restarted.

Pre-deploy strict served DER already matched the renewed leaf without another
restart. Old invocation's final receipt still names the old startup credential
snapshot (`STARTUP_NOT_AUTHORIZATION`); its negative startup headroom is **not**
evidence that the fresh served chain was expired.

## DEPLOYMENT / chronology UTC

| Time | Source | Event |
|---|---|---|
|12:17:32|Historical service snapshot|Baseline invocation `853bf7d3d15b4194b19629d546eaf92b`, PID1255784, NRestarts1|
|13:39:22|Issuance/publication receipts|One normal same-key renewal|
|13:42:11.692|Protected deployment intent|One controlled restart authorized; rollback prepared|
|13:42:14.526920811|Application receipt|Old invocation SIGTERM, CANCELLED, fatal=false, cleanup complete|
|13:42:14.886838|Systemd receipt|Old invocation exit0/success; controlled stop, not natural fatal|
|13:42:14|Systemd start boundary|Observation invocation `e5b8e21cb95440ce890062bede9ea6fa`, PID1305534, NRestarts0|
|After start|Local safe error receipt|Postcondition AssertionError; no success receipt, mutation not repeated|
|14:22:01.363107849|New immutable application receipt|SEED_READ / SIGNAL_READ, returned_error/fatal=true, elapsed2386358ms|
|14:22:01.450482|Matching systemd receipt|exit1, service_result=exit-code, NRestarts0|
|14:22:31|Systemd automatic restart|Invocation `e24e32cf8121436ca6ab772f7779362b`, PID1328380, NRestarts1|
|14:26–14:29|Read-only reconciliation|Observation loaded/next, listener, strict chain and receipt modes confirmed|
|14:37:43|Concurrent RU/NL read|Same current invocation; directory/authority/CRL/floors equal, CRL22983|

Only added systemd drop-in is `99-zzzzzzz-seed-observation.conf`: reset ExecStart
to the new executable with identical arguments. Existing observer env/ExecStopPost,
duration4h/rotation3h, restart policy30s, all other unit settings unchanged.
No second controlled start/restart, reset-failed or rollback. Protected rollback
script restores baseline executable selection only and retains valid renewed
credentials. It is prepared, **not executed**.

## PASSIVE_OBSERVATION / APPLICATION_FATAL_RECEIPT / SYSTEMD_EXIT_RECEIPT

Natural fatal occurred39m46s after the observation invocation started, and was
discovered at read-only reconciliation following the failed immediate driver
check. Do **not** call this a completed30-minute monitored acceptance: the planned
`passive.py` collector was not started and its expected postchecks never completed.
No synthetic fault, deliberate long wait, second observation window or manual
restart was used to obtain the receipt. Evidence is independent app/systemd
first-cause capture, not continuous CPU/listener samples over that interval.

New application first cause is immutable:

```text
first_stage = SEED_READ
first_cause = SIGNAL_READ
safe_error_class = sessiontrace.FirstClose
seed_close_source = SIGNAL_READ
seed_generation = 1
parent_context_at_failure = empty
fatal = true
exit_path = returned_error
credential_limiting_expiry = 2026-10-12T17:39:22Z
credential_headroom_seconds = 11840
cleanup_started/completed = true/true
```

`PROCESS_EXIT_CAUSE=PROVEN` **at this narrow boundary**: the shared seed's signaling
`conn.ReadJSON` returned an error while the carrier was not already closed;
existing `signalClosedAt(..., "SIGNAL_READ")` became shared Recv failure and the
unchanged process-fatal SEED_READ path. Matching systemd invocation exited1.

The original low-level ReadJSON error still is not in this safe fatal receipt:
**LOWER_LEVEL_SIGNALING_CAUSE=UNKNOWN**. Cannot distinguish socket timeout/reset,
WebSocket close, invalid JSON or other decoding/read error from this field alone.
Do not infer DPI/provider blocking/owner identity or prescribe a timeout increase.
Historical12:17 SEED_READ/UNKNOWN stays UNKNOWN; new evidence does not retroactively
recover its raw object or establish relation to the earlier late CONNECT.

## CURRENT_GATEWAY_STATE / POST_DEPLOY_HEALTH / OBSERVER_EFFECT

Final bounded snapshots, not a future availability promise:

- active/running, PID**1328380**, invocation**e24e32cf8121436ca6ab772f7779362b**,
  start14:22:31 UTC, **NRestarts1** after automatic restart. Current Result=success
  does not replace the preceding invocation's recorded exit-code/1.
- Loaded=next **fa4cf867…733eea**, observer armed after one natural trigger.
- Current directory **631ad2197c567f8c109f6807c3afdc6596fbdcbd1af76389314d29de0b235664**;
  issued14:22:33.825470806, expires18:22:31.743955333 UTC. Current invocation seed
  only; no cross-invocation overlap. Owner cache not read/refreshed or assumed usable.
- Controlled-start retired directory was
  `c55d9c7790fecb3373dda92f3ac1ac3fa5bb1334e9907d3be80e288c6f0afd33`;
  predeployment directory `5d3bc057…71316` also retired. Publication advanced by
  existing sync; the task's explicit sync command after the failed check did not run.
- Renewed leaf SHA256 `c4991747c1605c76c8067182a611f7ab0b6e015663e6294ffb25257af962b298`,
  expiry17:39:22 UTC. Strict served chain/DER match PASS. Effective limiting headroom
  **11379.8s at14:29:41.98 UTC** (receipt epoch is authoritative); authority expires
 13.10 09:33:59 UTC, CRL valid/signature verified. No client mTLS/owner admission probe.
- Final paired read proves RU/NL equality of directory, authority DER, CRL DER,
  revision and CRL floor. Sequence changes due to the unchanged periodic sync are
  not a new trust root or silent rollback.
- 18444 listener present; final eight-second health sample: RSS26212KiB,7 threads,
  FD77→77, CPU+10 ticks, write_bytes4096→4096. No new persistent diagnostic sink.
  No lock contention observed locally under race tests; live contention/load
  benchmark was not run. `OBSERVER_EFFECT=NONE_OBSERVED`, not a causal exclusion
  of all overhead or a long-term stability PASS.

## OWNER_UNCHANGED / counters / cleanup

No ADB/device access or lifecycle action in this task. Last saved owner state
12:23:09 UTC: VPN OFF, app ON, ChatDeliveryService ON, gate CLEANED. This is
historical; current phone lifecycle was not freshly measured. Research84 and owner
cache/enrollment/identity/publisher/history/AWG untouched. No forced launcher/chat
start, no helper or gate installed on owner. Ordinary server services retain PIDs.

```text
OWNER_CONNECTS = 0
OWNER_INSTRUMENTATION = 0
OWNER_REFRESH = 0
OWNER_INSTALL = 0
OWNER_TUN = 0
OWNER_TELEMOST_SESSIONS = 0
EXTRA_SYNTHETIC_TELEMOST_SESSIONS = 0
CONTROLLED_GATEWAY_RESTARTS = 1
NATURAL_FATAL_EXITS = 1
AUTOMATIC_RESTARTS = 1
ROLLBACKS = 0
```

**Room-counter scope:** a literal global `TELEMOST_SESSIONS_CREATED_BY_TASK=0`
would be false: the authorized ordinary gateway start necessarily creates **one
shared service seed**. The later automatic restart created one more. These are
counted explicitly (task-controlled seed1 / automatic seed1), not extra owner or
synthetic test rooms. No room was created just to exercise the observer.

Temporary local executable-check copy/synthetic fixture secrets removed after
evidence; validated source/binary/tests/provenance retained. Server observer,
receipts, bounded retention and rollback retained; no cleanup restart.
`ATTEMPT_CONSUMED_BY_THIS_TASK=NO`; prior late physical attempt remains consumedYES.
`READY_FOR_CLEAN_RETRY=NO`. Cold start/whitelist/egress not retested; public release,
APK publication/distribution, Telegram compatibility and real FIELD NOT_RUN.

## Ровно следующая операция

Отдельная **GATEWAY-SIGNAL-READ-CAUSE** remediation/localization task по новой
immutable receipt и точному ReadJSON→SIGNAL_READ коду, до любого behavioral fix
или нового warm-start. Не выполнять её автоматически. Принятый
[двухфазный runbook](../whitelist-warm-start-two-phase-runbook.md) сохранён без
изменений; ACK→fresh gate recheck→CONNECT window применяется только в последующей
отдельно разрешённой задаче. Поздний CONNECT остаётся OUTSIDE_TEST_WINDOW.
