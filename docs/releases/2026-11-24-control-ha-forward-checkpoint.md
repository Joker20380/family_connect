# 24 November 2026 — forward-checkpoint implementation handoff

Source `38a3ac27c524a37631be81b88d3dff00749b72e4` ordinarily pushed and independently
remote-SHA verified on `feature/device-technical-metadata-20261115`.
Authoritative implementation/full report: `/home/joker/.codex/worktrees/dad9/family_connect`.
This divergent old main is navigation only; preserve its four original dirty files and
six untracked paths. Previous ordinary main push was non-fast-forward against
`cb47bf230c6795cf21f4e6948253f49aa5377ed0`; no reset/force/reconciliation selected.

Owner explicitly accepted development of the forward-only current-state contract
without stopping services or making server changes. Development decision resolved;
original historical approval remains NOT_ESTABLISHED. No retroactive consent.

New `scripts/control_ha_forward_checkpoint.py` on the authoritative branch builds and
verifies a separate canonical request: domain-separated Ed25519 signature, independently
pinned request, externally retained sequence/CRL floors, exact encrypted current-state
and full opaque-history capsules, anchor/issuer/source/config/publication bindings and
bounded expiry. Only offline qualification is authorized. No actual signing authority,
production CLI, importer/resume API, service stop or remote capture is installed.
Existing old-equality import/audit gates remain strict and unchanged.

Complete unequal old archives, including unknown/pending historical content, remain
opaque and non-executable. Observed unsettled current markers refuse qualification;
absence of those markers is not proof of a coherent cross-store writer barrier.
Source identities are bound but not independently attested; second-node publication
semantics remain unqualified. Durable authorization-floor storage is external, not
provided by a read-only verifier. New-format PASS is not production recovery acceptance.

Final source gate:251 passed /3 optional PostgreSQL skips in69.25seconds:75 new contract,
56 unchanged current-audit,45 custody and75 maintenance tests. All new tests run with
zero skips; real PostgreSQL rehearsal is not newly claimed.5 changed source docs/963
local links and whitespace PASS. Private logs/JUnit remain under
`/tmp/fc-control-ha-20261124/forward-checkpoint/`, never Git.

Native synthetic renewal followed by a new certificate and consumed proof is captured;
after source removal, all DB/artifact bytes survive, an isolated recovered registry
refuses the old proof and accepts a fresh one. The old renewal binding still refuses
the advanced tables. This is not full installed-store/off-host restore or RPO0.

Same journal/current-state task IN_PROGRESS. Next work is actual-current source,
publication and capture binding, not another search for missing old approval.
The four stage2 blocks remain: journals partial; installed schemas/writer barrier,
full off-host recovery and strict quorum/RPO0 open. HA-03..05 follow; RU dependency
persists. No next queued block, production capture, deployment or writer stop authorized.

No SSH or fresh fleet-health claim. Installed console5ce82415, RU HTTP4e2df679,
NL GeoIP22 November, Android126/catalog9, public/invitation versions and8/12/120s/
all-three-node ACK unchanged. Full version hashes are in the authoritative report.

Rollback: discontinue the offline API or revert the source checkpoint with a new
ordinary commit. No deployed change needs undoing. Preserve current and old custody;
never restore old renewal/SQLite data over later writes. Future maintenance scope and
abort/recovery path require separate review before live capture/cutover.
