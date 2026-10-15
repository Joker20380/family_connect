# RESTRICTED-BASELINE-ENVIRONMENT-RECOVERY-1

**RESULT: BLOCKED — accepted operator entrypoints attempted, no credential
publication or gateway start.** This is not another conclusion based only on
MAINTENANCE_REQUIRED. The deployed, source-verified current-policy operator path
rejects the expired predecessor before it can produce an offline authority request
or enter its maintenance transaction. No applicable accepted expired-authority
recovery contract integrated with current4h was found in the retained procedures.
No expiry check, clock, signer, controller or publication policy was modified.

Input review: `c2755481d6e6e6d4d68a460b46b2f77909cd0d68` and the
[pre-install environment stop](2026-10-15-owner-cumulative-client-acceptance-1.md).
The phone was not accessed. This task did not spend either device CONNECT attempt.

## Accepted workflow and identities

Used the retained `ops-credential-renewal-controller-1-current-policy` acceptance
capsule, its MAINTENANCE-CONTRACT, OFFLINE-SIGNING-HANDOFF, VALIDITY-POLICY and
actual deployed entrypoints, not root main or experimental CRL writer work:

- Accepted isolated source commit: `9423d45ee013b349f342a81be502757b17b3fbf2`.
- Sealed source archive SHA256:
  `5fa24f5383e3f64c6ce7368e807972a6a4e4e9d832268feabefb9fea396c0e00`.
- Canonical runtime source-map SHA256, verified against all 12 installed modules
  on both nodes: `107d1c4219e13fdb91283b9e34f01951f95436a30c9b155f57ea427041221a5b`.
- `runtime_controller.py` SHA256:
  `2315a4bf795d3d1f4955ff755891f8d1c0ee1cb422b427820895864bb323c071`.
- `production_node.py` SHA256:
  `7a06b1e93645720e864f5eef7123f9884f1dc12d4d49873ef392934c487b4a2d`.
- Offline signer bytes matched the sealed accepted archive; signer was **not run**.
  No root private key was read or transferred in this task.

RU entrypoints, under `/opt/apps/family_connect/friends-restricted/renewal/`:
`node.py --config node.json` with the bounded `authority-request` RPC, followed
by `runtime_controller.py --config controller.json --mode operator
--approve-maintenance-outage --operation <operation>`.
Actual execution used absolute paths and the existing friends-access Python venv.

One logical operation ID: `restricted-baseline-recovery-20261015-1350`.
The accepted transaction uses coordinator locking, fresh hash/revision CAS and
per-node ownership; no competing writer was introduced. Before and after the calls,
both node owner markers were absent and the prior scheduled transaction remained
COMMITTED. The authority-request acquired the existing node lock; the operator
call failed during its initial read, before coordinator acquisition/quiescence.

Here “authority” is the one-day root-signed delegation envelope plus a delegated
CA certificate with the existing issuer key, not a replacement root trust anchor.
Existing issuer-bound grants are database authorization records. Policy remains
one day for authority/grants and four hours for gateway leaf/CRL, with six-hour
operator and 90-minute leaf/CRL renewal thresholds. No policy was extended.

## Fresh state and preserved primary failure

Initial source/state checks at 13:45 UTC found the baseline unit still failed,
PID 0, NRestarts 6; RU restricted API remained running. Current4h timer was active,
but its service was failed. The legacy writer remained disabled/inactive.
The last durable credential transaction was a scheduled COMMITTED operation at
04:47 UTC, not an operation belonging to this task.

The final retained gateway invocation is
`c332f43e5ced4aa58258e4d3877434fe`.
Its application fatal receipt at **11:08:07.758734711 UTC** records:

```text
last_confirmed_stage=PROFILE
first_stage=PROFILE
first_cause=CREDENTIALS_REJECTED
safe_error_class=typed
exit_path=returned_error
fatal=true
credential_limiting_expiry=2026-10-15T08:32:34Z
credential_headroom_seconds=-9333
```

The matching systemd receipt at **11:08:07.835188 UTC** has
`property_invocation_match=true`, `service_result=exit-code`, `exit_status=1`.
Thus **LAST_GATEWAY_EXIT_CAUSE=PROFILE / CREDENTIALS_REJECTED** is recorded, not
guessed from current expiry. The exact individual credential rejection mechanism
is not further resolved by that bounded cause. Earlier historical owner C1/I1
causality is not investigated or reclassified.

**CURRENT_ADMISSION_BLOCKERS** are separately observed expired authority, both
existing non-revoked grants, leaf, CRL and directory, plus no running listener.
Application/systemd fatal files were preserved before any potential reset/start.
Two initial unit-journal reads timed out; these failures were retained. A narrower
direct-field query subsequently returned the current controller's actual receipts.

## Actual operator attempts and exact blocking contract

| Step, one logical operation | Observed result |
|---|---|
| Accepted `authority-request` RPC, once | Exit 1; `REJECTED`, payload cause `UNKNOWN` |
| Accepted `--mode operator --approve-maintenance-outage`, once | Exit 1; `FAIL_CLOSED`, cause `SNAPSHOT_VALIDATION_FAILED`, automatic_retry=false |
| Readback | No authority request file; no new owner marker or transaction; previous COMMITTED record unchanged |
| Offline signature / grants / leaf / CRL / publication / start | NOT_RUN; prerequisite rejected |

The original RPC `UNKNOWN` is retained verbatim, not relabeled. A separate
read-only call of the **deployed exact delegation parser**, with the current
envelope, pinned anchor and current time, rejected at `restricted.py:140`:

```python
require(value['issued_at'] <= now < value['expires_at'])
```

The envelope signature verifies against the existing pinned public anchor.
Authority sequence is 13; expiry is 11:01:34 UTC. This establishes a present
time-validity blocker independently of the generic RPC error.

