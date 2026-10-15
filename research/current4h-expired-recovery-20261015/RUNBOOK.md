# Controlled deployment and expired recovery v1 — NOT EXECUTED

This is the next **separately authorized** operation. Local acceptance is not
environment recovery. Do not sign real material, SSH or start services as part of
the implementation task. Preserve baseline executable SHA256
`21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`
and the already signed cumulative APK. No device operation belongs here.

## 1. Compatible management update

Base: current-policy source map
`107d1c4219e13fdb91283b9e34f01951f95436a30c9b155f57ea427041221a5b`.
New RU/NL management source map:
`5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145`.
The full modules/individual hashes are in `source-manifest.json`; `package.py`
reconstructs the complete 13-module management install set, not just changed files.
The normal wire authority/profile schemas, API archive, receiver archive, privileged
RPC wrapper, unit definitions, keys and fixed SSH command remain unchanged.

1. Reconstruct/verify source and build `management/` with `apply.py` and `package.py`.
   Keep the offline signer and its dependencies on the existing offline signing host;
   **do not copy `sign_authority_offline.py`, test fixtures or root keys to RU/NL**.
2. Read fresh local/remote bounded receipts. An intact last COMMITTED coordinator
   transaction/plan and both protected node archives/`completed.json` are prerequisites.
   Do not invent or import a checkpoint to make an untracked snapshot pass.
   Resolve an existing pending transaction through its original version/contract
   before switching management versions. Never delete ownership markers.
3. Pause the existing `family-connect-credential-renewal.timer` and confirm the
   matching service is not active. Retain original timer/service configuration.
   No restart of unrelated servers/services. Hold the **existing** coordinator
   `renewal-coordinator/operation.lock` and both `renewal-state/operation.lock`
   exclusively/nonblocking during the short code/config switch. If any lock or
   marker belongs to another operation, stop; do not force ownership.
4. Privately preserve old management modules and node/controller configs (not vault,
   product DB or client data). Verify old installed module hashes against the accepted
   map. Prepare config copies, retaining every non-source field:

   ```sh
   python3 configure.py --node "$OLD_NL_NODE_CONFIG" --out "$NEW_PRIVATE_NL_CONFIG"
   python3 configure.py --node "$OLD_RU_NODE_CONFIG" \
     --controller "$OLD_RU_CONTROLLER_CONFIG" --out "$NEW_PRIVATE_RU_CONFIG"
   ```

