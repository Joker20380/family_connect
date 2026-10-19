# MESH-NL-RECOVERY-PREP-1 — PASS, preparation only

Follow-up: [SIGN-1](2026-10-18-mesh-nl-recovery-sign-1.md) subsequently signed this
exact request under separate authorization, without applying it. It also verifies
that the4h parent condition below is necessary but insufficient: existing grant-plan
validation requires>6h, so initial prepare must be before19 October03:33:41UTC,
with an additional operational reserve. The historical preparation result follows.

18 October 2026, UTC. Explicit owner authorization permits the existing
expired-predecessor **request preparation**, including same-key successor-CA
issuance on RU. It does not authorize offline-root signing, active credential
installation/publication, admission changes, gateway start/reset or deployment.
[Machine-readable evidence](2026-10-18-mesh-nl-recovery-prep-1-evidence.json).

## AUTHORIZATION_AND_STOP_GATE

**STOP GATE reached and respected.** A private, unsigned recovery request and its
successor CA are prepared. The CA has its normal issuer self-signature, generated
on RU with the existing issuer key; this is explicitly authorized preparation,
**not an offline-root signature or a newly trusted authority**. No root-key access
or vault interaction occurred. No current credentials, identities, grants,
revocations, floors, admission policies, transport settings or binaries changed.

NL remains failed/MainPID0/NRestarts6, no18444 listener. RU HTTP stays active with
the same PID/invocation. No service stop/start/reset or timer changes were made.
The scheduled controller continues its prior fail-closed behavior. Performance
testing remains blocked until separately authorized legitimate recovery.
Final independent readback at09:41:26–09:41:31UTC reconfirmed the same request hash,
unchanged active-state fingerprints and unchanged service identities.

## EXACT_BASELINE

Local HEAD and fresh GitHub main both
`7656f2c65ea2928b71a928c12ee65a2f47f8ac4f`; source parent
`edca5447418141cb44c0706e26d1973d7defd397`. Prior dirty work is preserved. No build,
checkout, commit, push, release or CI-triggering change was made. Latest recorded
release/CI results remain those in [PERF-2](2026-10-18-mesh-perf-2.md): source CI
is not gateway/UI84 acceptance; main's all-activated candidate is not deployed.

Read-only09:33 preflight used the actual deployed legacy controller, not main.
Every copied source pin and the RU/NL source manifests matched the previous
[lifecycle audit](2026-10-18-mesh-nl-credential-lifecycle-1.md). The **full installed
historical validator** verified root delegation, issuer, leaf, CRL and identity
bindings. Both nodes' archived checkpoint manifests/reconciliations matched their
live generations. Gateway private-key/public-leaf correspondence was checked on
NL by the existing method; no gateway private key was transferred or printed.

Authority16/grants expired08:57:40; leaf/CRL expired06:41:35. Current CRL27119 has
two revoked entries; pending revocations0. Existing nonrevoked grant count2,
revisions6/8; no current grant was renewed. Coordinator checkpoint remains
`scheduled-1792291291-d3bbc76b3aa8dc8d`, COMMITTED, plan SHA256
`289e59aecffe16a482ef29eb13995393d5b0e37dbe6b678c9a4dfc556052ba4d`.

## PREPARATION_RESULT

Operation: **`mesh-nl-recovery-prep-20261018-01`**.

Only the installed `runtime_controller.py --mode expired-request` was invoked,
with its current controller config, this fixed operation ID, a protected grant-scope
file derived from the exact existing nonrevoked set, and protected request output.
No `operator`, `expired-apply`, `expired-resume`, `recover`, signer or publication
command was invoked. An ambiguous result would require readback, not a new operation.

The controller acquired its existing coordinator/RU advisory locks, validated the
committed predecessor and both current snapshots, generated same-key successor CA,
validated the proposed grant cutover against an **in-memory SQLite copy**, checked
that live snapshots were unchanged, and durably stored the canonical request.
Its result was `RECOVERY_REQUESTED`; independent readback returned identical bytes.
There is no new leaf, CRL, active grant generation, signed delegation or directory.

