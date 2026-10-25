# L04.1-LIVE-2-R1 — pre-start refusal terminalization,25.10.2026

**ACTIVE source/package checkpoint.** Entry main
`403b22f25722252633c8ca4c5c8cb80f4f0a3395`; affected product source
`57f8eff8b291062d69248ac46413f8c9fc0f561d`.

LIVE-2 PARTIAL/review accepted; Gate A PASS retained for historical exact
0.2.12~l03.2.2/candidate d9c0d07f… only. One helper up request is permitted;
the defect is persistent APPLYING/pending after authoritative pre-start refusal.
RETEST DONE/review accepted; parent L04.1 IN_PROGRESS.

Plan: actual FriendsApplication/control journal/session/fixed-helper red AWG/TCP
in offline disposable systemd; strict pre-start/unknown outcome contract;
same-owner terminalization/recovery and sanitized diagnostics; regression gates;
new system/runtime and user candidate if root protocol/modules change.
No rebuild/patch of historical candidate. FC-3YSQ-BE2D/nl private state and gateways
are not used. Live B1 retest, B2–F, L04.2/L05 and device teardown NOT_RUN.

## Deterministic red — actual installed AWG and TCP

Separate offline Ubuntu24.04/systemd255 root containers, exact historical DEB/setup,
real polkit/session/fixed helper/transport flock. Synthetic local Device Identity
and verified public catalog vector only; no protected state, external network or fetch.
[Sanitized red](2026-10-25-linux-prestart-journal-l04-1-live-2-r1.red.json).

Both: one up request, zero transport starts/owners/TUN, unchanged network. First
authorization failure: BackendError `VPN operation failed`; TCP driver changes this
to `All VPN transports failed`. First rollback exception: ValueError
`invalid application recovery metadata`. Actual normal inventory includes virtual
`fcmesh0`; snapshot persists it, but rollback's normal-profile validator rejects it.
Journal stays APPLYING, generation1/pending true; physical locks free after fixture
release. No IDLE write or finish occurs after the rejection. Initial IDLE recover's
no-op finish is recorded separately. This reproduces the lifecycle defect rather
than inferring it from the GUI's generic waiting label.

The reproduction fixture's first attempt could not export the invalid journal via
its own strict `_read`; read-only raw phase projection repaired that fixture only.
Final AWG and TCP reproductions each use a fresh container and one Connect.

## Source correction checkpoint

Authorization session v2 has strict schema2 replies: OK, PRE_START_REJECTED
(TRANSPORT_BUSY/OWNER_CONFLICT), OUTCOME_UNKNOWN (HELPER_FAILED/HELPER_TIMEOUT).
Only fixed AWG/TCP up plus reserved helper exit78 and a strict schema1 root receipt
can prove pre-start rejection. EOF/malformed/unknown replies remain unknown;
exception text or a free physical lock never proves cleanup.

Normal snapshots exclude inactive virtual MESH/Auto identifiers, including recovery
of the old persisted baseline. Confirmed rejection removes only the operation's
unpaired, UID-owned inactive import using fixed `discard`, writes IDLE, then finishes
the same lease: generation0→1 reserve→2 finish, pending null. No retry/fallback.
Unknown outcome keeps APPLYING/generation1/pending; only same-owner recovery sends
bounded down even when TUN is absent, then checks/discards the inactive profile.
Unconfirmed cleanup retains pending. Primary and cleanup exceptions are kept
separately; expired leases cannot finish later generations. GUI diagnostics retain
bounded category/phase/outcome/cleanup/generation/pending, not profiles or endpoints.

Targeted ownership/Friends/auth pipes/diagnostics/GTK poll suite: **126 PASS**.
Intermediate full desktop runs exposed stale v1 fixtures and a new GTK test which
asserted before the idle render; these test-contract issues are corrected, not xfailed.
Mandatory full/actual-root/system/package gates remain in progress at this source
checkpoint. System build-9 is NOT reused: root helpers, backend and authorization
protocol changed. New internal version reserved: **0.2.12~l03.2.3**; public VERSION,
catalogs and historical .2 artifacts unchanged.

Source `ddbf880e4ce5488700aa633c28e2fdffd3a61971` pushed/remote verified.
Full desktop + Friends + Linux chat selections: **1178 PASS/96 SKIP** in the
locked Python3.12 test image with real GTK/Xvfb. Additional fixed-discard security
cases (wrong owner, paired, active/malformed marker, mode/link/hardlink) plus auth
suite: **44 PASS**. The root-gate wrapper explicitly forwards only its public
namespace assertion across its sanitized environment; no credentials are forwarded.
New exact system build `b8140c68…` real offline systemd255 smoke **PASS**:
native/RNS/import readback, actual polkit/root→UID, owner/sticky/start barrier,
real import-readback failure/rollback, unchanged synthetic user state/network.
Desktop pair/actual pre-start gates and CI results follow separately.

Intermediate AWG CI `40216532502/121238763466` exposed the existing isolated
gateway test's raw `ready:1`/`ok` assertions after the protocol change. The fixture
now checks exact v2 OK/unknown envelopes, preserving cross-UID and forbidden-action
denial. No transport implementation, candidate bytes or trust boundary changes in
that test-only correction. Source native/root→UID/Auto/DIRECT isolated job
`40216532591/121238763585` PASS, including both protocol OS jobs.

STOP after package evidence. NEXT — review L04.1-LIVE-2-R1.
