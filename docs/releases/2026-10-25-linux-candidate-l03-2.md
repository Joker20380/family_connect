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

## Implementation checkpoint

The two formats now bind an identical user inventory to the embedded system
archive, ABI, source SHA and distinct candidate build ID. The fixed setup action
is available in general GUI Settings before chat/identity creation, and via
`--setup-system` with no file/UID arguments. The ordinary user verifies and
extracts a private snapshot before polkit. The privileged fixed bootstrap receives
only bounded archive bytes via stdin, rechecks the exact digest/inventory and
invokes the accepted installer from a separate root-owned0700 temporary directory.
No user-supplied executable path is used at privilege elevation. Both snapshots
are removed normally/on denial; a killed caller never leaves a user-writable
snapshot trusted by root. L03.1 transaction/rollback/ownership is unchanged.

Matching user/system inventories gate READY and privileged start/import actions;
cleanup remains possible. A mismatched system cannot become compatible merely by
retaining the same native binary/version. DEB installs a non-enabled Type=dbus
user unit and activation file. AppImage retains transient user ownership and
reopens its original image, including extract-and-run when FUSE is unavailable.
GUI exit does not kill permitted background chat. Explicit DEB removal stops its
own user unit; AppImage `--remove-integration` removes its own menu entry/owner.
Both retain encrypted user state and the independent root runtime/backups.
Root chat services stay unenabled; no startup path mutates VPN intent.

Prototype build-4 (dirty-source checkpoint, **not final candidate**) passed both
real disposable package gates, including ordinary UID/polkit, installed imports,
safe repeated setup, background D-Bus owner and removal/state preservation.
Full source desktop at that checkpoint:1142 passed/24 skipped. Targeted final
selection61 PASS; final exact artifacts/full desktop remain to check after commit.
Local evidence: `state-client-build/linux-candidate-l032-20261025/` (ignored).
Failures retained: startup was queried before D-Bus boot; public unit copies
inherited builder umask002 (fixed to0644 with regression); synthetic identity
fixture lacked its parent; Docker noexec `/tmp` and root-owned private AppImage
extraction prevented fixture execution (runner corrected, not product hardening).
No blocking L03.1 defect/correction was required.

CI adds bounded package regressions, standard accepted-source rebuild, actual
L03.1 smoke, candidate inventory and both clean install gates. Rebuilt system
bytes have their own identity; they are not called build-9. Local final artifacts
continue to embed the exact accepted build-9. Ordinary Client Linux source
previews now use0.2.12~ci.preview.1 on branch builds, not public0.2.11 filenames;
they are not full L03.2 candidates. Release/tag and signing paths are unchanged.
Existing full desktop/native/root→UID/Auto/DIRECT and full suites stay enabled.

Source checkpoint `22868e168cf7f134bcab08425523eccc05f3c394` pushed.
First candidate CI run40183917951/job121140566373:58 passed/2 skipped/1 failed
before building. The new runner used hosted Python without real GI, not a
product import failure. Reuse the existing `ci_desktop_env.sh` system-Python/GI
environment; do not mock GI or skip the packaging import regression.

Run40184000969/job121140811312 passed the bounded tests/native standard build,
then RNS correctly rejected apt-provided pyserial without wheel RECORD. Separate
the real-GI test environment from the existing L03.1 pure-wheel Docker builder.
No dependency verification weakening and no change to accepted product bytes.
