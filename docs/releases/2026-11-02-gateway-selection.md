# Explicit Amsterdam selection — 2 November 2026

## Delivery continuation

Windows0.2.16 is qualified from exact source5ae821d / run41439156032,
native Windows and compatibility jobs PASS. The immutable distribution workflow
pins artifact13138243140, ZIP digestcccbbe7a… and installer491a731e…/49955605bytes;
publication and independent update-catalog sequence12 are not yet confirmed.
Android110 in that run failed its TCP emulator data test with ENETUNREACH;
the failure is retained and must be localized before signing/publication.

The retained synthetic TcpPrimary receipt localizes the failure: service status
was `on` with health `checking`, VPN120/tun0 already had both routes and the TCP
source, but Android's UID default remained non-VPN Ethernet101. The very first
connect failed in5ms, before writing any HTTP bytes. The instrumentation now waits
at most15s for the expected dual-stack TCP VPN to become the actual UID default.
No process/socket Network binding, HTTP retry, relaxed predicate or production
runtime change: all18 REALITY requests, DNS and switch/cancel/revoke gates remain.
Exact corrected emulator acceptance is pending, not inferred from source review.

Continuation of **FLEET-BOOTSTRAP-2**, explicitly requested by the owner. This is
source integration, not an installed or publicly distributed client release.
The existing ordinary admission remains the deployed baseline until separately
verified package/backend rollout receipts are recorded here.

## Contract

- Android, Linux GTK and Windows selectors include **Amsterdam 1** and **Amsterdam 2**.
  The previous Netherlands choice remains **Netherlands · assigned**; existing
  preferences and sticky assignments are not silently migrated.
- Explicit choices use stable signed `gateway_id` values `nl-amsterdam-1` and
  `nl-amsterdam-2`, distinct from country `nl`. A schema3 catalog contains exactly
  those two ordinary AWG/TCP templates. It does not advertise a second MESH service.
- Existing schema2 endpoints, global legacy floor and country semantics are unchanged.
  Explicit selection has a separate durable catalog/floor namespace, shared between
  both explicit choices. Alternating nodes therefore requires neither a downgrade nor
  rewriting a previously signed catalog. Same-sequence substitution is rejected.
- Fresh one-use proof purposes bind the exact target. Only the two fixed
  `/friends/gateway-configuration/nl-amsterdam-{1,2}` endpoints are accepted.
  A failed request never falls back to the assigned node or an old explicit profile.
  Registration uses the existing pinned SSH/forced-command boundary; credentials
  remain in stdin/private stores, not argv or UI results.
- Offline operator import binds each signed template to its already-admitted
  native-node policy template. The root-only `install-selection` operation uses
  expected predecessor, increasing sequence, idempotent operation ID and append-only
  database triggers. HTTP cannot import catalogs. Policy replacement fences selection
  until a newly bound selection catalog is installed.
- Explicit selection does not mutate `gateway_assignments`, transfer an existing
  session, create invitations or change paid state. Revocation is checked before
  registration. Existing schema2 clients continue to reject schema3.
- Explicit choices are available for AWG/TCP. Android/Linux refuse Auto/MESH with
  an explicit node and explain the limitation instead of silently using another
  MESH gateway. No node-specific load is invented from the country-level monitor.

## Local qualification

- Python protocol/backend/identity/store/application contour:190 PASS.
- Additional HTTP/package/floor/ordinary/restricted contour:171 PASS,25 existing
  environment-gated skips; no suppressed failures.
- GTK display-backed selection and disconnect tests:52 PASS. RU/EN selected-node
  renders captured with isolated HOME/network disabled; no workstation install.
- Android JVM control suite PASS, including shared schema3 positive/negative vectors.
- Native Windows control/DPAPI CI41431840282, ordinary user access41431840217,
  AWG41431840299 and TCP41431840245 PASS on source22069b2. Desktop visual CI41431840205
  PASS. These do not assert acceptance of a new distributed installer.
