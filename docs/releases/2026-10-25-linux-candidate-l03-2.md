# L03.2 — full internal Linux candidate

Date: **2026-10-25**. **ACTIVE**, not accepted, installed or published yet.
Entry: current main `1b285c6417676b3383c03c47620802a5f3d5ed6f` (remote verified).
Parallel ops STATUS/PLAN hunks and the VPN health report remain outside this task.

L03.1 REVIEW ACCEPTED / DONE: product source
`f826dbdfb562541bde95d2fcbecc1d944d15da3d`, **L03.1/build-9**, build ID
`8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da`, archive SHA256
`bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9`.
Use these exact retained standard-builder bytes; no architecture/ownership/native
contract change or silent rebuild. [Accepted evidence](2026-10-25-linux-system-runtime-l03-1.md).

Internal candidate version reserved: **0.2.12~l03.2.1**; source VERSION remains
**0.2.11**, published Linux remains **0.2.11**. Candidate filenames must not reuse
published artifact names. Nothing signed, released, installed on the workstation
or uploaded to public downloads. Windows/Android/reference pins unchanged.

Scope: paired user inventory and embedded system payload, explicit unprivileged
setup with polkit, exact AppImage/DEB and legacy-six-file integrity, clean
Ubuntu24.04/systemd255 package/install checks. L03 parent remains IN_PROGRESS
until review L03.2. No L04/L05 traffic/grants/registration, L07/L08, Windows,
fleet, iOS, public catalog, landing, signing sequence or server-policy changes.
Accepted L01/L01-R, L02/L02.2, D03/D04/D05, D01.3/D01.3-R remain unchanged.
D01 and D02.1-R stay open; residual54 full-suite failures and voice/Windows
observations are separate, not waived or repaired here.

Builds, exact hashes, source SHA, installation/removal, rollback and CI receipts
will be recorded here after the corresponding gates, never inferred from source.
**STOP after completion. NEXT — review L03.2.**
