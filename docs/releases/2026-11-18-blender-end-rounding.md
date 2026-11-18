# N185 rounded ends and panel fit — 18 November 2026

## Selected scope

The owner identified overly straight front/rear ends in plan, unlike the rounded
N185, and remaining panel mismatches. This follows the rejected-detail correction
recorded in [the headlamp checkpoint](2026-11-18-blender-headlamps.md); it is not
owner acceptance of that checkpoint or authorization for a Family Connect task.

Dependencies: existing Blender5.3.0 GUI, safe-mode loopback MCP and the saved gold
2001-style N185 scene. Gate: preserve rollback, compare retained reference views,
revise curvature and joins, inspect front/rear/top/close renders, check symmetry
and fixed dimension anchors, save editable files. Owner likeness acceptance is OPEN.

## Reference and geometry

- Toyota's [late-generation press photographs](https://media.toyota.ca/en/albums/2002/2002-toyota-4runner.html)
  show the installed front corners and the rear quarter/liftgate transitions.
- The retained [Toyota N185 catalogue scan](https://www.japanclassic.ru/en/booklets/438-toyota-hilux-surf-1999-rzn180-kzn185.html)
  supplies the small factory top-view diagram. Its JDM trim/spare-wheel differences
  are not copied onto the US-style rear.
- A shared symmetric field curves the visible front/rear body, glazing, optics,
  trim and bumpers together. The centre bumper crowns and axle locations stay fixed.
  Added sweep at710mm off centre is about66mm front/59mm rear; these are visual
  reconstruction controls, **not measured Toyota radii or drawing accuracy**.
- Front quarters use continuous shoulder/side surfaces instead of overlapping
  small upper corner caps. Bonnet nose and lower lamp aprons are rebuilt. Coplanar
  internal seam caps causing bright artifacts are disabled and normals matched.
- Rear door corners are separated from the lamp surrounds; upper shoulders and
  lower wrapping quarter panels replace protruding/flat corner pieces.
- Gold, OEM-pattern five-spoke wheels, two crossbars, scoop and lifted stance remain.

## Validation and artifacts

Local folder: `~/BlenderProjects/4Runner_N185_20261117/`.

- Current: `4runner_n185.blend`; matching revision copy: `4runner_n185_2001.blend`.
- Rollback: `4runner_n185_before_end_rounding.blend`, saved before this revision.
- Front/rear three-quarter, top and headlamp-close render inspection; intermediate
  artifacts identified a front shoulder reflection break and overlapping seam
  caps, which were revised rather than hidden by a different camera.
- Finite coordinates checked on347 visible meshes. Main glass, front-quarter and
  rear-lower-quarter mirrored vertex comparisons return zero error after explicit
  paired topology reconciliation (one independent merge initially differed).
- Wheelbase2.675m; centre bumper envelope4.654999971m; four wheels/two crossbars.
- Shared deformation sampled minimum Jacobian0.5623 remains positive; this guards
  against folding by that field, not against every possible model intersection.
- Visible clear headlamps still have no photograph texture. Materials and lenses
  remain an EEVEE appearance approximation, not optical/photometric simulation.
- Local evidence: `scripts/end_rounding`, `end_rounding_sources.json`,
  `rounding_verification.log`, current render files and `checksums.sha256`.

The current render set is `hero.png`, `front_2001_detail.png`, `rear.png`, `top.png`
and `headlamp_detail.png`. Other side/front/clay views are older checkpoints, not
misrepresented as fresh validation. Incremental source scripts are not a safe
build-from-empty recipe and must not be replayed onto the finished scene.

## Rollout and remaining checks

Local Blender revision only. Family Connect built, installed, public and invitation
versions, catalogs, gateways and deployment state are unchanged. Restore the separate
pre-rounding blend to roll back. Private assets, photographs and blends stay outside
Git; only sanitized documentation belongs in this repository.

This is not Toyota CAD, a measured scan, a watertight printing shell or an accepted
exact replica. Interior/underbody remain simplified. Whole-model manufacturing
tolerances and exhaustive intersection testing are not claimed; owner likeness
review is still required. Repository publication is separate from saving the blend
and remains subject to the existing divergent main history.