- Synthetic vectors use an explicitly public deterministic test signing seed and
  documentation-network endpoints. No production key/profile is in the fixtures.

## Package-gate repair

The first source CI was not green: Android's accepted-source guard did not yet
record the reviewed selection handlers/resources; the desktop three-gateway
negative test wrapped the former three-argument validator and failed before
inspecting its catalog. Exact reviewed hashes are now explicit, and the wrapper
passes/asserts legacy schema2. Neither production validation nor a test is skipped.
Focused release contracts53 PASS/40 native-environment skips/1 unrelated Windows
deselection; full desktop1229 PASS/185 environment-gated skips. With the rebuilt
native worker, configuration/Auto compatibility71 PASS, zero skips.

The full-runtime builder also found four stale shared-reference hashes. Their
bytes are already accepted commits a11eb8f (recovery lock), c309bff (canonical
profile DAC), and4a7bf20 (beta109 stream retirement), not changes introduced here.
Bounded desktop adaptations and companion source/test hashes advance explicitly;
the historical Android106 inventory is retained unchanged. Go1.26.1 native race
tests/build PASS, source inventory f0e48d7cd3bd68a02759a5ff29967492ab170e171942d502864f0e03a07c23fe.
The system reference advances only that inventory and two reviewed provisioning
files; other111 pinned system sources and RNS digest remain unchanged.
Local preparation failures (missing builder git/gcc, old Python tar API and host
umask002) are isolated packaging-environment failures, not accepted artifacts.
No failed output is reused or published. Full package/service smoke is still pending.

The exact Linux.12 system/DEB/AppImage, plus AWG/TCP pre-start failure cleanup,
now pass isolated Ubuntu26.04/systemd259/Python3.14 smoke. Packaged (not checkout)
GTK selection passes RU/EN at100% and200% scale:4 PASS. No workstation install.
Hosted candidate41436331524 failed at its container boot wait: `systemctl is-active`
with two names can succeed when only one is active. This CI-harness race remains
recorded. The wait now checks each service independently and fails explicitly on
timeout;5 deterministic shell regressions PASS (both-ready, either-delayed and
either-missing). Hosted rerun is pending. Local evidence is not relabelled as CI.

Ingress closure is now explicit: the packaged `gateway-selection-location.conf`
allows POST only for the two exact node routes, with an8KiB body limit and bounded
proxy timeouts. Deployment must substitute the observed active loopback upstream,
never start a competing backend. Real isolated Nginx + HTTP tests53 PASS/1 optional
sync-archive skip include alternating target proofs, wrong-purpose/replay rejection,
unknown/suffixed routes and GET rejection. The old test fixture is brought into
line with the already-existing diagnostics route; production diagnostics unchanged.
HTTP archive fce2340051ecc574156ee2b7eb50f87b443679b95bf69ee3f62c6c189de1ebf5
imports in isolation. Versus served f33dee20, only access proof purposes, gateway
routing/selection, catalog parsing and the dispatcher differ; paid module unchanged.

Read-only RU preflight: served HTTP remains f33dee20, original catalog4 hash unchanged,
policy generation2 and57 first-NL assignments retained. Devices57, invites111,
restricted grants2, paid subscription1/events4 and all protected row digests match
the previous admission baseline. Both maintenance timers active; no selection
catalog or public selection ingress installed. No production write in this phase.

## Rollout boundary

**Backend selection is now LIVE; client publication is still pending.** Exact HTTP
fce23400 and separate signed schema3 selection sequence1 are installed. Root-private
legacy catalog4, generation2 and all57 sticky assignments are unchanged. Public
system-CA-verified HTTPS confirms both routes, legacy ordinary/restricted malformed
requests, GET/unknown/suffixed-route rejection. Catalog4 is verified on the node,
not via `/friends/catalog.json` (that public URL returns404).

