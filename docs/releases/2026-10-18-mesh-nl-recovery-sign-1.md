# MESH-NL-RECOVERY-SIGN-1 — PASS signing only / APPLICATION NOT RUN

18 October 2026; all times UTC. Explicit authorization covers operator review and
offline-root signing of the exact PREP-1 request only. **The signed candidate is
not an installed authority, a restored NL gateway or physical acceptance.**

## RESULT

| Required field | Result / evidence |
|---|---|
| RESULT | **PASS — exact-request signing and independent verification only** |
| REQUEST_ID | `mesh-nl-recovery-prep-20261018-01` |
| INPUT_HASHES_MATCH | PASS before unlock, immediately before signing and after verification; exact hashes below |
| PREDECESSOR_CHECKPOINT_VALIDATION | PASS: installed historical validator, both node checkpoints and unchanged COMMITTED predecessor |
| SEQUENCE_TRANSITION | Signed candidate16→17; active authority remains16 |
| SCOPE_REVOCATIONS_FLOORS_PRESERVED | PASS: exact request included in signed bundle; family/gateway, same issuer key, grant set, CRL27119/two revoked entries and floors preserved |
| VALIDITY_AND_APPLICATION_DEADLINE | CA expires19 October09:33:41; necessary4h bound05:33:41 confirmed, but **grant validation imposes the earlier strict03:33:41 bound**. Reserve one further hour: target before02:33:41 |
| OFFLINE_ROOT_SIGNATURE | PASS: existing root unlocked through protected local vault dialog; unchanged signer returned `SIGNED_OFFLINE` |
| INDEPENDENT_SIGNATURE_VERIFICATION | PASS: separate isolated process, existing `expired_recovery.verify` and normal strict delegation parser, no expiry bypass |
| SIGNED_ARTIFACT_SHA256 | `3f7d0d1e5cd3021da25758a9965bfb8ad1caebb31d4afbe237f47be84de81c2e` |
| PRODUCTION_UNCHANGED | PASS for inspected active credentials/configuration/source/checkpoint/processes; matching pre/post fingerprints, NL failed/MainPID0 |
| APPLICATION_NOT_RUN | TRUE; no bundle sent to RU/NL, no apply/publication/service operation |
| NEXT_APPLICATION_PREREQUISITES | Separate application/outage authorization, fresh CAS/state/time checks, protected transfer and approved strict recovery workflow |

[Sanitized evidence](2026-10-18-mesh-nl-recovery-sign-1-evidence.json);
[PREP-1](2026-10-18-mesh-nl-recovery-prep-1.md);
[lifecycle root cause](2026-10-18-mesh-nl-credential-lifecycle-1.md).

## EXACT_INPUTS_AND_OUTPUT

Local/GitHub main was rechecked as `7656f2c65ea2928b71a928c12ee65a2f47f8ac4f`,
parent `edca5447418141cb44c0706e26d1973d7defd397`. Existing dirty investigation
work was preserved. No commit/push, release or runtime build occurred. Main's
unaccepted all-activated implementation was not substituted for deployed source.

Inputs and signed output:
`state-client-build/mesh-nl-recovery-prep-1/private/`.
Signing/verification journal:
`state-client-build/mesh-nl-recovery-sign-1/private/`.
Directories0700, files0600, local owner UID1000; Git ignore confirmed. Only hashes
and sanitized receipts are documented; no protected request/bundle, device/grant
identifiers, vault metadata or private keys are added to Git.

| Material | SHA256 |
|---|---|
| `recovery-request.json`, unchanged canonical bytes | `a985777611d8b5d2a54ea8f1928b4f7537e3ff7a19ea0506fa98ff8999c3b794` |
| `successor-ca.pem`, unchanged bytes | `8ef49f002afd64f7e92a7f764fdcc19784fddf6c590bf9fc79bfd041aabdc46a` |
| Canonical successor delegation payload | `ee75a86a3387fe914ffc31e494796ce1df6b0fd5fe264c2c1561d16760a9402b` |
| Trusted public root, raw32 bytes | `6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83` |
| `anchor.pub`, base64/newline file | `d0ae60e61af6ac5018428aaad89e362ec0f75d7468633a26c22906356228d281` |
| Same issuer DER SPKI | `1b86d9e01ae940e78efe7e1f29d91cec4aff06efbe92e142ca99222367100d34` |
| **Output `authority-bundle.json`** | **`3f7d0d1e5cd3021da25758a9965bfb8ad1caebb31d4afbe237f47be84de81c2e`** |
| Signer receipt `signing-result.json` | `4bc570139df03f740eb40859418d7d96662ce3a7eb6ebbc65b312c15635cf83b` |
| Safe independent receipt `independent-verification.json` | `ed931add1626c48758b307e699719ffb9052af7ce96644a1d7401ac007952e90` |

