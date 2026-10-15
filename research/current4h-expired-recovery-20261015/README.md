# Current4h expired-predecessor recovery — local implementation

Management-only derivative of `9423d45ee013b349f342a81be502757b17b3fbf2`.
Accepted source archive SHA256:
`5fa24f5383e3f64c6ce7368e807972a6a4e4e9d832268feabefb9fea396c0e00`.
Not root main, not the old issuer5→6 flow, not the experimental CRL writer.

## Review and reproduce

- [Report](../../docs/releases/2026-10-15-current4h-expired-predecessor-recovery-1.md)
- [Unified management/test delta](recovery.patch), [exact per-file identities](source-manifest.json)
- `before/`: unchanged copies of the affected base modules; `changed/`: derivative modules/tests.
- The patch uses zero-context hunks (`git apply --unidiff-zero` on the exact base);
  prefer the hash-guarded `apply.py` rather than applying it to a different checkout.
- [Security and operation runbook](RUNBOOK.md); [bounded results](results/summary.json).
- `apply.py` verifies the **entire supplied accepted archive hash**, each replaced
  file and the 299-file cumulative inventory. It does not fetch main or amend the archive.
- `package.py` verifies all 13 management modules against the published manifest;
  generates a local management directory with no APK/gateway executable, online
  offline-signer entrypoint, API replacement, private key or production configuration.
- `configure.py` prepares new **private copies** of existing node/controller configs,
  changing only source inventories and the peer source identity. It does not apply them.

The retained archive itself, dependencies, live configurations and generated
cryptographic fixtures are **not uploaded**. A reader without that archive can review
the before/after modules and patch, but cannot claim full reproduction from Git alone.
The base commit is the archive's source identity, not the publication commit and not
a new APK/gateway identity. `sign_authority_offline.py` stays exclusively offline.

```sh
python3 apply.py --archive "$ACCEPTED_ARCHIVE" --out "$NEW_PRIVATE_WORK/source"
python3 package.py --source "$NEW_PRIVATE_WORK/source" --out "$NEW_PRIVATE_WORK/management"
python3 run.py --archive "$ACCEPTED_ARCHIVE" --python "$PYTHON_WITH_LOCKED_DEPS" \
  --go "$GO" --gopath "$CACHED_GOPATH" --out "$ANOTHER_NEW_PRIVATE_WORK" \
  --build-disk "$NEW_DISK_BACKED_BUILD_DIRECTORY"
```

Use absolute paths. Python needs the retained test environment (`pytest`, cryptography
and exact API dependencies); Go needs the retained module cache. Network fetching is
disabled. Runner runs one base characterization, one full Python suite, three fixed
seven-case filesystem/SQLite fault batches, one normal and three race Family/TLS cases.
It stops on a failed command and preserves receipts. No retry-until-pass.
Go test binaries are built **before** generating time-valid synthetic vectors;
test credentials are not lengthened to accommodate a slow build. Only synthetic keys
are created, inside a fresh private fixture. Do not commit the runner output directory.

## Contract

`HistoricalPredecessor` is not an active validated snapshot. The dedicated reader
checks schema/signatures/root, issuer/gateway/key/Family bindings, original intervals,
grants/floors and protected committed-state evidence without pretending the current
time is earlier. Neither admission nor scheduled current4h accepts it.

An explicit recovery request is bound to operation, purpose, predecessor, protected
checkpoint, both nodes' observed state/policy hashes, approved grant scope, exact
proposed successor authority, update classes and expiry. The existing offline root
authorizes the request and the normal wire delegation independently of the old issuer.
No root key is available to the controller or scheduler. Shared verification code's
signing helper is invoked only by the offline signer/test fixtures, never by scheduling.

Current DB device/grant/invite/admission eligibility is rechecked with the actual API
grant validator against a disposable successor projection. Merely being unrevoked in
an old snapshot is insufficient. All currently unrevoked grants must be explicitly
approved and eligible; otherwise the request rejects. Deleted/revoked grants are not
reintroduced; removal of an ineligible entitlement is **not silently performed** by recovery.

Request creation releases locks before offline handoff. Apply requires a fresh
maintenance-outage approval, unchanged checkpoint/state and a valid root bundle.
The existing coordinator/node locks, owner markers, file CAS, SQLite CAS, stop gates,
commit reconciliation, directory publication and start-intent safeguards are retained.
RU API and restricted sync readers are stopped, not merely the NL gateway.
Partial recovery is forward-only, requires explicit `expired-resume`, and preserves
the first error. Ordinary recovery cannot roll back this transaction. A completed
operation is idempotent; the same ID with other bundle contents is rejected.

The predecessor must be linked to an intact **last COMMITTED** protected coordinator
and per-node archive. Lost checkpoint/archive, an untracked credential writer,
unknown additional reader, newer key/authority scope or unexpired certificate outside
this fully-expired case requires a separate decision; this implementation fails closed.
It does not assert that a root-signed old snapshot alone proves global freshness.
