# Bootstrap HELLO admission characterization

Status: **SOURCE_CHARACTERIZATION**, not FROZEN_BINARY_ACCEPTED.
Task: BOOTSTRAP-HELLO-ADMISSION-REPRO-1, 2026-10-15.

[Report](../../docs/releases/2026-10-15-bootstrap-hello-admission-repro-1.md)
separates source mechanism, research84 caller compatibility and historical binding.

## Inputs and scope

- Starting review commit: `2843b88252728902b23ca62d8df8c25914cdc5c8`.
- Server inputs: unchanged `../supervisor-20261015/baseline/carrier` and
  `../supervisor-20261015/frozen-candidate/carrier` from the published inventory.
- Client interpretation: retained exact research84 source, not root checkout.
  `source-bindings.json` records 32 necessary bindings and 11 newly published
  byte-identical source slices. Those slices are evidence, not an Android build.
- `results/compiled-source-manifest.json` records the actual selected source/test
  files in five mechanism packages. The executed client protocol, Family/TLS,
  reliability bridge and startupdiag files match retained research84 byte-for-byte.
  Entire snapshot trees are **not** identical: server carrier/seed observations,
  overlap/supervisor/acceptance files differ or are absent from research84.
- Unchanged production code is compiled only in disposable copies. No snapshot,
  product source, timeout, policy, workflow, installed binary or credential changes.

## Reproduce offline

From the review checkout, with Go 1.26.1 and dependencies already cached:

```sh
python3 research/bootstrap-hello-admission-20261015/run.py \
  --go /absolute/path/to/go \
  --work /tmp/fc-hello-characterization-unique-run \
  --race-count 3
```

The work directory must not exist. The runner sets `GOTOOLCHAIN=local`,
`GOPROXY=off`, `GOSUMDB=off`, a fresh build cache, and removes
`FC_FAMILY_TEST_FIXTURES`. It compiles `./bootstrap` with `seedacceptance` for
both variants, once normally and once with `-race`; it executes only `^TestRepro`.
There is no automatic retry after failure. Fixed repetition is 1 normal + 3 race
suite executions per variant; deadline/cancel/peer-close each have 12 observations
per suite, invalid/success each one. Expected B failure is a passing assertion.

Exact local paths, build/run commands, time bounds, toolchain environment, test
hashes, executable hashes, `go version -m`, exit codes and log hashes are in
`results/build-metadata.json`. These executable hashes identify new **test
executables**, not frozen gateway artifacts. No test executable is published.

## Test design

`admission_repro_test.go` exercises real Broker lifecycle transitions, real
Exchange/requestTransport, real Family/TLS and real startupdiag. The existing
bootstrap `pair`, `providerFunc` and `starterFunc` fixtures replace only the packet
carrier, external provider and dedicated gateway implementation. ACTIVE is reached
through Challenge/Create/Claim and the gateway's real `active` callback; no map or
state injection. Cancellation/Close channels control old-holder cleanup.

`tls_fixture_test.go` adapts the certificate fixture pattern from the retained
`familysession/session_test.go` (credential generator starting near line 71).
All credentials/identities/CRL are disposable, generated in memory per case;
only a temporary 0600 synthetic gateway profile is needed by SessionAuthorizer.
No credential/payload/identity values are logged. This is not PKI/provisioning or
CRL-writer work, and no real room or provider session is created.

Synchronization uses lifecycle channels and bounded ownership events. The error
test observes an actual blocked Family `Recv`/`net.Pipe` read using an in-memory
goroutine-stack predicate before triggering cancel/peer close; it does not inject
an error or pre-cancel Recv. No stack is printed or retained. Polling has a bounded
context, not a guessed sleep-to-ACTIVE. Tests are sequential. Fixed deadline
samples deliberately retain both read-deadline and context-cleanup race outcomes.

`observations.jsonl` contains all 736 structured records from the final run:
32 admission outcomes, 360 ownership events, 304 classification observations and
40 broker cleanup receipts. Ownership records precede their admission outcome in
suite order A/B/C/D; the following cleanup receipt completes that broker case.
Every opened Family endpoint is closed in test cleanup; Family stream Close joins
its bridge workers. Broker Close joins workers after releasing test cleanup gates.
No race-detector report, test timeout or unexpected failure occurred. This is not
an exhaustive global goroutine/leak proof outside the tested resources.

`classification-counts.json` groups all actual variants, not selected successes.
Raw stdout/build logs remain in the local work directory with published hashes;
the bounded structured records are sufficient to inspect every reported outcome.
Preliminary baseline-only runs also passed, before strengthening C ordering and
A/D no-wait assertions; they are not included in the final matrix counts.

Not covered: Android/JNI execution, Telemost/signaling/Pion/RTP/VP8, native packets,
dedicated network readiness, live lease renewal, production timings, historical
session attribution, installed/frozen-binary acceptance. The fixtures do not
establish correctness of those omitted layers.
