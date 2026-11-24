# 24 November 2026 — portable forward-checkpoint archive handoff

Source `75ad8011cf32893a2f283f6f78e1d469a97ddfd1` ordinarily pushed and independently
remote-SHA verified on `feature/device-technical-metadata-20261115`.
Authoritative implementation/full report: `/home/joker/.codex/worktrees/dad9/family_connect`.
Old main remains navigation only; four original dirty files and six untracked paths
are preserved separately. Previous ordinary main push rejected non-fast-forward against
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`; no force/reset/reconciliation selected.

Selected CONTROL-HA-20261123 journal/current-state development continues. No next queued
task, SSH, writer stop, server/config/policy change, real signing, production capture,
import/resume or deployment. Existing offline authorization is not a maintenance permit.

New `scripts/control_ha_forward_archive.py` seals the exact signed request/signature,
existing encrypted recovery/history capsules and both publication/delegation plus all
renewal source/config sidecars into one bounded AES-256-GCM artifact. Fixed ordered
length-prefixed frames reject missing/extra/trailing/oversized inputs; no compression,
executable deserialization, retained-code execution, filesystem extraction or upload.

Outer and both inner keys, trusted signer/anchor, request/ciphertext pins, verification
time and checkpoint/CRL/authority floors stay independently outside the artifact. Never
ship keys with the archive or commit private material. Packing checks byte bindings but
is not signature approval. Reading repeats the existing forward verifier; expiry and
all replay protections remain mandatory. Short-lived qualification does not become an
indefinite recovery authorization. Import/resume remain NOT_AUTHORIZED, activation
FORBIDDEN and full recovery NOT_QUALIFIED. Existing direct verifier/inner formats unchanged.

Final gate:261passed,0failed,2skipped in71.69seconds: archive59, forward checkpoint99,
recovery58passed/2skipped, opaque-history custody45. All59 new archive cases plus the
added native portable scenario run without skips. The two existing real-PostgreSQL
cases remain unqualified, not hidden as a new PostgreSQL/release PASS.
Fresh isolated Python process reads only encrypted artifact plus external custody after
deleting original capture directories; all store/reference/artifact/bootstrap/history/
source/public fingerprints match. Native recovered registry refuses a consumed proof,
accepts a fresh proof and still rejects old-baseline equality after later writes.
No production database is read or restored. Six source docs/975 links/0 errors and
whitespace PASS; external URLs inventoried, not fetched. Private receipts:
`/tmp/fc-control-ha-20261124/forward-archive/`, never Git.

Staged navigation gate:3files/380links/0errors and whitespace PASS. Original unstaged
changes and all six untracked files match the retained baseline exactly. Source push
is verified independently of this divergent-main navigation checkpoint.

This is portable custody of already supported offline inputs, not full backups or actual
coherent production capture. Selected task remains IN_PROGRESS. Four stage2 acceptance
blocks unchanged: journals/actual-current bindings partial; installed schemas/all writers
and coherent capture, full independent off-host current-state recovery, strict PostgreSQL/
Patroni quorum/RPO0 open. Actual authorization/source/publication/capture evidence is still
required. No automatic switch to a queued block or guessed calendar ETA. HA-03 fencing,
HA-04 failover and HA-05 cutover follow. RU dependence persists.

No built/installed/deployed/public/invitation version change or fresh health claim.
Known console image `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`,
RU HTTP archive `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`,
NL GeoIP22 November, Android126/catalog9 and8/12/120s/all-three-node ACK unchanged.

Rollback: discontinue the offline wrapper or revert its source checkpoint in a new
ordinary commit; keep the reader version with privately archived inputs. No server
change needs undoing. Never restore old SQLite over later writes, replay old history,
weaken floors or force-push. A future capture failure aborts before cutover; after writes
use current-state recovery and fencing, not an obsolete baseline.
