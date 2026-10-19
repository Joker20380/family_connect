# MESH-NL-RECOVERY-APPLY-1 — PARTIAL / credentials committed, NL READY

18 October 2026; times UTC unless explicitly marked MSK. Explicit APPLY-1
authorization supersedes the earlier signing-only STOP gate for this exact bundle.
No software deployment, new signature, policy change or performance optimization.
[Sanitized evidence](2026-10-18-mesh-nl-recovery-apply-1-evidence.json).
Evidence-file SHA256:
`2d7fe7d40ef2e8f10d3d94db2f89a93f3a96b4d2310ed1076948024033b2c074`.

## FINAL_RESULT

| Status | Result and evidence |
|---|---|
| RECOVERY_APPLICATION | **PASS** — exact signed bundle, existing workflow COMMITTED; both node archives CLEANED; independent installed-transition validation PASS |
| NL_GATEWAY_READINESS | **PASS — bounded server readiness** — accepted loaded executable, verified served TLS, seed READY, equal fresh RU/NL directory; same PID/invocation and zero restarts through11:19:53 |
| UI84_COMPATIBILITY | **NOT_RUN for MESH/DNS/HTTPS** — installed APK unchanged; fresh admitted-device UI84 import READY ACKs observed, but no physical VPN connection or traffic acceptance |
| RENEWAL_READINESS | **PASS for current validation/evaluation and scheduled-service readiness**; next actual credential rotation **NOT_OBSERVED**, not proof of indefinitely autonomous lifecycle |
| PERFORMANCE_BASELINE | **NOT_RUN** — no throughput/latency benchmark or optimization claim |
| FINAL_RESULT | **PARTIAL** — server recovery established; physical client acceptance remains outstanding |

## EXACT_BASELINE_AND_AUTHORIZATION

Local HEAD remains `7656f2c65ea2928b71a928c12ee65a2f47f8ac4f` (parent/source
checkpoint `edca5447418141cb44c0706e26d1973d7defd397`). Existing dirty documentation
and performance fixtures preserved. Main is not used to reconstruct UI84 or replace
deployed management. No build, signing, installation, commit, push or release.

Read STATUS/PLAN, SIGN-1, PREP-1, credential lifecycle and PERF-2 reports, retained
`current4h-expired-recovery-20261015/RUNBOOK.md`, installed renewal implementations
and `deploy/friends/restricted/GATEWAY_RENEWAL.md`. The retained runbook's historical
management-upgrade and old binary pin were **not replayed**: installed source map
`5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145` already includes
expired recovery. Current unit, paths, service account, configuration and binary
were inspected rather than copied from historical commands.

Request/operation: `mesh-nl-recovery-prep-20261018-01`.

| Authorized input | SHA256, rechecked before transfer/apply |
|---|---|
| Recovery request | `a985777611d8b5d2a54ea8f1928b4f7537e3ff7a19ea0506fa98ff8999c3b794` |
| Successor CA PEM | `8ef49f002afd64f7e92a7f764fdcc19784fddf6c590bf9fc79bfd041aabdc46a` |
| Signed bundle | `3f7d0d1e5cd3021da25758a9965bfb8ad1caebb31d4afbe237f47be84de81c2e` |
| Authorized prior verification receipt | `7856f0cc4ffa3602882396d35e1babe1bfcd3615d90a084ec23b1da1c0b0705a` |

Preflight10:43–10:47 verified the existing offline-root signature with the trusted
public anchor and pinned deployed `expired_recovery.verify`, not hashes alone.
Exact request, same issuer key, Family/gateway scope, grants, revocations and floors
match the authorized predecessor. Current RU/NL source/configuration was pinned.
NL was failed/MainPID0, no18444 listener or replacing MESH process. No successor
or partial conflicting transaction was present.

Previous COMMITTED checkpoint:

- Operation `scheduled-1792291291-d3bbc76b3aa8dc8d`.
- Plan `289e59aecffe16a482ef29eb13995393d5b0e37dbe6b678c9a4dfc556052ba4d`.
- Snapshot `008cbeb7adec69956b242012f17204d8ee4a242bbeec53089699587b566dd978`.
- Expected-state digest `2a44db20325b17132224897652b158c82ab0396f675b8b72f9b8465baa2712f2`.

