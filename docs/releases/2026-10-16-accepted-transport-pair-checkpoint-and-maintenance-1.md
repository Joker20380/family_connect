# ACCEPTED-TRANSPORT-PAIR-CHECKPOINT-AND-MAINTENANCE-1

## Result

**RESULT=ACCEPTED_PAIR_PRESERVED_MAINTENANCE_COMMITTED.**
**NEW_PAIR_FAST_RECONNECT=PASS_BOUNDED remains closed for its exact pair and scope.**
One existing ordinary operator/offline maintenance operation committed and completed
protected cleanup on RU/NL. Gateway remains running with the accepted executable.
**PRODUCT_BINARIES_UNCHANGED; OPERATIONAL_MATERIAL_UPDATED; PHONE_UNTOUCHED.**

Input review publication: `bf9b3c6c81847b6c75085d6184eac35dab5f30fc`.
[Safe selected evidence](evidence/2026-10-16-accepted-transport-pair-checkpoint-and-maintenance-1.json).
The publication commit, source inventories and artifact hashes are distinct identities.
No phone query, CONNECT, regression suite, build, APK signing or device acceptance was repeated.

## Accepted-pair checkpoint

| Retained identity | SHA256 |
| --- | --- |
| Installed diagnostic APK, last verified by the completed episode | `8e5579f04de91e4ec00e3e79271dbb0f380b1ed91945ff89016aa50d274a8845` |
| Embedded native | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Client cumulative source inventory, not Git commit | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |
| Gateway executable, configured and loaded before/after maintenance | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |
| Gateway source inventory, not Git commit | `722746429539a1307d693ce6fcc83579a842d3f1c549a626a36676a6d665c42e` |

Existing receipts, not new tests, establish this chain:

- [Local transport-pair acceptance](2026-10-16-gateway-transport-progress-burst-candidate-1.md):
  C_NEW/G_CANDIDATE supported 8/16/19/20 and separate stress40 checks, both directions,
  normal/Family-TLS and fixed normal/race/multicore coverage. Inherited server-suite
  failures remain; this is not an all-suites-green claim.
- [Diagnostic derivative](2026-10-16-bootstrap-pre-hello-correlation-1.md) preserves
  that transport policy and adds early exchange/export correlation with its recorded
  local checks; [observed trial](2026-10-16-bootstrap-pre-hello-observed-trial-1.md)
  establishes the diagnostic APK's device correlation, not historical causality.
- [Gateway deployment/readiness](2026-10-16-gateway-transport-progress-live-1.md)
  binds the actual executable to the retained candidate. Current maintenance checks
  independently retain that same executable; no old recovery baseline is substituted.
- [Completed no-restart A→B](2026-10-16-new-pair-fast-reconnect-no-restart-1.md):
  restricted A/B, **3431ms** local OFF→CONNECT, app PID12008 and gateway PID356992/
  INV_FAST continuous during the test; B CONNECTED270.203s, final OFF in334.941s.
  All three VPN-bound IP checks, including after240s, were explicitly owner-confirmed
  NL **UI observations**, not saved HTTP responses or exact check timestamps.
  Exact dedicated/native/app readiness and client/server session binding are retained.

DNS_A=NOT_DIRECTLY_EXERCISED and DNS_B=12 responses/0 recorded errors remain as reported.
DNS_A does **not** reopen this completed milestone. A's archived early tag/startup scalar
were not exported; B's early tag was retained. Late server terminals after OFF and the
per-surface retention limits remain documented, neither hidden nor universally benign.
No new ownership capture or whole live burst envelope was exercised. Chat operation,
borrowing/handoff, historical causal binding, supervisor, long-duration/field acceptance
and public release remain separate open criteria. Historical FAIL reports are unchanged.

## Fresh need and selected workflow

Read-only observations at12:56–13:03 UTC found the exact loaded gateway, listener and
valid strict served chain. Authority/grants expired at17:34:58 UTC, leaf/CRL at15:14:20 UTC:
**material was valid**, but the authority/grant six-hour operator threshold11:34:58 UTC
had passed. The accepted evaluator returned `RENEWAL_REQUIRED`, due `authority,grant`,
with `OFFLINE_AUTHORITY_RENEWAL_REQUIRED`. This was an operator action requirement,
not expired material or an active unfinished maintenance outage.

