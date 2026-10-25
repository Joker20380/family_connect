# U2604-COMPAT — Ubuntu26.04 / system CPython3.14

**U2604-COMPAT — CHECKPOINT PASS in Ubuntu26.04/CPython3.14 compatibility scope.**
This is not full-suite/release acceptance: mandatory full suites remain FAIL,
unsuppressed and separately recorded below. Report name/date
26.10 follows the owner request; the probe actually ran25.10.2026 UTC, starting21:48:03.
Entry main `5c4f0f3e734c8a1da41f6ce33822fbd4b1b6cf13` matched remote main.
Pre-existing ops additions in STATUS/PLAN and two VPN-health reports are preserved,
not part of this task's commits. No subagents or private product state are used.

## Boundary and frozen candidate

LOCAL-OWNER-UPGRADE stopped before any change: workstation Ubuntu26.04, system
`/usr/bin/python3`3.14.4, installed Family Connect0.2.11. Frozen
`0.2.12~l03.2.5` requires Python3.12 both in DEB dependencies and strict runtime ABI.
Old user desktop entries still point at control previews; none were moved.
No backup/installation/system setup/close-reopen or personal identity loading occurred.

[Frozen beta manifest](2026-10-25-linux-awg-tcp-beta-freeze.json) remains immutable:
candidate `f0ee17609cfc8dbaf48edfa0f33b417754f9674d578168fa4cbb1c47d51d3f95`,
system `8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d`.
AppImage/DEB/legacy hashes were rechecked before the probe; original bytes are not
rebuilt, replaced, repacked or relabelled. L04.1/LIVE-2 remain DONE/review accepted;
registry continuity NOT_PROVEN remains a separate observation, no F2 replay/R3.

## Source-read-only compatibility probe: PASS

New disposable Ubuntu26.04.1 container, official `ubuntu:26.04` digest
`sha256:c098726dd9b9733f3e885f8de0ef375206a311b0a317eadc40d347b1115fb944`.
System CPython3.14.4, systemd259.9 as PID1, private PID/cgroup/mount/network namespaces;
no host bus/resolver/cgroup or private state mount. Public source export is read-only.
Bridge egress is used only for public build dependencies; exact package gates used
offline loopback-only containers. Container tooling is not a production dependency.

| Exact lock | SHA256 | Result |
| --- | --- | --- |
| provisioning/requirements.lock | `837d0aa08e47bca06da94f07056f0e3fc46380f03c365ad4fd48ce9a3d601e7c` | installed, exit0 |
| messenger/requirements.lock | `d20e0c6336cc571e2313827b4d0c14ef328e9e0cc724bdc24054f15a7182493b` | installed with `--no-deps --require-hashes`, exit0 |

No pin/hash relaxation. `pip check` PASS. All17 distributions' locked versions and
630 collected members pass the existing wheel-RECORD SHA256/size/member checks.
Collected Python3.14 inventory SHA256
`761e5abb69ef1c2ba9766665982a47a410cf639f68c394e7865beb52e1796909`.
Strict `python -I` imports PASS for cryptography46.0.7 (including Rust binding),
cffi2.1.1/native backend, pydantic_core2.46.5, pydantic2.13.5, RNS1.5.1, LXMF1.1.1
and every other locked module. Origins resolve to the locked disposable venv.
No Py3.12 installation, interpreter switch, alternate interpreter or host pip.

GTK4.22.4/libadwaita1.9.1, cairo1.18.4, Secret typelib plus real private
Secret Service D-Bus Ping, GStreamer1.28.2 and codec2 shared-library loading PASS.
Xvfb window create/present/close PASS; expected no-DRI3/accessibility-bus warnings
are retained, not presented as a hardware-rendering acceptance.