Current-clock verification preserved ordinary successor validation; expired
predecessor was handled only by the dedicated recovery verifier. CA validity is
18 October09:33:41→19 October09:33:41. The original grant-plan bound is strictly
before19 October03:33:41; APPLY-1 operational bound before02:33:41. Application
occurred18 October10:49, well inside both bounds. Signing did not extend validity.

## RECOVERY_APPLICATION

Protected SSH transfer rehashed the exact bundle and independently verified its
signature/request binding on RU before protected atomic staging. Existing
coordinator/node locks and barriers serialized writers. Only the existing renewal
timer was temporarily paused, retaining its original enabled/active state. The
existing installed controller was called **once** with `--mode expired-apply`, this
operation ID/bundle and the authorized maintenance-outage flag. No invented apply
format, standalone credential rewrite, signer or key generation was used.

The controller performed normal staging, strict validation, credential issuance,
publication/reconciliation, single NL start-intent, fresh directory publication,
RU reader/directory-sync restoration and cleanup. Exit0, state **COMMITTED**,
mode expired, cursor9, commit_decided=true, first_cause=null. No blind retry,
manual start/restart or reset-failed. Both protected node ledgers say CLEANED;
all archive-manifest hashes verify; no owner/pending-authority marker remains.
The legacy full restricted-sync timer remains disabled/inactive.

| Output / receipt | SHA256 |
|---|---|
| Apply result, durable RU receipt | `153e8ad5372aa901786128b65e06223101a068ca7383b79d1d3c8965ad989ea9` |
| Current transaction | `8d01c9faa83cb9fee65fd2ef255c857ae6e520f854bc5b48de4366174eb9f5eb` |
| Current plan / checkpoint | `4ed8dd3c86f5dd2c6c1124dadf175a6269dabc390561d85b22519848049a14cf` |
| Current canonical snapshot | `1a0ef9193711f23b8a39b5a62e1a7e5d44b801fd00aad8f18caac67354c80a3e` |
| Installed signed issuer.json | `172ee21c9a02cd6f41a58700b684bf8d423baba8fd5c23e832503a7e76ec1042` |
| Installed CRL PEM bytes | `c79c08fbe1e4fe4df734ed5a6aa09a3acb66d13f73ffb64bec80852dd3124a6d` |
| CRL DER | `da02efb7cfc6f50ab512a2e4bd8b0a29ae312d5b9d6ff4e8f112d0cbf7aa560c` |
| Installed protected gateway profile | `64870fac58ec25d593837f0cfe7ecc6b2b58411adb03da396122f7c7b2f4bf8d` |
| Independent installed-verification receipt | `47fb56c9535caf7e804a7eccb563d373f3adca0180d197163575b6f78c73f926` |

Authority16→17; CRL27119→27120; grant revisions6/8→7/9. Both revoked CRL entries,
revocation dates/extensions, two existing admitted devices, grant binding and scope
are preserved. No all_activated/activation-v2 rollout or entitlement expansion.
The configured minimum_revision1/minimum_crl27088 remain unchanged; distinguish
these configuration minima from current signed CRL27120 and UI84's new ACK floor.
No monotonic state is reset or reduced.

Strict installed readback on RU checks both nodes, eligibility and current validity;
no pending revocations. A separate isolated local process at11:20:24 uses pinned
existing `verify` plus `transition` against the retrieved public snapshot: trusted
signature, exact request/CA, same issuer and gateway keys, grant scope/revisions,
leaf identity/extensions, revocation preservation and floors **PASS**. Its canonical
snapshot matches the committed plan, not merely a planned candidate. Full installed
source/API/configuration/unit/admission/anchor comparisons also pass. No new
approval fields, protocol schema or validator policy was introduced.

## NL_GATEWAY_READINESS

