# Local Blender N185 surface revision — 18 November 2026

## Selected scope

The owner rejected the previous reference reconstruction as crooked and too angular.
This revision addresses the actual mesh surfaces, joins and normals rather than
using extra accessories or a lighting change as a substitute for geometry work.
It remains a visual reconstruction: owner likeness acceptance is unconfirmed,
and no original Toyota CAD, manufacturing accuracy or complete internet coverage
is claimed.

Blender5.3.0, MCP for Blender2.3.0, the loopback listener and upstream safe mode are
unchanged. No Family Connect source, version, service, installer, catalog, deployment
or release gate changed. Unrelated dirty repository changes remain untouched.

## Geometry changes

- Lower body uses continuous width profiles instead of piecewise flat-tangent
  interpolation; the arch extensions blend back into those surfaces.
- Hood and wings share a compound surface definition. A rolled front hem and
  formed cowl close the previous openings at the grille and windscreen.
- Upper side panels contain window apertures, replacing separate raised metal
  frames. Glazing curvature, gaskets, B posts and diagonal C pillars are retained.
- The roof has a rounded transverse crown and softened front/rear profile corners.
  A/D returns terminate at the actual glass and header boundaries.
- The upper paint structure is joined into one closed surface using a4mm voxel
  union, local smoothing and adaptive tessellation. Original editable surface
  patches remain in disabled collection13A; the union is collection13. This
  removes intersecting sheet boundaries, not a claim of4mm dimensional accuracy.
- Front/rear bumpers use rounded swept cross-sections with consistent orientation,
  replacing the old seven-vertex loft and its irregular chrome reflections.
- Mirrors use welded quad surfaces with a convex nose. Front corner lamps wrap
  around the wing; optical panels have interior tessellation and explicit normals.
- Wheelhouse liners follow the revised arch shape. Wheel locations and the
 2675mm wheelbase are preserved. Existing cabin and undercarriage detail is reused.

## Local files and rollback

Directory: `~/BlenderProjects/4Runner_N185_20261117/`.

- `4runner_n185.blend`: current scene, opened in the existing Blender GUI.
- `4runner_n185_surfaced.blend`: separate copy of this surface revision.
- `4runner_n185_before_surface_rebuild.blend`: rejected angular version, saved
  before disruptive edits; reopen this file to roll back.
- `hero.png`: final closed-upper-body colour view. `side.png`, `front.png`,
  `rear.png`, `top.png`: surfacing review views made before the final upper-body union.
- `surface_clay.png`: material-override inspection of the same geometry.
- `before_surface_rebuild.png`: previous hero render for comparison.
- `scripts/07` through `scripts/13` incremental revision scripts and their helpers;
  these are source records, not idempotent scripts to rerun on the finished scene.
- `sources.json`, `README.txt`, `surface_verification.log`, `checksums.sha256`.

All blend files, images and modeling scripts stay outside the Family Connect Git
repository. The older generic draft also remains in its original project directory.

## Validation and reference limits

The MCP code guard accepts the revision scripts. Readback after the main revision:
814 scene objects,424 meshes,476839 mesh vertices including retained source patches,
0 non-finite vertex coordinates and0 non-finite corner normals. The unified upper
body has259432 vertices,295370 faces,0 boundary edges and0 nonmanifold edges; this
check applies to that component, not the whole vehicle. Measured wheelbase
is2.674999982m; chrome bumper
envelope length is4.654999971m. These are selected anchors, not whole-body accuracy.

EEVEE is used for the final2000×1375 colour view and smaller orthographic, rear/top
and clay inspections. Renders are inspected visually; a successful render command
alone is not treated as a likeness acceptance. Material override is removed and
the hero camera restored before the final save.

Existing Toyota brochure, catalogue diagram, press-photo and owner-photo sources
remain those documented in [the reference checkpoint](2026-11-17-blender-n185.md).
For reflection inspection, the packed
[Studio Small09 HDRI](https://polyhaven.com/a/studio_small_09) by Sergej Majboroda /
Poly Haven is added under CC0. It provides lighting, not vehicle geometry.

Remaining limitations: exact likeness still needs owner review; original diagram
resolution limits surface reconstruction; aftermarket stance and equipment are
estimated. Headlamp optical texture contains source-photo reflections. Interior
and underbody remain simplified. This is not a certified watertight printable shell,
animated rig, engineering model or physically complete glass simulation.

The owner subsequently requested a dedicated2001 facelift pass for headlights,
both bumpers, scoop hood and liftgate. That is a following local revision, not
acceptance of the present fascia. `4runner_n185_surfaced.blend` is its rollback.

## Source checkpoint boundary

Only this sanitized report and selected STATUS/PLAN additions are staged. The
existing divergent main branch is not reset, rebased, merged or force-pushed for
this modeling task. An ordinary push rejection is reported, not treated as success.
