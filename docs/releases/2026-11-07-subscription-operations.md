# SUBSCRIPTION-OPERATIONS — 7 November 2026

## Scope and provenance

Started from remote main `9d05c0f936b076b0536f7c7d23833436677e0191` in a separate
`feature/subscription-operations-20261107` worktree. PR1 and the Android matrix remain
closed. [Canonical Russian operator guide](../operators/subscriptions.ru.md).
No payment/enrollment, baseline, device, APK, production service/code, G4, renewal or
transport-policy changes. No production DB migrations. Only the existing local panel
console and its read-only collector source were updated. Private paths, HMAC key,
mapping, raw HTML/status, backups and operator receipts remain outside Git.

## PR2 review correction set

Review baseline `4e1dfeb4a5ba4624395e7f7712ac3fec5c8531bb`; main remains
`9d05c0f936b076b0536f7c7d23833436677e0191`. These are review findings, not evidence
of a live archive substitution or production mutation.

- First schema SELECT inside the canonical read-only SQLite transaction pins the
  snapshot before its single projection clock. A real server operation between collection
  start and snapshot acquisition is covered through a real ZIP import in fresh `python -I`
  and the strict RU envelope importer; future-event validation is unchanged.
- Archive hash, required members, module file/spec origin and zipimport loader archive
  are checked; preloaded canonical modules and external-package fallback fail unavailable.
  Projection-only tests explicitly stub the archive loader and are not provenance evidence.
- Existing immutable AuditRecord stores local attempt results separately from immutable,
  digest-idempotent SubscriptionSnapshot. UI orders attempts by local journal sequence,
  preserving last successful server observed_at even on collection/import failure and
  server-clock skew. No new subscription state machine or migration. If local import
  cannot run at all, private monitor receipt/journal and freshness remain the fallback.
  Error reporting shares the existing60s import budget; no extra polling/retry supervisor.
- Grace/expire/revoke have independent choose-one blocks and receipts; all copied
  operator commands use noclobber before invocation. True renewal requires a strictly
  later end, although backend accepts equality. Proposal B names RestrictedReadiness.

