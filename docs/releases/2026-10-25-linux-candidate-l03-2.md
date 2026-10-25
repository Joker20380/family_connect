# L03.2 — full internal Linux candidate

Date: **2026-10-25**. **CHECKPOINT — local candidate gate PASS, review pending**.
Installed only in disposable containers; not published. CI continuation below.
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

Exact artifacts and installation/removal/rollback evidence are recorded below;
these results are not inferred from source or a mocked systemctl/readback.
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

## First committed artifact checkpoint (superseded)

Product source **`22868e168cf7f134bcab08425523eccc05f3c394`**, `source_dirty=false`.
Retained evidence, superseded by the launcher fail-closed correction below.
Directory: `state-client-build/linux-candidate-l032-20261025/build-final-1/`.
Internal built/installed version **0.2.12~l03.2.1**, source/public VERSION **0.2.11**.
Candidate identity: `076f23d3f91423414c6afe4ab60c97a8c31447fe93e5566d45f0a433521d48fb`.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `FamilyConnect-0.2.12~l03.2.1-x86_64.AppImage` | 57924088 | `d284846dc356c294dbea4e9c4d521c9eb7644816dd7dd3e1493d461aea9641ca` |
| `FamilyConnect_0.2.12~l03.2.1_amd64.deb` | 55951132 | `fe5ac90f0694db13c027972c42e1ed8e80bd87c5231f204a6f4e93f91f029cc6` |
| `FamilyConnect-Linux-0.2.12~l03.2.1.tar.gz` | 112233 | `8a3847d88aa0b7098f94518c0e986bbaf3e00bcfcc4bc35f82a6817cae1e15ae` |

The legacy archive still has exactly six files and its existing updater contract;
it is **not** the full candidate. No public0.2.11 binary name has been reused.
Both full formats contain identical **707-member user inventory**, canonical
`candidate.json` schema1/runtime_contract2/Python3.12. Each file is size/SHA-bound;
extra/missing/symlink/unsafe-mode members fail closed. User application, daemon,
D-Bus integration, notifications/events, voice, Friends/identity, backend/updater,
DIRECT/EXISTING_EXIT code and locked vendor distributions are included. Host GI,
GTK, Secret Service and audio dependencies remain explicit, not hermetic GTK.

Embedded system: unchanged **L03.1/build-9**, 49247776 bytes, SHA256
`bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9`, build ID
`8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da`.
Fixed installer SHA256 `ed8eac3d1b1c666b1d00433f09ec9a6eec578623249e0895adfa96ae3b53f9d5`.
759 archive members =758 system payload files + manifest; retained AWG3.1,
Xray26.3.27, public anchor and licenses/notices use accepted provenance.
Appimagetool SHA256 `95cbe7cce9717fce90c484e34052ee7c7f1d7635b33c12525b4776826a7d29b6`.
No state/private keys/tokens/dev-venv/checkout paths are shipped. Inventory/license
audit and exact extraction readback PASS. Manifests/hashes are integrity records,
not signatures or authority to trust an unknown externally supplied artifact.

## Actual final installation evidence

Docker29.1.3; image `sha256:6705fc0e0b9a4c83fa3710e45f2b54a27c80cd49b27dbfe7db213d946f5b9dce`;
Ubuntu24.04.5, systemd255.4-1ubuntu8.18, Python3.12.3, GTK4.14.5,
Adwaita1.5, GI3.48.2, polkit/pkexec124, Codec2 1.2. Separate fresh containers
for each format and the accepted-system regression; private D-Bus/resolved,
PID/mount/cgroup/network namespaces, loopback only, `--network none`, executable
private `/tmp`. No workstation services/DNS/connections or neighbouring services
were touched. Installed smoke has no checkout, venv or pip dependencies mounted.
Xvfb/cairo/accessibility fixture settings are not installed defaults.