Current4h timer was enabled/active; the preceding scheduled service exited75 rather
than performing authority renewal. Both node owners and pending authority request were
absent; previous transaction was COMMITTED; no active writer was observed. Actual
restricted-session count remained **UNKNOWN**. The user-authorized outage includes
interruption of those sessions; no zero-session assertion was made.

Both authoritative grants were unrevoked and eligible under the installed device/
invite/admission validator. No pending revocations were reported before maintenance.
The existing source-pinned management map was
`5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145`.
The installed compatible node/controller and its existing locks/strict validators were
used without deployment or modification. **Ordinary `authority-request` → offline
signing → `operator --approve-maintenance-outage`** was applicable. Expired recovery
was neither necessary nor attempted; the [accepted recovery runbook](../../research/current4h-expired-recovery-20261015/RUNBOOK.md)
does not authorize restoring its historical `21f0a0fd…70509a` gateway.

## One maintenance operation

Operation `accepted-pair-maintenance-20261016-130941` retained one request, signed bundle
and durable phase/cleanup receipts privately. The renewal timer was paused once for
the handoff and restored once to its prior enabled/active state; schedule, permissions
and approved scheduled leaf/CRL scope were not edited. No parallel writer was launched.

One initial RPC envelope was rejected `NON_CANONICAL_INPUT` **before request issuance**.
Durable readback confirmed no owner/request; the same operation then used the accepted
node authority-request path. This was not a second issuance or a blind replay after an
ambiguous timeout. One preliminary local import check lacked an existing dependency;
the retained compatible environment was selected before custody/signing, without
installing dependencies, modifying the signer or running regressions.

The exact accepted offline signer
`2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6`
ran once on the existing signing host through protected vault custody and a memory FD.
Its pinned API/import origins were checked. No root key/password was placed in argv,
logs, Git, chat or on either server. Only the signed handoff went to RU.

| UTC,16Oct2026 | Durable observation |
| --- | --- |
| 13:10:27 approximately | Existing node issues the authority request; successor validity starts13:10:22 with the ordinary five-second skew allowance |
| 13:12:51.855 | One operator apply starts; exact configured/loaded gateway bytes checked immediately beforehand |
| 13:13:14.470 | Workflow NL start intent, same executable; new PID430332/INV_MAINT replaces PID356992/INV_FAST |
| 13:13:17.675 | New runtime-bound directory issued, not copied from the previous runtime |
| 13:13:17.678 | Current-invocation `bootstrap_seed_ready` |
| 13:13:18.061 /18.151 | Workflow restores RU HTTP / directory timer |
| 13:13:18 /19 | RU / NL protected cleanup ledger `CLEANED` |
| 13:13:20.419 | Apply exits0, `COMMITTED`, `first_cause=null` |
| 13:16:09.654 | Renewal timer restored; no manual scheduled writer invocation |
| 13:16:56–13:17:17 | Final short runtime/services/material readback |

The28.564s apply envelope is **not** an exact measured traffic-outage duration.
The planned stop/start loses prior in-memory holders; their count/roles were unknown.
This later maintenance does not change the earlier completed no-restart interval.

## Security, cleanup and runtime result

- Authority sequence14→15 with the same issuer key, trust anchor, identity bindings
  and policy. Both grants retain their exact scope/revoked state and increment revision
  once. No entitlement was added, removed or restored; grant lists remain private.
- CRL sequence27103→27104; existing revocations preserved, entries0→1 through normal
  cutover. Minimum revision1 / CRL floor27088 are unchanged, never lowered. Admission/
  anchor policy digests match before/after; normal strict snapshot validation passes.
- **Gateway leaf remains byte-identical**: it was not yet due at apply. Its existing
  key/certificate still validates against the same-key renewed authority. Do not call
  this a leaf renewal. Authority/grants and CRL, plus runtime/directory, were updated.