Unchanged source targeted tests: **129 PASS** across system runtime, candidate,
operations and queued Connect/Close GTK coverage. Initial `python -I -m pytest`
run:126 PASS/3 FAIL because `scripts`/`provisioning` public source roots were absent
from isolated test-runner sys.path. Corrected invocation explicitly adds only the
read-only `/source`, still under `-I`; no source/fixture/assertion changed.
Initial Secret Service CLI check lacked `gdbus`; actual Gio D-Bus Ping then passed.
Docker's legacy builder rejected `--progress` before building; flag removed only.
Polkit was explicitly started inside the disposable container before runtime checks.

Probe completed before any source edits. Both lockfiles and the initial worktree
diff remained exact. `PY314_BLOCKED` is **not** the result: locked install/imports pass.
[Sanitized probe/package evidence](2026-10-26-linux-ubuntu2604-python314-compat.evidence.json)
records each downloaded wheel's filename/SHA256; full member inventory stays local.

## Packaging-only adaptation

Built exact candidate **0.2.12~l03.2.7**, explicitly Ubuntu26.04/Python3.14.
The preliminary `.6` CI build is retained as failed evidence, not the owner-upgrade
candidate: run40237804085/job121303012680 verified a3.14 package with the runner's
3.12 interpreter and correctly rejected `Candidate runtime contract/ABI mismatch`.
The verifier now runs in the offline Ubuntu26.04 container; no ABI check is bypassed.
Initial local exact-package setup was refused by the fixture's polkit rule:
polkit127 resolves `program` to `/usr/bin/python3.14`, while retaining the original
`command_line`. The fixture now recognizes that resolved system-interpreter path
as well as `/usr/bin/python3`; exact full-command and UID checks remain unchanged.
No production authorization/setup change or artifact-byte replacement is needed.
Explicit target selects ABI3.14 and DEB `python3 >=3.14, <3.15`; candidate manifest
records Ubuntu26.04 and `/usr/bin/python3`. New target requires an explicit standard
system rebuild, rejects Python3.12 and frozen .5 version reuse. System/user vendor
payloads are collected afresh from locked3.14 distributions, never renamed old3.12 bytes.
System build ID is content-derived from the new runtime inventory; no old-ID reuse.
CI candidate version advances to .7 and uses official Ubuntu26.04 builder/package
containers. Existing offline fixture guards accept only the matching
Ubuntu24.04/systemd255/Python3.12 or Ubuntu26.04/systemd259/Python3.14 tuple.

No production VPN, GUI, MESH, messenger, updater, wire/auth2, identity/cache/floor,
server provisioning or Android code changes are required. Packaging metadata,
builders, fixture platform guards and tests only. Public VERSION/catalog/landing/
tags/releases unchanged. No real identity, activation/cache or gateway use.
New target/version/dependency guards plus original selected tests: **136 PASS**.
Full desktop on the same real GTK/Python3.14 environment: **1199 PASS/83 SKIP**,
no failures. Explicit native/kernel/fixture-dependent skips remain separate gates,
not deleted, xfailed or silently counted as runtime acceptance.

## Exact local delivery