Existing unit: `family-connect-restricted-bootstrap.service`. Configured and loaded
`/proc/2094910/exe` both hash
`4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7`.
Executable remains `friends-restricted/bin/bootstrap-broker-signal-observation-20261012`;
its date is not a new source/build identity. Current PID2094910, invocation
`e9cedbb2fb9d45a2ba0aefd9f211bcb6`, start10:49:27, NRestarts0. Same process verified
at10:50,10:55 and11:19:53; bounded observation exceeds35s. No restart loop observed.

Actual service account `family-restricted`, UID/GID979; profile0600 owner/group979,
parent root:979 mode01770; no extended POSIX ACL. Readback **as this account** succeeds
and matches the installed profile hash. No chmod relaxation. Immutable unit/drop-in
hashes and loaded/configured argv match. Read-only full ExecStart-property comparison
was corrected because systemd includes dynamic PID/start metadata; no unit repair.

Real listener127.0.0.1:18444 serves TLS1.3, verified CA chain and hostname
`gateway.family-connect.test`, ALPN `http/1.1`; presented leaf equals installed leaf:

- Leaf DER `f426d5c79c1dd758ff9cf911596ed92426517903fe4e45d884bf0ef495b9b5c3`.
- CA DER `10eeb2ef1adcb17aa6f75230042b38e2036fe6b3a4796c9b4592a50ca82dc361`.
- Gateway leaf and CRL:18 October10:49:14→14:49:14.
- CA, signed authority and grants expire19 October09:33:41.

This strict listener probe did **not** perform client mTLS or application traffic.
Native gateway startup succeeded; no separate native-authority-checker executable
was found or installed, so standalone native canary acceptance is not claimed.

`bootstrap_seed_ready` observed10:49:33.992185808. Fresh runtime-bound directory:

- Issued18 October10:49:33.989302554; expires14:49:31.111612545.
- Both RU and NL exact bytes:
  `4cbab5fe8a6856310b501380b45952acdd14d7488e41ae87cb5bdf1b32e5cf7b`.
- Delegation signature/directory binding and CRL signature verified independently.
- Effective usable interval is capped by leaf/CRL14:49:14, not the later directory
  expiry. Existing process duration14400s remains unchanged.

Bounded current-invocation fatal/validation query found seed READY and no new
matching failure event; it is not an unlimited journal audit. RU HTTP restored by
the workflow: PID3358039, invocation`8db61f9ec27c47c29bdcd95a3a5064dc`, NRestarts0,
same archive12ca0c…60ed. Ordinary AWG/TCP and unrelated services were not operated.

## UI84_COMPATIBILITY

ADB sees the existing authorized phone. Installed Friends package is code84,
`0.1.18-research84-ui60-4-batch1`; APK SHA256
`697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`
matches before and after. This also preserves packaged native bytes; PERF-2's
separate12-library extraction established the restricted library
`dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`.
No claim that a native MESH handle was loaded during this task.

The normal resolved launcher `FriendsActivity` was opened; its existing automatic
readiness refresh ran. Read-only RU DB lookup, scoped to the unchanged admitted set,
finds new UI84 import ACKs: READY/PRESENT_VALID, orchestrator_usable=true, revision9,
minimum_crl27120, expiry14:49:14, latest recorded11:15:16. These are stored ACKs
accepted by the existing endpoint, not injected test results. The receipt format
contains no directory digest, and this audit does not independently bind the ACK
to a physical media session. Current RU/NL directory equality and these import
observations are **not** substituted for DNS/HTTPS acceptance.

No VPN/TcpVpnService was present before or at11:18:50. No Connect tap was sent.
An initial incorrect MainActivity launch returned activity-not-found; launcher
resolution corrected only the observation. Standard UI dump cannot obtain idle
on this animated screen; screenshot attempts produced no usable image, and the
accepted app retains FLAG_SECURE. No security bypass, blind tap, new helper/APK,
owner instrumentation, animation change or data/floor clearing. Therefore the
allowed one normal connection and DNS/HTTPS tests are **NOT_RUN**, not failed MESH.
Next step needs the owner's ordinary manual UI action, not an application rebuild.

## RENEWAL_READINESS