- Both nodes have `CLEANED` ledgers and verified protected archive manifests: RU13 files,
  NL8;24 retained operations on each, existing bound256. Only `archive`, `completed.json`
  and `operation.lock` remain at the node state root: no owner/pending authority marker.
  Coordinator remains COMMITTED; no residual active writer or recovery-required state.
- Configured and loaded gateway SHA remain `a5372571…885e61f`; unit/argv fingerprints
  and loaded/next-start argv agree with pre-maintenance. No binary/management replacement,
  new research/supervisor flag, manual extra restart or configuration workaround.
- Listener18444, exact expected leaf, strict served chain, non-revocation and authority
  binding pass. New directory hash
  `7f63f2e0ec83f157b074aa0d2377cdf58d6eeda24571f493c9bbeb05d01fae73`
  matches RU/NL and current runtime. These are server readiness observations, **not**
  a new owner-TUN, mTLS-client or application traffic acceptance.
- Gateway and RU HTTP run; directory timer runs and directory sync succeeds. Current4h
  timer is enabled/active/waiting; its13:16:09–13:16:12 scheduled run exits0. The separate
  read-only evaluate returns NOOP with `LEAF_T_MINUS_120M` warning and zero mutations.
  A timer/NOOP is not evidence of leaf renewal or future successful scheduling.

## Absolute bounds at final readback

| Item | UTC |
| --- | --- |
| Renewed authority and both grants expire | **2026-10-17 13:10:22** |
| Next mandatory operator threshold, six-hour headroom | **2026-10-17 07:10:22** |
| Retained gateway leaf expires / current limiting security bound | **2026-10-16 15:14:20** |
| Leaf reaches scheduled90-minute threshold | **2026-10-16 13:44:20** |
| New CRL expires / reaches scheduled threshold | **2026-10-16 17:13:01 /15:43:01** |
| Directory issued | **2026-10-16 13:13:17.674917466** |
| Directory/runtime context bound | **2026-10-16 17:13:14.649495830** |
| Conservative process-start plus4h bound | **2026-10-16 17:13:14.494** |
| Seed rotation nominal3h boundary | **2026-10-16 16:13:14.649** |
| Next current4h run, systemd monotonic estimate at13:17:17 | **2026-10-16 13:31:09.646**, subject to timer accuracy |

Future renewal is **not assumed completed**. The15:14:20 leaf limit is earlier than
the new runtime/directory limit; ordinary scheduled leaf/CRL maintenance remains necessary.
No new multi-hour gate, changed TTL or scheduler authority was introduced.

## Counts and remaining work

One logical maintenance / accepted request / offline signature / operator apply;
zero explicit resume or credential rollback. One workflow stop/start each for NL gateway
and RU HTTP; one directory-timer stop/restore; one renewal-timer pause/restore.
One pre-issuance formatting rejection is recorded separately. No restart-until-green,
extra gateway restart, code/management deployment, build, source re-audit or regression run.
**ADB/APK signing/install/rollback/CONNECT/export=0.** Phone was not queried: its last
verified state remains the prior report's diagnostic APK, UID10283 and VPN OFF; that is
historical evidence, not a new device-state claim. No public distribution was changed.

Next product criterion: **a separately authorized bounded field trial in the target
network**, with fresh prerequisites. Do not automatically start it. Chat handoff,
supervisor, long-duration coverage and release are separate tasks. Preserve
`LIVE_BURST_ENVELOPE=NOT_DIRECTLY_EXERCISED`, `HANDOFF_ON_DEVICE=NOT_PROVEN`,
`HISTORICAL_A_CAUSE=NOT_PROVEN`, `HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN` and unpromoted
supervisor acceptance. Historical smoke PASS/reconnect FAIL remain unchanged.

Only safe documentation/evidence is published on the existing review branch. Raw
requests/bundle, operational archives, grant/identity data, credentials, keys, APK and
binary remain private. Remote publication readback is retained in the private receipt;
no main/workflow/catalog change or release is authorized by this checkpoint.
