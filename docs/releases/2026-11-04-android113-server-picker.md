# Android113 — hybrid server picker and per-node load

## Scope and distribution boundary

The owner's4 November request selects this bounded FLEET-BOOTSTRAP-2 UI follow-up:
the same three servers in every mode, country names rather than Amsterdam, and square
load indicators turning orange at85%. This takes priority over the next transport
diagnostic step for this change only; it does not resolve the recorded112 instability
or authorize an unrelated fleet task.

After reviewing three visual references, the owner selects the hybrid: the minimalist
flat list with the compact right-aligned load meter, a subtle green selected-row fill
and a checkmark, not separate cards or radio circles. Reference percentages are synthetic.

Source version is0.1.18-beta113/code113, preserving Friends Android8.1+/minSDK27.
Local CI-signed x86_64 artifacts are disposable emulator builds, not production-signed
phone updates. Owner phone remains112; public downloads, signed catalog6 and invitation
remain111. No113 public artifact/checksum/link, production signature, server deployment,
policy change or phone installation is claimed. Existing112 binaries remain immutable.

## Behavior

- Auto, AWG, TCP and MESH share one ordered list: Russia, Netherlands, Netherlands2
  (RU: Россия, Нидерланды, Нидерланды2). The actual resource includes a space before2.
  Switching mode preserves the selected physical node and the existing preferences.
- The list comes from the admitted gateway registry plus Russia, not independently
  maintained transport lists. A future admitted node can be added centrally; this is
  not permission to discover/connect arbitrary hosts from unsigned telemetry. Further
  fleet/catalog expansion still needs its own signed protocol and admission work.
- Russia remains visible/selectable in MESH with an explicit unavailable explanation.
  Connect is refused without opening a tunnel. Auto may use Russia's AWG/TCP but cannot
  silently fall back to Netherlands MESH. No Russian MESH deployment is invented.
- Auto loads the selected NL node's existing schema3 signed profiles from the separate
  explicit-node vault. Legacy country profiles retain schema2; identity, signatures,
  replay checks and device/node-bound materialization remain. Secondary Auto and MESH
  prewarm their own readiness alongside the primary chat scope.
- The status endpoint already publishes separate `nodes` entries. Android now reads
  them and requires matching `gateway_id` and country for each physical NL node. It
  never substitutes the aggregate Netherlands value for a missing node. Existing RU
  telemetry, freshness limits, CPU-only fallback and capacity/estimate semantics stay.
- Flat dropdown rows show a flag, country/node name, numeric load and ten square segments
  at the right. Thin dividers separate rows; the selected node has a soft green fill and
  a vector checkmark, including a spoken selection label. Row reuse clears this state
  from the collapsed selector. At large font scales or narrow screens the load moves
  below the name, still aligned right; rows grow rather than truncating names.
  Known load below85% is green;85% and above is orange. Missing/stale data is labelled
  with a dash and grey segments, not0%; accessibility retains the unavailable explanation.
  CPU-only and estimated values remain explicit.
  The selected-server load bar uses the same threshold. Text/accessibility descriptions
  retain the numerical meaning; color is not the only signal.

## Checks and remaining gates

Final offline local JVM suites: debug418 and Friends413 PASS,0 skips. Friends APK and
test APK assembly PASS; lint0 errors/56 pre-existing warnings. The initial new-view
constructor warning is fixed, not suppressed. API27 and API35 dashboard/picker/language
instrumentation:4/4 PASS/0 skips on each disposable emulator at both320dp and360dp
screen widths. RU/EN synthetic list
renders include default and1.3x font scales; visual review found mid-word wrapping on
the first narrow large-font layout. The responsive stacked layout corrects it; repeated
instrumentation and render review PASS. No owner phone is used for these tests.

Final selected Python checks:22 PASS/0 skips. Earlier source-provenance rejection of
the changed ServerLoad pin is reconciled by reviewing exact telemetry/Auto/resource
pins, without exclusions. The older row-text assertion is updated for the deliberate
unknown-load dash while preserving the shared bound presentation check. Public111
signature/catalog assertions stay. Scoped documentation links and whitespace checked.

Tests cover identical ordering in all modes, mode/recreation persistence, no unintended
connection, explicit Russia/MESH refusal, per-node binding/staleness/malformed isolation,
CPU-only labels, zero/unknown load,85% boundary, meter geometry, selected-row accessibility,
recycling cleanup, RU/EN server names and narrow/large-font text bounds.
Synthetic row/full-list renders are test evidence, not measured product load. Private
local artifacts stay in ignored `state-client-build/android113-server-picker-20261104/`.

Remaining delivery gates: exact committed-source platform/native CI and artifact review,
production signing, authorized in-place phone acceptance and, before general MESH rollout,
the still-open112 transport and renewal-race gates. No real Auto target/failover acceptance
on an enrolled phone is claimed by these UI/model checks.

## Rollback

No server or installed client is changed by this source/UI checkpoint. To withdraw it,
revert the focused source changes in a new commit; do not reset published history,
rewrite112 binaries or restore private databases/profiles. If113 is installed later,
use a qualified forward corrective version rather than uninstall/data-clear/downgrade.
