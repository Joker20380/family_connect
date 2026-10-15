# Local reproduction only

Do not rerun exclusive writers in this sealed capsule. Copy scripts/exact source into
a new isolated capsule, preserve donor hashes and use a new private synthetic output
directory. Never use SSH/ADB/provider OAuth for this acceptance.

1. `prepare.py` verifies prior sealed checksums and creates exact Go baseline/source
   copies. It does not infer current runtime from old PID values.
2. Apply `seed-supervisor-behaviour.diff`, then `observability.diff` to that baseline,
   or inspect `candidate.bundle` and its local validation commits. No root dirty-tree
   checkout/reset. API components are excluded.
3. `validation.py prepare` copies production source into a distinct validation tree,
   adds the sealed local SFU/network adapters, and builds the test driver around the
   production supervisor. That tree must never be packaged/deployed.
4. `validation.py accepted-batch` creates fresh synthetic credentials **after runtime
   approval** with the unchanged fixture policy; runs real Pion/supervisor race×3,
   security/lease/observer race×3 for candidate/baseline, then full differential tests.
   Pinned Go1.26.1, GOPROXY=off, local GOCACHE, no external dependency fetch.
5. `validation.py baseline-proof` runs the direct before-patch server TCP closure
   measurement×3 with separate fresh synthetic credentials. Client EOF timing is not
   assumed: server-side closure and subsequent fixture cleanup are distinguished.
6. `validation.py storage-race3 source '^TestSeedRecovery(Storage|WriteFailure|Receipts)' ./cmd/bootstrap-broker`
   checks actual pruning beyond64, preserved foreign file, malformed old receipt,
   0700/0600, write failure and concurrent enqueue. It needs no credentials or network.
7. `finalize.py` checks exact failure-set equality, protected source hashes and privacy,
   seals the local Git stack/bundle and builds the untagged gateway. Do not repeat it
   over an existing candidate-repo. It never pushes, starts or deploys the binary.
8. `closeout.py` checks production recovery events against the schema, removes only
   this task's private synthetic state, records document hashes and writes SHA256SUMS.

Exact per-command source hashes, arguments, elapsed time, return codes and JSONL results
are retained under receipts. Historical expired-credential/loopback-denial/compiler
iterations are retained, not passed off as product regressions or final acceptance.

The full suite remains NOT_GREEN with identical preserved diagnostic/source-guard
failures; real rejection boundaries and new targeted gates pass. No assertion from the
existing production suite was weakened. A new before-fixture's invalid5s client-EOF
assumption was replaced with the observable server TCP close contract, documented in
the differential receipt.