5. Under those locks, install the 13 allowlisted module files from `management/`
   into the existing `/opt/apps/family_connect/friends-restricted/renewal/`, first
   NL then RU, root-owned mode0600. Stage each same-directory temporary file, fsync,
   rename and fsync the directory (the accepted install's write procedure).
   Switch `node.json` **after** all modules; switch RU `controller.json` with the new
   NL source map before enabling callers. Do not change live/state/database/anchor,
   API archive hashes, SSH custody or approved schedule settings. New `node.py`
   refuses a manifest omitting `expired_recovery.py`; mixed module/config versions
   fail source-identity validation, not permissive fallback.
6. Check all installed bytes/config readback; use existing node `inspect`/fixed
   privileged RPC to verify both advertised source identities. Release short locks
   only when consistent. The old receiver already forwards bounded
   `CREDENTIAL_RENEWAL_RPC` to the same fixed root wrapper and rejects legacy writes
   with `MAINTENANCE_TRANSACTION_REQUIRED`; no receiver upgrade is needed.
   If update is interrupted, keep scheduling paused and finish the same verified
   code/config set before any credential operation. Do not guess a new writer.

This switch changes management code/config source inventories only. It does **not**
itself stop/start the gateway or mutate credentials. Admission quiescence for actual
publication is performed by the existing outage gate in step3 below, which preserves
the pre-outage service states for subsequent controlled restoration.

## 2. Request and explicit offline-root authorization

Use the existing private controller config and Python environment on RU. Set one
lowercase operation ID (16–96 `[a-z0-9-]` characters); retain it through all steps.
`SCOPE_JSON` is a canonical private JSON list of explicitly approved existing device
IDs. Confirm membership from current authoritative DB/device/invite/admission state,
not just an expired snapshot. It must be exactly the remaining unrevoked grant set.
An ineligible unrevoked grant rejects; this flow does not invent/remove entitlements.

```sh
"$PYTHON" -E -s -B "$RENEWAL/runtime_controller.py" --config "$CONTROLLER_CONFIG" \
  --mode expired-request --operation "$OP" --grant-scope "$SCOPE_JSON" \
  --request-output "$PRIVATE_REQUEST"
```

Expect `RECOVERY_REQUESTED`. Credential/service mutations are zero during this step;
the request/proposed public issuer cert are persisted in private coordinator state.
The issuer signs only the same-key proposed CA certificate; that is not sufficient
to make it an active authority. No lock is held during human review/signing.

Transfer the request through the accepted offline custody channel, not public Git
or a diagnostic export. On the offline host, review operation/purpose, predecessor
digest, scope, last committed checkpoint, observed state/floors, grant list, successor
and expiry. Existing authoritative-state hashes are assertions bound into this
approval; apply will recheck them against the actual nodes. Never infer freshness
from an old root signature alone. Use the same pinned anchor and existing root key.

```sh
"$OFFLINE_PYTHON" -E -s -B "$OFFLINE_SOURCE/controller/sign_authority_offline.py" \
  --request "$PRIVATE_REQUEST" --anchor "$EXISTING_PINNED_ANCHOR" \
  --root-key-fd 3 --output "$PRIVATE_BUNDLE" \
  --expired-recovery --confirm-authority-renewal 3<"$EXISTING_OFFLINE_KEY"
```

The offline host must already expose the retained API module to this interpreter,
as in the accepted signer environment. `-E` intentionally does not accept an ambient
PYTHONPATH workaround. A key requiring physical unlock/custody must be unlocked by
its owner using the existing workflow; never transfer the key or password to chat/RU/NL.
The new bundle is root-signed over the complete request plus normal wire delegation.
Both purpose and explicit CLI confirmation are required. Do not use the legacy signer
mode on this schema. Transfer only the signed bundle back through the accepted channel.

## 3. CAS, outage, publication and strict validation

```sh
"$PYTHON" -E -s -B "$RENEWAL/runtime_controller.py" --config "$CONTROLLER_CONFIG" \
  --mode expired-apply --operation "$OP" --authority-bundle "$PRIVATE_BUNDLE" \
  --approve-maintenance-outage
```

This explicitly authorizes interruption of unknown existing restricted sessions;
PID0 alone is not proof of zero sessions. The CLI binds a fresh 900-second outage
approval to current state, independently of the root bundle. Root request approval
expires within one day; successor strict validity/headroom can reject earlier.
No new full-day window is added after signing or draining.

The controller reacquires locks and rechecks saved request/checkpoint, signatures,
actual state hashes/policy, root approval and same operation. Any pre-apply mismatch
rejects before credential publication. Both durable node owners are acquired.
Exact stopped-unit gate covers:

- RU HTTP: `family-connect-friends-http-candidate.service`;
- RU restricted sync timer/service and restricted-directory-sync timer/service;
- NL: `family-connect-restricted-bootstrap.service`.

The current4h coordinator lock excludes concurrent normal and recovery operations.
Do not proceed if some other service/manual writer or alternate RU API is known to
read/write these materials outside this accepted list. This task verifies the declared
unit/forced-receiver contract locally; it has not inspected today's live topology.

After confirmed quiescence: prepare, strict-check normal successor, stage/fsync both
nodes, publish RU files/SQLite and NL profile, strict readback/reconciliation, persist
and replicate commit decision. CRL/revision/sequence never roll back; revoked entries
and issuer/device/gateway keys persist. Equal hashes alone are not distributed
atomicity: safety depends on the closed admission interval and verified commit gates.

Only then the existing start-intent mechanism starts the **unchanged baseline** on NL
(if previously active/failed), waits for a different currently valid directory, publishes
it to RU, and restores the prior RU HTTP/directory timer states. Do not run an extra
manual restart/reset when this succeeds. Keep legacy sync writers disabled as required
by the accepted contract. Verify the served TLS chain/seed/directory binding and
loaded baseline executable through the existing collectors in the authorized operation;
local Family/TLS tests are not that live proof. Do not restore the old expired directory.

## 4. Partial outcome and resume

`PUBLICATION_INCOMPLETE` preserves bounded `first_cause`, durable cursor, owner/staged
files and any committed state. Nodes owned by this operation are fenced; do not
delete state, issue another successor, open admission or roll back floors.
`CLEANUP_REQUIRED` keeps the durable CLEANING marker and completed valid publication;
cleanup can resume without replaying the issuance or start.

```sh
"$PYTHON" -E -s -B "$RENEWAL/runtime_controller.py" --config "$CONTROLLER_CONFIG" \
  --mode expired-resume --operation "$OP" --authority-bundle "$PRIVATE_BUNDLE" \
  --approve-maintenance-outage
```

Use the identical bundle. Ordinary `recover`, `operator` and `scheduled` must not
roll back/auto-resume this recovery. Before each remaining promotion, recheck policy,
DB and file CAS; the successor is validated at actual current time, including resume.
No old-time active-validation bypass is used. An expired/bad successor, lost protected
state or a changed entitlement remains fail-closed and needs a separate operator decision;
there is no automatic re-signing or floor reset. A failed gateway start is recorded once;
resume does not become restart-until-green. Report the failure without bypassing start-intent.

Completed same-ID/same-bundle calls return an idempotent receipt/readback, not another
issuance. Same ID with different content rejects. An idempotent COMMITTED receipt is
historical completion, not a promise that credentials remain valid now.

## 5. Return to current4h and later client acceptance

After COMMITTED and protected cleanup, run the existing `evaluate` mode and retain
its receipt. Restore the previously accepted credential-renewal timer to its original
enabled/active state; do not run a competing writer for reassurance or replace its unit.
Normal scheduled maintenance has only existing leaf/CRL authority; operator thresholds
for authority/grants remain in force. Record actual validity UTC bounds, next timer run
and next operator deadline. A timer being active is not proof of a successful renewal.

After separately verified live recovery, resume owner acceptance with the **already
signed** cumulative APK, fresh short environment/owner checks, then authorized install
and remaining CONNECTs. This runbook does not authorize those actions and does not
close historical production FAIL, causal binding or device acceptance.
