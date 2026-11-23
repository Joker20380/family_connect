# 24 November 2026 — CONTROL-HA opaque legacy custody

## Selected gate and result

Continuation of HA-02V's [installed inventory](2026-11-24-control-ha-installed-inventory.md):
lossless legacy-prefix custody for the observed mixed cohorts, service-bearing archives
and adjunct/fenced evidence. This bounded contract is COMPLETE IN ISOLATION, not a
production backup, journal execution, schema migration or full-system recovery PASS.
No gateway SSH, service/timer change or production private-data export occurs here.

The implementation preserves opaque bytes, directory structure and basic metadata
without claiming historical signature/approval validation. It deliberately offers no
SQL import, filesystem restore, rebinding, pruning, replay or host-resume function.
The existing Q/V validators and their strict limits are unchanged.

## Format and trust boundary

[Source](../../scripts/control_ha_legacy_custody.py) accepts four explicit, nonoverlapping
local source roots: RU, NL1, NL2 and coordinator, plus the prior read-only inventory.
There are no default production paths or automatic host discovery. Caller-selected
roots and a census do not prove a source-host identity or a consistent snapshot.

- Recursively preserve every selected regular file and directory, including zero-byte
  lock files, empty directories, unknown filenames and nested coordinator adjuncts.
  Do not follow symlinks, accept hardlinks/special files or skip an unsafe entry.
- Preserve file bytes exactly, including invalid UTF-8/JSON and native service/start
  intents, fenced rollback registry overlays and opaque authorization envelopes.
  Only structural ledger/coordinator projections are parsed to compare with the census.
  No signed historical plan/profile/approval is interpreted or repaired.
- Bind full names, topology, file SHA256 and uid/gid/mode/device/inode/nlink/size/
  mtime/ctime metadata. Access times, ACLs, xattrs, mount configuration and objects
  referenced outside the selected roots are NOT a qualified filesystem image.
- Use AES-256-GCM with a fresh96-bit nonce and a dedicated MAGIC/purpose, distinct
  from recovery capsules. CustodyCheckpoint independently binds a caller-supplied
  identifier, inventory digest, complete manifest digest and ciphertext digest.
  Authentication is custody-key authentication, not original operator approval.
- Verify the independent checkpoint before returning private readback bytes in memory.
  Never derive a trusted checkpoint from the incoming bundle alone. Preserve the key
  and checkpoint separately in protected custody; no key or plaintext logger exists.

The readback object suppresses private repr and exposes a count-only summary:
OPAQUE_CUSTODY_VERIFIED; activation FORBIDDEN; host_resume/database_import
NOT_AUTHORIZED; history_validation NOT_PERFORMED; approval_custody NOT_ESTABLISHED;
live_barrier NOT_IMPLEMENTED; current_state_recovery NOT_QUALIFIED.

Unequal cohorts remain unequal; no history directory or missing approval is fabricated.
Pending owner markers and unknown ledger results can be preserved, never executed.
A historical bundle remains readable against its historical receipt; it cannot satisfy
a newer expected checkpoint and never becomes evidence of current live state.

The scanner compares metadata before/after reads and at completion. Ordinary concurrent
changes refuse, but this is not a lock, fsfreeze or atomic multi-host writer barrier.
Do not use this observation mechanism to bypass the still-pending consistency gate.

## Bounds and qualification

Limits refuse rather than truncate: four roots,32768 tree entries,4096 children per
directory, eight relative path components,4096 UTF-8 path bytes,1MiB per file,64MiB
aggregate raw file payload and128MiB encoded plaintext. Metadata-reader bounds can
refuse earlier. Actual production payload sizes and full private capture were not tested.

[Tests](../../tests/test_control_ha_legacy_custody.py) use the
[sanitized fixture](../../tests/fixtures/control_ha_installed_shapes.json): allowlisted
filenames, aggregate result counts and15/6/5 shape histograms from the prior census.
No operation/device identifier, raw private evidence, production signature or key is in
that fixture. Payloads and operation names are generated test data, not purported native
authorization or proof of correct production semantics.