Canonical local output: `state-client-build/linux-ubuntu2604-python314-20261026/build/`.
Candidate/source: `c79b4feb51f3755ce458367d057abcb5fdd87bd975fe6059fa8fe06d88617c45` /
`3df82b4555d48f2ae8284244d093e36de5c4bc1d`, source_dirty=false.
System build: `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
System production-source commit remains `053c4e5f9532ca927f49a78f9c0ed17903375baf`:
production code is unchanged, but newly collected Python3.14 bytes produce a new ID.
Native source digest `cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61`;
fresh standard native Go1.26.1 build/race tests PASS; RNS rebuilt from exact locked deps.
Fixture validation commit `fb588c084240247166c500cdab568cc5ff0e48bc` changes only the
polkit test matcher; it does not change these selected artifact bytes.

| Exact file | Bytes | SHA256 |
| --- | ---: | --- |
| FamilyConnect-0.2.12~l03.2.7-x86_64.AppImage | 57924088 | `ff3b41fb051154852efddf43eaba8a73d1a7cf61ab5eb7d8d29bba246ee7342a` |
| FamilyConnect_0.2.12~l03.2.7_amd64.deb | 55962464 | `f77f44ea6ef70791d8e45a4b811e0e417e5ce1ecc4dbc6cbf1e320e2eda33d28` |
| FamilyConnect-Linux-0.2.12~l03.2.7.tar.gz | 114495 | `07ca375c7e8fc2794e8d2beb20c91ea7c96f2b1a2a08a0da27ebce8268aa42bd` |
| ../system/FamilyConnect-MESH-system-amd64.tar.gz | 49252181 | `402affe5628da4ecd1df3e274f3c67848d5e59023a63374765c91419490b9a55` |

Legacy is **six-file shape compatibility only**, not an updater/publication payload.
[Exact candidate manifest](2026-10-26-linux-ubuntu2604-python314-compat.candidate.json)
contains707 user members; [exact system manifest](2026-10-26-linux-ubuntu2604-python314-compat.system.json)
contains758 hashed payload members (759 archive members including the manifest).
[Shared user/system Python inventory](2026-10-26-linux-ubuntu2604-python314-compat.python-runtime.json)
contains630 members; all three Python contracts equal `[3,14]`.
DEB Depends is `python3 (>= 3.14), python3 (<< 3.15)`; executable remains system
`/usr/bin/python3`. Candidate manifest explicitly identifies Ubuntu26.04.
Manifest hashes/sizes and downloaded wheel provenance are in the evidence JSON.

## Disposable acceptance results

All exact package tests use real Ubuntu26.04/systemd259, D-Bus, polkit127/pkexec,
GTK4/Adw, NetworkManager/resolved, TUN/nftables/iproute2, Secret Service,
GStreamer/codec2. No host buses/network namespaces or private product state mounted.
Real pkexec authorization uses a narrow synthetic UID1000/exact-command fixture
rule, not a fake executable or the owner's interactive authentication.

| Gate | Result |
| --- | --- |
| Exact AppImage/DEB hashes, matching ID/inventory, six-file legacy shape | PASS |
| Strict user imports/candidate-check; system imports under system Python3.14 | PASS |
| GUI smoke, URI registration/Gio handler and invalid-URI smoke, user service | PASS |
| Explicit pkexec setup/reinstall, candidate/system matching READY | PASS |
| Root→UID IPC; no silent VPN/system setup; rollback after failed imports | PASS |
| Missing/tampered embedded payload, mixed build/schema/runtime rejection | PASS |
| Installer owner locks, concurrent install/direct-exec exclusion, sticky cleanup | PASS |
| Synthetic identity/settings/history, encrypted state, DEB reinstall/remove | PASS |
| AppImage/DEB shared user state and independent root runtime; no package-local state | PASS |
| Exact installed AWG/TCP prestart refusal/terminalization and lock/cache preservation | PASS both; zero successful transport starts, TUN0, network unchanged |
| Full desktop with real GTK/Xvfb | 1199 PASS /83 SKIP /0 FAIL |
| Native configuration/ownership/root→UID/chat selections | 144 PASS |
| Isolated Auto real TUN/nftables/native kernel gate | 18 checks PASS |
| Isolated DIRECT synthetic TLS/proofs/mailbox, fatal-TLS no fallback | PASS |
| Lifetime/terminal/status synthetic fixture | 15 PASS |
| Manual/Auto combined OFF–ON–OFF and release-control fixture | 3 PASS |

Synthetic DIRECT uses a gateway-shaped address **inside its isolated peer namespace**;
there is no route to the real gateway. These tests do not expand the AWG/TCP beta scope
to MESH/Auto/messenger and do not constitute live VPN acceptance.

Initial failures remain evidence: stale native inventory rejected (fresh native build
used instead); bare shallow Xray clone lacked its unreferenced pinned commit (exact
commit fetched); AppImage builder lacked `file` (installed only in disposable builder;
already-built DEB/legacy bytes preserved); DIRECT rejected UID1000-owned worker input
(identical bytes installed root-owned inside the disposable container, then PASS).
Full-suite preparation rejected Go1.26.1 and missing offline Go modules; official
Go1.26.0 plus locked carrier downloads supplied only in the disposable environment.
URI probe initially raced system D-Bus startup and encountered a fresh home without
`.config`; final run waits for D-Bus, creates that synthetic user's config directory,
requires a persisted nonempty mimeapps.list and verifies both xdg-mime and Gio.

## Full suites and remaining boundary

Mandatory full Ubuntu26.04/Python3.14 suite, with source-pinned release capsules and
no excluded tests: **3257 PASS /55 FAIL /104 SKIP**,7 subtests PASS,12 warnings.
The extra root `test_unit_umask_fresh_runtime_and_real_uid[lock]` observation is kept:
it reproduces under restrictive umask077 on **both** disposable Python3.12 and3.14;
the ordinary-umask isolated six-case runtime selection passes. This does not erase
the55-failure full result or establish general CI PASS. Existing54/54/54 residual
failures remain separate technical debt, not repaired or waived here.
Source checkpoint control CI40237803982/job121303012725:3172 PASS/54 FAIL/190 SKIP.
Later CI artifacts are independent internal rebuilds, not replacements for the exact
local candidate above. Existing push workflows may upload diagnostic artifacts;
no manual upload, release asset, tag, catalog or public publication was performed.

Validation-source CI: [Linux candidate40238990965/job121306534652](https://github.com/Joker20380/family_connect/actions/runs/40238990965/job/121306534652)
**PASS**, including real isolated Ubuntu26.04 package gates after the fixture fix.
Initial source native bridge40237803992 (Linux/Windows protocol + isolated kernel)
and Client builds40237803948 (Linux/Windows/Android/Windows compatibility) **PASS**;
release job skipped, no release performed. Validation-source control40238990957
FAIL; phase0/tests40238990933 still IN_PROGRESS at the final observation, its
Docker failover job FAIL. These states do not replace the complete local full-suite
result or imply green general CI. Exact job snapshots are retained in evidence.

## Installation and rollback boundary

Only after separate review/owner authorization, and confirmed disconnected/idle
owners with completed cleanup: protected local backup of user state and competing
launcher entries, exact DEB installation, ordinary-user
`/usr/bin/family-connect --setup-system` with real owner pkexec authorization,
then candidate-check/status
and persistent close/reopen. Never launch the GUI as root or substitute an installer
path. No Python switching, host pip, private interpreter or ABI bypass.

Installer rollback on failed readback is tested. Later manual rollback requires a
verified **matching user/system pair compatible with the actual system Python ABI**,
while disconnected; retain user backup and installer root backup. Frozen .5/Python3.12
is **not** an executable rollback pair on this Ubuntu26.04/Python3.14 host. DEB removal
alone does not remove independent root runtime/backups or private state. Do not erase
markers/journals/locks or legacy releases/current/previous/AppImages/desktop backups.
No host install, backup, launcher migration or rollback was performed here.

## Final hygiene

Exact frozen .5 AppImage/DEB/legacy hashes rechecked unchanged; host dpkg remains
0.2.11 and `/usr/bin/python3`3.14.4. Host launcher and both user desktop-entry hashes
match the read-only audit. Owned disposable containers stopped/removed; local build
artifacts and protected raw synthetic evidence retained outside Git.
JSON/manifest identities/member paths and artifact sizes/hashes PASS; changed-document
local links/anchors checked with0 errors; bounded staged secret scan2934 entries,
0 blocked files. Staged scope is only sanitized docs/manifests; `git diff --check`
PASS. Pre-existing VPN-health docs/STATUS/PLAN additions remain uncommitted and intact.

Workstation unchanged; rollback/install on host NOT_RUN. Disposable/synthetic gates
do not authorize owner installation. L04.2/L05/test-device teardown, live VPN,
signing/upload/catalog update/publication **NOT_RUN**.
**STOP after checkpoint. NEXT — review U2604-COMPAT.** Only after separate review
and owner authorization: LOCAL-OWNER-UPGRADE with launcher backup, exact DEB/setup,
persistent close/reopen and one AWG plus one TCP connect/disconnect; not a reopened L04.1.