Final-head CI links and ordinary merge/tree verification are retained in
[PR2](https://github.com/Joker20380/family_connect/pull/2). No post-CI cosmetic source
commit is required. Installed runtime and scoped-check receipt below supplement, not
replace, the earlier dated observations.

Review validation: final built-panel **212 tests PASS**, Django system check and
migration drift check PASS; **82 scoped host tests PASS** (collector/import orchestration,
source/prepare/network guards, real operator CLI and copied-command noclobber). Real ZIP
subprocess tests cover both missing modules, foreign parent fallback, foreign/already-pinned
preloads and hash mismatch. Strict importer still rejects an event after observed_at;
clock-skew/error/recovery preserves the original snapshot and immutable audit.
Global public-docs gate PASS. Test-only static-directory warnings are not installed
runtime failures; normal local startup still runs collectstatic.

Local authenticated actual gunicorn HTTP readback on7 November11:49:41UTC: HTTP200,
no-store, latest attempt ok11:49:23UTC, server snapshot11:49:21UTC,63 devices/1 cohort/
62 outside cohort, age20s, same pinned served archive. This exercises the fresh isolated
SSH process and verified ZIP module loading, not just the projection fixture. A transient
SSH banner/timeout was observed during review; no production/network change was made,
and normal collection recovered. Separate optional full-registry audit attempts timed
out; those are not claimed as a new live before/after paid-table fingerprint PASS.
Local users/payments/operations/cohort metadata and synthetic registry hashes match;
all50 synthetic projection identities/labels/readback match (only existing seed_demo
observation timestamps refreshed). Environment, HMAC key, source pin, volumes and the
PostgreSQL container are unchanged. Review adds no DB migration. Only the console image
and retained collector files are updated; final installed image/source and later fresh
readback receipts are attached to PR2. Old local image/private backup remain available.

## Observed system, not historical counts

- 7 November10:43UTC: local `fc-control-plane-0` console and PostgreSQL healthy;
  both user monitoring timers enabled/active. Readonly-monitor budget380s;
  network-probe95s. The current README's obsolete260s was corrected, historical
  receipts were not rewritten.
- RU HTTP runtime active/running; interpreter Python3.14.4; effective archive
  SHA256 `0fa13b0a92406c9d58043287e880b6533768d031f31e1de10059b9072eb6473e`.
  Its paid_beta module SHA256
  `207688fc4f4b6c151bba8887ba8d95a047ae831c9eddf023df41889e3005d014`
  equals current main source; baseline108, limit10. Archive origin is the previously
  installed subscription overlay, not a new deployment in this task.
- First real subscription read10:51:28UTC:63 registered devices,1 cohort member,
 62 outside cohort; saved/effective active, revision4. Canonical ledger has4 events.
  These are observations of devices/records, not a count of customers, bank payments
  or delivered client notifications. Personal periods/selectors are only in the
  authenticated local view/private receipt.
- Real `paid_beta_admin status` completed exit0 against that canonical registry
  using the current reviewed admin entrypoint over SSH stdin and the pinned served
  paid module. No remote code file was installed or modified.
- Discovery also found an older standalone operator archive
  `9666ce6e96172449fc6c2c2e39cd61a2d082c6742e794a52ba8edb5ef01ba271`, whose module
  still names106. It is **not** treated as the current108 operator. A matching
  source-only108 operator was prepared locally, hash
  `0970014d56501eb59c4a09ef2707f4220e744e761c692d205da123ee2b4c61e6`, with isolated
  real-CLI checks. It is not claimed installed remotely. Routine permanent archive
  installation must select this reviewed source/version, not silently reuse106.

## Actual local panel update

Address: **http://127.0.0.1:8765/subscriptions/** (existing login and inventory-view
permission). PRODUCTION/read-only banner; synthetic operation pages/guards remain.
Source is the external existing RU collector: pinned archive + canonical
`subscription.snapshot`/paid_beta, SQLite read-only transaction and one now for all
rows/events. Envelope2 adds a separate subscription envelope1; legacy inventory1 and
NL collection still work. No new polling service/SSH hop or authority is introduced.
Strict bounded importer saves append-only observations with PostgreSQL triggers;
there is no production payment model, web SSH credential or registry mount.

The image was built through `control_plane/prepare_local.py` and the existing locked
Dockerfile. Only the console was recreated, using the same project, PostgreSQL
container, named volumes and existing secrets. Pre-update private PG dump/synthetic
backup and exact rollback image are retained. Synthetic SQLite stayed byte-identical.
Final local console image ID:
`sha256:045c193cc0a0a91f92c652bcafbbc4e499fefe495ce3c7b08d2bf43267b61466`.
Final-image authenticated HTTP recheck:200/ok,63 devices/1 cohort, fresh observed_at
**11:10:10UTC**. This is a local operator image, not a public product artifact.
Extracted table-data fingerprints also match for existing local users, payment records,
operation requests and cohort metadata. Only the additive observation migration ran.
Only the readonly-monitor ExecStart source path changed to the retained allowlisted
collector copy, preserving interpreter/SSH pins and timer timing. Network probe and
all production services were untouched. Image/source manifests and exact installed
locations are in the private receipt.

Authenticated **real HTTP** readback through the running gunicorn route returned200,
`Cache-Control: no-store`, real63/1 data and fresh observed_at **11:02:58UTC**. This was
not a fixture view/direct template call. The temporary local authentication session
was deleted afterwards; no new user/password was created. Loopback health returns
`scope=synthetic` because operations remain synthetic; that health response is **not**
evidence of subscription freshness. The subscription page supplies its own source,
observed_at, archive hash, freshness, saved/effective state, bounds, revision and
corresponding event. APPLIED is explicitly not bank/delivery evidence.