After CLEANED/strict readback, existing `--mode evaluate` returned NOOP,
alerts[],due[],files_changed0,remote_writes0,restarts0. Existing renewal timer was
restored active/waiting, enabled state unchanged; no new timer or scheduling policy.
Natural scheduled service completed successfully10:58:10–10:58:15, and again
11:13:11–11:13:15 (exit0). At11:19 the same committed generation remained installed;
no authority-maintenance failure persisted. A manual service invocation/reset was
unnecessary. Health service succeeded11:18:51–11:19:15; its actual timer is
`family-connect-credential-health.timer`, enabled/active. A preliminary query using
the nonexistent healthcheck spelling was not treated as health evidence.

Two bounded renewal journal queries timed out; no journal/service reconfiguration
or unbounded retries. Scheduled success is attested by systemd status and unchanged
committed-state readback; the directly captured NOOP payload is from evaluate, not
invented scheduled stdout. Next timer snapshot: renewal11:28:11, health11:28:58.
These are scheduling observations, not promises of subsequent success.

| Next boundary | UTC / meaning |
|---|---|
| Leaf/CRL near-expiry threshold |18 October13:19:14, existing90min threshold; first eligible15min controller cycle must be observed |
| Current leaf/CRL expire |18 October14:49:14; fail closed if normal renewal fails |
| Operator authority/grant threshold |19 October03:33:41, existing6h headroom requirement |
| Operator target with1h reserve |Before19 October02:33:41, preferably earlier; arrange existing authorized maintenance, not another apply of this bundle |
| Authority/CA/grants expire |19 October09:33:41; no automatic offline-root renewal authorization |

**Next automatic credential rotation has not been observed.** Recovery does not
make the offline-root lifecycle indefinitely autonomous. Existing remote CRITICAL
delivery remains **UNAVAILABLE**; local logger/alert unit is not external delivery.
No new notification channel was configured. Operator coverage before the threshold
and subsequent-cycle evidence remain required.

## SAFETY_AND_RECOVERY

Protected materials remain outside Git: local
`state-client-build/mesh-nl-recovery-apply-1/private/` mode0700, receipts0600; RU
`friends-restricted/operator-receipts/mesh-nl-recovery-prep-20261018-01/` and existing
coordinator/node archives. Public evidence contains hashes/allowlisted metadata,
not keys, profiles, product DB, raw device IDs or session payloads.

Current committed sequence17 and recovery-result ledger already bind this bundle.
**Do not reapply, reset to16, regenerate/sign, or restore the old directory tree.**
Retained expired authority/grants/leaf/CRL are evidence only. Future interruption
requires readback of transaction, plan, ownership and CLEANED ledgers, then only
documented forward recovery for that state; no manual rollback of revocations,
grant revisions or floors. A new conflicting generation or ambiguous partial
state is a STOP. If future invalid material causes a loop, leave only the affected
MESH unit fail-closed rather than restoring expired credentials.

Runbook-controlled RU reader pause/resume, NL single start, credential publication
and timer restoration are the intentional runtime changes. Binary/API/management
sources, root/issuer/gateway/Device Identity, admission, security policy, unit
definitions, UI84/native bytes, batching, windows, RTP pacing and timeouts remain
unchanged. Gateway supervisor acceptance, UI84 source consolidation, all-activated
admission, IPv6 and external notifications remain separate workstreams.

## NEXT_SAFE_ACTION

1. Keep the recovered server running; no second apply/start/reset is needed.
2. Owner opens the existing UI84, chooses existing NL/MESH and performs **one normal
   Connect** after a current readiness refresh. Do not force a running-session
   disconnect, change networks or clear any state. Use the existing short DNS/HTTPS
   procedure, establish actual VPN/MESH routing and correlate SessionTrace/server
   evidence; a direct ADB-shell HTTPS success alone is not VPN acceptance.
3. Observe the next due normal renewal/commit and valid fresh runtime directory;
   maintain operator coverage before19 October02:33:41. Do not change TTLs or
   automate root signing to bridge the maintenance boundary.
4. Stop here. Full PERF-2 physical comparisons need their own bounded run; no claim
   of faster MESH, working IPv6, widened user admission or fixed external alerts.
