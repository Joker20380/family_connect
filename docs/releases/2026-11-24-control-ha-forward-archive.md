# 24 November 2026 — portable encrypted forward-checkpoint inputs

## Scope and result

Continuation of the selected CONTROL-HA-20261123 journal/current-state task from
source77bc5a98, under existing development-only authorization. No next queued block,
SSH, writer stop, server change, production capture, real signing, release or deployment.

The [forward archive](../../scripts/control_ha_forward_archive.py) makes the existing
offline inputs portable instead of relying on in-memory objects or unencrypted config
sidecars. `seal()` returns encrypted bytes and their SHA256; `verify()` requires external
custody and returns the existing qualified-input object only after every forward check.
It writes/extracts no files, loads no captured code and does not activate any service.
No CLI, storage provider, upload or production trust/key registry was added.

## Format and independent custody

AES-256-GCM uses a fresh96-bit nonce and a distinct versioned domain. Associated data
binds the independently approved request hash. The ciphertext has a separate externally
pinned SHA256. The plaintext uses exactly five bounded length-prefixed frames, with no
compression, archive paths, pickle, implicit members or executable deserialization:

1. Exact canonical signed forward request.
2. Its exact Ed25519 signature.
3. Existing encrypted current recovery capsule, unchanged.
4. Existing encrypted opaque-history capsule, unchanged.
5. Strict JSON/base64 sidecars: both publications, both signed delegations, and all
   three saved renewal source/config maps.

Request/signature limits are16KiB/64bytes; recovery/history retain their existing
96/128MiB plaintext-derived ciphertext limits; sidecar JSON is at most32MiB. Each
length is checked before slicing/decoding; trailing/missing/oversized frames refuse.
Sidecars retain existing per-file/count/total limits and exact node coverage.

**Outside the archive, independently retained:** outer encryption key, both inner
capsule keys, trusted authorization public key, anchor, request hash, ciphertext hash,
checkpoint/CRL/per-gateway authority floors and trusted verification time. The archive
cannot supply or lower those values. All test keys are ephemeral, never release keys.
Keys must not be shipped with the archive or committed to Git/CI/logs. Losing required
keys or trusted pins is not recoverable by guessing them from the encrypted document.

Packing checks bounds and byte bindings but does **not** authenticate owner approval.
An archive can be sealed with an invalid64-byte signature; subsequent verification
must refuse it. Successful decryption is likewise not approval. The existing verifier
still checks signature/domain, independent request pin, expiry, monotonic floors,
source/config/node/trust bindings, both publications, current capsule and opaque history.
It keeps activation FORBIDDEN and database import/host resume NOT_AUTHORIZED.

The original short-lived qualification expiry is unchanged. This does not turn a
checkpoint into an indefinite disaster-recovery authorization. Do not lower floors,
ignore expiry, re-sign stale state or replay old operations to make a backup acceptable.
Source scope remains renewal modules/node config only, not controller config, all API/
gateway binaries, dependencies or evidence of a running process's loaded code.

## Qualification

Final local gate: **261passed,0failed,2skipped** in71.69seconds:

| Selection | Passed | Skipped |
| --- | ---: | ---: |
| New archive tests |59|0|
| Forward checkpoint, including new native portable scenario |99|0|
| Existing recovery capsule regression |58|2|
| Existing opaque-history custody regression |45|0|

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_control_ha_forward_archive.py \
  tests/test_control_ha_forward_checkpoint.py \
  tests/test_control_ha_recovery_bundle.py \
  tests/test_control_ha_legacy_custody.py
```

Uses the existing control/identity lockfile environment; no dependency change. The two
skips are existing real-PostgreSQL recovery cases, not archive tests and not a claimed
new PostgreSQL/import/release PASS. Prior329-test results belong to77bc5a98, not this run.

- A fresh isolated Python process receives only the encrypted artifact plus independent
  external keys/trust/floors after original capture directories are deleted. Fingerprints
  of every store, reference, artifact, bootstrap, history manifest and source/public byte
  map match. No parent-process candidate objects or captured executable code are used.
- Native renewal followed by a new certificate/consumed proof now runs both directly
  and through the archive. Source-removed isolated recovery retains exact DB/artifact
  bytes, refuses the used proof and issues against a fresh one; old-baseline import
  still refuses the advanced DB. No product database is touched.
- Tests reject corruption with a repinned ciphertext, wrong keys/request pins/signers,
  expired/stale state, lowered authority acceptance, substituted inner capsules and
  public/source sidecars, malformed lengths/base64/JSON and archive-supplied trust/floors.

Private logs/JUnit: `/tmp/fc-control-ha-20261124/forward-archive/`. No actual private
state, profiles, keys, encrypted capsules or raw evidence enter Git.

Documentation gate:6changed files,975links,0errors; external URLs inventoried, not
fetched. `git diff --check` passes. This is a source checkpoint, not a release or
deployment acceptance.

## Remaining gate and rollback

Selected task remains IN_PROGRESS. This closes portable encrypted custody of the
**already supported offline inputs**, not coherent production capture or full recovery.
Actual current authorization/source/publication/capture binding, installed schemas/all
writers/barrier, complete mandatory stores/keys, independently placed off-host custody
and strict PostgreSQL/Patroni quorum/RPO0 remain unqualified. No next queued block is
selected. Real capture still needs separately reviewed scope/abort paths before any
writer stop. The four stage2 acceptance blocks and subsequent HA-03..05 remain unchanged.

No built/installed/deployed/public/invitation version change or fresh health claim.
Known console image `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`,
RU HTTP archive `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`,
NL GeoIP22 November, Android126/catalog9 and8/12/120s/all-three-node ACK unchanged.
RU-independent control is not deployed.

Rollback: discontinue the new offline wrapper or revert its source checkpoint in a new
ordinary commit; retain its reader version with any private archived inputs. Existing
direct forward verification and inner capsule formats remain unchanged. No server change
needs undoing. Never restore old SQLite over later writes, replay history, weaken floors
or force-push. A future failed capture aborts before cutover; after new writes recovery
requires current state and fencing, not an obsolete baseline.