Existing recovery envelope: the root signature binds the complete original request
and the normal root-signed successor delegation. No new approval schema, wire
field, root, issuer key, CA certificate or trust mechanism. Output already exists:
**do not sign again or overwrite**; reuse and verify it. Ambiguous future application
requires journal reconciliation, not another signature/request.

## OPERATOR_REVIEW_AND_WORKFLOW

Used section2 of the retained deployed runbook:
`state-client-build/owner-cumulative-client-acceptance-1-resume/review-publication/research/current4h-expired-recovery-20261015/RUNBOOK.md`,
the [vault instructions](../vault-signing.ru.md), and existing accepted
batch-maintenance vault custody. No management-code upgrade, section3 application
or later service-restoration step was executed.

The ordinary-maintenance launcher could not run unchanged: it binds a different
schema/path and lacks `--expired-recovery`. The private task-local parameterization
`state-client-build/mesh-nl-recovery-sign-1/sign_offline.py` reuses the existing
vault loader, unchanged `choose`/`discovery_run` selection functions and memfd→FD
custody. It passes this exact request/output to the **unchanged** retained signer
with `--expired-recovery --confirm-authority-renewal`. Additional checks only
restrict exact hashes/source pins, duplicate output, live-state freshness and time;
no custom signing algorithm or replacement recovery protocol was introduced.

Protected local selection/password dialogs completed. KDBX FD permissions,
memory-only attachment, private inventory/member checks and public-anchor match
use `scripts/signing_key.py`; key is passed only by memfd, closed on exit. Core
dumps disabled; no password in chat/argv/logs, no key file/export to RU/NL, no new
key. Only two metadata-selection functions were loaded from the historical helper;
its Android-labelled selection dialog does **not** mean APK signing code ran.
This is the documented local Linux offline-root workflow, not a claim of physical
air-gapping or protection from a compromised host/root/swap.

| Implementation pin | SHA256 |
|---|---|
| Installed RU API archive | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Installed RU/NL source manifest | `5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145` |
| Retained `sign_authority_offline.py` | `2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6` |
| Retained `expired_recovery.py` | `92fc24346df6b86b0621210e7847a2d17c11a69e8c2ae73bf32609fa2f2ab99e` |
| Vault loader, matching accepted retained copy | `d82ad0bed316d9ec1801605fce4282c4c7b8202b52419406bac72015937075a0` |
| Existing vault metadata helper | `f4f5bfb02f67ef76700ad2dd29163a8eab5a267fdb2045e072c51a18a70896df` |
| Private launcher parameterization | `7b69e82d236642c6566076a2caa9a29617297baf0058b53b0ce818d4c578e6ff` |
| Independent local verifier | `016903569c2d7968a500b6da53fab1fdcd8451286e714015db190687876a0e6c` |

Retained isolated environment uses PREP-1 matching cryptography46.0.7/cffi2.1.1/
pycparser3.0/rns1.5.1/pyserial3.5. API modules are supplied explicitly, not through
ambient PYTHONPATH. Remaining source pins are in the evidence file.

## PREDECESSOR_CHECKPOINT_VALIDATION

Read-only installed checks at09:59:15–16 and10:08:46–47 confirm:

- COMMITTED operation `scheduled-1792291291-d3bbc76b3aa8dc8d`, plan
  `289e59aecffe16a482ef29eb13995393d5b0e37dbe6b678c9a4dfc556052ba4d`.
- Predecessor/snapshot `008cbeb7adec69956b242012f17204d8ee4a242bbeec53089699587b566dd978`.
- Request-bound RU/NL state digest
  `2a44db20325b17132224897652b158c82ab0396f675b8b72f9b8465baa2712f2`.
