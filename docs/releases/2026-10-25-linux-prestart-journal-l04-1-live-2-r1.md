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

STOP. NEXT — review L04.1-LIVE-2-R1.
