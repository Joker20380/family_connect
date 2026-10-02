# Inert artifact staging contract

This operator stage never starts services, enables timers/routes, reloads ingress,
executes a staged artifact, migrates a DB or refreshes authority. It does not authorize
deployment. Keep existing host-key verification, SSH accounts and approved host mapping.

Do not pass binary artifacts as base64 literals inside `python -` source programs.
That path inflates bytes by about4/3, mixes transfer with Python source ingestion,
and cannot execute a progress/receipt statement until the whole program is received
and parsed. A single `subprocess.run` timeout cannot distinguish connect, reception,
remote mutation, validation or receipt loss. Attempt16 preserved no such phase evidence;
do not label its historical cause network slowness or inadequate timeout by assumption.

Use the stdlib-only `scripts.friends_staging` operator instead. A small bounded receiver
program travels in the SSH command; artifacts travel as **raw bytes**, not executable
source, in one authenticated connection per bundle. No scp/rsync/tar dependency or
change to production SSH trust is required. Run RU and NL sequentially to obtain
separate rate/timing evidence; concurrency correctness is nevertheless tested.

## Manifest and commands

Build the local JSON list from accepted inventories, not from whatever bytes happen
to be present. Each item has `artifact_id` (flat filename), `source` (local path),
`bytes`, `sha256`, and optional `mode` (384/0600 default or448/0700 for an executable).
Verify the enclosing accepted inventory and its source provenance before making this
manifest. The helper rechecks every supplied local size/hash before connecting.
Do not include credentials, authority bundles, private keys, DBs or profiles.

```sh
python -m scripts.friends_staging --role ru \
  --manifest /private/operator-manifest.json \
  --parent /opt/apps/family_connect/restricted-materials-stage-20261001/EXISTING_ATTEMPT \
  --destination http-operator --evidence /private/fresh-local-receipts
```

NL uses `--role nl`, the existing NL inert attempt parent, `--destination native-checker`
and a manifest containing the approved checker, acceptance script and provenance.
Uploading these files does not run native authority validation. A later separately
authorized JIT operation must consume these pinned staged files, not resend them as
source literals, and validate current authority under its existing execution bound.

Before any later consumer runs, use the **same expected manifest** with `--inspect`
and a fresh local evidence directory. Exit0/READY requires a complete matching
inventory, all remote sizes/hashes/modes and a durable READY receipt. Do not infer
readiness merely from a directory, one executable, an old PASS or process exit0.

## Atomicity and recovery

The receiver permits only existing, owner-controlled parents below the inert staging
root; symlinks/traversal, duplicate artifact IDs, excessive sizes/budgets and unexpected
final-directory contents are rejected. It takes a nonblocking per-destination `flock`.
Two concurrent operators cannot write the same destination. The fixed host map is
RU185.251.89.19 and NL186.246.45.246; production runtime paths are not destinations.

1. Remote receiver emits CONNECTED before consuming the manifest/artifact stream.
2. Create a unique0700 `.DESTINATION.partial-ATTEMPT` quarantine directory and durable
   intent/manifest. Existing final destinations are never overwritten.
3. Receive each exact-length file into this directory; emit receiver-confirmed byte
   progress, flush/fsync, reread and verify SHA256 under a separate validation deadline.
4. Fsync the directory; rename the complete directory atomically to the destination;
   fsync the parent. Only then fsync `.staging-ready.json` and the attempt receipt.
5. Emit READY only after those durable writes. No artifact content is executed.

Failures retain quarantine and per-attempt receipt; no automatic deletion, repair or
blind retry. A new explicitly requested attempt may use the same manifest with a new
attempt ID, leaving failed partial bytes untouched. If a matching final directory is
already READY, exact reinspection returns READY without rewriting/retransferring it.
If the process exits after promotion but before the receipt, inspection returns
PARTIAL/COMPLETE_BUT_UNACCEPTED, never READY. This case deliberately needs operator
reconciliation; do not remove/adopt a directory automatically or invent a receipt.
An unknown response always requires inspection before another write.

## Bounds and safe receipts

SSH: BatchMode, StrictHostKeyChecking=yes, UpdateHostKeys=no, ConnectTimeout10s,
ServerAliveInterval5s/CountMax2. CONNECTED/remote-start deadline15s is distinct from
the transfer deadline. Keep inherited compression behavior; do not assume compression
will rescue a slow transfer. No ControlMaster/authentication configuration is changed.

For file size `n` bytes, conservative minimum rate `r` bytes/s:

- Transfer: `5 + 2*n/r` seconds, absolute (progress does not extend it indefinitely).
- SHA verification: `5 + 2*n/(8 MiB/s)` seconds.
- Per-file fsync and final promotion/receipt:5s each. Manifest receipt:10s.
  Local phase allowance:2s, without extending the overall operation bound.
- Default `r=256 KiB/s`; adjust only from fresh measured lower-bound rate evidence,
  not merely after timeout. Allowed rates64KiB/s–16MiB/s; per-phase maximum300s,
  aggregate remote transfer/fsync/validation maximum600s and overall operator maximum660s.
- No retry loop. EOF/hash mismatch/timeouts cannot promote incomplete data to READY.

Receiver/connection startup and each item persist safe role/ID, expected bytes/local
hash, quarantine path class, connect/transfer timestamps, confirmed byte count,
remote hash result, validation completion, atomic promotion result, elapsed times,
timeout phase, exception class and READY/PARTIAL/FAILED. Local receipts also pin receiver
source and preserve process exit. No credentials, body data, raw stderr, identity or
authority bundle is recorded. Safe hash/size/inventory checks are not a secret scanner;
the operator is responsible for selecting only approved public build artifacts.

## Regression / scope

`python -m pytest -q tests/test_friends_staging.py` runs locally, without SSH/secrets.
It covers normal/slow transfers, connect/mid-transfer/validation timeouts, hash mismatch,
exit after promotion before receipt, partial retry/idempotence, concurrent destination
ownership, local pin failure, manifest/path rejection and tamper detection. The existing
control CI runs this through its full pytest suite. Tests never enable restricted routes.

Staging READY is not native authority PASS, NL/RU runtime acceptance, real owner READY
or Stage5N closure. Do not start PROV-1 or FIELD/DIAG/OPS/beta automatically afterwards.
