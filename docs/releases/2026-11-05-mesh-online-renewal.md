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

## Implementation checkpoint (not stage acceptance)

The explicit `MESH_SAME_HOLDER_ONLINE_V1` path reuses the controller/node locks,
owner journal, issuer, membership, staged file CAS, ProfileStore, SQLite sequence and
existing archive ledger. It does not change the ordinary quiesced transaction. Node RPC
requires an explicit in-process qualification flag; packaged production construction
does not set it. There is no new timer, production online CLI activation or second signer.

Window calculation after initial read: eight bounded RPC rounds plus explicit scheduling
lateness, Android cooldown300s, owner polling30s, readiness request30s, maximum ordinary
lease control attempts55s, credential exchange15s and skew5s. Thus local1s-RPC/0s-schedule
qualification requires443s; configured SSH120s plus schedule requires1395s+schedule.
Neither production validity nor timeouts are increased. Unknown timing rejects.
Both gateway bindings, authority, keys, grants, policy revisions, CRL floors and current
material validity are checked. Existing client certificate records also need headroom.

States: ONLINE_ACQUIRING/FENCING → PREPARED/STAGED → durable COMMIT_DECIDED →
per-node DECIDED/PUBLISHED → RU delivery-ready → CLEANING → COMMITTED. Before the
decision, explicit ABORT requires unchanged credential files and does not restore DB rows.
After COMMIT, retry uses the same plan/digests and higher fencing epoch, never a new CRL
or rollback. Lost RPC results reconcile against node state; completed cleanup is archived.

During NL-only publication, existing peers retain their authenticated generations and RU
still gives predecessor readiness. Runtime receipts use the same native credential loader,
cryptographic successor validation and process-instance nonce. RU only exposes the new
CRL/readiness generation after both exact profile hashes acknowledge. It copies validated
current directories without creating seed rooms; no distributed instantaneous atomicity is
claimed. Readiness uses a fixed committed issuance target, not a moving target per refresh.
Local publication is not a native session commit; only authenticated exchange advances it.

45 focused tests cover17 controller crash boundaries,17 node crash/lost-response points,
four durable abort positions, stale epochs, maintenance contention, client headroom,
duplicate delivery/commands and two revoke positions. Positive/unit readers are doubles;
those tests alone are NOT native continuity proof. Existing affected Python/package scope
is214 PASS/5 optional skips. A real two-node stand has reached two authenticated native
generations on both nodes; its complete cross-bound outcome/provenance is pending.

Known blocking gaps at this checkpoint: post-decision emergency detection safely stops
readers and preserves the COMMIT decision, but machine handoff/reconciliation from that
fenced state is unfinished; no manual marker deletion is prescribed. Complete malformed
receipt, expiry, old-peer/new-connection and cache-delay acceptance is also outstanding.
The accepted maintenance API archive is intentionally unchanged; it must not be silently
substituted with the newer readiness implementation. Final online runtime packaging and
root qualification remain separate required gates. This checkpoint is NOT release-ready.

## Additional negative and bootstrap evidence

Source checkpoint `a8e1db900105219b22abae21accd2c2b6e2f5b30` is pushed and remote SHA
verified. The real native stand is repeated from an immutable export of this commit.
The earlier development stand passes999.28s but is not substituted for that frozen-source
acceptance. Isolated root/package scope on the checkpoint passes219 tests. The first root
attempt incorrectly put root-owned fixtures below a user-owned bind mount (UNSAFE_PARENT)
and omitted Git's explicit read-only repository trust; both harness errors are retained.
The repeat uses root-owned tmpfs, without relaxing ProfileStore ownership checks.

Focused online negatives now pass55 tests: add unavailable participant/precommit abort,
rollforward after predecessor expiry versus successor-expiry fencing, corrupt durable
decision, and six readiness-marker failures with an unconsumed proof challenge. Strict
existing JSON parsing rejects duplicate marker fields; no new runtime package dependency.

The six inherited cases (unknown issuer, wrong Family, revoked device, wrong gateway,
stale CRL floor, stale revision) all failed the same baseline `auth_test.go:87` assertion:
expected zero authenticated-exchange reports before TLS admission, actual nonzero reports.
Baseline15ef592 reproduces each case five times. The new observer preserves separate
admission diagnostics and all denial assertions.

The expanded bootstrap artifact gate also reproduces an independent busy-reason assertion:
an ERROR frame gives a direct public Code, while a peer closing before HELLO gives the same
public Code wrapped by the existing startupdiag.Preserve with its receive cause. Comparing
Go error object identity incorrectly calls the latter a changed wire reason. The check now
requires both errors.Is and exact startupdiag.Legacy category; a new deterministic test
also requires the original receive cause and unchanged public Error text, and contrasts
the actual ERROR-frame branch. No production error is suppressed or authorization changed.
Ten race repetitions of busy, both HELLO outcomes and negative admission boundary PASS.
The complete artifact-enabled bootstrap repeat is still required after this assertion fix.
