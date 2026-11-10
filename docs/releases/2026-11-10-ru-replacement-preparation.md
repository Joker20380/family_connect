# RU transport replacement preparation —10 November2026

Selected task: **RU-TRANSPORT-REPLACEMENT-PREP**. Separate worktree from remote
main `87fbe744490499f7e72de807a29e9dd306da3d56`; parallel work preserved.
PR17 [deployment receipt](https://github.com/Joker20380/family_connect/pull/17#issuecomment-6765941574)
remains **DEPLOYMENT_FAILED_ROLLED_BACK_VERIFIED / ROOT_CAUSE_OPEN**.
No more PR16/17/paid123 rollout on the current RU.

## Deliverable

- Exact PR17 bundle/inventory/nested node members and qualified fixture inputs
  checked, no runtime or native rebuild. Offline native image and pinned Python
  wheelhouse accompany an allowlisted preparation package; no production state,
  keys, SSH configuration or private deployment helpers are included.
- Existing systemd/native fixture gains a finite replacement profile:63 records,
 20/49/5 registrations,600s ordinary cycles, live full-set comparison, explicit
  AWG DNS plus actual TLS/egress, lease loss/expiry/revoke, retained deny and one
  controlled stop/PID0/preflight/start. No diagnostic fault series or endless soak.
- Local preparation regressions cover input hashes/symlinks/archive members,
  distribution integrity, registration overlap, bounded orchestration and first
  failure exit. These are **not** replacement-node/native PASS.
  `test_ru_replacement_preparation.py` + existing `test_fleet_canary.py`:46 PASS;
  syntax, documentation links and whitespace checked. Packaged108/119 operator
  policy and reconciler help execute locally without opening a product registry.
- One [host handoff and cutover plan](../operators/ru-transport-replacement.ru.md)
  identifies the local-only RU HTTP registration dependency, full enrollment maps,
  signed catalog sequencing, profiles/keys, and per-node collector pins.

## Status and scope

**LOCAL_PREPARATION_READY; NEW_HOST_QUALIFICATION=NOT_RUN.**
One external resource is missing: an explicitly authorized independent host with
the specified access/OS/runtime capabilities. No new host is assumed or purchased.
No production SSH/readback or mutation, phone use, paid operation, NL change,
new runtime candidate, Android/G4 test, or change to8/12/120s occurred.

Saved serving evidence is dated10 November11:10–11:14UTC, not a fresh live query.
The old host's provider is not blamed by a fixture result. Even a future short
PASS is neither stability guarantee nor permission to switch users.

Private offline artifact/inventory and local verification receipt live under
`/mnt/data/fc-ru-replacement-20261110`; final digests identify the preparation
wrapper separately from runtime source377cfe8a. On qualification failure stop for
a separate control/recovery decision; do not resume the previous rollout series.