First activation encountered a cold HTTP listener after systemd reported an active
PID. Its rollback restored f33dee20/old Nginx, but the same premature probe left a
fenced journal. Read-only reconciliation confirmed old runtime/ports/config and
protected rows, then appended `ROLLBACK_RECONCILED`; no receipt was erased. The
next explicit attempt uses the existing bounded durable readiness helper: new
delayed-start and never-ready regressions PASS; full Nginx/HTTP55 PASS/1 optional
sync-archive skip. Final activation/HTTPS PASS. Total3 manual HTTP restarts,
1 reconciled rollback,1 Nginx reload,0 database restores. Append-only selection
event is retained; its retry is verified idempotent, not inserted twice.

Production writes are authorized/nonzero for artifact/catalog import and API/ingress
activation; native gateway services are untouched. Protected row digests unchanged:
devices57/invites111/restricted2/paid1 subscription+4 events; invitations0, paid
mutations0, device moves0, phone actions0. No authenticated physical selection/tunnel
test is claimed; ordinary native-node acceptance remains the earlier live baseline.
[Safe receipt](2026-11-02-gateway-selection.receipt.json).

Corrected Windows0.2.16 exact installer13138243140: native build/compatibility
CI41439156032 PASS; downloaded ZIP digest and installer SHA256/size verified.
Installer491a731edbf80887122844bebcccb8741e701b03816202f9a9b77c77855e8a65,
49,955,605 bytes. Render shows0.2.16. It is not yet published. Hosted Linux candidate
41438372471 also PASS after the boot-wait repair; its CI artifact is separate from
the frozen local.12 package. Android110 is still running its emulator gates.

Windows source89f4e8 native build/compatibility passed, but downloaded artifact
13137401420 is rejected for distribution: its installer still declared0.2.15
despite the application0.2.16. ZIP digest130d173d21f951c2904b3f9a499356f25b66e24b541a273a3c80a256c6c68927
is verified; these bytes are retained privately and MUST NOT replace public0.2.15.
`build.ps1` now passes the single project version to required Inno metadata/filename
and signed-artifact checks. Native rebuild remains mandatory; local source guards25
PASS. Android instrumentation additionally renders/asserts both explicit rows and
rejects showing country-level CPU as a node measurement; exact emulator run pending.

Source versions reserved for this change: Android0.1.18-beta110/code110 and
Windows0.2.16. They are not yet signed/published/installed. Linux complete internal
Ubuntu26.04/Python3.14 candidate0.2.12~l03.2.12 is built from efc13f1 (not installed),
with DEB/AppImage byte/member audit PASS and system-component isolated systemd259
install/rollback/identity-preservation smoke PASS. DEB/AppImage smoke is pending.
System build d5fc9df50a66292b7cd1b10c81a2521352d7648c0bd2b5037af2c457b1617eb7;
DEB cde8416c07ef87ec2ef5441e17a33b93f72be8aad2e1675c7203d542ea975972;
AppImage1fb37e03b01e8aaf7d598f9907e27e6bee8500fa37d272018abcc49287fb2d2c.
The bundled legacy six-file tar is NOT a supported update for internal candidates.

Not yet delivered to clients: Android APK, Windows installer/update catalog and
the reviewed full Linux DEB/AppImage. Backend/catalog/ingress rollout is recorded above.
Public Android109/Linux0.2.11/Windows0.2.15 and installed owner Linux
0.2.12~l03.2.9 remain unchanged. L08 migration is not bypassed; the existing internal
Linux updater cannot install a legacy six-file archive as a full runtime update.

Before claiming the new choices appear for users: qualify exact client artifacts,
publish only immutable increasing versions/catalog sequences, verify delivered
bytes and install the reviewed Linux package without losing identity/state. Retain
the deployed selection catalog/HTTP runtime and their protected-state/readback
and rollback receipts. Keep existing sticky routing intact. Until then,
the current clients continue to show the old country selector.

References: [current state](../STATUS.md), [existing task](../PLAN.md),
[ordinary live baseline](2026-11-02-second-nl-ordinary-live.md),
[desktop identity boundary](../desktop-architecture.md#desktop-fleet-boundary),
[Linux full-package boundary](../linux-appimage-deb.ru.md).