| Time / property | Exact value |
|---|---|
| Request created | 2026-10-18 **09:33:46 UTC** |
| Request expires | 2026-10-19 **09:33:46 UTC** |
| Proposed CA validity | 2026-10-18 **09:33:41** →2026-10-19 **09:33:41 UTC**, exactly24h |
| Proposed authority sequence |16→17; existing family/gateway/version/minimum revision unchanged |
| Next6h parent-maintenance threshold, if used | 2026-10-19 **03:33:41 UTC**; arrange coverage before this, not after |
| Latest theoretical initial prepare time | 2026-10-19 **05:33:41 UTC**, because installed `ProductionNode.prepare` requires at least4h parent headroom; practical deadline is earlier with safety margin |
| Predicted grant cutover |6→7 and8→9 only in memory; existing nonrevoked set unchanged; **not applied** |
| Live floors | Authority16, signed CRL27119, minimum revision1; profile minimum CRL27088 unchanged, not a substitute for the current signed floor |

**Do not interpret the request's24h expiry as a24h recovery-execution window.**
The CA starts at preparation, not future signing. Clock skew, validation, operator
review, four-hour child headroom and transaction completion shorten the usable
window. Do not edit dates or overwrite this request to extend it. A stale or
insufficient-headroom request needs a separately reviewed new request, not replay.

### Artifact custody

Canonical RU request:
`/opt/apps/family_connect/friends-restricted/renewal-coordinator/recovery-requests/mesh-nl-recovery-prep-20261018-01.json`.

RU preparation directory:
`/opt/apps/family_connect/friends-restricted/renewal-coordinator/recovery-prep/mesh-nl-recovery-prep-20261018-01/`.
It contains `grant-scope.json`, `before.json`, `recovery-request.json`,
`controller-receipt.json`, `validation-receipt.json`. Directory0700; all inspected
files0600, operated by the existing root-only workflow. Advisory lock files belong
to the existing workflow; no transaction owner/quiesce/publication was acquired.

Local protected copy and operator bundle:
`state-client-build/mesh-nl-recovery-prep-1/private/`:
`recovery-request.json`, `successor-ca.pem`, public `anchor.pub`, private receipts,
`package-inventory.json`, and `offline/` containing pinned deployed verification
modules, the retained approved signer, matching API archive and dependency lock.
This tree is Git-ignored; request/grant scope and live-snapshot material must stay
private. Only sanitized results/hashes appear in this report and its evidence.
The inventory is unsigned bookkeeping, not authority to sign or deploy anything.

## EXACT_SHA256