| Full shape-corpus observation | Result |
| --- | --- |
| RU / NL1 / NL2 ledger entries | 366 /366 /172 |
| Common operations / common result conflicts | 172 /0 |
| Fenced rollback entries | 3 /3 /2 |
| Native-shaped archive directories | 904 |
| Preserved regular files / all directories including four roots | 8546 /917 |
| Complete source deletion before readback | PASS |
| Exact SHA256 equality for every file after deletion | PASS |
| Opaque payload / empty file / metadata / empty-directory preservation | PASS |
| Independent checkpoint / ciphertext tampering / stale substitution refusal | PASS |
| Automatic repair, SQL import, filesystem restore or host resume | FORBIDDEN |

71 tests PASS /0 skips:45 new custody tests and26 existing inventory tests. Another12
selected Q envelope/parser regression tests PASS /0 skips;48 other Q tests deliberately
deselected. Historical PostgreSQL/Patroni, client/platform/release or full recovery
suites were not rerun or claimed. The selected slice has no DB writer or release change.
Six changed documentation files/993 local links and whitespace checks PASS.

Tests also cover pruning with a newly calculated manifest, missing/extra cohort members,
modified current state, removed adjuncts, malformed metadata/parents/base64, symlink
ancestors/leaves, hardlinks/FIFOs, overlapping roots, bounds, concurrent modification,
fresh nonces, pending/unknown evidence and source-free readback. Subprocess execution
is forbidden in the no-executor test; Q rejects even a rewrapped custody receipt/bundle.

```sh
python -m pytest -q tests/test_control_ha_legacy_custody.py tests/test_control_ha_installed_inventory.py
python -m pytest -q tests/test_control_ha_recovery_bundle.py \
  -k 'invalid_json_errors_are_sanitized or hash_repin_does_not_bypass_aead or authenticated_but_invalid_documents_refuse'
```

Runs use the existing control/identity-lockfile environment. Private JUnit evidence is
outside Git at `/tmp/fc-control-ha-20261124/legacy-custody-tests.xml` and
`/tmp/fc-control-ha-20261124/legacy-custody-foundation-tests.xml`.
The full fixture's encrypted capsule is3,998,218 bytes in the recorded run; its key is
ephemeral test material, not a deployed backup/recovery key. No production ciphertext
or source capsule is committed. Durable off-host custody remains a separate gate.
Qualified source SHA256:
`d1d6b9909138123b2413e5760f6b4e86216c7f6e32190454a09125d78720832b`.

## Next gate, rollout and rollback

NEXT, not started: semantic validation of the actual installed completed scheduled,
service-bearing current operation, separately from this opaque history. Require native
three-node service receipts and gate provenance, current issuer/both publications/
five-table DB state, and fail-closed pending/unknown/stale inputs. Do not replay old
approvals or install source retention as an unreviewed fix. Only after independent
qualification can current semantics and opaque history participate in a stronger
recovery capsule; possession of this bundle alone must never authorize that import.

The journal block remains partial. Other HA-02 blocks are installed schema/live writer
barrier, full-system/off-host recovery and strict PostgreSQL/Patroni replication/RPO0.
Stage2 of5, RU dependence,8s/12s/paid120s and all-three-serving-node ACK remain unchanged.

Latest known deployment is still console
`sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`,
NL GeoIP collectors22 November20:53:48UTC, RU HTTP archive
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`,
and installed renewal source aggregate e9fd3175. Android126/catalog9 and invitation/
public artifact versions are unchanged; no new build, installation, public release,
catalog signing, host policy change or fresh health acceptance is claimed.

Rollback is to stop using/revert this source-only module; preserve any independent
custody receipt and native evidence. No server restart, old database restore, history
rewrite or cleanup is needed or authorized. Original dirty main work is preserved;
implementation stays on the existing metadata branch/worktree.