Normal scheduled collector receipt **11:03:05UTC** reports all three existing sources
IMPORTED. Both timers remain active; services Result=success/ExecMainStatus=0,
budgets380/95 seconds. Before/after canonical fingerprints match for devices, invites,
device_support, paid subscriptions/events and restricted_grants. This is a bounded
comparison, not a claim that a live registry can never change after the observation.

## Checks

PASS — built local-panel image: Django checks, no missing migrations, **203 panel
tests** on a separate PostgreSQL container/network/test DB and synthetic SQLite.
Coverage includes roles, non-editable production route, append-only DB trigger,
strict schema/private-field rejection, atomic envelope import, error/unsupported/
no-data/zero/noncohort/stale separation, canonical active→natural expiry projection
without new event/revision, source pin failure, preserved synthetic guards.
Staticfiles warnings belong to test configuration without collectstatic; the installed
console ran collectstatic and the authenticated page/asset route were checked separately.
The final presentation-only cohort totals/order refinement passes **17 subscription
tests** against the final image; full panel gate above remains its immediately prior
source check. Global `check_public_docs.py --all` completed with no errors.

PASS — **83 scoped repository tests**: collector/source preparation/monitor bounds,
network probe, existing operator CLI and backup. Real operator commands cover activate,
explicit absolute extension, exact replay, grace, expire and terminal revoke on isolated
data. New paid-aware backup verifies full table inventory, SQLite integrity/FK and
canonical projection after isolated restore of a **nonempty** registry. The old default
still rejects nonempty paid data. No made-up renew/restore/dry-run command is documented.

PASS — actual nonempty-registry recovery rehearsal: a bounded520192-byte consistent
SQLite backup was obtained read-only over the existing pinned SSH path (remote
in-memory destination only, no remote file/service write). The private local copy was
then backed up/restored by `--include-paid`; full inventory, integrity/FK and canonical
paid projection PASS. This is stronger than synthetic-only backup evidence, but not
production service restart/recovery or an encrypted offline/off-site copy (NOT_RUN).

The first test run found two test-contract issues: the synthetic test opened a readonly
transaction before creating its event, and the old table-name guard forbade even an
immutable observation table. Both were fixed specifically: write only in the synthetic
fixture; the guard permits only the exact observation table/column set, no paid state
machine. Final full panel gate passes. No production workaround or skipped assertion.

## Recovery and limits

Local rollback: select the retained previous console image with the same compose project,
env and volumes; restore only this task's collector ExecStart override. The additive
observation table can remain. Do not downgrade/restore PostgreSQL or paid registry merely
to roll back the view. Current private receipts list exact image/config paths and checksums.
The paid backup procedure now explicitly supports nonempty registries; full service/
secret cold-recovery remains NOT_RUN, distinct from PASS isolated SQLite/paid projection.

No new Android/runtime acceptance: physical beta119 still proves only its own noncohort
through normal ingress. Prior API35 synthetic event evidence stays separate. Physical
paid-event notification, hard whitelist, COLD_BOOTSTRAP_GAP, Android natural expiry,
real identity switch and mixed-network keep their earlier statuses/NOT_RUN gates.
New events are discovered on subscription screen open/Refresh; startup drains already
saved events only. There is no independent background event acquisition or full-history
delivery guarantee. No external alerts; timers depend on this workstation.

## Prepared decisions, not production changes

Guide decision A defines an explicit paired108/119 eligibility allowlist and matching
APK attestation, preserving108 replay/entitlements; mixed/unknown observations fail.
Guide decision B identifies configuration issuance, gateway peer/TCP-user registration
and runtime/persisted active-set reconciliation on all nodes, retaining existing MESH
checks. Previously issued profiles/sessions need real server-side removal/deadlines;
blocking configuration download alone is insufficient. Both have explicit completion
gates; neither changes current policy. A real paid action still requires a specific
recipient, UTC period and legitimate basis, not a demonstration record.
