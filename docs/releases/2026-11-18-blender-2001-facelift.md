# Local N185 late-facelift detail revision — 18 November 2026

## Selected scope and authority

The owner requested 2001-onward facelift lights and bumpers, a scoop hood and a
more recognisable liftgate. This follows the separate [body-surfacing checkpoint](2026-11-18-blender-surfacing.md);
it does not claim owner acceptance of the likeness or an exact Toyota digital twin.
No Family Connect version, source, service, deployment or engineering gate changes.
Blender 5.3.0 and the existing guarded loopback MCP connection remain unchanged.

References inspected for this pass:

- [Toyota USA 2001 brochure](https://www.auto-brochures.com/makes/Toyota/4Runner/Toyota_US%204Runner_2001.pdf):
  multi-reflector headlamps, new grille/taillamps and Sport package scoop/trim.
- [Toyota Canada 2002 official press photographs](https://media.toyota.ca/en/albums/2002/2002-toyota-4runner.html):
  late-generation front/side/rear surfaces, reflector pattern, scoop and rear
  plate stamping. Canadian Badlands badges are not copied onto the US model.
- [2001 US Sport front and three-quarter photographs](https://www.mminvestmentcars.com/vehicle-details/2001-toyota-4runner-sport-edition---4wd---diff-lock---hood-scoop-suv-456f82e60edeff41b7f06335a50dc7a7):
  layout cross-check, not reliance on dealer specification prose.
- [2001 rear photograph](https://www.curbsideclassic.com/cars-of-a-lifetime/coal-2001-toyota-4runner-oh-what-a-feeling/):
  secondary check of rear lamps and badge placement.
- [2001 Toyota 16x7 OEM wheel catalogue W69431](https://autorimshop.com/products/2001-toyota-4runner-16-oem-wheel-rim-w69431s):
  five broad spokes, triangular ventilation apertures, recessed spoke details and
  six-lug pattern; checked against Toyota's complete-vehicle press photograph.

The latest owner request supersedes the photo's silver paint, aftermarket wheels
and basket: champagne-gold metallic, OEM-pattern 16x7 five-spoke Toyota wheels and
two bowed factory-style roof crossbars are modeled. Chrome trim, lifted stance and
mud tyres remain. Gold is an artistic approximation, not measured factory paint.
The scoop is the requested Sport-style addition. This is a custom
combination: the US brochure describes factory Sport bumpers/grille as colour-keyed,
not chrome. No JDM rear spare or newer-generation body is substituted.

## Geometry

- Trapezoidal late headlamp outlines, housings, seals, multi-facet reflector bowls,
  bulb shields and curved covers; revised narrow corner reflectors.
- Revised grille slots and carrier, under-headlamp fillers and upper closing panel.
- Rounded chrome front impact bar, formed lower valance, cut intake/lamp openings,
  raised U-profile surround, recessed louvres, rectangular indicator chambers and
  round outboard fog optics. The former flat overlay intake is disabled.
- Rear bumper with lowered centre step, raised corner ends, non-slip pad and ribs.
- Compound scoop shell, rolled lip, recessed mouth and duct walls; subtle hood
  shoulder creases. This is mesh geometry rather than a painted black decal.
- Liftgate skin with stamped-in plate cavity, handle/grip, key cylinder, plate
  lamps, oval/model badges, shaped glass sill and rear wiper.
- Late clear-over-red rear lamp clusters with curved wraps, inner chambers and
  prism detail. Obstructing body faces are removed and aperture returns added.
- Four cast five-spoke dishes with real openings, spoke channels, rolled lips,
  six 139.7mm-PCD lug positions, Toyota caps and valves. The retained off-road tyre
  carcasses now seat on 16-inch beads; size lettering and brake clearance are revised.
- Basket, clamps and aftermarket rims are individually disabled. Two low bowed
  crossbars have mounting tracks, tapered pedestals, gaskets and recessed fasteners.

New collections are 14–19. Previous collections 04, 05 and 12 remain disabled,
not deleted. The earlier upper-body union and its editable source patches remain.
The scoop/optics/fascia/liftgate parts remain individually editable.

## Local files, checks and rollback

Directory: `~/BlenderProjects/4Runner_N185_20261117/`.

- `4runner_n185.blend`: current working scene in the existing GUI.
- `4runner_n185_2001.blend`: matching late-facelift revision copy.
- `4runner_n185_surfaced.blend`: preserved pre-facelift rollback.
- `hero.png`, `front_2001_detail.png`, `rear.png`, `front.png`, `side.png`, `top.png`
  and `facelift_clay.png`: current inspection views.
- `wheel_oem_detail.png`: revised rim, lug and tyre-seat inspection.
- `scripts/14`–`scripts/23`, helpers and final save/check scripts: incremental source
  records, not an idempotent build-from-empty script.
- `references/facelift2001/`, `sources.json`, `README.txt`,
  `facelift_verification.log`, `facelift_final_readback.log`, `checksums.sha256`:
  sources and local evidence; all100 listed local file digests verify.

The MCP guard accepts the modeling scripts. Numeric validation checks finite
coordinates/normals, unchanged 2675mm wheelbase, retained closed upper-body mesh,
disabled previous fascia collections, four revised rims, two crossbars and no
render-visible basket objects. This does not assert that the entire
assembled vehicle is watertight. EEVEE renders are inspected, including front/rear
details and a material-override view; no Cycles validation is claimed.

Saved-scene numeric readback:1329 objects including retained geometry,633 mesh
objects and871082 mesh vertices; zero non-finite coordinates or normals. Wheelbase
is2674.99995mm and the chrome-bumper envelope4654.99997mm. These are construction
anchor checks, not the accuracy of the reconstructed skin. The upper-body union
has zero boundary/nonmanifold edges;4 OEM-pattern rims,2 crossbars and0 visible
basket objects are confirmed. The pre-facelift rollback file remains separate.

One combined detail-render call exceeded the180s bridge deadline after writing
the front view. It was not replayed: Blender subsequently wrote the rear view,
confirmed by the session log and image inspection; the next guarded render call
completed normally. Final hero output is2000px wide/192 EEVEE samples; inspection
views use reduced resolution/samples and do not replace that saved render setup.

Headlamp optical detail is projected from an official 2002 photograph and packed
into the blend; the modeled housings and bowls remain underneath. It retains
source lighting and is not a physically complete headlight simulation. Photographs
and brochure scans remain local reference material with their original rights.
Interior/underbody and some small hardware remain approximate. Likeness acceptance
is still OPEN; no manufacturing accuracy or complete internet coverage is claimed.

## Repository checkpoint

Only sanitized documentation is committed; modeling assets stay outside this repo.
The preceding surfacing report was committed as `07c01c33`. Its ordinary push was
rejected as non-fast-forward; remote main readback was
`380da279588761c83e5433bec33a0511e4781133`. No reset, merge, rebase or force push is
performed to publish this modeling note. Unrelated local changes are preserved.
The current checkout remains divergent (10 local/288 upstream-only commits before
this checkpoint); ordinary publication is blocked by the existing non-fast-forward
boundary. The saved Blender assets do not depend on a successful repository push.
