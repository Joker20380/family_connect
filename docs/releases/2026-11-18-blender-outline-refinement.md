# N185 outline refinement — 18 November 2026

**Superseded19 November: OWNER-REJECTED / UNDONE.** The owner requested rollback.
The active model is restored from the pre-outline checkpoint; the geometry and
checks below describe the rejected historical revision, not the current model.
[Verified rollback](2026-11-19-blender-outline-rollback.md).

## Scope and references

The owner requested more believable vehicle outlines in the open Blender scene.
This continues the gold [end-rounding checkpoint](2026-11-18-blender-end-rounding.md),
not a product task or acceptance of the earlier likeness. Local references are the
retained Toyota 2002 factory front-three-quarter and near-side photographs, the
2001 Sport photograph, factory side drawing and original custom-stance reference.
The retained source links and trim limitations remain in the preceding checkpoint.
No paid generation, external asset upload or new dependency is used.

## Geometry changes

- The front upper cabin moves forward to reduce excessive windscreen rake; a
  follow-up correction keeps the B-pillar at its existing station rather than
  leaning the whole window assembly.
- Bonnet crown, nose falloff and roof crown receive small continuous adjustments.
  Side/rear roof edges fall away more gently from the central roof surface.
- Side shoulders, lower door sections and handle surroundings receive restrained
  stamped-section curvature rather than additional decorative strips.
- Wheel-arch upper corners are less circular and the sides slightly wider. The
  surrounding body and trim follow the same fields; wheel/axle positions are fixed.
- Mirror housings/glass are modestly enlarged together; front wipers move forward
  out of the windscreen surface. Gold, lifted stance, OEM-pattern five-spoke wheels,
  scoop and two low-profile crossbars remain.

These are reference-guided modelling controls, not measured Toyota radii. Visible
meshes, curves and trim are transformed consistently in body-root coordinates;
existing custom normals are transformed with inverse-transpose Jacobians.

## Checks and local artifacts

Local project: `~/BlenderProjects/4Runner_N185_20261117/`.

- Active/current: `4runner_n185.blend`.
- Separate revision: `4runner_n185_outline_refined.blend`.
- Pre-edit rollback: `4runner_n185_before_outline_refinement_20261118.blend`.
- The previous `4runner_n185_2001.blend` remains an earlier checkpoint, not a
  second alias for this new revision.
- Scripts, notes, checksums and current `hero.png`, `side.png`, `front.png`,
  `rear.png`, `top.png`: `outline_refinement_20261118/`.
- 347 visible meshes checked; zero non-finite vertex coordinates.
- Zero mirrored nearest-vertex error for paired lower body, front shoulders,
  front door glass and rear door glass. This is a selected-pair check, not a claim
  that asymmetric fittings such as the antenna are symmetric.
- Wheelbase2.674999952m; body-root lift0.170000002m; four tire carcasses/two crossbars.
- Sampled minimum Jacobians0.81415/0.81482 for the two incremental fields remain
  positive. This detects field folding, not all possible mesh intersections.
- Front-three-quarter, side/front orthographic, rear and top renders inspected;
  final images use EEVEE64 samples at1500×1000. Front orthographic is a body/front
  inspection view, not a complete antenna/tire-extremity framing.
- Verification JSON is retained in the blend scene property
  `outline_verification_20261118`; incremental scripts must not be replayed onto
  the finished scene or treated as a build-from-empty recipe.
- The three-view render batch exceeded the MCP180s response timeout. It was not
  replayed: subsequent readback confirmed the final camera and no running render;
  all five completed PNGs were checked and visually inspected before saving.

## Rollback, publication and remaining checks

Open the separate pre-refinement blend to roll back. All blends, local scripts,
reference photographs and render images remain outside the Family Connect Git
repository. Only sanitized checkpoint documentation is committed here; unrelated
existing working-tree changes are preserved. Repository push is separate from
the local Blender save and must not be described as successful without verification.
At entry, local `main` is18 commits ahead/294 behind its recorded upstream; no
merge, rebase, reset, force push or unrelated source checkpoint is part of this task.

Owner likeness acceptance remains **OPEN**. This is not OEM CAD, a scan, a watertight
printing shell or a manufacturing-tolerance model. Interior/underbody remain
simplified; exhaustive intersection testing and whole-vehicle dimensional
requalification are not claimed. No Family Connect build, installed/public/invitation
version, installer/catalog, gateway, server policy or deployment changes.