- Extended active fingerprint, identical to PREP-1 and before/after signing:
  `5e34a50401fef9b1079039cedee9200e881b7860212ee59e4baab759ba792cd4`.
- Existing family/gateway/version/minimum revision1, issuer key/subject/extensions
  and self-signature match. No new identity/entitlement. CRL27119/two revocations,
  pending revocations0; two nonrevoked grants6/8 unchanged. Prospective7/9 is an
  in-memory preview only. Profile minimum CRL27088 must not replace signed floor27119.

After the interruption, another read-only check at10:19:27–29 returned the same
active fingerprint, checkpoint, source/configuration/binary hashes and service
identities. No recovery or service command was retried.

No matching signed result was found in canonical local output locations or retained
bundle/signed JSON envelope search before signing. At10:09:52, direct read-only RU
journal check confirms no `recovery-results/<this-request>.json`: the transaction
is still the prior COMMITTED operation. No newer active successor/checkpoint was
observed. Future apply must repeat CAS validation; these observations are not a lock
on production state throughout the human approval interval.

## VALIDITY_AND_APPLICATION_DEADLINE

| Material | Observed validity / status |
|---|---|
| Existing public root | Pinned raw Ed25519 anchor, not a certificate with an invented expiry |
| Predecessor authority16 / CA | Expired18 October08:57:40; historical signature/bindings valid, not current authority acceptance |
| Predecessor gateway leaf / CRL | Expired18 October06:41:35; historical signatures/identity/revocations checked |
| Nonrevoked grants6/8 | Expired18 October08:57:40; exact set/floors preserved |
| Existing directory | Prior audit: issued18 October05:41:54.637165993, expired06:41:47.650095111; unchanged bytes/hash now, not newly valid |
| Successor CA / signed authority17 |18 October09:33:41→19 October09:33:41, exactly24h; signing does not change dates |
| Recovery request |18 October09:33:46→19 October09:33:46, exactly24h |
| Future leaf/CRL/grants/directory | Not issued/installed here; current-clock and loaded/served validity remain application gates |

Immediate pre-sign checker ran10:03:51.879; output mtime10:03:52.180 is local journal
timing, not a signed timestamp. Independent verification at10:05:00 left84,521s
(23h28m41s) CA validity. After the connection interruption, the existing bundle
was reverified at10:19:14: unchanged hashes/signature, signer not invoked,83,667s
remaining. No duplicate signing or incomplete-write recovery was necessary.

**Refinement of PREP-1:**05:33:41 is the necessary4h parent bound in deployed
`ProductionNode.prepare` (`trust.expires_at >= now + VALIDITY['leaf']`), not a
sufficient execution deadline. `recovery_plan` caps grant expiry at CA expiry;
`prepare_crl`/plan validation invokes existing `validate_grant_plan`, requiring
`plan.issued_at + THRESHOLD['grant'] < successor.expires`, threshold6h. This expired
CRL takes that path. Initial prepare must therefore be **strictly before19 October
03:33:41UTC**. No limit, date or validator was changed.

Isolated probe with actual predecessor grant rows and the unchanged grant-plan
validator:6h+1s accepted;6h exactly and4h rejected as `GRANT_REVISION_OR_VALIDITY`.
This is a validator boundary test, not publication or full recovery acceptance.
Reserve at least one additional operational hour for separate approval/checks and
execution: **target before19 October02:33:41UTC**, preferably much earlier. This
reserve is not a protocol change or a guarantee of availability until that time.
The signing launcher required>7h headroom and<15-minute live-state evidence; both
passed. Stale/insufficient material requires STOP and separate review, not editing
or re-signing this request. The raw24h request expiry does not extend the CA window.

## VERIFICATION_RESULTS

- Actual unsigned request/historical signature/self-signature checks PASS;
  13 purpose/hash/scope/floor/sequence/grant/expiry/key negative cases rejected,
  rerun immediately before signing.
- Existing signer returned `SIGNED_OFFLINE`, stderr empty; one invocation reached
  signing. Existing root/public-anchor match, no output overwrite or re-sign.
- Separate process verified recovery root envelope and normal strict successor
  delegation. Embedded canonical request and successor PEM are byte-identical to
  authorized inputs; sequence/scope/checkpoint/expected-state/floors/time match.