Relevant existing source boundaries:

- `ProductionNode.authority_request()` validates the **previous** delegation at
  `now` before loading the issuer key or constructing a successor request.
- `runtime_controller.main()` operator mode first calls `controller.read()`;
  `Validator.validate()` parses the previous authority at `now`, requires a
  current CRL and valid non-revoked grants. `expired_leaf_predecessor=True`
  permits only an expired leaf, not expired authority/CRL/grants.
- The offline handoff verifier also parses the previous authority at current time.
  Supplying a handcrafted signed bundle would not be an accepted workaround.

The retained October 6 expired-parent operator precedent was also checked. It
authenticates historical provenance and uses an independent offline root signature,
but its executable is pinned to issuer 5→6, old HTTP/archive identities and the
old sync timer, before current4h coordination. The later bridge helper assumes a
still-valid authority and does not renew it. Neither is an applicable, already
accepted current4h expired-parent maintenance/resume entrypoint. They were not run
or adapted into a new writer.

**Missing accepted contract:** operator recovery of an already expired authority,
CRL and grants, with independently authenticated historical provenance/offline
successor authorization, under the installed current4h lock/CAS/publication gates.
Continuing would require a separately accepted recovery path, not another retry of
the same operator command, a new key, or bypassing current-time validation.

## Final state, invariants and validity limits

Final readback completed **2026-10-15 13:54:08 UTC**. Before/after authority, leaf,
CRL, grants, CRL database sequence and each node's directory hashes are unchanged.
Gateway unit/drop-in configuration hashes match the initial snapshot. Minimum
revision remains 1, CRL sequence 27095, grant revisions 3 and 5, revoked grants 0;
revoked-set hash is unchanged. No revoked authorization was restored or floor lowered.

| Boundary | Final observation / absolute UTC |
|---|---|
| Authority and both grants valid until | 2026-10-15 11:01:34 — expired |
| Leaf valid until | 2026-10-15 08:47:36 — expired |
| CRL nextUpdate | 2026-10-15 08:32:34 — expired |
| RU and NL directory valid until | 2026-10-15 11:05:36.386432969 — expired |
| Process lifetime boundary | NOT_APPLICABLE: no live process; no fresh runtime window |
| Next current4h run at final check | Approximately 2026-10-15 14:04:06.841 UTC, scheduled, not a promised renewal |
| Necessary operator maintenance threshold | 2026-10-15 05:01:34 UTC — already missed |
| Earliest material boundary for device acceptance | 2026-10-15 08:32:34 UTC; no remaining usable window |
| DEVICE_WINDOW_READY_AT_CHECK | NO; cannot cover the existing 18-minute sequence or preparation |

RU and NL directory hashes differ: retained issue times are 07:05:42.810665114 and
10:05:45.455790517 UTC respectively, with the same expired bound. Neither was copied
back or declared a usable current publication. No runtime/directory binding PASS
or distributed atomicity claim is made.

`GATEWAY_LOADED_SHA256=NOT_APPLICABLE_NO_PROCESS`.
Configured baseline on disk remains
`21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
PID remains 0, invocation unchanged, listener absent, acceptance flag absent.
`SERVED_CHAIN=NOT_TESTED_NO_LISTENER`; `SEED_READY=NOT_READY`.
The post-success 120-second stability observation was not started because there
was no successful start. No Android TUN/DNS/HTTPS inference is made.

Current4h's actual scheduled 13:49:08 UTC receipt is `FAIL_CLOSED /
SNAPSHOT_VALIDATION_FAILED`, exit 1; the 13:34 receipt has the same result.
One natural scheduled evaluation was observed during this task. The active
15-minute timer and existing leaf/CRL policy remain installed, but renewal is
**not operationally recovered**. Daily authority/grant work is outside its
unattended scope. No new alerting/timer or speculative maintenance date was added.

## Actions, custody and continuation

- Logical recovery operations 1; authority-request calls 1; operator calls 1.
- Read-only SSH executions 12 plus the two operator-entry SSH calls; two initial
  journal timeouts are retained. No blind retry of a changing operation.
- Authority/grant/leaf/CRL publications 0; offline signing 0; gateway start,
  reset-failed, reload/restart and observed new automatic gateway starts 0.
- Gateway executable/config changes 0; product patches/rebuilds 0; new PKI/key,
  trust/TTL/clock changes 0; provider sessions initiated by this task 0.
- ADB, install, CONNECT/reconnect/export, re-enrollment and faults/triggers all 0.
  Existing unrelated/background application activity is NOT_MEASURED.
- Signed client hash verified unchanged:
  `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513`.
  No rebuild, resigning or APK publication; phone not accessed.

Private receipts, bounded raw fatal/controller observations and checksums remain in
`/tmp/fc-restricted-baseline-environment-recovery-1/`; this local path is not public
evidence. Only safe documentation is published. Original dirty checkout, frozen
artifacts, main and workflows are preserved. No new server helper, staging bundle,
pending transaction or temporary service was left behind. Existing timers retain
their prior configuration; restricted gateway remains failed/closed, not restored.

Once the missing **accepted** recovery path has restored the environment, resume
OWNER-CUMULATIVE-CLIENT-ACCEPTANCE-1 at fresh short environment/owner checks, then
the still-unperformed compatible install and bounded device stages using the
already signed APK. Rebuilding, resigning and repeating the full offline audit
are unnecessary. Do not install or CONNECT automatically from this task.

DEVICE_ACCEPTANCE=NOT_RUN; PRODUCTION_ACCEPTANCE=FAIL;
HISTORICAL_CAUSAL_BINDING=NOT_PROVEN remain unchanged.
