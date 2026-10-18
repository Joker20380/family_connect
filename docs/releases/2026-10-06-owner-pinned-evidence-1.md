# OWNER-PINNED-EVIDENCE-1 — PARTIAL / STOP before arming

Subsequent [PINNED-RELIABLE-CALLBACKS-1](2026-10-06-pinned-reliable-callbacks-1.md)
passes source-level remediation. It has not been frozen as a new binary pair or
deployed; this physical task remains unexecuted/PARTIAL on deployed beta67.

Date: 2026-10-06. Continues accepted PINNED-EVIDENCE-DEPLOY-1 with explicit separate
owner-only physical experiment authorization. **Zero physical attempts executed**.
The task stopped at a frozen diagnostic contract limitation, not expired credentials,
missing ADB, lost owner state, or a failed transport experiment.

## Fresh preflight

At16:11:50UTC, intended authorized Redmi31ce63ba / Redmi Note9Pro:

- Installed package com.familyconnect.app.friends, beta67/code67, non-debuggable;
  exact APK SHA256 `8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f`.
  Same bytes retain accepted signer/arm64/native provenance from deployment.
- UID10283, inode601521, data directory and firstInstallTime preserved.
  Existing signed snapshot helper verifies Support FC-4D8Q-REEG, encrypted identity
  fingerprint/decryption, enrollment fingerprint and activation against deployment
  closeout. Helper removed; owner app reopened without uninstall/data clear.
- Wi-Fi0/mobile_data1. Status-only Android receipt UNAVAILABLE, empty target,
  armedfalse, consumedfalse, count0. No prearm/nonce created.
- RU owner admission revision3, non-revoked. Current beta67 READY, PRESENT_VALID
  provisioning/bootstrap, failureNONE, ACK_RECEIVED; authenticated fetch epoch
  1791302980, latest receipt1791303117, ACK1791303118. No forced cache bypass.

Gateway readback: actual loaded SHA256
`c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143`, embedded revision
`ffd27988468fba427aaba6213b862dca01020972`, vcs.modified=false. PID1266691,
NRestarts0, active/listening. Configuration unchanged from accepted deployment,
including only the authorized FC_DIAGNOSTIC_CONTROL_DIR=diag67 exception. Dedicated
directory empty, UID/GID979/mode0700. No gateway restart/config/binary replacement.

At16:12:04.441605UTC actual served TLS leaf matches accepted profile:
DER SHA256 `a2c4324401fbfb2374a61c1404caa0d264305533496394a17c641c4549940ff4`,
valid14:47:25–18:47:30UTC. Effective headroom9325s =2h35m25s, leaf-limited.
Issuer6/grants3/1 valid through07.10 14:45:31UTC; bindings/revisions/revocation unchanged.
CRL9478, SHA256 `8c67ac61e1489de2c541a27d943e499c2ca7dd398d0806ed95e59181adf8113e`,
valid16:11:35–20:11:35UTC, exact RU/NL match. RU/NL directory generation
15:53:17.577994843UTC, SHA256
`0c160f8b9ada7888ae1bd7f2000b0c0deee08527a10393a5e96c2fb97bb6bff9`, exact match.
No renewal needed for this bounded preflight; later execution needs a fresh check.

## Proven frozen-contract blocker

Inspected clean checkout `/tmp/fc-freeze67-validation2`, HEAD exactly
`ffd27988468fba427aaba6213b862dca01020972`; git status clean before/after checks.
These findings concern the accepted frozen source, not the surrounding dirty worktree.

1. `carrier/sessiontrace/correlation.go:54` ProvisionalCandidate retains media,
   reconstruction/completion flags and timestamps; CorrelationReceipt at65 exports
   key/state/candidates/descriptor. It has no Reliable acceptance/consumption events,
   receive_next/buffered before/after, or ACK generation/sending callback records.
2. `correlationBoundary` collects selected carrier/media stages. `complete()` checks
   exact descriptor identity, sequence-known, carrier completion and reconstructed
   fragments. **COMPLETE does not require Reliable acceptance or an ACK callback.**
3. `carrier/sessiontrace/watch.go:32` rejects every target whose direction is not tx.
   Receiver-oriented code branches elsewhere in that file are not an operational
   accepted receiver watch: `PrearmCorrelation` does not enable such a legacy watch.
4. `carrier/sessiontrace/correlation_command.go` and `correlation_linux.go` expose
   correlation prearm/status/bind/cleanup, not an additional receiver callback-pinning
   or full snapshot export operation. Ordinary Boundaries remain a64-entry ring.
5. Therefore media identity can survive ring churn, but requested exact receiver
   Reliable acceptance/consumption and ACK proof cannot be retained by this pinned
   control contract. Polling ordinary snapshots/logs cannot be silently substituted
   for the explicitly required ring-independent pinned chain.

Existing tests rerun locally against that exact clean frozen source (no product
artifact built or changed):

```text
go test -count=1 -tags fc_owner_diagnostic ./sessiontrace \
  -run 'TestLegacyReceiverWatchRejected|TestCorrelationRetryMatrix' -v
PASS (0.015s)
```

`TestLegacyReceiverWatchRejected` confirms intentional rx API rejection.
`TestCorrelationRetryMatrix` passes six identity/order scenarios and2100 ring-churn
events, reaching COMPLETE using only media/carrier callbacks: its fixture does not
emit the requested Reliable acceptance/consumption/ACK callbacks. This is confirmation
of the accepted media-level scope, **not physical callback-chain acceptance**.

Deployment PASS established artifact/preservation/control availability and ordinary
baseline. It did not establish this stronger end-to-end callback retention. The
earlier statement that a physical task was technically unblocked is corrected here.

## Physical result fields

- Session tag / selected DATA N / attempt1 identity: not issued; no session started.
- Attempt0 drop: zero; fault arm/prearm/bind commands: zero.
- Sender RTP / exact remote RTP / PictureID+fragment matching: not measured in this task.
- Reliable acceptance / ACK generation+send / sender ACK+base progression: not measured.
- HTTPS/DNS/TCP continuity and no-restart proof: not rerun; prior deployment baseline
  is historical, not substituted for the authorized physical experiment.
- Cleanup: no experiment state created. Android unarmed/count0; gateway directory
  empty; temporary identity helper removed. No stale generation introduced.
- Reverse DATA104 lifecycle: not observed because no experiment session/cleanup ran;
  not inferred absent and not fixed.
- Remaining uncertainty: physical selected retry behavior and all unexecuted gates.
  The receiver pinned callback retention limitation itself is confirmed by source/tests.

No impairment/netem, repeat, soak, Krasnodar, transport tuning, reverse DATA104 fix,
public/default/catalog changes, sealed rebuild/substitution or security relaxation.
Preserved beta67 installation and beta66 rollback state unchanged.

## Evidence and next step

Restricted local receipts:
`state-client-build/field65-export16/owner-pinned-evidence-1/owner-preflight.json`,
`gateway-preflight.json`, `readiness.json`, `frozen-contract-tests.log`;
credential receipt `pinned-evidence-deploy-1/verification-1791303124551085686.json`.
Initial local wrapper had a Python split/syntax error before any runtime action;
corrected wrapper then completed preflight. No private identity/key bytes in docs/Git.

**Exactly one recommended next step:** authorize a separately scoped diagnostic-only
receiver callback-pinning/export change with new immutable acceptance before the
single owner physical experiment. No source change or new artifact is authorized or
performed by this report; do not weaken PASS criteria to consume the physical attempt.