- Four signed-bundle negative cases rejected: bad outer signature, wrong trusted
  root, wrong operation, altered inner authority. Three grant-boundary cases as above.
- First auxiliary verifier attempt stopped because its diagnostic reader mistakenly
  required canonical JSON for a pretty-printed local audit receipt. Only receipt
  parsing changed to ordinary JSON loading; request/bundle protocol parsers stayed
  strict. The **same** signed output passed; no second signing occurred.
- Final input hashes, artifact0600/parent0700 and Git exclusion checked. Evidence
  contains no private payload/vault inventory. No current native/live UI84 or
  physical throughput acceptance is inferred from these offline results.

## PRODUCTION_UNCHANGED_AND_STOP_GATE

Post-sign10:08:46–47: RU HTTP active PID1921548, invocation
`bdf17918da9f4f438363a7bc46e0f467`; NL failed/MainPID0/NRestarts6, invocation
`4f3ce31195364bed961748ae13fa1c00`, no18444 listener. Accepted configured binary
`4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`, profile
`de06a5b0bf468614f33baa61190cb5419874abbde379ed16ec798c8248e760d7`, directory
`50aa786cb751a40c8ef6c7ccfdc60a126f6bcd9432d7f78cb912f1f9fc104ad8` unchanged.

No signed-bundle transfer, authority/grant/leaf/CRL/directory publication, active-link
switch, apply/deployment, timer/admission/security change, service start/restart/
reload/reset-failed, gateway replacement, Android build/sign/install, transport
tuning or commit/push. UI84/native artifacts were not touched; PERF-2 phone evidence
is retained, not presented as a new phone attestation. Normal log activity is not
claimed to have stopped: invariance covers inspected security/config/process state.

## NEXT_APPLICATION_PREREQUISITES

Repeated SIGN-1 authorization was handled idempotently at18 October10:29:27–31UTC:
the existing bundle passed `expired_recovery.verify` and the normal strict
delegation parser again. Both input hashes, bundle and original verification
receipt are unchanged; same16→17 candidate, issuer key, scope/revocations/floors
and checkpoint. CA headroom83,054s (>7h operational gate). No vault access, signer
invocation or duplicate output. Fresh RU/NL readback confirms the same active
fingerprint, COMMITTED predecessor, binary and failed/MainPID0 gateway.

Protected follow-up receipt:
`state-client-build/mesh-nl-recovery-sign-1/private/repeat-request-verification.json`,
SHA256 `7856f0cc4ffa3602882396d35e1babe1bfcd3615d90a084ec23b1da1c0b0705a`.
This is a diagnostic receipt, not a new approval format or application authorization.
RESULT remains **PASS signing only**, PRODUCTION_UNCHANGED / APPLICATION_NOT_RUN.

1. Obtain separate explicit approval for exact-bundle transfer, credential
   application/publication and the runbook's bounded RU/NL maintenance outage and
   service restoration. None is authorized by this signing-only task.
2. Recheck UTC, exact hashes/root signature, current checkpoint/state, eligibility,
   revocations/floors and>6h grant headroom plus reserve. Keep accepted binaries and
   deployed legacy source. Any conflict means STOP; do not relax checks or replace ID.
3. Under that approval, use existing expired-apply lock/CAS/quiescence/staging/
   publication/reconciliation gates, not manual active-file installation. Preserve
   identity/revocations; fresh leaf/CRL and native current-clock checks are required.
4. On ambiguity retain the exact operation/journal, fail closed and use approved
   reconciliation/forward-resume. Expired predecessor credentials are not usable
   rollback; never decrement floors or reset state to make a service start. Signing
   itself needs no production rollback because no active state was changed.
5. Attest the actually loaded accepted gateway, readable credentials, fresh equal
   directory, same UI84/native bytes and authenticated stable reconnect. Only then
   perform the prepared PERF-2 physical baseline, with transport settings unchanged.
6. Arrange acknowledged alerts/operator coverage before the next parent threshold
   and observe subsequent cycles. This signature alone does not repair the recurring
   handoff gap or demonstrate sustainable renewal.

**FINAL_RESULT: PASS signing only. APPLICATION_NOT_RUN.** NL restoration, live UI84
compatibility/reconnect and physical throughput remain unverified/BLOCKED pending
separate authorized recovery. Work stops at this gate.
