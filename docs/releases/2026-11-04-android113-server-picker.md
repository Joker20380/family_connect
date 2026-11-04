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

## Owner-requested release preparation

The owner's subsequent «выпускай» authorizes preparing and publishing the optional113
client update, not changing server admission, transport policy or declaring MESH stable.
The exact committed build input is `d2882cde4c50b15085b925007c04c48f4de61bf0`.
Client workflow41833086774 attempt1 passes JVM/native construction and contracts but
fails the Android15 emulator action before any instrumentation cases execute. No
qualified ARM64 release payload is produced by that attempt. A bounded retry uses the
same commit and unchanged gates; failure evidence is retained, not relabelled PASS.
Linux and Windows jobs are skipped by Android-only scope, not newly accepted releases.

Additional local API27 CI-signed112→113 in-place upgrade PASS: application UID,
nonexportable identity/journal wrapping keys, interrupted atomic-write recovery and
durable outbox survive across distinct processes. This is synthetic storage acceptance,
not product-signed phone operation or proof of live MESH stability.

The release remains pending exact CI/artifact review, offline signing, installed-client
acceptance and guarded public APK/catalog/invitation readback. Current public111/catalog6
and owner112 remain unchanged at this preparation checkpoint. Existing MESH stability
and renewal-race work remains open; this UI update does not change its acceptance status.
The required full documentation baseline scan has738 files/4569 links and two pre-existing
historical anchor errors (STATUS's October27 evening link and the October24 source
checkpoint's October23 phase22 link); no unrelated historical repair is folded in.

### Exact CI and downloaded artifact qualification

At13:35UTC, workflow41833086774 attempt2 is successful on the unchanged d2882cd source.
All required Android stages execute, including both API levels, restricted native and
production-configuration ARM64 packaging. The first failed attempt remains distinct.
All four attempt2 ZIPs match their GitHub artifact digests and source/run; stale attempt1
debug/runtime artifacts are explicitly excluded. UI renders on both APIs are reviewed;
the server-list percentages are synthetic and contain no product identities.

- Unsigned Friends0.1.18-beta113/code113, ARM64, minSDK27/target35:50,254,721 bytes,
  SHA256 `1b77a8ff91cb5718ddd42766e5c546b6f6a51bfb6c9031b43f0bef23bf496062`.
- JNI/source receipts,12 libraries, ELF/ZIP16K alignment, audio source/licenses and
  absence of the diagnostic provisioning entrypoint PASS; APK is not debuggable.
- Exact JVM debug418/Friends413 PASS/0 skips. API35 debug28/Friends19 PASS,25/4 existing
  opt-in/variant skips; API27 debug27/Friends18 PASS,26/5 existing opt-in/API skips.
  Required picker, language, storage and legacy-audio cases execute; skips are not PASS.
- Offline signing is requested through the accepted protected-vault reader; no key or
  password is exported. At this checkpoint it awaits the local dialog. No product-signed
  113 APK, phone update, public catalog7 or public113 link is claimed.

Private qualification/download receipts remain in ignored
`state-client-build/android113-release-20261104/`. The unsigned artifact is qualified for
the next signing step, not a public installer or sustained-MESH acceptance.
