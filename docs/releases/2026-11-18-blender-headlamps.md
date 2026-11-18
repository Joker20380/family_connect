# N185 clear-glass headlamp rebuild — 18 November 2026

## Selected task

The owner rejected the headlights in the [previous gold facelift checkpoint](2026-11-18-blender-2001-facelift.md).
This pass replaces that treatment rather than declaring it accepted. Scope is the
main headlamps, adjoining corner lights and their fit against the grille, bonnet
edge and front wings. Gold paint, OEM-pattern wheels, two roof crossbars, scoop,
rear work and off-road stance remain. No Family Connect task or deployment runs.

Dependencies: the existing Blender 5.3.0 GUI and guarded loopback MCP connection;
the prior editable gold N185 scene. Completion gate: inspect actual close reference
photographs, rebuild the visible optics, inspect close/front/three-quarter renders,
verify paired geometry and save a separate rollback plus the updated blend.
Owner likeness acceptance remains OPEN; this is not Toyota CAD or photometric design.

## Reference findings

- [Toyota 2001 US brochure](https://www.auto-brochures.com/makes/Toyota/4Runner/Toyota_US%204Runner_2001.pdf)
  and [official 2002 exterior photographs](https://media.toyota.ca/en/albums/2002/2002-toyota-4runner.html):
  late-N185 installed outlines, multi-reflector optics and separate corner lights.
- [DEPO OE-fit catalogue](https://umnitza.com/products/1999-2002-toyota-4runner-oe-replacement-headlight-set-made-by-depo):
  clear-headlamp fitment spans 1999–2002, including the requested 2001; it is not a
  claim that these lamps first appeared in 2001. Listed interchange references are
  LH 81150-35300 and RH 81110-35320.
- [Close replacement-lamp photographs](https://www.ebay.com/itm/324763220611) and
  [the matching pair](https://www.ebay.com/itm/183505951666): clear unfluted cover,
  trapezoid outline, rectangular reflector facets, H4 glare shield and edge bands.
- [TYC corner-lamp photograph](https://www.carid.com/tyc/driver-side-replacement-turn-signal-corner-light-value-line-mpn-18-5716-00.html):
  curved clear cover, separate rounded amber insert and fine prism pattern.

Product photos are aftermarket OE-fit references, not misrepresented as Toyota
drawings or original scanned parts. They are local study material, not embedded
textures on the new visible headlamps. The prior photograph-projected covers are hidden.

## Implementation and evidence

Collection `20 N185 clear glass headlamps - reference rebuild` contains separate
clear covers, faceted reflector bowls, sockets, small bulb shields, thin perimeter
seals and corner-lamp chambers. Main-lamp spacing and adjacent grille width change
together; corner apertures and bonnet/fender returns are revised to fit them.
The covers use a thin-surface Fresnel preview shader, not a simulated beam pattern.
Full-resolution EEVEE reflection tracing replaces the earlier half-resolution
reflection setting; this materially improves the small reflector-facet readback.

Local project: `~/BlenderProjects/4Runner_N185_20261117/`.

- `4runner_n185.blend`: current editable scene.
- `4runner_n185_2001.blend`: matching revision copy.
- `4runner_n185_before_headlamp_rebuild.blend`: preserved gold pre-headlamp rollback.
- `headlamp_detail.png`, `front.png`, `front_2001_detail.png`, `hero.png`: headlamp
  inspection views. Unchanged rear/wheel views and older side/top/clay views remain
  evidence of the preceding checkpoint, not separately rerun acceptance gates.
- `headlamp_sources.json`, `scripts/24_headlamp_rebuild.py` through the subsequent
  headlamp fit/fairing/save scripts and `headlamp_verification.log`: local sources
  and checks. Scripts are incremental and not safe to replay on the finished scene.

Readback checks verify two visible clear main covers, mirrored cover vertices with
zero measured symmetry error, finite new mesh coordinates, no image-texture nodes
on the new covers, both old photo covers hidden, two retained crossbars and unchanged
gold material values. This does not assert whole-car watertightness or correct
photometric output. Safe mode remained enabled; a disallowed GPU-module inspection
was rejected before execution and removed, not bypassed.

Final saved-scene readback retains all four OEM-pattern rims, both roof crossbars
and the front-detail camera. The reconstructed clear-cover bounds are approximately
305 by184 mm, with zero paired vertex-mirror error; these are model checks, not
measurements certified against a factory drawing. The local checksum manifest
verifies the saved sources, reference files, renders and blend checkpoints.

## Rollout and limits

Local Blender file update only. Built/installed/public Family Connect versions,
catalogues, signing, gateways and release gates are unchanged. Restore the pre-headlamp
blend to roll back this modeling pass. All blends, downloaded photos and rendered
images stay outside Git; only this sanitized record and state/plan routing belong
in the repository. The remaining acceptance check is the owner's likeness review.

Repository publication is subject to the existing divergent `main` history; a
local documentation commit does not imply remote publication or deployment.
