# Closed candidate-readiness adapter

This is an operator acceptance runtime, not the Friends HTTP service, authority
issuer, or owner-proof API. It never starts/stops production services, switches
ingress, renews authority, installs Android, or commits a generation. Production
execution requires separate authorization. Keep old18084 available until actual
Friends app `OWNER_PRODUCT_READY`; never touch18085.

## Attempt13 defect

The retained operator called `runpy.run_path(friends-http.pyz, run_name='__main__')`
with `--help`, then `runpy.run_path(fixture_recipe.py)`. The latter imported
`control.friends.restricted`, whose line21 imports `provisioning.friends_catalog`.
`runpy` had removed the HTTP archive from `sys.path`. Cached `control.friends`
still resolved inside the archive, but the first top-level `provisioning` import
failed. The accepted HTTP archive **contains** that module. This was a transitive
adapter import-layout defect, not a missing HTTP-service dependency.

The historical recipe extracted `configured` from a test file. Full-checkout tests
preloaded modules/resolved repository roots; the isolated transition-loader test
checked exports, not this subsequent recipe/import sequence. Neither tested the
actual outer operator dependency closure. Do not restore this recipe, add
`PYTHONPATH`/`sys.path`, copy the checkout, or install packages ad hoc on a host.

## Build and inventory

Use a committed HEAD containing this fix. The deterministic builder exports that
HEAD with `git archive` into a clean temporary tree, ignoring unrelated worktree
changes. Its own source and manifest must match the commit. The final bundle is:

- `candidate-readiness.pyz`:13 explicitly mapped Python sources plus the lockfile
  and embedded inventory; normal ZIP imports retain a stable archive search root.
- `readiness-delivery-check`: public-input-only wrapper over the unchanged accepted
  `wholedevice.ValidateDelivery`, built CGO-disabled with Go1.26.0 linux/amd64.
- `readiness.lock`: exact existing Python distribution versions; use the existing
  locked Friends venv. No new dependency/install is required or authorized.
- `provenance.json`: source commit, builder digest, every packaged source digest,
  native source/dependency inventory, native/archive digests and tool provenance.

```sh
python scripts/package_friends_readiness.py --revision FULL_COMMITTED_HEAD \
  --go /path/to/accepted/go --output /new/private/bundle
```

Go uses the existing verified module cache with network downloads disabled and
`-mod=readonly -trimpath -buildvcs=false`. Build twice and compare all bundle bytes.
The main HTTP/sync archives and canary54 APK are inputs, never rebuilt by this tool.
Record external Python/stdlib and locked package versions separately: this is a
closed application-source artifact, not a bundled Python interpreter/venv.

## Isolated command and configuration

Use absolute artifact/config/evidence paths. The evidence parent must already
exist; the evidence directory must be **new**. No working-directory dependency.

```sh
/path/to/locked/venv/bin/python -I /bundle/candidate-readiness.pyz \
  --config /private/adapter-config.json --evidence /private/new-receipts --check
```

`--check` checks full imports, inventory, exact configuration/pins and installed
runtime versions without creating a listener or probing a candidate. Omit it only
for authorized acceptance. The exact version1 JSON schema rejects extra fields:

```json
{
  "version": 1,
  "mode": "fixture",
  "http_artifact": "/absolute/friends-http.pyz",
  "http_sha256": "verified-64-hex-sha256"
}
```

`fixture` mode creates fresh disposable authority/identities in a private temporary
directory and starts the pinned HTTP artifact on ephemeral loopback. It runs B–G,
checks challenge semantics and native delivery crypto, then stops only that owned
fixture process and deletes its synthetic state. No provider or production calls.
The room URL is the non-live `test-only` sentinel. No static private fixture keys,
OAuth, production identity/proof, credential bundle or live room URL is shipped.
Fresh synthetic keys exist only in the short-lived fixture's private state/memory.

`candidate` mode adds exactly these objects:

- `candidate`: `port` (only18086), `generation`, owned `pid`, `/proc` `start` token,
  `non_canaries` (nonempty array of objects containing only `public_identity` and
  `wireguard_public_key`). These are public challenge inputs, not owner proofs.
- `authority`: absolute `runtime` (accepted sync archive), `sha256`, `database`,
  `material`, `host` (accepted NL gateway), `ssh_key`, `known_hosts` paths. Only
  the accepted isolated `sync --check` pre-network/read-only operation is invoked.
  The adapter never signs, refreshes, syncs, or records those path values in receipts.

First it runs controlled B–G against its **disposable** HTTP process. Then it checks
the existing candidate's exact artifact/process start/argv/exclusive loopback
binding, current authority load, and direct B–E. It never starts the candidate.
Requests are serialized, at least1.1s apart, without retries. The direct adapter
does not request nginx's `/status/server-load.json`.

## Existing transaction integration

Use `Candidate.ready_with_adapter(evidence, python=..., runtime=..., sha256=...,
config=..., directory=...)` as the existing transaction's `ready` callback after
`candidate.capture`. It runs the pinned closed artifact as a fresh isolated
subprocess and consumes only that invocation's new durable receipt. It binds PASS
to candidate port/generation/PID/start/HTTP digest and re-verifies ownership and
both artifact pins before setting `direct_pass`. Failure never enables ingress.
Do not manually set `direct_pass`, reuse receipts or convert them into a portable
`ContractFixture`. The wrapper does not set external or owner acceptance flags.

Accepted matrix: B400, C400 (established safe ordinary behavior), D400, E403,
controlled F200, controlled G200 with native validation. F/G are always
`server_contract_fixture`; candidate result always has `owner_product_ready=false`.
External A–E and real Friends-app F/G/import/persistence remain separate gates.
The old generation retirement/rollback transaction is otherwise unchanged.

## Failure receipts

The stdlib bootstrap installs no alternate search path and guards deferred runtime
imports. Before returning it fsyncs owner-only `result.json` and its directory;
new-directory creation is also fsynced. Receipts include step ID, safe exception
class, allowlisted missing-module/importer, stack files/lines, transitive/entrypoint
classification, actual artifact digest, cwd/search roots, isolation/Python version,
and argv **shape** only. No exception message, locals, source lines, argument
values, request/response bodies, proofs, credentials or private identity IDs.
Per-probe receipts use the unchanged accepted durable redaction contract.

Existing evidence is never overwritten/reused. Storage failure returns exit2 and a
fixed redacted failure; no PASS is reported. Missing/corrupt `__main__.py` cannot
execute its own receipt writer: pre-execution artifact pinning and the caller's
durable failure event cover that boundary. No automatic retry or live hotfix.

## Local acceptance

`tests/test_readiness_adapter_packaging.py` launches `python -I` outside the checkout
from the exact deployed bundle tree; no imports are supplied by pytest's process.
It reproduces the original `provisioning` failure, removes every manifest Python
dependency, verifies durable/redacted failures, runs controlled B–G and candidate
B–E on temporary local listeners, exercises the transaction callback, and compares
repeat builds. `FC_TEST_READINESS_ARTIFACT` selects the final committed bundle;
`FC_TEST_HTTP_ARTIFACT`, `FC_TEST_SYNC_ARTIFACT`, `FC_TEST_GO` select accepted inputs.
The local candidate test exclusively owns18086 and fails rather than replacing an
existing listener. No production, Redmi, live Telemost or deployment is involved.
