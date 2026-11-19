# N185 outline rollback — 19 November 2026

The owner rejected the last refinement: “верни все назад. получилось плохо”.
Only that refinement is undone; earlier gold/facelift/end-rounding work remains.
No new modelling or Family Connect task is selected.

## Restore and verification

Local project: `~/BlenderProjects/4Runner_N185_20261117/`.

- Before restore, the live Blender file is the saved outline revision, not dirty,
  with no running render. No intervening unsaved edits are discarded.
- The rejected main file is preserved as
  `4runner_n185_rejected_outline_20261119.blend`; other revision copies remain.
- `4runner_n185.blend` is atomically replaced by a byte-identical copy of
  `4runner_n185_before_outline_refinement_20261118.blend`.
- Restored/source SHA256:
  `974c198c3f17bf85bad96b8028c956747047c87e040fceca233349e79939e085`.
- The restored current file is reopened in the existing Blender instance, with
  embedded scripts disabled. Live readback confirms the canonical current path
  and absence of `outline_refinement_20261118`.
- The restored top-camera view is visually checked. No replacement geometry or
  further aesthetic adjustment is applied during rollback.
- Local receipt: `outline_rollback_20261119.json`. The earlier refinement's
  checksum manifest and renders are historical evidence of the rejected revision,
  not checksums/previews of the restored current file.

## State and limits

Rollback is complete; this is not approval of either model's likeness. Rejected
assets remain outside Git for recovery, not as the active model. Existing unrelated
working-tree changes are preserved. Family Connect build, installed/public/invitation
versions, catalogs, gateways and deployment state are unchanged. Source publication
remains separate from local model restoration; the existing divergent `main` must
not be force-pushed or reconciled implicitly for this task.
