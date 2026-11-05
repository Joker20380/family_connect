# Online MESH renewal qualification / 5 November 2026

## Entry and boundary

Entry HEAD is exactly `15ef592bf92c143839130da7884328e4a7d9918f`. The four pre-existing
dirty documents and six untracked historical files are preserved. This is the existing
Android MESH incident, source/isolated qualification only: no production access, installed
APK change, catalog, timer, paid/cohort/admission/boot change or activation permission.
Installed/opt-in118 and updater113 remain unchanged. Paired-DNS/WebSocket remain OPEN.

## Dependency map and selected contract (implementation in progress)

- RU's existing issuer signs leaf/CRL materials using the existing local custody key.
  ProductionController owns the operation under DurableOperation.lock; ProductionNode
  uses the existing owner, staging/archive ledger, membership and canonical ProfileStore.
- The controller transaction.json/plan.json carries the durable decision. Online prepare
  must not promote files before this decision; normal quiesced/emergency paths remain.
- NL gateway profiles feed Family TLS, credential exchange, lease and broker monitors.
  Runtime receipts must come from the actual reader, bound to its process instance and
  exact profile digest, not merely a successful rename. Unknown runtime contract rejects.
- RU CRL/issuers and per-node directory feed authenticated readiness. A delivery gate
  must hide the committed successor until both corresponding runtime readers acknowledge.
  Directories retain the running rooms; no restart/new seed is evidence of continuity.
- Readiness's existing certificate retention (expires > now+300) must be reconciled with
  the Android300s persisted cooldown,30s owner polling,30s request and bounded exchange.
  Otherwise an early CRL-only delivery may produce a refused, non-retried candidate.
- Recovery follows the same durable decision/fenced owner, not the newest local file.
  Pre-decision abort requires unchanged live state; post-decision may only roll forward.

Online controller/node/publication/native qualification is NOT yet complete at this
checkpoint. No production route is enabled by committing this source.

## Bootstrap diagnostic contract

The inherited six assertions are a phase-classification regression: OpenServer sent
profile/TLS-open failures to the callback for an authenticated broker exchange, although
no authenticated exchange or provider admission occurred. The preserved contract requires
that callback only after Family authentication. Admission failures are not successful
exchanges, but their errors must still be observable.

OpenServerObserved separates the admission observer from the authenticated exchange
observer. The command records structured bootstrap_admission_rejected with stage/reason;
the existing exchange event remains reserved for authenticated protocol failures. The
legacy OpenServer contract and all six negative assertions are unchanged. Added negative
checks require exactly one family_open admission report and zero exchange reports, no
descriptor/provider call/authentication; valid control has no rejection report.

Raw local evidence: `state-client-build/mesh-online-renewal-20261105/`.
Baseline15ef592 is rerun from an isolated source archive; updated bootstrap `-race -count=3`
passes. An initial broader run retains a transient existing authenticated-busy wire-reason
failure; it is not erased or attributed to this fix without evidence. No tests are disabled.

## Remaining gates

Finish online transaction, runtime/readiness integration, both-node continuity and fault
matrix before claiming this stage complete. Then stop. Full release CI, new immutable
artifacts, equal gateway builds, scheduled live renewal and physical/mobile allowlist
acceptance remain separate, unexecuted gates. No independent timer or writer is authorized.