| Material / definition | SHA256 |
|---|---|
| Canonical recovery-request bytes, RU and local identical | `a985777611d8b5d2a54ea8f1928b4f7537e3ff7a19ea0506fa98ff8999c3b794` |
| Successor CA PEM bytes | `8ef49f002afd64f7e92a7f764fdcc19784fddf6c590bf9fc79bfd041aabdc46a` |
| Canonical successor payload, not signed | `ee75a86a3387fe914ffc31e494796ce1df6b0fd5fe264c2c1561d16760a9402b` |
| Canonical signed historical predecessor snapshot | `008cbeb7adec69956b242012f17204d8ee4a242bbeec53089699587b566dd978` |
| Bound expected RU/NL state, canonical JSON | `2a44db20325b17132224897652b158c82ab0396f675b8b72f9b8465baa2712f2` |
| Extended active-state fingerprint, before/after unchanged | `5e34a50401fef9b1079039cedee9200e881b7860212ee59e4baab759ba792cd4` |
| Existing public anchor, raw32-byte key | `6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83` |
| Issuer public key, DER SPKI, old/new equal | `1b86d9e01ae940e78efe7e1f29d91cec4aff06efbe92e142ca99222367100d34` |
| Local package inventory bytes | `abb6bf11fc1ba6106727e387a8771f8c1254d9033af6d318fa7ddac36208da58` |
| Deployed RU/NL renewal source manifest | `5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145` |
| Configured accepted gateway, unchanged | `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |
| Matching RU API archive / local offline copy | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Retained offline signer, copied but **not executed** | `2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6` |
| Offline dependency lock | `d6870c56a9b8c435973aee3a92331fb336b0f596ba3b110c0307a1757a7c5bbe` |

Raw anchor hash differs from the base64 text file hash; neither is a private-key
hash. Exact individual module pins are retained in the evidence and the checker.
The active fingerprint includes controller/node config, selected live material,
logical DB snapshot, both nodes' current state/checkpoint and RU HTTP identity;
NL binary/profile/directory/config/service identity are also compared separately.
This is bounded before/after attestation, not a claim to monitor every host file.

## VALIDATION_RESULTS

| Verification | Result / boundary |
|---|---|
| Full deployed historical/checkpoint checks on RU/NL | PASS, no expired credential treated as currently valid |
| Deployed `request_check` on exact request | PASS on RU and independently in isolated local environment |
| Same issuer key, subject/issuer, CA extensions, bounded validity | PASS, verified self-signature and exact sequence+1; no new identity/key |
| Grant entitlement / scope / revision preview | PASS with existing `recovery_plan` and memory-only DB; no DB writes |
| Live material and services before/after | PASS, fingerprints unchanged; RU HTTP same invocation; NL stays stopped |
| Local real-cryptography negative cases | **13 PASS**: tampered purpose, predecessor digest/signature, scope, CRL floor, authority sequence, grant/update scope, expired request, extended validity, old-CA substitution, wrong root, expired predecessor as live authority all rejected |
| Request integrity after tests | PASS, same canonical bytes/hash; mutations only on in-memory test copies |
| Offline-root signature / accepted signed successor | **NOT PERFORMED / NOT AVAILABLE**, expressly outside scope |
| New leaf/CRL, full native delivery and physical reconnect | **NOT TESTED**, requires later authorized signing/issuance/apply stages |

Unlike the previous mocked decision probe, this check uses the actual predecessor
signatures, successor certificate and pinned deployed validation code. It does not
create credentials or emulate a root signature. Initial local system Python lacked
RNS; an isolated local `verify-venv` was created with the **exact observed RU
dependency versions**: cryptography46.0.7, cffi2.1.1, pycparser3.0, rns1.5.1,
pyserial3.5. No system/server packages changed. No vault environment was accessed.

Reproducible, read-only request validation, from repository root:

```sh
state-client-build/mesh-nl-recovery-prep-1/private/verify-venv/bin/python -I -B \
  tests/fixtures/mesh_expired_request_check.py \
  --request state-client-build/mesh-nl-recovery-prep-1/private/recovery-request.json \
  --offline-dir state-client-build/mesh-nl-recovery-prep-1/private/offline \
  --expected-sha256 a985777611d8b5d2a54ea8f1928b4f7537e3ff7a19ea0506fa98ff8999c3b794 \
  --expected-operation mesh-nl-recovery-prep-20261018-01 \
  --expected-anchor-sha256 6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83 \
  --summary-output state-client-build/mesh-nl-recovery-prep-1/private/offline-validation.json
