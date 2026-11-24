# 24 November 2026 — forward-checkpoint renewal source custody

Historical source checkpoint77bc5a98. The subsequent
[portable archive](2026-11-24-control-ha-forward-archive.md) encrypts the complete forward
input set, including these source/config sidecars. Limits/results below belong to this
earlier in-memory source-custody change; full production recovery is still unqualified.

## Scope and result

Continues the selected CONTROL-HA-20261123 journal/current-state task from sourceb105033d,
under existing development-only authorization. No next queued task, SSH, server change,
writer stop, production capture, real signing, import/resume or deployment.

[Source custody](../../scripts/control_ha_forward_sources.py) is now mandatory in
[forward verification](../../scripts/control_ha_forward_checkpoint.py). Previously a
caller could supply two source/config hashes per node without any corresponding bytes.
Verification now checks the exact saved node configuration and declared renewal files
against the independent signed request, before opening the recovery capsule.

- Exact RU/NL1/NL2 coverage; NL1 maps explicitly to native slotNL. Each node's role,
  schema1, gateway set and anchor must agree with its checkpoint context.
- Configuration bytes, every declared module and the aggregate hash must match. The
  known legacy14-module base is mandatory; extra declared modules are allowed only with
  exact matching bytes. Missing/extra/unbound files, path escapes and duplicate JSON refuse.
- Each config/module is bounded to1MiB, at most128 modules/node and16MiB across the three
  material sets. Mutable byte buffers refuse; nested input maps are copied. Source
  substitution after verification cannot replace the returned approved bytes.
- `collect(config_path, runtime)` reads only explicitly supplied local paths, with the
  existing bounded no-follow reader. It rejects symlinks, hardlinks, nonregular files,
  undeclared `.py` entries and observed file/directory changes. Paths inside a config
  are never followed. It neither imports retained Python nor starts a process/service.
- `QualifiedCheckpoint.source_materials` retains exact private source/config bytes with
  repr suppressed. Summary reports `source_identity=RENEWAL_BYTES_VERIFIED_OFFLINE`,
  `installed_source=NOT_ATTESTED`, and the renewal/node-config-only scope.

No wire-format/version or production dependency change. Existing unreleased requests
still need their exact approved source/config bytes at verification; there is no default
empty-material compatibility path. Existing old-equality auditors/importers are unchanged.
Source hashes alone do not reconstruct missing files. Material must be kept in protected
private custody alongside other inputs, never logs/Git; no encrypted source archive,
independent off-host backup, persistent replay-floor store or activation permission is
provided by this in-memory API. The two existing encrypted capsules are unchanged.

## Qualification

Final local result: **329passed,0failed,0skipped** in41.49seconds:

| Selection | Passed |
| --- | ---: |
| New source-custody tests |72|
| Forward-checkpoint integration |98|
| Both-publication regression |77|
| Unchanged no-follow reader/inventory regression |26|
| Unchanged strict current audit |56|

```sh
/tmp/fc-control-ha-20261123/venv/bin/python -m pytest -q \
  tests/test_control_ha_forward_sources.py \
  tests/test_control_ha_forward_checkpoint.py \
  tests/test_control_ha_forward_publications.py \
  tests/test_control_ha_installed_inventory.py \
  tests/test_control_ha_current_audit.py
```

Uses the existing control/identity lockfile environment. Tests cover native development
module bytes, missing/extra/substituted material, exact config-byte identity, new signed
requests with wrong node/trust, bounded reads, symlink/hardlink/FIFO, metadata races,
non-execution sentinel, source removal and caller mutation. The existing full checkpoint
fixture still preserves captured DB/artifact/history bytes and consumed/fresh-proof checks.
No new PostgreSQL, complete recovery or release acceptance is claimed.
Documentation:6 changed files,972 links,0 errors; external URLs inventoried, not fetched.
Whitespace gate `git diff --check` passes. Sources/tests/docs only; no build/private state.

Additional retained-source check uses Gitfcb311641457165405dc85fa070aaa4b1464e185. Its
packager's MODULES tuple is parsed as AST, not executed. All14 files reconstruct aggregate
`e9fd31754bdf50c95842a1644f86ddb328b839ec1e0c9454daf08d3e9d17f0cc`, matching the already
recorded three-host observation24 November00:34:17–00:34:20UTC. Local collection and
source-removed verification pass with **synthetic node configurations/anchor/identities**.
This proves compatibility with those retained source bytes, not current production
configuration, new host evidence or historical approval. No private production data read.
Private receipts: `/tmp/fc-control-ha-20261124/forward-sources/` (`qualified.xml`,
`qualified.log`, `retained-source-check.json`); no raw private evidence enters Git.

## Remaining gate and rollback

Offline source byte identity is not evidence that a running process loaded those bytes,
nor a writer barrier. Controller config, API archive/gateway binaries, dependencies,
installed-schema/writer census, live publication origin and gateway private keys remain
outside this check. It does not independently attest who captured a source or when.
Node configuration is checked for source/node/trust bindings, not full runtime semantics.

Selected task remains IN_PROGRESS. The next acceptance boundary is independently bound
actual current inputs and a qualified coherent capture/recovery, not another search for
missing old approval. Actual capture needs known writers/schemas and a separately reviewed
maintenance scope; this change neither starts that queued block nor authorizes downtime.
The fixed four stage2 gates remain: journals partial; installed schemas/coherent writer
barrier, full independent off-host restore and strict PostgreSQL/Patroni quorum/RPO0 open.
No calendar ETA or completion percentage inferred from passing tests. HA-03..05 follow.

No built/installed/deployed/public/invitation version change or fresh health claim.
Known console image `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`,
RU HTTP archive `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`,
NL GeoIP22 November, Android126/catalog9 and8/12/120s/all-three-node ACK unchanged.
RU-independent control is not deployed.

Rollback: stop using the offline helper or revert this source checkpoint in a new ordinary
commit. No server change needs undoing. Keep current inputs and opaque old history; never
restore old SQLite over later writes, replay old operations, weaken checks or force-push.
Future capture failure must abort before cutover; after new writes require current-state
recovery and fencing rather than an obsolete baseline.
