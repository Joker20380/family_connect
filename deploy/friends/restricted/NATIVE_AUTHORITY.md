# Offline native authority prerequisite

This checker is an operator prerequisite, not a gateway service, issuer, grant
manager or replacement for Python/Android validation. No production operation is
authorized by this document. Attempt #11 remains failed/rolled back; do not retry
deployment automatically.

## Source and scope

`carrier/cmd/native-authority-check/main.go` calls the unchanged
`carrier/familysession.Configuration` and native peer authorization callbacks. It
validates gateway/owner X.509 chains, current validity, Family/role/key bindings,
CRL signature/revocation/floor and revision-floor compatibility. It then verifies
negative Family, revision and CRL variants. This is not a TLS possession handshake.

Inputs are an existing private gateway profile and a public owner validation
certificate. The tool never issues credentials, creates a room, modifies a grant,
refreshes authority or resets floors. Delegation signature/sequence and current
DB grant/admission remain required separate producer prerequisites. Actual device
delivery also requires `wholedevice.ValidateDelivery`/`DeliveryMaterial` and the
Android persistent `RestrictedCache` checks.

These sequence spaces are independent:

- Delegation sequence increases when signed delegation changes; it is not a device
  revision floor. Delegation2/grant1 is not automatically stale if minimum revision1
  and current membership permit it.
- Device certificate revision must meet the configured minimum and match the
  producer's current grant when issued/delivered. Native TLS is stateless: retained
  history is enforced through supplied floors, signed CRL and the client cache,
  not a hidden database inside `familysession`.
- CRL number must meet the supplied CRL floor; a newer CRL than the floor is valid.
- Cache rollback/conflicting same-issued content is rejected by the existing
  client cache. A later legitimate refresh at the same grant revision is allowed.

The historical untracked checker incorrectly set its negative revision floor to
`profile.minimum_revision + 1`. For attempt #11 that is2, equal to the valid owner
revision2: acceptance is correct, the assertion that it must reject is wrong.
The corrected negative uses **validated peer revision + 1**. Likewise the CRL
negative uses **validated signed CRL number + 1**, and the wrong-Family negative
must actually differ from the profile. All three false-negative assumptions have
offline regression cases. Unrepresentable integer successors fail closed with a
safe classification, never wrap or skip a negative.

No production validation predicate is relaxed. Actual expired material still
fails at the actual clock. Historical debugger clock replay is evidence tooling
only; there is **no clock override flag** in the checker or deployment wrapper.

## Clean reproducible build

Use the full accepted commit containing the checker, not a branch name or dirty
worktree overlay. The packager exports only tracked source from that commit into
a new temporary directory and builds outside checkout, with CGO disabled and
locked Go1.26.0/linux-amd64. Network module access is disabled.

```sh
python scripts/package_native_authority_check.py \
  --revision FULL_ACCEPTED_COMMIT \
  --go /path/to/go1.26.0/bin/go \
  --output /protected/new-checker-bundle
```

`provenance.json` records source commit/archive hash, per-file source inventory,
Go/compiler/assembler/linker hashes, flags/build metadata and hashes for the binary
and standalone Python acceptance adapter. Build twice in separate export/output
directories and compare artifact hashes. Neither bundling nor a local PASS deploys
the binary. Existing sync/HTTP archives are not changed by this gate.

## Durable execution contract

After a separately authorized operator has installed and pinned accepted components,
invoke this **before** NL/RU runtime startup, after current Python authority checks:

```sh
python -I /protected/new-checker-bundle/native_authority_acceptance.py \
  --binary /protected/new-checker-bundle/native-authority-check \
  --sha256 EXACT_ACCEPTED_BINARY_SHA256 \
  --profile /protected/existing/gateway.json \
  --certificate /protected/existing/canary-validation.pem \
  --receipt /protected/new-owner-only-evidence/native-authority.json
```

The native binary takes exactly those two material paths; it uses current time and
prints one bounded JSON object with `version,status,stage,reason,object,comparison`.
Failure stages distinguish input/configuration, device parse/chain/admission,
gateway parse/chain/binding and each negative. Values are fixed safe enums, never
raw Go/X.509 errors, subject IDs, certificates, key material, paths or OAuth.

The standalone adapter pins the binary, bounds execution to10s, suppresses raw
stderr, validates the JSON schema and exit/status consistency, and checks the
artifact again after execution. It file+directory-fsyncs a new0600 receipt before
returning/printing any verdict. Unknown/malformed/oversized output, timeout,
artifact mismatch/change and persistence failure forbid PASS. Existing receipt
paths are never overwritten or automatically rerun. Future orchestration must
consume this adapter, retain the receipt **before** rollback, and never substitute
Python-only acceptance, suppress a failed negative or retry blindly.

## Focused checks

```sh
go test ./cmd/native-authority-check ./familysession ./wholedevice
FC_TEST_GO=/path/to/go1.26.0/bin/go python -m pytest -q \
  tests/test_native_authority_acceptance.py tests/test_native_authority_compat.py \
  tests/test_friends_restricted.py
```

Go tests use synthetic keys and a deterministic virtual test clock. Cross-language
tests create disposable authority with the same value classes, and exercise the
real Python grant/CRL/issuance machinery, old/new native tools and shared delivery
parser. JVM `RestrictedCacheTest` covers1→2/CRL19, future revisions, persistence,
rollback and conflicting content. No Android build/device access is needed.
The legacy source under `testdata/legacy.go.txt` is regression evidence only,
not an installable/current prerequisite.