```

This command rechecks the actual current clock: an expired request later fails
closed, correctly. It writes only the local sanitized validation receipt. It never
imports the production controller into a running service or invokes the signer.

## UI84_AND_GATEWAY_COMPATIBILITY

**Structural compatibility verified; end-to-end acceptance pending.** Existing
issuer key and all X.509 extensions/names are unchanged; authority payload schema
and24h duration match the installed legacy policy. Sequence17 is a monotonic
successor, not a new wire format. Retained UI84
`carrier/wholedevice/provisioning.go:119` verifies the root signature on the issuer
envelope, parses this CA shape, validates client identity, CRL/time/floors and
directory. `carrier/familysession/session.go:47` on the accepted pair enforces the
CA self-signature, keypair, CRL signature/number/time and certificate checks. No
source or binary change is required by this proposed CA structure.

An unsigned successor payload cannot satisfy UI84's root-signature requirement;
the expired old CRL/leaf cannot be used with the new CA to manufacture readiness.
Full native validation needs the subsequently authorized signed delegation and
new leaf/CRL, followed by real same-identity readiness refresh/reconnect. No Android
activity occurred here. Preserve accepted UI84 APK
`697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f` and restricted
native `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`, attested
in PERF-2, not freshly reinstalled or measured in this task.

## OFFLINE_ROOT_HANDOFF

The next operator must review **this exact operation and request SHA256**, existing
root fingerprint, same-key successor, scopes/floors, current clocks and remaining
headroom. Use the existing local vault GUI and memory-only key descriptor custody
procedure; never provide a key/password in chat, copy the root to a server, or use
CI. The signer is already packaged with matching public dependencies that were
missing from the old ordinary-maintenance directory.

Signing requires **new explicit authorization**, then the existing signer with
`--expired-recovery` and `--confirm-authority-renewal`, the reviewed request and
anchor, a memory-only `--root-key-fd`, and a new protected bundle output. The older
batch-maintenance wrapper hardcodes an ordinary request/flags and different
deployment identity: **do not run it unchanged**. No executable signing wrapper
or automatic signing action was added by this task.

After authorized signing, independently verify the bundle's root signature,
purpose, operation, predecessor/snapshot bindings and current validity. Do not
consider this step installation approval. Apply requires another explicit grant
for the bounded RU/NL maintenance, issuance/publication of new leaf/CRL/grants,
guarded file ownership/readability and authorized gateway/start-limit recovery.
Re-read live state first; do not force an old snapshot through a changed revocation,
grant, identity, floor, checkpoint or policy state.

## RISKS_AND_NEXT_PERMISSIONS

1. **Time/headroom:** the24h CA clock is already running. Schedule signing/recovery
   soon; retain the next03:33:41 operator deadline if this candidate is used. Never
   extend TTL or change the clock to salvage stale material.
2. **Concurrent state:** any relevant admission, grant, revocation, identity or
   checkpoint change invalidates the approval snapshot. Stop and reconcile; do not
   override CAS/floors or silently substitute a freshly generated CA under this ID.
3. **Privacy/custody:** request contains device references and grant scope although
   it has no private keys. Keep0700/0600 and out of Git/CI/public attachments. Do not
   treat public hashes or this report as root authorization.
4. **Publication/recovery:** future apply can interrupt RU/NL readers. Obtain
   explicit maintenance permission and preserve current binary/profile contract.
   Stale systemd start limit is a later operational consequence, not solved here.
   Unknown post-commit outcomes require bound forward-resume/readback, not expired
   credential rollback or a new operation ID.
5. **Sustainability:** request preparation does not fix tomorrow's operator gap.
   Owner coverage and acknowledged external alerts remain required before the
   six-hour authority threshold; current notifications are local-only. No alert
   policy or schedule was changed in this task.

No production rollback is required for preparation: active state was not changed.
If this candidate is abandoned, leave it untrusted/unapplied; retirement/removal of
private request records is a separately reviewed custody action, not automatic
deletion of operation history. No active trust chain should ever be rolled back to
the already expired predecessor to make service startup appear successful.

## FINAL_RESULT

**PASS for MESH-NL-RECOVERY-PREP-1 only.** The authorized request and same-key
successor-CA were prepared through the installed workflow, exact bytes read back,
historical/current-snapshot and unsigned-request checks passed,13 negative cases
rejected, and active production state remained unchanged.

**STOP before offline-root signing or any active-state mutation.** Required next
permission is the offline-root review/signing ceremony for the exact request hash
above. Credential installation, service recovery and physical UI84 performance
testing remain separately gated and have not passed.
