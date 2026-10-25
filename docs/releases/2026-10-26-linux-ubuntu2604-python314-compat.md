# U2604-COMPAT — Ubuntu26.04 / system CPython3.14

**IN_PROGRESS / source packaging checkpoint; not acceptance PASS.** Report name/date
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
Bridge egress is used only for official OS/Python dependencies; package gates will
use offline loopback-only containers. Container tooling is not a production dependency.

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

Reserved new candidate **0.2.12~l03.2.7**, explicitly Ubuntu26.04/Python3.14.
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

## Remaining gates and release boundary

New exact AppImage/DEB/legacy, candidate/system manifests and artifact hashes:
**NOT_BUILT** at this source checkpoint. Exact package/system imports, real pkexec,
READY, state preservation, rollback/tamper/mixed-build/install barriers,
AWG/TCP and isolated native/Auto/DIRECT, mandatory full suites: pending; no suppression.
Existing full-suite54/54/54 residual failures are separate technical debt, not fixed
or waived here. No CHECKPOINT PASS until all required package/contract gates finish.

Workstation unchanged; rollback/install on host NOT_RUN. Disposable/synthetic gates
do not authorize owner installation. L04.2/L05/test-device teardown, live VPN,
signing/upload/catalog update/publication **NOT_RUN**.
**STOP after checkpoint. NEXT — review U2604-COMPAT.** Only after separate review
and owner authorization: LOCAL-OWNER-UPGRADE with launcher backup, exact DEB/setup,
persistent close/reopen and one AWG plus one TCP connect/disconnect; not a reopened L04.1.