| Gate on exact final bytes | Result |
|---|---|
| AppImage extraction + DEB content/hash/member/license audit, identical user/system contract, six-file legacy shape | PASS |
| Both formats: real isolated imports from installed/extracted paths, GTK GUI smoke as UID1000, no silent root install/start | PASS |
| Real pkexec/polkit fixture, exact fixed bootstrap/installer, wrong UID/path refused, private temporary cleanup | PASS |
| Explicit setup + bounded safe reinstall, exact installed inventory/capabilities/build ID, no VPN | PASS |
| Tampered embedded archive, old schema, coherent wrong build ID and modified installed module fail closed | PASS |
| Fixed prepare-chat starts only idle DIRECT/service-only hosts; no VPN interface/intent/real traffic | PASS |
| Real D-Bus user daemon/Secret Service, synthetic identity/store, background setting and PID survive GUI close | PASS |
| DEB install/reinstall/remove/reinstall, URI handler/user unit, encrypted state/settings and root backups retained | PASS |
| AppImage original-image reopen (not GUI FUSE mount), menu/URI integration and explicit removal, state retained | PASS |
| Same embedded system: real root→UID IPC/wrong UID, live owner/lock/sticky cleanup refusal, concurrent starts fenced | PASS |
| Same embedded system: intentionally broken real installed import triggers own-file rollback; starts fenced during restore | PASS |

Sanitized local logs under `state-client-build/linux-candidate-l032-20261025/`:
`integrity-final-1.log`, `deb-smoke-final-1.log`, `appimage-smoke-final-1.log`,
`system-smoke-final-1.log`, `environment-final-1.log`, `desktop-final-1.log`.
Full desktop: **1145 passed /24 skipped**,62.76s; targeted packaging/installer/
authorization/capability selection: **61 PASS**. Mock-based unit tests are separate
from the actual system/package gates. Build-time `candidate-delivery.json` retains
`installed:false/acceptance:NOT_RUN`: immutable build metadata, not a smoke receipt;
this report and corresponding logs record the later disposable installation.

## Removal, rollback and remaining limits

DEB removal stops only its fixed user unit before executable removal, preserves
identity/history/config and does not uninstall the independent root runtime.
AppImage requires its fixed `--remove-integration` before deleting the original
image; raw deletion of a running image is not the supported uninstall procedure.
Root units remain unenabled, and already-running idle hosts refer only to the
retained root payload, not removed user paths. Package removal does not terminate
VPN/user network sessions. Root component removal/old-client migration is not
implemented as a hidden maintainer-script action.

Failed system readback rolls back its own files under accepted locks/barriers;
root-owned backups remain. Switching to another reviewed full pair requires its
explicit idle/cleanup-safe setup, not a standalone native binary replacement.
Clean install/reinstall of this candidate is tested; upgrade from public0.2.11,
cross-format migration and legacy updater migration remain **L08 NOT_RUN**.
Full visual L07, live VPN/Telemost, registration, grants and installed delivery
remain **L04/L05 NOT_RUN**. Linux systemd255/Ubuntu24.04 is the measured platform;
other distro/Python/GTK combinations are not claimed accepted.
No L03.1 product correction was necessary. Parent L03 remains IN_PROGRESS until
review L03.2. D01/D02.1-R and the residual54/Windows/voice observations stay open.
No public release/upload, catalog, landing, signing sequence or server mutation.

## L03.2 launcher integrity correction

Post-checkpoint review found a missing `candidate.json` allowed entry into the
legacy launcher branch. New regression reproduced **1 failure** before the fix.
Candidate companion files now require candidate verification even when the
manifest is absent; the installed smoke also removes the manifest from a copy
and verifies rejection before GUI launch. This corrects new L03.2 packaging,
not the accepted L03.1 system contract. New final bytes/gates are required below;
do not transfer the preceding artifact hashes or smoke receipts to the rebuild.

The new AppImage negative fixture initially copied0700 extracted directories
as root: rejection was EACCES, not the intended missing-manifest check. Retain
`appimage-smoke-final-2.log` as FAIL. The tampered copy now belongs to the ordinary
UID, asserts the exact hash/manifest error and tests wrong-UID polkit denial
directly (not merely inability to traverse another user's home). Product bytes
are unchanged by this fixture correction; repeat both exact package gates.
The direct polkit-denial assertion initially expected cancellation126; actual
polkit124 returns127/`Not authorized` for a policy denial. Preserve final-3 logs
as fixture FAIL; assert the measured denial, not merely any nonzero result.
